"""Migration 009: Add workout_plans and planned_exercises tables.

Issue #59: workout plan generator
"""
import sqlite3
import sys


def run(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = OFF")

    # Check if tables already exist
    tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('workout_plans', 'planned_exercises')"
    ).fetchall()
    tables = [t[0] for t in tables]

    if 'workout_plans' in tables and 'planned_exercises' in tables:
        print("Migration 009: already applied, skipping.")
        db.close()
        return

    print("Migration 009: creating workout_plans and planned_exercises tables...")

    if 'workout_plans' not in tables:
        db.execute("""
            CREATE TABLE workout_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                week_start TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                plan_data TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, week_start)
            )
        """)

    if 'planned_exercises' not in tables:
        db.execute("""
            CREATE TABLE planned_exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                day_idx INTEGER NOT NULL,
                title TEXT NOT NULL,
                sets TEXT,
                muscle_groups TEXT,
                estimated_minutes INTEGER DEFAULT 45,
                is_rest_day INTEGER DEFAULT 0,
                is_done INTEGER DEFAULT 0,
                FOREIGN KEY (plan_id) REFERENCES workout_plans(id)
            )
        """)

    db.commit()
    db.execute("PRAGMA foreign_keys = ON")
    db.close()
    print("Migration 009: done.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/gym_coach.db"
    run(path)
