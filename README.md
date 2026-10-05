# Gembong IT

Website company profile Gembong Information Technology, dibangun dengan Flask, Jinja, CSS, dan JavaScript. Konten situs disimpan dalam `data.json`; gambar unggahan ada di `static/uploads/`.

## Prasyarat

- Python 3.10 atau lebih baru
- `pip`
- Koneksi internet saat membuka situs, karena UI memuat Tailwind melalui CDN

## Instalasi lokal

1. Clone repository dan masuk ke direktori proyek:

   ```bash
   git clone https://github.com/asda1-max/gembong-compra.git
   cd gembong-compra
   ```

   Jika proyek sudah ada di komputer, cukup buka direktori tersebut.

2. Buat dan aktifkan virtual environment:

   Windows PowerShell:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instal Flask:

   ```bash
   python -m pip install Flask
   ```

   Werkzeug dipasang sebagai dependensi Flask. Belum ada `requirements.txt` di repository.

4. Jalankan aplikasi:

   ```bash
   python app.py
   ```

5. Buka alamat lokal yang ditampilkan Flask (umumnya `http://127.0.0.1:5000`).

Pada proses pertama, aplikasi menyiapkan berkas data dan secret key yang diperlukan jika belum tersedia. Jangan hapus atau bagikan berkas rahasia dan data admin.

## Akun admin

Buka `/admin` untuk masuk ke dashboard. Instalasi baru memakai kredensial awal `admin` / `gembong2024` kecuali environment variable `GEMBONG_ADMIN_USER` dan `GEMBONG_ADMIN_PASS` telah disetel. Ganti kredensial awal segera setelah login pertama.

Untuk deployment, set `FLASK_SECRET_KEY` ke nilai acak yang kuat serta set kredensial admin melalui environment variable sebelum aplikasi dijalankan. Jangan gunakan server development Flask untuk deployment publik.

## Struktur penting

- `app.py` — aplikasi Flask dan route
- `templates/` — halaman Jinja
- `static/theme.css`, `static/theme.js` — tema dan interaksi frontend
- `data.json` — konten situs dan konfigurasi
- `static/uploads/` — gambar yang diunggah melalui admin
- `auth.json` — data autentikasi admin; jangan dipublikasikan

## Catatan

Root `index.html` adalah salinan statis lama. Halaman utama yang disajikan Flask berasal dari `templates/index.html`.
