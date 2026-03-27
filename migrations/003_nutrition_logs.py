"""Migration 003: Create nutrition_logs table."""
import sqlite3
import sys


def run(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = OFF")

    tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='nutrition_logs'"
    ).fetchone()

    if tables:
        print("Migration 003: nutrition_logs table already exists, skipping.")
        db.close()
        return

    print("Migration 003: creating nutrition_logs table...")
    db.execute("""
        CREATE TABLE nutrition_logs (
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
    db.execute("PRAGMA foreign_keys = ON")
    db.close()
    print("Migration 003: done.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/gym_coach.db"
    run(path)
