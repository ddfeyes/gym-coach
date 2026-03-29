import json
from flask import Blueprint, request, jsonify
from config import Config
from models.user import get_user_by_telegram_id
from models.workout_plan import (
    create_workout_plan, get_active_plan, mark_day_complete,
    get_recent_training_history, get_week_start,
)
from routes.auth import validate_telegram_init_data, extract_user_from_init_data
from datetime import date, timedelta

plan_bp = Blueprint("plan", __name__)


def _get_user_from_request():
    """Authenticate user via X-Telegram-Init-Data header."""
    init_data = request.headers.get("X-Telegram-Init-Data")
    if not init_data:
        return None, jsonify({"error": "Unauthorized"}), 401
    if not validate_telegram_init_data(init_data, Config.TELEGRAM_BOT_TOKEN):
        return None, jsonify({"error": "Invalid init data"}), 401
    tg_user = extract_user_from_init_data(init_data)
    if not tg_user:
        return None, jsonify({"error": "User not found"}), 401
    db_user = get_user_by_telegram_id(tg_user.get("id"))
    if not db_user:
        return None, jsonify({"error": "User not registered"}), 401
    return db_user, None, None


def _build_ai_context(user: dict, history: list) -> str:
    """Build text context from user profile and training history for AI prompt."""
    lines = [
        f"User: {user['name']}, {user['age']}yo {user['gender']}",
        f"Experience: {user['experience_level']}",
        f"Training days/week: {user['training_days_per_week']}",
        f"Primary goal: {user['primary_goal']}",
        f"Equipment: {user['available_equipment']}",
        f"Gym type: {user['gym_type']}",
    ]
    if history:
        lines.append("Recent training sessions:")
        for s in history[-14:]:
            lines.append(f"  - {s['date']}: {s.get('notes', 'no notes')}")
    return "\n".join(lines)


@plan_bp.route("/training-program/generate", methods=["POST"])
def generate_plan():
    user, error, status = _get_user_from_request()
    if error:
        return error, status

    data = request.get_json() or {}

    # Determine week_start
    ws = data.get("week_start")
    if ws:
        week_start = ws
    else:
        today = date.today()
        # If today is already past midweek, start next week
        if today.weekday() >= 3:
            today = today + timedelta(days=7 - today.weekday())
        week_start = get_week_start(today)

    # Check if plan already exists
    existing = get_active_plan(user["id"], week_start)
    if existing:
        return jsonify({"plan_id": existing["id"], "week_start": week_start, "days": existing["days"], "already_exists": True})

    # Build AI context
    history = get_recent_training_history(user["id"])
    context = _build_ai_context(user, history)

    # Build AI prompt
    equipment_list = user.get("available_equipment", "[]")
    if isinstance(equipment_list, str):
        equipment_list = json.loads(equipment_list)
    equipment_str = ", ".join(equipment_list) if equipment_list else "full gym"

    ai_prompt = f"""Generate a 7-day training plan for the following user.

{context}

Equipment available: {equipment_str}

Generate a JSON array with 7 entries (one per day, Monday to Sunday). Each day must be:
{{
  "day_idx": 0-6,
  "title": "Day title (e.g. Upper Body Push, Rest Day, Lower Body)",
  "is_rest_day": true/false,
  "muscle_groups": ["chest", "triceps", "shoulders"] (empty if rest day),
  "estimated_minutes": 45,
  "exercises": [  (empty if rest day)
    {{
      "title": "Exercise name",
      "reps": "8-12",
      "weight_kg": 20.0
    }}
  ]
}}

Rules:
- No muscle group may appear on consecutive days (enforce rest/recovery)
- Respect training_days_per_week from user profile (use rest days for the rest)
- For rest days: is_rest_day=true, exercises=[], title="Rest Day"
- Use realistic weight suggestions based on experience level
- Return ONLY the JSON array, no markdown, no explanation
"""

    try:
        from agents.base import ai
        response_text = ai.chat(
            system_prompt="You are a fitness planning assistant. Return ONLY valid JSON.",
            user_message=ai_prompt,
            context={},
        )
    except Exception as e:
        return jsonify({"error": f"AI error: {str(e)}"}), 500

    # Parse AI response
    try:
        # Try to extract JSON from response
        text = response_text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        plan_data = json.loads(text)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse AI response: {str(e)}", "raw": response_text[:500]}), 500

    if not isinstance(plan_data, list) or len(plan_data) != 7:
        return jsonify({"error": "AI returned invalid plan format", "raw": response_text[:500]}), 500

    plan_id = create_workout_plan(user["id"], week_start, plan_data)
    result = get_active_plan(user["id"], week_start)

    return jsonify({
        "plan_id": plan_id,
        "week_start": week_start,
        "days": result["days"],
    })


@plan_bp.route("/training-program", methods=["GET"])
def current_plan():
    user, error, status = _get_user_from_request()
    if error:
        return error, status

    week_start = get_week_start()
    plan = get_active_plan(user["id"], week_start)
    if not plan:
        return jsonify({"has_program": False})

    # Transform to frontend-expected format: flat exercises list with day number
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
    schedule = []
    flat_exercises = []
    for day in plan.get("days", []):
        day_idx = day.get("day_idx", 0)
        title = day.get("title", f"День {day_idx + 1}")
        schedule.append(f"{day_names[day_idx]}: {title}")
        primary_muscle = (day.get("muscle_groups") or [""])[0]
        for ex in day.get("exercises", []):
            flat_exercises.append({
                "day": day_idx + 1,
                "muscle_group": primary_muscle,
                "exercise": ex.get("exercise", ""),
                "sets": ex.get("sets", 3),
                "reps": ex.get("reps", ""),
                "rest_seconds": ex.get("rest_seconds", 60),
                "notes": ex.get("notes", ""),
            })

    return jsonify({
        "has_program": True,
        "program": {
            "name": plan.get("name", "Тренувальна програма"),
            "schedule": schedule,
            "exercises": flat_exercises,
        },
    })


@plan_bp.route("/training-program/<int:plan_id>/complete/<int:day_idx>", methods=["POST"])
def complete_day(plan_id: int, day_idx: int):
    user, error, status = _get_user_from_request()
    if error:
        return error, status

    if day_idx < 0 or day_idx > 6:
        return jsonify({"error": "day_idx must be 0-6"}), 400

    # IDOR fix: verify plan belongs to this user
    from database import get_db
    db = get_db()
    row = db.execute(
        "SELECT id FROM workout_plans WHERE id = ? AND user_id = ?",
        (plan_id, user["id"])
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Plan not found"}), 404

    mark_day_complete(plan_id, day_idx)

    # Log to training_sessions
    from models.training_session import log_training_session
    today = date.today().isoformat()
    log_training_session(user["id"], date_str=today, duration_minutes=0, notes=f"Plan {plan_id} day {day_idx} completed")

    return jsonify({"ok": True})
