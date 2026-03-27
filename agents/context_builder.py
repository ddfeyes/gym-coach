import json
from models.user import get_user_by_id


def build_context(user_id: int, module: str) -> dict:
    context = {}

    user = get_user_by_id(user_id)
    if user:
        context["user_profile"] = {
            "name": user["name"],
            "gender": user["gender"],
            "age": user["age"],
            "height_cm": user["height_cm"],
            "weight_kg": user["weight_kg"],
            "experience_level": user["experience_level"],
            "training_days_per_week": user["training_days_per_week"],
            "primary_goal": user["primary_goal"],
            "injuries": json.loads(user["injuries"]) if user.get("injuries") else [],
            "gym_type": user.get("gym_type", "full_gym"),
        }

    # Recent nutrition
    try:
        from models.nutrition import get_daily_summary
        today_summary = get_daily_summary(user_id)
        context["today_nutrition"] = today_summary
    except Exception:
        pass

    # Recent training
    try:
        from models.training_program import get_active_program
        program = get_active_program(user_id)
        if program:
            context["active_program"] = {
                "name": program.get("name"),
                "schedule": program.get("schedule", []),
                "days_count": len(program.get("exercises", [])),
            }
    except Exception:
        pass

    # Recent sleep
    try:
        from models.sleep_log import get_sleep_summary
        sleep_summary = get_sleep_summary(user_id, days=3)
        context["recent_sleep"] = sleep_summary
    except Exception:
        pass

    return context


def format_context_for_prompt(context: dict) -> str:
    if not context:
        return ""

    parts = []
    if "user_profile" in context:
        profile = context["user_profile"]
        parts.append(f"""## Профіль юзера
Ім'я: {profile.get('name', 'Невідомо')}
Стать: {profile.get('gender', 'Невідомо')}
Вік: {profile.get('age', 'Невідомо')}
Зріст: {profile.get('height_cm', 'Невідомо')} см
Вага: {profile.get('weight_kg', 'Невідомо')} кг
Рівень: {profile.get('experience_level', 'Невідомо')}
Тренувань на тиждень: {profile.get('training_days_per_week', 'Невідомо')}
Ціль: {profile.get('primary_goal', 'Невідомо')}
Травми: {profile.get('injuries', [])}
Тип залу: {profile.get('gym_type', 'Невідомо')}""")

    if "today_nutrition" in context:
        n = context["today_nutrition"]
        if n.get("total_calories", 0) > 0:
            parts.append(f"""## Сьогоднішнє харчування
Калорії: {n['total_calories']} ккал
Білок: {n['total_protein']} г
Вуглеводи: {n['total_carbs']} г
Жири: {n['total_fat']} г
Прийомів: {len(n.get('meals', []))}""")

    if "active_program" in context:
        p = context["active_program"]
        parts.append(f"""## Активна програма
{p.get('name', 'Невідома')} — {p.get('days_count', 0)} вправ
Дні: {', '.join(p.get('schedule', []))}""")

    if "recent_sleep" in context:
        s = context["recent_sleep"]
        if s.get("average_hours", 0) > 0:
            parts.append(f"""## Останній сон
Середнє: {s['average_hours']} год/день
Якість: {s['average_quality']}/5""")

    return "\n\n".join(parts)
