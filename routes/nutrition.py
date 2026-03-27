"""Nutrition routes — meal logging, macro tracking, and AI-powered calculations."""
import json
import os
from datetime import date
from flask import Blueprint, request, jsonify
from models.user import get_user_by_id
from models.nutrition import log_meal, get_daily_summary, get_weekly_summary

nutrition_bp = Blueprint('nutrition', __name__)

BASE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'agents', 'prompts', 'base_prompt.txt')


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


@nutrition_bp.route('/api/v1/nutrition/summary', methods=['GET'])
def daily_nutrition():
    """Get daily nutrition summary for today (or specified date)."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    target_date = request.args.get('date', str(date.today()))
    summary = get_daily_summary(user_id, target_date)

    # Get user targets
    user = get_user_by_id(user_id)
    targets = _calculate_targets(user)

    return jsonify({
        "summary": summary,
        "targets": targets,
    }), 200


@nutrition_bp.route('/api/v1/nutrition/log', methods=['POST'])
def add_meal():
    """Log a meal with optional AI-powered macro calculation."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or 'description' not in data:
        return jsonify({"error": "description required"}), 400

    description = data['description']
    meal_type = data.get('meal_type', 'meal')
    calories = float(data.get('calories', 0) or 0)
    protein = float(data.get('protein', 0) or 0)
    carbs = float(data.get('carbs', 0) or 0)
    fat = float(data.get('fat', 0) or 0)

    # If macros not provided, try AI calculation
    if calories == 0 and protein == 0 and carbs == 0 and fat == 0:
        macros = _estimate_macros_ai(description, user_id)
        if macros:
            calories = macros.get('calories', 0)
            protein = macros.get('protein', 0)
            carbs = macros.get('carbs', 0)
            fat = macros.get('fat', 0)

    log_id = log_meal(user_id, description, meal_type, calories, protein, carbs, fat)
    return jsonify({"ok": True, "log_id": log_id}), 200


@nutrition_bp.route('/api/v1/nutrition/targets', methods=['GET'])
def get_targets():
    """Get personalized calorie and macro targets."""
    user_id = _get_user_id_from_auth()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = get_user_by_id(user_id)
    targets = _calculate_targets(user)
    return jsonify({"targets": targets}), 200


def _calculate_targets(user: dict) -> dict:
    """Calculate personalized calorie and macro targets based on user profile."""
    if not user:
        return {"calories": 2000, "protein": 150, "carbs": 200, "fat": 70}

    weight = user.get('weight_kg', 70)
    height = user.get('height_cm', 170)
    age = user.get('age', 30)
    gender = user.get('gender', 'male')
    goal = user.get('primary_goal', 'muscle_gain')
    experience = user.get('experience_level', 'beginner')

    # Mifflin-St Jeor BMR
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Activity multiplier (assume moderate activity based on training days)
    training_days = user.get('training_days_per_week', 3)
    activity_multiplier = 1.55  # moderate

    tdee = bmr * activity_multiplier

    # Adjust for goal
    if goal == 'muscle_gain':
        calories = tdee + 400
    elif goal == 'fat_loss':
        calories = tdee - 400
    elif goal == 'strength':
        calories = tdee + 200
    elif goal == 'recomposition':
        calories = tdee
    else:
        calories = tdee

    # Protein: 1.6-2.2g/kg depending on goal
    if goal in ('muscle_gain', 'strength'):
        protein = weight * 2.0
    elif goal == 'fat_loss':
        protein = weight * 2.2
    else:
        protein = weight * 1.6

    # Fat: 0.8-1g/kg
    fat = weight * 0.9

    # Carbs: remainder
    carbs = (calories - protein * 4 - fat * 9) / 4

    return {
        "calories": round(calories),
        "protein": round(protein),
        "carbs": round(carbs),
        "fat": round(fat),
    }


def _estimate_macros_ai(description: str, user_id: int) -> dict | None:
    """Use AI to estimate macros for a meal description."""
    try:
        base_prompt_path = BASE_PROMPT_PATH
        with open(base_prompt_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read()
    except FileNotFoundError:
        base_prompt = "Ти — Body Coach AI, дієтолог."

    user = get_user_by_id(user_id)
    weight = user.get('weight_kg', 70) if user else 70

    system_prompt = f"""{base_prompt}

Оціни приблизну калорійність і макроси для наступного прийому їжі.
Відповідь — ТІЛЬКИ JSON (без markdown), формат:
{{
  "calories": 450,
  "protein": 35,
  "carbs": 40,
  "fat": 15
}}

Без пояснень, ТІЛЬКИ JSON."""

    try:
        from agents.base import ai
        response = ai.chat(system_prompt=system_prompt, user_message=description, context={})
        text = response.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return None
