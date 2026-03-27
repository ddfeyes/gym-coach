import hashlib
import hmac
import json
from functools import wraps
from urllib.parse import parse_qs

from flask import Blueprint, request, jsonify
from config import Config

auth_bp = Blueprint('auth', __name__)


def validate_telegram_init_data(init_data: str, bot_token: str) -> bool:
    """Валідація initData від Telegram Mini App"""
    parsed = dict(parse_qs(init_data))

    received_hash = parsed.pop('hash', [None])[0]
    if not received_hash:
        return False

    data_check_string = '\n'.join(
        f"{k}={v[0]}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    return calculated_hash == received_hash


def extract_user_from_init_data(init_data: str) -> dict:
    """Витягти дані юзера з initData"""
    parsed = dict(parse_qs(init_data))
    user_json = parsed.get('user', [None])[0]
    if user_json:
        return json.loads(user_json)
    return {}


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        init_data = request.headers.get('X-Telegram-Init-Data')
        if not init_data or not validate_telegram_init_data(init_data, Config.TELEGRAM_BOT_TOKEN):
            return jsonify({"error": "Unauthorized"}), 401

        user_data = extract_user_from_init_data(init_data)
        request.telegram_user = user_data

        return f(*args, **kwargs)
    return decorated
