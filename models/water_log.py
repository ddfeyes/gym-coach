"""Water intake tracking model."""
from database import get_db
from datetime import date


def log_water(user_id: int, amount_ml: int, log_date: str = None) -> int:
    """Log water intake. Adds to today's total (doesn't overwrite)."""
    if log_date is None:
        log_date = str(date.today())

    db = get_db()
    cursor = db.cursor()

    # Check if there's already a water log for today - if so, add to it
    existing = db.execute(
        "SELECT id, amount_ml FROM water_logs WHERE user_id = ? AND date = ?",
        (user_id, log_date)
    ).fetchone()

    if existing:
        new_amount = existing['amount_ml'] + amount_ml
        cursor.execute(
            "UPDATE water_logs SET amount_ml = ? WHERE user_id = ? AND date = ?",
            (new_amount, user_id, log_date)
        )
        log_id = existing['id']
    else:
        cursor.execute(
            "INSERT INTO water_logs (user_id, date, amount_ml) VALUES (?, ?, ?)",
            (user_id, log_date, amount_ml)
        )
        log_id = cursor.lastrowid

    db.commit()
    db.close()
    return log_id


def get_daily_water(user_id: int, log_date: str = None) -> dict:
    """Get water intake for a specific day."""
    if log_date is None:
        log_date = str(date.today())

    db = get_db()
    row = db.execute(
        "SELECT * FROM water_logs WHERE user_id = ? AND date = ?",
        (user_id, log_date)
    ).fetchone()
    db.close()
    return dict(row) if row else {'date': log_date, 'amount_ml': 0}


def get_water_history(user_id: int, days: int = 7) -> list:
    """Get water history for the last N days."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM water_logs WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, days)
    ).fetchall()
    db.close()
    return [dict(row) for row in rows]
