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
            "injuries": json.loads(user["injuries"]) if user["injuries"] else [],
            "gym_type": user["gym_type"],
        }

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

    return "\n\n".join(parts)
