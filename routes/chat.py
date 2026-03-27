import os
from flask import Blueprint, request, jsonify
from agents.router import classify_message
from agents.context_builder import build_context, format_context_for_prompt
from models.conversation import (
    create_conversation, get_conversation, append_message, update_conversation_meta,
)

chat_bp = Blueprint('chat', __name__)

BASE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'agents', 'prompts', 'base_prompt.txt')


def _load_base_prompt():
    with open(BASE_PROMPT_PATH, 'r', encoding='utf-8') as f:
        return f.read()


@chat_bp.route('/api/v1/chat/message', methods=['POST'])
def chat_message():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400

    user_message = data['message']
    user_id = data.get('user_id')
    conversation_id = data.get('conversation_id')

    # If user_id not provided, try to resolve from Telegram auth
    if user_id is None:
        init_data = request.headers.get('X-Telegram-Init-Data')
        if init_data:
            from routes.auth import validate_telegram_init_data, extract_user_from_init_data
            if validate_telegram_init_data(init_data, Config.TELEGRAM_BOT_TOKEN):
                tg_user = extract_user_from_init_data(init_data)
                if tg_user:
                    from models.user import get_user_by_telegram_id
                    db_user = get_user_by_telegram_id(tg_user.get('id'))
                    if db_user:
                        user_id = db_user['id']

    module = classify_message(user_message)

    base_prompt = _load_base_prompt()

    system_prompt = base_prompt
    context = {}
    if user_id:
        context = build_context(user_id, module)
        context_text = format_context_for_prompt(context)
        if context_text:
            system_prompt = f"{base_prompt}\n\n{context_text}"

    conversation_history = []
    if conversation_id:
        conv = get_conversation(conversation_id)
        if conv:
            conversation_history = conv['messages']

    try:
        from agents.base import ai
        response_text = ai.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            context={"conversation_history": conversation_history},
        )
    except Exception as e:
        return jsonify({"error": f"AI service error: {str(e)}"}), 500

    if not conversation_id:
        # user_id=None is fine — create_conversation handles anonymous sessions
        conversation_id = create_conversation(user_id=user_id or None, module=module)

    append_message(conversation_id, "user", user_message)
    append_message(conversation_id, "assistant", response_text)

    return jsonify({
        "response": response_text,
        "conversation_id": conversation_id,
        "module_used": module,
    })


@chat_bp.route('/api/v1/chat/conversations', methods=['GET'])
def list_conversations():
    """List recent conversations for the authenticated user."""
    init_data = request.headers.get('X-Telegram-Init-Data')
    user_id = None

    if init_data:
        from routes.auth import validate_telegram_init_data, extract_user_from_init_data
        if validate_telegram_init_data(init_data, Config.TELEGRAM_BOT_TOKEN):
            tg_user = extract_user_from_init_data(init_data)
            if tg_user:
                from models.user import get_user_by_telegram_id
                db_user = get_user_by_telegram_id(tg_user.get('id'))
                if db_user:
                    user_id = db_user['id']

    from models.conversation import get_recent_conversations
    conversations = get_recent_conversations(user_id, limit=5)

    # Return only id, module, updated_at and a preview of the last message
    result = []
    for c in conversations:
        messages = c.get('messages', [])
        last_msg = messages[-1] if messages else None
        result.append({
            'id': c['id'],
            'module': c['module'],
            'updated_at': c['updated_at'],
            'last_message': last_msg['content'][:100] if last_msg else None,
            'messages': messages,
        })

    return jsonify({"conversations": result, "current_user_id": user_id})
