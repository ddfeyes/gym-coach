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

    db.close()

    return jsonify({
        "weight_history": weight_history,
        "measurements": measurements,
        "training_per_week": training_per_week,
        "active_program": active_program,
        "streak_weeks": streak,
        "sleep_history": sleep_history,
        "water_history": water_history,
    })
