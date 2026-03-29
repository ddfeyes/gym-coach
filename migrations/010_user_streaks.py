"""Migration 010: user_streaks table for personal best tracking."""
import sqlite3


def migrate(db: sqlite3.Connection):
    db.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            streak_type TEXT NOT NULL,
            best_count INTEGER DEFAULT 0,
            best_start TEXT,
            best_end TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, streak_type)
        )
    """)
    db.commit()
