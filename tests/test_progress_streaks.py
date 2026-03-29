"""Tests for streak tracking (issue #53)."""
import pytest
from datetime import date, timedelta


def test_calc_consecutive_days_empty():
    from routes.progress import calc_consecutive_days
    count, start, end = calc_consecutive_days([], lambda d: True)
    assert count == 0
    assert start is None
    assert end is None


def test_calc_consecutive_days_single():
    from routes.progress import calc_consecutive_days
    today = date.today().isoformat()
    count, start, end = calc_consecutive_days([today], lambda d: True)
    assert count == 1
    assert start == today
    assert end == today


def test_calc_consecutive_days_consecutive():
    from routes.progress import calc_consecutive_days
    today = date.today()
    dates = [(today - timedelta(days=i)).isoformat() for i in range(5)]
    count, start, end = calc_consecutive_days(dates, lambda d: True)
    assert count == 5
    assert start == (today - timedelta(days=4)).isoformat()
    assert end == today.isoformat()


def test_calc_consecutive_days_gap():
    from routes.progress import calc_consecutive_days
    today = date.today()
    # Days 0, 1, 2, skip 3, days 4, 5
    dates = [(today - timedelta(days=i)).isoformat() for i in [0, 1, 2, 4, 5]]
    count, start, end = calc_consecutive_days(dates, lambda d: True)
    assert count == 3
    assert start == (today - timedelta(days=2)).isoformat()
    assert end == today.isoformat()


def test_calc_consecutive_days_threshold():
    from routes.progress import calc_consecutive_days
    today = date.today()
    # All consecutive valid days (no gaps)
    dates_hours = {
        (today - timedelta(days=0)).isoformat(): 8,   # valid
        (today - timedelta(days=1)).isoformat(): 9,   # valid
        (today - timedelta(days=2)).isoformat(): 7,   # valid
        (today - timedelta(days=3)).isoformat(): 6,   # fails threshold → breaks streak
    }
    dates = list(dates_hours.keys())  # descending: today, yesterday, 2d ago, 3d ago
    threshold = lambda d: dates_hours.get(d, 0) >= 7
    count, start, end = calc_consecutive_days(dates, threshold)
    # today→yesterday→2d ago are all valid and consecutive = 3 days
    assert count == 3
    assert end == today.isoformat()
    assert start == (today - timedelta(days=2)).isoformat()


def test_calc_consecutive_days_streak_ended():
    from routes.progress import calc_consecutive_days
    today = date.today()
    yesterday = (today - timedelta(days=1)).isoformat()
    two_days_ago = (today - timedelta(days=2)).isoformat()
    # Today NOT in valid, yesterday IS, two_days_ago IS
    dates = [yesterday, two_days_ago]
    count, start, end = calc_consecutive_days(dates, lambda d: True)
    assert count == 2
    assert start == two_days_ago
    assert end == yesterday


def _create_test_user(db):
    """Create a minimal valid test user and return user_id."""
    db.execute("""
        INSERT OR IGNORE INTO users (
            telegram_id, name, gender, age, height_cm, weight_kg,
            experience_level, training_days_per_week, available_equipment,
            primary_goal
        ) VALUES (999988, 'streak_test', 'male', 30, 180.0, 80.0,
                  'beginner', 3, '[]', 'muscle_gain')
    """)
    db.commit()
    row = db.execute("SELECT id FROM users WHERE telegram_id = 999988").fetchone()
    return row['id'] if row else None


def test_training_streak_no_sessions(client):
    """No training sessions → streak 0."""
    from routes.progress import get_training_streak
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    count, start, end = get_training_streak(user_id, db)
    assert count == 0


def test_water_streak_no_logs(client):
    """No water logs → streak 0."""
    from routes.progress import get_water_streak
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    count, start, end = get_water_streak(user_id, db)
    assert count == 0


def test_sleep_streak_no_logs(client):
    """No sleep logs → streak 0."""
    from routes.progress import get_sleep_streak
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    count, start, end = get_sleep_streak(user_id, db)
    assert count == 0


def test_upsert_personal_best_new(client):
    """Insert new personal best."""
    from routes.progress import upsert_personal_best
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    upsert_personal_best(user_id, 'training', 5, '2026-03-25', '2026-03-29', db)
    row = db.execute(
        "SELECT * FROM user_streaks WHERE user_id = ? AND streak_type = 'training'",
        (user_id,)).fetchone()
    assert row is not None
    assert row['best_count'] == 5


def test_upsert_personal_best_updates_when_higher(client):
    """Best updates only when new count > stored."""
    from routes.progress import upsert_personal_best
    from database import get_db
    db = get_db()
    user_id = _create_test_user(db)
    upsert_personal_best(user_id, 'training', 5, '2026-03-25', '2026-03-29', db)
    upsert_personal_best(user_id, 'training', 3, '2026-03-20', '2026-03-22', db)  # lower, no update
    row = db.execute(
        "SELECT * FROM user_streaks WHERE user_id = ? AND streak_type = 'training'",
        (user_id,)).fetchone()
    assert row['best_count'] == 5
    upsert_personal_best(user_id, 'training', 10, '2026-03-15', '2026-03-24', db)  # higher
    row = db.execute(
        "SELECT * FROM user_streaks WHERE user_id = ? AND streak_type = 'training'",
        (user_id,)).fetchone()
    assert row['best_count'] == 10
