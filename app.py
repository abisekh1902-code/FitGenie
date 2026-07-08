"""
FitGenie — AI-Powered Fitness Coach
Flask backend powered by IBM Watsonx.ai (Granite models)
"""

import os
import json
import math
import time
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
#  AGENT INSTRUCTIONS  ← Customize everything about the AI coach here
# ─────────────────────────────────────────────────────────────────────────────
AGENT_INSTRUCTIONS = {
    # ── Personality & Tone ──────────────────────────────────────────────────
    "name": "FitGenie",
    "persona": (
        "You are FitGenie, an enthusiastic, friendly, and knowledgeable AI fitness coach. "
        "You speak in a warm, encouraging, and motivating tone—like a supportive gym buddy "
        "who also has expert-level knowledge. You use simple language, avoid medical jargon, "
        "and always celebrate small wins to keep users motivated."
    ),

    # ── Fitness Specialization ───────────────────────────────────────────────
    "specializations": [
        "Home workouts with zero or minimal equipment",
        "Bodyweight training (push-ups, squats, lunges, planks, burpees)",
        "HIIT (High-Intensity Interval Training)",
        "Yoga and flexibility routines",
        "Beginner to advanced progressive training",
        "Fat loss, muscle gain, and general fitness goals",
        "Recovery and rest-day strategies",
        "Breathing techniques and mindfulness for fitness",
    ],

    # ── Indian Fitness Context ───────────────────────────────────────────────
    "indian_context": {
        "enabled": True,
        "meal_preferences": [
            "Prefer Indian food options: dal, sabzi, roti, rice, idli, dosa, upma, poha, sprouts",
            "Suggest high-protein Indian foods: paneer, dal, chana, rajma, soya, eggs, curd",
            "Include festive and regional meal alternatives when relevant",
            "Account for vegetarian and vegan Indian diets by default",
            "Suggest desi superfoods: turmeric milk (haldi doodh), amla, moringa, sattu, ragi",
        ],
        "exercise_references": [
            "Reference Indian sports: kabaddi, cricket warm-ups, yoga (sun salutation / Surya Namaskar)",
            "Mention morning walk culture popular in Indian households",
            "Include staircase workouts for apartment dwellers",
        ],
        "cultural_tips": [
            "Acknowledge Indian meal timings (late dinners) and suggest alternatives",
            "Mention hydration importance in hot Indian climate",
            "Reference Ayurvedic principles when discussing recovery and nutrition",
        ],
    },

    # ── Response Style ───────────────────────────────────────────────────────
    "response_style": {
        "use_emojis": True,
        "use_bullet_points": True,
        "include_encouragement": True,
        "max_workout_exercises": 8,
        "default_workout_duration_minutes": 30,
        "structure_responses": True,
    },

    # ── Safety Rules ─────────────────────────────────────────────────────────
    "safety_rules": [
        "Always recommend consulting a doctor before starting any new exercise program, "
        "especially for users with pre-existing health conditions.",
        "Never diagnose medical conditions or provide medical treatment advice.",
        "If a user mentions pain, injury, dizziness, or chest discomfort, immediately advise "
        "them to stop exercise and seek medical attention.",
        "For weight loss, never recommend below 1200 kcal/day for women or 1500 kcal/day for men.",
        "Do not recommend extreme diets, fasting beyond 16 hours, or unsafe supplements.",
        "Always include warm-up and cool-down reminders for workout plans.",
        "For beginners, emphasize proper form over speed or weight.",
        "Remind users to stay hydrated—minimum 8 glasses (2 liters) of water daily.",
    ],

    # ── Motivational Style ───────────────────────────────────────────────────
    "motivation_style": {
        "quotes_language": "English with occasional Hindi phrases for Indian users",
        "challenge_intensity": "gradual",  # gradual | moderate | intense
        "streak_encouragement": True,
        "celebrate_milestones": [1, 3, 7, 14, 21, 30, 60, 90],  # days
    },

    # ── Habit Building Framework ─────────────────────────────────────────────
    "habit_building": {
        "framework": "BJ Fogg Tiny Habits + James Clear Atomic Habits principles",
        "focus": "Start small, be consistent, attach habits to existing routines",
        "daily_minimum": "Even 5 minutes of movement counts—never miss twice",
    },

    # ── Topics Out of Scope ──────────────────────────────────────────────────
    "out_of_scope": [
        "Medical diagnoses or prescriptions",
        "Steroid or performance-enhancing drug advice",
        "Extreme weight loss (more than 1 kg/week)",
        "Political, religious, or unrelated lifestyle topics",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  Watsonx.ai Configuration
# ─────────────────────────────────────────────────────────────────────────────
IBM_API_KEY        = os.getenv("IBM_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_MODEL_ID   = os.getenv("WATSONX_MODEL_ID", "ibm/granite-4-h-small")
MAX_NEW_TOKENS     = int(os.getenv("MAX_NEW_TOKENS", "1024"))
TEMPERATURE        = float(os.getenv("TEMPERATURE", "0.7"))
TOP_P              = float(os.getenv("TOP_P", "0.9"))

# IAM token cache  {token, expires_at}
_iam_cache: dict = {}

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


def _get_iam_token() -> str:
    """Exchange IBM API key for a Bearer token, caching until 5 min before expiry."""
    now = time.time()
    if _iam_cache.get("token") and now < _iam_cache.get("expires_at", 0):
        return _iam_cache["token"]

    resp = requests.post(
        IAM_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": IBM_API_KEY,
        },
        timeout=20,
    )
    resp.raise_for_status()
    payload = resp.json()
    _iam_cache["token"]      = payload["access_token"]
    _iam_cache["expires_at"] = now + payload.get("expires_in", 3600) - 300
    return _iam_cache["token"]

# ─────────────────────────────────────────────────────────────────────────────
#  Flask App
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fitgenie-dev-secret-key-change-in-production")

# Custom Jinja2 filters
app.jinja_env.filters["enumerate"] = enumerate


def _generate_via_rest(prompt: str) -> str:
    """Call Watsonx.ai text generation REST API directly — no SDK, no WML instance needed."""
    token = _get_iam_token()
    url   = f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"

    payload = {
        "model_id":   WATSONX_MODEL_ID,
        "project_id": WATSONX_PROJECT_ID,
        "input":      prompt,
        "parameters": {
            "max_new_tokens":  MAX_NEW_TOKENS,
            "temperature":     TEMPERATURE,
            "top_p":           TOP_P,
            "stop_sequences":  ["<|endoftext|>", "Human:", "User:"],
            "repetition_penalty": 1.05,
        },
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        body = resp.json()
        errs = body.get("errors", [{}])
        code = errs[0].get("code", "unknown")
        msg  = errs[0].get("message", resp.text[:200])
        raise RuntimeError(f"[{resp.status_code}] {code}: {msg}")

    result = resp.json()
    return result["results"][0]["generated_text"].strip()


def build_system_prompt(user_profile: dict) -> str:
    """Construct the full system prompt from AGENT_INSTRUCTIONS + user profile."""
    ai = AGENT_INSTRUCTIONS
    indian = ai["indian_context"]

    # Base persona
    prompt = f"{ai['persona']}\n\n"

    # Specializations
    prompt += "Your areas of expertise include:\n"
    for spec in ai["specializations"]:
        prompt += f"  • {spec}\n"
    prompt += "\n"

    # Indian context
    if indian["enabled"]:
        prompt += "Indian Fitness Context:\n"
        for pref in indian["meal_preferences"]:
            prompt += f"  • {pref}\n"
        for ex in indian["exercise_references"]:
            prompt += f"  • {ex}\n"
        for tip in indian["cultural_tips"]:
            prompt += f"  • {tip}\n"
        prompt += "\n"

    # Safety rules
    prompt += "IMPORTANT SAFETY RULES (always follow):\n"
    for rule in ai["safety_rules"]:
        prompt += f"  ⚠️  {rule}\n"
    prompt += "\n"

    # Out of scope
    prompt += "Topics you must NOT discuss:\n"
    for topic in ai["out_of_scope"]:
        prompt += f"  ✗ {topic}\n"
    prompt += "\n"

    # User profile context
    if user_profile:
        prompt += "Current User Profile:\n"
        if user_profile.get("name"):
            prompt += f"  Name: {user_profile['name']}\n"
        if user_profile.get("age"):
            prompt += f"  Age: {user_profile['age']} years\n"
        if user_profile.get("weight"):
            prompt += f"  Weight: {user_profile['weight']} kg\n"
        if user_profile.get("height"):
            prompt += f"  Height: {user_profile['height']} cm\n"
        if user_profile.get("goal"):
            prompt += f"  Fitness Goal: {user_profile['goal']}\n"
        if user_profile.get("level"):
            prompt += f"  Fitness Level: {user_profile['level']}\n"
        if user_profile.get("diet"):
            prompt += f"  Diet Preference: {user_profile['diet']}\n"
        prompt += "\n"

    prompt += (
        "Always structure your responses clearly using bullet points, emojis, and headers. "
        "Keep responses practical, concise, and actionable. "
        "End each response with a motivational sentence.\n"
    )
    return prompt


def chat_with_watsonx(user_message: str, history: list, user_profile: dict) -> str:
    """Send a message to Watsonx.ai and return the response."""
    # Guard: catch missing / placeholder credentials immediately
    if not IBM_API_KEY or IBM_API_KEY == "your_ibm_cloud_api_key_here":
        return "⚠️ IBM_API_KEY is not set. Please add it to your .env file and restart."
    if not WATSONX_PROJECT_ID or WATSONX_PROJECT_ID == "your_watsonx_project_id_here":
        return "⚠️ WATSONX_PROJECT_ID is not set. Please add it to your .env file and restart."

    system_prompt = build_system_prompt(user_profile)

    # Build conversation context (last 6 turns to stay within token limits)
    conversation = ""
    recent_history = history[-6:] if len(history) > 6 else history
    for turn in recent_history:
        conversation += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n\n"

    full_prompt = (
        f"<|system|>\n{system_prompt}<|end|>\n"
        f"{conversation}"
        f"<|user|>\n{user_message}<|end|>\n"
        f"<|assistant|>\n"
    )

    try:
        return _generate_via_rest(full_prompt)
    except requests.exceptions.ConnectionError:
        return "⚠️ Cannot reach IBM Cloud. Please check your internet connection."
    except requests.exceptions.Timeout:
        return "⚠️ IBM Watsonx.ai took too long to respond. Please try again."
    except RuntimeError as e:
        err = str(e)
        print(f"[FitGenie] Generation error: {err}")
        # Friendly messages for the most common IBM error codes
        if "no_associated_service_instance" in err:
            return (
                "⚠️ Your Watsonx project is not linked to a Watson Machine Learning instance.\n\n"
                "**Fix in 2 minutes:**\n"
                "1. Open dataplatform.cloud.ibm.com → your project\n"
                "2. Go to **Manage → Services & integrations → Associate service**\n"
                "3. Select (or create) a **Watson Machine Learning** instance → Associate\n"
                "4. Restart FitGenie and try again."
            )
        if "invalid_request_entity" in err or "model_not_supported" in err:
            return f"⚠️ Model `{WATSONX_MODEL_ID}` is not available. Try changing WATSONX_MODEL_ID in .env."
        if "403" in err:
            return "⚠️ Access denied (403). Your API key may not have Watsonx.ai permissions."
        if "401" in err:
            return "⚠️ Authentication failed (401). Please check your IBM_API_KEY in .env."
        return f"⚠️ Watsonx error: {err[:200]}"
    except Exception as e:
        print(f"[FitGenie] Unexpected error: {e}")
        return f"⚠️ Unexpected error: {str(e)[:200]}"


# ─────────────────────────────────────────────────────────────────────────────
#  Fitness Calculation Utilities
# ─────────────────────────────────────────────────────────────────────────────
def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        category, color = "Underweight", "info"
    elif bmi < 25.0:
        category, color = "Normal weight", "success"
    elif bmi < 30.0:
        category, color = "Overweight", "warning"
    else:
        category, color = "Obese", "danger"
    return {"bmi": round(bmi, 1), "category": category, "color": color}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor equation."""
    if gender.lower() == "female":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5


def calculate_tdee(bmr: float, activity_level: str) -> float:
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    return bmr * multipliers.get(activity_level, 1.55)


def calculate_ideal_weight(height_cm: float, gender: str) -> dict:
    """Devine formula for ideal body weight."""
    height_inches = height_cm / 2.54
    if gender.lower() == "female":
        base = 45.5 + 2.3 * (height_inches - 60) if height_inches > 60 else 45.5
    else:
        base = 50 + 2.3 * (height_inches - 60) if height_inches > 60 else 50
    return {"min": round(base * 0.9, 1), "ideal": round(base, 1), "max": round(base * 1.1, 1)}


def calculate_water_intake(weight_kg: float, activity_level: str) -> float:
    """Recommended daily water intake in liters."""
    base = weight_kg * 0.033
    activity_bonus = {"sedentary": 0, "light": 0.25, "moderate": 0.5, "active": 0.75, "very_active": 1.0}
    return round(base + activity_bonus.get(activity_level, 0.5), 1)


# ─────────────────────────────────────────────────────────────────────────────
#  Static Content — Workouts, Meals, Motivation
# ─────────────────────────────────────────────────────────────────────────────
WORKOUT_PLANS = {
    "beginner": {
        "label": "Beginner",
        "duration": "20–30 min",
        "rest": "60 sec between sets",
        "exercises": [
            {"name": "Jumping Jacks", "sets": "3", "reps": "20", "icon": "🏃"},
            {"name": "Wall Push-Ups", "sets": "3", "reps": "10", "icon": "💪"},
            {"name": "Chair Squats", "sets": "3", "reps": "12", "icon": "🦵"},
            {"name": "Plank Hold", "sets": "3", "reps": "20 sec", "icon": "🧘"},
            {"name": "Glute Bridges", "sets": "3", "reps": "15", "icon": "🍑"},
            {"name": "Seated Leg Raises", "sets": "3", "reps": "12", "icon": "🦶"},
            {"name": "Marching in Place", "sets": "1", "reps": "3 min", "icon": "🚶"},
        ],
    },
    "intermediate": {
        "label": "Intermediate",
        "duration": "30–40 min",
        "rest": "45 sec between sets",
        "exercises": [
            {"name": "Burpees", "sets": "4", "reps": "10", "icon": "🔥"},
            {"name": "Standard Push-Ups", "sets": "4", "reps": "15", "icon": "💪"},
            {"name": "Jump Squats", "sets": "4", "reps": "15", "icon": "🦵"},
            {"name": "Mountain Climbers", "sets": "4", "reps": "20", "icon": "⛰️"},
            {"name": "Reverse Lunges", "sets": "3", "reps": "12 each", "icon": "🏋️"},
            {"name": "Tricep Dips (Chair)", "sets": "3", "reps": "12", "icon": "💺"},
            {"name": "High Knees", "sets": "3", "reps": "30 sec", "icon": "🏃"},
            {"name": "Superman Hold", "sets": "3", "reps": "10", "icon": "🦸"},
        ],
    },
    "advanced": {
        "label": "Advanced",
        "duration": "40–50 min",
        "rest": "30 sec between sets",
        "exercises": [
            {"name": "Plyometric Push-Ups", "sets": "4", "reps": "15", "icon": "💥"},
            {"name": "Pistol Squat Progressions", "sets": "4", "reps": "8 each", "icon": "🦵"},
            {"name": "Burpee + Tuck Jump", "sets": "4", "reps": "12", "icon": "🔥"},
            {"name": "Diamond Push-Ups", "sets": "4", "reps": "12", "icon": "💎"},
            {"name": "Jump Lunges", "sets": "4", "reps": "12 each", "icon": "⚡"},
            {"name": "Plank with Shoulder Taps", "sets": "4", "reps": "20", "icon": "🧘"},
            {"name": "Hindu Push-Ups", "sets": "3", "reps": "15", "icon": "🙏"},
            {"name": "Box Jump (on stair step)", "sets": "4", "reps": "10", "icon": "📦"},
        ],
    },
}

MEAL_SUGGESTIONS = {
    "breakfast": [
        {"name": "Poha with Peanuts", "calories": 280, "protein": "8g", "tag": "🇮🇳 Desi Favourite"},
        {"name": "Moong Dal Chilla", "calories": 220, "protein": "14g", "tag": "⚡ High Protein"},
        {"name": "Oats with Banana & Almonds", "calories": 320, "protein": "10g", "tag": "🌾 Fiber Rich"},
        {"name": "Besan Cheela", "calories": 200, "protein": "12g", "tag": "🇮🇳 Quick & Healthy"},
        {"name": "Idli with Sambar", "calories": 250, "protein": "9g", "tag": "🇮🇳 South Indian"},
        {"name": "Sprouts Salad with Lemon", "calories": 180, "protein": "11g", "tag": "🥗 Raw Power"},
    ],
    "lunch": [
        {"name": "Dal + 2 Roti + Sabzi", "calories": 480, "protein": "18g", "tag": "🇮🇳 Classic Thali"},
        {"name": "Brown Rice + Rajma", "calories": 520, "protein": "22g", "tag": "💪 Muscle Food"},
        {"name": "Paneer Bhurji + Roti", "calories": 450, "protein": "24g", "tag": "🧀 Protein Boost"},
        {"name": "Vegetable Khichdi", "calories": 380, "protein": "14g", "tag": "🌿 Comfort Food"},
        {"name": "Curd Rice with Pomegranate", "calories": 340, "protein": "10g", "tag": "🇮🇳 Cooling Meal"},
        {"name": "Quinoa Vegetable Bowl", "calories": 400, "protein": "16g", "tag": "🌾 Super Grain"},
    ],
    "dinner": [
        {"name": "Grilled Paneer + Salad", "calories": 360, "protein": "28g", "tag": "🌙 Light & Lean"},
        {"name": "Dal Soup + 1 Roti", "calories": 300, "protein": "14g", "tag": "🍵 Easy Digest"},
        {"name": "Stir-fried Vegetables + Tofu", "calories": 280, "protein": "18g", "tag": "🥦 Clean Eating"},
        {"name": "Moong Dal Soup", "calories": 260, "protein": "16g", "tag": "🌿 Detox Friendly"},
        {"name": "Egg Bhurji + Toast", "calories": 340, "protein": "22g", "tag": "🍳 Quick Protein"},
        {"name": "Mixed Vegetable Daliya", "calories": 290, "protein": "10g", "tag": "🌾 Wholesome"},
    ],
    "snacks": [
        {"name": "Roasted Chana", "calories": 120, "protein": "7g", "tag": "🌰 Crunchy & Filling"},
        {"name": "Banana + Peanut Butter", "calories": 200, "protein": "8g", "tag": "⚡ Pre-Workout"},
        {"name": "Makhana (Fox Nuts)", "calories": 100, "protein": "4g", "tag": "🇮🇳 Desi Snack"},
        {"name": "Greek Yogurt with Honey", "calories": 150, "protein": "10g", "tag": "🍯 Post-Workout"},
        {"name": "Cucumber + Hummus", "calories": 110, "protein": "5g", "tag": "🥒 Low Calorie"},
        {"name": "Mixed Nuts (30g)", "calories": 180, "protein": "6g", "tag": "🥜 Healthy Fats"},
    ],
}

MOTIVATION_QUOTES = [
    {"quote": "Your body can stand almost anything. It's your mind you have to convince.", "author": "Unknown"},
    {"quote": "Don't wish for it. Work for it.", "author": "Unknown"},
    {"quote": "Fitness is not about being better than someone else. It's about being better than you used to be.", "author": "Khloe Kardashian"},
    {"quote": "The hardest lift is lifting your butt off the couch.", "author": "Unknown"},
    {"quote": "Take care of your body. It's the only place you have to live.", "author": "Jim Rohn"},
    {"quote": "Sweat is just fat crying.", "author": "Unknown"},
    {"quote": "जो शुरू किया, उसे खत्म करो। (What you started, finish it.)", "author": "Indian Proverb"},
    {"quote": "Success isn't given. It's earned — in the gym, on the field, in every rep.", "author": "Unknown"},
    {"quote": "Small steps, big results. Consistency beats perfection every time.", "author": "FitGenie"},
    {"quote": "Your future self is watching you right now through memories.", "author": "Aubrey De Grey"},
]

DAILY_CHALLENGES = [
    {"challenge": "100 Jumping Jacks Challenge", "detail": "Complete 100 jumping jacks throughout the day—break it into sets of 10!"},
    {"challenge": "Plank a Minute", "detail": "Hold a plank for 60 seconds. Too easy? Try 3 sets!"},
    {"challenge": "Staircase Sprint", "detail": "Walk up and down stairs 10 times. Apartment dwellers, this is your cardio!"},
    {"challenge": "20-Minute Walk", "detail": "Step outside for a brisk 20-minute walk. No excuses!"},
    {"challenge": "50 Squats", "detail": "50 squats spread across 5 sets of 10. Do them during TV commercials!"},
    {"challenge": "Hydration Hero", "detail": "Drink 8 glasses of water today. Set reminders every 2 hours!"},
    {"challenge": "Morning Surya Namaskar", "detail": "Complete 5 rounds of Surya Namaskar before breakfast."},
    {"challenge": "No Sugar Day", "detail": "Avoid added sugar for the entire day. Replace with fruits!"},
    {"challenge": "10-Minute Stretch", "detail": "Spend 10 minutes stretching all major muscle groups before bed."},
    {"challenge": "Protein Goal", "detail": "Hit your protein target today—include dal, paneer, eggs, or sprouts in every meal!"},
]

# ─────────────────────────────────────────────────────────────────────────────
#  Flask Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    profile = session.get("user_profile", {})
    stats = {}
    if profile.get("weight") and profile.get("height"):
        w, h = float(profile["weight"]), float(profile["height"])
        gender = profile.get("gender", "male")
        age = int(profile.get("age", 25))
        activity = profile.get("activity", "moderate")

        bmi_data = calculate_bmi(w, h)
        bmr = calculate_bmr(w, h, age, gender)
        tdee = calculate_tdee(bmr, activity)
        ideal = calculate_ideal_weight(h, gender)
        water = calculate_water_intake(w, activity)

        goal = profile.get("goal", "maintenance")
        if goal == "weight_loss":
            calorie_target = round(tdee - 500)
        elif goal == "muscle_gain":
            calorie_target = round(tdee + 300)
        else:
            calorie_target = round(tdee)

        stats = {
            "bmi": bmi_data["bmi"],
            "bmi_category": bmi_data["category"],
            "bmi_color": bmi_data["color"],
            "bmr": round(bmr),
            "tdee": round(tdee),
            "calorie_target": calorie_target,
            "ideal_weight": ideal,
            "water_intake": water,
        }
    return render_template("dashboard.html", profile=profile, stats=stats)


@app.route("/workout")
def workout():
    level = request.args.get("level", "beginner")
    plan = WORKOUT_PLANS.get(level, WORKOUT_PLANS["beginner"])
    return render_template("workout.html", plan=plan, level=level, all_plans=WORKOUT_PLANS)


@app.route("/calculator")
def calculator():
    return render_template("calculator.html")


@app.route("/meals")
def meals():
    return render_template("meals.html", meals=MEAL_SUGGESTIONS)


@app.route("/motivation")
def motivation():
    day_of_year = datetime.now().timetuple().tm_yday
    quote = MOTIVATION_QUOTES[day_of_year % len(MOTIVATION_QUOTES)]
    challenge = DAILY_CHALLENGES[day_of_year % len(DAILY_CHALLENGES)]
    return render_template("motivation.html", quote=quote, challenge=challenge,
                           all_quotes=MOTIVATION_QUOTES)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        session["user_profile"] = {
            "name": request.form.get("name", ""),
            "age": request.form.get("age", ""),
            "weight": request.form.get("weight", ""),
            "height": request.form.get("height", ""),
            "gender": request.form.get("gender", "male"),
            "goal": request.form.get("goal", "maintenance"),
            "level": request.form.get("level", "beginner"),
            "activity": request.form.get("activity", "moderate"),
            "diet": request.form.get("diet", "vegetarian"),
        }
        return jsonify({"status": "saved", "message": "Profile saved successfully! 🎉"})
    return render_template("profile.html", profile=session.get("user_profile", {}))


@app.route("/chat")
def chat_page():
    return render_template("index.html", open_chat=True)


# ─────────────────────────────────────────────────────────────────────────────
#  API Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if "chat_history" not in session:
        session["chat_history"] = []

    history = session["chat_history"]
    user_profile = session.get("user_profile", {})

    response = chat_with_watsonx(user_message, history, user_profile)

    history.append({"user": user_message, "assistant": response})
    if len(history) > 20:
        history = history[-20:]
    session["chat_history"] = history

    return jsonify({
        "response": response,
        "timestamp": datetime.now().strftime("%H:%M"),
    })


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    data = request.get_json(silent=True) or {}
    try:
        weight = float(data["weight"])
        height = float(data["height"])
        age = int(data["age"])
        gender = data.get("gender", "male")
        activity = data.get("activity", "moderate")
        goal = data.get("goal", "maintenance")

        bmi_data = calculate_bmi(weight, height)
        bmr = calculate_bmr(weight, height, age, gender)
        tdee = calculate_tdee(bmr, activity)
        ideal = calculate_ideal_weight(height, gender)
        water = calculate_water_intake(weight, activity)

        if goal == "weight_loss":
            calorie_target = round(tdee - 500)
            goal_label = "Weight Loss (-500 kcal)"
        elif goal == "muscle_gain":
            calorie_target = round(tdee + 300)
            goal_label = "Muscle Gain (+300 kcal)"
        else:
            calorie_target = round(tdee)
            goal_label = "Maintenance"

        return jsonify({
            "bmi": bmi_data["bmi"],
            "bmi_category": bmi_data["category"],
            "bmi_color": bmi_data["color"],
            "bmr": round(bmr),
            "tdee": round(tdee),
            "calorie_target": calorie_target,
            "goal_label": goal_label,
            "ideal_weight": ideal,
            "water_intake": water,
        })
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400


@app.route("/api/clear-chat", methods=["POST"])
def api_clear_chat():
    session["chat_history"] = []
    return jsonify({"status": "cleared"})


@app.route("/api/profile", methods=["GET"])
def api_get_profile():
    return jsonify(session.get("user_profile", {}))


# ─────────────────────────────────────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"""
╔══════════════════════════════════════════╗
║   🏋️  FitGenie is starting up...         ║
║   Model  : {WATSONX_MODEL_ID:<30}║
║   URL    : http://localhost:{port:<13}║
╚══════════════════════════════════════════╝
    """)
    app.run(debug=debug, host="0.0.0.0", port=port)
