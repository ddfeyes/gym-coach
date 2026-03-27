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

    # Call AI
    try:
        from agents.base import ai
        response_text = ai.chat(
            system_prompt=system_prompt,
            user_message=text,
            context={},
        )
    except Exception as e:
        response_text = (
            "Вибач, щось пішло не так. Спробуй ще раз або напиши пізніше. 💪"
        )

    reply = {
        "method": "sendMessage",
        "chat_id": chat_id,
        "text": response_text,
    }
    return reply
