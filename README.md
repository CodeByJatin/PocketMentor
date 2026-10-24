# Pocket Mentor

An autonomous AI Career Strategist and Daily Curriculum Architect. Powered by Google Gemini and Flask, Pocket Mentor converts broad career ambitions across any discipline into an intensive, sequential execution ladder with curated learning resources, date-synchronized industry intelligence, and real-time AI mentorship.

---

## Executive Overview: The Problem We Solve

Self-directed learners, career switchers, and ambitious practitioners face a persistent paradox: **infinite learning resources, but zero structured daily execution.**

- **The Flaw of Static Roadmaps**: Generic roadmaps provide static lists of topics without sequential prerequisites, daily time constraints, or verifiable deliverables.
- **Tutorial Hell**: Learners consume endless video courses and tutorials passively without building tangible, production-grade outputs.
- **Lack of Candid Evaluation**: Beginners lack honest, objective feedback on transferable skills, critical blind spots, and real market viability.

Pocket Mentor solves this by functioning as an autonomous personal career strategist. It diagnoses an individual's unique baseline, formulates a 6-month master architecture, and translates it into an unbroken chain of 30-day sequential execution missions.

---

## Core Benefits

### 1. Algorithmic Elimination of Tutorial Hell
Pocket Mentor converts passive consumption into active, verifiable engineering. Every single daily mission requires a concrete deliverable: a GitHub commit, an architecture spec, a configured pipeline, or a solved algorithmic kata.

### 2. Candid AI Reality Check & Unfair Advantage Diagnosis
Instead of superficial encouragement, the AI career strategist delivers a rigorous diagnosis:
- **Transferable Strengths**: Pinpoints existing skills that provide leverage in the target domain.
- **Critical Blind Spots**: Identifies foundational gaps that lead to rejection in hiring processes.
- **Strategic Trajectories**: Evaluates 3 distinct high-demand career pathways aligned with current market demand.

### 3. Zero-Cognitive-Overload Execution
Learners are never overwhelmed by broad, nebulous curriculum lists. Each morning presents:
- Exactly **one clear task** that builds directly on the previous day's work.
- One **authoritative primary source** (e.g. Official Documentation, LeetCode, GitHub, MDN, Real Python).
- Explicit, step-by-step instructions on how to use the assigned platform.
- An estimated time investment tailored to the user's daily availability.

### 4. Non-Linear Knowledge Gatekeeping
Month 2+ is strictly locked until 100% of Month 1 missions are completed. When generating subsequent months, the system injects past achievements and completed deliverables into the AI context, guaranteeing that topics are never redundantly repeated and difficulty scales naturally.

### 5. Date-Synchronized Domain Intelligence & Daily Momentum
- **Domain Pulse Engine**: Fetches and caches industry headlines tailored to the user's career track, upgrading automatically on calendar date rollover (`pulse_date == YYYY-MM-DD`).
- **Daily Action Directives**: Rotates through 31 hand-selected discipline and execution directives based on annual calendar day index (`tm_yday`).

### 6. Embedded Context-Aware Mentor Partner
A real-time AI companion available 24/7 directly on the dashboard. Operating with sub-2-second response latency, the mentor chatbot maintains real-time awareness of:
- The user's active streak and completion rate.
- The exact task and deliverables assigned for the current day.
- The user's underlying background, goals, and technical bottlenecks.

---

## Future Impact & Long-Term Vision

### 1. The Shift to Proof-of-Work Career Mobility
Traditional credentialing (diplomas, static certificates, standardized resumes) is rapidly losing relevance in favor of **verifiable proof of work**. Pocket Mentor's mission architecture builds a chronological, public record of deployed repositories, system designs, and code contributions that demonstrate actual competence to recruiters and engineering leads.

### 2. Autonomous Workforce Reskilling in the AI Era
As artificial intelligence rapidly transforms software engineering, operations, design, and analytics, millions of professionals must pivot into emerging specializations. Pocket Mentor democratizes elite executive career strategy, offering personalized, high-intensity retraining at zero cost without expensive bootcamps.

### 3. Continuous Skill Graph & Dual-Track Mastery
Future iterations of Pocket Mentor will introduce dynamic knowledge graphs:
- **Skill Overlap Deduplication**: When transitioning from one domain to another (e.g., Web Development to AI Systems), the platform automatically maps mastered skills and constructs an accelerated bridge curriculum.
- **Dual-Track Learning**: Concurrently balancing a primary core career track (75% focus) with a complementary secondary skill pillar (25% focus, such as Cloud Architecture or System Design).

### 4. Decentralized Global Accountability Pods
Expanding the platform to support peer accountability circles, matching learners worldwide who are progressing through the exact same month and track to share code reviews, daily check-ins, and collaborative project builds.

---

## System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                  USER ONBOARDING                                  |
|   Profile Genesis: Discipline, Experience, Primary Goal, Daily Hours, Narrative   |
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

## Technical Specifications

| Layer | Technology | Function |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+, Flask | Routing, session state, REST API endpoints |
| **Database** | SQLite3 | Relational ledger for users, profiles, roadmaps, and daily tasks |
| **AI Engine** | Google Gemini (`gemini-3.6-flash`, `gemini-2.5-flash`) | Structured JSON generation, career diagnosis, curriculum architecture |
| **Production WSGI** | Gunicorn | High-concurrency production server for cloud deployment |
| **Environment Management** | Python-Dotenv | Isolation of API keys and deployment configuration |
| **Frontend Architecture** | HTML5, CSS3 Glassmorphism, Vanilla JS | High-contrast, responsive interface built for deep focus |

---

## Database Architecture

```sql
-- User Authentication & Streak Tracking
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

-- Master 6-Month Milestone Blueprints
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

Pocket Mentor's Gemini inference client is built for high availability and sub-2-second turnaround:
- **Thinking Budget Zero**: Configured with `thinkingBudget: 0` to eliminate internal chain-of-thought latency.
- **Multi-Model Fallback Cascade**: Cascades automatically across `gemini-3.6-flash` -> `gemini-2.5-flash` -> `gemini-3-flash-preview` on rate limits or API service interruptions.
- **Quota-Aware Fast Failover**: Immediately fails over on HTTP 429 quota exhaustion without stalling execution loops.
- **Strict RFC 8259 Sanitization**: Cleans and strips markdown fences prior to deserialization to guarantee consistent JSON schema compliance.

---

## Getting Started

### Prerequisites
- Python 3.10+
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

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
Copy `.env.example` to `.env`:
```bash
# Windows PowerShell:
Copy-Item .env.example .env

# macOS/Linux:
cp .env.example .env
```

Open `.env` and set your credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
SECRET_KEY=pocket_mentor_production_secret_key_2026
```

### 5. Launch Application
```bash
python app.py
```
Open `http://localhost:5000` in your browser.

---

## Production Deployment on Render

Pocket Mentor is pre-configured for deployment on [Render](https://render.com) using Gunicorn:

1. Create a **New Web Service** connected to your repository.
2. Configure settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python init_db.py`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`
3. Add Environment Variables:
   - `GEMINI_API_KEY`: `your_actual_gemini_api_key`
   - `SECRET_KEY`: `your_random_secret_string`
   - `PYTHON_VERSION`: `3.10.12`
4. Click **Deploy Web Service**.

---

## Future Roadmap

- [ ] **Dual-Track Learning**: Balance a primary career path (75%) with a secondary technical pillar (25%).
- [ ] **Proof-of-Work Verification**: Attach GitHub commits, PRs, and live deployment links to daily deliverables.
- [ ] **Discipline Heatmap**: 365-day contribution grid measuring uninterrupted daily focus.
- [ ] **End-of-Month Capstone Boss Battles**: Deployable live application review required to unlock subsequent months.
- [ ] **Calendar Synchronization**: Direct export to Google Calendar, Notion, and Todoist.

---

## License

Distributed under the MIT License. Open source and community-driven.
