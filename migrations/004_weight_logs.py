"""Migration 004: Create weight_logs table."""
import sqlite3
import sys


def run(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = OFF")

    tables = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='weight_logs'"
    ).fetchone()

    if tables:
        print("Migration 004: weight_logs table already exists, skipping.")
        db.close()
        return

    print("Migration 004: creating weight_logs table...")
    db.execute("""
        CREATE TABLE weight_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            date TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.execute("PRAGMA foreign_keys = ON")
    db.close()
    print("Migration 004: done.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/gym_coach.db"
    run(path)
