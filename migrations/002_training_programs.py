"""Migration 002: Create training_programs table.

SQLite doesn't support IF NOT EXISTS fully across all scenarios,
so we recreate the table only if it doesn't exist.
"""
import sqlite3
import sys


def run(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = OFF")

    # Check if table exists
    tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='training_programs'"
    ).fetchone()

    if tables:
        print("Migration 002: training_programs table already exists, skipping.")
        db.close()
        return

    print("Migration 002: creating training_programs table...")
    db.execute("""
        CREATE TABLE training_programs (
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

    db.commit()
    db.execute("PRAGMA foreign_keys = ON")
    db.close()
    print("Migration 002: done.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/gym_coach.db"
    run(path)
