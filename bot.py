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
        "/help — Показати це меню\n\n"
        "💬 Ти також можеш просто написати мені — я відповім на будь-які питання про тренування, харчування, відновлення і здоров'я.\n\n"
        "🏋️ У Mini App ти знайдеш:\n"
        "• Персональну тренувальну програму\n"
        "• Трекінг харчування з AI-підрахунком калорій\n"
        "• Чат з персональним коучем"
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
