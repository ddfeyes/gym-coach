"""Measurement tracking model."""
from database import get_db
from datetime import date


def log_measurement(user_id: int, measurement_date: str = None, **kwargs) -> int:
    """Log body measurements for a user. Updates same-day entry if exists."""
    if measurement_date is None:
        measurement_date = str(date.today())

    allowed_fields = ['biceps_l', 'biceps_r', 'chest', 'waist', 'hips', 'thigh_l', 'thigh_r', 'notes']
    data = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

    db = get_db()
    cursor = db.cursor()

    existing = db.execute(
        "SELECT id FROM measurements WHERE user_id = ? AND date = ?",
        (user_id, measurement_date)
    ).fetchone()

    if existing:
        if data:
            set_clause = ', '.join(f"{k} = ?" for k in data.keys())
            cursor.execute(
                f"UPDATE measurements SET {set_clause} WHERE user_id = ? AND date = ?",
                list(data.values()) + [user_id, measurement_date]
            )
        log_id = existing['id']
    else:
        data['user_id'] = user_id
        data['date'] = measurement_date
        cols = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        cursor.execute(
            f"INSERT INTO measurements (user_id, date, biceps_l, biceps_r, chest, waist, hips, thigh_l, thigh_r, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [user_id, measurement_date,
             data.get('biceps_l'), data.get('biceps_r'),
             data.get('chest'), data.get('waist'),
             data.get('hips'), data.get('thigh_l'),
             data.get('thigh_r'), data.get('notes', '')]
        )
        log_id = cursor.lastrowid

    db.commit()
    db.close()
    return log_id


def get_measurement_history(user_id: int, limit: int = 30) -> list:
    """Get measurement history for a user."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM measurements WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    db.close()
    return [dict(row) for row in rows]


def get_latest_measurement(user_id: int) -> dict | None:
    """Get most recent measurement entry."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM measurements WHERE user_id = ? ORDER BY date DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    db.close()
    return dict(row) if row else None
