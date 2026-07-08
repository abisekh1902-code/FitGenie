# 🏋️ FitGenie — AI-Powered Fitness Coach

> A conversational AI health & fitness coach built with **Python Flask** + **IBM Watsonx.ai (Granite models)** featuring a modern responsive frontend with dark mode, chat UI, fitness dashboard, workout planner, BMI calculator, Indian meal suggestions, and daily motivation.

---

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Agent Customization](#agent-customization)
- [Project Structure](#project-structure)
- [IBM Cloud Deployment](#ibm-cloud-deployment)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 AI Chat | Conversational fitness coach via IBM Granite models |
| 📊 Dashboard | BMI, BMR, TDEE, ideal weight, water intake |
| 💪 Workout Planner | Home routines: Beginner / Intermediate / Advanced |
| 🧮 Calculator | BMI, BMR, TDEE, daily calorie targets |
| 🥗 Meal Suggestions | 24 Indian-inspired meals across 4 meal types |
| 🔥 Daily Motivation | Quotes, challenges & streak tracker |
| 👤 User Profile | Personalized AI responses based on your details |
| 🌙 Dark Mode | Smooth light/dark theme with localStorage persistence |
| 📱 Mobile Ready | Fully responsive Bootstrap 5 layout |
| 🔧 Agent Config | Dedicated `AGENT_INSTRUCTIONS` section in `app.py` |

---

## 🏗️ Architecture

```
Browser  ←→  Flask (app.py)  ←→  IBM Watsonx.ai (Granite)
               │
               ├── /              (Home / Landing Page)
               ├── /dashboard     (Fitness Stats Dashboard)
               ├── /workout       (Workout Planner)
               ├── /calculator    (BMI & Calorie Calculator)
               ├── /meals         (Meal Suggestions)
               ├── /motivation    (Quotes + Streak Tracker)
               ├── /profile       (User Profile Form)
               ├── /api/chat      (POST — AI chat endpoint)
               ├── /api/calculate (POST — Fitness calculations)
               └── /api/clear-chat(POST — Clear session)
```

**Tech Stack:**
- **Backend:** Python 3.10+, Flask 3, `ibm-watsonx-ai`, `python-dotenv`
- **AI Model:** `ibm/granite-3-8b-instruct` (IBM Watsonx.ai)
- **Frontend:** Bootstrap 5.3, Bootstrap Icons, Google Fonts (Inter + Space Grotesk)
- **Storage:** Flask server-side sessions (no database required)

---

## ✅ Prerequisites

- Python 3.10 or higher
- An **IBM Cloud** account → [cloud.ibm.com](https://cloud.ibm.com)
- An **IBM Watsonx.ai** project → [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
- IBM Cloud API Key with **Watsonx.ai** service access

---

## 🚀 Local Setup

### 1. Clone / Download the Project

```bash
# If using git:
git clone <your-repo-url>
cd FitGenie

# Or just navigate to the downloaded folder:
cd path/to/FitGenie
```

### 2. Create a Virtual Environment

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example file
copy .env.example .env          # Windows
cp .env.example .env            # macOS/Linux

# Edit .env with your credentials
notepad .env                    # Windows
nano .env                       # macOS/Linux
```

### 5. Run the Application

```bash
python app.py
```

Open your browser at **http://localhost:5000** 🎉

---

## 🔐 Environment Variables

Edit the `.env` file:

```env
# Required — IBM Watsonx.ai
IBM_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Model Selection
WATSONX_MODEL_ID=ibm/granite-3-8b-instruct

# Flask Security
FLASK_SECRET_KEY=your_random_secret_key_here
FLASK_ENV=development

# Model Tuning
MAX_NEW_TOKENS=1024
TEMPERATURE=0.7
TOP_P=0.9
PORT=5000
```

### Getting IBM Credentials

#### IBM Cloud API Key
1. Go to [cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys)
2. Click **"Create an IBM Cloud API key"**
3. Give it a name (e.g., `FitGenie-Key`)
4. Copy the key — **you won't see it again!**

#### Watsonx Project ID
1. Open [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)
2. Create or open a project
3. Go to **Manage → General → Project ID**
4. Copy the UUID

#### Available Model IDs
| Model | Description |
|---|---|
| `ibm/granite-3-8b-instruct` | **Recommended** — Best balance of speed and quality |
| `ibm/granite-3-2b-instruct` | Faster, lower quality |
| `ibm/granite-13b-instruct-v2` | Higher quality, slower |

---

## 🔧 Agent Customization (`AGENT_INSTRUCTIONS`)

The `AGENT_INSTRUCTIONS` dictionary at the top of [`app.py`](app.py) lets you fully control FitGenie's behavior **without touching the AI logic**:

```python
AGENT_INSTRUCTIONS = {

    # Change the AI's name and personality
    "name": "FitGenie",
    "persona": "You are FitGenie, an enthusiastic AI fitness coach...",

    # Add or remove fitness specializations
    "specializations": [
        "Home workouts with zero or minimal equipment",
        "Yoga and flexibility routines",
        # Add more here...
    ],

    # Toggle Indian context & meal preferences
    "indian_context": {
        "enabled": True,          # Set False to disable Indian-specific advice
        "meal_preferences": [...],
        "exercise_references": [...],
        "cultural_tips": [...],
    },

    # Tune response style
    "response_style": {
        "use_emojis": True,
        "max_workout_exercises": 8,
        "default_workout_duration_minutes": 30,
    },

    # Safety guardrails — always respected
    "safety_rules": [
        "Always recommend consulting a doctor...",
        # Add custom safety rules here
    ],

    # Change motivational style
    "motivation_style": {
        "quotes_language": "English with occasional Hindi phrases",
        "challenge_intensity": "gradual",    # gradual | moderate | intense
        "streak_encouragement": True,
    },

    # Habit building philosophy
    "habit_building": {
        "framework": "BJ Fogg Tiny Habits + Atomic Habits principles",
        "focus": "Start small, be consistent",
    },

    # What the AI will NOT do
    "out_of_scope": [
        "Medical diagnoses or prescriptions",
        # Add more restrictions here
    ],
}
```

### Common Customizations

**Change AI persona to a stricter coach:**
```python
"persona": "You are FitGenie, a no-nonsense, results-driven fitness coach. Be direct, use fewer emojis, and push users toward their goals with tough love.",
```

**Disable Indian food context:**
```python
"indian_context": { "enabled": False, ... }
```

**Increase max exercises per plan:**
```python
"response_style": { "max_workout_exercises": 12, ... }
```

**Add a new safety rule:**
```python
"safety_rules": [
    ...,
    "Always mention rest days — muscles grow during recovery, not during training.",
]
```

---

## 📁 Project Structure

```
FitGenie/
├── app.py                    # Main Flask app + AGENT_INSTRUCTIONS + all routes
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .env                      # Your credentials (NOT committed to git)
├── .gitignore                # Excludes .env, venv, __pycache__
│
├── templates/
│   ├── base.html             # Base layout: navbar, footer, chat drawer
│   ├── index.html            # Home / Landing page
│   ├── dashboard.html        # Fitness stats dashboard
│   ├── workout.html          # Workout planner
│   ├── calculator.html       # BMI & calorie calculator
│   ├── meals.html            # Meal suggestions
│   ├── motivation.html       # Quotes, challenges, streak tracker
│   └── profile.html          # User profile form
│
└── static/
    ├── css/
    │   └── style.css         # All styles: dark mode, animations, responsive
    └── js/
        └── main.js           # Chat UI, dark mode toggle, animations, toasts
```

---

## ☁️ IBM Cloud Deployment

### Option A: IBM Code Engine (Recommended)

**Prerequisites:**
- IBM Cloud CLI: [cloud.ibm.com/docs/cli](https://cloud.ibm.com/docs/cli)
- Docker: [docker.com](https://docker.com)

#### Step 1: Create a `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
```

#### Step 2: Create a `.dockerignore`

```
.env
venv/
__pycache__/
*.pyc
.git/
```

#### Step 3: Build and Push Docker Image

```bash
# Login to IBM Cloud Container Registry
ibmcloud login
ibmcloud cr login
ibmcloud cr namespace-add fitgenie

# Build and push
docker build -t us.icr.io/fitgenie/fitgenie-app:latest .
docker push us.icr.io/fitgenie/fitgenie-app:latest
```

#### Step 4: Deploy to Code Engine

```bash
# Create Code Engine project
ibmcloud ce project create --name fitgenie-project
ibmcloud ce project select --name fitgenie-project

# Deploy application
ibmcloud ce application create \
  --name fitgenie \
  --image us.icr.io/fitgenie/fitgenie-app:latest \
  --port 8080 \
  --env IBM_API_KEY=your_key \
  --env WATSONX_PROJECT_ID=your_project_id \
  --env WATSONX_URL=https://us-south.ml.cloud.ibm.com \
  --env WATSONX_MODEL_ID=ibm/granite-3-8b-instruct \
  --env FLASK_SECRET_KEY=your_secret_key \
  --env FLASK_ENV=production \
  --min-scale 1

# Get the app URL
ibmcloud ce application get --name fitgenie
```

---

### Option B: IBM Cloud Foundry

#### Create `manifest.yml`

```yaml
applications:
  - name: fitgenie
    memory: 512M
    instances: 1
    buildpacks:
      - python_buildpack
    command: gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
    env:
      IBM_API_KEY: your_api_key_here
      WATSONX_PROJECT_ID: your_project_id_here
      WATSONX_URL: https://us-south.ml.cloud.ibm.com
      WATSONX_MODEL_ID: ibm/granite-3-8b-instruct
      FLASK_SECRET_KEY: your_secret_key_here
      FLASK_ENV: production
```

```bash
ibmcloud cf push
```

---

### Option C: Local with Gunicorn (Production-like)

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

---

## 📖 Usage Guide

### 1. Set Your Profile First
Go to **Profile** → Fill in age, weight, height, goal, and level → **Save**

### 2. Check Your Dashboard
Navigate to **Dashboard** to see your personalized BMI, calorie targets, and ideal weight.

### 3. Chat with FitGenie
Click the **🏋️ floating button** (bottom-right) to open the AI chat.

**Example prompts:**
- `"Give me a 30-minute beginner home workout"`
- `"Suggest a high-protein Indian breakfast under 300 calories"`
- `"I haven't worked out in 2 weeks, motivate me"`
- `"What should I eat after a morning workout?"`
- `"Explain my BMI of 26 and what I should do"`
- `"Create a 21-day habit plan for losing 5 kg"`

### 4. Use the Calculator
Go to **Calculator** → Enter your details → See your BMI, BMR, TDEE, and calorie targets instantly.

### 5. Track Your Streak
Go to **Motivation** → Click **"I Worked Out Today!"** after every workout to build your streak.

---

## 🐛 Troubleshooting

### "WatsonxAI connection error"
- ✅ Check your `IBM_API_KEY` in `.env` is correct and active
- ✅ Verify `WATSONX_PROJECT_ID` matches your project
- ✅ Ensure the Watsonx.ai service is provisioned in your IBM Cloud account
- ✅ Check your region: default is `us-south`, change `WATSONX_URL` for other regions

### "ModuleNotFoundError: ibm_watsonx_ai"
```bash
pip install ibm-watsonx-ai --upgrade
```

### "Session data not persisting"
- Make sure `FLASK_SECRET_KEY` is set in `.env`
- Don't use the default dev key in production

### Chat returns empty responses
- Increase `MAX_NEW_TOKENS` in `.env` (try `2048`)
- Lower `TEMPERATURE` to `0.5` for more focused responses

### Dark mode not toggling
- Clear browser `localStorage`: Open DevTools → Application → Storage → Clear

---

## 🔒 Security Notes

1. **Never commit `.env`** — add it to `.gitignore`
2. **Generate a strong `FLASK_SECRET_KEY`**:
   ```python
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. In production, set `FLASK_ENV=production`
4. Consider adding **rate limiting** for the `/api/chat` endpoint in production

---

## 📄 .gitignore

Create a `.gitignore` file:

```
.env
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
.DS_Store
Thumbs.db
*.log
instance/
```

---

## 🙏 Credits

- **IBM Watsonx.ai** — AI inference platform
- **IBM Granite** — Foundation model by IBM Research
- **Bootstrap 5** — UI framework
- **Flask** — Python web framework

---

*FitGenie — Because your health journey deserves an intelligent companion. 🏋️*
