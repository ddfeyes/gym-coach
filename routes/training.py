"""Training program routes — generate and manage personalized training programs."""
import json
import os
from flask import Blueprint, request, jsonify
from models.user import get_user_by_telegram_id, get_user_by_id
from models.training_program import (
    create_training_program, get_active_training_program,
    get_training_programs, set_active_program, delete_training_program,
)

training_bp = Blueprint('training', __name__)

BASE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'agents', 'prompts', 'base_prompt.txt')


def _get_user_id_from_auth():
    """Resolve user_id from X-Telegram-Init-Data header."""
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
        db_user = get_user_by_telegram_id(tg_user.get('id'))
        return db_user['id'] if db_user else None
    except Exception:
        return None


def _load_base_prompt():
    try:
        with open(BASE_PROMPT_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Ти — Body Coach AI, персональний фітнес-тренер."


@training_bp.route('/api/v1/training-program', methods=['GET'])
def get_program():
    """Get the user's active training program."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    program = get_active_training_program(user_id)
    if not program:
        return jsonify({"has_program": False}), 200

    return jsonify({"has_program": True, "program": program}), 200


@training_bp.route('/api/v1/training-program/generate', methods=['POST'])
def generate_program():
    """Generate a new training program using AI based on user profile."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.get('onboarding_completed'):
        return jsonify({"error": "Complete onboarding first"}), 400

    # Load base prompt
    base_prompt = _load_base_prompt()

    # Build user context
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
Згенеруй персональну тренувальну програму у форматі JSON. Відповідь ДОЛЖНА бути лише JSON (без будь-якого іншого тексту):

{{
  "name": "Назва програми (напр. 'Push/Pull/Legs 3 дні')",
  "program_type": "split | upper_lower | full_body | custom",
  "schedule": ["День 1: Груди+Трицепси", "День 2: Спина+Біцепси", ...],
  "exercises": [
    {{
      "day": 1,
      "muscle_group": "Груди",
      "exercise": "Назва вправи",
      "sets": 4,
      "reps": "8-12",
      "rest_seconds": 90,
      "notes": "Техніка або варіація"
    }},
    ...
  ],
  "notes": "Загальні нотатки до програми"
}}

Вимоги:
- Врахуй досвід: {user['experience_level']}
- Врахуй ціль: {user['primary_goal']}
- {user['training_days_per_week']} тренувань на тиждень
- Вкажи конкретні вправи з підходами, повторами і відпочинком
- Відповідь — ТІЛЬКИ JSON, без markdown код-блоків"""

    try:
        from agents.base import ai
        response_text = ai.chat(
            system_prompt=system_prompt,
            user_message="Згенеруй персональну тренувальну програму",
            context={},
        )
    except Exception as e:
        return jsonify({"error": f"AI error: {str(e)}"}), 500

    # Parse JSON from response
    try:
        import re as _re
        text = response_text.strip()
        # Strip markdown code blocks
        if '```' in text:
            parts = text.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    part = part[4:].strip()
                try:
                    program_data = json.loads(part)
                    break
                except Exception:
                    continue
            else:
                raise json.JSONDecodeError("no valid json block", text, 0)
        else:
            # Try to extract JSON object directly
            m = _re.search(r'\{.*\}', text, _re.DOTALL)
            if m:
                program_data = json.loads(m.group(0))
            else:
                program_data = json.loads(text)
    except (json.JSONDecodeError, Exception):
        return jsonify({"error": "Failed to parse AI response", "raw": response_text}), 500

    # Normalize schedule: if dict, convert days list to strings
    schedule = program_data.get('schedule', [])
    if isinstance(schedule, dict):
        days = schedule.get('days', [])
        schedule = [f"День {i+1}: {d}" for i, d in enumerate(days)] if days else []
    elif not isinstance(schedule, list):
        schedule = []

    # Normalize exercises: must be list of dicts
    exercises = program_data.get('exercises', [])
    if not isinstance(exercises, list):
        exercises = []

    # Save to DB
    try:
        program_id = create_training_program(
            user_id=user_id,
            name=program_data.get('name', 'Training Program'),
            schedule=schedule,
            exercises=exercises,
            program_type=program_data.get('program_type', 'split'),
            notes=program_data.get('notes', ''),
        )
        # Deactivate other programs
        set_active_program(user_id, program_id)
    except Exception as e:
        return jsonify({"error": f"DB error: {str(e)}"}), 500

    return jsonify({
        "ok": True,
        "program_id": program_id,
        "program": program_data,
    }), 200


@training_bp.route('/api/v1/training-program/history', methods=['GET'])
def list_programs():
    """List user's training programs."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    programs = get_training_programs(user_id)
    return jsonify({"programs": programs}), 200
