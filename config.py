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
