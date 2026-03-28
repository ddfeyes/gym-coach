"""Training session routes — log and retrieve completed workouts."""
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from models.user import get_user_by_telegram_id
from models.training_session import (
    log_training_session, get_training_sessions, get_sessions_by_date_range,
)
from models.training_program import get_active_training_program

sessions_bp = Blueprint('training_sessions', __name__)


def _get_user_id_from_auth():
    """Resolve user_id from X-Telegram-Init-Data header."""
    init_data = request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return None
    try:
        from routes.auth import validate_telegram_init_data, extract_user_from_init_data
        from config import Config
        if not validate_telegram_init_data(init_data, Config.TELEGRAM_BOT_TOKEN):
            return None
        tg_user = extract_user_from_init_data(init_data)
        if not tg_user:
            return None
        db_user = get_user_by_telegram_id(tg_user.get('id'))
        return db_user['id'] if db_user else None
    except Exception:
        return None


@sessions_bp.route('/api/v1/training-sessions', methods=['POST'])
def create_session():
    """Log a completed training session."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    date_str = data.get('date')  # optional, defaults to today
    program_id = data.get('program_id')  # optional
    duration_minutes = data.get('duration_minutes', 0)
    notes = data.get('notes', '')

    # If program_id not provided, try to get active program
    if program_id is None:
        active = get_active_training_program(user_id)
        if active:
            program_id = active['id']

    session_id = log_training_session(
        user_id=user_id,
        date_str=date_str,
        program_id=program_id,
        duration_minutes=duration_minutes,
        notes=notes,
    )

    return jsonify({"ok": True, "session_id": session_id}), 201


@sessions_bp.route('/api/v1/training-sessions', methods=['GET'])
def list_sessions():
    """List training sessions for the user."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    limit = request.args.get('limit', 30, type=int)
    sessions = get_training_sessions(user_id, limit=limit)
    return jsonify({"sessions": sessions}), 200


@sessions_bp.route('/api/v1/training-sessions/weekly', methods=['GET'])
def weekly_sessions():
    """Get training sessions for the last N weeks (for heatmap)."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    weeks = request.args.get('weeks', 12, type=int)
    today = datetime.now().date()
    start_date = str(today - timedelta(weeks=weeks * 7))

    sessions = get_sessions_by_date_range(user_id, start_date, str(today))

    # Build weekly aggregation
    weekly = {}
    for s in sessions:
        d = datetime.strptime(s['date'], '%Y-%m-%d')
        week_start = d - timedelta(days=d.weekday())
        week_key = week_start.isoformat()
        if week_key not in weekly:
            weekly[week_key] = {'count': 0, 'sessions': []}
        weekly[week_key]['count'] += 1
        weekly[week_key]['sessions'].append(s)

    # Calculate streak
    sorted_weeks = sorted(weekly.keys(), reverse=True)
    streak = 0
    for w in sorted_weeks:
        if weekly[w]['count'] > 0:
            streak += 1
        else:
            break

    return jsonify({
        "weekly": [{"week": k, **v} for k, v in sorted(weekly.items())],
        "streak": streak,
    }), 200
