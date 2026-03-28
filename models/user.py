import json
from database import get_db


def get_user_by_telegram_id(telegram_id):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    db.close()
    return dict(user) if user else None


def get_user_by_id(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    return dict(user) if user else None


def create_user(telegram_id, username, name, gender, age, height_cm, weight_kg,
                experience_level, training_days_per_week, primary_goal, **kwargs):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO users (telegram_id, username, name, gender, age, height_cm, weight_kg,
                           experience_level, training_days_per_week, primary_goal,
                           session_duration_minutes, available_equipment, gym_type,
                           injuries, exercise_restrictions, medical_notes,
                           secondary_goals, cycle_tracking_enabled, cycle_average_length,
                           cycle_last_start_date, language)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        telegram_id, username, name, gender, age, height_cm, weight_kg,
        experience_level, training_days_per_week, primary_goal,
        kwargs.get('session_duration_minutes', 60),
        json.dumps(kwargs.get('available_equipment', [])),
        kwargs.get('gym_type', 'full_gym'),
        json.dumps(kwargs.get('injuries', [])),
        json.dumps(kwargs.get('exercise_restrictions', [])),
        kwargs.get('medical_notes'),
        json.dumps(kwargs.get('secondary_goals', [])),
        kwargs.get('cycle_tracking_enabled', 0),
        kwargs.get('cycle_average_length', 28),
        kwargs.get('cycle_last_start_date'),
        kwargs.get('language', 'uk'),
    ))
    db.commit()
    user_id = cursor.lastrowid
    db.close()
    return user_id


def update_user(user_id, **fields):
    if not fields:
        return
    db = get_db()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    db.execute(
        f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values,
    )
    db.commit()
    db.close()


def set_calorie_target(user_id: int, calorie_target: int) -> None:
    """Set or update user's calorie target override."""
    db = get_db()
    try:
        db.execute("ALTER TABLE users ADD COLUMN calorie_target_override INTEGER")
    except Exception:
        pass  # column already exists
    db.execute(
        "UPDATE users SET calorie_target_override = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (calorie_target, user_id)
    )
    db.commit()
    db.close()


def get_calorie_target(user_id: int) -> int | None:
    """Get user's calorie target override if set."""
    db = get_db()
    row = db.execute(
        "SELECT calorie_target_override FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    db.close()
    return row[0] if row else None
