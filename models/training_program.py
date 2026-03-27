import json
from database import get_db


def create_training_program(user_id: int, name: str, schedule: list, exercises: list, program_type: str = 'split', notes: str = '') -> int:
    """Create a new training program."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO training_programs (user_id, name, program_type, schedule, exercises, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, name, json.dumps(schedule, ensure_ascii=False), json.dumps(exercises, ensure_ascii=False), program_type, notes),
    )
    db.commit()
    prog_id = cursor.lastrowid
    db.close()
    return prog_id


def get_active_training_program(user_id: int) -> dict | None:
    """Get the active training program for a user."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM training_programs WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    db.close()
    if not row:
        return None
    prog = dict(row)
    prog['schedule'] = json.loads(prog['schedule'])
    prog['exercises'] = json.loads(prog['exercises'])
    return prog


def get_training_programs(user_id: int, limit: int = 10) -> list:
    """Get all training programs for a user."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM training_programs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    db.close()
    results = []
    for row in rows:
        prog = dict(row)
        prog['schedule'] = json.loads(prog['schedule'])
        prog['exercises'] = json.loads(prog['exercises'])
        results.append(prog)
    return results


def set_active_program(user_id: int, program_id: int):
    """Set a program as active, deactivate others."""
    db = get_db()
    db.execute("UPDATE training_programs SET is_active = 0 WHERE user_id = ?", (user_id,))
    db.execute("UPDATE training_programs SET is_active = 1 WHERE id = ? AND user_id = ?", (program_id, user_id))
    db.commit()
    db.close()


def delete_training_program(program_id: int, user_id: int) -> bool:
    """Delete a training program."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM training_programs WHERE id = ? AND user_id = ?", (program_id, user_id))
    db.commit()
    deleted = cursor.rowcount > 0
    db.close()
    return deleted
