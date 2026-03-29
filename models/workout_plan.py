import json
from database import get_db
from datetime import date, timedelta


def get_week_start(d: date = None) -> str:
    """Return Monday of the week for the given date (YYYY-MM-DD)."""
    if d is None:
        d = date.today()
    monday = d - timedelta(days=d.weekday())
    return monday.isoformat()


def create_workout_plan(user_id: int, week_start: str, plan_data: list) -> int:
    """Create a new workout plan. Deactivates any previous active plan for same week."""
    db = get_db()

    # Deactivate existing plan for this week
    db.execute(
        "UPDATE workout_plans SET is_active = 0 WHERE user_id = ? AND week_start = ?",
        (user_id, week_start)
    )

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO workout_plans (user_id, week_start, plan_data, is_active) VALUES (?, ?, ?, 1)",
        (user_id, week_start, json.dumps(plan_data))
    )
    plan_id = cursor.lastrowid

    # Insert planned exercises
    for day in plan_data:
        day_idx = day.get("day_idx")
        db.execute(
            "INSERT INTO planned_exercises (plan_id, day_idx, title, sets, muscle_groups, estimated_minutes, is_rest_day) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                plan_id,
                day_idx,
                day.get("title", ""),
                json.dumps(day.get("exercises", [])),
                json.dumps(day.get("muscle_groups", [])),
                day.get("estimated_minutes", 45),
                1 if day.get("is_rest_day") else 0,
            )
        )

    db.commit()
    db.close()
    return plan_id


def get_active_plan(user_id: int, week_start: str = None) -> dict | None:
    """Return active workout plan for the given week."""
    if week_start is None:
        week_start = get_week_start()
    db = get_db()
    row = db.execute(
        "SELECT * FROM workout_plans WHERE user_id = ? AND week_start = ? AND is_active = 1",
        (user_id, week_start)
    ).fetchone()
    if not row:
        db.close()
        return None

    plan = dict(row)
    plan["plan_data"] = json.loads(plan["plan_data"])

    # Fetch planned exercises
    exercises = db.execute(
        "SELECT * FROM planned_exercises WHERE plan_id = ? ORDER BY day_idx",
        (plan["id"],)
    ).fetchall()
    db.close()

    plan["days"] = []
    by_day = {}
    for ex in exercises:
        ex_dict = dict(ex)
        ex_dict["sets"] = json.loads(ex_dict["sets"])
        ex_dict["muscle_groups"] = json.loads(ex_dict["muscle_groups"])
        day_idx = ex_dict["day_idx"]
        if day_idx not in by_day:
            by_day[day_idx] = {
                "day_idx": day_idx,
                "title": ex_dict["title"],
                "is_rest_day": bool(ex_dict["is_rest_day"]),
                "muscle_groups": ex_dict["muscle_groups"],
                "estimated_minutes": ex_dict["estimated_minutes"],
                "exercises": [],
                "is_done": bool(ex_dict["is_done"]),
            }
        if not ex_dict["is_rest_day"]:
            # Normalize: AI sends {title, reps, weight_kg}, frontend expects {exercise, sets, reps, rest_seconds, notes}
            for exercise in ex_dict["sets"]:
                day_ex = {
                    "exercise": exercise.get("title", exercise.get("exercise", "")),
                    "sets": exercise.get("sets", 3),
                    "reps": exercise.get("reps", ""),
                    "rest_seconds": exercise.get("rest_seconds", exercise.get("rest", 60)),
                    "weight_kg": exercise.get("weight_kg", None),
                    "notes": exercise.get("notes", ""),
                }
                by_day[day_idx]["exercises"].append(day_ex)

    plan["days"] = [by_day[i] for i in sorted(by_day.keys())]
    return plan


def mark_day_complete(plan_id: int, day_idx: int) -> None:
    """Mark a day's planned exercises as done."""
    db = get_db()
    db.execute(
        "UPDATE planned_exercises SET is_done = 1 WHERE plan_id = ? AND day_idx = ?",
        (plan_id, day_idx)
    )
    db.commit()
    db.close()


def get_recent_training_history(user_id: int, days: int = 14) -> list:
    """Get training sessions from the last N days for AI context."""
    db = get_db()
    end_date = date.today().isoformat()
    start_date = (date.today() - timedelta(days=days)).isoformat()
    rows = db.execute(
        "SELECT * FROM training_sessions WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date",
        (user_id, start_date, end_date)
    ).fetchall()
    db.close()
    return [dict(row) for row in rows]
