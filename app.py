from flask import Flask, render_template, jsonify, request
from config import Config
from database import create_tables
from routes.chat import chat_bp
from routes.auth import auth_bp
from bot import handle_telegram_update

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(chat_bp)
app.register_blueprint(auth_bp)


@app.route('/')
def index():
    return render_template('app.html')


@app.route('/api/v1/health')
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    update = request.get_json(force=True)
    result = handle_telegram_update(update)
    return jsonify(result)


with app.app_context():
    create_tables()

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
