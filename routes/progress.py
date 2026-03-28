"""Progress routes — aggregated data for charts and analytics."""
import sqlite3
import os
from flask import Blueprint, request, jsonify
from config import Config
from routes.auth import validate_telegram_init_data, extract_user_from_init_data

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


@progress_bp.route('/api/v1/progress', methods=['GET'])
def get_progress():
    """Return all progress data for a user: weight, measurements, training."""
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

    # Weight history — last 30 days
    weight_rows = db.execute("""
        SELECT weight_kg, logged_at FROM weight_logs
        WHERE user_id = ?
        ORDER BY logged_at DESC
        LIMIT 30
    """, (user_id,)).fetchall()

    weight_history = [
        {"date": r[1][:10], "weight_kg": r[0]}
        for r in reversed(weight_rows)
    ]

    # Measurements — last 30 days for each body part
    measurement_fields = ['biceps', 'chest', 'waist', 'hips', 'thighs']
    measurements_raw = db.execute("""
        SELECT field_name, value, logged_at FROM measurement_logs
        WHERE user_id = ? AND field_name IN ('biceps','chest','waist','hips','thighs')
        ORDER BY logged_at DESC
    """, (user_id,)).fetchall()

    # Group by field, take last 10 entries each
    measurements = {f: [] for f in measurement_fields}
    for field, value, logged_at in measurements_raw:
        if len(measurements[field]) < 10:
            measurements[field].insert(0, {"date": logged_at[:10], "value": value})

    # Training frequency — count per week for last 8 weeks (from actual sessions)
    training_rows = db.execute("""
        SELECT strftime('%Y-%W', date) as week, COUNT(*) as count
        FROM training_sessions
        WHERE user_id = ?
        GROUP BY week
        ORDER BY week DESC
        LIMIT 8
    """, (user_id,)).fetchall()

    training_per_week = [
        {"week": r[0], "count": r[1]}
        for r in reversed(training_rows)
    ]

    # Active program
    active = db.execute("""
        SELECT name, created_at FROM training_programs
        WHERE user_id = ? AND is_active = 1
        LIMIT 1
    """, (user_id,)).fetchone()

    active_program = {
        "name": active[0],
        "created_at": active[1]
    } if active else None

    # Current streak (consecutive weeks with training, from most recent backward)
    streak = 0
    if training_per_week:
        for t in reversed(training_per_week):
            if t['count'] > 0:
                streak += 1
            else:
                break

    # Sleep history — last 14 days
    sleep_rows = db.execute("""
        SELECT hours, quality, logged_at FROM sleep_logs
        WHERE user_id = ?
        ORDER BY logged_at DESC
        LIMIT 14
    """, (user_id,)).fetchall()

    sleep_history = [
        {"date": r[2][:10], "hours": r[0], "quality": r[1]}
        for r in reversed(sleep_rows)
    ]

    db.close()

    return jsonify({
        "weight_history": weight_history,
        "measurements": measurements,
        "training_per_week": training_per_week,
        "active_program": active_program,
        "streak_weeks": streak,
        "sleep_history": sleep_history,
    })
