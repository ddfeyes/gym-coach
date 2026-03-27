import json
from database import get_db


def create_conversation(user_id=None, module='general'):
    """Create a new conversation. user_id may be None for anonymous sessions."""
    db = get_db()
    cursor = db.cursor()
    # Validate user_id exists to avoid FK violation
    if user_id is not None:
        exists = db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
        if not exists:
            user_id = None
    cursor.execute(
        "INSERT INTO ai_conversations (user_id, module) VALUES (?, ?)",
        (user_id, module),
    )
    db.commit()
    conv_id = cursor.lastrowid
    db.close()
    return conv_id


def get_conversation(conversation_id):
    db = get_db()
    conv = db.execute(
        "SELECT * FROM ai_conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    db.close()
    if not conv:
        return None
    conv = dict(conv)
    conv['messages'] = json.loads(conv['messages'])
    return conv


def append_message(conversation_id, role, content):
    db = get_db()
    conv = db.execute(
        "SELECT messages FROM ai_conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    if not conv:
        db.close()
        return
    messages = json.loads(conv['messages'])
    messages.append({"role": role, "content": content})
    db.execute(
        "UPDATE ai_conversations SET messages = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(messages, ensure_ascii=False), conversation_id),
    )
    db.commit()
    db.close()


def update_conversation_meta(conversation_id, tokens_used=None, model_used=None):
    db = get_db()
    updates = []
    values = []
    if tokens_used is not None:
        updates.append("tokens_used = ?")
        values.append(tokens_used)
    if model_used is not None:
        updates.append("model_used = ?")
        values.append(model_used)
    if updates:
        values.append(conversation_id)
        db.execute(
            f"UPDATE ai_conversations SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        db.commit()
    db.close()


def get_recent_conversations(user_id, limit=10):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM ai_conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    db.close()
    results = []
    for row in rows:
        conv = dict(row)
        conv['messages'] = json.loads(conv['messages'])
        results.append(conv)
    return results
