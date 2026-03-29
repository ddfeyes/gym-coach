from flask import Flask, render_template, jsonify, request
from config import Config
from database import create_tables, get_db
import time as _time
import threading

_APP_START_TIME = _time.monotonic()
_health_cache = {"data": None, "ts": 0}
_health_lock = threading.Lock()
from routes.chat import chat_bp
from routes.auth import auth_bp
from routes.onboarding import onboarding_bp
from routes.training import training_bp
from routes.nutrition import nutrition_bp
from routes.sleep import sleep_bp
from routes.measurements import measurements_bp
from routes.water import water_bp
from routes.progress import progress_bp
from routes.training_sessions import sessions_bp
from routes.plan import plan_bp
from bot import handle_telegram_update

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(chat_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(onboarding_bp)
app.register_blueprint(training_bp)
app.register_blueprint(nutrition_bp)
app.register_blueprint(sleep_bp)
app.register_blueprint(measurements_bp)
app.register_blueprint(water_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(plan_bp, url_prefix='/api/v1/workout-plan')


@app.route('/')
def index():
    return render_template('app.html')


@app.route('/api/v1/health')
def health():
    import time as _t
    import datetime

    now = _t.monotonic()
    with _health_lock:
        if _health_cache["data"] is not None and (now - _health_cache["ts"]) < 60:
            return jsonify(_health_cache["data"])

    db_status = "error"
    users_total = 0
    training_sessions_total = 0
    last_activity_at = None

    try:
        db = get_db()
        db.execute("SELECT 1")
        db_status = "ok"

        row = db.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
        users_total = row["cnt"] if row else 0

        row = db.execute("SELECT COUNT(*) as cnt FROM training_sessions").fetchone()
        training_sessions_total = row["cnt"] if row else 0

        row = db.execute(
            "SELECT MAX(created_at) as last FROM training_sessions"
        ).fetchone()
        last_activity_at = row["last"] if row and row["last"] else None

        db.close()
    except Exception:
        pass

    uptime_seconds = int(_t.monotonic() - _APP_START_TIME)

    payload = {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": "1.0.0",
        "db": db_status,
        "uptime_seconds": uptime_seconds,
        "users_total": users_total,
        "training_sessions_total": training_sessions_total,
        "last_activity_at": last_activity_at,
    }

    with _health_lock:
        _health_cache["data"] = payload
        _health_cache["ts"] = _t.monotonic()

    return jsonify(payload)


@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    update = request.get_json(force=True)
    result = handle_telegram_update(update)
    return jsonify(result)


with app.app_context():
    create_tables()

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
