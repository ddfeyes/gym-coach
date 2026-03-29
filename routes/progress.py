"""Progress routes — aggregated data for charts and analytics."""
import sqlite3
import os
from flask import Blueprint, request, jsonify
from config import Config
from routes.auth import validate_telegram_init_data, extract_user_from_init_data
from datetime import datetime, timedelta

progress_bp = Blueprint('progress', __name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', Config.DATABASE_PATH)


def get_db():
    return sqlite3.connect(DB_PATH)


def get_user_id(telegram_id: int) -> int:
    db = get_db()
    cur = db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    db.close()
    return row[0] if row else None


def linear_regression(weights: list[float], days: list[str]) -> dict:
    """Calculate linear regression trend from weight history.
    
    Returns slope (kg/day), intercept, and predicted date to hit goal.
    """
    if len(weights) < 2:
        return {"slope": 0, "intercept": weights[0] if weights else 0, "r2": 0, "predicted_date": None}

    n = len(weights)
    # x = day index (0, 1, 2, ...)
    # y = weight
    sum_x = sum(range(n))
    sum_y = sum(weights)
    sum_xy = sum(i * w for i, w in enumerate(weights))
    sum_xx = sum(i * i for i in range(n))

    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-10:
        return {"slope": 0, "intercept": sum_y / n, "r2": 0, "predicted_date": None}

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    # R² calculation
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in weights)
    ss_res = sum((y - (slope * i + intercept)) ** 2 for i, y in enumerate(weights))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    return {
        "slope": round(slope, 4),
        "intercept": round(intercept, 2),
        "r2": round(r2, 3),
        "predicted_date": None,  # computed with goal in context
    }


def compute_trend_data(weight_history: list[dict], goal_weight: float | None) -> dict:
    """Compute trend line data for the last 14 weight entries."""
    history = weight_history[-14:] if len(weight_history) > 14 else weight_history
    if len(history) < 2:
        return {"trend_points": [], "on_track": None, "status_text": None}

    weights = [float(w["weight_kg"]) for w in history]
    dates = [w["date"] for w in history]

    trend = linear_regression(weights, dates)
    slope = trend["slope"]

    # Build trend line points as {date, weight_kg} for SVG rendering
    trend_points = []
    latest_date = datetime.strptime(dates[-1], "%Y-%m-%d")
    for i, w in enumerate(weights):
        trend_points.append({"date": dates[i], "weight_kg": w})

    # Project forward up to 90 days if we have a slope
    current_weight = weights[-1]
    if slope != 0 and goal_weight:
        # Determine direction: losing = goal < current, gaining = goal > current
        going_toward = (slope < 0 and goal_weight < current_weight) or (slope > 0 and goal_weight > current_weight)
        if going_toward:
            days_to_goal = abs((goal_weight - current_weight) / slope)
            if 0 < days_to_goal < 365:
                predicted = latest_date + timedelta(days=int(days_to_goal))
                trend["predicted_date"] = predicted.strftime("%Y-%m-%d")

    # Status text
    if goal_weight and trend["predicted_date"]:
        d = datetime.strptime(trend["predicted_date"], "%Y-%m-%d")
        status_text = f"При поточному темпі: мета до {d.strftime('%d.%m.%Y')}"
    elif goal_weight and slope != 0:
        direction = "набирає" if slope > 0 else "втрачає"
        status_text = f"Не на шляху до мети — {direction} {abs(slope)*7:.1f} кг/тиждень"
    else:
        status_text = None

    return {
        "slope_kg_per_day": trend["slope"],
        "slope_kg_per_week": round(trend["slope"] * 7, 2),
        "r2": trend["r2"],
        "predicted_date": trend["predicted_date"],
        "status_text": status_text,
        "goal_weight": goal_weight,
    }


def calc_consecutive_days(dates: list, threshold_fn) -> tuple:
    """Returns (streak_count, start_date, end_date) for consecutive days meeting threshold.
    Dates should be sorted descending (most recent first).
    threshold_fn(date) -> bool
    """
    if not dates:
        return 0, None, None

    from datetime import date as date_cls, timedelta
    today = date_cls.today().isoformat()
    yesterday = (date_cls.today() - timedelta(days=1)).isoformat()

    # Build set of valid dates
    valid = set()
    for d in dates:
        if d and threshold_fn(d):
            valid.add(d)

    if not valid:
        return 0, None, None

    # If today not valid, streak must start from yesterday
    if today in valid:
        cursor = today
    elif yesterday in valid:
        cursor = yesterday
    else:
        return 0, None, None

    # Count consecutive days backward
    count = 0
    d = date_cls.fromisoformat(cursor)
    while d.isoformat() in valid:
        count += 1
        d -= timedelta(days=1)

    end_date = cursor
    start_date = (d + timedelta(days=1)).isoformat()
    return count, start_date, end_date


def get_training_streak(user_id: int, db) -> tuple:
    rows = db.execute("""
        SELECT DISTINCT DATE(date) as d FROM training_sessions
        WHERE user_id = ? AND DATE(date) >= DATE('now', '-90 days')
        ORDER BY d DESC
    """, (user_id,)).fetchall()
    dates = [r['d'] for r in rows]
    return calc_consecutive_days(dates, lambda d: True)


def get_sleep_streak(user_id: int, db) -> tuple:
    rows = db.execute("""
        SELECT date, hours FROM sleep_logs
        WHERE user_id = ? AND DATE(date) >= DATE('now', '-90 days')
    """, (user_id,)).fetchall()
    date_hours = {r['date']: r['hours'] for r in rows}
    return calc_consecutive_days(list(date_hours.keys()),
        lambda d: date_hours.get(d, 0) >= 7)


def get_water_streak(user_id: int, db) -> tuple:
    rows = db.execute("""
        SELECT date, amount_ml FROM water_logs
        WHERE user_id = ? AND DATE(date) >= DATE('now', '-90 days')
    """, (user_id,)).fetchall()
    # Group by date, sum amount_ml
    from collections import defaultdict
    date_amounts = defaultdict(int)
    for r in rows:
        date_amounts[r['date']] += r['amount_ml']
    WATER_GOAL = 2500  # default ml per day
    return calc_consecutive_days(list(date_amounts.keys()),
        lambda d: date_amounts.get(d, 0) >= WATER_GOAL)


def upsert_personal_best(user_id: int, streak_type: str, count: int, start: str, end: str, db):
    existing = db.execute(
        "SELECT best_count FROM user_streaks WHERE user_id = ? AND streak_type = ?",
        (user_id, streak_type)).fetchone()
    if not existing or count > existing['best_count']:
        db.execute("""
            INSERT INTO user_streaks (user_id, streak_type, best_count, best_start, best_end, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, streak_type) DO UPDATE SET
                best_count = excluded.best_count,
                best_start = excluded.best_start,
                best_end = excluded.best_end,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, streak_type, count, start, end))
        db.commit()


@progress_bp.route('/api/v1/progress/streaks', methods=['GET'])
def get_streaks():
    """Return current streak + personal best for training, sleep, water."""
    init_data = request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return jsonify({"error": "Unauthorized"}), 401

    if not validate_telegram_init_data(init_data, Config.TELEGRAM_BOT_TOKEN):
        return jsonify({"error": "Invalid init data"}), 401

    tg_user = extract_user_from_init_data(init_data)
    telegram_id = tg_user.get('id')
    user_id = get_user_id(telegram_id)
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    db = get_db()
    db.row_factory = sqlite3.Row

    training_count, training_start, training_end = get_training_streak(user_id, db)
    sleep_count, sleep_start, sleep_end = get_sleep_streak(user_id, db)
    water_count, water_start, water_end = get_water_streak(user_id, db)

    upsert_personal_best(user_id, 'training', training_count, training_start, training_end, db)
    upsert_personal_best(user_id, 'sleep', sleep_count, sleep_start, sleep_end, db)
    upsert_personal_best(user_id, 'water', water_count, water_start, water_end, db)

    best_rows = db.execute(
        "SELECT streak_type, best_count, best_start, best_end FROM user_streaks WHERE user_id = ?",
        (user_id,)).fetchall()
    bests = {r['streak_type']: {'count': r['best_count'], 'start': r['best_start'], 'end': r['best_end']}
             for r in best_rows}

    db.close()
    return jsonify({
        "training": {"current": training_count, "start": training_start, "end": training_end,
                     "best": bests.get('training', {})},
        "sleep": {"current": sleep_count, "start": sleep_start, "end": sleep_end,
                  "best": bests.get('sleep', {})},
        "water": {"current": water_count, "start": water_start, "end": water_end,
                  "best": bests.get('water', {})},
    })
    db.row_factory = sqlite3.Row

    # Weight history — last 30 days (uses created_at, NOT logged_at)
    weight_rows = db.execute("""
        SELECT weight_kg, date FROM weight_logs
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 30
    """, (user_id,)).fetchall()

    weight_history = [
        {"date": r["date"], "weight_kg": r["weight_kg"]}
        for r in reversed(weight_rows)
    ]

    # Measurements — from measurements table (biceps_l, biceps_r, chest, waist, etc.)
    meas_rows = db.execute("""
        SELECT date, biceps_l, biceps_r, chest, waist, hips, thigh_l, thigh_r
        FROM measurements
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 10
    """, (user_id,)).fetchall()

    measurements = {"biceps_l": [], "biceps_r": [], "chest": [], "waist": [], "hips": [], "thigh_l": [], "thigh_r": []}
    for row in reversed(meas_rows):
        d = dict(row)
        for field in measurements:
            if d.get(field) is not None:
                measurements[field].append({"date": d["date"], "value": d[field]})

    # Training sessions per week — from training_sessions table
    try:
        training_rows = db.execute("""
            SELECT strftime('%Y-%W', date) as week, COUNT(*) as count
            FROM training_sessions
            WHERE user_id = ?
            GROUP BY week
            ORDER BY week DESC
            LIMIT 8
        """, (user_id,)).fetchall()
        training_per_week = [
            {"week": r["week"], "count": r["count"]}
            for r in reversed(training_rows)
        ]
    except Exception:
        training_per_week = []

    # Active program — from training_programs table (most recently created)
    active = db.execute("""
        SELECT name, created_at FROM training_programs
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,)).fetchone()

    # Goal weight and date
    user_row = db.execute(
        "SELECT goal_weight, goal_date FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    goal_weight = user_row["goal_weight"] if user_row else None
    goal_date = user_row["goal_date"] if user_row else None

    active_program = {
        "name": active["name"],
        "created_at": active["created_at"]
    } if active else None

    # Current streak — count consecutive weeks with training_sessions entries
    streak = 0
    if training_per_week:
        for t in training_per_week:
            if t['count'] > 0:
                streak += 1
            else:
                break

    # Sleep history — last 14 days
    sleep_rows = db.execute("""
        SELECT date, hours, quality FROM sleep_logs
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 14
    """, (user_id,)).fetchall()

    sleep_history = [
        {"date": r["date"], "hours": r["hours"], "quality": r["quality"]}
        for r in reversed(sleep_rows)
    ]

    # Water history — last 7 days
    water_rows = db.execute("""
        SELECT date, amount_ml FROM water_logs
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT 7
    """, (user_id,)).fetchall()

    water_history = [
        {"date": r["date"], "amount_ml": r["amount_ml"]}
        for r in reversed(water_rows)
    ]

    # Nutrition history — last 7 days summed by date
    nutrition_rows = db.execute("""
        SELECT date, SUM(calories) as total_calories, SUM(protein) as total_protein,
               SUM(carbs) as total_carbs, SUM(fat) as total_fat
        FROM nutrition_logs
        WHERE user_id = ?
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    """, (user_id,)).fetchall()

    nutrition_history = [
        {"date": r["date"], "calories": round(r["total_calories"] or 0),
         "protein": round(r["total_protein"] or 0),
         "carbs": round(r["total_carbs"] or 0),
         "fat": round(r["total_fat"] or 0)}
        for r in reversed(nutrition_rows)
    ]

    db.close()

    # Compute trend data from last 14 weight entries
    trend_data = compute_trend_data(weight_history, goal_weight)

    return jsonify({
        "weight_history": weight_history,
        "measurements": measurements,
        "training_per_week": training_per_week,
        "active_program": active_program,
        "streak_weeks": streak,
        "sleep_history": sleep_history,
        "water_history": water_history,
        "nutrition_history": nutrition_history,
        "total_workouts": sum(t['count'] for t in training_per_week) if training_per_week else 0,
        "avg_workouts_per_week": round(sum(t['count'] for t in training_per_week) / len(training_per_week), 1) if training_per_week else 0,
        "weight_change": round(weight_history[0]['weight_kg'] - weight_history[-1]['weight_kg'], 1) if len(weight_history) >= 2 else None,
        "goal_weight": goal_weight,
        "goal_date": goal_date,
        "weight_trend": {
            "slope_kg_per_week": trend_data.get("slope_kg_per_week"),
            "r2": trend_data.get("r2"),
            "predicted_date": trend_data.get("predicted_date"),
            "status_text": trend_data.get("status_text"),
        },
    })
