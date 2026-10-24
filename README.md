# Pocket Mentor AI

Pocket Mentor is an autonomous Personal Career Strategist and Daily Curriculum Architect. Built with Python, Flask, and Google Gemini Flash, it translates career ambitions across any discipline into an intensive, sequential execution ladder.

---

## Key Features

- **Universal Multi-Domain Alignment**: Tailored career blueprints for any discipline (Engineering, Data/AI, Product, Design, Finance, Business, Trades).
- **Candid Career Diagnosis**: Generates a high-impact reality check analyzing transferable strengths, critical blind spots, high-leverage career trajectories, and daily habits.
- **Dynamic Track Proposal**: Proposes three distinct, high-demand career pathways tailored specifically to individual background and goals, with support for custom specializations.
- **5–6 Month Master Blueprint**: Wide-screen milestone architecture breaking down monthly objectives, core competencies, concrete portfolio deliverables, and authoritative primary sources.
- **30-Day Sequential Prerequisite Ladder**: Breaks down each month into 30 sequential daily missions where each day directly builds on the prior day's deliverable.
- **Curated Multi-Platform Resources**: Every mission pairs specific tasks with recognized authoritative learning platforms (e.g. Official Documentation, LeetCode, GitHub, MDN, GeeksforGeeks, Real Python) and explicit platform instructions.
- **Strict Progression Gatekeeper**: Unlocks Month 2+ only after 100% completion of the active month, injecting past month accomplishments into the AI curriculum generator so topics never repeat.
- **Daily Upgrading Industry News**: Delivers concise industry news headlines with publisher source tags and direct links, updating automatically every day based on calendar date.
- **Daily Action Directive**: A date-synchronized motivational directive focusing on daily execution, discipline, and momentum.
- **Pocket Mentor Partner AI Chatbot**: An embedded AI companion chatbot delivering real-time, context-aware mentoring tailored to the user's active streak and daily mission with sub-2-second response latency.
- **Emoji-Free Executive Interface**: Professional, clean typography and responsive glassmorphism layout designed for deep focus.

---

## Tech Stack

- **Backend**: Python 3.10+, Flask
- **Database**: SQLite3
- **AI Engine**: Google Gemini API (`gemini-3.6-flash` / `gemini-2.5-flash` with zero thinking latency)
- **Frontend**: Responsive HTML5, CSS3 Glassmorphism, Vanilla JavaScript

---

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/CodeByJatin/PocketMentor.git
cd PocketMentor
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
python init_db.py
```

### 5. Configure Gemini API Key
Set your Gemini API key in `app.py` or as an environment variable:
```python
GEMINI_API_KEY = "your-gemini-api-key"
GEMINI_MODEL = "gemini-3.6-flash"
```

### 6. Run the Application
```bash
python app.py
```
Visit `http://127.0.0.1:5000` in your browser.

---

## License

This project is licensed under the MIT License.
