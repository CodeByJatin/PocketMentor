# Pocket Mentor

An autonomous AI career strategist and daily curriculum builder. Powered by Google Gemini and Flask, Pocket Mentor analyzes your background, creates a custom 6-month career roadmap, and breaks it down into sequential daily missions with multi-platform learning resources.

---

## Creator & Current Focus

- **Built By**: Jatin ([@CodeByJatin](https://github.com/CodeByJatin))
- **Background**: 2nd Year B.Tech in Automation and Robotics
- **Active Track**: AI & Machine Learning Engineering
- **Current Focus**: Mastering core ML fundamentals, autonomous systems, neural networks, and building production-grade AI-powered web applications.

---

## How It Works

Pocket Mentor turns career ambitions into a daily execution ladder in 4 simple steps:

1. **Profile Genesis**: Enter your background, experience level, daily time commitment, and primary career goals.
2. **Candid Diagnosis**: AI evaluates your strengths, highlights blind spots, and proposes 3 tailored career specializations.
3. **Master Blueprint**: Generates a 6-month roadmap with monthly milestone deliverables and authoritative sources.
4. **Daily Execution Ladder**: Breaks each month into 30 sequential daily missions paired with verified learning resources, active habit tracking, and an embedded AI Mentor Partner chatbot.

---

## Core Features

- **Sequential Daily Missions**: 30 daily tasks per month that strictly build on prior deliverables.
- **Strict Progression Gatekeeper**: Month 2 unlocks only upon 100% completion of Month 1, ensuring no repeated topics.
- **Curated Multi-Platform Resources**: Every mission pairs with primary documentation (LeetCode, GitHub, MDN, Real Python, Official Docs).
- **Daily Upgrading Industry News**: Real-time domain news headlines that refresh automatically each day based on calendar date.
- **Daily Action Directive**: Date-synchronized discipline and action quotes to maintain momentum.
- **Mentor Partner AI Chatbot**: An embedded AI chatbot aware of your current streak, daily mission, and learning history.
- **Clean Focus Interface**: High-contrast, executive glassmorphism UI designed for deep focus with zero distraction.

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask |
| **Database** | SQLite3 |
| **AI Model** | Google Gemini (`gemini-3.6-flash` / `gemini-2.5-flash`) |
| **Server** | Gunicorn (Production WSGI) |
| **Frontend** | HTML5, Modern CSS Glassmorphism, Vanilla JavaScript |

---

## Quick Start (3 Steps)

### 1. Clone & Set Up
```bash
git clone https://github.com/CodeByJatin/PocketMentor.git
cd PocketMentor
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey):
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
SECRET_KEY=your_secret_session_key
```

### 3. Run
```bash
python app.py
```
Open `http://localhost:5000` in your browser.

---

## Deploy to Render

Pocket Mentor is pre-configured for one-click deployment on Render:

1. Create a **New Web Service** connected to your GitHub repository.
2. Set configuration:
   - **Build Command**: `pip install -r requirements.txt && python init_db.py`
   - **Start Command**: `gunicorn app:app`
3. Add Environment Variable:
   - `GEMINI_API_KEY`: *(Your Google AI Studio API Key)*

---

## License

MIT License. Built by [Jatin](https://github.com/CodeByJatin).
