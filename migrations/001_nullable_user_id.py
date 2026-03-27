"""Migration 001: Make ai_conversations.user_id nullable.

SQLite doesn't support ALTER COLUMN, so we recreate the table.
"""
import sqlite3
import sys


def run(db_path: str):
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = OFF")

    # Check current schema
    col = db.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='ai_conversations'"
    ).fetchone()
    if col and "NOT NULL" not in col[0].split("user_id")[1].split("\n")[0]:
        print("Migration 001: already applied (user_id is nullable), skipping.")
        db.close()
        return

    print("Migration 001: making ai_conversations.user_id nullable...")

    db.executescript("""
        BEGIN;

        CREATE TABLE ai_conversations_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            module TEXT NOT NULL DEFAULT 'general',
            messages TEXT NOT NULL DEFAULT '[]',
            tokens_used INTEGER DEFAULT 0,
            model_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        INSERT INTO ai_conversations_new
            SELECT id, user_id, module, messages, tokens_used, model_used, created_at, updated_at
            FROM ai_conversations;

        DROP TABLE ai_conversations;

        ALTER TABLE ai_conversations_new RENAME TO ai_conversations;

        COMMIT;
    """)

    db.execute("PRAGMA foreign_keys = ON")
    db.close()
    print("Migration 001: done.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/gym_coach.db"
    run(path)
