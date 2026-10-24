from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import requests
import markdown
import json
import re
import urllib.parse
import time
import os
from datetime import date, datetime, timedelta
from init_db import init_db

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAyrghdEBHqvfhd5HXwp0o2bzl5FHQWxWM")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pocket_mentor_production_secret_key_2026")

DATABASE = "users.db"
init_db(DATABASE)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS domain_pulses (
            user_id INTEGER PRIMARY KEY,
            pulse_json TEXT,
            pulse_date TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        conn.execute("ALTER TABLE profiles ADD COLUMN about_narrative TEXT")
        conn.commit()
    except Exception:
        pass
    return conn

def call_gemini_api(prompt, json_mode=False, max_output_tokens=8192, temperature=0.2):
    """High-speed Gemini Client with zero-latency thinking budget, quota-aware fast failover, and fallback models."""
    models_to_try = [GEMINI_MODEL, "gemini-2.5-flash", "gemini-3-flash-preview"]
    
    gen_config = {
        "temperature": temperature,
        "maxOutputTokens": max_output_tokens,
        "thinkingConfig": {"thinkingBudget": 0}
    }
    if json_mode:
        gen_config["responseMimeType"] = "application/json"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config
    }

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        for attempt in range(2):
            try:
                res = requests.post(url, json=payload, timeout=40)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        output_text = "".join([p.get("text", "") for p in parts if "text" in p]).strip()
                        if output_text:
                            return output_text
                elif res.status_code == 429:
                    err_lower = res.text.lower()
                    if "quota" in err_lower or "exceeded" in err_lower:
                        # Model quota exceeded; immediately fail over to next model without wasting time sleeping
                        break
                    time.sleep(1)
                elif res.status_code == 503:
                    time.sleep(1)
                else:
                    print(f"Gemini API ({model}) {res.status_code}: {res.text[:150]}")
                    break
            except Exception as e:
                print(f"Gemini API attempt {attempt+1} ({model}) exception: {e}")
                time.sleep(0.5)

    return ""

def clean_json_response(raw_text):
    if not raw_text:
        return {}
    text = raw_text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
    start_idx = min([i for i in [text.find('{'), text.find('[')] if i != -1], default=-1)
    end_idx = max([text.rfind('}'), text.rfind(']')], default=-1)
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        text = text[start_idx:end_idx+1]
    
    try:
        return json.loads(text, strict=False)
    except Exception:
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
        try:
            return json.loads(cleaned, strict=False)
        except Exception:
            cleaned2 = re.sub(r'\\([^"\\/bfnrtu])', r'\1', cleaned)
            try:
                return json.loads(cleaned2, strict=False)
            except Exception:
                return {}

def build_platform_url(platform, query):
    plat_lower = platform.lower()
    q = urllib.parse.quote(query)
    if "python.org" in plat_lower or "docs.python" in plat_lower:
        return f"https://docs.python.org/3/search.html?q={q}"
    elif "geeks" in plat_lower:
        return f"https://www.geeksforgeeks.org/search/?q={q}"
    elif "overthewire" in plat_lower or "bandit" in plat_lower:
        return "https://overthewire.org/wargames/bandit/"
    elif "leetcode" in plat_lower:
        return f"https://leetcode.com/problemset/?search={q}"
    elif "mdn" in plat_lower:
        return f"https://developer.mozilla.org/en-US/search?q={q}"
    elif "github" in plat_lower:
        return f"https://github.com/search?q={q}"
    elif "kaggle" in plat_lower:
        return f"https://www.kaggle.com/search?q={q}"
    elif "figma" in plat_lower:
        return f"https://www.figma.com/community/search?resource_type=mixed&sort_by=relevancy&query={q}"
    elif "behance" in plat_lower:
        return f"https://www.behance.net/search/projects?search={q}"
    elif "coursera" in plat_lower:
        return f"https://www.coursera.org/search?query={q}"
    elif "youtube" in plat_lower:
        return f"https://www.youtube.com/results?search_query={q}"
    elif "investopedia" in plat_lower:
        return f"https://www.investopedia.com/search?q={q}"
    elif "freecodecamp" in plat_lower:
        return f"https://www.freecodecamp.org/news/search/?query={q}"
    elif "stackoverflow" in plat_lower or "stack overflow" in plat_lower:
        return f"https://stackoverflow.com/search?q={q}"
    else:
        return f"https://www.google.com/search?q={q}+{urllib.parse.quote(platform)}"

def parse_daily_tasks(raw_text, chosen_career, start_day=1, month_num=1):
    """Universal parser that extracts 30 sequential days for ANY domain."""
    extracted = []
    
    try:
        data = clean_json_response(raw_text)
        if isinstance(data, dict) and "days" in data and isinstance(data["days"], list) and len(data["days"]) > 0:
            extracted = data["days"]
        elif isinstance(data, list) and len(data) > 0:
            extracted = data
    except Exception:
        pass

    if not extracted:
        blocks = re.findall(r'\{[^{}]*?"day"\s*:\s*\d+[\s\S]*?\}', raw_text)
        for b in blocks:
            day_m = re.search(r'"day"\s*:\s*(\d+)', b)
            if day_m:
                d_num = int(day_m.group(1))
                w_num = ((d_num - 1) // 7) + 1
                task_m = re.search(r'"task"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                skill_m = re.search(r'"skill_focus"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                brief_m = re.search(r'"mission_brief"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                mini_m = re.search(r'"mini_output"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                ref_m = re.search(r'"reflection_question"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                res_m = re.search(r'"resource_title"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                plat_m = re.search(r'"platform"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                instr_m = re.search(r'"platform_instruction"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                url_m = re.search(r'"resource_url"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                type_m = re.search(r'"resource_type"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)
                est_m = re.search(r'"estimated_minutes"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', b)

                task_val = task_m.group(1) if task_m else f"Day {d_num}: {chosen_career} Step"
                skill_val = skill_m.group(1) if skill_m else f"{chosen_career} Competency"
                plat_val = plat_m.group(1) if plat_m else "Official Documentation"
                r_url = url_m.group(1) if (url_m and url_m.group(1).startswith("http")) else build_platform_url(plat_val, task_val)

                extracted.append({
                    "day": d_num,
                    "week": w_num,
                    "task": task_val,
                    "skill_focus": skill_val,
                    "mission_brief": brief_m.group(1) if brief_m else f"Prerequisite step for Day {d_num + 1} progression in {chosen_career}.",
                    "mini_output": mini_m.group(1) if mini_m else f"Complete Day {d_num} hands-on task and verify results.",
                    "reflection_question": ref_m.group(1) if ref_m else "What key concept was learned and how does it connect to the goal?",
                    "resource_title": res_m.group(1) if res_m else f"{task_val} Guide",
                    "platform": plat_val,
                    "platform_instruction": instr_m.group(1) if instr_m else f"Study tutorial on {plat_val} and execute practice steps.",
                    "resource_type": type_m.group(1) if type_m else "Practical Guide",
                    "resource_url": r_url,
                    "estimated_minutes": est_m.group(1) if est_m else "35 mins"
                })

    # Defensive check: if start_day > 1 (e.g. Month 2 start_day=31) but LLM numbered days starting from 1
    if start_day > 1 and extracted and max(d.get("day", 1) for d in extracted) <= 30:
        for d in extracted:
            d["day"] = d["day"] + (start_day - 1)
            d["week"] = ((d["day"] - 1) // 7) + 1

    # Universal 30-day sequential progression
    target_end = start_day + 29
    existing_day_nums = {d.get("day") for d in extracted}
    
    stages = [
        ("Foundational Concepts & Core Workflow", "Master core principles and initial tools essential for subsequent modules."),
        ("Applied Skills & Practical Analysis", "Execute intermediate hands-on exercises and solve domain-specific challenges."),
        ("Advanced Synthesis & Case Studies", "Design structured projects and examine production-grade methodologies."),
        ("Capstone Milestone & Synthesis", "Build a verifiable capstone project and document comprehensive insights.")
    ]

    for d in range(start_day, target_end + 1):
        if d not in existing_day_nums:
            step_in_month = d - start_day
            stage_idx = min(step_in_month // 7, 3)
            stage_name, stage_desc = stages[stage_idx]
            w_num = ((d - 1) // 7) + 1
            extracted.append({
                "day": d,
                "week": w_num,
                "task": f"Day {d}: {chosen_career} — {stage_name} (Module {(step_in_month % 7) + 1})",
                "skill_focus": f"{chosen_career}: {stage_name}",
                "mission_brief": f"{stage_desc} Prerequisite for Day {d + 1}.",
                "mini_output": f"Construct Day {d} deliverable and document key takeaways.",
                "reflection_question": f"How does Day {d} build on earlier foundations?",
                "resource_title": f"{chosen_career} {stage_name} Guide",
                "platform": "Industry Documentation",
                "platform_instruction": f"Read documentation on {chosen_career} fundamentals and complete exercises.",
                "resource_type": "Interactive Guide",
                "resource_url": build_platform_url("Official Guide", f"{chosen_career} {stage_name}"),
                "estimated_minutes": "35 mins"
            })

    extracted = [d for d in extracted if start_day <= d.get("day", 0) <= target_end]
    extracted.sort(key=lambda x: x.get("day", start_day))
    return extracted[:30]


def get_onboarding_step(user_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT about, chosen_career FROM profiles WHERE user_id=?", (user_id,))
    profile = cursor.fetchone()
    if not profile or not profile["about"]:
        conn.close()
        return "create_profile"

    cursor.execute("SELECT id FROM career_suggestions WHERE user_id=?", (user_id,))
    career = cursor.fetchone()
    if not career:
        conn.close()
        return "career"

    cursor.execute("SELECT chosen_career, onboarding_completed FROM users WHERE id=?", (user_id,))
    u = cursor.fetchone()
    chosen_career = (u["chosen_career"] if u else None) or profile["chosen_career"]
    if not chosen_career:
        conn.close()
        return "choose_career"

    cursor.execute("SELECT id FROM roadmaps WHERE user_id=?", (user_id,))
    roadmap = cursor.fetchone()
    if not roadmap:
        conn.close()
        return "roadmap"

    cursor.execute("SELECT COUNT(*) as count FROM daily_tasks WHERE user_id=?", (user_id,))
    task_count = cursor.fetchone()["count"]
    if task_count == 0:
        conn.close()
        return "start_roadmap"

    if u and not u["onboarding_completed"]:
        conn.close()
        return "start_roadmap"

    conn.close()
    return "dashboard"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        action = request.form["action"]

        conn = get_db()
        cursor = conn.cursor()

        if action == "register":
            try:
                cursor.execute(
                    "INSERT INTO users (username, password, streak_count, longest_streak, onboarding_completed) VALUES (?, ?, 0, 0, 0)",
                    (username, password)
                )
                conn.commit()
                cursor.execute("SELECT id FROM users WHERE username=?", (username,))
                user_id = cursor.fetchone()["id"]
                conn.close()
                session["user"] = username
                step = get_onboarding_step(user_id)
                return redirect(url_for(step))
            except Exception:
                conn.close()
                return render_template("index.html", error="Username already exists. Try logging in.", mode="register")

        if action == "login":
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )
            user = cursor.fetchone()
            conn.close()

            if user:
                session["user"] = username
                step = get_onboarding_step(user["id"])
                return redirect(url_for(step))
            else:
                return render_template("index.html", error="Invalid username or password. Please try again.", mode="login")

    if "user" in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (session["user"],))
        user = cursor.fetchone()
        conn.close()
        if user:
            step = get_onboarding_step(user["id"])
            return redirect(url_for(step))

    return render_template("index.html")


@app.route("/create_profile", methods=["GET", "POST"])
def create_profile():
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, onboarding_completed, chosen_career FROM users WHERE username=?", (session["user"],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        session.clear()
        return redirect(url_for("index"))
    user_id = user_row["id"]
    is_onboarded = bool(user_row["onboarding_completed"])
    chosen_career = user_row["chosen_career"]

    if request.method == "POST":
        action_type = request.form.get("action_type", "save")
        primary_field = request.form.get("primary_field", "").strip()
        experience_level = request.form.get("experience_level", "").strip()
        primary_goal = request.form.get("primary_goal", "").strip()
        time_commitment = request.form.get("time_commitment", "").strip()
        learning_style = request.form.get("learning_style", "").strip()
        narrative = (request.form.get("about_narrative") or request.form.get("about") or "").strip()

        about_parts = []
        if primary_field:
            about_parts.append(f"• Primary Discipline / Field: {primary_field}")
        if experience_level:
            about_parts.append(f"• Current Experience Level: {experience_level}")
        if primary_goal:
            about_parts.append(f"• Core Objective / Target: {primary_goal}")
        if time_commitment:
            about_parts.append(f"• Daily Time Commitment: {time_commitment}")
        if learning_style:
            about_parts.append(f"• Preferred Learning Mode: {learning_style}")
        if narrative:
            about_parts.append(f"\nBackground & Specific Details:\n{narrative}")

        combined_about = "\n".join(about_parts).strip()
        if not combined_about:
            combined_about = "Practitioner seeking strategic career guidance and daily sequential milestones."

        cursor.execute("DELETE FROM profiles WHERE user_id=?", (user_id,))
        cursor.execute("""
            INSERT INTO profiles (user_id, about, primary_field, experience_level, primary_goal, time_commitment, learning_style, about_narrative)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, combined_about, primary_field, experience_level, primary_goal, time_commitment, learning_style, narrative))

        if is_onboarded and action_type != "recalibrate":
            conn.commit()
            conn.close()
            return redirect(url_for("dashboard"))

        cursor.execute("DELETE FROM career_suggestions WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM roadmaps WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM daily_tasks WHERE user_id=?", (user_id,))
        cursor.execute("UPDATE users SET chosen_career=NULL, onboarding_completed=0 WHERE id=?", (user_id,))

        conn.commit()
        conn.close()

        return redirect(url_for("career"))

    cursor.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,))
    profile = cursor.fetchone()

    narrative = ""
    selected_field = ""
    selected_experience = ""
    selected_goal = ""
    selected_commitment = ""
    selected_learning_style = ""

    if profile:
        profile_dict = dict(profile)
        if profile_dict.get("about_narrative"):
            narrative = profile_dict["about_narrative"]
        elif profile_dict.get("about"):
            raw_about = profile_dict["about"]
            if "Background & Specific Details:" in raw_about:
                narrative = raw_about.split("Background & Specific Details:", 1)[1].strip()
            elif "• Primary Discipline / Field:" in raw_about:
                lines = [l for l in raw_about.splitlines() if not l.strip().startswith("•")]
                narrative = "\n".join(lines).strip()
            else:
                narrative = raw_about.strip()

        selected_field = profile_dict.get("primary_field") or ""
        selected_experience = profile_dict.get("experience_level") or ""
        selected_goal = profile_dict.get("primary_goal") or ""
        selected_commitment = profile_dict.get("time_commitment") or ""
        selected_learning_style = profile_dict.get("learning_style") or ""

    if not selected_field and chosen_career:
        cc = chosen_career.lower()
        if "ai" in cc or "machine learning" in cc or "data" in cc:
            selected_field = "AI, Machine Learning & Data Science"
        elif "design" in cc or "ux" in cc or "ui" in cc:
            selected_field = "UI/UX & Product Design"
        elif "product" in cc:
            selected_field = "Product Management & Tech Strategy"
        elif "security" in cc or "cyber" in cc:
            selected_field = "Cybersecurity & Systems Administration"
        elif "finance" in cc or "venture" in cc or "business" in cc:
            selected_field = "Business, Finance & Venture Operations"
        elif "marketing" in cc or "growth" in cc:
            selected_field = "Marketing, Brand & Growth Engineering"
        elif "web" in cc or "software" in cc or "engineer" in cc or "fullstack" in cc or "backend" in cc:
            selected_field = "Software Engineering & Web Systems"

    conn.close()
    return render_template(
        "profile.html",
        profile=profile,
        narrative=narrative,
        is_onboarded=is_onboarded,
        selected_field=selected_field,
        selected_experience=selected_experience,
        selected_goal=selected_goal,
        selected_commitment=selected_commitment,
        selected_learning_style=selected_learning_style
    )


@app.route("/career")
def career():
    """Universal Career Strategist Prompt (Works for ANY domain: Tech, Creative, Business, Finance, etc.)"""
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, onboarding_completed FROM users WHERE username=?", (session["user"],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        session.clear()
        return redirect(url_for("index"))
    user_id = user_row["id"]
    is_onboarded = bool(user_row["onboarding_completed"])

    cursor.execute("""
        SELECT suggestion_json FROM career_suggestions
        WHERE user_id=?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    existing = cursor.fetchone()

    if existing:
        html_output = markdown.markdown(existing["suggestion_json"])
        conn.close()
        return render_template("career.html", username=session["user"], result=html_output, is_onboarded=is_onboarded)

    cursor.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,))
    profile = cursor.fetchone()

    if not profile:
        conn.close()
        return redirect(url_for("create_profile"))

    prompt = f"""
You are an elite, perceptive Personal Career Strategist and Life Mastery Mentor.
The user may be pursuing ANY field (such as Technology, Design, Business, Marketing, Finance, Sciences, Arts, or Trades).
Analyze their background, skills, and ambitions honestly:

{profile['about']}

Deliver a high-impact, candid, and inspiring career strategy blueprint in this exact markdown structure:

### 1. Mindset & Reality Check
A sharp, honest 2-sentence evaluation of their current mindset, approach, and what will cause them to stall if they do not adapt.

### 2. Defensible Strengths & Unfair Advantages
- Bullet points highlighting genuine, transferable strengths or promising baseline qualities they possess.

### 3. Critical Blind Spots (What Will Block Your Success)
- Candid warning points on habits, knowledge gaps, or assumptions that will hinder their progress.

### 4. Top 2 High-Leverage Career Trajectories
- **Option A:** Specific, high-demand career pathway tailored to their profile with clear market rationale.
- **Option B:** Alternative viable high-growth pathway.

### 5. High-Leverage Daily Habits & Focus Areas
- 3 non-negotiable daily principles to transition from passive learning to proactive, tangible mastery.
"""

    output = call_gemini_api(prompt, json_mode=False, max_output_tokens=4096, temperature=0.3)
    if not output:
        output = "Career analysis generation temporarily unavailable. Please try again."

    html_output = markdown.markdown(output)

    cursor.execute("""
        INSERT INTO career_suggestions (user_id, suggestion_json)
        VALUES (?, ?)
    """, (user_id, output))

    conn.commit()
    conn.close()

    return render_template("career.html", username=session["user"], result=html_output, is_onboarded=is_onboarded)


@app.route("/choose_career", methods=["GET", "POST"])
def choose_career():
    """Universal Career Selection: Dynamically suggests 3 tailored tracks for ANY domain."""
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username=?", (session["user"],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        session.clear()
        return redirect(url_for("index"))
    user_id = user_row["id"]

    if request.method == "POST":
        custom = (request.form.get("custom_career") or "").strip()
        standard = (request.form.get("career_choice") or "").strip()
        career_choice = custom if custom else (standard or "Professional Specialist")
        
        cursor.execute("UPDATE users SET chosen_career=? WHERE id=?", (career_choice, user_id))
        cursor.execute("UPDATE profiles SET chosen_career=? WHERE user_id=?", (career_choice, user_id))
        
        cursor.execute("DELETE FROM roadmaps WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM daily_tasks WHERE user_id=?", (user_id,))

        conn.commit()
        conn.close()

        return redirect(url_for("roadmap"))

    cursor.execute("SELECT about FROM profiles WHERE user_id=?", (user_id,))
    p = cursor.fetchone()
    about_text = p["about"] if p else ""

    # Call AI to dynamically propose 3 tailored pathways for ANY domain
    prompt = f"""
Based on this individual's background:
{about_text}

Propose 3 distinct, high-leverage career trajectories tailored specifically to their interests.
Return ONLY valid JSON matching:
{{
  "tracks": [
    {{"title": "Specific Pathway Title", "desc": "1-sentence description of the specialization and market demand."}}
  ]
}}
Provide exactly 3 options. Pure RFC 8259 JSON only.
"""
    suggested_tracks = []
    try:
        raw_output = call_gemini_api(prompt, json_mode=True, max_output_tokens=2048, temperature=0.3)
        res_data = clean_json_response(raw_output)
        suggested_tracks = res_data.get("tracks", [])
    except Exception:
        pass

    if not suggested_tracks:
        suggested_tracks = [
            {"title": "High-Impact Specialist", "desc": "Develop depth in core fundamentals and industry-standard workflows."},
            {"title": "Cross-Functional Practitioner", "desc": "Bridge strategic planning, execution, and practical deliverables."},
            {"title": "Autonomous Creator / Builder", "desc": "Deliver end-to-end projects with independent accountability."}
        ]

    conn.close()
    return render_template("choose_career.html", suggested_tracks=suggested_tracks)


@app.route("/roadmap")
def roadmap():
    """Universal 5–6 Month Master Roadmap for ANY chosen goal."""
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, chosen_career FROM users WHERE username=?", (session["user"],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        session.clear()
        return redirect(url_for("index"))
    user_id = user_row["id"]
    chosen_career = user_row["chosen_career"] or "Specialist Track"

    cursor.execute("SELECT DISTINCT month_number FROM daily_tasks WHERE user_id=? ORDER BY month_number ASC", (user_id,))
    months_rows = cursor.fetchall()
    unlocked_months = [r["month_number"] for r in months_rows] if months_rows else [1]
    active_month = max(unlocked_months)

    cursor.execute("""
        SELECT roadmap_json FROM roadmaps
        WHERE user_id=?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    existing = cursor.fetchone()

    if existing:
        try:
            roadmap_data = json.loads(existing["roadmap_json"])
            conn.close()
            return render_template("roadmap.html",
                                   username=session["user"],
                                   roadmap=roadmap_data,
                                   chosen_career=chosen_career,
                                   unlocked_months=unlocked_months,
                                   active_month=active_month)
        except Exception:
            pass

    cursor.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,))
    profile = cursor.fetchone()

    if not profile:
        conn.close()
        return redirect(url_for("create_profile"))

    prompt = f"""
You are an expert Strategic Career & Curriculum Architect.
Target Goal: {chosen_career}
Individual Profile: {profile['about']}

Design an intensive, step-by-step 5 to 6-month Master Roadmap for {chosen_career}.
Each month must represent a progressive milestone that strictly builds upon the previous month.
Avoid domain-specific assumptions (adapt completely to the target field, whether tech, creative, business, or trades).

Return ONLY valid JSON matching this exact structure:
{{
  "title": "{chosen_career} Master Blueprint",
  "overview": "From foundational core principles to advanced autonomous mastery.",
  "months": [
    {{
      "month": 1,
      "title": "Month 1 Milestone Title",
      "goal": "Core objective for month 1",
      "skills": ["Skill 1", "Skill 2", "Skill 3"],
      "projects": ["Concrete Milestone Deliverable"],
      "resources": ["Key reputable learning platform or definitive documentation"]
    }}
  ]
}}
Provide 5 to 6 progressive months. Pure RFC 8259 JSON only.
"""

    try:
        raw_output = call_gemini_api(prompt, json_mode=True, max_output_tokens=4096, temperature=0.2)
        roadmap_data = clean_json_response(raw_output)
        if not roadmap_data or not isinstance(roadmap_data, dict) or "months" not in roadmap_data:
            roadmap_data = {
                "title": f"{chosen_career} Master Blueprint",
                "overview": "From foundational core principles to advanced autonomous mastery.",
                "months": [
                    {
                        "month": m,
                        "title": f"Month {m}: Core Progression Phase {m}",
                        "goal": f"Mastery of Stage {m} techniques and practical deliverables in {chosen_career}.",
                        "skills": [f"{chosen_career} Fundamentals", f"Applied Practice {m}", f"Milestone Execution {m}"],
                        "projects": [f"Month {m} Practical Portfolio Deliverable"],
                        "resources": ["Official Documentation & Industry Standards"]
                    }
                    for m in range(1, 7)
                ]
            }
    except Exception as e:
        conn.close()
        return f"Roadmap generation failed: {str(e)}"

    cursor.execute("""
        INSERT INTO roadmaps (user_id, roadmap_json)
        VALUES (?, ?)
    """, (user_id, json.dumps(roadmap_data)))

    conn.commit()
    conn.close()

    return render_template("roadmap.html",
                           username=session["user"],
                           roadmap=roadmap_data,
                           chosen_career=chosen_career,
                           unlocked_months=unlocked_months,
                           active_month=active_month)


@app.route("/start_roadmap")
def start_roadmap():
    """Universal Month 1 Action Plan (Days 1 to 30) with Diverse, Reputable Platforms."""
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, chosen_career, streak_count, longest_streak FROM users WHERE username=?", (session["user"],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        session.clear()
        return redirect(url_for("index"))
    user_id = user_row["id"]
    chosen_career = user_row["chosen_career"] or "Specialist Track"
    streak_count = user_row["streak_count"] or 0
    longest_streak = user_row["longest_streak"] or 0

    # Fetch all existing months for this user
    cursor.execute("SELECT DISTINCT month_number FROM daily_tasks WHERE user_id=? ORDER BY month_number ASC", (user_id,))
    months_rows = cursor.fetchall()
    unlocked_months = [r["month_number"] for r in months_rows] if months_rows else [1]
    max_unlocked_month = max(unlocked_months)

    # Get requested month filter or default to current active month
    req_month = request.args.get("month", type=int)
    if not req_month or req_month not in unlocked_months:
        req_month = max_unlocked_month

    # Check if max_unlocked_month is 100% completed
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) as comp FROM daily_tasks WHERE user_id=? AND month_number=?", (user_id, max_unlocked_month))
    max_stats = cursor.fetchone()
    max_total = max_stats["total"] or 0
    max_comp = max_stats["comp"] or 0
    can_unlock_next = (max_total > 0 and max_comp == max_total and max_unlocked_month < 6)
    next_month_num = max_unlocked_month + 1

    cursor.execute("""
        SELECT * FROM daily_tasks
        WHERE user_id=? AND month_number=?
        ORDER BY day_number ASC
    """, (user_id, req_month))
    existing_days = cursor.fetchall()

    if existing_days:
        daily_data = {
            "days": [
                {
                    "id": row["id"],
                    "month": row["month_number"],
                    "day": row["day_number"],
                    "week": row["week_number"] or (((row["day_number"] - 1) // 7) + 1),
                    "task": row["task"],
                    "skill_focus": row["skill_focus"],
                    "mission_brief": row["mission_brief"] or f"Direct sequential step for Day {row['day_number'] + 1} in {chosen_career}.",
                    "mini_output": row["mini_output"],
                    "reflection_question": row["reflection_question"],
                    "completed": row["completed"],
                    "resource_title": row["resource_title"] or f"{row['task']} Guide",
                    "platform": row["platform"] or "Official Documentation",
                    "platform_instruction": row["platform_instruction"] or f"Study resource on {row['platform']} and complete the practical output.",
                    "resource_url": row["resource_url"] or build_platform_url(row["platform"] or "Documentation", row["task"]),
                    "resource_type": row["resource_type"] or "Practical Guide",
                    "estimated_minutes": row["estimated_minutes"] or "35 mins"
                }
                for row in existing_days
            ]
        }
        completed_count = sum(1 for d in daily_data["days"] if d["completed"] == 1)
        conn.close()
        return render_template("daily_roadmap.html",
                               username=session["user"],
                               roadmap=daily_data,
                               streak_count=streak_count,
                               longest_streak=longest_streak,
                               completed_count=completed_count,
                               total_tasks=len(daily_data["days"]),
                               chosen_career=chosen_career,
                               current_month=req_month,
                               unlocked_months=unlocked_months,
                               max_unlocked_month=max_unlocked_month,
                               can_unlock_next=can_unlock_next,
                               next_month_num=next_month_num,
                               need_completion=(request.args.get("need_completion") == "true"))

    # Generate Month 1 if no tasks exist
    cursor.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,))
    profile = cursor.fetchone()

    if not profile:
        conn.close()
        return redirect(url_for("create_profile"))

    prompt = f"""
You are an expert personal learning mentor and curriculum architect.
Target Career / Discipline: {chosen_career}
User Background: {profile['about']}

Design Month 1 as a strictly sequential, ladder-like 30-day curriculum (Day 1 to Day 30).
EVERY SINGLE DAY MUST BE A DIRECT PREREQUISITE FOR THE NEXT. No scattered or disconnected tasks.
- Week 1: Foundational building blocks, basic vocabulary, and initial setup.
- Week 2: Core techniques, primary data manipulation, and essential workflows.
- Week 3: Intermediate application, practical synthesis, and problem solving.
- Week 4: Month 1 Capstone project, verification, and end-to-end review.

PLATFORM DIVERSITY RULE:
Select recognized, authoritative learning platforms and primary sources best suited for {chosen_career} (e.g. for Tech: Official Docs, LeetCode, OverTheWire, MDN Docs, GitHub, GeeksforGeeks; for Design: Figma Community, Behance, Nielsen Norman Group; for Business/Finance: SEC EDGAR, Harvard Business Review, Investopedia; for General: Coursera, edX, official documentation).
For EVERY single day, provide explicit "platform_instruction" detailing EXACTLY what the user must read, run, analyze, or build on that platform.

Return ONLY valid JSON matching:
{{
  "days": [
    {{
      "day": 1,
      "task": "Sequential task name (e.g. Core Foundations & Environment Setup)",
      "skill_focus": "Specific skill",
      "mission_brief": "Why this day is the exact prerequisite for Day 2.",
      "mini_output": "Concrete 15-minute verifiable output",
      "reflection_question": "Understanding check question",
      "resource_title": "Tutorial or documentation title",
      "platform": "Recognized Platform Name",
      "platform_instruction": "Exact step-by-step instruction on what to read or execute.",
      "resource_type": "Interactive Guide / Video / Lab",
      "resource_url": "https://...",
      "estimated_minutes": "35 mins"
    }}
  ]
}}
Pure RFC 8259 JSON only.
"""

    try:
        raw_output = call_gemini_api(prompt, json_mode=True, max_output_tokens=8192, temperature=0.2)
        days_list = parse_daily_tasks(raw_output, chosen_career, start_day=1, month_num=1)
    except Exception as e:
        conn.close()
        return f"Daily Roadmap generation failed: {str(e)}"

    for day in days_list:
        d_num = day.get("day", 1)
        w_num = day.get("week") or (((d_num - 1) // 7) + 1)
        task_name = day.get("task", f"Day {d_num} Mission")
        skill = day.get("skill_focus", chosen_career)
        brief = day.get("mission_brief", f"Prerequisite step for Day {d_num + 1} in {chosen_career}.")
        plat = day.get("platform", "Documentation")
        instr = day.get("platform_instruction", f"Complete interactive exercises on {plat}.")
        q_url = day.get("resource_url")
        if not q_url or not q_url.startswith("http"):
            q_url = build_platform_url(plat, task_name)

        cursor.execute("""
            INSERT INTO daily_tasks
            (user_id, month_number, day_number, week_number, task, skill_focus, mission_brief, mini_output, reflection_question, completed, resource_title, platform, platform_instruction, resource_url, resource_type, estimated_minutes)
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            d_num,
            w_num,
            task_name,
            skill,
            brief,
            day.get("mini_output", f"Complete Day {d_num} deliverable"),
            day.get("reflection_question", "What did you verify today?"),
            day.get("resource_title", f"{task_name} Guide"),
            plat,
            instr,
            q_url,
            day.get("resource_type", "Practical Guide"),
            day.get("estimated_minutes", "35 mins")
        ))

    conn.commit()

    cursor.execute("SELECT * FROM daily_tasks WHERE user_id=? AND month_number=1 ORDER BY day_number ASC", (user_id,))
    inserted_days = cursor.fetchall()

    daily_data = {
        "days": [
            {
                "id": row["id"],
                "month": 1,
                "day": row["day_number"],
                "week": row["week_number"] or (((row["day_number"] - 1) // 7) + 1),
                "task": row["task"],
                "skill_focus": row["skill_focus"],
                "mission_brief": row["mission_brief"],
                "mini_output": row["mini_output"],
                "reflection_question": row["reflection_question"],
                "completed": row["completed"],
                "resource_title": row["resource_title"],
                "platform": row["platform"],
                "platform_instruction": row["platform_instruction"],
                "resource_url": row["resource_url"],
                "resource_type": row["resource_type"],
                "estimated_minutes": row["estimated_minutes"]
            }
            for row in inserted_days
        ]
    }

    conn.close()
    return render_template("daily_roadmap.html",
                           username=session["user"],
                           roadmap=daily_data,
                           streak_count=streak_count,
                           longest_streak=longest_streak,
                           completed_count=0,
                           total_tasks=len(daily_data["days"]),
                           chosen_career=chosen_career,
                           current_month=1,
                           unlocked_months=[1],
                           max_unlocked_month=1,
                           can_unlock_next=False,
                           next_month_num=2,
                           need_completion=False)


@app.route("/unlock_next_month")
def unlock_next_month():
    """Contextual Month 2+ Generator: Gated until previous month is 100% complete!"""
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, chosen_career FROM users WHERE username=?", (session["user"],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return redirect(url_for("index"))
    user_id = user_row["id"]
    chosen_career = user_row["chosen_career"] or "Specialist Track"

    # Determine highest existing month
    cursor.execute("SELECT MAX(month_number) as max_m FROM daily_tasks WHERE user_id=?", (user_id,))
    row_max = cursor.fetchone()
    max_m = row_max["max_m"] if (row_max and row_max["max_m"]) else 1
    next_month = max_m + 1

    # Verify that the active max month is 100% completed
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) as comp FROM daily_tasks WHERE user_id=? AND month_number=?", (user_id, max_m))
    m_stats = cursor.fetchone()
    m_total = m_stats["total"] or 0
    m_comp = m_stats["comp"] or 0

    if m_total == 0 or m_comp < m_total:
        conn.close()
        return redirect(url_for("start_roadmap", month=max_m, need_completion="true"))

    if next_month > 6:
        conn.close()
        return redirect(url_for("start_roadmap", month=max_m))

    # Check if next month is already generated
    cursor.execute("SELECT COUNT(*) as count FROM daily_tasks WHERE user_id=? AND month_number=?", (user_id, next_month))
    if cursor.fetchone()["count"] > 0:
        conn.close()
        return redirect(url_for("start_roadmap", month=next_month))

    # Fetch complete context of past month achievements
    cursor.execute("""
        SELECT day_number, task, skill_focus, mini_output 
        FROM daily_tasks 
        WHERE user_id=? AND month_number=? 
        ORDER BY day_number ASC
    """, (user_id, max_m))
    past_tasks = cursor.fetchall()
    past_context = "\n".join([f"- Day {r['day_number']}: {r['task']} (Skill: {r['skill_focus']})" for r in past_tasks])

    # Fetch roadmap goal for this month
    cursor.execute("SELECT roadmap_json FROM roadmaps WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (user_id,))
    roadmap_row = cursor.fetchone()
    next_month_goal = f"Month {next_month} advanced milestone"
    if roadmap_row:
        try:
            rdata = json.loads(roadmap_row["roadmap_json"])
            for m in rdata.get("months", []):
                if m.get("month") == next_month:
                    next_month_goal = m.get("goal") or m.get("title") or next_month_goal
        except:
            pass

    cursor.execute("SELECT about FROM profiles WHERE user_id=?", (user_id,))
    p = cursor.fetchone()
    about_text = p["about"] if p else ""

    start_day = (next_month - 1) * 30 + 1
    end_day = next_month * 30

    prompt = f"""
You are an expert personal learning mentor and curriculum architect.
Target Career / Discipline: {chosen_career}
User Background: {about_text}

=== CRITICAL CONTEXT: PAST MONTH {max_m} ACHIEVEMENTS ===
The user has successfully completed ALL 30 days of Month {max_m}!
Here is the exact progression they conquered:
{past_context}

=== MONTH {next_month} OBJECTIVE ===
Target Month: Month {next_month} (Days {start_day} to {end_day})
Month Objective: {next_month_goal}

BUILD STRICTLY ON TOP OF PAST MONTH. DO NOT REPEAT PAST MONTH TOPICS.
Break Month {next_month} into an intensive, sequential 30-day prerequisite ladder (Days {start_day} to {end_day}).
For EVERY day, select recognized reputable platforms (Official Docs, Practice Platforms, Repos, Interactive sites) and provide explicit platform instructions.

Return ONLY valid JSON matching:
{{
  "days": [
    {{
      "day": {start_day},
      "task": "Sequential task name building directly on Month {max_m}",
      "skill_focus": "Specific advanced skill",
      "mission_brief": "How this elevates past month achievements",
      "mini_output": "Concrete 15-minute deliverable",
      "reflection_question": "Deep understanding check question",
      "resource_title": "Tutorial or documentation title",
      "platform": "Recognized Platform Name",
      "platform_instruction": "Exact action on that platform",
      "resource_type": "Interactive Guide / Lab / Spec",
      "resource_url": "https://...",
      "estimated_minutes": "35 mins"
    }}
  ]
}}
Pure RFC 8259 JSON only.
"""

    try:
        raw_output = call_gemini_api(prompt, json_mode=True, max_output_tokens=8192, temperature=0.2)
        days_list = parse_daily_tasks(raw_output, chosen_career, start_day=start_day, month_num=next_month)
    except Exception as e:
        conn.close()
        return f"Month {next_month} generation failed: {str(e)}"

    for day in days_list:
        d_num = day.get("day", start_day)
        w_num = ((d_num - 1) // 7) + 1
        t_name = day.get("task", f"Day {d_num} Mission")
        plat = day.get("platform", "Documentation")
        instr = day.get("platform_instruction", f"Complete exercises on {plat}.")
        q_url = day.get("resource_url") or build_platform_url(plat, t_name)

        cursor.execute("""
            INSERT INTO daily_tasks
            (user_id, month_number, day_number, week_number, task, skill_focus, mission_brief, mini_output, reflection_question, completed, resource_title, platform, platform_instruction, resource_url, resource_type, estimated_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            next_month,
            d_num,
            w_num,
            t_name,
            day.get("skill_focus", chosen_career),
            day.get("mission_brief", ""),
            day.get("mini_output", ""),
            day.get("reflection_question", ""),
            day.get("resource_title", t_name),
            plat,
            instr,
            q_url,
            day.get("resource_type", "Interactive Guide"),
            day.get("estimated_minutes", "35 mins")
        ))

    conn.commit()
    conn.close()
    return redirect(url_for("start_roadmap", month=next_month))


ACTION_QUOTES = [
    {"text": "Action is the foundational key to all success.", "author": "Pablo Picasso"},
    {"text": "The secret of getting ahead is getting started. Break your complex overwhelming tasks into small manageable tasks, and start on the first one.", "author": "Mark Twain"},
    {"text": "Do you want to know who you are? Don't ask. Act! Action will delineate and define you.", "author": "Thomas Jefferson"},
    {"text": "You do not rise to the level of your goals. You fall to the level of your systems. Focus on daily execution.", "author": "James Clear"},
    {"text": "Knowing is not enough; we must apply. Willing is not enough; we must do.", "author": "Johann Wolfgang von Goethe"},
    {"text": "Waste no more time arguing about what a good man should be. Be one.", "author": "Marcus Aurelius"},
    {"text": "It is not because things are difficult that we do not dare; it is because we do not dare that they are difficult.", "author": "Seneca"},
    {"text": "Long-term consistency trumps short-term intensity. Show up and do the work every single day.", "author": "Bruce Lee"},
    {"text": "Amateurs sit and wait for inspiration. The rest of us just get up and go to work.", "author": "Stephen King"},
    {"text": "An ounce of action is worth a ton of theory.", "author": "Friedrich Engels"},
    {"text": "Inaction breeds doubt and fear. Action breeds confidence and courage.", "author": "Dale Carnegie"},
    {"text": "The way to get started is to quit talking and begin doing.", "author": "Steve Jobs"},
    {"text": "Start where you are. Use what you have. Do what you can.", "author": "Arthur Ashe"},
    {"text": "Ideas are cheap. Deliberate, disciplined execution is everything.", "author": "Chris Sacca"},
    {"text": "Small disciplines repeated with consistency every day lead to great achievements gained slowly over time.", "author": "John C. Maxwell"},
    {"text": "Every action you take is a vote for the type of person you wish to become.", "author": "James Clear"},
    {"text": "Continuous effort, not strength or intelligence, is the key to unlocking our potential.", "author": "Winston Churchill"},
    {"text": "Do not wait; the time will never be 'just right.' Start where you stand, and work with whatever tools you may have at your command.", "author": "George Herbert"},
    {"text": "First say to yourself what you would be; and then do what you have to do.", "author": "Epictetus"},
    {"text": "You don't have to be great to start, but you have to start to be great.", "author": "Zig Ziglar"},
    {"text": "Discipline is choosing between what you want now and what you want most.", "author": "Abraham Lincoln"},
    {"text": "Great things are not done by impulse, but by a series of small things brought together.", "author": "Vincent van Gogh"},
    {"text": "Do something today that your future self will thank you for.", "author": "Sean Patrick Flanery"},
    {"text": "Nothing will work unless you do.", "author": "Maya Angelou"},
    {"text": "The critical ingredient is getting off your butt and doing something. It is as simple as that.", "author": "Nolan Bushnell"},
    {"text": "Success is the sum of small efforts, repeated day in and day out.", "author": "Robert Collier"},
    {"text": "Don't count the days; make the days count through intentional action.", "author": "Muhammad Ali"},
    {"text": "Simplicity boils down to two steps: Identify the essential. Eliminate the rest. Then execute relentlessly.", "author": "Leo Babauta"},
    {"text": "Focus on being productive instead of busy. What you execute today improves all your tomorrows.", "author": "Ralph Marston"},
    {"text": "The path to success is to take massive, determined action.", "author": "Tony Robbins"},
    {"text": "Never mistake activity for achievement. Focus on verifiable daily outputs.", "author": "John Wooden"}
]

def get_daily_quote():
    today = date.today()
    day_of_year = today.timetuple().tm_yday
    quote = ACTION_QUOTES[day_of_year % len(ACTION_QUOTES)]
    formatted_date = today.strftime("%B %d, %Y")
    return quote, formatted_date


@app.route("/regenerate_daily_tasks")
def regenerate_daily_tasks():
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=?", (session["user"],))
    user = cursor.fetchone()
    req_month = request.args.get("month", type=int) or 1
    if user:
        user_id = user["id"]
        cursor.execute("DELETE FROM daily_tasks WHERE user_id=? AND month_number=?", (user_id, req_month))
        conn.commit()
    conn.close()

    return redirect(url_for("start_roadmap", month=req_month))


@app.route("/finish_onboarding")
def finish_onboarding():
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=?", (session["user"],))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE users SET onboarding_completed=1 WHERE id=?", (user["id"],))
        conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (session["user"],))
    user = cursor.fetchone()
    if not user:
        conn.close()
        session.clear()
        return redirect(url_for("index"))
    user_id = user["id"]

    step = get_onboarding_step(user_id)
    if step != "dashboard":
        conn.close()
        return redirect(url_for(step))

    cursor.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,))
    profile = cursor.fetchone()

    cursor.execute("SELECT id FROM career_suggestions WHERE user_id=?", (user_id,))
    has_career = cursor.fetchone() is not None

    cursor.execute("SELECT id FROM roadmaps WHERE user_id=?", (user_id,))
    has_roadmap = cursor.fetchone() is not None

    cursor.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_count 
        FROM daily_tasks WHERE user_id=?
    """, (user_id,))
    task_stats = cursor.fetchone()
    total_tasks = task_stats["total"] if task_stats else 0
    completed_tasks = (task_stats["completed_count"] or 0) if task_stats else 0

    cursor.execute("""
        SELECT id, day_number, task, skill_focus, resource_title, platform, platform_instruction, resource_url, estimated_minutes 
        FROM daily_tasks 
        WHERE user_id=? AND completed=0 
        ORDER BY day_number ASC 
        LIMIT 1
    """, (user_id,))
    today_task = cursor.fetchone()

    streak_count = user["streak_count"] or 0
    longest_streak = user["longest_streak"] or 0
    chosen_career = user["chosen_career"] or "Specialist Track"

    conn.close()

    # Automatically fetch or upgrade news daily based on today's date
    domain_items, pulse_date, pulse_updated = get_daily_news(user_id, chosen_career, force_refresh=False)
    
    # Get daily action quote updated automatically based on date
    daily_quote, today_formatted_date = get_daily_quote()

    return render_template("dashboard.html",
                           username=session["user"],
                           profile=profile,
                           has_career=has_career,
                           has_roadmap=has_roadmap,
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           streak_count=streak_count,
                           longest_streak=longest_streak,
                           today_task=today_task,
                           chosen_career=chosen_career,
                           domain_items=domain_items,
                           pulse_date=pulse_date,
                           pulse_updated=pulse_updated,
                           daily_quote=daily_quote,
                           today_formatted_date=today_formatted_date)


def get_daily_news(user_id, chosen_career, force_refresh=False):
    """Fetches clean industry news headlines with links, upgrading daily based on date."""
    conn = get_db()
    cursor = conn.cursor()
    today_str = date.today().isoformat()

    if not force_refresh:
        cursor.execute("SELECT pulse_json, pulse_date, updated_at FROM domain_pulses WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if row and row["pulse_json"] and row["pulse_date"] == today_str:
            try:
                items = json.loads(row["pulse_json"])
                if items and isinstance(items, list):
                    conn.close()
                    return items, row["pulse_date"], row["updated_at"] or "Today"
            except Exception:
                pass

    prompt = f"""
You are an authoritative industry and technical news curator specializing in {chosen_career}.
Today's Date: {today_str}

Generate 4 top, authoritative industry news headlines relevant to {chosen_career}.
For each item, provide:
- "title": A clear, informative news headline (under 14 words).
- "source": Publisher name (e.g. Hacker News, GitHub Blog, InfoQ, TechCrunch, Official Docs, Arxiv, The Verge).
- "url": A real, direct, relevant web link (e.g. https://news.ycombinator.com, https://github.blog, https://docs.python.org, or topic search URL).

Return ONLY valid JSON matching:
{{
  "news": [
    {{
      "title": "Concise industry news headline",
      "source": "Platform Name",
      "url": "https://..."
    }}
  ]
}}
Strict Rules:
- Pure RFC 8259 JSON only.
- Do NOT use ANY emojis anywhere.
"""
    raw_output = call_gemini_api(prompt, json_mode=True, max_output_tokens=1024, temperature=0.3)
    data = clean_json_response(raw_output)
    news_items = data.get("news", []) if isinstance(data, dict) else []

    if not news_items or not isinstance(news_items, list) or len(news_items) < 3:
        q = urllib.parse.quote(chosen_career)
        news_items = [
            {
                "title": f"Recent Advances and Production Architectures in {chosen_career}",
                "source": "InfoQ",
                "url": f"https://www.infoq.com/search.action?queryString={q}"
            },
            {
                "title": f"Industry Engineering Standards and Workflow Shifts for {chosen_career}",
                "source": "Hacker News",
                "url": f"https://hn.algolia.com/?q={q}"
            },
            {
                "title": f"Emerging Open-Source Repositories and Tooling for {chosen_career}",
                "source": "GitHub Trending",
                "url": f"https://github.com/search?q={q}&type=repositories"
            },
            {
                "title": f"Core Competency Benchmarks and Technical Hiring Trends in {chosen_career}",
                "source": "TechCrunch",
                "url": f"https://techcrunch.com/search/{q}"
            }
        ]

    # Clean any accidental emoji from items
    emoji_cleaner = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27ff]|[\u2300-\u23ff]')
    for item in news_items:
        item["title"] = emoji_cleaner.sub('', str(item.get("title", ""))).strip()
        item["source"] = emoji_cleaner.sub('', str(item.get("source", ""))).strip()
        if not item.get("url") or not str(item["url"]).startswith("http"):
            item["url"] = f"https://www.google.com/search?q={urllib.parse.quote(item['title'])}"

    now_str = datetime.now().strftime("%I:%M %p")
    cursor.execute("""
        INSERT INTO domain_pulses (user_id, pulse_json, pulse_date, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET pulse_json=excluded.pulse_json, pulse_date=excluded.pulse_date, updated_at=excluded.updated_at
    """, (user_id, json.dumps(news_items), today_str, now_str))
    conn.commit()
    conn.close()

    return news_items, today_str, now_str


@app.route("/api/chat", methods=["POST"])
def chat_with_mentor():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "<p>I am here. What is on your mind regarding your learning roadmap?</p>"})

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, chosen_career, streak_count FROM users WHERE username=?", (session["user"],))
    u = cursor.fetchone()
    if not u:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    user_id = u["id"]
    chosen_career = u["chosen_career"] or "General Mastery"
    streak = u["streak_count"] or 0

    cursor.execute("SELECT about FROM profiles WHERE user_id=?", (user_id,))
    p = cursor.fetchone()
    profile_about = p["about"] if p else ""

    cursor.execute("""
        SELECT day_number, task, skill_focus, platform, platform_instruction 
        FROM daily_tasks 
        WHERE user_id=? AND completed=0 
        ORDER BY day_number ASC LIMIT 1
    """, (user_id,))
    today = cursor.fetchone()
    today_info = f"Day {today['day_number']}: {today['task']} on {today['platform']} ({today['skill_focus']})" if today else "All current daily missions completed."

    conn.close()

    prompt = f"""
You are the user's personal "Pocket Mentor Partner", an empathetic, razor-sharp, inspiring AI companion.
User Name: {session['user']}
Target Career / Discipline: {chosen_career}
User Background: {profile_about}
Today's Mission Status: {today_info}
Active Daily Streak: {streak} days

User Message: {user_msg}

Guidelines:
- Answer with concise, warm, practical, and inspiring advice (under 120 words).
- If they ask about today's task, break it down into an easy 15-minute first step.
- Use clean Markdown formatting (bold, brief bullet points).
- Strict Rule: Do NOT use ANY emojis anywhere in your response.
"""
    reply = call_gemini_api(prompt, json_mode=False, max_output_tokens=1024, temperature=0.4)
    if not reply:
        reply = "I am right here with you. Focus on executing today's deliberate step and compounding your momentum."

    # Strip any emojis from response
    emoji_cleaner = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27ff]|[\u2300-\u23ff]')
    reply = emoji_cleaner.sub('', reply).strip()

    reply_html = markdown.markdown(reply)
    return jsonify({"reply": reply_html, "raw": reply})


@app.route("/api/domain_pulse", methods=["GET", "POST"])
def domain_pulse():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, chosen_career FROM users WHERE username=?", (session["user"],))
    u = cursor.fetchone()
    if not u:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    
    user_id = u["id"]
    chosen_career = u["chosen_career"] or "Specialist Track"
    conn.close()

    force_refresh = request.args.get("refresh") == "true" or request.method == "POST"
    news_items, pulse_date, updated_at = get_daily_news(user_id, chosen_career, force_refresh=force_refresh)

    return jsonify({"items": news_items, "pulse_date": pulse_date, "updated_at": updated_at})


@app.route("/api/toggle_task/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username=?", (session["user"],))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    user_id = user_row["id"]

    cursor.execute("SELECT id, completed, month_number FROM daily_tasks WHERE id=? AND user_id=?", (task_id, user_id))
    task = cursor.fetchone()
    if not task:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    new_completed = 0 if task["completed"] == 1 else 1
    now_str = datetime.now().isoformat()

    cursor.execute("UPDATE daily_tasks SET completed=?, completed_at=? WHERE id=?", 
                   (new_completed, now_str if new_completed == 1 else None, task_id))

    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    cursor.execute("SELECT streak_count, longest_streak, last_active_date FROM users WHERE id=?", (user_id,))
    u = cursor.fetchone()
    streak = u["streak_count"] or 0
    longest = u["longest_streak"] or 0
    last_date = u["last_active_date"]

    if new_completed == 1:
        if last_date == today_str:
            pass
        elif last_date == yesterday_str:
            streak += 1
        else:
            streak = 1
        longest = max(longest, streak)
        cursor.execute("UPDATE users SET streak_count=?, longest_streak=?, last_active_date=? WHERE id=?",
                       (streak, longest, today_str, user_id))

    conn.commit()

    cursor.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_count 
        FROM daily_tasks WHERE user_id=?
    """, (user_id,))
    stats = cursor.fetchone()
    total_count = stats["total"] or 0
    completed_count = stats["completed_count"] or 0

    month_num = task["month_number"] or 1
    cursor.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_count 
        FROM daily_tasks WHERE user_id=? AND month_number=?
    """, (user_id, month_num))
    m_stats = cursor.fetchone()
    month_total = (m_stats["total"] or 0) if m_stats else 0
    month_completed = (m_stats["completed_count"] or 0) if m_stats else 0

    conn.close()
    return jsonify({
        "success": True,
        "task_id": task_id,
        "completed": new_completed,
        "streak_count": streak,
        "longest_streak": longest,
        "completed_count": completed_count,
        "total_tasks": total_count,
        "month_total": month_total,
        "month_completed_count": month_completed
    })


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
