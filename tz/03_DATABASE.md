# Схема бази даних

## Загальні правила

- Усі таблиці мають `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- Усі таблиці мають `created_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
- JSON поля зберігаються як TEXT у SQLite, парсяться на рівні Python
- Foreign keys увімкнені: `PRAGMA foreign_keys = ON`
- Soft delete де потрібно: `deleted_at` (TIMESTAMP NULL)

---

## Спільні таблиці (Фундамент)

### users

Центральна таблиця. Шариться між усіма модулями.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,                          -- Telegram username
    name TEXT NOT NULL,
    gender TEXT NOT NULL CHECK(gender IN ('female', 'male')),
    age INTEGER NOT NULL CHECK(age BETWEEN 14 AND 80),
    height_cm REAL NOT NULL CHECK(height_cm BETWEEN 100 AND 250),
    weight_kg REAL NOT NULL CHECK(weight_kg BETWEEN 30 AND 300),
    
    -- Training profile
    experience_level TEXT NOT NULL CHECK(experience_level IN ('beginner', 'intermediate', 'advanced')),
    training_days_per_week INTEGER NOT NULL CHECK(training_days_per_week BETWEEN 2 AND 6),
    session_duration_minutes INTEGER DEFAULT 60,
    available_equipment TEXT NOT NULL DEFAULT '[]',   -- JSON: ["barbell","dumbbells","machines","cables","pullup_bar","dip_bars","bands","trx"]
    gym_type TEXT DEFAULT 'full_gym' CHECK(gym_type IN ('full_gym', 'home_gym', 'dumbbells_only', 'bodyweight')),
    
    -- Health
    injuries TEXT DEFAULT '[]',             -- JSON: [{"area":"right_shoulder","description":"impingement","severity":"moderate","is_current":true}]
    exercise_restrictions TEXT DEFAULT '[]', -- JSON: ["overhead_press","behind_neck"]
    medical_notes TEXT,
    
    -- Goals
    primary_goal TEXT NOT NULL CHECK(primary_goal IN ('muscle_gain', 'fat_loss', 'strength', 'health', 'recomposition')),
    secondary_goals TEXT DEFAULT '[]',      -- JSON: ["posture","energy","flexibility","pain_reduction"]
    
    -- Menstrual cycle (nullable — not everyone tracks)
    cycle_tracking_enabled INTEGER DEFAULT 0,
    cycle_average_length INTEGER DEFAULT 28,
    cycle_last_start_date TEXT,             -- ISO date: "2026-03-15"
    
    -- Nutrition profile (Фаза 3)
    allergies TEXT DEFAULT '[]',            -- JSON: ["gluten","lactose"]
    diet_type TEXT DEFAULT 'omnivore',      -- omnivore, vegetarian, vegan, pescatarian, keto
    budget_level TEXT DEFAULT 'medium',     -- low, medium, high
    
    -- Settings
    language TEXT DEFAULT 'uk',             -- uk, ru, en
    timezone TEXT DEFAULT 'Europe/Lisbon',
    checkin_reminder_time TEXT DEFAULT '08:00',
    notifications_enabled INTEGER DEFAULT 1,
    
    -- System
    onboarding_completed INTEGER DEFAULT 0,
    onboarding_step INTEGER DEFAULT 0,     -- для збереження прогресу онбордингу
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### daily_checkins

Щоденний стан юзера. Використовується всіма модулями.

```sql
CREATE TABLE daily_checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,                     -- ISO date: "2026-03-27"
    
    sleep_quality INTEGER CHECK(sleep_quality BETWEEN 1 AND 10),
    sleep_hours REAL,
    energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),
    stress_level INTEGER CHECK(stress_level BETWEEN 1 AND 10),
    muscle_soreness INTEGER CHECK(muscle_soreness BETWEEN 1 AND 10),
    mood INTEGER CHECK(mood BETWEEN 1 AND 10),
    
    weight_morning_kg REAL,
    
    -- Cycle
    cycle_day INTEGER,                      -- auto-calculated, manual override
    cycle_phase TEXT CHECK(cycle_phase IN ('menstrual', 'follicular', 'ovulation', 'luteal')),
    cycle_override INTEGER DEFAULT 0,       -- 1 якщо юзер скоригувала вручну
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, date)
);
```

### pain_journal

Трекінг болю і дискомфорту.

```sql
CREATE TABLE pain_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,
    
    body_area TEXT NOT NULL,                -- shoulder, knee, lower_back, upper_back, hip, elbow, wrist, ankle, neck, other
    side TEXT DEFAULT 'center' CHECK(side IN ('left', 'right', 'both', 'center')),
    pain_type TEXT NOT NULL CHECK(pain_type IN ('sharp', 'dull', 'aching', 'burning', 'tingling', 'stiffness')),
    intensity INTEGER NOT NULL CHECK(intensity BETWEEN 1 AND 10),
    
    when_occurs TEXT DEFAULT '[]',          -- JSON: ["during_exercise","after_training","morning","constant","specific_movement"]
    related_exercise_id INTEGER REFERENCES exercises(id),
    related_workout_log_id INTEGER REFERENCES workout_logs(id),
    
    notes TEXT,
    ai_recommendation TEXT,                 -- AI відповідь на цей запис
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### body_measurements

Обхвати тіла і фото прогресу.

```sql
CREATE TABLE body_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,
    
    weight_kg REAL,
    body_fat_pct REAL,                      -- опціонально, якщо є каліпер або DEXA
    
    chest_cm REAL,
    waist_cm REAL,
    hips_cm REAL,
    left_arm_cm REAL,
    right_arm_cm REAL,
    left_thigh_cm REAL,
    right_thigh_cm REAL,
    left_calf_cm REAL,
    right_calf_cm REAL,
    
    photo_front_path TEXT,
    photo_side_path TEXT,
    photo_back_path TEXT,
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ai_conversations

Історія чатів з AI.

```sql
CREATE TABLE ai_conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    module TEXT NOT NULL DEFAULT 'general',  -- training, nutrition, sleep, technique, psychology, general
    
    messages TEXT NOT NULL DEFAULT '[]',     -- JSON: [{"role":"user","content":"...","timestamp":"..."},{"role":"assistant","content":"...","timestamp":"..."}]
    
    -- Metadata
    tokens_used INTEGER DEFAULT 0,
    model_used TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Training Module (Фаза 1-2)

### exercises

Бібліотека всіх вправ. Read-mostly, заповнюється на старті.

```sql
CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    name_uk TEXT NOT NULL,                  -- "Жим штанги лежачи"
    name_en TEXT NOT NULL,                  -- "Barbell Bench Press"
    name_ru TEXT,                           -- "Жим штанги лежа"
    
    category TEXT NOT NULL CHECK(category IN ('compound', 'isolation', 'cardio', 'mobility', 'warmup')),
    movement_pattern TEXT,                   -- push, pull, hinge, squat, carry, rotation, lunge
    
    primary_muscles TEXT NOT NULL DEFAULT '[]',    -- JSON: ["chest","front_delt"]
    secondary_muscles TEXT DEFAULT '[]',            -- JSON: ["triceps","serratus"]
    
    equipment_needed TEXT DEFAULT '[]',      -- JSON: ["barbell","bench"]
    min_equipment TEXT DEFAULT 'barbell',     -- мінімально необхідне обладнання
    
    difficulty_level TEXT DEFAULT 'intermediate' CHECK(difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    
    description TEXT,                        -- Як виконувати
    setup TEXT,                              -- Як зайняти вихідне положення
    cues TEXT DEFAULT '[]',                  -- JSON: ["Лопатки зведені","Стопи на підлозі","Штанга над очима"]
    common_mistakes TEXT DEFAULT '[]',       -- JSON: ["Відрив сідниць від лавки","Занадто широкий хват"]
    breathing TEXT,                           -- "Вдих на опусканні, видих на жимі"
    
    contraindications TEXT DEFAULT '[]',     -- JSON: ["shoulder_impingement","rotator_cuff_tear","lower_back_injury"]
    alternatives TEXT DEFAULT '[]',          -- JSON: [exercise_ids] — вправи-замінники
    
    -- Для progressive overload
    default_rest_seconds INTEGER DEFAULT 120,
    typical_rep_range_min INTEGER DEFAULT 8,
    typical_rep_range_max INTEGER DEFAULT 12,
    weight_increment_kg REAL DEFAULT 2.5,    -- стандартний крок збільшення
    
    video_url TEXT,                           -- Посилання на відео техніки
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### training_programs

Тренувальна програма юзера. Один юзер = одна активна програма.

```sql
CREATE TABLE training_programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    name TEXT NOT NULL,                     -- "Hypertrophy Block 1"
    description TEXT,
    
    type TEXT NOT NULL DEFAULT 'hypertrophy' CHECK(type IN ('hypertrophy', 'strength', 'powerbuilding', 'deload', 'recovery', 'home', 'travel')),
    split_type TEXT,                         -- push_pull_legs, upper_lower, full_body, bro_split
    
    periodization TEXT DEFAULT 'linear',     -- linear, undulating, block
    phase TEXT DEFAULT 'accumulation',       -- accumulation, intensification, peaking, deload
    
    weeks_planned INTEGER DEFAULT 5,         -- 4 робочих + 1 deload
    current_week INTEGER DEFAULT 1,
    
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'paused', 'archived')),
    
    -- AI metadata
    generation_context TEXT,                 -- JSON: профіль юзера на момент генерації
    ai_notes TEXT,                           -- Нотатки AI про програму
    
    started_at TEXT,
    completed_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### program_days

Дні в програмі.

```sql
CREATE TABLE program_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL REFERENCES training_programs(id),
    
    day_number INTEGER NOT NULL,             -- 1, 2, 3... (порядок в спліті)
    name TEXT NOT NULL,                      -- "Push", "Pull A", "Legs"
    focus_muscles TEXT DEFAULT '[]',         -- JSON: ["chest","shoulders","triceps"]
    
    estimated_duration_min INTEGER DEFAULT 60,
    warmup_notes TEXT,                       -- AI рекомендації для розминки цього дня
    
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### program_exercises

Вправи в дні програми.

```sql
CREATE TABLE program_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_day_id INTEGER NOT NULL REFERENCES program_days(id),
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    
    order_in_day INTEGER NOT NULL,           -- порядок виконання
    
    sets_planned INTEGER NOT NULL DEFAULT 3,
    reps_min INTEGER NOT NULL DEFAULT 8,
    reps_max INTEGER NOT NULL DEFAULT 12,
    
    rest_seconds INTEGER DEFAULT 120,
    tempo TEXT,                              -- "3-1-2-0" (eccentric-pause-concentric-pause)
    
    weight_suggestion_kg REAL,               -- рекомендована вага
    weight_suggestion_source TEXT DEFAULT 'ai', -- ai, algorithm, user_override
    
    superset_group INTEGER,                  -- NULL = звичайна, число = група суперсету
    
    notes TEXT,                              -- "Фокус на розтягування в нижній точці"
    
    is_optional INTEGER DEFAULT 0,           -- 1 = можна пропустити якщо мало часу/енергії
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### workout_logs

Лог виконаного тренування (сесія).

```sql
CREATE TABLE workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    program_id INTEGER REFERENCES training_programs(id),
    program_day_id INTEGER REFERENCES program_days(id),
    
    date TEXT NOT NULL,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_minutes INTEGER,
    
    -- Суб'єктивна оцінка після тренування
    overall_feeling INTEGER CHECK(overall_feeling BETWEEN 1 AND 10),
    
    -- Обчислювані метрики (заповнюються після збереження)
    total_volume_kg REAL,                    -- сума (вага × повтори) по всіх вправах
    total_sets INTEGER,
    
    -- Чи були адаптації
    was_adapted INTEGER DEFAULT 0,           -- 1 якщо AI адаптував тренування (втома, цикл)
    adaptation_reason TEXT,                   -- "low_energy", "luteal_phase", "pain"
    
    notes TEXT,
    ai_feedback TEXT,                        -- фідбек AI після тренування
    
    status TEXT DEFAULT 'completed' CHECK(status IN ('in_progress', 'completed', 'partial', 'skipped')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### exercise_logs

Лог кожного підходу кожної вправи.

```sql
CREATE TABLE exercise_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_log_id INTEGER NOT NULL REFERENCES workout_logs(id),
    program_exercise_id INTEGER REFERENCES program_exercises(id), -- NULL якщо вправа додана на ходу
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    
    set_number INTEGER NOT NULL,
    weight_kg REAL NOT NULL DEFAULT 0,
    reps_done INTEGER NOT NULL,
    
    rpe INTEGER CHECK(rpe BETWEEN 1 AND 10), -- Rate of Perceived Exertion
    rpe_simple TEXT CHECK(rpe_simple IN ('easy', 'moderate', 'hard', 'max')), -- спрощений RPE для початківців
    
    -- Порівняння з планом
    was_target_hit INTEGER,                  -- 1 якщо повтори в межах reps_min-reps_max
    
    set_type TEXT DEFAULT 'working' CHECK(set_type IN ('warmup', 'working', 'dropset', 'failure', 'amrap')),
    
    notes TEXT,                              -- "відчула біль", "поганий контроль"
    skipped INTEGER DEFAULT 0,               -- 1 якщо підхід пропущено
    skip_reason TEXT,                         -- "pain", "fatigue", "equipment"
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### progressive_overload_log

Лог рішень алгоритму прогресії (для аудиту і навчання).

```sql
CREATE TABLE progressive_overload_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    exercise_id INTEGER NOT NULL REFERENCES exercises(id),
    program_exercise_id INTEGER REFERENCES program_exercises(id),
    
    date TEXT NOT NULL,
    
    -- Що було
    previous_weight_kg REAL,
    previous_reps_avg REAL,
    previous_rpe_avg REAL,
    weeks_at_current_weight INTEGER,
    
    -- Рішення
    decision TEXT NOT NULL,                  -- "increase_weight", "increase_reps", "maintain", "decrease", "change_exercise", "deload"
    new_weight_suggestion_kg REAL,
    new_reps_min INTEGER,
    new_reps_max INTEGER,
    
    reason TEXT NOT NULL,                    -- Пояснення рішення
    decision_source TEXT DEFAULT 'algorithm', -- algorithm, ai_override, user_override
    
    -- Чи прийняв юзер
    accepted INTEGER,                        -- 1 = прийнято, 0 = юзер відхилив
    user_override_value REAL,                -- що юзер вибрав замість
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Nutrition Module (Фаза 3) — схема наперед

### meal_plans

```sql
CREATE TABLE meal_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    name TEXT,                               -- "Набір маси — тиждень 1"
    
    daily_calories_target INTEGER,
    protein_g INTEGER,
    carbs_g INTEGER,
    fat_g INTEGER,
    
    type TEXT DEFAULT 'training_day',        -- training_day, rest_day
    status TEXT DEFAULT 'active',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### meal_log

```sql
CREATE TABLE meal_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,
    
    meal_type TEXT NOT NULL,                 -- breakfast, lunch, dinner, snack, pre_workout, post_workout
    description TEXT NOT NULL,               -- "курка з рисом і овочами"
    
    calories_estimated INTEGER,
    protein_g REAL,
    carbs_g REAL,
    fat_g REAL,
    
    photo_path TEXT,                         -- фото їжі для AI-оцінки
    ai_estimation INTEGER DEFAULT 0,         -- 1 якщо макроси оцінені AI
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Sleep Module (Фаза 4) — схема наперед

### sleep_logs

```sql
CREATE TABLE sleep_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,                      -- дата пробудження
    
    bedtime TEXT,                            -- "23:15"
    waketime TEXT,                           -- "07:00"
    sleep_duration_hours REAL,
    
    time_to_fall_asleep_min INTEGER,         -- скільки засинала
    night_awakenings INTEGER DEFAULT 0,
    
    quality INTEGER CHECK(quality BETWEEN 1 AND 10),
    
    caffeine_cutoff_time TEXT,               -- "14:00" — останній кофеїн
    screen_before_bed INTEGER,               -- 1 якщо екрани за 1 год до сну
    alcohol INTEGER DEFAULT 0,               -- 1 якщо пила алкоголь
    
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);
```

---

## Індекси

```sql
-- Основні запити
CREATE INDEX idx_daily_checkins_user_date ON daily_checkins(user_id, date);
CREATE INDEX idx_workout_logs_user_date ON workout_logs(user_id, date);
CREATE INDEX idx_exercise_logs_workout ON exercise_logs(workout_log_id);
CREATE INDEX idx_pain_journal_user_area ON pain_journal(user_id, body_area);
CREATE INDEX idx_training_programs_user_status ON training_programs(user_id, status);
CREATE INDEX idx_body_measurements_user_date ON body_measurements(user_id, date);
CREATE INDEX idx_progressive_overload_user_exercise ON progressive_overload_log(user_id, exercise_id);
```

---

## Міграції

При додаванні нових модулів — нові таблиці додаються через міграції. Існуючі таблиці НЕ змінюються (backward compatible). Таблиця `users` може розширюватись через ALTER TABLE ADD COLUMN.
