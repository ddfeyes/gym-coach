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
        from models.sleep_log import get_latest_weight
        from models.training_session import get_sessions_by_date_range

        today = str(__import__('datetime').date.today())
        nutrition = get_daily_summary(user['id'], today)
        latest_weight = get_latest_weight(user['id'])
        today_sessions = get_sessions_by_date_range(user['id'], today, today)

        lines = ["📊 *Сьогодні:*"]

        if nutrition.get('total_calories', 0) > 0:
            lines.append(f"🍽️ Калорії: {round(nutrition['total_calories'])} ккал")
            lines.append(f"🥩 Білок: {round(nutrition['total_protein'])} г | Вугл: {round(nutrition['total_carbs'])} г | Жири: {round(nutrition['total_fat'])} г")
            lines.append(f"Прийомів: {len(nutrition.get('meals', []))}")
        else:
            lines.append("🍽️ Їжа: ще не логив(-ла)")

        if latest_weight:
            lines.append(f"⚖️ Вага: {latest_weight['weight_kg']} кг")

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
