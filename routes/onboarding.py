"""Onboarding routes — profile creation and updates via Telegram Mini App auth."""
import json
import threading
from flask import Blueprint, request, jsonify
from models.user import get_user_by_telegram_id, create_user, update_user

onboarding_bp = Blueprint('onboarding', __name__)


def _generate_training_async(user_id: int):
    """Generate training program in background thread."""
    def _run():
        try:
            from models.user import get_user_by_id
            from models.training_program import create_training_program, set_active_program
            from agents.base import ai
            import os

            user = get_user_by_id(user_id)
            if not user:
                return

            base_prompt_path = os.path.join(os.path.dirname(__file__), '..', 'agents', 'prompts', 'base_prompt.txt')
            try:
                with open(base_prompt_path, 'r', encoding='utf-8') as f:
                    base_prompt = f.read()
            except FileNotFoundError:
                base_prompt = "Ти — Body Coach AI, персональний фітнес-тренер."

            context_parts = [
                f"Ім'я: {user['name']}",
                f"Стать: {user['gender']}",
                f"Вік: {user['age']}",
                f"Зріст: {user['height_cm']} см",
                f"Вага: {user['weight_kg']} кг",
                f"Досвід: {user['experience_level']}",
                f"Тренувань/тиждень: {user['training_days_per_week']}",
                f"Ціль: {user['primary_goal']}",
                f"Тип залу: {user['gym_type']}",
            ]
            if user.get('injuries'):
                context_parts.append(f"Травми/обмеження: {user['injuries']}")

            system_prompt = f"""{base_prompt}

## Контекст користувача
{chr(10).join(context_parts)}

## Завдання
Згенеруй персональну тренувальну програму JSON. Відповідь — ТІЛЬКИ JSON (без markdown):

{{
  "name": "Назва програми",
  "program_type": "split",
  "schedule": ["День 1: Груди+Трицепси", "День 2: Спина+Біцепси", ...],
  "exercises": [
    {{
      "day": 1,
      "muscle_group": "Груди",
      "exercise": "Назва вправи",
      "sets": 4,
      "reps": "8-12",
      "rest_seconds": 90,
      "notes": ""
    }}
  ],
  "notes": "Загальні нотатки"
}}

Вимоги:
- {user['training_days_per_week']} тренувань на тиждень
- Врахуй досвід: {user['experience_level']} і ціль: {user['primary_goal']}"""

            response = ai.chat(
                system_prompt=system_prompt,
                user_message="Згенеруй персональну тренувальну програму",
                context={},
            )

            text = response.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            program_data = json.loads(text.strip())

            program_id = create_training_program(
                user_id=user_id,
                name=program_data.get('name', 'Training Program'),
                schedule=program_data.get('schedule', []),
                exercises=program_data.get('exercises', []),
                program_type=program_data.get('program_type', 'split'),
                notes=program_data.get('notes', ''),
            )
            set_active_program(user_id, program_id)
        except Exception as e:
            print(f"[onboarding] Training program generation failed: {e}")

    thread = threading.Thread(target=_run)
    thread.start()


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

    # Auto-generate training program in background
    _generate_training_async(user_id)

    return jsonify({"ok": True, "user_id": user_id, "generating_program": True})


@onboarding_bp.route('/api/v1/profile', methods=['GET', 'PATCH'])
def get_or_update_profile():
    """Get or update current user's profile.

    GET: Returns profile + latest weight + weight history
    PATCH: Updates profile fields (name, weight_kg, primary_goal, etc.)
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

    safe_fields = [
        'id', 'name', 'gender', 'age', 'height_cm', 'weight_kg',
        'experience_level', 'training_days_per_week', 'primary_goal',
        'secondary_goals', 'gym_type', 'available_equipment',
        'injuries', 'onboarding_completed', 'language',
    ]

    if request.method == 'GET':
        # Include weight data
        try:
            from models.weight_log import get_weight_history, get_latest_weight
            weight_history = get_weight_history(user['id'])
            latest_weight = get_latest_weight(user['id'])
        except Exception:
            weight_history = []
            latest_weight = None

        # Include daily targets (TDEE, calories, macros)
        try:
            from routes.nutrition import _calculate_targets
            targets = _calculate_targets(user)
        except Exception:
            targets = {}

        profile = {k: v for k, v in user.items() if k in safe_fields}
        profile['weight_history'] = weight_history
        profile['latest_weight'] = latest_weight
        profile['targets'] = targets
        return jsonify(profile)

    # PATCH — update profile
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    updatable = ['name', 'weight_kg', 'primary_goal', 'training_days_per_week',
                 'experience_level', 'gym_type', 'age']
    update_data = {k: v for k, v in data.items() if k in updatable}

    if update_data:
        if 'age' in update_data:
            update_data['age'] = int(update_data['age'])
        if 'weight_kg' in update_data:
            update_data['weight_kg'] = float(update_data['weight_kg'])
        if 'training_days_per_week' in update_data:
            update_data['training_days_per_week'] = int(update_data['training_days_per_week'])
        update_user(user['id'], **update_data)

    if 'weight_kg' in data:
        try:
            from models.weight_log import log_weight
            log_weight(user['id'], float(data['weight_kg']))
        except Exception:
            pass

    return jsonify({"ok": True})
