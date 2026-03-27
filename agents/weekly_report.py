#!/usr/bin/env python3
"""
Weekly progress report for gym-coach.
Run via cron on Sunday evening.
Sends Telegram reports to users who completed onboarding.
"""
import os
import sqlite3
import json
from datetime import date, timedelta

DB_PATH = os.environ.get('DB_PATH', '/srv/gym-coach/data/gym_coach.db')
TG_BOT_TOKEN = os.environ.get('TG_BOT_TOKEN', '')


def get_onboarded_users():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT id, telegram_id, name FROM users WHERE onboarding_completed = 1 AND telegram_id IS NOT NULL"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_user_stats(user_id: int) -> dict:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    today = date.today()
    week_ago = (today - timedelta(days=7)).isoformat()
    two_weeks_ago = (today - timedelta(days=14)).isoformat()
    today_str = today.isoformat()

    # Weight change
    weight_now = db.execute(
        "SELECT weight_kg FROM weight_logs WHERE user_id = ? ORDER BY date DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    weight_prev = db.execute(
        "SELECT weight_kg FROM weight_logs WHERE user_id = ? AND date <= ? ORDER BY date DESC LIMIT 1",
        (user_id, week_ago)
    ).fetchone()

    weight_change = None
    if weight_now and weight_prev:
        wc = round(weight_now['weight_kg'] - weight_prev['weight_kg'], 1)
        weight_change = wc

    # Nutrition this week
    nutrition_rows = db.execute("""
        SELECT SUM(calories) as total_cal, SUM(protein) as total_prot,
               COUNT(*) as meals
        FROM nutrition_logs
        WHERE user_id = ? AND date >= ?
    """, (user_id, week_ago)).fetchone()

    # Training days this week (days with any log entry)
    training_rows = db.execute("""
        SELECT COUNT(DISTINCT date) as days
        FROM training_program
        WHERE user_id = ? AND created_at >= ?
    """, (user_id, week_ago)).fetchone()

    # Sleep average this week
    sleep_rows = db.execute("""
        SELECT AVG(hours) as avg_hours, AVG(quality) as avg_quality
        FROM sleep_logs
        WHERE user_id = ? AND date >= ?
    """, (user_id, week_ago)).fetchone()

    db.close()
    return {
        'weight_now': weight_now['weight_kg'] if weight_now else None,
        'weight_change': weight_change,
        'avg_calories': round(nutrition_rows['total_cal'] / 7) if nutrition_rows['total_cal'] else 0,
        'avg_protein': round(nutrition_rows['total_prot'] / 7) if nutrition_rows['total_prot'] else 0,
        'meals_logged': nutrition_rows['meals'] if nutrition_rows['meals'] else 0,
        'sleep_avg': round(sleep_rows['avg_hours'], 1) if sleep_rows['avg_hours'] else 0,
        'sleep_quality': round(sleep_rows['avg_quality'], 1) if sleep_rows['avg_quality'] else 0,
    }


def format_report(user_name: str, stats: dict) -> str:
    lines = [
        f"📊 *Тижневий звіт для {user_name}*",
        f"",
    ]

    if stats.get('weight_now'):
        wc = stats['weight_change']
        wc_str = f"{wc:+.1f} кг" if wc is not None else "н/д"
        lines.append(f"⚖️ *Вага:* {stats['weight_now']} кг ({wc_str})")

    if stats.get('avg_calories', 0) > 0:
        lines.append(f"🍽️ *Харчування:* ~{stats['avg_calories']} ккал/день ({stats['meals_logged']} прийомів logged)")
        lines.append(f"🥩 *Білок:* ~{stats['avg_protein']} г/день")

    if stats.get('sleep_avg', 0) > 0:
        sq = '⭐' * int(stats['sleep_quality']) + '☆' * (5 - int(stats['sleep_quality']))
        lines.append(f"😴 *Сон:* {stats['sleep_avg']} год/день {sq}")

    lines.extend([
        f"",
        f"💪 Продовжуй роботу! Натисни /start щоб відкрити додаток.",
    ])

    return "\n".join(lines)


def send_telegram_message(chat_id: int, text: str):
    import urllib.request
    import json

    if not TG_BOT_TOKEN:
        return False

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
        print(f"[weekly] Failed to send to {chat_id}: {e}")
        return False


def main():
    users = get_onboarded_users()
    sent = 0
    for user in users:
        stats = get_user_stats(user['id'])
        report = format_report(user['name'], stats)
        ok = send_telegram_message(user['telegram_id'], report)
        status = 'OK' if ok else 'FAIL'
        print(f"[weekly] {status} → {user['name']} ({user['telegram_id']})")
        if ok:
            sent += 1

    print(f"[weekly] Done. Sent {sent}/{len(users)} reports.")


if __name__ == "__main__":
    main()
