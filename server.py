from flask import Flask, jsonify, request, render_template_string, redirect, session, send_from_directory
import json, os, uuid, datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Секретный ключ для сессий (авторизации в админке)
app.secret_key = 'vakson_time_system_2026'
KEYS_FILE = 'keys.json'
ADMIN_PASSWORD = 'Vakson'
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- ЛОГИКА БД ---
def load_db():
    if not os.path.exists(KEYS_FILE):
        return {"licenses": {}, "logs": [], "design": {"title": "HUNTER PRO", "notification": "", "logo": ""}}
    try:
        with open(KEYS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"licenses": {}, "logs": [], "design": {"title": "HUNTER PRO", "notification": "", "logo": ""}}

def save_db(data):
    with open(KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_log(message):
    db = load_db()
    now = datetime.datetime.now().strftime("%d.%m %H:%M")
    db["logs"].insert(0, f"[{now}] {message}")
    db["logs"] = db["logs"][:50]
    save_db(db)

# --- РОУТЫ ---
@app.route('/')
def index():
    return redirect('/admin_panel')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect('/admin_panel')
        return "❌ Ошибка! <a href='/login'>Назад</a>"
    return '''<body style="background:#0d0d12; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
        <form method="post" style="background:#16161d; padding:40px; border-radius:15px; border:1px solid #333; width:320px; text-align:center;">
            <h2 style="color:#ffcc00;">VAKSON CRM</h2>
            <input type="password" name="password" placeholder="Пароль" autofocus style="padding:12px; width:100%; margin:15px 0; background:#08080b; border:1px solid #444; color:white; border-radius:8px;">
            <button type="submit" style="width:100%; padding:12px; background:#ffcc00; border:none; font-weight:bold; border-radius:8px; cursor:pointer;">ВОЙТИ</button>
        </form></body>'''

@app.route('/admin_panel')
def admin():
    if not session.get('logged_in'): return redirect('/login')
    db = load_db()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Vakson Control</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #08080b; color: #e0e0e0; font-family: sans-serif; }
            .navbar { background: #111116; border-bottom: 1px solid #222; }
            .card { background: #111116; border: 1px solid #222; border-radius: 12px; margin-top:20px; }
            .nav-tabs .nav-link { color: #888; border: none; padding: 12px 25px; }
            .nav-tabs .nav-link.active { background: transparent; color: #ffcc00; border-bottom: 3px solid #ffcc00; font-weight: bold; }
            .btn-gold { background: #ffcc00; color: #000; font-weight: bold; }
            .log-item { font-family: monospace; font-size: 0.85em; border-bottom: 1px solid #222; padding: 5px; color: #888; }
            .preview-img { max-width: 80px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark"><div class="container d-flex justify-content-between">
            <span class="navbar-brand fw-bold text-warning">🛡️ VAKSON MANAGEMENT</span>
            <a href="/logout" class="btn btn-outline-danger btn-sm">Выйти</a>
        </div></nav>
        <div class="container mt-4">
            <ul class="nav nav-tabs" id="myTab">
                <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#keys">🔑 Ключи</button></li>
                <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#design">🎨 Дизайн</button></li>
                <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#logs">📜 Логи</button></li>
            </ul>
            <div class="tab-content pt-3">
                <div class="tab-pane fade show active" id="keys">
                    <div class="card p-4 shadow-sm">
                        <form action="/create_key" method="POST" class="row g-2 mb-4">
                            <div class="col-md-5"><input type="text" name="user" class="form-control bg-dark text-white border-secondary" placeholder="Игрок" required></div>
                            <div class="col-md-4">
                                <select name="duration" class="form-select bg-dark text-white border-secondary">
                                    <option value="1">1 День</option>
                                    <option value="7">7 Дней</option>
                                    <option value="30">30 Дней</option>
                                    <option value="9999">Навсегда</option>
                                </select>
                            </div>
                            <div class="col-md-3"><button type="submit" class="btn btn-gold w-100">СОЗДАТЬ</button></div>
                        </form>
                        <table class="table table-dark small">
                            <thead><tr><th>Игрок</th><th>Ключ</th><th>Истекает</th><th>HWID</th><th>Удалить</th></tr></thead>
                            <tbody>
                                {% for k, v in db.licenses.items() %}
                                <tr>
                                    <td>{{ v.user }}</td>
                                    <td><code class="text-warning">{{ k }}</code></td>
                                    <td>{{ v.expiry }}</td>
                                    <td class="text-secondary">{{ v.hwid or '---' }}</td>
                                    <td><a href="/delete/{{ k }}" class="btn btn-sm btn-outline-danger">🗑️</a></td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="tab-pane fade" id="design">
                    <div class="card p-4">
                        <form action="/update_design" method="POST" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label class="form-label small">Логотип бота:</label>
                                <input type="file" name="logo" class="form-control bg-dark text-white border-secondary mb-2">
                                {% if db.design.logo %}<img src="/static/{{ db.design.logo }}" class="preview-img">{% endif %}
                            </div>
                            <div class="mb-3">
                                <label class="form-label small">Заголовок бота:</label>
                                <input type="text" name="title" class="form-control bg-dark text-white border-secondary" value="{{ db.design.title }}">
                            </div>
                            <div class="mb-3">
                                <label class="form-label small">Объявление:</label>
                                <textarea name="notification" class="form-control bg-dark text-white border-secondary">{{ db.design.notification }}</textarea>
                            </div>
                            <button type="submit" class="btn btn-gold w-100">СОХРАНИТЬ</button>
                        </form>
                    </div>
                </div>
                <div class="tab-pane fade" id="logs">
                    <div class="card p-4">
                        <div style="max-height: 350px; overflow-y: auto;">
                            {% for log in db.logs %}<div class="log-item">{{ log }}</div>{% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', db=db)

# --- ОБРАБОТЧИКИ ---
@app.route('/create_key', methods=['POST'])
def create_key():
    db = load_db()
    user = request.form.get('user')
    days = int(request.form.get('duration'))
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
    if days > 1000: expiry_date = "LifeTime"
    new_k = str(uuid.uuid4()).split('-')[0].upper()
    db['licenses'][new_k] = {"user": user, "hwid": None, "expiry": expiry_date}
    save_db(db)
    add_log(f"Ключ {new_k} ({user}) выдан на {days} дн.")
    return redirect('/admin_panel')

@app.route('/check_key')
def check_key():
    key = request.args.get('key', '').upper()
    hwid = request.args.get('hwid', '')
    db = load_db()
    if key in db['licenses']:
        data = db['licenses'][key]
        if data['expiry'] != "LifeTime":
            expiry = datetime.datetime.strptime(data['expiry'], "%Y-%m-%d %H:%M")
            if datetime.datetime.now() > expiry:
                return "KEY_EXPIRED", 403
        if not data.get('hwid'):
            db['licenses'][key]['hwid'] = hwid
            save_db(db)
            return "OK", 200
        if data['hwid'] == hwid: return "OK", 200
        return "HWID_MISMATCH", 403
    return "NOT_FOUND", 404

@app.route('/get_config')
def get_config():
    db = load_db()
    return jsonify(db.get('design', {}))

@app.route('/update_design', methods=['POST'])
def update_design():
    db = load_db()
    file = request.files.get('logo')
    if file and file.filename != '':
        fname = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
        db['design']['logo'] = fname
    db['design']['title'] = request.form.get('title')
    db['design']['notification'] = request.form.get('notification')
    save_db(db)
    return redirect('/admin_panel')

@app.route('/delete/<key>')
def delete_key(key):
    db = load_db()
    db['licenses'].pop(key, None)
    save_db(db)
    return redirect('/admin_panel')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# --- ЗАПУСК (ИСПРАВЛЕНО ДЛЯ RENDER) ---
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)