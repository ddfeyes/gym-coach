#!/usr/bin/env python3
"""
Daily reminder script for gym-coach.
Run via cron or directly.
Sends Telegram reminders to users who completed onboarding.
"""
import os
import sqlite3
import sys
from datetime import date

DB_PATH = os.environ.get('DB_PATH', '/srv/gym-coach/data/gym_coach.db')
TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN', '')


def get_onboarded_users():
    """Get all users who completed onboarding."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT id, telegram_id, name FROM users WHERE onboarding_completed = 1 AND telegram_id IS NOT NULL"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def send_telegram_message(chat_id: int, text: str):
    """Send a message via Telegram Bot API."""
    import urllib.request
    import json

    if not TG_BOT_TOKEN:
        print(f"[reminder] No bot token, skipping")
        return

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()

    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        print(f"[reminder] Failed to send to {chat_id}: {e}")
        return False


def main():
    users = get_onboarded_users()
    today = date.today().strftime("%d.%m.%Y")

    messages = [
        f"🌅 Доброго ранку! {today}\n\nТи вже залогив(-ла) сніданок? Натисни /start щоб відкрити додаток 💪",
        f"🏋️ Час тренування!\n\nПеревір свою програму у додатку — натисни /start → Тренування 🏋️",
        f"🥗 Вечірній чекін!\n\nЯк пройшов день? Залогуй останній прийом їжі та сон у додатку 💪",
    ]

    sent = 0
    for user in users:
        msg = messages[sent % len(messages)]
        msg = f"Привіт, {user['name']}! 👋\n\n" + msg
        ok = send_telegram_message(user['telegram_id'], msg)
        if ok:
            sent += 1
        print(f"[reminder] {'OK' if ok else 'FAIL'} → {user['name']} ({user['telegram_id']})")

    print(f"[reminder] Done. Sent {sent}/{len(users)} reminders.")


if __name__ == "__main__":
    main()
