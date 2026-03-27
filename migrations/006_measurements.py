"""Migration 006: Create measurements table."""
import sqlite3
import sys


def run(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = OFF")

    tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'"
    ).fetchone()

    if tables:
        print("Migration 006: measurements table already exists, skipping.")
        db.close()
        return

    print("Migration 006: creating measurements table...")
    db.execute("""
        CREATE TABLE measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            date TEXT NOT NULL,
            biceps_l REAL,
            biceps_r REAL,
            chest REAL,
            waist REAL,
            hips REAL,
            thigh_l REAL,
            thigh_r REAL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.execute("PRAGMA foreign_keys = ON")
    db.close()
    print("Migration 006: done.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/gym_coach.db"
    run(path)
