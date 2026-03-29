"""Tests for weekly summary endpoint (issue #54)."""
import pytest
from datetime import date, timedelta


def _create_test_user(db):
    """Create minimal valid test user."""
    db.execute("""
        INSERT OR IGNORE INTO users (
            telegram_id, name, gender, age, height_cm, weight_kg,
            experience_level, training_days_per_week, available_equipment,
            primary_goal
        ) VALUES (999988, 'weekly_test', 'male', 30, 180.0, 80.0,
                  'beginner', 3, '[]', 'muscle_gain')
    """)
    db.commit()
    row = db.execute("SELECT id FROM users WHERE telegram_id = 999988").fetchone()
    return row['id'] if row else None


def test_weekly_summary_empty_db(client):
    """No data → all zeros."""
    from routes.progress import get_weekly_summary_data
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    result = get_weekly_summary_data(user_id, db)
    assert result['training_count'] == 0
    assert result['avg_sleep'] == 0
    assert result['water_hit_days'] == 0
    assert result['weight_delta'] is None


def test_weekly_summary_training_sessions(client):
    """Training sessions counted correctly."""
    from routes.progress import get_weekly_summary_data
    from database import get_db
    import datetime
    db = get_db()
    user_id = _create_test_user(db)
    today = date.today()
    for i in range(3):
        d = (today - timedelta(days=i)).isoformat()
        db.execute(
            "INSERT INTO training_sessions (user_id, date, duration_minutes, notes) VALUES (?, ?, 60, 'test')",
            (user_id, d + ' 10:00:00'))
    db.commit()
    result = get_weekly_summary_data(user_id, db)
    assert result['training_count'] == 3


def test_weekly_summary_sleep_avg(client):
    """Average sleep calculated correctly."""
    from routes.progress import get_weekly_summary_data
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    today = date.today()
    # 3 days of sleep: 7h, 8h, 6h → avg 7
    for i, hours in enumerate([7, 8, 6]):
        d = (today - timedelta(days=i)).isoformat()
        db.execute(
            "INSERT INTO sleep_logs (user_id, date, hours, quality) VALUES (?, ?, ?, 3)",
            (user_id, d, hours))
    db.commit()
    result = get_weekly_summary_data(user_id, db)
    assert result['avg_sleep'] == 7.0


def test_weekly_summary_water_hit_days(client):
    """Water goal hit days counted correctly (>= 2500ml = hit)."""
    from routes.progress import get_weekly_summary_data
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    today = date.today()
    # 4 days: 3000ml, 2000ml, 2500ml, 2600ml → 3 hit days
    amounts = [3000, 2000, 2500, 2600]
    for i, amt in enumerate(amounts):
        d = (today - timedelta(days=i)).isoformat()
        db.execute(
            "INSERT INTO water_logs (user_id, date, amount_ml) VALUES (?, ?, ?)",
            (user_id, d, amt))
    db.commit()
    result = get_weekly_summary_data(user_id, db)
    assert result['water_hit_days'] == 3


def test_weekly_summary_insight_generation(client):
    """Insight text is generated."""
    from routes.progress import get_weekly_summary_data
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    # Clear prior test data for this user
    db.execute("DELETE FROM training_sessions WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM sleep_logs WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM water_logs WHERE user_id = ?", (user_id,))
    db.commit()
    today = date.today()
    # Good week: 4 trainings, 7.5h avg sleep, 5 water days
    for i in range(4):
        d = (today - timedelta(days=i)).isoformat()
        db.execute(
            "INSERT INTO training_sessions (user_id, date, duration_minutes) VALUES (?, ?, 60)",
            (user_id, d + ' 10:00:00'))
    for i, hours in enumerate([8, 7, 8, 7, 8]):
        d = (today - timedelta(days=i)).isoformat()
        db.execute("INSERT INTO sleep_logs (user_id, date, hours, quality) VALUES (?, ?, ?, 3)",
                   (user_id, d, hours))
    for i in range(5):
        d = (today - timedelta(days=i)).isoformat()
        db.execute("INSERT INTO water_logs (user_id, date, amount_ml) VALUES (?, ?, ?)",
                   (user_id, d, 2600))
    db.commit()
    result = get_weekly_summary_data(user_id, db)
    assert 'Тренувань 4' in result['insight']
    assert 'Сон' in result['insight']
    assert 'Вода 5/7' in result['insight']
