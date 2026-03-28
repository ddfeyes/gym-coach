import json
import os
from config import Config


def handle_telegram_update(update_data: dict) -> dict:
    """Обробка webhook оновлення від Telegram"""
    # Handle callback query from inline keyboard buttons
    callback_query = update_data.get('callback_query')
    if callback_query:
        from models.user import get_user_by_telegram_id
        user = get_user_by_telegram_id(callback_query['from']['id'])
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']
        data = callback_query.get('data', '')

        # Route callback data to appropriate handler
        if data == 'action:log':
            return _handle_inline_log(chat_id, message_id, callback_query['id'])
        elif data == 'action:log_snidanok':
            return _handle_inline_log_meal(chat_id, message_id, callback_query['id'], 'snidanok')
        elif data == 'action:log_obid':
            return _handle_inline_log_meal(chat_id, message_id, callback_query['id'], 'obid')
        elif data == 'action:log_vecherya':
            return _handle_inline_log_meal(chat_id, message_id, callback_query['id'], 'vecherya')
        elif data == 'action:log_perekus':
            return _handle_inline_log_meal(chat_id, message_id, callback_query['id'], 'perekus')
        elif data == 'action:water':
            return _handle_inline_water(chat_id, message_id, callback_query['id'])
        elif data == 'action:workout':
            return _handle_inline_workout(chat_id, message_id, callback_query['id'])
        elif data == 'action:week':
            return _handle_inline_week(chat_id, message_id, callback_query['id'])
        elif data == 'action:progress':
            return _handle_inline_progress(chat_id, message_id, callback_query['id'])
        else:
            return {"method": "answerCallbackQuery", "callback_query_id": callback_query['id']}

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
    if text.startswith('/today'):
        return _handle_today(chat_id)
    if text.startswith('/program'):
        return _handle_program(chat_id)
    if text.startswith('/log '):
        return _handle_log(chat_id, text[5:].strip())
    if text.startswith('/workout'):
        return _handle_workout(chat_id, text)
    if text.startswith('/water'):
        return _handle_water(chat_id, text)
    if text.startswith('/week'):
        return _handle_week(chat_id)
    if text.startswith('/month'):
        return _handle_month(chat_id)
    if text.startswith('/weight'):
        return _handle_weight(chat_id, text)
    if text.startswith('/measure'):
        return _handle_measure(chat_id, text)
    if text.startswith('/sleep'):
        return _handle_sleep(chat_id, text)
    if text.startswith('/next'):
        return _handle_next(chat_id)
    if text.startswith('/meals'):
        return _handle_meals(chat_id)
    if text.startswith('/profile'):
        return _handle_profile(chat_id)
    if text.startswith('/day'):
        return _handle_day(chat_id, text)
    if text.startswith('/progress'):
        return _handle_progress(chat_id)
    if text.startswith('/left'):
        return _handle_left(chat_id)
    if text.startswith('/target'):
        return _handle_target(chat_id, text)
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
        "/sleep — Переглянути або записати сон\n"
        "/tdee — Добова норма калорій та макроси\n"
        "/left — Скільки залишилось з'їсти сьогодні\n"
        "/target — Встановити добову ціль калорій\n"
        "/profile — Твій профіль та біо дані\n"
        "/day <дата> — Переглянути день (2026-03-25)\n"
        "/progress — Прогрес: вага, заміри, тренування\n"
        "/program — Твоя тренувальна програма\n"
        "/next — Що тренувати сьогодні\n"
        "/log <опис> — Швидко залогировать прийом їжі\n"
        "/meals — Сьогоднішній раціон (всі прийоми)\n"
        "/workout — Залогировать тренування\n"
        "/water [мл] — Додати води або переглянути\n"
        "/weight [кг] — Записати або переглянути вагу\n"
        "/measure — Переглянути заміри тіла\n"
        "/measure chest=95 waist=78 — Записати заміри\n\n"
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

    # Override from manual target setting
    override = user.get('calorie_target_override')
    if override and override > 0:
        target = override

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
                    done_marker = " ✅" if today_sessions else ""
                    lines.append(f"📅 *{day_label}*{done_marker}")
                    if day_exercises:
                        for ex in day_exercises[:5]:
                            lines.append(f"  • {ex['exercise']} — {ex['sets']}×{ex['reps']}")
                        if len(day_exercises) > 5:
                            lines.append(f"  ...та ще {len(day_exercises) - 5}")
                    else:
                        lines.append("  (вiдпочинок)")
                elif not schedule and not today_sessions:
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

        reply_markup = json.dumps({
            "inline_keyboard": [[
                {"text": "🍽️ Лог їжі", "callback_data": "action:log"},
                {"text": "💧 Вода", "callback_data": "action:water"},
                {"text": "💪 Тренування", "callback_data": "action:workout"},
            ], [
                {"text": "📊 Тиждень", "callback_data": "action:week"},
                {"text": "📈 Прогресс", "callback_data": "action:progress"},
            ]],
        })

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
            "reply_markup": reply_markup,
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


def _handle_workout(chat_id: int, raw_text: str = '') -> dict:
    """Quick log a training session. Accepts: /workout [duration] ["notes"]
    Examples: /workout, /workout 45, /workout 45min, /workout "felt great"
    Examples: /workout 45min "Upper body" """
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Спочатку пройди онбординг — натисни /start!",
        }

    try:
        import re
        from models.training_session import log_training_session, get_training_sessions
        from models.training_program import get_active_training_program
        from datetime import date

        # Parse duration and notes from raw_text
        duration = 0
        notes = ''

        text = raw_text.strip()

        # Extract duration: "45min", "45 min", "45", "1h30", "90min"
        duration_pattern = r'(\d+)\s*(?:h|год)?\s*(\d+)?\s*(?:min|хв|м|хвилин)?'
        duration_match = re.search(duration_pattern, text.lower())
        if duration_match:
            hours = int(duration_match.group(1)) if duration_match.group(1) else 0
            mins = int(duration_match.group(2)) if duration_match.group(2) else 0
            # If only one number and it's > 100, treat as minutes (common case)
            if hours > 0 and not duration_match.group(2):
                # Could be hours or minutes - check context
                if hours <= 23:  # likely minutes
                    duration = hours
                    hours = 0
                else:  # likely hours
                    mins = 0
            else:
                duration = hours * 60 + mins
            # Remove the duration part from text for notes
            text = re.sub(duration_pattern, '', text, flags=re.IGNORECASE).strip()

        # Extract quoted notes: "some text" or 'some text'
        quote_pattern = r'["\"\']([^"\']+)["\"\']]'
        quote_match = re.search(quote_pattern, text)
        if quote_match:
            notes = quote_match.group(1).strip()
        else:
            # Rest of text is notes
            notes = text.strip()
            # Remove common words
            notes = re.sub(r'^(тренування|треня|training|workout)\s*', '', notes, flags=re.IGNORECASE).strip()

        # Get active program
        program_id = None
        program_name = None
        today_workout = None
        active = get_active_training_program(user['id'])
        if active:
            program_id = active['id']
            program_name = active.get('name', 'Тренувальна програма')
            schedule = active.get('schedule', [])
            if schedule:
                today = date.today()
                day_idx = today.weekday() % len(schedule)
                today_workout = schedule[day_idx]

        # Log the session
        session_id = log_training_session(
            user['id'],
            program_id=program_id,
            duration_minutes=duration if duration > 0 else 0,
            notes=notes if notes else ''
        )

        # Calculate totals
        sessions = get_training_sessions(user['id'], limit=100)
        total = len(sessions)

        # Build confirmation
        lines = ["✅ *Тренування залоговано!*"]

        if today_workout:
            lines.append(f"🏋️ {today_workout}")

        if duration > 0:
            lines.append(f"⏱️ {duration} хв")

        if notes:
            lines.append(f"📝 {notes}")

        lines.append(f"\n💪 Всього тренувань: {total}")

        # Calculate streak
        from datetime import timedelta
        streak = 0
        current = date.today()
        while True:
            week_start = current - timedelta(days=current.weekday())
            week_end = week_start + timedelta(days=6)
            week_sessions = [s for s in sessions
                           if week_start <= date.fromisoformat(s['date']) <= week_end]
            if week_sessions:
                streak += 1
                current = week_start - timedelta(days=1)
            else:
                break
            if streak > 52:
                break

        if streak > 0:
            lines.append(f"🔥 Streak: {streak} тижнів")

        lines.append(f"\n💡 /next — що тренувати сьогодні")
        lines.append(f"💡 /program — повна програма")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }

    except Exception as e:
        import traceback
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося залогировать: " + str(e),
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




def _handle_weight(chat_id: int, text: str) -> dict:
    """Handle /weight command — show weight history or log new weight.
    /weight — show latest weight + recent history
    /weight 75.5 — log weight for today
    /weight 75.5 2026-03-27 — log weight for specific date
    """
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.weight_log import log_weight, get_weight_history, get_latest_weight
        from datetime import date, timedelta

        parts = text.split()
        target_weight = user.get('target_weight')
        unit = "кг"

        # Parse command: /weight [value] [date]
        log_date = None
        weight_value = None

        if len(parts) > 1:
            # Try to parse weight value
            try:
                weight_value = float(parts[1].replace(',', '.'))
            except ValueError:
                weight_value = None

            # Optional date argument
            if len(parts) > 2:
                log_date = parts[2].strip()

        # Log weight if value provided
        if weight_value:
            if weight_value < 20 or weight_value > 500:
                return {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "⚠️ Нереалістична вага! Вкажи між 20 і 500 кг.",
                }

            actual_date = log_date if log_date else str(date.today())
            log_weight(user['id'], weight_value, log_date=actual_date)

            latest = get_latest_weight(user['id'])
            latest_kg = latest['weight_kg'] if latest else weight_value

            # Build response
            lines = ["⚖️ Записано: *"+str(weight_value)+" "+unit+"*"]
            lines.append("📅 Дата: " + actual_date)

            if target_weight:
                diff = latest_kg - target_weight
                if diff > 0:
                    lines.append("📊 До мети: *-"+str(round(diff, 1))+" "+unit+"* (залишилось)")
                elif diff < 0:
                    lines.append("📊 Перевищення мети на *+"+str(round(abs(diff), 1))+" "+unit+"*")
                else:
                    lines.append("📊 ✅ На цілі!")

            lines.append("\n💡 Відкрий додаток щоб побачити графік!")
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "\n".join(lines),
                "parse_mode": "Markdown",
            }

        # Show weight history
        history = get_weight_history(user['id'], limit=30)
        latest = get_latest_weight(user['id'])

        lines = ["⚖️ *Вага*\n"]

        if latest:
            latest_date = date.fromisoformat(latest['date'])
            days_ago = (date.today() - latest_date).days
            age_str = "" if days_ago == 0 else (" ("+str(days_ago)+" дн. тому)" if days_ago > 0 else " (сьогодні)")
            lines.append("Остання: *" + str(latest['weight_kg']) + " " + unit + "*" + age_str)
        else:
            lines.append("Немає даних. Додай першу вагу!")

        if target_weight:
            lines.append("🎯 Мета: " + str(target_weight) + " " + unit)

        if history and len(history) > 1:
            # Show last 7 entries
            last7 = history[:7]
            lines.append("\n📋 Останні записи:")
            for entry in reversed(last7):
                d = date.fromisoformat(entry['date'])
                day_name = d.strftime("%d.%m")
                w = entry['weight_kg']
                # Compare to previous
                prev = history[history.index(entry)+1]['weight_kg'] if history.index(entry) < len(history)-1 else w
                diff = w - prev
                if abs(diff) < 0.05:
                    arrow = "→"
                elif diff > 0:
                    arrow = "↑"
                else:
                    arrow = "↓"
                lines.append("  " + day_name + ": " + str(w) + " " + unit + " " + arrow)

            # Show change over period
            if len(history) >= 2:
                oldest = history[-1]['weight_kg']
                newest = history[0]['weight_kg']
                change = newest - oldest
                if abs(change) >= 0.1:
                    if change > 0:
                        lines.append("\n📈 Зміна: *+"+str(round(change, 1))+" "+unit+"* за "+str(len(history)-1)+" днів")
                    else:
                        lines.append("\n📉 Зміна: *"+str(round(change, 1))+" "+unit+"* за "+str(len(history)-1)+" днів")

        lines.append("\n💡 /weight 75.5 — записати вагу")
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
            "text": "❌ Не вдалося завантажити дані про вагу.",
        }

def _handle_measure(chat_id: int, text: str) -> dict:
    """Handle /measure command — show or log body measurements.
    /measure — show latest measurements + recent history
    /measure chest=95 waist=78 biceps_l=35 — log measurements for today
    /measure chest=95 2026-03-28 — log for specific date
    """
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.measurement import log_measurement, get_measurement_history, get_latest_measurement
        from datetime import date

        # Parse command
        # /measure chest=95 waist=78 [date]
        parts = text.split()
        measurement_date = str(date.today())
        parsed_measurements = {}

        for part in parts[1:]:
            if '=' in part:
                key, val = part.split('=', 1)
                key = key.strip().lower()
                val = val.strip()
                # Map common aliases
                alias_map = {
                    'chest': 'chest',
                    'waist': 'waist',
                    'hips': 'hips',
                    'biceps_l': 'biceps_l',
                    'biceps_r': 'biceps_r',
                    'b_l': 'biceps_l',
                    'b_r': 'biceps_r',
                    'thigh_l': 'thigh_l',
                    'thigh_r': 'thigh_r',
                    't_l': 'thigh_l',
                    't_r': 'thigh_r',
                    'note': 'notes',
                    'notes': 'notes',
                }
                if key in alias_map:
                    try:
                        parsed_measurements[alias_map[key]] = float(val)
                    except ValueError:
                        return {
                            "method": "sendMessage",
                            "chat_id": chat_id,
                            "text": "⚠️ Невірне значення для " + key + ": " + val + ". Вкажи число.",
                        }
                else:
                    return {
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": "⚠️ Невідоме поле: " + key + ". Дозволені: chest, waist, hips, biceps_l, biceps_r, thigh_l, thigh_r",
                    }
            elif '-' in part and len(part) == 10:
                # Looks like a date
                measurement_date = part

        # Log if measurements provided
        if parsed_measurements:
            try:
                log_measurement(user['id'], measurement_date=measurement_date, **parsed_measurements)
            except Exception as e:
                return {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "❌ Не вдалося зберегти заміри: " + str(e),
                }

            lines = ["📏 *Заміри записано!*"]
            if measurement_date == str(date.today()):
                lines.append("📅 Сьогодні")
            else:
                lines.append("📅 " + measurement_date)
            for k, v in parsed_measurements.items():
                labels = {
                    'chest': 'Груди',
                    'waist': 'Талія',
                    'hips': 'Стегна',
                    'biceps_l': 'Біцепс ℒ',
                    'biceps_r': 'Біцепс ɍ',
                    'thigh_l': 'Стегно ℒ',
                    'thigh_r': 'Стегно ɍ',
                    'notes': 'Нотатки',
                }
                lines.append(labels.get(k, k) + ": *" + str(v) + "*")
            lines.append("\n💡 Відкрий додаток щоб побачити графік!")
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "\n".join(lines),
                "parse_mode": "Markdown",
            }

        # Show history
        latest = get_latest_measurement(user['id'])
        history = get_measurement_history(user['id'], limit=30)

        lines = ["📏 *Заміри тіла*\n"]

        if latest:
            latest_date = date.fromisoformat(latest['date'])
            days_ago = (date.today() - latest_date).days
            age_str = "" if days_ago == 0 else (" ("+str(days_ago)+" дн. тому)" if days_ago > 0 else " (сьогодні)")
            lines.append("📅 *Останні:* " + latest['date'] + age_str)

            # Show latest values with emoji
            fields = [
                ('chest', 'Груди', '💪'),
                ('waist', 'Талія', '📐'),
                ('hips', 'Стегна', '🦵'),
                ('biceps_l', 'Біцепс ℒ', '💪'),
                ('biceps_r', 'Біцепс ɍ', '💪'),
                ('thigh_l', 'Стегно ℒ', '🦵'),
                ('thigh_r', 'Стегно ɍ', '🦵'),
            ]
            for key, label, icon in fields:
                val = latest.get(key)
                if val is not None and val > 0:
                    lines.append("  " + icon + " " + label + ": *" + str(val) + "* см")
        else:
            lines.append("Немає даних. Додай перші заміри!")

        if history and len(history) > 1:
            lines.append("\n📋 Останні записи:")
            for entry in reversed(history[:5]):
                d = date.fromisoformat(entry['date'])
                day_name = d.strftime("%d.%m")
                chest = entry.get('chest')
                waist = entry.get('waist')
                if chest or waist:
                    parts_str = []
                    if chest: parts_str.append("г:"+str(chest))
                    if waist: parts_str.append("т:"+str(waist))
                    lines.append("  " + day_name + ": " + ", ".join(parts_str))

        lines.append("\n💡 /measure chest=95 waist=78 — записати заміри")
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }

    except Exception as e:
        import traceback
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити дані про заміри: " + str(e),
        }

def _handle_sleep(chat_id: int, text: str) -> dict:
    """Handle /sleep command — view or log sleep data.
    /sleep — show 7-day sleep summary
    /sleep 7.5 — log 7.5h sleep (quality=3 default)
    /sleep 7.5 4 — log 7.5h with quality 4/5
    /sleep 8 2026-03-27 — log 8h for specific date
    """
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.sleep_log import log_sleep, get_sleep_summary
        from datetime import date, timedelta

        parts = text.split()
        log_date = str(date.today())
        log_hours = None
        log_quality = 3

        for part in parts[1:]:
            if '-' in part and len(part) == 10 and part[4] == '-' and part[7] == '-':
                log_date = part
            elif '.' in part:
                try:
                    hours = float(part)
                    if 0 < hours <= 24:
                        log_hours = hours
                except ValueError:
                    pass
            else:
                try:
                    q = int(part)
                    if 1 <= q <= 5:
                        log_quality = q
                except ValueError:
                    pass

        # Log if hours provided
        if log_hours is not None:
            try:
                log_sleep(user['id'], hours=log_hours, quality=log_quality, log_date=log_date)
            except Exception as e:
                return {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "❌ Не вдалося записати сон: " + str(e),
                }

            quality_emoji = '⭐' * log_quality + '☆' * (5 - log_quality)
            date_str = "сьогодні" if log_date == str(date.today()) else log_date
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "😴 *Сон записано!*\n📅 " + date_str + "\n⏱️ " + str(log_hours) + " год\n" + quality_emoji,
                "parse_mode": "Markdown",
            }

        # Show 7-day summary
        summary = get_sleep_summary(user['id'], days=7)
        history = summary.get('entries', [])

        lines = ["😴 *Сон — останні 7 днів*\n"]

        avg_h = summary.get('average_hours', 0)
        avg_q = summary.get('average_quality', 0)
        if avg_h > 0:
            quality_stars = '⭐' * round(avg_q) + '☆' * (5 - round(avg_q))
            lines.append("📊 Середнє: *" + str(avg_h) + "* год | Якість: " + quality_stars)
        else:
            lines.append("📊 Немає даних за останні 7 днів")

        if history:
            lines.append("")
            day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
            for entry in reversed(history):
                d = date.fromisoformat(entry['date'])
                day_name = day_names[d.weekday()]
                day_str = d.strftime('%d.%m')
                h = entry.get('hours', 0)
                q = entry.get('quality', 0)
                if h > 0:
                    stars = '⭐' * q + '☆' * (5 - q)
                    # Mood based on hours
                    if h >= 8:
                        mood = '✅'
                    elif h >= 6:
                        mood = '🔶'
                    else:
                        mood = '⚠️'
                    lines.append(f"  {mood} {day_str} ({day_name}): *{h}* год {stars}")

        lines.append("\n💡 /sleep 7.5 — записати сон")
        lines.append("💡 /sleep 7.5 4 — з якістю 4/5")
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }

    except Exception as e:
        import traceback
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити дані про сон: " + str(e),
        }

def _handle_next(chat_id: int) -> dict:
    """Handle /next command — show today's scheduled workout from the training program.
    The schedule is assumed to align with Mon=0, Sun=6."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.training_program import get_active_training_program
        from datetime import date

        program = get_active_training_program(user['id'])
        if not program:
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "🏋️ У тебе ще немає програми! Відкрий додаток і згенеруй свою першу програму.",
            }

        schedule = program.get('schedule', [])
        exercises = program.get('exercises', [])
        program_name = program.get('name', 'Тренувальна програма')

        if not schedule:
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "🏋️ Програма порожня. Відкрий додаток щоб налаштувати вправи.",
            }

        # Build exercise list per day (1-indexed, matches schedule positions)
        by_day = {}
        for ex in exercises:
            d = ex.get('day', 1)
            if d not in by_day:
                by_day[d] = []
            by_day[d].append(ex)

        # Map today's weekday (0=Mon) to schedule index
        today = date.today()
        today_weekday = today.weekday()  # 0=Mon ... 6=Sun

        if today_weekday < len(schedule):
            day_label = schedule[today_weekday]
            day_num = today_weekday + 1  # 1-indexed for exercises
        else:
            # Program has fewer days than a week — use modulo
            day_idx = today_weekday % len(schedule)
            day_label = schedule[day_idx]
            day_num = day_idx + 1

        day_exercises = by_day.get(day_num, [])
        day_names_ukr = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця", 'Субота', 'Неділя']
        day_name = day_names_ukr[today_weekday]
        today_str = "Сьогодні (" + day_name + ")"

        lines = [f"🏋️ *{program_name}*\n📅 {today_str}\n📋 {day_label}"]

        if day_exercises:
            # Group by muscle group for cleaner display
            by_muscle = {}
            for ex in day_exercises:
                mg = ex.get('muscle_group', 'Інше')
                if mg not in by_muscle:
                    by_muscle[mg] = []
                by_muscle[mg].append(ex)

            for mg, exs in by_muscle.items():
                lines.append(f"\n💪 {mg}:")
                for ex in exs:
                    sets_reps = f"{ex['sets']}×{ex['reps']}"
                    rest = ex.get('rest_seconds')
                    rest_str = f" | відпочинок {rest}с" if rest else ""
                    lines.append(f"  • {ex['exercise']} — {sets_reps}{rest_str}")
        else:
            lines.append("\n🌿 Відпочинок")

        lines.append(f"\n💡 /workout — залогировать тренування")
        lines.append("💡 /program — повна програма")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }

    except Exception as e:
        import traceback
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити програму: " + str(e),
        }

def _handle_meals(chat_id: int) -> dict:
    """Handle /meals command — show today's logged meals with calorie breakdown."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.nutrition import get_daily_summary
        from datetime import date

        today = str(date.today())
        summary = get_daily_summary(user['id'], today)
        meals = summary.get('meals', [])
        macros = _calculate_tdee(user)

        lines = ["🍽️ *Сьогоднішній раціон*\n"]

        if not meals:
            lines.append("Ще немає записів.")
            lines.append(f"\n💡 /log <опис> — додати прийом їжі")
            lines.append(f"Приклад: /log 2 яйця + тост + кава")
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "\n".join(lines),
                "parse_mode": "Markdown",
            }

        # Group by meal type
        meal_order = ['breakfast', 'lunch', 'dinner', 'snack']
        meal_labels = {
            'breakfast': '☀️ Сніданок',
            'lunch': '🌇 Обід',
            'dinner': '🌙 Вечеря',
            'snack': '🍎 Перекус',
        }
        by_type = {m: [] for m in meal_order}
        for m in meals:
            mt = m.get('meal_type', 'snack')
            if mt not in by_type:
                by_type[mt] = []
            by_type[mt].append(m)

        total_cal = summary.get('total_calories', 0)
        total_prot = summary.get('total_protein', 0)
        total_carbs = summary.get('total_carbs', 0)
        total_fat = summary.get('total_fat', 0)
        target = macros.get('target', 2000)

        # Show each meal type
        for mtype in meal_order:
            meal_list = by_type.get(mtype, [])
            if not meal_list:
                continue
            label = meal_labels.get(mtype, mtype.capitalize())
            lines.append(f"\n{label}:")
            for meal in meal_list:
                fname = meal.get('food_name', 'Невідомо')
                cal = meal.get('calories', 0)
                prot = meal.get('protein', 0)
                lines.append(f"  • {fname} — *{cal}* ккал" +
                             (f" | Б:{prot}г" if prot else ""))
            meal_cal = sum(m.get('calories', 0) for m in meal_list)
            lines.append(f"  └ Всього: *{meal_cal}* ккал")

        # Summary
        remaining = target - total_cal
        pct = round(total_cal / target * 100) if target > 0 else 0
        bar_len = 10
        filled = min(bar_len, round(bar_len * total_cal / target)) if target > 0 else 0
        bar = '█' * filled + '░' * (bar_len - filled)

        lines.append(f"\n━━━━━━━━━━━━━━")
        lines.append(f"Σ *{total_cal}* / {target} ккал ({pct}%)")
        lines.append(f"[{bar}]")
        if remaining > 0:
            lines.append(f"Залишилось: *{remaining}* ккал")
        elif remaining < 0:
            lines.append(f"⚠️ Перебір: *{-remaining}* ккал")
        else:
            lines.append("✅ Точно по плану!")

        lines.append(f"\n🥩 Б: {round(total_prot)}г | В: {round(total_carbs)}г | Ж: {round(total_fat)}г")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }

    except Exception as e:
        import traceback
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити дані: " + str(e),
        }

def _handle_progress(chat_id: int) -> dict:
    """Handle /progress command — show overall progress summary.
    Weight trend, measurement changes, training frequency, streak."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from datetime import date, timedelta
        from models.weight_log import get_weight_history
        from models.measurement import get_measurement_history
        from models.training_session import get_training_sessions

        lines = ["📊 *Твій прогрес*\n"]

        # Weight history — first and latest
        weight_history = get_weight_history(user['id'], limit=30)
        if len(weight_history) >= 2:
            first = weight_history[-1]
            last = weight_history[0]
            first_w = first.get('weight_kg', 0)
            last_w = last.get('weight_kg', 0)
            change = last_w - first_w
            emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            first_date = first.get('date', '')[:5]
            last_date = last.get('date', '')[:5]
            lines.append(f"{emoji} *Вага:* {first_w} → {last_w} кг ({change:+.1f})")
            lines.append(f"   ({first_date} → {last_date})")
        elif len(weight_history) == 1:
            lines.append(f"⚖️ *Вага:* {weight_history[0].get('weight_kg')} кг")
        else:
            lines.append("⚖️ *Вага:* немає даних")

        # Measurement changes — first vs latest (measurements table has all fields per row)
        measurement_rows = get_measurement_history(user['id'], limit=100)
        if len(measurement_rows) >= 2:
            first_row = measurement_rows[-1]  # oldest
            last_row = measurement_rows[0]   # newest

            field_labels = {
                'biceps_l': 'Біцепс лівий',
                'biceps_r': 'Біцепс правий',
                'chest': 'Груди',
                'waist': 'Талія',
                'hips': 'Стегна',
                'thigh_l': 'Стегно ліве',
                'thigh_r': 'Стегно праве',
            }

            changes = []
            for field, label in field_labels.items():
                v_first = first_row.get(field)
                v_last = last_row.get(field)
                if v_first is not None and v_last is not None:
                    chg = v_last - v_first
                    if abs(chg) > 0.01:  # only show meaningful changes
                        changes.append((label, v_first, v_last, chg))

            if changes:
                lines.append("\n📏 *Заміри тіла:*")
                for label, v_first, v_last, chg in changes:
                    emoji = "📈" if chg > 0 else "📉" if chg < 0 else "➡️"
                    lines.append(f"{emoji} {label}: {v_first} → {v_last} см ({chg:+.1f})")

        # Training sessions — total + per week average
        sessions = get_training_sessions(user['id'], limit=100)
        total = len(sessions)
        lines.append(f"\n🏋️ *Тренування:* {total} всього")

        if total > 0:
            dates = [date.fromisoformat(s['date']) for s in sessions]
            min_d = min(dates)
            max_d = max(dates)
            weeks_span = max(1, (max_d - min_d).days // 7)
            avg = total / weeks_span
            lines.append(f"📅 Середнє: {avg:.1f} тренувань/тиждень")

        # Streak
        if sessions:
            streak = 0
            current = date.today()
            while True:
                week_start = current - timedelta(days=current.weekday())
                week_end = week_start + timedelta(days=6)
                week_sessions = [s for s in sessions
                               if week_start <= date.fromisoformat(s['date']) <= week_end]
                if week_sessions:
                    streak += 1
                    current = week_start - timedelta(days=1)
                else:
                    break
                if streak > 52:
                    break
            if streak > 0:
                lines.append(f"🔥 Streak: {streak} тижнів")

        # Active program
        try:
            from models.training_program import get_active_training_program
            active = get_active_training_program(user['id'])
            if active:
                lines.append(f"\n📋 *Програма:* {active.get('name', 'Моя програма')}")
        except:
            pass

        lines.append(f"\n💡 /stats — детальна статистика")
        lines.append(f"💡 /week — щотижневий звіт")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }

    except Exception as e:
        import traceback
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити прогрес: " + str(e),
        }

def _handle_profile(chat_id: int) -> dict:
    """Handle /profile command — show user profile summary."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.weight_log import get_latest_weight
        from models.measurement import get_latest_measurement
        from models.training_session import get_training_sessions
        from datetime import date

        lines = ["👤 *Твій профіль*\n"]

        # Name
        name = user.get('name', '')
        if name:
            lines.append(f"Ім'я: {name}")

        # Gender + Age + Height
        gender_map = {'male': 'Чоловік', 'female': 'Жінка', 'other': 'Інше'}
        gender = gender_map.get(user.get('gender', ''), user.get('gender', '—'))
        age = user.get('age') or '—'
        height = user.get('height_cm') or '—'
        lines.append(f"Стать: {gender} | Вік: {age} | Зріст: {height} см")

        # Current weight (latest logged, not onboarding weight)
        latest_weight = get_latest_weight(user['id'])
        if latest_weight:
            lines.append(f"Поточна вага: {latest_weight.get('weight_kg')} кг")
        else:
            onboarding_weight = user.get('weight_kg', '—')
            lines.append(f"Вага (онбординг): {inboarding_weight} кг")

        # Experience + training days
        exp_map = {
            'beginner': 'Початківець',
            'intermediate': 'Середній',
            'advanced': 'Просунутий',
        }
        exp = exp_map.get(user.get('experience_level', ''), user.get('experience_level', '—'))
        training_days = user.get('training_days_per_week', '—')
        lines.append(f"Досвід: {exp} | Тренувань/тиждень: {training_days}")

        # Primary goal
        goal_map = {
            'muscle_gain': '📈 Набір маси',
            'fat_loss': '🔥 Жироспалення',
            'strength': '💪 Сила',
            'health': "❤️ Здоров'я",
            'recomposition': '♻️ Рекомпозиція',
        }
        goal = goal_map.get(user.get('primary_goal', ''), user.get('primary_goal', '—'))
        lines.append(f"Мета: {goal}")

        # Secondary goals
        try:
            import json
            secondary = json.loads(user.get('secondary_goals', '[]'))
            if secondary:
                goal_labels = list(goal_map.values())
                secondary_labels = [goal_labels[int(g)] if g.isdigit() and int(g) < len(goal_labels) else g for g in secondary]
                lines.append(f"Додаткові цілі: {', '.join(secondary_labels)}")
        except:
            pass

        # Latest measurements
        meas = get_latest_measurement(user['id'])
        if meas:
            date_str = meas.get('date', '')[:5]
            lines.append(f"\n📏 Останні заміри ({date_str}):")
            field_map = {
                'biceps_l': 'Біцепс лівий',
                'biceps_r': 'Біцепс правий',
                'chest': 'Груди',
                'waist': 'Талія',
                'hips': 'Стегна',
                'thigh_l': 'Стегно ліве',
                'thigh_r': 'Стегно праве',
            }
            parts = []
            for field, label in field_map.items():
                val = meas.get(field)
                if val:
                    parts.append(f"{label} {val}")
            if parts:
                lines.append(", ".join(parts))

        # Active training program
        try:
            from models.training_program import get_active_training_program
            active = get_active_training_program(user['id'])
            if active:
                lines.append(f"\n📋 Програма: {active.get('name', 'Моя програма')}")
        except:
            pass

        lines.append(f"\n💡 /tdee — розрахунок калорій та макросів")
        lines.append(f"💡 /progress — прогрес тренувань")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }

    except Exception as e:
        import traceback
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити профіль: " + str(e),
        }

def _handle_day(chat_id: int, text: str) -> dict:
    """Handle /day <date> command — show all tracking for a specific date.
    Usage: /day 2026-03-25 or /day yesterday or /day today"""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from datetime import date, timedelta, datetime
        from models.nutrition import get_daily_summary
        from models.training_session import get_sessions_by_date_range
        from models.sleep_log import get_sleep_logs
        from models.water_log import get_daily_water
        from models.weight_log import get_weight_history

        # Parse date argument
        arg = text.strip().lower()
        if not arg or arg == 'today':
            target_date = date.today()
        elif arg == 'yesterday':
            target_date = date.today() - timedelta(days=1)
        else:
            # Try YYYY-MM-DD
            try:
                target_date = date.fromisoformat(arg)
            except ValueError:
                # Try DD.MM.YYYY or DD/MM/YYYY
                for fmt in ['%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        target_date = datetime.strptime(arg, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return {
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": "❌ Неправильний формат дати. Використай:\n`/day` — сьогодні\n`/day 2026-03-25` — конкретна дата\n`/day yesterday` — вчора",
                        "parse_mode": "Markdown",
                    }

        target_str = str(target_date)
        date_display = target_date.strftime('%d.%m.%Y')

        lines = [f"📅 *{date_display}*\n"]

        # === Nutrition ===
        nutrition = get_daily_summary(user['id'], target_str)
        meals = nutrition.get('meals', [])
        total_cal = nutrition.get('total_calories', 0)

        if meals:
            lines.append(f"🍽️ *Харчування:* {total_cal} ккал")
            for meal in meals:
                name = meal.get('meal_name', meal.get('description', 'Прийом'))
                cal = meal.get('calories', 0)
                p = meal.get('protein', 0)
                c = meal.get('carbs', 0)
                f = meal.get('fat', 0)
                lines.append(f"  • {name}: {cal} ккал | Б: {p}г В: {c}г Ж: {f}г")
            lines.append(f"  💰 Всього: {total_cal} ккал | Б: {nutrition.get('total_protein',0)}г В: {nutrition.get('total_carbs',0)}г Ж: {nutrition.get('total_fat',0)}г")
        else:
            lines.append("🍽️ Харчування: немає записів")

        # === Training ===
        sessions = get_sessions_by_date_range(user['id'], target_str, target_str)
        if sessions:
            lines.append(f"\n🏋️ *Тренування:*")
            for s in sessions:
                name = s.get('workout_name', s.get('program_name', 'Тренування'))
                dur = s.get('duration_minutes')
                dur_str = f" ({dur} хв)" if dur else ""
                lines.append(f"  • {name}{dur_str}")
        else:
            lines.append("\n🏋️ Тренування: немає")

        # === Sleep ===
        try:
            sleep_logs = get_sleep_history(user['id'], days=30)
            sleep_today = [sl for sl in sleep_logs if sl.get('date', '') == target_str]
            if sleep_today:
                sl = sleep_today[0]
                duration = sl.get('hours', 0)
                quality = sl.get('quality', '')
                lines.append(f"\n😴 *Сон:* {duration} год")
                if quality:
                    lines.append(f"   Якість: {quality}/5")
            else:
                lines.append("\n😴 Сон: немає записів")
        except:
            lines.append("\n😴 Сон: немає записів")

        # === Water ===
        try:
            water = get_daily_water(user['id'], target_str)
            amount = water.get('amount_ml', 0) if isinstance(water, dict) else 0
            if amount > 0:
                lines.append(f"\n💧 Вода: {amount} мл")
            else:
                lines.append("\n💧 Вода: немає записів")
        except:
            lines.append("\n💧 Вода: немає записів")

        # === Weight ===
        weight_history = get_weight_history(user['id'], limit=100)
        weight_today = next((w for w in weight_history if w.get('date', '') == target_str), None)
        if weight_today:
            lines.append(f"\n⚖️ Вага: {weight_today.get('weight_kg')} кг")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }

    except Exception as e:
        import traceback
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося завантажити дані: " + str(e),
        }



def _handle_left(chat_id: int) -> dict:
    """Show calories/macros remaining for today vs daily targets."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.nutrition import get_daily_summary
        from models.water_log import get_daily_water
        from datetime import date

        today_str = str(date.today())

        # Today's logged nutrition
        daily = get_daily_summary(user['id'], today_str)
        eaten_cal = daily.get('total_calories', 0)
        eaten_protein = daily.get('total_protein', 0)
        eaten_carbs = daily.get('total_carbs', 0)
        eaten_fat = daily.get('total_fat', 0)

        # Water
        water = get_daily_water(user['id'], today_str)
        water_ml = water.get('amount_ml', 0) if isinstance(water, dict) else 0

        # TDEE targets
        macros = _calculate_tdee(user)
        target_cal = macros['target']
        target_protein = macros['protein_g']
        target_carbs = macros['carbs_g']
        target_fat = macros['fat_g']
        water_target = 2500  # default 2.5L

        # Calculate remaining
        left_cal = max(0, target_cal - eaten_cal)
        left_protein = max(0, target_protein - eaten_protein)
        left_carbs = max(0, target_carbs - eaten_carbs)
        left_fat = max(0, target_fat - eaten_fat)
        left_water = max(0, water_target - water_ml)

        # Progress bars (10 chars)
        def bar(filled, total, width=10):
            if total <= 0:
                return "▓" * width
            pct = min(1.0, filled / total)
            filled_chars = round(pct * width)
            return "▓" * filled_chars + "░" * (width - filled_chars)

        cal_bar = bar(eaten_cal, target_cal)
        cal_pct = min(100, round(eaten_cal / target_cal * 100)) if target_cal > 0 else 0

        lines = ["🍽️ *Залишок на сьогодні*\n"]
        lines.append(f"[{cal_bar}] {cal_pct}%\n")

        lines.append(f"🎯 Калорії: *{left_cal}* ккал залишилось ({eaten_cal}/{target_cal})")
        lines.append(f"🥩 Білок:   {round(left_protein)} г ({round(eaten_protein)}/{target_protein})")
        lines.append(f"🌾 Вуглеводи: {round(left_carbs)} г ({round(eaten_carbs)}/{target_carbs})")
        lines.append(f"🧈 Жири:    {round(left_fat)} г ({round(eaten_fat)}/{target_fat})")

        if water_ml > 0 or water_target > 0:
            water_bar = bar(water_ml, water_target)
            water_pct = min(100, round(water_ml / water_target * 100)) if water_target > 0 else 0
            lines.append(f"\n💧 Вода: [{water_bar}] {water_pct}% ({water_ml}/{water_target} мл)")

        lines.append("\n📋 Відкрий додаток щоб побачити детальніше!")

        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "\n".join(lines),
            "parse_mode": "Markdown",
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося розрахувати.",
        }

def _handle_target(chat_id: int, text: str) -> dict:
    """Handle /target command — set or view daily calorie target.
    Usage: /target — view current target, /target 2200 — set new target."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "👋 Ти ще не пройшов онбординг! Натисни /start щоб почати.",
        }

    try:
        from models.user import set_calorie_target, get_calorie_target

        parts = text.strip().split()
        macros = _calculate_tdee(user)

        if len(parts) == 1:
            # View current target
            current = get_calorie_target(user['id'])
            override_note = ""
            if current and current > 0:
                override_note = f"\n⚙️ Встановлена вручну: {current} ккал"
                lines = [
                    "🎯 *Поточна денна норма калорій*\n",
                    f"Розрахована: {macros['target']} ккал{override_note}",
                    "",
                    f"🥩 Білок: {macros['protein_g']} г",
                    f"🌾 Вуглеводи: {macros['carbs_g']} г",
                    f"🧈 Жири: {macros['fat_g']} г",
                    "",
                    "💡 /target <число> — змінити ціль",
                ]
            else:
                lines = [
                    "🎯 *Поточна денна норма калорій*\n",
                    f"{macros['target']} ккал (розрахована)",
                    "",
                    f"🥩 Білок: {macros['protein_g']} г",
                    f"🌾 Вуглеводи: {macros['carbs_g']} г",
                    f"🧈 Жири: {macros['fat_g']} г",
                    "",
                    "💡 /target <число> — встановити свою ціль",
                ]
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "\n".join(lines),
                "parse_mode": "Markdown",
            }
        else:
            # Set new target
            try:
                new_target = int(parts[1])
                if new_target < 500 or new_target > 10000:
                    return {
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": "❌ Ціль має бути від 500 до 10000 ккал.",
                    }
            except ValueError:
                return {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "❌ Невірний формат. Приклад: /target 2200",
                }

            set_calorie_target(user['id'], new_target)
            lines = [
                "✅ *Ціль встановлена*\n",
                f"Нова денна норма: {new_target} ккал",
                "",
                f"🥩 Білок: {macros['protein_g']} г",
                f"🌾 Вуглеводи: {macros['carbs_g']} г",
                f"🧈 Жири: {macros['fat_g']} г",
                "",
                "❌ Щоб скасувати — /target 0",
            ]
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "\n".join(lines),
                "parse_mode": "Markdown",
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❌ Не вдалося встановити ціль.",
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

def _handle_inline_log(chat_id: int, message_id: int, cq_id: str) -> dict:
    """Respond to inline log food button — show meal type quick-add options."""
    return {
        "method": "editMessageText",
        "chat_id": chat_id,
        "message_id": message_id,
        "text": "🍽️ *Лог прийому їжі*\n\nОбери тип прийому або використай:\n`/log Обід: курча з рисом`",
        "parse_mode": "Markdown",
        "reply_markup": json.dumps({
            "inline_keyboard": [[
                {"text": "🍳 Сніданок", "callback_data": "action:log_snidanok"},
                {"text": "🍲 Обід", "callback_data": "action:log_obid"},
                {"text": "🍽️ Вечеря", "callback_data": "action:log_vecherya"},
            ], [
                {"text": "🍎 Перекус", "callback_data": "action:log_perekus"},
                {"text": "💧 Вода", "callback_data": "action:water"},
                {"text": "💪 Тренування", "callback_data": "action:workout"},
            ]],
        }),
    }


def _handle_inline_log_meal(chat_id: int, message_id: int, cq_id: str, meal_type: str) -> dict:
    """Show format hint for specific meal type."""
    meal_hints = {
        "snidanok": "🍳 *Сніданок* — приклад:\n`/log Сніданок: вівсянка з бананом і медом`",
        "obid": "🍲 *Обід* — приклад:\n`/log Обід: курча з рисом і овочами`",
        "vecherya": "🍽️ *Вечеря* — приклад:\n`/log Вечеря: салат з лососем`",
        "perekus": "🍎 *Перекус* — приклад:\n`/log Перекус: йогурт з горіхами`",
    }
    hint = meal_hints.get(meal_type, "Вибери тип прийому їжі")
    return {
        "method": "editMessageText",
        "chat_id": chat_id,
        "message_id": message_id,
        "text": hint + "\n\n_Скопіюй і заміни на своє_",
        "parse_mode": "Markdown",
        "reply_markup": json.dumps({
            "inline_keyboard": [[
                {"text": "🍽️ Інший прийом", "callback_data": "action:log"},
                {"text": "💧 Вода", "callback_data": "action:water"},
            ]],
        }),
    }


def _handle_inline_water(chat_id: int, message_id: int, cq_id: str) -> dict:
    """Log 250ml water and respond."""
    user = _get_user(chat_id)
    if not user or not user.get('onboarding_completed'):
        return {"method": "answerCallbackQuery", "callback_query_id": cq_id, "text": "❌ Спочатку /start"}
    try:
        from models.water_log import add_water_log
        from datetime import date
        add_water_log(user['id'], date.today().isoformat(), 250)
        today = str(date.today())
        from models.water_log import get_daily_water
        today_water = get_daily_water(user['id'], today)
        water_ml = today_water.get('amount_ml', 0)
        return {
            "method": "editMessageText",
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"💧 *Вода записана!*\n\n+250 мл\nСьогодні: {water_ml} / 2500 мл",
            "parse_mode": "Markdown",
            "reply_markup": json.dumps({
                "inline_keyboard": [[{"text": "🍽️ Лог їжі", "callback_data": "action:log"}, {"text": "💪 Тренування", "callback_data": "action:workout"}]],
            }),
        }
    except Exception as e:
        return {"method": "answerCallbackQuery", "callback_query_id": cq_id, "text": "❌ Помилка"}


def _handle_inline_workout(chat_id: int, message_id: int, cq_id: str) -> dict:
    """Show workout logging instructions."""
    return {
        "method": "editMessageText",
        "chat_id": chat_id,
        "message_id": message_id,
        "text": "💪 *Лог тренування*\n\nВикористай:\n`/workout` — швидкий лог\n`/workout 45` — з тривалістю\n`/workout 45 \"Upper body\"` — з нотатками",
        "parse_mode": "Markdown",
        "reply_markup": json.dumps({
            "inline_keyboard": [[{"text": "🍽️ Лог їжі", "callback_data": "action:log"}, {"text": "💧 Вода", "callback_data": "action:water"}]],
        }),
    }


def _handle_inline_week(chat_id: int, message_id: int, cq_id: str) -> dict:
    """Show week stats (same as /week)."""
    result = _handle_week(chat_id)
    result["method"] = "editMessageText"
    result["chat_id"] = chat_id
    result["message_id"] = message_id
    return result


def _handle_inline_progress(chat_id: int, message_id: int, cq_id: str) -> dict:
    """Show progress (same as /progress)."""
    result = _handle_progress(chat_id)
    result["method"] = "editMessageText"
    result["chat_id"] = chat_id
    result["message_id"] = message_id
    return result


