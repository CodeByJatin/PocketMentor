# Pocket Mentor

An autonomous AI Career Strategist and Daily Curriculum Architect. Built with Python, Flask, SQLite, and Google Gemini Flash, Pocket Mentor transforms broad career ambitions across any discipline into an intensive, sequential execution ladder with curated learning resources, daily industry intelligence, and real-time AI mentorship.

---

## Creator & Engineering Focus

- **Author**: Jatin ([@CodeByJatin](https://github.com/CodeByJatin))
- **Academic Background**: 2nd Year B.Tech in Automation and Robotics
- **Active Specialization**: AI & Machine Learning Systems
- **Core Engineering Focus**: Machine learning fundamentals, neural network architectures, autonomous robotics systems, and production-grade LLM agent orchestration.
- **Project Mission**: Bridge the divide between open-ended career ambitions and disciplined daily execution through deterministic milestone gatekeeping and intelligent, context-grounded AI coaching.

---

## Architecture & System Flow

```text
+-----------------------------------------------------------------------------------+
|                                  USER ONBOARDING                                  |
|   Profile Genesis (Discipline, Experience, Primary Goal, Daily Hours, Narrative)  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            CANDID AI CAREER DIAGNOSIS                             |
|    Transferable Strengths  |  Critical Blind Spots  |  3 High-Demand Track Options|
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                         5-6 MONTH MASTER ROADMAP ENGINE                           |
|        Monthly Milestone Objectives  |  Core Competencies  |  Portfolio Projects  |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     30-DAY SEQUENTIAL DAILY EXECUTION LADDER                      |
|  Day N builds on Day N-1  |  Mini Deliverables  |  Multi-Platform Authoritative Docs  |
|           Strict Month Gatekeeper (100% completion unlocks next month)            |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                                EXECUTIVE DASHBOARD                                |
|   - Daily Action Quote Engine (tm_yday deterministic rotation)                    |
|   - Domain Pulse News Engine (Date-synchronized industry headlines & links)       |
|   - Active Streak & Completion Metrics (Database-backed progress)                 |
|   - Pocket Mentor Partner AI (Embedded context-aware assistant, <2s latency)      |
+-----------------------------------------------------------------------------------+
```

---

## Key Technical Features

### 1. Dynamic Profile Genesis & Non-Destructive Calibration
- Captures granular user parameters: primary discipline, current stage, milestone target, daily commitment, preferred learning delivery, and detailed narrative.
- Non-destructive updates: Users can edit their background, goals, or time commitment at any time from the dashboard without wiping active roadmaps, task completion history, or streaks.

### 2. Candid AI Career Diagnosis & Tri-Track Recommendation
- Evaluates individual background narrative against real-world industry benchmarks.
- Produces an executive diagnosis detailing unfair strengths, high-leverage trajectories, critical skill bottlenecks, and foundational daily habits.
- Proposes three tailored, high-demand specializations with custom pathway support.

### 3. Wide-Screen Master Milestone Blueprint
- Generates a 5 to 6-month roadmap broken into distinct milestone chapters.
- Outlines monthly objectives, theoretical competencies, concrete portfolio deliverables, and primary documentation sources.

### 4. 30-Day Sequential Prerequisite Daily Curriculum Engine
- Deconstructs each month into 30 sequential daily missions where each day's task directly builds on the prior day's deliverable.
- Eliminates repetition: When generating Month 2+, past month accomplishments and completed deliverables are injected into the prompt context to ensure zero duplicated material.
- Strict Progression Gatekeeper: Month N+1 is hard-locked until 100% of Month N's tasks are verified and completed.

### 5. Multi-Platform Authoritative Resource Mapping
- Every daily mission is matched with recognized primary resources:
  - Official Documentation (Python, MDN, PyTorch, Docker, Kubernetes)
  - Interactive Problem-Solving (LeetCode, HackerRank)
  - Production Code Repositories (GitHub, Real Python, GeeksforGeeks)
- Pairs each task with explicit instructions on how to use the assigned platform.

### 6. Date-Synchronized Domain Pulse News System
- Automates live industry news headline fetching tailored to the user's selected career track.
- Uses date-keyed SQLite caching (`pulse_date == YYYY-MM-DD`): automatically updates on calendar date rollover while preventing redundant API calls throughout the day.
- Delivers clean headlines with verified publisher tags and direct links.

### 7. Deterministic Action Directive Engine
- Evaluates calendar day of the year (`date.today().timetuple().tm_yday`) to rotate through 31 hand-curated action and discipline quotes.
- Focused specifically on execution, momentum, and daily consistency.

### 8. Context-Aware Mentor Partner AI Chatbot
- Embedded AI companion styled with clean glassmorphism and sub-2-second response latency.
- Injects the user's active streak count, current day's mission, chosen specialization, and background narrative into each interaction for precise, context-grounded mentoring.

### 9. Distraction-Free Executive Interface
- Clean, responsive glassmorphism aesthetic built with semantic HTML5 and modern CSS variables.
- Free of emojis and juvenile gamification fluff, engineered for deep professional focus.

---

## Tech Stack & Architecture

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+, Flask | Application routing, session management, REST API endpoints |
| **Database** | SQLite3 | Relational persistence for user accounts, profiles, roadmaps, and tasks |
| **AI Inference** | Google Gemini (`gemini-3.6-flash`, `gemini-2.5-flash`) | Structured JSON generation, career diagnosis, curriculum architecture |
| **Production Server** | Gunicorn | Production WSGI HTTP Server for high-concurrency cloud environments |
| **Configuration** | Python-Dotenv | Environment-based credential isolation and configuration |
| **Frontend** | HTML5, CSS3 Glassmorphism, Vanilla JS | Responsive interface, asynchronous task updates, interactive chat |

---

## Database Schema Overview

```sql
-- Core User Account & Streak Ledger
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    streak_count INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_active_date TEXT,
    onboarding_completed INTEGER DEFAULT 0,
    chosen_career TEXT
);

-- Granular Profile Parameters & Narrative
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    about TEXT,
    about_narrative TEXT,
    chosen_career TEXT,
    primary_field TEXT,
    experience_level TEXT,
    primary_goal TEXT,
    time_commitment TEXT,
    learning_style TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Master 6-Month Blueprint
CREATE TABLE roadmaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    roadmap_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sequential 30-Day Daily Task Ledger
CREATE TABLE daily_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    month_number INTEGER DEFAULT 1,
    day_number INTEGER,
    week_number INTEGER DEFAULT 1,
    task TEXT,
    skill_focus TEXT,
    mission_brief TEXT,
    mini_output TEXT,
    reflection_question TEXT,
    completed INTEGER DEFAULT 0,
    resource_title TEXT,
    platform TEXT,
    platform_instruction TEXT,
    resource_url TEXT,
    resource_type TEXT,
    estimated_minutes TEXT,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Date-Keyed Industry Intelligence Cache
CREATE TABLE domain_pulses (
    user_id INTEGER PRIMARY KEY,
    pulse_json TEXT,
    pulse_date TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## AI Orchestration & Fault Tolerance

Pocket Mentor's Gemini inference client is engineered for low latency and high availability:
- **Thinking Budget Zero**: Configured with `thinkingBudget: 0` to eliminate internal chain-of-thought latency and return structured outputs in under 2 seconds.
- **Multi-Model Fallback Chain**: Automatically cascades from `gemini-3.6-flash` to `gemini-2.5-flash` to `gemini-3-flash-preview` on rate limits or service unavailability.
- **Quota-Aware Fast Failover**: Distinguishes between HTTP 429 quota exhaustion (immediate failover) and server load (exponential backoff).
- **Strict RFC 8259 JSON Generation**: Sanitizes raw LLM markdown artifacts and code fences before JSON deserialization, preventing syntax breaks.

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- A free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone the Repository
```bash
git clone https://github.com/CodeByJatin/PocketMentor.git
cd PocketMentor
```

### 2. Set Up Virtual Environment
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a local `.env` file in the root directory (based on `.env.example`):
```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS/Linux:
cp .env.example .env
```

Open `.env` and configure your credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
SECRET_KEY=pocket_mentor_session_secret_key_2026
```

### 5. Launch Application
```bash
python app.py
```
Open your browser and navigate to `http://localhost:5000`.

---

## Production Deployment on Render

Pocket Mentor is ready for zero-downtime deployment on [Render](https://render.com) using Gunicorn.

1. Create a new **Web Service** on Render and connect your GitHub repository (`CodeByJatin/PocketMentor`).
2. Configure service specifications:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python init_db.py`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`
3. Add Environment Variables in Render:
   - `GEMINI_API_KEY`: `your_actual_gemini_api_key`
   - `SECRET_KEY`: `a_strong_random_secret_string`
   - `PYTHON_VERSION`: `3.10.12`
4. Click **Deploy Web Service**.

---

## Future Roadmap

- [ ] **Dual-Track Learning**: Concurrently pursue a Primary Career Track (75% focus) and a Secondary Skill Pillar (25% focus).
- [ ] **Proof-of-Work Submissions**: Attach GitHub commits, PRs, and live deployment links to each day's task.
- [ ] **Discipline Heatmap**: 365-day GitHub-style consistency grid visualizing daily focus intensity.
- [ ] **End-of-Month Capstone Battles**: Deployable project evaluation required to unlock subsequent months.
- [ ] **Calendar Synchronization**: One-click curriculum export to Google Calendar, Notion, and Todoist.

---

## License

Distributed under the MIT License. Developed and maintained by [Jatin](https://github.com/CodeByJatin).
