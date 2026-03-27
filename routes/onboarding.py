"""Onboarding routes — profile creation and updates via Telegram Mini App auth."""
import json
from flask import Blueprint, request, jsonify
from models.user import get_user_by_telegram_id, create_user, update_user

onboarding_bp = Blueprint('onboarding', __name__)


@onboarding_bp.route('/api/v1/onboarding', methods=['POST'])
def submit_onboarding():
    """Create or update user profile from Mini App onboarding form.
    
    Requires X-Telegram-Init-Data header for authentication.
    """
    init_data = request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return jsonify({"error": "Unauthorized"}), 401

    # Validate init data
    from routes.auth import validate_telegram_init_data, extract_user_from_init_data
    if not validate_telegram_init_data(init_data, __import__('config').Config.TELEGRAM_BOT_TOKEN):
        return jsonify({"error": "Invalid init data"}), 401

    tg_user = extract_user_from_init_data(init_data)
    if not tg_user:
        return jsonify({"error": "No user in init data"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    telegram_id = tg_user.get('id')
    if not telegram_id:
        return jsonify({"error": "telegram_id required"}), 400

    # Check if user exists
    existing = get_user_by_telegram_id(telegram_id)

    required_fields = ['name', 'gender', 'age', 'height_cm', 'weight_kg',
                       'experience_level', 'training_days_per_week', 'primary_goal']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    user_data = {
        'telegram_id': telegram_id,
        'username': tg_user.get('username'),
        'name': data['name'],
        'gender': data['gender'],
        'age': int(data['age']),
        'height_cm': float(data['height_cm']),
        'weight_kg': float(data['weight_kg']),
        'experience_level': data['experience_level'],
        'training_days_per_week': int(data['training_days_per_week']),
        'primary_goal': data['primary_goal'],
        'session_duration_minutes': int(data.get('session_duration_minutes', 60)),
        'available_equipment': json.dumps(data.get('available_equipment', [])),
        'gym_type': data.get('gym_type', 'full_gym'),
        'injuries': json.dumps(data.get('injuries', [])),
        'exercise_restrictions': json.dumps(data.get('exercise_restrictions', [])),
        'secondary_goals': json.dumps(data.get('secondary_goals', [])),
        'language': data.get('language', 'uk'),
        'onboarding_completed': 1,
    }

    if existing:
        update_user(existing['id'], **user_data)
        user_id = existing['id']
    else:
        user_id = create_user(**user_data)

    return jsonify({"ok": True, "user_id": user_id})


@onboarding_bp.route('/api/v1/profile', methods=['GET'])
def get_profile():
    """Get current user's profile.
    
    Requires X-Telegram-Init-Data header.
    """
    init_data = request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return jsonify({"error": "Unauthorized"}), 401

    from routes.auth import validate_telegram_init_data, extract_user_from_init_data
    if not validate_telegram_init_data(init_data, __import__('config').Config.TELEGRAM_BOT_TOKEN):
        return jsonify({"error": "Invalid init data"}), 401

    tg_user = extract_user_from_init_data(init_data)
    telegram_id = tg_user.get('id')

    user = get_user_by_telegram_id(telegram_id)
    if not user:
        return jsonify({"error": "User not found", "onboarding_completed": False}), 404

    # Remove sensitive internal fields
    safe_fields = [
        'id', 'name', 'gender', 'age', 'height_cm', 'weight_kg',
        'experience_level', 'training_days_per_week', 'primary_goal',
        'secondary_goals', 'gym_type', 'available_equipment',
        'injuries', 'onboarding_completed', 'language',
    ]
    profile = {k: v for k, v in user.items() if k in safe_fields}

    return jsonify(profile)
