"""Migration 008: Add goal_weight and goal_date columns to users.

Issue #57: body weight trend line — predicted trajectory to goal weight
"""
import sqlite3
import sys


def run(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = OFF")

    # Check if columns already exist
    cols = db.execute(
        "SELECT name FROM pragma_table_info('users') WHERE name IN ('goal_weight', 'goal_date')"
    ).fetchall()
    cols = [c[0] for c in cols]

    if 'goal_weight' in cols and 'goal_date' in cols:
        print("Migration 008: already applied, skipping.")
        db.close()
        return

    print("Migration 008: adding goal_weight and goal_date to users...")

    if 'goal_weight' not in cols:
        db.execute("ALTER TABLE users ADD COLUMN goal_weight REAL")
    if 'goal_date' not in cols:
        db.execute("ALTER TABLE users ADD COLUMN goal_date TEXT")

    db.commit()
    db.execute("PRAGMA foreign_keys = ON")
    db.close()
    print("Migration 008: done.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/gym_coach.db"
    run(path)
