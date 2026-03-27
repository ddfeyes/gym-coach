from database import get_db
from datetime import date


def log_weight(user_id: int, weight_kg: float, notes: str = '', log_date: str = None) -> int:
    """Log a weight entry for a user. Updates same-day entry if exists."""
    if log_date is None:
        log_date = str(date.today())

    db = get_db()
    cursor = db.cursor()

    # Check if entry for this date exists
    existing = db.execute(
        "SELECT id FROM weight_logs WHERE user_id = ? AND date = ?",
        (user_id, log_date)
    ).fetchone()

    if existing:
        cursor.execute(
            "UPDATE weight_logs SET weight_kg = ?, notes = ? WHERE user_id = ? AND date = ?",
            (weight_kg, notes, user_id, log_date)
        )
        log_id = existing['id']
    else:
        cursor.execute(
            "INSERT INTO weight_logs (user_id, date, weight_kg, notes) VALUES (?, ?, ?, ?)",
            (user_id, log_date, weight_kg, notes)
        )
        log_id = cursor.lastrowid

    db.commit()
    db.close()
    return log_id


def get_weight_history(user_id: int, limit: int = 30) -> list:
    """Get weight history for a user."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM weight_logs WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    db.close()
    return [dict(row) for row in rows]


def get_latest_weight(user_id: int) -> dict | None:
    """Get the most recent weight entry."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM weight_logs WHERE user_id = ? ORDER BY date DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    db.close()
    return dict(row) if row else None
