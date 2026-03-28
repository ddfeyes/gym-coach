import json
import os
from config import Config


def handle_telegram_update(update_data: dict) -> dict:
    """Обробка webhook оновлення від Telegram"""
    message = update_data.get('message')
    if not message:
        return {"ok": True}

    chat_id = message['chat']['id']
    text = message.get('text', '')

    if text == '/start':
        return _handle_start(chat_id)
    if text == '/help' or text == '/menu':
        return _handle_help(chat_id)
    if text.startswith('/today') or text.startswith('/stats'):
        return _handle_today(chat_id)
    if text.startswith('/program'):
        return _handle_program(chat_id)
    if text.startswith('/log '):
        return _handle_log(chat_id, text[5:].strip())
    if text.startswith('/workout'):
        return _handle_workout(chat_id)
    if text.startswith('/week'):
        return _handle_week(chat_id)
    if text.startswith('/tdee'):
        return _handle_tdee(chat_id)

    # Wire AI chat for all other messages
    return _handle_ai_message(chat_id, text)


def _handle_start(chat_id: int) -> dict:
    """Обробка команди /start"""
    welcome_text = (
        "Привіт! 👋 Я Body Coach AI — твій персональний тренер, "
        "дієтолог і health-коуч.\n\n"
        "Давай познайомимось і я створю для тебе ідеальну програму 💪"
    )

    webapp_url = Config.TELEGRAM_WEBHOOK_URL
    if webapp_url:
        base_url = webapp_url.replace('/webhook/telegram', '')
    else:
        base_url = ''

    reply = {
        "method": "sendMessage",
        "chat_id": chat_id,
        "text": welcome_text,
        "reply_markup": json.dumps({
            "inline_keyboard": [[
                {
                    "text": "🏋️ Відкрити додаток",
                    "web_app": {"url": base_url}
                }
            ]]
        }),
    }
    return reply


def _handle_help(chat_id: int) -> dict:
    """Обробка команди /help"""
    webapp_url = Config.TELEGRAM_WEBHOOK_URL
    if webapp_url:
        base_url = webapp_url.replace('/webhook/telegram', '')
    else:
        base_url = ''

    help_text = (
        "📱 *Body Coach AI — Команди*\n\n"
        "/start — Відкрити Mini App і почати онбординг\n"
        "/help — Показати це меню\n"
        "/today — Сьогоднішній трекінг (калорії, сон)\n"
        "/week — Тижнева статистика\n"
        "/tdee — Добова норма калорій та макроси\n"
        "/program — Твоя тренувальна програма\n"
        "/log <опис> — Швидко залогировать прийом їжі\n"
        "/workout — Залогировать тренування\n\n"
        "💬 Або просто напиши мені — я відповім!"
    )

    reply = {
        "method": "sendMessage",
        "chat_id": chat_id,
        "text": help_text,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps({
            "inline_keyboard": [[
                {
                    "text": "🏋️ Відкрити додаток",
                    "web_app": {"url": base_url}
                }
            ]]
        }),
    }
    return reply


def _get_user(chat_id: int):
    """Get user by telegram_id."""
    try:
        from models.user import get_user_by_telegram_id
        return get_user_by_telegram_id(chat_id)
    except Exception:
        return None


def _calculate_tdee(user: dict) -> dict:
    """Calculate TDEE and macro targets from user data."""
    weight = float(user.get('weight_kg', 70))
    height = float(user.get('height_cm', 170))
    age = int(user.get('age', 25))
    gender = user.get('gender', 'male')
    goal = user.get('primary_goal', 'health')
    training_days = int(user.get('training_days_per_week', 3))

    # Mifflin-St Jeor BMR
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Activity multiplier
    if training_days <= 1:
        activity = 1.2
    elif training_days <= 3:
        activity = 1.375
    elif training_days <= 5:
        activity = 1.55
    else:
        activity = 1.725

    tdee = bmr * activity

    # Goal adjustment
    if goal == 'muscle_gain':
        target = tdee + 300
    elif goal == 'fat_loss':
        target = tdee - 500
    elif goal in ('strength', 'health', 'recomposition'):
        target = tdee
    else:
        target = tdee

    # Macro targets
    protein_g = weight * 2.0  # 2g per kg
    fat_g = weight * 1.0       # 1g per kg
    protein_cal = protein_g * 4
    fat_cal = fat_g * 9
    carbs_cal = max(0, target - protein_cal - fat_cal)
    carbs_g = carbs_cal / 4

    return {
        'tdee': round(tdee),
        'target': round(target),
        'protein_g': round(protein_g),
        'carbs_g': round(carbs_g),
        'fat_g': round(fat_g),
    }


def _handle_today(chat_id: int) -> dict:
    """Show today's tracking summary."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.nutrition import get_daily_summary
        from models.sleep_log import get_latest_weight, get_sleep_history
        from models.training_session import get_sessions_by_date_range
        from models.water_log import get_daily_water

        today = str(__import__('datetime').date.today())
        nutrition = get_daily_summary(user['id'], today)
        latest_weight = get_latest_weight(user['id'])
        today_sessions = get_sessions_by_date_range(user['id'], today, today)
        macros = _calculate_tdee(user)
        today_water = get_daily_water(user['id'], today)
        sleep_history = get_sleep_history(user['id'], 1)
        today_sleep = sleep_history[0] if sleep_history else None

        lines = ["📊 *Сьогодні:*"]

        if nutrition.get('total_calories', 0) > 0:
            cal = round(nutrition['total_calories'])
            remaining = macros['target'] - cal
            lines.append(f"🍽️ {cal} / {macros['target']} ккал")
            if remaining > 0:
                lines.append(f"   🔥 Залишилось: {remaining} ккал")
            else:
                lines.append(f"   ⚠️ Перевищено: {abs(remaining)} ккал")
            lines.append(f"🥩 Б: {round(nutrition['total_protein'])}/{macros['protein_g']} г | В: {round(nutrition['total_carbs'])}/{macros['carbs_g']} г | Ж: {round(nutrition['total_fat'])}/{macros['fat_g']} г")
            lines.append(f"Прийомів: {len(nutrition.get('meals', []))}")
        else:
            lines.append(f"🍽️ Немає даних | Денна норма: {macros['target']} ккал")
            lines.append(f"🥩 Б: 0/{macros['protein_g']} г | В: 0/{macros['carbs_g']} г | Ж: 0/{macros['fat_g']} г")

        if latest_weight:
            lines.append(f"⚖️ Вага: {latest_weight['weight_kg']} кг")

        # Water (target 2500ml)
        water_ml = today_water.get('amount_ml', 0)
        water_target = 2500
        if water_ml > 0:
            lines.append(f"💧 {water_ml} / {water_target} мл")
        else:
            lines.append(f"💧 0 / {water_target} мл")

        # Sleep
        if today_sleep:
            hours = today_sleep.get('hours', 0)
            quality = today_sleep.get('quality', 0)
            q_stars = "⭐" * quality if quality else "-"
            lines.append(f"😴 Сон: {hours} год {q_stars}")

        if today_sessions:
            session = today_sessions[0]
            program = session.get('program_name', 'Тренування')
            duration = session.get('duration_minutes', 0)
            lines.append(f"💪 {program} ({duration} хв)")
        else:
            lines.append("💪 Тренувань немає / /workout щоб залогити")

        lines.append("")
        lines.append("💪 Натисни /log щоб додати прийом їжі!")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }
    except Exception as e:
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити дані. Спробуй пізніше.",
        }


def _handle_program(chat_id: int) -> dict:
    """Show user's current training program."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.training_program import get_active_training_program
        program = get_active_training_program(user['id'])
        if not program:
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "🏋️ У тебе ще немає програми! Відкрий додаток і згенеруй свою першу програму.",
            }

        lines = [f"🏋️ *{program.get('name', 'Програма')}*\n"]
        for ex in program.get('exercises', [])[:8]:
            lines.append(
                f"• {ex['exercise']} — {ex['sets']}×{ex['reps']} ({ex.get('muscle_group', '')})"
            )

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }
    except Exception as e:
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити програму.",
        }


def _handle_log(chat_id: int, description: str) -> dict:
    """Quick log a meal."""
    if not description:
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Використання: /log <опис прийому>\n\nПриклад: /log Обід: курча з рисом",
        }

    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Спочатку пройди онбординг — натисни /start!",
        }

    try:
        from models.nutrition import log_meal
        log_id = log_meal(user['id'], description, 'quick_log', 0, 0, 0, 0)
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": f"✅ Додано: {description}\n\nВідкрий додаток щоб побачити розрахунок калорій AI 🕸️",
        }
    except Exception as e:
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося додати. Спробуй пізніше.",
        }


def _handle_workout(chat_id: int) -> dict:
    """Quick log a training session."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Спочатку пройди онбординг — натисни /start!",
        }

    try:
        from models.training_session import log_training_session
        from models.training_program import get_active_training_program

        # Get active program if exists
        program_id = None
        active = get_active_training_program(user['id'])
        if active:
            program_id = active['id']

        session_id = log_training_session(user['id'], program_id=program_id)

        # Calculate total sessions
        from models.training_session import get_training_sessions
        sessions = get_training_sessions(user['id'], limit=100)
        total = len(sessions)

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": f"✅ Тренування залоговано!\nВсього тренувань: {total} 💪",
        }
    except Exception as e:
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося залогировать. Спробуй пізніше.",
        }


def _handle_week(chat_id: int) -> dict:
    """Show this week's tracking summary."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.nutrition import get_weekly_summary
        from models.training_session import get_sessions_by_date_range
        from models.sleep_log import get_latest_weight
        from datetime import date, timedelta

        today = date.today()
        week_start = today - timedelta(days=6)  # last 7 days including today
        week_start_str = str(week_start)
        today_str = str(today)

        # Nutrition summary
        week_nutrition = get_weekly_summary(user['id'])
        total_cal = sum(d.get('total_calories', 0) for d in week_nutrition)
        total_protein = sum(d.get('total_protein', 0) for d in week_nutrition)
        total_carbs = sum(d.get('total_carbs', 0) for d in week_nutrition)
        total_fat = sum(d.get('total_fat', 0) for d in week_nutrition)
        days_with_logs = sum(1 for d in week_nutrition if d.get('total_calories', 0) > 0)

        # Training sessions this week
        sessions = get_sessions_by_date_range(user['id'], week_start_str, today_str)
        workout_count = len(sessions)

        # Calculate streak
        all_sessions = get_sessions_by_date_range(user['id'], '2020-01-01', today_str)
        streak = 0
        current_week_start = today - timedelta(days=today.weekday())
        while True:
            w_start = current_week_start - timedelta(weeks=streak)
            w_end = w_start + timedelta(days=6)
            week_sessions = [s for s in all_sessions
                           if w_start <= date.fromisoformat(s['date']) <= w_end]
            if week_sessions:
                streak += 1
                current_week_start = w_start - timedelta(days=1)
            else:
                break

        macros = _calculate_tdee(user)
        weekly_target = macros['target'] * 7

        lines = ["📊 *Тиждень*"]
        lines.append(f"🍽️ {round(total_cal)} / {weekly_target} ккал | Дні: {days_with_logs}/7")

        if total_cal > 0:
            avg_cal = int(total_cal / 7)
            diff = avg_cal - macros['target']
            if diff > 0:
                lines.append(f"📈 Середнє: {avg_cal} ккал/день (🔺+{diff})")
            elif diff < 0:
                lines.append(f"📈 Середнє: {avg_cal} ккал/день (🔻{diff})")
            else:
                lines.append(f"📈 Середнє: {avg_cal} ккал/день ✅")
            weekly_protein = macros['protein_g'] * 7
            weekly_carbs = macros['carbs_g'] * 7
            weekly_fat = macros['fat_g'] * 7
            lines.append(f"🥩 Б: {round(total_protein)}/{weekly_protein} г | В: {round(total_carbs)}/{weekly_carbs} г | Ж: {round(total_fat)}/{weekly_fat} г")

        lines.append(f"💪 Тренувань: {workout_count}")
        if streak > 0:
            lines.append(f"🔥 Streak: {streak} тижнів")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }
    except Exception as e:
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити тижневу статистику.",
        }



def _handle_tdee(chat_id: int) -> dict:
    """Show calculated TDEE and macro targets."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        macros = _calculate_tdee(user)
        weight = float(user.get('weight_kg', 70))
        goal = user.get('primary_goal', 'health')
        training_days = int(user.get('training_days_per_week', 3))

        goal_labels = {
            'muscle_gain': '📈 Набір маси (+300 ккал)',
            'fat_loss': '🔥 Жироспалення (-500 ккал)',
            'strength': '💪 Сила (TDEE)',
            'health': "❤️ Здоров'я (TDEE)",
            'recomposition': "♻️ Рекомпозиція (TDEE)",
        }

        lines = ["🎯 *Твої цілі*\n"]
        lines.append(f"Базовий обмін (BMR): {macros['tdee'] - 300} ккал")
        lines.append(f"Добова норма: {macros['target']} ккал")
        lines.append(f"Тренувань/тиждень: {training_days}")
        lines.append(f"Мета: {goal_labels.get(goal, 'TDEE')}")
        lines.append("")
        lines.append("🍽️ *Макроси:*")
        lines.append(f"Білок: {macros['protein_g']} г ({round(macros['protein_g'] / weight, 1)} г/кг)")
        lines.append(f"Вуглеводи: {macros['carbs_g']} г")
        lines.append(f"Жири: {macros['fat_g']} г")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }
    except Exception as e:
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося розрахувати.",
        }



def _handle_ai_message(chat_id: int, text: str) -> dict:
    """Handle AI-powered chat message via Telegram"""
    if not text or not text.strip():
        return {"ok": True}

    # Look up user by telegram_id
    user = None
    telegram_user_id = None
    try:
        from models.user import get_user_by_telegram_id
        user = get_user_by_telegram_id(chat_id)
        if user:
            telegram_user_id = user['id']
    except Exception:
        pass

    # Load base prompt
    base_prompt_path = os.path.join(os.path.dirname(__file__), 'agents', 'prompts', 'base_prompt.txt')
    try:
        with open(base_prompt_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read()
    except FileNotFoundError:
        base_prompt = "Ти — Body Coach AI, персональний фітнес-тренер."

    # Classify message to determine module
    try:
        from agents.router import classify_message
        module = classify_message(text)
    except Exception:
        module = 'general'

    # Build context from user profile
    system_prompt = base_prompt
    if user:
        try:
            from agents.context_builder import build_context, format_context_for_prompt
            context = build_context(telegram_user_id, module)
            context_text = format_context_for_prompt(context)
            if context_text:
                system_prompt = f"{base_prompt}\n\n{context_text}"
        except Exception:
            pass

    # Load conversation history from DB
    conversation_history = []
    conversation_id = None
    if user:
        try:
            from models.conversation import get_recent_conversations, create_conversation, append_message
            recent = get_recent_conversations(telegram_user_id, limit=1)
            if recent:
                conversation_id = recent[0]['id']
                conversation_history = recent[0]['messages']
        except Exception:
            pass

    # Call AI
    try:
        from agents.base import ai
        response_text = ai.chat(
            system_prompt=system_prompt,
            user_message=text,
            context={"conversation_history": conversation_history},
        )
    except Exception as e:
        response_text = (
            "Вибач, щось пішло не так. Спробуй ще раз або напиши пізніше. 💪"
        )

    # Save conversation to DB
    if user:
        try:
            from models.conversation import create_conversation, append_message
            if not conversation_id:
                conversation_id = create_conversation(user_id=telegram_user_id, module=module)
            append_message(conversation_id, "user", text)
            append_message(conversation_id, "assistant", response_text)
        except Exception:
            pass

    reply = {
        "method": "sendMessage",
        "chat_id": chat_id,
        "text": response_text,
    }
    return reply
