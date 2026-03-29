# Macro Breakdown Chart — Implementation Plan

**Issue:** #51 — Horizontal stacked bar per day: protein (blue) / carbs (yellow) / fat (red) vs targets

**Files to modify:**
- `routes/progress.py` — add `macro_targets` to `/api/v1/progress` response
- `templates/app.html` — render macro stacked bars in `progress-nutrition` section

---

## Task 1: Backend — add macro_targets to progress endpoint

**File:** `routes/progress.py`

The progress endpoint already returns `nutrition_history` with per-day protein/carbs/fat (lines 450-480). I need to add `macro_targets` using the existing `_calculate_targets` function from `routes/nutrition.py`.

Changes:
1. Import `_calculate_targets` from `routes.nutrition`
2. After computing `nutrition_history`, get user profile and compute targets
3. Add `macro_targets` to the response

Steps:
- [ ] Import: add `from routes.nutrition import _calculate_targets` at top
- [ ] In the progress endpoint, after fetching user data, call `_calculate_targets(user)`  
- [ ] Add `macro_targets` to response dict
- [ ] Write test
- [ ] Commit

---

## Task 2: Frontend — macro stacked bar chart

**File:** `templates/app.html`

The `progress-nutrition` section (inside `loadProgress()`) currently shows calories bars. Replace/add macro stacked bars:

For each of the last 7 days:
- Show stacked horizontal bar: protein (blue #3b82f6) | carbs (yellow #f59e0b) | fat (red #ef4444)
- Bar width proportional to target
- Color coding: orange when 10% under target, green when within 10%
- Below each bar: totals "P: X/Y  C: X/Y  F: X/Y"

Above the chart:
- Summary totals: "P: 840/1050g  C: 1260/1400g  F: 385/490g"
- Color indicators: green/white/orange based on progress

Steps:
- [ ] Modify the `progress-nutrition` rendering in `loadProgress()`
- [ ] Replace calories-only chart with macro stacked bars
- [ ] Commit

---

## Verification

1. Progress tab shows macro bars for last 7 days
2. Each bar shows protein/carbs/fat stacked
3. Targets shown
4. Color coding correct
5. Tests pass
