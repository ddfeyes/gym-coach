"""Body measurements routes."""
from flask import Blueprint, request, jsonify
from models.measurement import log_measurement, get_measurement_history, get_latest_measurement

measurements_bp = Blueprint('measurements', __name__)


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


@measurements_bp.route('/api/v1/measurements', methods=['GET'])
def get_measurements():
    """Get measurement history."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    limit = request.args.get('limit', 30, type=int)
    history = get_measurement_history(user_id, limit)
    latest = get_latest_measurement(user_id)
    return jsonify({"history": history, "latest": latest}), 200


@measurements_bp.route('/api/v1/measurements', methods=['POST'])
def add_measurement():
    """Log body measurements."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    log_date = data.get('date')

    try:
        log_id = log_measurement(
            user_id,
            date=log_date,
            biceps_l=data.get('biceps_l'),
            biceps_r=data.get('biceps_r'),
            chest=data.get('chest'),
            waist=data.get('waist'),
            hips=data.get('hips'),
            thigh_l=data.get('thigh_l'),
            thigh_r=data.get('thigh_r'),
            notes=data.get('notes', ''),
        )
        return jsonify({"ok": True, "log_id": log_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
