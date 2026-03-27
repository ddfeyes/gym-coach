"""Sleep tracking routes."""
from flask import Blueprint, request, jsonify
from models.sleep_log import log_sleep, get_sleep_summary

sleep_bp = Blueprint('sleep', __name__)


def _get_user_id_from_auth():
    init_data = request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return None
    try:
        from routes.auth import validate_telegram_init_data, extract_user_from_init_data
        if not validate_telegram_init_data(init_data, __import__('config').Config.TELEGRAM_BOT_TOKEN):
            return None
        tg_user = extract_user_from_init_data(init_data)
        if not tg_user:
            return None
        from models.user import get_user_by_telegram_id
        db_user = get_user_by_telegram_id(tg_user.get('id'))
        return db_user['id'] if db_user else None
    except Exception:
        return None


@sleep_bp.route('/api/v1/sleep/summary', methods=['GET'])
def get_summary():
    """Get sleep summary for the last 7 days."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    days = request.args.get('days', 7, type=int)
    summary = get_sleep_summary(user_id, days)
    return jsonify(summary), 200


@sleep_bp.route('/api/v1/sleep/log', methods=['POST'])
def add_sleep():
    """Log sleep hours for today (or specified date)."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    hours = float(data.get('hours', 0))
    if hours <= 0 or hours > 24:
        return jsonify({"error": "hours must be between 0 and 24"}), 400

    quality = int(data.get('quality', 3))
    if quality < 1 or quality > 5:
        quality = 3

    log_date = data.get('date')
    notes = data.get('notes', '')

    log_id = log_sleep(user_id, hours, quality, notes, log_date)
    return jsonify({"ok": True, "log_id": log_id}), 200
