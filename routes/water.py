"""Water intake routes."""
from flask import Blueprint, request, jsonify
from models.water_log import log_water, get_daily_water, get_water_history

water_bp = Blueprint('water', __name__)


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


@water_bp.route('/api/v1/water/summary', methods=['GET'])
def get_water_summary():
    """Get today's water intake."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    date_str = request.args.get('date')
    today = get_daily_water(user_id, date_str)
    history = get_water_history(user_id, 7)

    return jsonify({
        "today": today,
        "history": history,
        "target_ml": 2500,  # default target
    }), 200


@water_bp.route('/api/v1/water/log', methods=['POST'])
def add_water():
    """Log water intake (adds to today's total)."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    amount_ml = int(data.get('amount_ml', 0))
    if amount_ml <= 0:
        return jsonify({"error": "amount_ml required"}), 400

    log_id = log_water(user_id, amount_ml)
    return jsonify({"ok": True, "log_id": log_id}), 200
