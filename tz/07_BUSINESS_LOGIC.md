# Бізнес-логіка

## 1. Progressive Overload — Алгоритм прогресії

### Принцип
Прогресія — детерміністична (алгоритм), AI — як supervisor для edge cases.

### Дані для рішення
Для кожної вправи аналізуємо:
- `last_3_sessions`: вага, повтори, RPE за останні 3 тренування
- `weeks_at_current_weight`: скільки тижнів на поточній вазі
- `target_reps_min`, `target_reps_max`: цільовий діапазон повторів
- `weight_increment`: стандартний крок збільшення (2.5кг верх тіла, 5кг ноги)

### Дерево рішень

```python
def decide_progression(exercise_data):
    last = exercise_data['last_session']
    avg_rpe = last['avg_rpe']  # або rpe_simple → числове значення
    all_sets_in_range = last['all_sets_hit_target']
    reps_max_hit = last['all_sets_hit_max_reps']  # всі підходи на верхній межі
    weeks_stuck = exercise_data['weeks_at_current_weight']
    
    # RPE mapping для простого режиму
    # easy = 5, moderate = 7, hard = 8.5, max = 10
    
    # Правило 1: Всі підходи на максимальних повторах, RPE ≤ 8
    # → Збільшити вагу
    if reps_max_hit and avg_rpe <= 8:
        return Decision(
            action="increase_weight",
            new_weight=last['weight'] + exercise_data['weight_increment'],
            new_reps_target="reset to min",  # повертаємось до нижньої межі повторів
            reason=f"Всі підходи на {last['reps_max']} повторів з RPE {avg_rpe}. Час збільшувати!"
        )
    
    # Правило 2: Всі підходи в діапазоні, RPE 7-8
    # → Збільшити повтори (залишити вагу)
    if all_sets_in_range and 7 <= avg_rpe <= 8:
        return Decision(
            action="increase_reps",
            new_weight=last['weight'],  # та сама вага
            reason="Хороший прогрес! Спробуй додати 1 повтор до кожного підходу"
        )
    
    # Правило 3: RPE 9-10, не всі повтори виконані
    # → Зберегти вагу, дати ще тиждень
    if avg_rpe >= 9 and not all_sets_in_range:
        if weeks_stuck >= 3:
            # Стагнація — потрібна зміна
            return Decision(
                action="change_strategy",
                reason="3 тижні без прогресу. Варіанти: змінити варіацію, додати підходи, або зменшити вагу на 10% і прогресувати знову",
                requires_ai=True  # AI вирішує що саме змінити
            )
        return Decision(
            action="maintain",
            new_weight=last['weight'],
            reason="Тримаємо поточну вагу, працюємо над повторами"
        )
    
    # Правило 4: RPE 10 два тижні поспіль + біль в журналі
    # → Зменшити або замінити
    if avg_rpe >= 9.5 and has_related_pain(exercise_data):
        return Decision(
            action="decrease_or_replace",
            reason="Високий RPE + записи болю. Потрібно адаптувати",
            requires_ai=True
        )
    
    # Правило 5: Deload тиждень
    if exercise_data['is_deload_week']:
        return Decision(
            action="deload",
            new_weight=last['weight'] * 0.6,  # 60% від робочої ваги
            new_sets=last['sets'] - 1,  # на 1 підхід менше
            reason="Deload тиждень — знижуємо навантаження для відновлення"
        )
    
    # Default: зберегти
    return Decision(action="maintain", reason="Продовжуємо в поточному режимі")
```

### Коли AI override

AI перевіряє рішення алгоритму і може перевизначити:
- Є записи в pain journal для цієї зони тіла
- Юзер в лютеальній фазі → не збільшувати вагу
- Чекін показує низьку енергію / поганий сон 3+ дні
- Стагнація 3+ тижні → AI пропонує зміну стратегії

---

## 2. Адаптація під менструальний цикл

### Автоматичний розрахунок

```python
def calculate_cycle_info(user):
    if not user.cycle_tracking_enabled:
        return None
    
    last_start = parse_date(user.cycle_last_start_date)
    today = date.today()
    cycle_day = (today - last_start).days + 1
    
    # Якщо перевищує середню довжину — можливо новий цикл
    if cycle_day > user.cycle_average_length + 5:
        return CycleInfo(
            day=cycle_day,
            phase="unknown",
            alert="Цикл довший за звичайний. Оновити дату початку?"
        )
    
    # Визначення фази (стандартна модель для 28-денного циклу, масштабується)
    ratio = cycle_day / user.cycle_average_length
    
    if ratio <= 0.18:  # день 1-5 (для 28 днів)
        phase = "menstrual"
    elif ratio <= 0.50:  # день 6-14
        phase = "follicular"
    elif ratio <= 0.57:  # день 14-16
        phase = "ovulation"
    else:  # день 16-28
        phase = "luteal"
    
    return CycleInfo(day=cycle_day, phase=phase)
```

### Правила адаптації

```python
CYCLE_ADAPTATIONS = {
    "menstrual": {
        "intensity_modifier": 1.0,    # за самопочуттям, не обмежуємо автоматично
        "volume_modifier": 1.0,
        "notes": "Тренуйся за самопочуттям. Багато жінок відчувають себе нормально.",
        "alert_if_checkin_below": 4,   # якщо енергія < 4, пропонуємо полегшити
    },
    "follicular": {
        "intensity_modifier": 1.0,     # повна інтенсивність
        "volume_modifier": 1.0,
        "notes": "Найкращий час для важких тренувань і нових рекордів!",
        "can_attempt_pr": True,
    },
    "ovulation": {
        "intensity_modifier": 0.95,
        "volume_modifier": 1.0,
        "notes": "Увага до суглобів — підвищена лаксичність зв'язок. Контролюй техніку.",
        "extra_warmup": True,
        "avoid_plyometrics": True,      # стрибкові вправи — ризик для зв'язок
    },
    "luteal": {
        "intensity_modifier": 0.85,     # зменшити ваги на 10-15%
        "volume_modifier": 0.85,        # зменшити об'єм на 15%
        "rest_modifier": 1.2,           # подовжити відпочинок на 20%
        "notes": "Знижена працездатність — це нормально. Зменшуємо навантаження.",
        "can_attempt_pr": False,
        "prefer_moderate_intensity": True,
    }
}
```

### Застосування

```python
def adapt_workout(user, program_day, checkin, cycle_info):
    adaptations = []
    
    # 1. Адаптація під цикл
    if cycle_info and cycle_info.phase in CYCLE_ADAPTATIONS:
        cycle_rules = CYCLE_ADAPTATIONS[cycle_info.phase]
        if cycle_rules['intensity_modifier'] < 1.0:
            for ex in program_day.exercises:
                ex.weight_suggestion *= cycle_rules['intensity_modifier']
            adaptations.append({
                "type": "cycle",
                "phase": cycle_info.phase,
                "change": f"Ваги зменшені на {(1-cycle_rules['intensity_modifier'])*100:.0f}%",
                "reason": cycle_rules['notes']
            })
    
    # 2. Адаптація під чекін
    if checkin:
        if checkin.energy_level <= 3:
            # Дуже низька енергія — пропонуємо легке тренування або відпочинок
            adaptations.append({
                "type": "energy",
                "change": "Пропоную легке тренування або відпочинок",
                "severity": "high"
            })
        elif checkin.energy_level <= 5:
            # Середня — зменшити
            for ex in program_day.exercises:
                if ex.is_optional:
                    ex.skipped = True
            adaptations.append({
                "type": "energy",
                "change": "Прибрані опціональні вправи",
                "severity": "medium"
            })
        
        if checkin.sleep_hours and checkin.sleep_hours < 5:
            adaptations.append({
                "type": "sleep",
                "change": "Менше 5 годин сну — зменшуємо інтенсивність",
                "severity": "high"
            })
        
        if checkin.muscle_soreness >= 8:
            adaptations.append({
                "type": "soreness",
                "change": "Сильна крепатура — збільшимо відпочинок між підходами",
                "severity": "medium"
            })
    
    # 3. Адаптація під біль
    recent_pain = get_recent_pain(user.id, days=7)
    for pain_entry in recent_pain:
        affected_exercises = find_exercises_by_contraindication(pain_entry.body_area, program_day)
        for ex in affected_exercises:
            adaptations.append({
                "type": "pain",
                "exercise": ex.name,
                "change": "Замінити або модифікувати через біль",
                "requires_ai": True
            })
    
    return adaptations
```

---

## 3. Deload Logic

### Коли deload

```python
def should_deload(user_id):
    workouts = get_workouts_since_last_deload(user_id)
    weeks = count_training_weeks(workouts)
    
    # Правило 1: кожні 4-6 тижнів (залежить від рівня)
    max_weeks = {
        'beginner': 6,       # новачки відновлюються швидше
        'intermediate': 5,
        'advanced': 4,        # досвідчені потребують частіше
    }
    user = get_user(user_id)
    if weeks >= max_weeks.get(user.experience_level, 5):
        return True, "Час для deload тижня — ти тренувалась {weeks} тижнів без перерви"
    
    # Правило 2: стагнація на 60%+ вправ
    stagnating = count_stagnating_exercises(user_id, weeks=3)
    total = count_active_exercises(user_id)
    if stagnating / total > 0.6:
        return True, "Більшість вправ стагнує — організм просить відпочинку"
    
    # Правило 3: хронічно поганий чекін
    bad_checkins = count_checkins_below_threshold(user_id, days=7, threshold=4)
    if bad_checkins >= 5:  # 5 з 7 днів погане самопочуття
        return True, "Поганий стан 5 з 7 днів — потрібен deload"
    
    return False, None
```

### Deload протокол

```python
DELOAD_PROTOCOL = {
    "volume_reduction": 0.5,      # 50% від звичайного об'єму (менше підходів)
    "intensity_reduction": 0.0,   # НЕ зменшуємо вагу (зберігаємо нейром'язову адаптацію)
    "sets_multiplier": 0.5,       # 2 підходи замість 4
    "reps_keep": True,            # повтори ті самі
    "duration_days": 7,           # один тиждень
    "notes": "Зменшуємо підходи вдвічі, ваги залишаємо. Фокус на техніці і відновленні."
}
```

---

## 4. Weekly Volume Tracking

### Оптимальний об'єм (серій на тиждень по м'язових групах)

```python
OPTIMAL_WEEKLY_VOLUME = {
    # muscle_group: (min_sets, max_sets) per week
    "chest":        (10, 20),
    "back":         (10, 20),
    "shoulders":    (10, 20),   # рахуючи непряму роботу від жимів
    "quads":        (10, 20),
    "hamstrings":   (10, 16),
    "glutes":       (10, 20),
    "biceps":       (8, 16),    # включаючи непряму роботу від тяг
    "triceps":      (8, 16),    # включаючи непряму роботу від жимів
    "calves":       (8, 16),
    "abs":          (6, 14),
    "traps":        (6, 12),
    "forearms":     (4, 10),
}

# Для початківців: нижня межа
# Для досвідчених: верхня межа
# Responsive volume: збільшувати на 1-2 серії на тиждень якщо прогрес є
```

### Підрахунок

```python
def calculate_weekly_volume(user_id, week_start, week_end):
    logs = get_exercise_logs_for_period(user_id, week_start, week_end)
    
    volume = {}  # muscle_group: sets count
    
    for log in logs:
        if log.set_type != 'working':  # не рахуємо розминкові
            continue
        exercise = get_exercise(log.exercise_id)
        
        # Primary muscles — рахуємо повну серію
        for muscle in exercise.primary_muscles:
            volume[muscle] = volume.get(muscle, 0) + 1
        
        # Secondary muscles — рахуємо 0.5 серії (непряма робота)
        for muscle in exercise.secondary_muscles:
            volume[muscle] = volume.get(muscle, 0) + 0.5
    
    # Оцінка
    assessment = {}
    for muscle, sets in volume.items():
        optimal = OPTIMAL_WEEKLY_VOLUME.get(muscle, (10, 20))
        if sets < optimal[0]:
            status = "below_optimal"
        elif sets > optimal[1]:
            status = "above_optimal"  # ризик overtrain
        else:
            status = "optimal"
        assessment[muscle] = {"sets": sets, "range": optimal, "status": status}
    
    return assessment
```

---

## 5. AI Feedback Generation

### Після тренування

```python
def generate_post_workout_feedback(workout_log, user):
    context = {
        "user_profile": user.to_dict(),
        "workout": workout_log.to_dict(),
        "exercise_logs": get_exercise_logs(workout_log.id),
        "previous_same_day": get_previous_workout_for_day(user.id, workout_log.program_day_id),
        "personal_records": detect_prs(workout_log),
        "progressive_overload_decisions": get_overload_decisions(workout_log),
    }
    
    prompt = f"""
    Дай короткий фідбек після тренування (3-5 речень максимум).
    
    Обов'язково згадай:
    - Якщо є нові рекорди (PR) — святкуй!
    - Якщо є прогрес порівняно з минулим тижнем — відміть
    - Якщо є проблеми (пропущені вправи, високий RPE) — прокоментуй конструктивно
    - Що планується далі (рекомендації на наступне тренування)
    
    НЕ роби:
    - Довгих лекцій
    - Generic мотиваційних фраз
    - Списків (відповідай текстом)
    
    Дані тренування: {json.dumps(context, ensure_ascii=False)}
    """
    
    return call_claude(base_prompt + training_module_prompt, prompt, context)
```

### Тижневий ревю

```python
def generate_weekly_review(user_id):
    week_data = {
        "workouts": get_workouts_this_week(user_id),
        "checkins": get_checkins_this_week(user_id),
        "pain_entries": get_pain_this_week(user_id),
        "volume_analysis": calculate_weekly_volume(user_id, ...),
        "exercise_trends": get_exercise_trends(user_id, weeks=4),
        "overload_log": get_overload_decisions_this_week(user_id),
        "measurements": get_latest_measurements(user_id),
    }
    
    prompt = f"""
    Зроби тижневий ревю для юзера. Структура:
    
    1. Загальна оцінка тижня (1-2 речення)
    2. Прогрес: які вправи зросли, де нові рекорди
    3. Увага: що потребує корекції (об'єм, біль, стагнація)
    4. План на наступний тиждень: конкретні рекомендації
    
    Тримай коротко — максимум 10 речень.
    
    Дані: {json.dumps(week_data, ensure_ascii=False)}
    """
    
    return call_claude(base_prompt + training_module_prompt, prompt)
```

---

## 6. Smart Rest Timer

```python
def recommended_rest(exercise, set_rpe, exercise_type):
    base_rest = {
        "compound": {
            "strength": 180,    # 3 хвилини для силових compound
            "hypertrophy": 120, # 2 хвилини для гіпертрофії compound
        },
        "isolation": {
            "hypertrophy": 60,  # 1 хвилина для ізоляції
        },
        "cardio": {"default": 30},
        "mobility": {"default": 15},
    }
    
    rest = base_rest.get(exercise.category, {}).get("hypertrophy", 90)
    
    # Корекція по RPE
    if set_rpe >= 9:
        rest *= 1.3  # +30% якщо дуже важко
    elif set_rpe <= 5:
        rest *= 0.8  # -20% якщо легко
    
    return int(rest)
```

---

## 7. Формули

### TDEE (Total Daily Energy Expenditure)

```python
def calculate_tdee(user):
    # Mifflin-St Jeor (найточніша для загальної популяції)
    if user.gender == 'male':
        bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age + 5
    else:
        bmr = 10 * user.weight_kg + 6.25 * user.height_cm - 5 * user.age - 161
    
    # Activity multiplier
    multipliers = {
        2: 1.375,  # 2 тренування на тиждень
        3: 1.465,
        4: 1.55,
        5: 1.635,
        6: 1.725,
    }
    
    tdee = bmr * multipliers.get(user.training_days_per_week, 1.55)
    return round(tdee)
```

### Macros

```python
def calculate_macros(user, tdee):
    goal_adjustments = {
        'muscle_gain': 300,       # профіцит 300 ккал
        'fat_loss': -400,         # дефіцит 400 ккал
        'recomposition': 0,       # підтримка
        'strength': 200,          # невеликий профіцит
        'health': 0,
    }
    
    target_calories = tdee + goal_adjustments.get(user.primary_goal, 0)
    
    # Protein: 1.8-2.2г на кг (gold standard для гіпертрофії)
    protein_g = round(user.weight_kg * 2.0)
    protein_kcal = protein_g * 4
    
    # Fat: 25-30% калорій (мінімум для гормональної функції)
    fat_kcal = target_calories * 0.28
    fat_g = round(fat_kcal / 9)
    
    # Carbs: решта
    carbs_kcal = target_calories - protein_kcal - fat_kcal
    carbs_g = round(carbs_kcal / 4)
    
    return {
        "calories": target_calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
    }
```
