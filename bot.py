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
    if text.startswith('/stats'):
        return _handle_stats(chat_id)
    if text.startswith('/today') or text.startswith('/stats'):
        return _handle_today(chat_id)
    if text.startswith('/program'):
        return _handle_program(chat_id)
    if text.startswith('/log '):
        return _handle_log(chat_id, text[5:].strip())
    if text.startswith('/workout'):
        return _handle_workout(chat_id)
    if text.startswith('/water'):
        return _handle_water(chat_id, text)
    if text.startswith('/week'):
        return _handle_week(chat_id)
    if text.startswith('/month'):
        return _handle_month(chat_id)
    if text.startswith('/tdee'):
        return _handle_tdee(chat_id)

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
        "/week — Тижнева статистика\n"
        "/month — Місяцна статистика (30 днів)\n"
        "/stats — Загальна статистика (тренування, вага, заміри)\n"
        "/tdee — Добова норма калорій та макроси\n"
        "/program — Твоя тренувальна програма\n"
        "/log <опис> — Швидко залогировать прийом їжі\n"
        "/workout — Залогировать тренування\n"
        "/water [мл] — Додати води або переглянути\n\n"
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


def _calculate_tdee(user: dict) -> dict:
    """Calculate TDEE and macro targets from user data."""
    weight = float(user.get('weight_kg', 70))
    height = float(user.get('height_cm', 170))
    age = int(user.get('age', 25))
    gender = user.get('gender', 'male')
    goal = user.get('primary_goal', 'health')
    training_days = int(user.get('training_days_per_week', 3))

    # Mifflin-St Jeor BMR
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Activity multiplier
    if training_days <= 1:
        activity = 1.2
    elif training_days <= 3:
        activity = 1.375
    elif training_days <= 5:
        activity = 1.55
    else:
        activity = 1.725

    tdee = bmr * activity

    # Goal adjustment
    if goal == 'muscle_gain':
        target = tdee + 300
    elif goal == 'fat_loss':
        target = tdee - 500
    elif goal in ('strength', 'health', 'recomposition'):
        target = tdee
    else:
        target = tdee

    # Macro targets
    protein_g = weight * 2.0  # 2g per kg
    fat_g = weight * 1.0       # 1g per kg
    protein_cal = protein_g * 4
    fat_cal = fat_g * 9
    carbs_cal = max(0, target - protein_cal - fat_cal)
    carbs_g = carbs_cal / 4

    return {
        'tdee': round(tdee),
        'target': round(target),
        'protein_g': round(protein_g),
        'carbs_g': round(carbs_g),
        'fat_g': round(fat_g),
    }


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
        from models.sleep_log import get_latest_weight, get_sleep_history
        from models.training_session import get_sessions_by_date_range
        from models.water_log import get_daily_water

        today = str(__import__('datetime').date.today())
        nutrition = get_daily_summary(user['id'], today)
        latest_weight = get_latest_weight(user['id'])
        today_sessions = get_sessions_by_date_range(user['id'], today, today)
        macros = _calculate_tdee(user)
        today_water = get_daily_water(user['id'], today)
        sleep_history = get_sleep_history(user['id'], 1)
        today_sleep = sleep_history[0] if sleep_history else None

        lines = ["📊 *Сьогодні:*"]

        if nutrition.get('total_calories', 0) > 0:
            cal = round(nutrition['total_calories'])
            remaining = macros['target'] - cal
            lines.append(f"🍽️ {cal} / {macros['target']} ккал")
            if remaining > 0:
                lines.append(f"   🔥 Залишилось: {remaining} ккал")
            else:
                lines.append(f"   ⚠️ Перевищено: {abs(remaining)} ккал")
            lines.append(f"🥩 Б: {round(nutrition['total_protein'])}/{macros['protein_g']} г | В: {round(nutrition['total_carbs'])}/{macros['carbs_g']} г | Ж: {round(nutrition['total_fat'])}/{macros['fat_g']} г")
            lines.append(f"Прийомів: {len(nutrition.get('meals', []))}")
        else:
            lines.append(f"🍽️ Немає даних | Денна норма: {macros['target']} ккал")
            lines.append(f"🥩 Б: 0/{macros['protein_g']} г | В: 0/{macros['carbs_g']} г | Ж: 0/{macros['fat_g']} г")

        if latest_weight:
            lines.append(f"⚖️ Вага: {latest_weight['weight_kg']} кг")

        # Water (target 2500ml)
        water_ml = today_water.get('amount_ml', 0)
        water_target = 2500
        if water_ml > 0:
            lines.append(f"💧 {water_ml} / {water_target} мл")
        else:
            lines.append(f"💧 0 / {water_target} мл")

        # Sleep
        if today_sleep:
            hours = today_sleep.get('hours', 0)
            quality = today_sleep.get('quality', 0)
            q_stars = "⭐" * quality if quality else "-"
            lines.append(f"😴 Сон: {hours} год {q_stars}")

        # Today's planned workout (based on program schedule)
        try:
            from models.training_program import get_active_training_program
            active_program = get_active_training_program(user['id'])
            if active_program:
                from datetime import date
                today_date = date.today()
                training_days = int(user.get('training_days_per_week', 3))
                # Determine which program day today is (Mon=0, Sun=6)
                # Simple: weekday modulo training_days gives program day index
                program_day_index = (today_date.weekday() % training_days)
                schedule = active_program.get('schedule', [])
                exercises = active_program.get('exercises', [])
                if schedule and program_day_index < len(schedule):
                    day_label = schedule[program_day_index]
                    day_exercises = [e for e in exercises if e.get('day', 0) == program_day_index + 1]
                    lines.append(f"📅 *{day_label}*")
                    if day_exercises:
                        for ex in day_exercises[:5]:
                            lines.append(f"  • {ex['exercise']} — {ex['sets']}×{ex['reps']}")
                        if len(day_exercises) > 5:
                            lines.append(f"  ...та ще {len(day_exercises) - 5}")
                    else:
                        lines.append("  (вiдпочинок)")
                elif not today_sessions:
                    lines.append("📅 Відпочинок сьогодні")
        except Exception:
            pass

        if today_sessions:
            session = today_sessions[0]
            program_name = session.get('program_name', 'Тренування')
            duration = session.get('duration_minutes', 0)
            lines.append(f"💪 Залоговано: {program_name} ({duration} хв)")
        else:
            lines.append("💪 Немає / /workout щоб залогити")

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

        # Group exercises by day
        schedule = program.get('schedule', [])
        exercises = program.get('exercises', [])
        by_day = {}
        for ex in exercises:
            d = ex.get('day', 1)
            if d not in by_day:
                by_day[d] = []
            by_day[d].append(ex)

        # Show each schedule day with its exercises
        for i, day_label in enumerate(schedule):
            day_num = i + 1
            day_exercises = by_day.get(day_num, [])
            lines.append(f"\n📅 *{day_label}*")
            if day_exercises:
                for ex in day_exercises[:6]:
                    mg = ex.get('muscle_group', '')
                    mg_str = f" ({mg})" if mg else ""
                    lines.append(f"  • {ex['exercise']} — {ex['sets']}×{ex['reps']}{mg_str}")
                if len(day_exercises) > 6:
                    lines.append(f"  ...ще {len(day_exercises) - 6} вправ")
            else:
                lines.append("  Відпочинок")

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
        from utils.food_estimator import estimate_food

        # Estimate calories and macros from description
        estimate = estimate_food(description)
        log_id = log_meal(user['id'], description, 'quick_log',
                          estimate['kcal'], estimate['protein'],
                          estimate['carbs'], estimate['fat'])

        if estimate['matched']:
            lines = [
                f"✅ Додано: {description}",
                f"🍽 ~{estimate['kcal']} ккал",
                f"🥩 Б: {estimate['protein']}г | В: {estimate['carbs']}г | Ж: {estimate['fat']}г",
                "",
                "Відкрий додаток щоб скоригувати 🕸"
            ]
        else:
            lines = [
                f"✅ Додано: {description}",
                f"🍽 ~{estimate['kcal']} ккал (оріентово)",
                "Скоригуй в додатку 🕸"
            ]

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
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


def _handle_water(chat_id: int, text: str) -> dict:
    """Handle /water command — show today's water or log water intake.
    /water — show today's water + 7-day history
    /water 250 or /water +250 — add 250ml to today's total
    """
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.water_log import log_water, get_daily_water, get_water_history
        from datetime import date

        today = str(date.today())
        target = 2500  # ml

        # Parse amount from command
        # /water 250 or /water +250
        parts = text.split()
        amount = None
        if len(parts) > 1:
            val = parts[1].strip()
            if val.startswith('+'):
                val = val[1:]
            if val.isdigit():
                amount = int(val)

        # Log water if amount provided
        if amount and amount > 0:
            if amount > 5000:
                return {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "⚠️ Занадто багато! Максимум 5000мл за раз.",
                }
            log_water(user['id'], amount)
            new_total = get_daily_water(user['id'], today).get('amount_ml', 0)
            pct = min(round(new_total / target * 100), 100)
            bars = "█" * (pct // 10) + "░" * (10 - pct // 10)
            msg = "💧 Додано +" + str(amount) + "мл\n\n💧 " + str(new_total) + " / " + str(target) + " мл [" + bars + "] " + str(pct) + "%"
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": msg,
            }

        # Show today's water + 7-day history
        today_water = get_daily_water(user['id'], today)
        today_ml = today_water.get('amount_ml', 0)
        history = get_water_history(user['id'], 7)

        lines = ["💧 *Вода*\n"]
        pct = min(round(today_ml / target * 100), 100)
        bars = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append("Сьогодні: " + str(today_ml) + " / " + str(target) + " мл")
        lines.append("[" + bars + "] " + str(pct) + "%")

        if history:
            lines.append("\n📋 Останні дні:")
            for entry in history[:7]:
                d = date.fromisoformat(entry['date'])
                day_name = d.strftime("%d.%m")
                ml = entry['amount_ml']
                if ml >= target:
                    icon = "✅"
                elif ml >= target * 0.5:
                    icon = "🔶"
                else:
                    icon = "⚪"
                lines.append("  " + icon + " " + day_name + ": " + str(ml) + "мл")

        lines.append("\n💡 /water 250 — додати води")
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
            "text": "❌ Не вдалося завантажити дані про воду.",
        }



def _handle_week(chat_id: int) -> dict:
    """Show this week's tracking summary."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.nutrition import get_weekly_summary
        from models.training_session import get_sessions_by_date_range
        from models.sleep_log import get_latest_weight
        from datetime import date, timedelta

        today = date.today()
        week_start = today - timedelta(days=6)  # last 7 days including today
        week_start_str = str(week_start)
        today_str = str(today)

        # Nutrition summary
        week_nutrition = get_weekly_summary(user['id'])
        total_cal = sum(d.get('total_calories', 0) for d in week_nutrition)
        total_protein = sum(d.get('total_protein', 0) for d in week_nutrition)
        total_carbs = sum(d.get('total_carbs', 0) for d in week_nutrition)
        total_fat = sum(d.get('total_fat', 0) for d in week_nutrition)
        days_with_logs = sum(1 for d in week_nutrition if d.get('total_calories', 0) > 0)

        # Training sessions this week
        sessions = get_sessions_by_date_range(user['id'], week_start_str, today_str)
        workout_count = len(sessions)

        # Calculate streak
        all_sessions = get_sessions_by_date_range(user['id'], '2020-01-01', today_str)
        streak = 0
        current_week_start = today - timedelta(days=today.weekday())
        while True:
            w_start = current_week_start - timedelta(weeks=streak)
            w_end = w_start + timedelta(days=6)
            week_sessions = [s for s in all_sessions
                           if w_start <= date.fromisoformat(s['date']) <= w_end]
            if week_sessions:
                streak += 1
                current_week_start = w_start - timedelta(days=1)
            else:
                break

        macros = _calculate_tdee(user)
        weekly_target = macros['target'] * 7

        lines = ["📊 *Тиждень*"]
        lines.append(f"🍽️ {round(total_cal)} / {weekly_target} ккал | Дні: {days_with_logs}/7")

        if total_cal > 0:
            avg_cal = int(total_cal / 7)
            diff = avg_cal - macros['target']
            if diff > 0:
                lines.append(f"📈 Середнє: {avg_cal} ккал/день (🔺+{diff})")
            elif diff < 0:
                lines.append(f"📈 Середнє: {avg_cal} ккал/день (🔻{diff})")
            else:
                lines.append(f"📈 Середнє: {avg_cal} ккал/день ✅")
            weekly_protein = macros['protein_g'] * 7
            weekly_carbs = macros['carbs_g'] * 7
            weekly_fat = macros['fat_g'] * 7
            lines.append(f"🥩 Б: {round(total_protein)}/{weekly_protein} г | В: {round(total_carbs)}/{weekly_carbs} г | Ж: {round(total_fat)}/{weekly_fat} г")

        lines.append(f"💪 Тренувань: {workout_count}")
        if streak > 0:
            lines.append(f"🔥 Streak: {streak} тижнів")

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
            "text": "❌ Не вдалося завантажити тижневу статистику.",
        }


def _handle_stats(chat_id: int) -> dict:
    """Show user's overall training and progress stats."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.training_session import get_sessions_by_date_range, get_training_sessions
        from models.weight_log import get_weight_history, get_latest_weight
        from models.measurement import get_latest_measurement
        from datetime import date, timedelta

        today = date.today()
        today_str = str(today)

        lines = ["📊 *Прогресс / Статистика*\n"]

        # === Workouts ===
        all_sessions = get_training_sessions(user['id'], limit=1000)
        total_workouts = len(all_sessions)

        # Current streak
        streak = 0
        if all_sessions:
            current_week_start = today - timedelta(days=today.weekday())
            while True:
                w_start = current_week_start - timedelta(weeks=streak)
                w_end = w_start + timedelta(days=6)
                week_sessions = [s for s in all_sessions
                               if w_start <= date.fromisoformat(s['date']) <= w_end]
                if week_sessions:
                    streak += 1
                    current_week_start = w_start - timedelta(days=1)
                else:
                    break

        # Workouts per week (average)
        if all_sessions and total_workouts > 0:
            first_session_date = date.fromisoformat(all_sessions[-1]['date'])
            weeks_active = max(1, (today - first_session_date).days / 7)
            workouts_per_week = round(total_workouts / weeks_active, 1)
        else:
            workouts_per_week = 0

        lines.append(f"🏋️ Тренувань всього: {total_workouts}")
        lines.append(f"📈 За тиждень: {workouts_per_week}/тиждень")
        if streak > 0:
            lines.append(f"🔥 Streak: {streak} тижнів")

        # === Weight ===
        weight_history = get_weight_history(user['id'], limit=100)
        if len(weight_history) >= 2:
            latest_w = weight_history[0]['weight_kg']
            first_w = weight_history[-1]['weight_kg']
            diff = round(latest_w - first_w, 1)
            if diff > 0:
                diff_str = f"(+{diff} кг)"
            elif diff < 0:
                diff_str = f"(−{diff} кг)"
            else:
                diff_str = "(= 0)"
            lines.append(f"\n⚖️ Вага: {latest_w} кг {diff_str}")
        elif weight_history:
            lines.append(f"\n⚖️ Вага: {weight_history[0]['weight_kg']} кг")

        # === Measurements ===
        meas = get_latest_measurement(user['id'])
        if meas:
            lines.append(f"\n📏 Заміри (останній запис):")
            field_map = {
                'biceps_l': 'Біцепс лівий',
                'biceps_r': 'Біцепс правий',
                'chest': 'Груди',
                'waist': 'Талія',
                'hips': 'Стегна',
                'thigh_l': 'Стегно ліве',
                'thigh_r': 'Стегно праве',
            }
            for field, label in field_map.items():
                val = meas.get(field)
                if val:
                    lines.append(f"  {label}: {val} см")

        lines.append("\n")
        lines.append("📋 Відкрий додаток щоб побачити графіки!")

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
            "text": "❌ Не вдалося завантажити статистику.",
        }

def _handle_month(chat_id: int) -> dict:
    """Show monthly tracking summary — last 30 days."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.nutrition import get_daily_summary
        from models.training_session import get_sessions_by_date_range
        from models.weight_log import get_weight_history
        from datetime import date, timedelta

        today = date.today()
        month_start = today - timedelta(days=29)
        month_start_str = str(month_start)
        today_str = str(today)

        lines = ["📅 *Місяць* (останні 30 днів)\n"]

        # Nutrition — sum across all 30 days
        total_cal = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        days_with_logs = 0
        days_data = []
        for i in range(30):
            d = today - timedelta(days=i)
            d_str = str(d)
            day_summary = get_daily_summary(user['id'], d_str)
            day_cal = day_summary.get('total_calories', 0)
            if day_cal > 0:
                days_with_logs += 1
                total_cal += day_cal
                total_protein += day_summary.get('total_protein', 0)
                total_carbs += day_summary.get('total_carbs', 0)
                total_fat += day_summary.get('total_fat', 0)
                days_data.append((d_str, day_cal))

        # Training sessions this month
        sessions = get_sessions_by_date_range(user['id'], month_start_str, today_str)
        workout_count = len(sessions)

        # Weight change
        weight_history = get_weight_history(user['id'], limit=30)
        weight_change_str = ""
        if len(weight_history) >= 2:
            latest_w = weight_history[0]['weight_kg']
            first_w = weight_history[-1]['weight_kg']
            diff = round(latest_w - first_w, 1)
            if diff > 0:
                diff_str = f"(+{diff} кг)"
            elif diff < 0:
                diff_str = f"(−{abs(diff)} кг)"
            else:
                diff_str = "(= 0)"
            weight_change_str = f" | ⚖️ {latest_w} кг {diff_str}"

        # Monthly summary
        if days_with_logs > 0:
            avg_cal = int(total_cal / days_with_logs)
            lines.append(f"🍽️ Калорії: {total_cal:,} ккал | Днів: {days_with_logs}/30")
            lines.append(f"📈 Середнє/день: {avg_cal} ккал")
            lines.append(f"🥩 Б: {int(total_protein)} г | В: {int(total_carbs)} г | Ж: {int(total_fat)} г")
        else:
            lines.append("🍽️ Немає записів за цей період")

        lines.append(f"💪 Тренувань: {workout_count}{weight_change_str}")

        # Show last 3 logged days as mini-diary
        if days_data:
            lines.append("\n📋 Останні записи:")
            for d_str, cal in days_data[:3]:
                d_obj = date.fromisoformat(d_str)
                day_name = d_obj.strftime("%d.%m")
                lines.append(f"  {day_name}: {cal} ккал")

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
            "text": "❌ Не вдалося завантажити місячну статистику.",
        }




def _handle_tdee(chat_id: int) -> dict:
    """Show calculated TDEE and macro targets."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        macros = _calculate_tdee(user)
        weight = float(user.get('weight_kg', 70))
        goal = user.get('primary_goal', 'health')
        training_days = int(user.get('training_days_per_week', 3))

        goal_labels = {
            'muscle_gain': '📈 Набір маси (+300 ккал)',
            'fat_loss': '🔥 Жироспалення (-500 ккал)',
            'strength': '💪 Сила (TDEE)',
            'health': "❤️ Здоров'я (TDEE)",
            'recomposition': "♻️ Рекомпозиція (TDEE)",
        }

        lines = ["🎯 *Твої цілі*\n"]
        lines.append(f"Базовий обмін (BMR): {macros['tdee'] - 300} ккал")
        lines.append(f"Добова норма: {macros['target']} ккал")
        lines.append(f"Тренувань/тиждень: {training_days}")
        lines.append(f"Мета: {goal_labels.get(goal, 'TDEE')}")
        lines.append("")
        lines.append("🍽️ *Макроси:*")
        lines.append(f"Білок: {macros['protein_g']} г ({round(macros['protein_g'] / weight, 1)} г/кг)")
        lines.append(f"Вуглеводи: {macros['carbs_g']} г")
        lines.append(f"Жири: {macros['fat_g']} г")

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
            "text": "❌ Не вдалося розрахувати.",
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
