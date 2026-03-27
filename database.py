import sqlite3
from config import Config


def get_db():
    db = sqlite3.connect(Config.DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def create_tables():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            name TEXT NOT NULL,
            gender TEXT NOT NULL CHECK(gender IN ('female', 'male')),
            age INTEGER NOT NULL CHECK(age BETWEEN 14 AND 80),
            height_cm REAL NOT NULL CHECK(height_cm BETWEEN 100 AND 250),
            weight_kg REAL NOT NULL CHECK(weight_kg BETWEEN 30 AND 300),

            experience_level TEXT NOT NULL CHECK(experience_level IN ('beginner', 'intermediate', 'advanced')),
            training_days_per_week INTEGER NOT NULL CHECK(training_days_per_week BETWEEN 2 AND 6),
            session_duration_minutes INTEGER DEFAULT 60,
            available_equipment TEXT NOT NULL DEFAULT '[]',
            gym_type TEXT DEFAULT 'full_gym' CHECK(gym_type IN ('full_gym', 'home_gym', 'dumbbells_only', 'bodyweight')),

            injuries TEXT DEFAULT '[]',
            exercise_restrictions TEXT DEFAULT '[]',
            medical_notes TEXT,

            primary_goal TEXT NOT NULL CHECK(primary_goal IN ('muscle_gain', 'fat_loss', 'strength', 'health', 'recomposition')),
            secondary_goals TEXT DEFAULT '[]',

            cycle_tracking_enabled INTEGER DEFAULT 0,
            cycle_average_length INTEGER DEFAULT 28,
            cycle_last_start_date TEXT,

            allergies TEXT DEFAULT '[]',
            diet_type TEXT DEFAULT 'omnivore',
            budget_level TEXT DEFAULT 'medium',

            language TEXT DEFAULT 'uk',
            timezone TEXT DEFAULT 'Europe/Lisbon',
            checkin_reminder_time TEXT DEFAULT '08:00',
            notifications_enabled INTEGER DEFAULT 1,

            onboarding_completed INTEGER DEFAULT 0,
            onboarding_step INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            module TEXT NOT NULL DEFAULT 'general',

            messages TEXT NOT NULL DEFAULT '[]',

            tokens_used INTEGER DEFAULT 0,
            model_used TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            program_type TEXT NOT NULL DEFAULT 'split',
            schedule TEXT NOT NULL DEFAULT '[]',
            exercises TEXT NOT NULL DEFAULT '[]',
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            date TEXT NOT NULL,
            meal_type TEXT DEFAULT 'meal',
            description TEXT NOT NULL,
            calories REAL DEFAULT 0,
            protein REAL DEFAULT 0,
            carbs REAL DEFAULT 0,
            fat REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()
