import os
import json
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'gembong-it-secret-change-in-prod')

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')

CAROUSEL = [
    {"title": "\u2605 Sistem Manajemen Bisnis \u2605", "desc": "Platform terintegrasi untuk operasional dan pengambilan keputusan yang lebih cepat.", "hp": 90, "mode": "text", "image": ""},
    {"title": "\u2605 Aplikasi Web & Mobile \u2605", "desc": "Produk digital custom yang responsif, cepat, dan mudah digunakan klien.", "hp": 85, "mode": "text", "image": ""},
    {"title": "\u2605 Infrastruktur Jaringan \u2605", "desc": "Solusi jaringan andal untuk mendukung skala bisnis yang terus bertumbuh.", "hp": 95, "mode": "text", "image": ""},
]


def load_data():
    if not os.path.exists(DATA_FILE):
        save_data({"carousel": CAROUSEL})
        return {"carousel": CAROUSEL}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", carousel=data["carousel"])


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if session.get("logged_in"):
        if request.method == "POST":
            return redirect(url_for("admin_save"))
        data = load_data()
        return render_template("admin.html", slides=data["carousel"], error=None)

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == "admin" and password == "gembong2024":
            session["logged_in"] = True
            return redirect(url_for("admin"))
        error = "Invalid credentials"

    return render_template("admin.html", slides=[], error=error)


@app.route("/admin/save", methods=["POST"])
def admin_save():
    if not session.get("logged_in"):
        return redirect(url_for("admin"))

    slides_raw = request.form.getlist("slides[][title]")
    descs = request.form.getlist("slides[][desc]")
    hps = request.form.getlist("slides[][hp]")
    modes = request.form.getlist("slides[][mode]")
    images = request.form.getlist("slides[][image]")

    carousel = []
    for i in range(len(slides_raw)):
        mode = modes[i] if modes[i] else "text"
        slide = {
            "title": slides_raw[i].strip(),
            "desc": descs[i].strip() if mode == "text" else "",
            "hp": int(hps[i]) if mode == "text" and hps[i] else 80,
            "mode": mode,
            "image": images[i].strip() if mode == "image" else "",
        }
        carousel.append(slide)

    save_data({"carousel": carousel})
    return render_template("admin.html", slides=carousel, message="Carousel updated successfully!", error=None)


@app.route("/admin/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
