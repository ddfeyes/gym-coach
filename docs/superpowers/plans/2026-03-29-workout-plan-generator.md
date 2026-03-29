# Workout Plan Generator — Implementation Plan

**Goal:** AI-generate a 7-day training plan per week based on user profile + recent training history.

**Issue:** #59

**Architecture:**
- New table `workout_plans`: stores generated 7-day plans per user/week
- New route `routes/plan.py`: handles `/api/v1/plan/generate` and `/api/v1/plan/current`
- AI generation via `agents.base.ai.chat()` with structured output prompt (reuses existing AI infrastructure)
- Frontend: add "Today's Plan" card to Training tab in `app.html`

---

## Database Schema

**New table:** `workout_plans`
```sql
CREATE TABLE workout_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    week_start DATE NOT NULL,          -- Monday of the plan week
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    plan_data TEXT NOT NULL,           -- JSON: [{"day_idx": 0, "title": "Push Day", "exercises": [...], "muscle_groups": [...], "estimated_minutes": 60}, ...]
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, week_start)
);
```

**New table:** `planned_exercises`
```sql
CREATE TABLE planned_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    day_idx INTEGER NOT NULL,          -- 0=Monday ... 6=Sunday
    title TEXT NOT NULL,
    sets TEXT,                          -- JSON: [{"reps": "3×12", "weight_kg": 20}]
    muscle_groups TEXT,                -- JSON: ["chest", "triceps", "shoulders"]
    estimated_minutes INTEGER DEFAULT 45,
    is_rest_day BOOLEAN DEFAULT 0,
    FOREIGN KEY (plan_id) REFERENCES workout_plans(id)
);
```

---

## File Changes

### New File: `routes/plan.py`
- `POST /api/v1/plan/generate` — generates 7-day plan for current or next week
- `GET /api/v1/plan/current` — returns active plan for this week
- `POST /api/v1/plan/<plan_id>/complete/<day_idx>` — marks a day's workout as done

### New File: `models/workout_plan.py`
- `create_workout_plan(user_id, week_start, plan_data)`
- `get_active_plan(user_id)` → returns plan with planned_exercises
- `mark_day_complete(plan_id, day_idx)`
- `get_recent_training_history(user_id, days=14)` — used for AI context

### Modify: `app.html`
- Add "Today's Plan" card at top of Training tab
- Fetch `/api/v1/plan/current` on tab load
- Show today's workout with "Mark as Done" button
- If rest day → show rest day message

### Modify: `routes/__init__.py`
- Register `plan_bp`

---

## API Design

### `POST /api/v1/plan/generate`

**Auth:** X-Telegram-Init-Data header

**Request body:** (optional)
```json
{ "week_start": "2026-03-30" }  // defaults to next Monday
```

**Response:**
```json
{
  "plan_id": 12,
  "week_start": "2026-03-30",
  "days": [
    {
      "day_idx": 0,
      "title": "Upper Body (Push)",
      "is_rest_day": false,
      "muscle_groups": ["chest", "triceps", "shoulders"],
      "estimated_minutes": 60,
      "exercises": [
        {"title": "Bench Press", "sets": "3×10", "reps": "10", "weight_kg": 40},
        {"title": "Overhead Press", "sets": "3×8", "reps": "8", "weight_kg": 25},
        {"title": "Incline Dumbbell Press", "sets": "3×12", "reps": "12", "weight_kg": 16}
      ]
    },
    { "day_idx": 1, "title": "Rest", "is_rest_day": true, ... },
    ...
  ]
}
```

**AI Prompt:** Build from user profile (experience_level, training_days_per_week, primary_goal, available_equipment) + last 14 days training history.

### `GET /api/v1/plan/current`

**Auth:** X-Telegram-Init-Data header

**Response:** Same as above, or `{"has_plan": false}` if none active.

### `POST /api/v1/plan/<plan_id>/complete/<day_idx>`

**Auth:** X-Telegram-Init-Data header

**Response:** `{"ok": true}`

---

## Frontend: Today's Plan Card

Insert at top of `#tab-training` in `app.html`:

```html
<div id="today-plan-card" style="display:none; background:linear-gradient(135deg,#667eea,#764ba2);border-radius:16px;padding:20px;margin:12px 0;color:#fff;">
  <div style="font-size:12px;opacity:0.85;margin-bottom:4px;">📅 Today's Plan</div>
  <div id="today-plan-title" style="font-size:18px;font-weight:700;margin-bottom:8px;"></div>
  <div id="today-plan-muscles" style="font-size:13px;opacity:0.9;margin-bottom:10px;"></div>
  <div style="display:flex;gap:8px;align-items:center;">
    <button id="mark-done-btn" class="btn-primary" onclick="markDayDone()">✓ Mark as Done</button>
    <span id="mark-done-status" style="font-size:12px;opacity:0.85;"></span>
  </div>
</div>
```

JS logic:
- `loadTodayPlan()` → `GET /api/v1/plan/current` → render card
- If rest day → show "Rest Day ☕" instead of button
- `markDayDone()` → `POST /api/v1/plan/<id>/complete/<day_idx>` → show ✓, log session

---

## Rest Day Logic (AI prompt constraint)
No muscle group should appear on consecutive days. AI prompt must enforce this.

---

## Tasks

### Task 1: Database migration
Create `migrations/` SQL file or use Alembic equivalent for `workout_plans` + `planned_exercises` tables.

### Task 2: `models/workout_plan.py`
Implement `create_workout_plan`, `get_active_plan`, `mark_day_complete`, `get_recent_training_history`.

### Task 3: `routes/plan.py`
Implement `POST /api/v1/plan/generate`:
- Build context: user profile + 14-day history
- Call `ai.chat()` with structured plan prompt
- Parse JSON response → store in DB
- Return plan data

Implement `GET /api/v1/plan/current`:
- Return active plan for current week (week_start = this week's Monday)

Implement `POST /api/v1/plan/<id>/complete/<day_idx>`:
- Mark `is_done=True` for that day's planned_exercises row
- Log to training_sessions via existing model

### Task 4: Frontend in `app.html`
Add today's plan card + JS functions. Call `loadTodayPlan()` in `switchTab('training')`.

### Task 5: Register blueprint
Add `from routes.plan import plan_bp` and `app.register_blueprint(plan_bp, url_prefix='/api/v1/plan')` in `app.py`.

### Task 6: Test
1. `POST /api/v1/plan/generate` → should return 7-day plan
2. `GET /api/v1/plan/current` → should return plan
3. Training tab shows today's plan card
4. "Mark as Done" → session logged

---

## Verification Checklist

- [ ] `POST /api/v1/plan/generate` returns valid 7-day plan
- [ ] No muscle group appears on consecutive days (rest day logic)
- [ ] `GET /api/v1/plan/current` returns active plan
- [ ] Today's plan card shows in Training tab
- [ ] "Mark as Done" logs to training_sessions
- [ ] No 500 errors
- [ ] CI passes
