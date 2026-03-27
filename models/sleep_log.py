from database import get_db
from datetime import date, timedelta


def log_sleep(user_id: int, hours: float, quality: int = 3, notes: str = '', log_date: str = None) -> int:
    """Log sleep for a user. Updates same-day entry if exists."""
    if log_date is None:
        log_date = str(date.today())

    db = get_db()
    cursor = db.cursor()
    existing = db.execute(
        "SELECT id FROM sleep_logs WHERE user_id = ? AND date = ?",
        (user_id, log_date)
    ).fetchone()

    if existing:
        cursor.execute(
            "UPDATE sleep_logs SET hours = ?, quality = ?, notes = ? WHERE user_id = ? AND date = ?",
            (hours, quality, notes, user_id, log_date)
        )
        log_id = existing['id']
    else:
        cursor.execute(
            "INSERT INTO sleep_logs (user_id, date, hours, quality, notes) VALUES (?, ?, ?, ?, ?)",
            (user_id, log_date, hours, quality, notes)
        )
        log_id = cursor.lastrowid

    db.commit()
    db.close()
    return log_id


def get_sleep_history(user_id: int, days: int = 7) -> list:
    """Get sleep history for the last N days."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM sleep_logs WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, days)
    ).fetchall()
    db.close()
    return [dict(row) for row in rows]


def get_sleep_summary(user_id: int, days: int = 7) -> dict:
    """Get sleep summary stats."""
    history = get_sleep_history(user_id, days)
    if not history:
        return {'average_hours': 0, 'average_quality': 0, 'entries': []}

    avg_hours = sum(h['hours'] for h in history) / len(history)
    avg_quality = sum(h['quality'] for h in history) / len(history)

    return {
        'average_hours': round(avg_hours, 1),
        'average_quality': round(avg_quality, 1),
        'entries': history,
    }
