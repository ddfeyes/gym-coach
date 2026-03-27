# Roadmap — Фази та терміни реалізації

## Загальний таймлайн

```
Фаза 0 ████░░░░░░░░░░░░░░░░░░░░░░░░░░░  3-4 дні    ← Фундамент
Фаза 1 ░░░░████████░░░░░░░░░░░░░░░░░░░░  7-10 днів  ← Training MVP
Фаза 2 ░░░░░░░░░░░░████████░░░░░░░░░░░░  7-10 днів  ← Smart Coach
────── MVP READY (3-4 тижні) ──────
Фаза 3 ░░░░░░░░░░░░░░░░░░░░██████████░░  10-14 днів ← Nutrition
Фаза 4 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██  5-7 днів   ← Sleep
Фаза 5 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  5-7 днів   ← Technique
Фаза 6 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  5-7 днів   ← Analytics
Фаза 7 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  3-5 днів   ← Psychology
Фаза 8 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  7-10 днів  ← Polish
────── FULL VERSION (~2.5-3 місяці) ──────
```

Оцінка при 2-4 годинах роботи на день.

---

## ФАЗА 0 — Фундамент (3-4 дні)

### Ціль
Робочий скелет: бот відповідає, Mini App відкривається, AI pipeline працює.

### День 1
| # | Задача | Деталі | Час |
|---|--------|--------|-----|
| 0.1 | Створити репо | `git init`, `.gitignore`, `requirements.txt` | 15 хв |
| 0.2 | Flask app | `app.py` з базовим routing, `/` → Mini App, `/api/v1/health` | 30 хв |
| 0.3 | Config | `.env`, `config.py` з усіма ключами | 15 хв |
| 0.4 | Database init | `database.py` — створення таблиць `users`, `ai_conversations` | 1 год |
| 0.5 | Telegram bot | `bot.py` — /start команда, webhook setup | 1 год |

### День 2
| # | Задача | Деталі | Час |
|---|--------|--------|-----|
| 0.6 | Mini App shell | `app.html` — темна тема, bottom nav з табами, placeholder контент | 2 год |
| 0.7 | Telegram auth | Валідація initData, middleware `@require_auth` | 1 год |
| 0.8 | AI provider | `agents/base.py` — абстракція Claude/Groq, базовий виклик | 1 год |

### День 3
| # | Задача | Деталі | Час |
|---|--------|--------|-----|
| 0.9 | Base prompt | Написати і відтестувати base system prompt | 1 год |
| 0.10 | Chat pipeline | `/api/v1/chat/message` → router → AI → response | 1.5 год |
| 0.11 | E2E тест | Відкрити Mini App, написати "привіт" → отримати відповідь від коуча | 30 хв |
| 0.12 | Deploy | Railway або Render, webhook живий | 1 год |

### Критерій завершення
- [ ] Mini App відкривається з Telegram
- [ ] Бот відповідає на /start
- [ ] Чат з AI працює (написав → отримав відповідь)
- [ ] Деплой на хостинг, webhook живий

---

## ФАЗА 1 — Training MVP (7-10 днів)

### Ціль
Можна пройти онбординг, отримати програму, виконати тренування і залогати його.

### Тиждень 1

| # | Задача | Деталі | Час |
|---|--------|--------|-----|
| 1.1 | DB tables | Всі training-таблиці: `training_programs`, `program_days`, `program_exercises`, `exercises`, `workout_logs`, `exercise_logs` | 2 год |
| 1.2 | Exercise seed | Створити `exercises_seed.json` з 50-80 вправами (compound + isolation, основні м'язові групи) | 3 год |
| 1.3 | Onboarding UI | 6-крокова форма в Mini App з валідацією | 4 год |
| 1.4 | Onboarding API | Ендпоінти збереження кроків і фіналізації | 2 год |
| 1.5 | Program generation | AI prompt для генерації програми → парсинг JSON → збереження в БД | 4 год |
| 1.6 | Program UI | Відображення програми: дні → вправи → деталі | 3 год |

### Тиждень 2

| # | Задача | Деталі | Час |
|---|--------|--------|-----|
| 1.7 | Workout UI | Екран виконання: вправи, підходи, інпути ваги/повторів/RPE | 5 год |
| 1.8 | Workout API | Start, log-set, skip, finish ендпоінти | 3 год |
| 1.9 | Rest timer | Таймер відпочинку між підходами | 1 год |
| 1.10 | Post-workout | Екран завершення + AI фідбек | 2 год |
| 1.11 | Workout history | Список минулих тренувань | 2 год |
| 1.12 | Bug fixes | Тестування і фікси | 2 год |

### Критерій завершення
- [ ] Можна пройти онбординг від початку до кінця
- [ ] Програма генерується і відображається
- [ ] Можна виконати тренування з логуванням кожного підходу
- [ ] AI дає фідбек після тренування
- [ ] Видно історію тренувань

---

## ФАЗА 2 — Smart Coach (7-10 днів)

### Ціль
Агент адаптується: прогресія, цикл, чекін, біль.

| # | Задача | Час |
|---|--------|-----|
| 2.1 | Progressive overload algorithm | 4 год |
| 2.2 | Overload UI (рекомендації, прийняти/відхилити) | 3 год |
| 2.3 | Daily checkin form | 3 год |
| 2.4 | Checkin API + notifications (бот) | 2 год |
| 2.5 | Cycle tracker (auto-calculation, phase display) | 3 год |
| 2.6 | Cycle adaptation logic | 3 год |
| 2.7 | Workout adapter (cycle + checkin + pain → adapted workout) | 4 год |
| 2.8 | Pain journal UI + API | 3 год |
| 2.9 | Pain pattern analysis (AI) | 2 год |
| 2.10 | Exercise replacement flow | 3 год |
| 2.11 | Deload logic (detection + protocol) | 2 год |
| 2.12 | Testing + fixes | 3 год |

### Критерій завершення
- [ ] Прогресія пропонує збільшення ваги автоматично
- [ ] Чекін працює і впливає на тренування
- [ ] Цикл трекається і адаптує рекомендації
- [ ] Біль-журнал працює, AI аналізує патерни
- [ ] Вправи можна замінити на льоту

---

## ФАЗА 3 — Nutrition (10-14 днів)

| # | Задача | Час |
|---|--------|-----|
| 3.1 | DB tables (meal_plans, meal_log) | 1 год |
| 3.2 | Nutrition profile (інтерв'ю, алергії, TDEE) | 3 год |
| 3.3 | Nutrition module prompt | 2 год |
| 3.4 | Meal plan generation (AI) | 4 год |
| 3.5 | Meal plan UI (таб "Food") | 4 год |
| 3.6 | Food logging (text input → AI estimation) | 4 год |
| 3.7 | Daily macros dashboard | 3 год |
| 3.8 | Cross-module: nutrition ← training data | 2 год |
| 3.9 | Supplement recommendations | 2 год |
| 3.10 | Testing + fixes | 3 год |

---

## ФАЗА 4 — Sleep & Recovery (5-7 днів)

| # | Задача | Час |
|---|--------|-----|
| 4.1 | DB tables (sleep_logs) | 1 год |
| 4.2 | Sleep logging UI | 3 год |
| 4.3 | Recovery module prompt | 2 год |
| 4.4 | Sleep recommendations (AI) | 3 год |
| 4.5 | Recovery routines (stretching, foam rolling) | 3 год |
| 4.6 | Cross-module: sleep ← training load | 2 год |

---

## ФАЗА 5 — Technique & Library (5-7 днів)

| # | Задача | Час |
|---|--------|-----|
| 5.1 | Expand exercise library to 200+ | 4 год |
| 5.2 | Exercise detail screen (техніка, помилки, відео) | 3 год |
| 5.3 | Technique chat (specialized AI) | 3 год |
| 5.4 | Mobility routines generator | 3 год |
| 5.5 | Warmup generator per workout | 2 год |
| 5.6 | Video analysis via Claude Vision (experimental) | 3 год |

---

## ФАЗА 6 — Analytics (5-7 днів)

| # | Задача | Час |
|---|--------|-----|
| 6.1 | Weekly volume calculation + UI | 3 год |
| 6.2 | Exercise progress charts | 4 год |
| 6.3 | Body measurements tracker | 3 год |
| 6.4 | Progress photo comparison | 3 год |
| 6.5 | AI weekly review | 3 год |
| 6.6 | AI monthly review | 2 год |

---

## ФАЗА 7 — Sport Psychology (3-5 днів)

| # | Задача | Час |
|---|--------|-----|
| 7.1 | Psychology module prompt | 2 год |
| 7.2 | Gamification: streaks, achievements | 4 год |
| 7.3 | Plateau management (AI) | 2 год |
| 7.4 | Motivation system (contextual encouragement) | 2 год |

---

## ФАЗА 8 — Polish & Integrations (7-10 днів)

| # | Задача | Час |
|---|--------|-----|
| 8.1 | Notification system (reminders, reviews) | 3 год |
| 8.2 | Travel/sick mode (home workouts) | 3 год |
| 8.3 | Blood test analysis (experimental) | 3 год |
| 8.4 | Wearables integration research | 3 год |
| 8.5 | PDF export (report for doctor) | 3 год |
| 8.6 | UX polish, animations, micro-interactions | 4 год |
| 8.7 | Performance optimization | 2 год |
| 8.8 | Bug fixing sprint | 4 год |

---

## Milestone Checkpoints

### 🏁 Milestone 1: "It Works" (кінець Фази 1)
Можна використовувати як базовий тренувальний трекер з AI-програмою.

### 🏁 Milestone 2: "It's Smart" (кінець Фази 2)
Коуч адаптується під тебе — цикл, стан, біль, прогресія. Вже краще за 95% фітнес-додатків.

### 🏁 Milestone 3: "It's Complete" (кінець Фази 3-4)
Тренування + Харчування + Сон = повний health stack.

### 🏁 Milestone 4: "It's Professional" (кінець Фази 5-8)
Повноцінна платформа рівня premium fitness app.

---

## Ризики і мітігація

| Ризик | Ймовірність | Мітігація |
|-------|------------|-----------|
| AI генерує неадекватну програму | Середня | Валідація output (кількість вправ, баланс м'язів), review перед збереженням |
| Контекст переповнюється | Середня | Structured summaries замість raw data, selective context |
| Mini App повільно працює | Низька | Мінімальний JS, lazy loading, кешування |
| Telegram API зміни | Низька | Абстракція над bot API |
| Claude API дорого | Низька | Groq для dev, кешування, batch operations |
| Юзер вводить сміття | Середня | Валідація на UI + backend, AI парсинг нечітких inputs |
| Мотивація юзера падає | Висока | Gamification, мінімальний обов'язковий ввід, positive reinforcement |

---

## Наступний крок

Фаза 0, День 1, Задача 0.1: створити репозиторій і базову структуру.

Скажи "поїхали" — і ми починаємо.
