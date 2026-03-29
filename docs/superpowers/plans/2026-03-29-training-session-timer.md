# Training Session Timer — Implementation Plan

**Goal:** Add a start/stop timer to the Training tab that logs workout duration automatically.

**Architecture:** Client-side timer (JS) with session logged to existing `/api/v1/training-sessions` endpoint which already accepts `duration_minutes`. No new API endpoints needed.

**Tech Stack:** Vanilla JS timer, Flask backend (existing), HTML/CSS in app.html.

---

## File Changes

**Modify:** `templates/app.html`
- Add timer display HTML inside `#tab-training`
- Add timer JS functions: `startTimer()`, `stopTimer()`, `updateTimerDisplay()`
- Add CSS for timer widget

**Modify:** `routes/training_sessions.py` — no changes needed (already supports `duration_minutes`)

**Modify:** `models/training_session.py` — verify `duration_minutes` column exists

---

## Tasks

### Task 1: Add timer widget HTML to Training tab

**Modify:** `templates/app.html` — insert timer UI near the "Почати тренування" button

```html
<div id="workout-timer" style="display:none;background:#1c1c21;border-radius:12px;padding:16px;margin:8px 0;text-align:center;">
    <div style="font-size:13px;color:#a0a0a0;margin-bottom:4px;">⏱️ Тренування</div>
    <div id="timer-display" style="font-size:36px;font-weight:700;font-variant-numeric:tabular-nums;">00:00:00</div>
    <div style="margin-top:12px;display:flex;gap:8px;justify-content:center;">
        <button id="timer-start-btn" class="btn-primary" onclick="startTimer()">▶ Старт</button>
        <button id="timer-stop-btn" class="btn-secondary" onclick="stopTimer()" disabled>⏹ Стоп</button>
    </div>
</div>
```

### Task 2: Add timer JavaScript

**Modify:** `templates/app.html` — add in `<script>` section

```javascript
let timerInterval = null;
let timerSeconds = 0;
let timerStartTime = null;

function startTimer() {
    if (timerInterval) return;
    document.getElementById('timer-start-btn').disabled = true;
    document.getElementById('timer-stop-btn').disabled = false;
    document.getElementById('workout-timer').style.display = 'block';
    timerStartTime = Date.now() - (timerSeconds * 1000);
    timerInterval = setInterval(() => {
        timerSeconds = Math.floor((Date.now() - timerStartTime) / 1000);
        updateTimerDisplay();
    }, 1000);
}

function stopTimer() {
    if (!timerInterval) return;
    clearInterval(timerInterval);
    timerInterval = null;
    document.getElementById('timer-start-btn').disabled = false;
    document.getElementById('timer-stop-btn').disabled = true;
    // Log session
    logWorkoutSession();
}

function updateTimerDisplay() {
    const h = Math.floor(timerSeconds / 3600);
    const m = Math.floor((timerSeconds % 3600) / 60);
    const s = timerSeconds % 60;
    document.getElementById('timer-display').textContent =
        `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

async function logWorkoutSession() {
    const durationMinutes = Math.max(1, Math.round(timerSeconds / 60));
    try {
        const res = await fetch('/api/v1/training-sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': initData,
            },
            body: JSON.stringify({ duration_minutes: durationMinutes }),
        });
        if (res.ok) {
            timerSeconds = 0;
            updateTimerDisplay();
            document.getElementById('workout-timer').style.display = 'none';
            loadTrainingProgram(); // refresh
        }
    } catch (e) { console.error(e); }
}
```

### Task 3: Wire timer into loadTrainingProgram()

**Modify:** `templates/app.html` — in the "Почати тренування" button's `onclick`, call `startTimer()` instead of `showLogWorkout()`. Find and replace the `onclick="showLogWorkout()"` in the training tab with `onclick="startTimer()"`.

### Task 4: Test

1. Open app → Training tab
2. Click "🏋️ Почати тренування"
3. Timer starts, displays 00:00:00
4. Wait ~5 seconds, click "⏹ Стоп"
5. Session logged with ~1 minute duration
6. UI refreshes showing session as completed

---

## Verification Checklist

- [ ] Timer starts on button click
- [ ] Timer counts up in HH:MM:SS format
- [ ] Stop button logs session with correct duration
- [ ] Training tab refreshes after logging
- [ ] Session appears in history
- [ ] No JS console errors
