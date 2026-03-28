from database import get_db
from datetime import date


def log_training_session(user_id: int, date_str: str = None, program_id: int = None,
                         duration_minutes: int = 0, notes: str = '') -> int:
    """Log a completed training session."""
    if date_str is None:
        date_str = str(date.today())
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO training_sessions (user_id, program_id, date, duration_minutes, notes) VALUES (?, ?, ?, ?, ?)",
        (user_id, program_id, date_str, duration_minutes, notes),
    )
    db.commit()
    log_id = cursor.lastrowid
    db.close()
    return log_id


def get_training_sessions(user_id: int, limit: int = 30) -> list:
    """Get training sessions for a user."""
    db = get_db()
    rows = db.execute(
        "SELECT ts.*, tp.name as program_name FROM training_sessions ts "
        "LEFT JOIN training_programs tp ON ts.program_id = tp.id "
        "WHERE ts.user_id = ? ORDER BY ts.date DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    db.close()
    return [dict(row) for row in rows]


def get_sessions_by_date_range(user_id: int, start_date: str, end_date: str) -> list:
    """Get training sessions within a date range."""
    db = get_db()
    rows = db.execute(
        "SELECT ts.*, tp.name as program_name FROM training_sessions ts "
        "LEFT JOIN training_programs tp ON ts.program_id = tp.id "
        "WHERE ts.user_id = ? AND ts.date BETWEEN ? AND ? ORDER BY ts.date DESC",
        (user_id, start_date, end_date)
    ).fetchall()
    db.close()
    return [dict(row) for row in rows]
