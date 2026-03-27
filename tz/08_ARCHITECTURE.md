# Технічна архітектура

## 1. Структура проекту

```
gym-coach/
│
├── app.py                          # Flask application, entry point
├── config.py                       # Configuration, API keys, constants
├── database.py                     # DB init, migrations, connection
├── bot.py                          # Telegram bot (webhook handler)
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (не в git)
├── .gitignore
│
├── models/                         # Data models (SQLite operations)
│   ├── __init__.py
│   ├── user.py                     # CRUD для users
│   ├── training.py                 # programs, days, exercises, logs
│   ├── checkin.py                  # daily_checkins
│   ├── pain.py                     # pain_journal
│   ├── measurements.py             # body_measurements
│   ├── conversation.py             # ai_conversations
│   ├── nutrition.py                # (Фаза 3) meal_plans, meal_log
│   └── sleep.py                    # (Фаза 4) sleep_logs
│
├── agents/                         # AI layer
│   ├── __init__.py
│   ├── base.py                     # Base system prompt, Claude API call
│   ├── router.py                   # Message classification / routing
│   ├── context_builder.py          # Builds user context per module
│   ├── prompts/
│   │   ├── base_prompt.txt         # Core persona prompt
│   │   ├── training_prompt.txt     # Training module prompt
│   │   ├── nutrition_prompt.txt    # (Фаза 3)
│   │   ├── recovery_prompt.txt     # (Фаза 4)
│   │   └── psychology_prompt.txt   # (Фаза 7)
│   ├── training_agent.py           # Training-specific AI logic
│   ├── nutrition_agent.py          # (Фаза 3)
│   └── recovery_agent.py           # (Фаза 4)
│
├── logic/                          # Business logic (non-AI)
│   ├── __init__.py
│   ├── progressive_overload.py     # Overload decision algorithm
│   ├── cycle_tracker.py            # Menstrual cycle calculations
│   ├── workout_adapter.py          # Adapts workout based on state
│   ├── analytics.py                # Volume, trends, stats calculations
│   ├── rest_timer.py               # Smart rest recommendations
│   └── formulas.py                 # TDEE, macros, BMR calculations
│
├── routes/                         # Flask API routes
│   ├── __init__.py
│   ├── auth.py                     # /api/v1/auth/*
│   ├── user.py                     # /api/v1/user/*
│   ├── training.py                 # /api/v1/training/*
│   ├── workout.py                  # /api/v1/workout/*
│   ├── checkin.py                  # /api/v1/checkin/*
│   ├── pain.py                     # /api/v1/pain/*
│   ├── measurements.py             # /api/v1/measurements/*
│   ├── exercises.py                # /api/v1/exercises/*
│   ├── chat.py                     # /api/v1/chat/*
│   └── analytics.py                # /api/v1/analytics/*
│
├── templates/
│   └── app.html                    # Telegram Mini App (single-file HTML/CSS/JS)
│
├── data/
│   ├── exercises_seed.json         # Початкова бібліотека вправ (50-80 вправ)
│   └── program_templates.json      # Шаблони програм для AI reference
│
└── tests/                          # (опціонально)
    ├── test_overload.py
    ├── test_cycle.py
    └── test_api.py
```

---

## 2. Потік даних

### Запит від юзера в Mini App:

```
[Telegram Mini App (HTML/JS)]
        │
        ▼
[Flask API endpoint]
        │
        ├─── Потрібен AI? ──→ НІ ──→ [Logic layer] ──→ [Response]
        │                                   │
        │                                   ▼
        │                              [Database]
        │
        └─── ТАК ──→ [Router: визначити тему]
                          │
                          ▼
                    [Context Builder: зібрати дані з БД]
                          │
                          ▼
                    [Prompt Assembly: base + module + context]
                          │
                          ▼
                    [Claude API call]
                          │
                          ▼
                    [Parse response]
                          │
                          ├── Structured (JSON) ──→ [Save to DB] ──→ [Response]
                          │
                          └── Text ──→ [Save conversation] ──→ [Response]
```

### Запит від юзера через Telegram бота:

```
[Telegram Bot message]
        │
        ▼
[bot.py webhook handler]
        │
        ├── Command (/start, /checkin, /today) ──→ [Handle command]
        │
        └── Text message ──→ [AI Chat pipeline] ──→ [Reply to bot message]
```

---

## 3. Конфігурація

### config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'gym_coach.db')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')
    
    # AI
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
    
    # Groq (для dev/тестів)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    USE_GROQ = os.getenv('USE_GROQ', 'false').lower() == 'true'
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    # App
    MAX_CONTEXT_TOKENS = 4000
    DEFAULT_LANGUAGE = 'uk'
```

### .env

```
SECRET_KEY=your-secret-key
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklmnOPQrstUVwxyz
TELEGRAM_WEBHOOK_URL=https://your-app.railway.app/webhook/telegram

ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
USE_GROQ=true

DATABASE_PATH=gym_coach.db
DEBUG=true
```

---

## 4. Dependencies

### requirements.txt

```
flask==3.1.0
python-telegram-bot==21.8
anthropic==0.43.0
groq==0.15.0
python-dotenv==1.0.1
gunicorn==23.0.0
```

---

## 5. Deployment

### Railway (рекомендовано)

```
# Procfile
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### Або Render

```
# render.yaml
services:
  - type: web
    name: gym-coach
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
```

### Telegram Webhook setup

```python
# В app.py або окремим скриптом
import requests

def set_webhook():
    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/setWebhook"
    data = {"url": f"{Config.TELEGRAM_WEBHOOK_URL}"}
    requests.post(url, json=data)
```

---

## 6. Безпека

### Telegram WebApp Auth

```python
import hashlib
import hmac
from urllib.parse import parse_qs

def validate_telegram_init_data(init_data: str, bot_token: str) -> bool:
    """Валідація initData від Telegram Mini App"""
    parsed = dict(parse_qs(init_data))
    
    # Витягти hash
    received_hash = parsed.pop('hash', [None])[0]
    if not received_hash:
        return False
    
    # Створити data check string
    data_check_string = '\n'.join(
        f"{k}={v[0]}" for k, v in sorted(parsed.items())
    )
    
    # Створити secret key
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    
    # Перевірити hash
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == received_hash
```

### API middleware

```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        init_data = request.headers.get('X-Telegram-Init-Data')
        if not init_data or not validate_telegram_init_data(init_data, Config.TELEGRAM_BOT_TOKEN):
            return jsonify({"error": "Unauthorized"}), 401
        
        # Витягти user info
        user_data = extract_user_from_init_data(init_data)
        request.telegram_user = user_data
        
        return f(*args, **kwargs)
    return decorated
```

---

## 7. AI Provider Abstraction

```python
# agents/base.py

class AIProvider:
    """Абстракція над Claude / Groq для легкого перемикання"""
    
    def __init__(self):
        if Config.USE_GROQ:
            from groq import Groq
            self.client = Groq(api_key=Config.GROQ_API_KEY)
            self.model = Config.GROQ_MODEL
            self.provider = 'groq'
        else:
            import anthropic
            self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model = Config.CLAUDE_MODEL
            self.provider = 'anthropic'
    
    def chat(self, system_prompt: str, user_message: str, context: dict = None) -> str:
        messages = []
        if context and context.get('conversation_history'):
            messages.extend(context['conversation_history'])
        messages.append({"role": "user", "content": user_message})
        
        if self.provider == 'groq':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        else:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages,
            )
            return response.content[0].text

ai = AIProvider()
```

---

## 8. Масштабування (на майбутнє)

### SQLite → PostgreSQL
Коли потрібно:
- Більше 1 юзера одночасно (SQLite не любить concurrent writes)
- Деплой на Railway/Render з persistent storage

Як:
- Замінити sqlite3 на psycopg2
- Мінімальні зміни в SQL (SQLite і PostgreSQL дуже схожі)
- Або використати SQLAlchemy як ORM з самого початку (але це ускладнює старт)

### Кешування
- Бібліотека вправ — кешувати в пам'яті (рідко змінюється)
- AI відповіді на типові питання — кешувати по хешу запиту
- User profile — кешувати на час сесії

### Rate Limiting
- Claude API: ~50 запитів на хвилину (Tier 1)
- Groq free: ~30 запитів на хвилину
- Telegram Bot API: 30 повідомлень на секунду
