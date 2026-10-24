import sqlite3

def init_db(db_path="users.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        streak_count INTEGER DEFAULT 0,
        longest_streak INTEGER DEFAULT 0,
        last_active_date TEXT,
        onboarding_completed INTEGER DEFAULT 0,
        chosen_career TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
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
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roadmaps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        roadmap_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_tasks (
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
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS career_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        suggestion_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS domain_pulses (
        user_id INTEGER PRIMARY KEY,
        pulse_json TEXT,
        pulse_date TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
