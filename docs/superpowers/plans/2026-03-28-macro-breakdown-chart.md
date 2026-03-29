# Macro Breakdown Chart — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the calories-only bar chart in the Progress tab with a stacked bar chart showing daily protein, carbs, and fat breakdown for the last 7 days.

**Architecture:** The `/api/v1/progress` endpoint already returns `nutrition_history` with `protein`, `carbs`, `fat` per day. Only the frontend `loadProgress()` rendering needs to be updated in `templates/app.html`. Replace the single-metric calorie bars with a stacked SVG bar chart showing all three macros.

**Tech Stack:** Vanilla JS + inline SVG (same pattern as existing weight/sleep charts)

---

## Task 1: Update the Nutrition Chart in loadProgress()

**Files:**
- Modify: `templates/app.html:2009-2025`

The existing block at line 2009 renders only calories as horizontal bars. Replace it with a stacked bar chart.

- [ ] **Step 1: Locate the nutrition chart block**

In `templates/app.html`, find the `progress-nutrition` rendering block inside `loadProgress()`. It starts around line 2009 with:
```javascript
const nutrEl = document.getElementById('progress-nutrition');
const nh = d.nutrition_history || [];
```

- [ ] **Step 2: Replace with stacked bar chart**

Replace the entire `if (nh.length > 0) { ... } else { ... }` block for `progress-nutrition` with the following code:

```javascript
// Nutrition — stacked macro bar chart (last 7 days)
const nutrEl = document.getElementById('progress-nutrition');
const nh = d.nutrition_history || [];
if (nh.length > 0) {
    const W = 340, H = nh.length * 56 + 40, PAD = 8;
    const barH = 28;
    const macros = ['protein', 'carbs', 'fat'];
    const colors = { protein: '#3b82f6', carbs: '#f59e0b', fat: '#ef4444' };
    const labels = { protein: 'Білок', carbs: 'Вуглеводи', fat: 'Жири' };
    const maxVals = { protein: 200, carbs: 300, fat: 100 }; // reasonable max display values
    const targetCal = 2000;

    let legend = '<div style="display:flex;gap:12px;margin-bottom:8px;flex-wrap:wrap;">';
    macros.forEach(function(m) {
        legend += '<span style="display:flex;align-items:center;gap:4px;font-size:11px;color:#aaa;">' +
            '<span style="width:10px;height:10px;border-radius:2px;background:' + colors[m] + ';display:inline-block;"></span>' +
            labels[m] + '</span>';
    });
    legend += '</div>';

    let svgContent = '';
    nh.slice().reverse().forEach(function(n, i) {
        var y = PAD + 20 + i * 56;
        var runningX = PAD;
        var totalGrams = (n.protein || 0) + (n.carbs || 0) + (n.fat || 0);

        // Draw protein, carbs, fat stacked bars
        macros.forEach(function(m) {
            var grams = n[m] || 0;
            var barW = totalGrams > 0 ? (grams / totalGrams) * (W - PAD * 2) : 0;
            if (barW < 1) return;
            svgContent += '<rect x="' + runningX.toFixed(1) + '" y="' + y + '" width="' + barW.toFixed(1) + '" height="' + barH + '" rx="3" fill="' + colors[m] + '" opacity="0.85"/>';
            if (barW > 30) {
                svgContent += '<text x="' + (runningX + barW / 2).toFixed(1) + '" y="' + (y + barH / 2 + 4).toFixed(1) + '" text-anchor="middle" fill="#fff" font-size="10" font-weight="600">' + grams + 'г</text>';
            }
            runningX += barW;
        });

        // Date label
        svgContent += '<text x="' + (W - PAD) + '" y="' + (y + barH / 2 + 4) + '" text-anchor="end" fill="#aaa" font-size="10">' + (n.date || '').substring(5) + '</text>';
        // Calories below bars
        svgContent += '<text x="' + PAD + '" y="' + (y + barH + 14) + '" fill="#666" font-size="10">' + (n.calories || 0) + ' ккал</text>';
    });

    nutrEl.innerHTML = legend + '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:auto;display:block;" xmlns="http://www.w3.org/2000/svg">' + svgContent + '</svg>';
} else {
    nutrEl.innerHTML = '<div style="color:#888;font-size:13px">Немає даних про харчування</div>';
}
```

- [ ] **Step 3: Verify the change**

Run: `grep -n "progress-nutrition" templates/app.html`
Confirm block starts around line 2009 and ends around line 2025.

- [ ] **Step 4: Commit**

```bash
cd /home/hui20metrov/gym-coach
git add templates/app.html
git commit -m "feat(ui): macro breakdown stacked bar chart in progress tab
- show protein/carbs/fat per day as stacked bars
- add legend and calorie labels per day
- refs #51"
```

---

## Verification

1. **Visual check:** After deploy, open Progress tab → Nutrition section. Confirm 7 stacked bars (one per day), each bar split into 3 colored segments (blue=protein, amber=carbs, red=fat) with gram labels inside bars and date + calorie count below.
2. **Edge cases:**
   - No nutrition data → shows "Немає даних про харчування"
   - One macro = 0 → that segment is skipped, others expand
   - Very small segment (<30px) → no text label shown inside bar
3. **API check:** `curl /api/v1/progress` → `nutrition_history` array has `protein`, `carbs`, `fat`, `calories` per entry.
