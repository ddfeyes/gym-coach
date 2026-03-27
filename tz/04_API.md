# API Endpoints

## Загальні правила

- Base URL: `/api/v1`
- Авторизація: Telegram Init Data (валідація hash)
- Формат: JSON
- Помилки: `{"error": "message", "code": "ERROR_CODE"}`
- Пагінація: `?page=1&per_page=20`
- Дати: ISO 8601 (`2026-03-27`)

---

## Auth & User

### POST /api/v1/auth/telegram
Валідація Telegram WebApp initData і створення/отримання юзера.

**Request:**
```json
{
  "init_data": "query_string_from_telegram_webapp"
}
```

**Response 200:**
```json
{
  "user_id": 1,
  "telegram_id": 123456789,
  "onboarding_completed": false,
  "token": "session_token"
}
```

### GET /api/v1/user/profile
Отримати профіль юзера.

**Response 200:**
```json
{
  "id": 1,
  "name": "Наталя",
  "gender": "female",
  "age": 28,
  "height_cm": 168,
  "weight_kg": 62,
  "experience_level": "intermediate",
  "training_days_per_week": 4,
  "session_duration_minutes": 60,
  "gym_type": "full_gym",
  "available_equipment": ["barbell", "dumbbells", "machines", "cables"],
  "injuries": [
    {"area": "right_shoulder", "description": "Іноді болить при жимі над головою", "severity": "mild", "is_current": true}
  ],
  "primary_goal": "muscle_gain",
  "secondary_goals": ["posture", "energy"],
  "cycle_tracking_enabled": true,
  "cycle_average_length": 28,
  "cycle_last_start_date": "2026-03-10",
  "onboarding_completed": true
}
```

### PUT /api/v1/user/profile
Оновити профіль (часткове оновлення).

**Request:**
```json
{
  "weight_kg": 63,
  "training_days_per_week": 5
}
```

### POST /api/v1/user/onboarding
Зберегти крок онбордингу.

**Request:**
```json
{
  "step": 3,
  "data": {
    "gym_type": "full_gym",
    "available_equipment": ["barbell", "dumbbells", "machines", "cables"]
  }
}
```

### POST /api/v1/user/onboarding/complete
Фіналізувати онбординг і запустити генерацію програми.

**Response 200:**
```json
{
  "status": "generating",
  "message": "Створюю твою програму..."
}
```

---

## Training Programs

### GET /api/v1/training/program/current
Отримати активну програму з усіма днями і вправами.

**Response 200:**
```json
{
  "id": 1,
  "name": "Hypertrophy Block 1",
  "type": "hypertrophy",
  "split_type": "push_pull_legs",
  "current_week": 3,
  "weeks_planned": 5,
  "status": "active",
  "days": [
    {
      "id": 1,
      "day_number": 1,
      "name": "Push",
      "focus_muscles": ["chest", "shoulders", "triceps"],
      "estimated_duration_min": 60,
      "last_completed": "2026-03-25",
      "exercises": [
        {
          "id": 1,
          "exercise_id": 10,
          "name": "Жим штанги лежачи",
          "sets_planned": 4,
          "reps_min": 8,
          "reps_max": 10,
          "rest_seconds": 120,
          "tempo": "3-1-2-0",
          "weight_suggestion_kg": 40,
          "last_performance": {
            "weight_kg": 37.5,
            "reps": [10, 10, 9, 8],
            "avg_rpe": 7.5
          },
          "notes": "Фокус на контролі ексцентрики",
          "is_optional": false
        }
      ]
    }
  ]
}
```

### POST /api/v1/training/program/generate
Згенерувати нову програму через AI.

**Request:**
```json
{
  "reason": "new_block",
  "preferences": "Хочу більше фокусу на сідниці і спину"
}
```

**Response 200:**
```json
{
  "status": "generating",
  "estimated_seconds": 15
}
```

### GET /api/v1/training/program/generate/status
Перевірити статус генерації.

**Response 200:**
```json
{
  "status": "ready",
  "program_id": 2
}
```

### POST /api/v1/training/program/{id}/accept
Прийняти згенеровану програму (зробити активною).

### POST /api/v1/training/exercise/replace
Замінити вправу в програмі.

**Request:**
```json
{
  "program_exercise_id": 5,
  "reason": "equipment_busy",
  "permanent": false
}
```

**Response 200:**
```json
{
  "alternatives": [
    {"exercise_id": 15, "name": "Жим гантелей лежачи", "reason": "Найближчий аналог по паттерну руху"},
    {"exercise_id": 22, "name": "Жим в Хаммері", "reason": "Менше навантаження на стабілізатори"},
    {"exercise_id": 18, "name": "Жим в Смітті", "reason": "Якщо потрібна максимальна стабільність"}
  ]
}
```

### POST /api/v1/training/exercise/replace/confirm
Підтвердити заміну.

**Request:**
```json
{
  "program_exercise_id": 5,
  "new_exercise_id": 15,
  "permanent": false
}
```

---

## Workout Execution

### POST /api/v1/workout/start
Почати тренування.

**Request:**
```json
{
  "program_day_id": 1
}
```

**Response 200:**
```json
{
  "workout_log_id": 42,
  "needs_checkin": true,
  "program_day": { ... },
  "ai_adaptation": null
}
```

**Response 200 (з адаптацією):**
```json
{
  "workout_log_id": 42,
  "needs_checkin": false,
  "program_day": { ... },
  "ai_adaptation": {
    "type": "reduced_intensity",
    "reason": "Енергія 3/10, лютеальна фаза",
    "message": "Пропоную зменшити ваги на 15% і прибрати останню ізоляцію",
    "changes": [
      {"program_exercise_id": 1, "new_weight_suggestion_kg": 34, "change": "weight_reduced"},
      {"program_exercise_id": 6, "change": "removed", "reason": "optional_low_energy"}
    ]
  }
}
```

### POST /api/v1/workout/{id}/log-set
Залогати один підхід.

**Request:**
```json
{
  "program_exercise_id": 1,
  "exercise_id": 10,
  "set_number": 1,
  "weight_kg": 40,
  "reps_done": 10,
  "rpe": 7,
  "rpe_simple": "moderate",
  "set_type": "working",
  "notes": null
}
```

**Response 200:**
```json
{
  "exercise_log_id": 156,
  "was_target_hit": true,
  "rest_recommendation_seconds": 120,
  "ai_note": null
}
```

**Response 200 (з AI попередженням):**
```json
{
  "exercise_log_id": 157,
  "was_target_hit": false,
  "rest_recommendation_seconds": 180,
  "ai_note": "RPE 10 другий підхід поспіль. Зменши вагу на 5кг для наступних підходів?"
}
```

### POST /api/v1/workout/{id}/skip-exercise
Пропустити вправу.

**Request:**
```json
{
  "program_exercise_id": 3,
  "reason": "pain",
  "pain_entry": {
    "body_area": "right_shoulder",
    "side": "right",
    "pain_type": "sharp",
    "intensity": 6
  }
}
```

### POST /api/v1/workout/{id}/finish
Завершити тренування.

**Request:**
```json
{
  "overall_feeling": 8,
  "notes": "Хороше тренування, жим пішов легше"
}
```

**Response 200:**
```json
{
  "workout_log_id": 42,
  "summary": {
    "duration_minutes": 58,
    "exercises_completed": 6,
    "exercises_total": 6,
    "total_volume_kg": 12450,
    "volume_vs_last_week": "+5%",
    "personal_records": [
      {"exercise": "Жим штанги лежачи", "type": "weight", "value": "40кг", "previous": "37.5кг"}
    ]
  },
  "ai_feedback": "Відмінне тренування! Новий рекорд на жимі — 40кг! На наступному тренуванні спробуємо утримати цю вагу на всі 4 підходи. Присідання стабільні, ще тиждень і підвищимо.",
  "progressive_overload_suggestions": [
    {"exercise": "Жим штанги лежачи", "suggestion": "Утримати 40кг, ціль 4×10"},
    {"exercise": "Розведення гантелей", "suggestion": "Збільшити до 10кг (+2кг)"}
  ]
}
```

### GET /api/v1/workout/history
Історія тренувань.

**Query params:** `?page=1&per_page=20&from=2026-01-01&to=2026-03-27`

---

## Daily Checkins

### POST /api/v1/checkin
Зберегти щоденний чекін.

**Request:**
```json
{
  "sleep_quality": 7,
  "sleep_hours": 7.5,
  "energy_level": 6,
  "stress_level": 4,
  "muscle_soreness": 5,
  "mood": 7,
  "weight_morning_kg": 62.3,
  "cycle_day": 18,
  "notes": ""
}
```

**Response 200:**
```json
{
  "id": 100,
  "cycle_phase": "luteal",
  "ai_note": null
}
```

### GET /api/v1/checkin/today
Перевірити чи є чекін сьогодні.

**Response 200:**
```json
{
  "exists": true,
  "checkin": { ... }
}
```

**Response 200 (нема):**
```json
{
  "exists": false
}
```

### GET /api/v1/checkin/history
Історія чекінів.

**Query params:** `?days=30`

---

## Pain Journal

### POST /api/v1/pain
Записати біль.

### GET /api/v1/pain/history
Історія болю.

**Query params:** `?body_area=right_shoulder&days=90`

### GET /api/v1/pain/analysis
AI-аналіз патернів болю.

**Response 200:**
```json
{
  "patterns": [
    {
      "body_area": "right_shoulder",
      "occurrences": 5,
      "avg_intensity": 5.4,
      "trend": "stable",
      "related_exercises": ["Жим штанги лежачи", "Жим над головою"],
      "ai_recommendation": "Систематичний дискомфорт правого плеча при жимових рухах. Рекомендую: 1) Замінити жим штанги на жим гантелями нейтральним хватом 2) Додати зовнішню ротацію з гумкою в розминку 3) Тимчасово прибрати жим над головою. Якщо не покращиться за 2 тижні — зверніся до ортопеда."
    }
  ]
}
```

---

## Body Measurements

### POST /api/v1/measurements
Записати виміри.

### GET /api/v1/measurements/history
Історія вимірів з трендами.

### GET /api/v1/measurements/comparison
Порівняння двох дат.

---

## Exercises Library

### GET /api/v1/exercises
Список вправ з фільтрацією.

**Query params:** `?category=compound&muscles=chest&equipment=barbell&search=жим`

### GET /api/v1/exercises/{id}
Детальна інфо про вправу.

---

## AI Chat

### POST /api/v1/chat/message
Відправити повідомлення агенту.

**Request:**
```json
{
  "message": "Як правильно робити румунську тягу?",
  "conversation_id": null,
  "module": "training"
}
```

**Response 200:**
```json
{
  "conversation_id": 15,
  "response": "Румунська тяга — одна з найкращих вправ для задньої поверхні стегна і сідниць. Ось ключові моменти техніки...",
  "module_used": "training_technique"
}
```

### GET /api/v1/chat/conversations
Список розмов.

### GET /api/v1/chat/conversation/{id}
Конкретна розмова з історією.

---

## Analytics (Фаза 6)

### GET /api/v1/analytics/weekly
Тижневий звіт.

### GET /api/v1/analytics/monthly
Місячний звіт.

### GET /api/v1/analytics/exercise/{id}/progress
Прогрес конкретної вправи.

**Response 200:**
```json
{
  "exercise": "Жим штанги лежачи",
  "history": [
    {"date": "2026-02-01", "weight_kg": 30, "best_reps": 10, "avg_rpe": 6},
    {"date": "2026-02-08", "weight_kg": 32.5, "best_reps": 9, "avg_rpe": 7},
    {"date": "2026-02-15", "weight_kg": 35, "best_reps": 8, "avg_rpe": 8}
  ],
  "total_progress": "+10кг (+33%)",
  "weeks_tracked": 8
}
```

### GET /api/v1/analytics/volume
Тижневий об'єм по м'язових групах.

**Response 200:**
```json
{
  "week": "2026-03-23",
  "muscle_groups": {
    "chest": {"sets": 16, "optimal_range": "10-20", "status": "optimal"},
    "back": {"sets": 18, "optimal_range": "10-20", "status": "optimal"},
    "shoulders": {"sets": 12, "optimal_range": "10-20", "status": "optimal"},
    "quads": {"sets": 8, "optimal_range": "10-20", "status": "below_optimal"},
    "hamstrings": {"sets": 10, "optimal_range": "10-20", "status": "optimal"},
    "glutes": {"sets": 12, "optimal_range": "10-20", "status": "optimal"},
    "biceps": {"sets": 10, "optimal_range": "8-16", "status": "optimal"},
    "triceps": {"sets": 12, "optimal_range": "8-16", "status": "optimal"}
  }
}
```

---

## Notifications (Bot)

### POST /api/v1/notifications/settings
Налаштувати нотифікації.

**Request:**
```json
{
  "checkin_reminder": true,
  "checkin_time": "08:00",
  "training_reminder": true,
  "training_reminder_hours_before": 2,
  "measurement_reminder": true,
  "measurement_frequency_days": 14
}
```

---

## Webhook (Telegram Bot)

### POST /webhook/telegram
Приймає оновлення від Telegram.

Обробляє:
- `/start` — привітання + кнопка Mini App
- `/checkin` — швидкий чекін через бота
- `/today` — що на сьогодні (тренування, прийом їжі)
- `/stats` — швидка статистика
- Текстові повідомлення → AI chat
- Фото → аналіз техніки (Фаза 5) або їжі (Фаза 3)
