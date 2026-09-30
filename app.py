import os
import re
import json
import secrets
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET_KEY'),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data.json')
AUTH_FILE = os.path.join(BASE_DIR, 'auth.json')

CAROUSEL = [
    {"title": "\u2605 Sistem Manajemen Bisnis \u2605", "desc": "Platform terintegrasi untuk operasional dan pengambilan keputusan yang lebih cepat.", "hp": 90, "mode": "text", "image": ""},
    {"title": "\u2605 Aplikasi Web & Mobile \u2605", "desc": "Produk digital custom yang responsif, cepat, dan mudah digunakan klien.", "hp": 85, "mode": "text", "image": ""},
    {"title": "\u2605 Infrastruktur Jaringan \u2605", "desc": "Solusi jaringan andal untuk mendukung skala bisnis yang terus bertumbuh.", "hp": 95, "mode": "text", "image": ""},
]

REPO_STATUS = ("active", "beta", "wip", "archived")

CONTACT_DEFAULTS = {
    "whatsapp": "6281234567890",
    "email": "hello@gembong-it.com",
    "phone": "+62 812-3456-7890",
    "address": "Yogyakarta, Indonesia",
    "instagram": "https://instagram.com/gembong.it",
    "linkedin": "https://linkedin.com/company/gembong-it",
}


# --------------------------------------------------------------------------
# Secret key: env first, then a generated file so production is never left
# with a hardcoded, publicly known fallback.
# --------------------------------------------------------------------------
def _get_secret_key():
    env = os.environ.get('FLASK_SECRET_KEY')
    if env:
        return env
    path = os.path.join(BASE_DIR, '.flask_secret')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            stored = f.read().strip()
        if stored:
            return stored
    key = secrets.token_hex(32)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(key)
    return key


app.secret_key = _get_secret_key()


# --------------------------------------------------------------------------
# Storage helpers (atomic writes: temp file + os.replace)
# --------------------------------------------------------------------------
def _write_json(path, obj):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"carousel": json.loads(json.dumps(CAROUSEL)), "projects": [],
                "messages": [], "contact": json.loads(json.dumps(CONTACT_DEFAULTS))}
        save_data(data)
        return data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except ValueError:
            data = {}
    if not isinstance(data, dict):
        data = {}
    if not isinstance(data.get("carousel"), list):
        data["carousel"] = json.loads(json.dumps(CAROUSEL))
    if not isinstance(data.get("projects"), list):
        data["projects"] = []
    if not isinstance(data.get("messages"), list):
        data["messages"] = []
    contact = data.get("contact")
    if not isinstance(contact, dict):
        data["contact"] = json.loads(json.dumps(CONTACT_DEFAULTS))
    else:
        merged = json.loads(json.dumps(CONTACT_DEFAULTS))
        merged.update({k: (v if isinstance(v, str) else "") for k, v in contact.items() if k in merged})
        data["contact"] = merged
    return data


def save_data(data):
    _write_json(DATA_FILE, data)


def load_auth():
    if not os.path.exists(AUTH_FILE):
        auth = {
            "username": os.environ.get('GEMBONG_ADMIN_USER', 'admin'),
            "password_hash": generate_password_hash(os.environ.get('GEMBONG_ADMIN_PASS', 'gembong2024')),
        }
        _write_json(AUTH_FILE, auth)
        return auth
    with open(AUTH_FILE, 'r', encoding='utf-8') as f:
        auth = json.load(f)
    # Migrate a legacy plaintext "password" field to a hash on first load.
    if "password" in auth and "password_hash" not in auth:
        auth["password_hash"] = generate_password_hash(str(auth.pop("password")))
        _write_json(AUTH_FILE, auth)
    return auth


def save_auth(auth):
    _write_json(AUTH_FILE, auth)


def verify_login(username, password):
    auth = load_auth()
    if username != auth.get("username"):
        return False
    return check_password_hash(auth.get("password_hash", ""), password)


# --------------------------------------------------------------------------
# Form collection
# --------------------------------------------------------------------------
# Matches slides[<token>][<field>] so both server-rendered (slides[0][title])
# and JS-added (slides[3][title]) inputs are collected per card.
SLIDE_KEY_RE = re.compile(r"^slides\[([^\]]*)\]\[(title|desc|hp|mode|image)\]$")


def collect_slides(form):
    cards = {}
    order = []
    for key, values in form.lists():
        match = SLIDE_KEY_RE.match(key)
        if not match:
            continue
        token, field = match.group(1), match.group(2)
        if token not in cards:
            cards[token] = {}
            order.append(token)
        picked = next((v for v in values if v.strip()), values[0]) if values else ""
        cards[token][field] = picked

    carousel = []
    for token in order:
        card = cards[token]
        mode = (card.get("mode") or "").strip() or "text"
        hp_raw = (card.get("hp") or "").strip()
        try:
            hp = int(float(hp_raw))
        except (ValueError, OverflowError):
            hp = 80
        hp = max(0, min(100, hp))
        carousel.append({
            "title": (card.get("title") or "").strip(),
            "desc": (card.get("desc") or "").strip(),
            "hp": hp if hp_raw else 80,
            "mode": mode,
            "image": (card.get("image") or "").strip() if mode == "image" else "",
        })
    return carousel


REPO_KEY_RE = re.compile(r"^repos\[([^\]]*)\]\[(name|description|repo_url|demo_url|tags|status)\]$")


def collect_projects(form):
    cards = {}
    order = []
    for key, values in form.lists():
        match = REPO_KEY_RE.match(key)
        if not match:
            continue
        token, field = match.group(1), match.group(2)
        if token not in cards:
            cards[token] = {}
            order.append(token)
        picked = next((v for v in values if v.strip()), values[0]) if values else ""
        cards[token][field] = picked

    projects = []
    for token in order:
        card = cards[token]
        name = (card.get("name") or "").strip()
        description = (card.get("description") or "").strip()
        repo_url = (card.get("repo_url") or "").strip()
        demo_url = (card.get("demo_url") or "").strip()
        status = (card.get("status") or "").strip().lower()
        if status not in REPO_STATUS:
            status = "active"
        tags = [t.strip() for t in (card.get("tags") or "").split(",") if t.strip()][:8]
        if not (name or description or repo_url):
            continue
        projects.append({
            "name": name or "Untitled Project",
            "description": description,
            "repo_url": repo_url,
            "demo_url": demo_url,
            "tags": tags,
            "status": status,
        })
    return projects


def _render_admin(message=None, error=None, active_tab="carousel"):
    data = load_data()
    return render_template(
        "admin.html",
        slides=data["carousel"],
        projects=data["projects"],
        messages=data.get("messages", []),
        contact=data["contact"],
        message=message,
        error=error,
        active_tab=active_tab,
    )


# --------------------------------------------------------------------------
# Public routes
# --------------------------------------------------------------------------
@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", carousel=data["carousel"], contact=data["contact"])


@app.route("/projects")
def projects():
    data = load_data()
    return render_template("projects.html", projects=data["projects"])


@app.route("/info")
def info():
    data = load_data()
    return render_template("info.html", contact=data["contact"])


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()

    if not (name and message):
        return {"ok": False, "error": "Nama dan pesan wajib diisi."}, 400

    data = load_data()
    data.setdefault("messages", []).append({
        "name": name,
        "email": email,
        "phone": phone,
        "message": message,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_data(data)
    return {"ok": True, "message": "Pesan terkirim! Kami akan menghubungi Anda segera."}


CONTACT_FIELDS = ("whatsapp", "email", "phone", "address", "instagram", "linkedin")


def collect_contact(form):
    contact = {}
    for field in CONTACT_FIELDS:
        contact[field] = (form.get(field, "") or "").strip()
    raw = (form.get("whatsapp", "") or "").strip()
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    contact["whatsapp_digits"] = digits
    return {k: contact[k] for k in CONTACT_FIELDS}


def _wa_digits(value):
    digits = re.sub(r"\D", "", value or "")
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    return digits


app.jinja_env.filters["wa_digits"] = _wa_digits


# --------------------------------------------------------------------------
# Admin routes
# --------------------------------------------------------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("logged_in"):
        error = None
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            if verify_login(username, password):
                session.clear()
                session["logged_in"] = True
                session["admin_user"] = username
                return redirect(url_for("admin"))
            error = "Invalid credentials"
        return render_template("admin.html", slides=[], projects=[], messages=[], contact={},
                               error=error, message=None, active_tab="carousel")

    if request.method == "POST":
        return redirect(url_for("admin"))
    return _render_admin()


@app.route("/admin/save", methods=["POST"])
def admin_save():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    carousel = collect_slides(request.form)
    if not carousel:
        return _render_admin(
            error="No slides found in the form, nothing was saved.", active_tab="carousel")

    data = load_data()
    data["carousel"] = carousel
    save_data(data)
    return _render_admin(message="Carousel updated successfully!", active_tab="carousel")


@app.route("/admin/projects/save", methods=["POST"])
def admin_projects_save():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    data = load_data()
    data["projects"] = collect_projects(request.form)
    save_data(data)
    return _render_admin(message="Projects updated successfully!", active_tab="projects")


@app.route("/admin/password", methods=["POST"])
def admin_password():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    auth = load_auth()
    current = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")
    new_username = request.form.get("username", "").strip()

    if not check_password_hash(auth.get("password_hash", ""), current):
        return _render_admin(error="Password saat ini salah.", active_tab="account")

    changed = []
    if new_username and new_username != auth.get("username"):
        auth["username"] = new_username
        session["admin_user"] = new_username
        changed.append("username")

    if new_password:
        if len(new_password) < 6:
            return _render_admin(error="Password baru minimal 6 karakter.", active_tab="account")
        if new_password != confirm:
            return _render_admin(error="Konfirmasi password tidak cocok.", active_tab="account")
        auth["password_hash"] = generate_password_hash(new_password)
        changed.append("password")

    if not changed:
        return _render_admin(error="Tidak ada perubahan untuk disimpan.", active_tab="account")

    save_auth(auth)
    return _render_admin(message="Akun berhasil diperbarui.", active_tab="account")


@app.route("/admin/contact/save", methods=["POST"])
def admin_contact_save():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    data = load_data()
    data["contact"] = collect_contact(request.form)
    save_data(data)
    return _render_admin(message="Contact info updated successfully!", active_tab="contact")


@app.route("/admin/messages/<int:index>/delete", methods=["POST"])
def admin_message_delete(index):
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    data = load_data()
    messages = data.get("messages", [])
    if 0 <= index < len(messages):
        messages.pop(index)
        data["messages"] = messages
        save_data(data)
        return _render_admin(message="Pesan dihapus.", active_tab="messages")
    return _render_admin(error="Pesan tidak ditemukan.", active_tab="messages")


@app.route("/admin/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("admin_user", None)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9012)
