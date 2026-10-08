import os
import re
import json
import secrets
import sqlite3
from datetime import datetime
from html import unescape
from urllib.parse import urlsplit
from flask import Flask, render_template, request, session, redirect, url_for
from markupsafe import Markup, escape
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename
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
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
PROJECT_DB_FILE = os.path.join(BASE_DIR, 'projects.sqlite3')
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
PROJECT_BANNER_MAX_BYTES = 8 * 1024 * 1024

CAROUSEL = [
    {"title": "\u2605 Sistem Manajemen Bisnis \u2605", "desc": "Platform terintegrasi untuk operasional dan pengambilan keputusan yang lebih cepat.", "hp": 90, "mode": "text", "image": "", "link": "", "primary": "#d4af0e", "secondary": "#0d1b4c", "text": "#0d1b4c"},
    {"title": "\u2605 Aplikasi Web & Mobile \u2605", "desc": "Produk digital custom yang responsif, cepat, dan mudah digunakan klien.", "hp": 85, "mode": "text", "image": "", "link": "", "primary": "#d4af0e", "secondary": "#0d1b4c", "text": "#0d1b4c"},
    {"title": "\u2605 Infrastruktur Jaringan \u2605", "desc": "Solusi jaringan andal untuk mendukung skala bisnis yang terus bertumbuh.", "hp": 95, "mode": "text", "image": "", "link": "", "primary": "#d4af0e", "secondary": "#0d1b4c", "text": "#0d1b4c"},
]

COLOR_DEFAULTS = {"primary": "#d4af0e", "secondary": "#0d1b4c", "text": "#0d1b4c",
                  "hero_desc": "#ffffff", "about_desc": "#d4af0e"}
HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# Carousel auto-rotate interval in seconds.
INTERVAL_MIN = 15
INTERVAL_MAX = 86400
INTERVAL_DEFAULT = 15


def _clean_interval(value):
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return INTERVAL_DEFAULT
    return max(INTERVAL_MIN, min(INTERVAL_MAX, seconds))


# Site theme presets. The active public theme is the admin-controlled default.
THEMES = ("retro", "modern", "professional")
THEME_DEFAULT = "retro"


def _clean_theme(value):
    v = (value or "").strip().lower()
    return v if v in THEMES else THEME_DEFAULT


def _clean_color(value, default):
    v = (value or "").strip()
    return v if HEX_RE.match(v) else default


def _clean_slide_link(value):
    link = (value or "").strip()
    try:
        parsed = urlsplit(link)
    except ValueError:
        return ""
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return link
    if not parsed.scheme and not parsed.netloc and (link.startswith("/") and not link.startswith("//") or link.startswith("#")):
        return link
    return ""


def _hex_to_rgba(value, alpha=1.0):
    v = (value or "").strip().lstrip("#")
    if len(v) == 3:
        v = "".join(ch * 2 for ch in v)
    if len(v) != 6:
        v = "d4af0e"
    try:
        r, g, b = int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    except ValueError:
        r, g, b = 212, 175, 14
    try:
        a = max(0.0, min(1.0, float(alpha)))
    except (TypeError, ValueError):
        a = 1.0
    return "rgba(%d, %d, %d, %s)" % (r, g, b, a)

REPO_STATUS = ("active", "beta", "wip", "archived")

CONTACT_DEFAULTS = {
    "whatsapp": "6281234567890",
    "email": "hello@gembong-it.com",
    "phone": "+62 812-3456-7890",
    "address": "Yogyakarta, Indonesia",
    "instagram": "https://instagram.com/gembong.it",
    "linkedin": "https://linkedin.com/company/gembong-it",
}

CONTENT_DEFAULTS = {
    "hero_desc": "Kami membantu bisnis Anda bertransformasi digital lewat pengembangan sistem, aplikasi, dan infrastruktur jaringan yang cepat, andal, dan tepat guna.",
    "hero_desc_color": "#ffffff",
    "about_desc": "Kami adalah mitra digital yang mengubah tantangan teknologi menjadi solusi nyata. Dengan semangat inovasi dan dedikasi tinggi, kami menghadirkan layanan information technology yang cepat, andal, dan tepat guna mulai dari pengembangan sistem, infrastruktur jaringan, hingga solusi digital yang disesuaikan dengan kebutuhan bisnis Anda. Bersama Gembong Information Technology, setiap langkah menuju transformasi digital menjadi lebih mudah, efisien, dan penuh keyakinan.",
    "about_desc_color": "#d4af0e",
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


def _connect_projects_db():
    connection = sqlite3.connect(PROJECT_DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            position INTEGER PRIMARY KEY,
            project_json TEXT NOT NULL
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    return connection


def migrate_json_to_sqlite():
    """Import existing site and authentication JSON once, without deleting it."""
    connection = _connect_projects_db()
    try:
        with connection:
            for key, path in (("site_data", DATA_FILE), ("admin_auth", AUTH_FILE)):
                marker = f"{key}_migrated"
                done = connection.execute(
                    "SELECT value FROM app_meta WHERE key = ?", (marker,)
                ).fetchone()
                if done:
                    continue
                if os.path.isfile(path):
                    with open(path, "r", encoding="utf-8") as source:
                        imported = json.load(source)
                    connection.execute(
                        "INSERT OR IGNORE INTO app_data(key, value) VALUES (?, ?)",
                        (key, json.dumps(imported, ensure_ascii=False)),
                    )
                connection.execute(
                    "INSERT OR REPLACE INTO app_meta(key, value) VALUES (?, '1')",
                    (marker,),
                )
    finally:
        connection.close()


def _load_app_value(key):
    migrate_json_to_sqlite()
    connection = _connect_projects_db()
    try:
        row = connection.execute(
            "SELECT value FROM app_data WHERE key = ?", (key,)
        ).fetchone()
        return json.loads(row["value"]) if row else None
    finally:
        connection.close()


def _save_app_value(key, value):
    migrate_json_to_sqlite()
    connection = _connect_projects_db()
    try:
        with connection:
            connection.execute(
                "INSERT OR REPLACE INTO app_data(key, value) VALUES (?, ?)",
                (key, json.dumps(value, ensure_ascii=False)),
            )
    finally:
        connection.close()


def _normalize_project(project):
    if not isinstance(project, dict):
        project = {}
    normalized = dict(project)
    normalized["name"] = str(normalized.get("name") or "Untitled Project")
    normalized["description"] = str(normalized.get("description") or "")
    normalized["type"] = str(normalized.get("type") or "Software").strip()
    normalized["detail_markdown"] = str(normalized.get("detail_markdown") or "").strip()
    normalized["banner"] = str(normalized.get("banner") or "")
    normalized["featured"] = bool(normalized.get("featured", False))
    normalized["repo_url"] = str(normalized.get("repo_url") or "")
    normalized["demo_url"] = str(normalized.get("demo_url") or "")
    normalized["status"] = normalized.get("status") if normalized.get("status") in REPO_STATUS else "active"
    normalized["tags"] = normalized.get("tags") if isinstance(normalized.get("tags"), list) else []
    stack = normalized.get("tech_stack", [])
    if isinstance(stack, str):
        stack = [item.strip() for item in stack.split(",") if item.strip()]
    normalized["tech_stack"] = stack if isinstance(stack, list) else []
    return normalized


def _order_projects(projects):
    """Put every admin-selected featured project first, preserving order."""
    return sorted(projects, key=lambda project: not project.get("featured", False))


def _get_projects():
    data = load_data()
    connection = _connect_projects_db()
    try:
        rows = connection.execute(
            "SELECT project_json FROM projects ORDER BY position"
        ).fetchall()
        migrated = connection.execute(
            "SELECT value FROM app_meta WHERE key = 'projects_migrated'"
        ).fetchone()
        if not migrated:
            if not rows and data.get("projects"):
                for position, project in enumerate(data["projects"]):
                    connection.execute(
                        "INSERT INTO projects(position, project_json) VALUES (?, ?)",
                        (position, json.dumps(_normalize_project(project), ensure_ascii=False)),
                    )
                connection.commit()
                rows = connection.execute(
                    "SELECT project_json FROM projects ORDER BY position"
                ).fetchall()
            connection.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES ('projects_migrated', '1')"
            )
            connection.commit()
        return [_normalize_project(json.loads(row["project_json"])) for row in rows]
    finally:
        connection.close()


def _save_projects(projects):
    connection = _connect_projects_db()
    try:
        with connection:
            connection.execute("DELETE FROM projects")
            connection.executemany(
                "INSERT INTO projects(position, project_json) VALUES (?, ?)",
                [(i, json.dumps(_normalize_project(project), ensure_ascii=False))
                 for i, project in enumerate(projects)],
            )
            connection.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES ('projects_migrated', '1')"
            )
    finally:
        connection.close()


def load_data():
    data = _load_app_value("site_data")
    if data is None:
        data = {"carousel": json.loads(json.dumps(CAROUSEL)), "projects": [],
                "messages": [], "contact": json.loads(json.dumps(CONTACT_DEFAULTS)),
                "carousel_interval": INTERVAL_DEFAULT, "theme": THEME_DEFAULT}
        save_data(data)
        return data
    if not isinstance(data, dict):
        data = {}
    if not isinstance(data.get("carousel"), list):
        data["carousel"] = json.loads(json.dumps(CAROUSEL))
    for slide in data["carousel"]:
        if isinstance(slide, dict):
            slide["primary"] = _clean_color(slide.get("primary"), COLOR_DEFAULTS["primary"])
            slide["secondary"] = _clean_color(slide.get("secondary"), COLOR_DEFAULTS["secondary"])
            slide["text"] = _clean_color(slide.get("text"), COLOR_DEFAULTS["text"])
            slide["hero_desc"] = _clean_color(slide.get("hero_desc"), COLOR_DEFAULTS["hero_desc"])
            slide["about_desc"] = _clean_color(slide.get("about_desc"), COLOR_DEFAULTS["about_desc"])
    data["carousel_interval"] = _clean_interval(data.get("carousel_interval"))
    data["theme"] = _clean_theme(data.get("theme"))
    if not isinstance(data.get("projects"), list):
        data["projects"] = []
    if data["projects"]:
        selected_ids = {id(project) for project in data["projects"]
                        if isinstance(project, dict) and project.get("featured")}
        if not selected_ids and isinstance(data["projects"][0], dict):
            selected_ids.add(id(data["projects"][0]))
        data["projects"] = [dict(project, featured=(id(project) in selected_ids))
                            if isinstance(project, dict) else project for project in data["projects"]]
    for project in data["projects"]:
        if isinstance(project, dict):
            project["type"] = str(project.get("type") or "Software").strip()
            project["detail_markdown"] = str(project.get("detail_markdown") or "").strip()
            stack = project.get("tech_stack", [])
            if isinstance(stack, str):
                stack = [item.strip() for item in stack.split(",") if item.strip()]
            project["tech_stack"] = stack if isinstance(stack, list) else []
    if not isinstance(data.get("messages"), list):
        data["messages"] = []
    content = data.get("content")
    if not isinstance(content, dict):
        content = {}
    merged_content = dict(CONTENT_DEFAULTS)
    merged_content.update({k: v for k, v in content.items() if k in CONTENT_DEFAULTS and isinstance(v, str)})
    for field in ("hero_desc_color", "about_desc_color"):
        merged_content[field] = _clean_color(merged_content[field], CONTENT_DEFAULTS[field])
    data["content"] = merged_content
    contact = data.get("contact")
    if not isinstance(contact, dict):
        data["contact"] = json.loads(json.dumps(CONTACT_DEFAULTS))
    else:
        merged = json.loads(json.dumps(CONTACT_DEFAULTS))
        merged.update({k: (v if isinstance(v, str) else "") for k, v in contact.items() if k in merged})
        data["contact"] = merged
    return data


def save_data(data):
    _save_app_value("site_data", data)


def load_auth():
    auth = _load_app_value("admin_auth")
    if auth is None:
        auth = {
            "username": os.environ.get('GEMBONG_ADMIN_USER', 'admin'),
            "password_hash": generate_password_hash(os.environ.get('GEMBONG_ADMIN_PASS', 'gembong2024')),
        }
        save_auth(auth)
        return auth
    # Migrate a legacy plaintext "password" field to a hash on first load.
    if "password" in auth and "password_hash" not in auth:
        auth["password_hash"] = generate_password_hash(str(auth.pop("password")))
        _write_json(AUTH_FILE, auth)
    return auth


def save_auth(auth):
    _save_app_value("admin_auth", auth)


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
SLIDE_KEY_RE = re.compile(r"^slides\[([^\]]*)\]\[(title|desc|hp|mode|image|link|primary|secondary|text|hero_desc|about_desc)\]$")


def collect_slides(form, files=None):
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
        slide = {
            "title": (card.get("title") or "").strip(),
            "desc": (card.get("desc") or "").strip(),
            "hp": hp if hp_raw else 80,
            "mode": mode,
            "image": (card.get("image") or "").strip() if mode == "image" else "",
            "link": _clean_slide_link(card.get("link")),
            "primary": _clean_color(card.get("primary"), COLOR_DEFAULTS["primary"]),
            "secondary": _clean_color(card.get("secondary"), COLOR_DEFAULTS["secondary"]),
            "text": _clean_color(card.get("text"), COLOR_DEFAULTS["text"]),
            "hero_desc": _clean_color(card.get("hero_desc"), COLOR_DEFAULTS["hero_desc"]),
            "about_desc": _clean_color(card.get("about_desc"), COLOR_DEFAULTS["about_desc"]),
        }
        uploaded = (files or {}).get(f"slides[{token}][image_file]")
        if uploaded and uploaded.filename:
            filename = secure_filename(uploaded.filename)
            extension = os.path.splitext(filename)[1].lower()
            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValueError("Format gambar harus JPG, PNG, GIF, atau WEBP.")
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            stored_name = f"{secrets.token_hex(16)}{extension}"
            uploaded.save(os.path.join(UPLOAD_FOLDER, stored_name))
            slide["image"] = f"/static/uploads/{stored_name}"
        carousel.append(slide)
    return carousel


REPO_KEY_RE = re.compile(r"^repos\[([^\]]*)\]\[(name|description|type|repo_url|demo_url|tags|tech_stack|detail_markdown|banner|featured|status)\]$")


def collect_projects(form, files=None, existing_projects=None):
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
    existing_projects = existing_projects or []
    for position, token in enumerate(order):
        card = cards[token]
        name = (card.get("name") or "").strip()
        description = (card.get("description") or "").strip()
        project_type = (card.get("type") or "Software").strip() or "Software"
        detail_markdown = (card.get("detail_markdown") or "").strip()
        repo_url = (card.get("repo_url") or "").strip()
        demo_url = (card.get("demo_url") or "").strip()
        status = (card.get("status") or "").strip().lower()
        if status not in REPO_STATUS:
            status = "active"
        tags = [t.strip() for t in (card.get("tags") or "").split(",") if t.strip()][:8]
        tech_stack = [t.strip() for t in (card.get("tech_stack") or "").split(",") if t.strip()][:12]
        banner = (card.get("banner") or "").strip()
        featured = (card.get("featured") or "").strip().lower() in ("1", "true", "on", "yes")
        try:
            original_position = int(token)
        except ValueError:
            original_position = position
        if original_position < len(existing_projects) and not banner:
            banner = existing_projects[original_position].get("banner", "")
        uploaded = (files or {}).get(f"repos[{token}][banner_file]")
        if uploaded and uploaded.filename:
            extension = os.path.splitext(secure_filename(uploaded.filename))[1].lower()
            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValueError("Banner harus berupa JPG, PNG, GIF, atau WEBP.")
            uploaded.stream.seek(0, os.SEEK_END)
            file_size = uploaded.stream.tell()
            uploaded.stream.seek(0)
            if file_size > PROJECT_BANNER_MAX_BYTES:
                raise ValueError("Ukuran banner maksimal 8 MB.")
            try:
                image = Image.open(uploaded.stream)
                image.verify()
                width, height = image.size
            except (UnidentifiedImageError, OSError, ValueError):
                raise ValueError("File banner bukan gambar yang valid.")
            finally:
                uploaded.stream.seek(0)
            if height == 0 or abs(width / height - 16 / 9) > 0.01:
                raise ValueError("Rasio banner harus 16:9.")
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            stored_name = f"project-{secrets.token_hex(16)}{extension}"
            uploaded.save(os.path.join(UPLOAD_FOLDER, stored_name))
            banner = f"/static/uploads/{stored_name}"
        if not (name or description or repo_url):
            continue
        projects.append({
            "name": name or "Untitled Project",
            "description": description,
            "type": project_type[:60],
            "detail_markdown": detail_markdown[:12000],
            "banner": banner,
            "featured": featured,
            "repo_url": repo_url,
            "demo_url": demo_url,
            "tags": tags,
            "tech_stack": tech_stack,
            "status": status,
        })
    return projects


def _render_admin(message=None, error=None, active_tab="carousel"):
    data = load_data()
    projects = _get_projects()
    return render_template(
        "admin.html",
        slides=data["carousel"],
        projects=projects,
        messages=data.get("messages", []),
        contact=data["contact"],
        content=data["content"],
        carousel_interval=data["carousel_interval"],
        interval_min=INTERVAL_MIN,
        interval_max=INTERVAL_MAX,
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
    return render_template("index.html", carousel=data["carousel"], contact=data["contact"], content=data["content"],
                           carousel_interval=data["carousel_interval"])


@app.route("/projects")
def projects():
    raw_projects = _get_projects()
    selected = [project for project in raw_projects if project.get("featured")]
    if not selected and raw_projects:
        selected = [raw_projects[0]]
    featured = _order_projects(selected)
    other = [project for project in raw_projects if project not in featured]
    ordered = featured + other
    return render_template("projects.html", projects=ordered, featured_projects=featured, other_projects=other)


@app.route("/projects/<int:project_index>")
def project_detail(project_index):
    projects = _order_projects(_get_projects())
    if project_index < 0 or project_index >= len(projects):
        return render_template("project_detail.html", project=None, project_index=project_index, projects=projects), 404
    return render_template("project_detail.html", project=projects[project_index], project_index=project_index, projects=projects)


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
app.jinja_env.filters["hexa"] = _hex_to_rgba

# Tech-stack badge icons via Devicon CDN. Entries without a reliable icon
# (Adobe suite, Flask, AMD, ...) fall back to an abbreviation mark instead.
DEVICON_BASE = "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/"

TECH_BADGES = (
    ("typescript", "typescript/typescript-original.svg", "#3178C6", "TS"),
    ("javascript", "javascript/javascript-original.svg", "#F7DF1E", "JS"),
    ("node", "nodejs/nodejs-original.svg", "#339933", "Node"),
    ("express", "express/express-original.svg", "#000000", "Ex"),
    ("python", "python/python-original.svg", "#3776AB", "Py"),
    ("dart", "dart/dart-original.svg", "#0175C2", "Dart"),
    ("flutter", "flutter/flutter-original.svg", "#02569B", "Fl"),
    ("php", "php/php-original.svg", "#777BB4", "PHP"),
    ("laravel", "laravel/laravel-original.svg", "#FF2D20", "Lv"),
    ("c++", "cplusplus/cplusplus-original.svg", "#00599C", "C++"),
    ("c#", "csharp/csharp-original.svg", "#239120", "C#"),
    (".net", "dotnetcore/dotnetcore-original.svg", "#512BD4", ".NET"),
    ("dotnet", "dotnetcore/dotnetcore-original.svg", "#512BD4", ".NET"),
    ("html", "html5/html5-original.svg", "#E34F26", "HTML"),
    ("css", "css3/css3-original.svg", "#1572B6", "CSS"),
    ("react", "react/react-original.svg", "#61DAFB", "Re"),
    ("vue", "vuejs/vuejs-original.svg", "#4FC08D", "Vue"),
    ("angular", "angular/angular-original.svg", "#DD0031", "Ng"),
    ("mysql", "mysql/mysql-original.svg", "#4479A1", "My"),
    ("postgres", "postgresql/postgresql-original.svg", "#4169E1", "Pg"),
    ("mongo", "mongodb/mongodb-original.svg", "#47A248", "Mg"),
    ("firebase", "firebase/firebase-plain.svg", "#FFCA28", "Fb"),
    ("blender", "blender/blender-original.svg", "#E87D0D", "Bl"),
    ("git", "git/git-original.svg", "#F05032", "Git"),
    ("godot", "godot/godot-original.svg", "#478CBF", "Gd"),
    ("docker", "docker/docker-original.svg", "#2496ED", "Dk"),
    ("tailwind", "tailwindcss/tailwindcss-original.svg", "#06B6D4", "TW"),
    ("java", "java/java-original.svg", "#007396", "Ja"),
    ("kotlin", "kotlin/kotlin-original.svg", "#7F52FF", "Kt"),
    ("swift", "swift/swift-original.svg", "#F05138", "Sw"),
    ("rust", "rust/rust-original.svg", "#131313", "Rs"),
    ("golang", "go/go-original-wordmark.svg", "#00ADD8", "Go"),
    ("figma", "figma/figma-original.svg", "#F24E1E", "Fi"),
    ("after effect", "", "#9999FF", "Ae"),
    ("illustrator", "", "#FF9A00", "Ai"),
    ("lightroom", "", "#31A8FF", "Lr"),
    ("photoshop", "", "#31A8FF", "Ps"),
    ("premiere", "", "#9999FF", "Pr"),
    ("adobe", "", "#FA0F00", "Ad"),
    ("flask", "", "#10131A", "Fl"),
    ("amd", "", "#ED1C24", "AMD"),
)


def _tech_badge(value):
    label = str(value or "").strip()
    key = label.lower()
    for needle, icon, color, mark in TECH_BADGES:
        if needle in key:
            return {
                "label": label,
                "icon": DEVICON_BASE + icon if icon else "",
                "color": color,
                "mark": mark,
            }
    if key in ("c", "c language"):
        return {"label": label, "icon": DEVICON_BASE + "c/c-original.svg",
                "color": "#A8B9CC", "mark": "C"}
    return {"label": label, "icon": "", "color": "#64748B",
            "mark": (label[:2] or "?").upper()}


app.jinja_env.filters["tech_badge"] = _tech_badge


def _safe_markdown(value):
    """Render a small, safe Markdown subset for optional project stories."""
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return Markup("")

    def inline(raw):
        rendered = str(escape(raw))

        def image(match):
            alt = escape(unescape(match.group(1).strip()))
            target = unescape(match.group(2).strip())
            if not (target.startswith("/static/uploads/") or _clean_slide_link(target).startswith(("http://", "https://"))):
                return ""
            return '<img class="story-image" src="%s" alt="%s" loading="lazy">' % (escape(target), alt)

        def link(match):
            label = unescape(match.group(1).strip())
            target = unescape(match.group(2).strip())
            clean = _clean_slide_link(target)
            if not clean or not clean.startswith(("http://", "https://", "/", "#")):
                return escape(label)
            return '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (escape(clean), escape(label))

        rendered = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", image, rendered)
        rendered = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, rendered)
        rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
        rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
        return rendered

    output = []
    in_list = False
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            if in_list:
                output.append("</ul>")
                in_list = False
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        if heading:
            if in_list:
                output.append("</ul>")
                in_list = False
            level = len(heading.group(1)) + 2
            output.append("<h%d>%s</h%d>" % (level, inline(heading.group(2)), level))
        elif bullet:
            if not in_list:
                output.append("<ul>")
                in_list = True
            output.append("<li>%s</li>" % inline(bullet.group(1)))
        else:
            if in_list:
                output.append("</ul>")
                in_list = False
            output.append("<p>%s</p>" % inline(stripped))
    if in_list:
        output.append("</ul>")
    return Markup("\n".join(output))


app.jinja_env.filters["safe_markdown"] = _safe_markdown


@app.context_processor
def inject_site_theme():
    try:
        data = load_data()
        theme = data.get("theme", THEME_DEFAULT)
    except Exception:
        theme = THEME_DEFAULT
    return {"site_theme": theme, "themes": THEMES}


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
                               content=CONTENT_DEFAULTS,
                               carousel_interval=INTERVAL_DEFAULT, interval_min=INTERVAL_MIN,
                               interval_max=INTERVAL_MAX,
                               error=error, message=None, active_tab="carousel")

    if request.method == "POST":
        return redirect(url_for("admin"))
    return _render_admin()


@app.route("/admin/save", methods=["POST"])
def admin_save():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    try:
        carousel = collect_slides(request.form, request.files)
    except ValueError as exc:
        return _render_admin(error=str(exc), active_tab="carousel")
    if not carousel:
        return _render_admin(
            error="No slides found in the form, nothing was saved.", active_tab="carousel")

    data = load_data()
    data["carousel"] = carousel
    data["carousel_interval"] = _clean_interval(request.form.get("carousel_interval"))
    data["content"] = {
        "hero_desc": (request.form.get("hero_desc") or "").strip() or CONTENT_DEFAULTS["hero_desc"],
        "about_desc": (request.form.get("about_desc") or "").strip() or CONTENT_DEFAULTS["about_desc"],
    }
    data["theme"] = _clean_theme(request.form.get("theme"))
    save_data(data)
    return _render_admin(message="Appearance updated successfully!", active_tab="appearance")


@app.route("/admin/projects/save", methods=["POST"])
def admin_projects_save():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    existing_projects = _get_projects()
    try:
        projects = collect_projects(request.form, request.files, existing_projects)
    except ValueError as exc:
        return _render_admin(error=str(exc), active_tab="projects")
    _save_projects(projects)
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


@app.route("/admin/appearance/save", methods=["POST"])
def admin_appearance_save():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    data = load_data()
    data["theme"] = _clean_theme(request.form.get("theme"))
    save_data(data)
    return _render_admin(message="Tema default berhasil diperbarui.", active_tab="appearance")


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
