from database import get_db
from datetime import date


def log_meal(user_id: int, description: str, meal_type: str = 'meal',
             calories: float = 0, protein: float = 0, carbs: float = 0, fat: float = 0) -> int:
    """Log a meal for a user."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO nutrition_logs (user_id, date, meal_type, description, calories, protein, carbs, fat) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, str(date.today()), meal_type, description, calories, protein, carbs, fat),
    )
    db.commit()
    log_id = cursor.lastrowid
    db.close()
    return log_id


def get_daily_summary(user_id: int, target_date: str = None) -> dict:
    """Get nutrition summary for a specific date."""
    if target_date is None:
        target_date = str(date.today())

    db = get_db()
    rows = db.execute(
        "SELECT * FROM nutrition_logs WHERE user_id = ? AND date = ? ORDER BY created_at",
        (user_id, target_date)
    ).fetchall()
    db.close()

    meals = [dict(row) for row in rows]
    total_calories = sum(m['calories'] for m in meals)
    total_protein = sum(m['protein'] for m in meals)
    total_carbs = sum(m['carbs'] for m in meals)
    total_fat = sum(m['fat'] for m in meals)

    return {
        'date': target_date,
        'meals': meals,
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs,
        'total_fat': total_fat,
    }


def get_weekly_summary(user_id: int) -> list:
    """Get nutrition summaries for the last 7 days."""
    summaries = []
    from datetime import timedelta
    for i in range(7):
        d = date.today() - timedelta(days=i)
        summaries.append(get_daily_summary(user_id, str(d)))
    return summaries
