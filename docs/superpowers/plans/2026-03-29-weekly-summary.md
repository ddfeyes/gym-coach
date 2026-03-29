# Weekly Summary Card — Implementation Plan

**Goal:** Показывать карточку с weekly summary в Progress tab по понедельникам. Dismissible, не показывается повторно на той же неделе.

**Architecture:** 
- Новый endpoint `GET /api/v1/progress/weekly-summary` — данные за последние 7 дней
- Dismissible state в localStorage (`weekly_summary_dismissed_week`)
- Карточка вверху Progress tab, видна только в понедельник

**Files:**
- `routes/progress.py` — endpoint weekly-summary
- `migrations/011_weekly_summary_seen.py` — optionally track seen state server-side (для future use)
- `templates/app.html` — weekly summary card HTML + CSS + JS
- `tests/test_progress_weekly.py` — тесты endpoint

---

## Task 1: API endpoint

**Files:** Modify `routes/progress.py`

```python
@progress_bp.route('/api/v1/progress/weekly-summary', methods=['GET'])
def get_weekly_summary():
    """Return weekly summary data for Monday card."""
    init_data = request.headers.get('X-Telegram-Init-Data')
    if not init_data:
        return jsonify({"error": "Unauthorized"}), 401
    if not validate_telegram_init_data(init_data, Config.TELEGRAM_BOT_TOKEN):
        return jsonify({"error": "Invalid init data"}), 401
    tg_user = extract_user_from_init_data(init_data)
    telegram_id = tg_user.get('id')
    user_id = get_user_id(telegram_id)
    if not user_id:
        return jsonify({"error": "User not found"}), 404

    db = get_db()
    db.row_factory = sqlite3.Row
    today = date.today()
    week_ago = (today - timedelta(days=7)).isoformat()
    two_weeks_ago = (today - timedelta(days=14)).isoformat()

    # Training sessions this week
    training_rows = db.execute("""
        SELECT COUNT(*) as c FROM training_sessions
        WHERE user_id = ? AND DATE(date) >= ?
    """, (user_id, week_ago)).fetchone()
    training_count = training_rows['c'] if training_rows else 0

    # Avg sleep this week
    sleep_rows = db.execute("""
        SELECT AVG(hours) as avg_hours FROM sleep_logs
        WHERE user_id = ? AND DATE(date) >= ?
    """, (user_id, week_ago)).fetchall()
    avg_sleep = round(sleep_rows[0]['avg_hours'], 1) if sleep_rows and sleep_rows[0]['avg_hours'] else 0

    # Water goal hit days (>= 2500ml)
    water_rows = db.execute("""
        SELECT SUM(amount_ml) as total, date FROM water_logs
        WHERE user_id = ? AND DATE(date) >= ?
        GROUP BY date
    """, (user_id, week_ago)).fetchall()
    water_hit_days = sum(1 for r in water_rows if r['total'] >= 2500)

    # Weight change
    weight_now = db.execute(
        "SELECT weight_kg FROM weight_logs WHERE user_id = ? ORDER BY date DESC LIMIT 1",
        (user_id,)).fetchone()
    weight_prev = db.execute(
        "SELECT weight_kg FROM weight_logs WHERE user_id = ? AND date <= ? ORDER BY date DESC LIMIT 1",
        (user_id, week_ago)).fetchone()
    weight_delta = None
    if weight_now and weight_prev:
        weight_delta = round(weight_now['weight_kg'] - weight_prev['weight_kg'], 1)

    # AI insight
    insights = []
    if training_count >= 4:
        insights.append(f"Тренувань {training_count} з 7 — відмінно!")
    elif training_count >= 2:
        insights.append(f"Тренувань {training_count} з 7 — непогано")
    else:
        insights.append(f"Тільки {training_count} тренувань — час активізуватись")
    if avg_sleep >= 7:
        insights.append(f"Сон {avg_sleep}г — добре")
    elif avg_sleep > 0:
        insights.append(f"Сон {avg_sleep}г — менше 7г рекомендовано")
    if water_hit_days >= 5:
        insights.append(f"Вода {water_hit_days}/7 днів")
    insight = " ".join(insights)

    db.close()
    return jsonify({
        "training_count": training_count,
        "avg_sleep": avg_sleep,
        "water_hit_days": water_hit_days,
        "weight_delta": weight_delta,
        "insight": insight,
    })
```

- [ ] **Step 1: Write test** — `tests/test_progress_weekly.py`
- [ ] **Step 2: Add endpoint** to routes/progress.py
- [ ] **Step 3: Run tests** — pytest → PASS
- [ ] **Step 4: Commit**

---

## Task 2: Frontend card

**Files:** Modify `templates/app.html`

Add after streak-cards in `#tab-progress`:

```html
<!-- Weekly Summary Card -->
<div class="weekly-summary-card hidden" id="weekly-summary-card">
    <div class="ws-header">
        <span class="ws-title">📊 Тижневий огляд</span>
        <button class="ws-dismiss" onclick="dismissWeeklySummary()">✕</button>
    </div>
    <div class="ws-stats">
        <div class="ws-stat">
            <div class="ws-stat-value" id="ws-training">—</div>
            <div class="ws-stat-label">Тренувань</div>
        </div>
        <div class="ws-stat">
            <div class="ws-stat-value" id="ws-sleep">—</div>
            <div class="ws-stat-label">Сон (ср)</div>
        </div>
        <div class="ws-stat">
            <div class="ws-stat-value" id="ws-water">—</div>
            <div class="ws-stat-label">Вода дні</div>
        </div>
        <div class="ws-stat">
            <div class="ws-stat-value" id="ws-weight">—</div>
            <div class="ws-stat-label">Вага Δ</div>
        </div>
    </div>
    <div class="ws-insight" id="ws-insight"></div>
</div>
```

CSS:
```css
.weekly-summary-card {
    background: linear-gradient(135deg, rgba(255,107,53,0.15), rgba(255,140,53,0.1));
    border: 1px solid rgba(255,107,53,0.3);
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 12px;
}
.ws-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.ws-title { font-size: 14px; font-weight: 700; color: var(--accent); }
.ws-dismiss { background: none; border: none; color: rgba(255,255,255,0.4); font-size: 16px; cursor: pointer; padding: 0; }
.ws-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 8px; }
.ws-stat { text-align: center; }
.ws-stat-value { font-size: 18px; font-weight: 900; color: #fff; }
.ws-stat-label { font-size: 9px; color: rgba(255,255,255,0.4); text-transform: uppercase; }
.ws-insight { font-size: 12px; color: rgba(255,255,255,0.7); font-style: italic; }
.hidden { display: none !important; }
```

JS:
```javascript
function shouldShowWeeklySummary() {
    const dismissedWeek = localStorage.getItem('weekly_summary_dismissed_week');
    const currentWeek = getWeekKey();  // e.g. "2026-W13"
    return dismissedWeek !== currentWeek;
}

function getWeekKey() {
    const now = new Date();
    const jan1 = new Date(now.getFullYear(), 0, 1);
    const week = Math.ceil(((now - jan1) / 86400000 + jan1.getDay() + 1) / 7);
    return now.getFullYear() + '-W' + String(week).padStart(2, '0');
}

function dismissWeeklySummary() {
    const card = document.getElementById('weekly-summary-card');
    if (card) card.classList.add('hidden');
    localStorage.setItem('weekly_summary_dismissed_week', getWeekKey());
}

async function loadWeeklySummary() {
    if (!initData) return;
    const now = new Date();
    if (now.getDay() !== 1) return;  // Only Monday (day 1)
    if (!shouldShowWeeklySummary()) return;
    try {
        const res = await fetch('/api/v1/progress/weekly-summary', {
            headers: { 'X-Telegram-Init-Data': initData },
        });
        if (!res.ok) return;
        const d = await res.json();
        const card = document.getElementById('weekly-summary-card');
        if (!card) return;
        document.getElementById('ws-training').textContent = d.training_count || 0;
        document.getElementById('ws-sleep').textContent = d.avg_sleep ? d.avg_sleep + 'г' : '—';
        document.getElementById('ws-water').textContent = (d.water_hit_days || 0) + '/7';
        const weightEl = document.getElementById('ws-weight');
        if (d.weight_delta !== null && d.weight_delta !== undefined) {
            const sign = d.weight_delta > 0 ? '+' : '';
            weightEl.textContent = sign + d.weight_delta + 'кг';
        } else {
            weightEl.textContent = '—';
        }
        document.getElementById('ws-insight').textContent = d.insight || '';
        card.classList.remove('hidden');
    } catch (err) {}
}
```

Add `loadWeeklySummary()` call in `loadProgress()` (after `loadStreaks()`).

- [ ] **Step 1: Add HTML** after streak-cards in #tab-progress
- [ ] **Step 2: Add CSS** to style block
- [ ] **Step 3: Add JS functions** + call in loadProgress
- [ ] **Step 4: Commit**

---

## Verification

1. `curl` endpoint → JSON with training_count, avg_sleep, water_hit_days, weight_delta, insight
2. App open on Monday → card visible; dismiss → localStorage set; refresh → card hidden
3. App open on non-Monday → card hidden
