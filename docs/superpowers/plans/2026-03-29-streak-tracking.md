# Streak Tracking Implementation Plan

**Goal:** Добавить отслеживание streaks (training/sleep/water) в Progress tab — карточки вверху, API endpoint, personal bests.

**Architecture:** Новый endpoint `/api/v1/progress/streaks` возвращает current streak + personal best для training (дни подряд с тренировкой), sleep (дни подряд ≥7h), water (дни подряд с goal hit). Personal bests хранятся в новой таблице `user_streaks`, обновляются при каждом вызове.

**Tech Stack:** Flask, SQLite (существующий), JavaScript (фронтенд)

---

## File Map

- **Create:** `migrations/010_user_streaks.py` — миграция для таблицы personal bests
- **Modify:** `routes/progress.py` — новый endpoint `/streaks`
- **Modify:** `templates/app.html` — JS fetch + HTML streak cards
- **Create:** `tests/test_progress_streaks.py` — тесты streak endpoint

---

## Task 1: Миграция для user_streaks

**Files:** Create: `migrations/010_user_streaks.py`

```python
def migrate(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            streak_type TEXT NOT NULL,  -- 'training' | 'sleep' | 'water'
            best_count INTEGER DEFAULT 0,
            best_start TEXT,
            best_end TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, streak_type)
        )
    """)
    db.commit()
```

- [ ] **Step 1: Написать миграцию** (содержимое выше)
- [ ] **Step 2: Запустить миграцию вручную** — `python -c "from migrations.010_user_streaks import migrate; from database import get_db; migrate(get_db())"`
- [ ] **Step 3: Проверить** — `sqlite3 data/gymcoach.db ".schema user_streaks"`

---

## Task 2: Streak calculation helpers + endpoint

**Files:** Modify: `routes/progress.py`

Streak algorithm: берём все даты из нужной таблицы за последние 90 дней, сортируем descending, идём с сегодняшки назад пока days consecutive.

Helper functions to add to `routes/progress.py`:

```python
def calc_consecutive_days(dates: list[str], threshold_check_fn) -> tuple[int, str, str]:
    """Returns (streak_count, start_date, end_date) for consecutive days meeting threshold."""
    if not dates:
        return 0, None, None
    today = date.today().isoformat()
    # Build set of valid dates
    valid = set()
    for d in dates:
        if threshold_check_fn(d):
            valid.add(d)
    if today not in valid:
        # Check if streak ended yesterday
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        if yesterday not in valid:
            return 0, None, None
        start_check = yesterday
    else:
        start_check = today
    # Count consecutive from start_check backwards
    count = 0
    d = date.fromisoformat(start_check)
    while d.isoformat() in valid:
        count += 1
        d -= timedelta(days=1)
    end_date = start_check
    start_date = (d + timedelta(days=1)).isoformat()
    return count, start_date, end_date

def get_training_streak(user_id: int, db) -> tuple[int, str, str]:
    rows = db.execute("""
        SELECT DISTINCT DATE(date) as d FROM training_sessions
        WHERE user_id = ? AND DATE(date) >= DATE('now', '-90 days')
        ORDER BY d DESC
    """, (user_id,)).fetchall()
    dates = [r['d'] for r in rows]
    return calc_consecutive_days(dates, lambda d: True)  # any training = success

def get_sleep_streak(user_id: int, db) -> tuple[int, str, str]:
    rows = db.execute("""
        SELECT date, hours FROM sleep_logs
        WHERE user_id = ? AND DATE(date) >= DATE('now', '-90 days')
    """, (user_id,)).fetchall()
    date_hours = {r['date']: r['hours'] for r in rows}
    return calc_consecutive_days(list(date_hours.keys()), lambda d: date_hours.get(d, 0) >= 7)

def get_water_streak(user_id: int, db) -> tuple[int, str, str]:
    rows = db.execute("""
        SELECT wl.date, up.water_goal_ml
        FROM water_logs wl
        JOIN user_profiles up ON up.user_id = wl.user_id
        WHERE wl.user_id = ? AND DATE(wl.date) >= DATE('now', '-90 days')
    """, (user_id,)).fetchall()
    date_goal = {r['date']: r['water_goal_ml'] for r in rows}
    return calc_consecutive_days(list(date_goal.keys()),
        lambda d: date_goal.get(d, 0) >= 2500)  # default 2500ml

def upsert_personal_best(user_id: int, streak_type: str, count: int, start: str, end: str, db):
    existing = db.execute(
        "SELECT best_count FROM user_streaks WHERE user_id = ? AND streak_type = ?",
        (user_id, streak_type)).fetchone()
    if not existing or count > existing['best_count']:
        db.execute("""
            INSERT INTO user_streaks (user_id, streak_type, best_count, best_start, best_end, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, streak_type) DO UPDATE SET
                best_count = excluded.best_count,
                best_start = excluded.best_start,
                best_end = excluded.best_end,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, streak_type, count, start, end))
        db.commit()
```

Endpoint to add to `routes/progress.py`:

```python
@progress_bp.route("/progress/streaks", methods=["GET"])
@login_required
def get_streaks():
    user_id = get_current_user_id()
    db = get_db()
    
    training_count, training_start, training_end = get_training_streak(user_id, db)
    sleep_count, sleep_start, sleep_end = get_sleep_streak(user_id, db)
    water_count, water_start, water_end = get_water_streak(user_id, db)
    
    # Update personal bests
    upsert_personal_best(user_id, 'training', training_count, training_start, training_end, db)
    upsert_personal_best(user_id, 'sleep', sleep_count, sleep_start, sleep_end, db)
    upsert_personal_best(user_id, 'water', water_count, water_start, water_end, db)
    
    # Get stored personal bests
    best_rows = db.execute(
        "SELECT streak_type, best_count, best_start, best_end FROM user_streaks WHERE user_id = ?",
        (user_id,)).fetchall()
    bests = {r['streak_type']: {'count': r['best_count'], 'start': r['best_start'], 'end': r['best_end']}
             for r in best_rows}
    
    db.close()
    return jsonify({
        "training": {"current": training_count, "start": training_start, "end": training_end,
                     "best": bests.get('training', {})},
        "sleep": {"current": sleep_count, "start": sleep_start, "end": sleep_end,
                  "best": bests.get('sleep', {})},
        "water": {"current": water_count, "start": water_start, "end": water_end,
                  "best": bests.get('water', {})},
    })
```

- [ ] **Step 1: Написать тест** (pytest tests/test_progress_streaks.py)
- [ ] **Step 2: Запустить — FAIL (module not found)**
- [ ] **Step 3: Добавить helpers + endpoint в routes/progress.py**
- [ ] **Step 4: Добавить импорт** `from datetime import date, timedelta` если нет
- [ ] **Step 5: Запустить тесты — PASS**
- [ ] **Step 6: Commit**

---

## Task 3: Frontend streak cards

**Files:** Modify: `templates/app.html`

Add after the stats-row in `#tab-progress`:

```html
<!-- Streak Cards -->
<div class="streak-cards">
    <div class="streak-card" id="streak-training">
        <span class="streak-emoji">🔥</span>
        <div class="streak-info">
            <div class="streak-count" id="streak-training-count">—</div>
            <div class="streak-label">тренувань</div>
            <div class="streak-pb" id="streak-training-pb"></div>
        </div>
    </div>
    <div class="streak-card" id="streak-sleep">
        <span class="streak-emoji">💤</span>
        <div class="streak-info">
            <div class="streak-count" id="streak-sleep-count">—</div>
            <div class="streak-label">днів сну ≥7г</div>
            <div class="streak-pb" id="streak-sleep-pb"></div>
        </div>
    </div>
    <div class="streak-card" id="streak-water">
        <span class="streak-emoji">💧</span>
        <div class="streak-info">
            <div class="streak-count" id="streak-water-count">—</div>
            <div class="streak-label">днів води</div>
            <div class="streak-pb" id="streak-water-pb"></div>
        </div>
    </div>
</div>
```

CSS (add to existing style block):
```css
.streak-cards { display: flex; gap: 8px; margin-bottom: 12px; }
.streak-card { flex: 1; background: rgba(255,255,255,0.05); border-radius: 12px; padding: 10px 8px; display: flex; align-items: center; gap: 8px; border: 1px solid rgba(255,255,255,0.08); }
.streak-emoji { font-size: 20px; }
.streak-info { flex: 1; }
.streak-count { font-size: 18px; font-weight: 700; color: var(--text); }
.streak-label { font-size: 10px; color: rgba(255,255,255,0.5); }
.streak-pb { font-size: 10px; color: rgba(255,200,50,0.7); margin-top: 2px; }
```

JS function:
```javascript
function loadStreaks() {
    fetch('/api/v1/progress/streaks')
        .then(r => r.json())
        .then(data => {
            for (const type of ['training', 'sleep', 'water']) {
                const d = data[type] || {};
                const count = d.current || 0;
                const best = d.best || {};
                document.getElementById('streak-' + type + '-count').textContent = count ? count + ' дн' : '—';
                const pbEl = document.getElementById('streak-' + type + '-pb');
                if (best && best.count > 0) {
                    pbEl.textContent = 'PB: ' + best.count + ' дн';
                } else {
                    pbEl.textContent = '';
                }
            }
        }).catch(() => {});
}
```

Add `loadStreaks()` call in the tab-switching or progress tab load function (find where other progress data loads like `loadProgressData()`).

- [ ] **Step 1: Добавить HTML streak cards** after stats-row
- [ ] **Step 2: Добавить CSS** to style block
- [ ] **Step 3: Добавить JS функцию + вызов** in progress tab load
- [ ] **Step 4: Commit**

---

## Verification

1. `curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/progress/streaks` → should return JSON with training/sleep/water
2. Open Mini App → Progress tab → verify streak cards show
3. `pytest tests/test_progress_streaks.py -v` → PASS
