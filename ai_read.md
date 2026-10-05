# AI Read — Workspace Scan

> Project overview refreshed 2026-10-05 · Repo: `C:\Productivity\Coding\gembonf compra` · Branch `main` @ `490bfc8`
> Working tree was clean at scan time; HEAD tracks `origin/main`.

## 1. Project overview

**Gembong IT** is an Indonesian-language Flask/Jinja marketing site for an IT services company in Yogyakarta. The public site has a retro arcade baseline plus `modern` and `professional` themes. Frontend uses Tailwind Play CDN, custom CSS, and vanilla JavaScript. Content is stored in JSON; image uploads live under `static/uploads/`.

The app serves a home page, services/FAQ page, project listing, contact form, and session-protected admin dashboard. Root `index.html` is a legacy static copy; Flask renders `templates/index.html` for `/`.

## 2. Project files

```text
gembonf compra/
├── app.py                         # Flask app, data/auth helpers and routes
├── data.json                      # carousel, projects, messages, contact, theme
├── auth.json                      # admin account data — confidential
├── .flask_secret                  # secret key material — confidential
├── ai_read.md                     # this context document
├── index.html                     # legacy static copy, not served by Flask
├── static/theme.css               # modern/professional theme skins
├── static/theme.js                # visitor theme selector and localStorage
├── static/uploads/                # carousel image uploads
└── templates/
    ├── index.html                 # home, carousel and contact terminal
    ├── admin.html                 # login and dashboard
    ├── info.html                  # services, FAQ, contact form
    └── projects.html              # project/repository listing
```

Approximate line counts at scan: `app.py` 524; `templates/index.html` 1244; `templates/admin.html` 710; `templates/info.html` 399; `templates/projects.html` 343; `static/theme.css` 390; `static/theme.js` 57; `data.json` 66. No tracked requirements manifest, tests, CI, README, or `.gitignore` were found.

## 3. Architecture and routes

`app.py` normalizes JSON data on load. `_write_json()` writes to a temporary file, fsyncs, then atomically replaces the destination. `data.json` stores carousel, projects, messages, contact info, carousel interval, and default theme. `auth.json` stores a password hash, migrating a legacy plaintext password field if found. Secret key is read from `FLASK_SECRET_KEY` or generated and persisted in `.flask_secret`.

Public routes:
- `GET /` — home page and carousel
- `GET /projects` — project listing
- `GET /info` — services, FAQ, contact details/form
- `POST /contact` — validates name/message and stores the submission

Admin routes:
- `GET|POST /admin` — login/dashboard
- `POST /admin/save` — carousel and interval
- `POST /admin/projects/save` — project records
- `POST /admin/contact/save` — contact information
- `POST /admin/appearance/save` — default theme
- `POST /admin/password` — username/password change
- `POST /admin/messages/<index>/delete` — delete a message
- `GET /admin/logout` — clear the session

Dashboard tabs: Carousel, Projects, Appearance, Contact, Messages, Account. Form collectors group indexed slide/project fields in submitted order. Image uploads allow JPG/JPEG/PNG/GIF/WEBP and are stored with randomized names.

## 4. Current content (`data.json`)

- Carousel: 4 slides, mixed image/text modes; some titles/descriptions are empty. One uses a local upload, another an external image URL.
- Projects: 1 record: name `kontol`, description `kontil`, repository/demo URL `https://kedungwinangun.com`, tag `flask`, status `active`.
- Messages: none.
- Contact values are populated with WhatsApp, email, phone, Yogyakarta address, Instagram and LinkedIn.
- Carousel interval: 15 minutes; accepted range is 15–1440 minutes.
- Default theme: `retro`.

Review public-facing placeholder or inappropriate data before deployment.

## 5. UI behavior

- Home: hero/about, latest-project carousel, contact terminal and footer.
- Theme selector supports `retro`, `modern`, `professional`; visitor choice persists in `localStorage` key `gembong_theme` and overrides the admin default in that browser.
- Services form asynchronously posts to `/contact`.
- Tailwind Play CDN is used; it is convenient for development but not a production build pipeline.

## 6. Git state

- Remote: `https://github.com/asda1-max/gembong-compra.git`
- Branch `main`, tracking `origin/main`; current HEAD `490bfc8` (`cmt`), preceding `afecd30`, `d1f0719`, `420ee0f`.
- Working tree clean at scan time.
- `.flask_secret`, `auth.json`, and `__pycache__/app.cpython-312.pyc` are tracked. Never disclose secret/auth file contents. Remove secrets from version control and rotate credentials if repository is shared.
- Recent commits added multi-page project/services/contact features, account management, themes, and image uploads.

## 7. Security and reliability

- Direct-run app uses `debug=True` and binds `0.0.0.0:9012`; do not expose Werkzeug debugger or use this for production.
- Initial admin credentials come from `GEMBONG_ADMIN_USER` / `GEMBONG_ADMIN_PASS` only when `auth.json` is absent. Subsequent updates use the admin UI.
- Secret key is configurable/generated, but `.flask_secret` is tracked: rotate it and remove it from Git history when appropriate.
- `SESSION_COOKIE_HTTPONLY=True` and `SESSION_COOKIE_SAMESITE=Lax` are configured.
- No CSRF protection or login rate limiting was identified in reviewed routes.
- Atomic JSON replacement prevents partial-file writes but does not prevent concurrent lost updates.
- Contact messages are stored locally; no email delivery integration identified.
- Remote carousel images may expire or reject hotlinking.

## 8. Run and validate

```sh
python app.py
```

Development server binds `0.0.0.0:9012` with debug enabled. Install Flask in the active environment if needed. There is no tracked dependency pin or automated test suite; add tests for routes, auth, normalization, collectors, uploads, and contact submissions, then smoke-test browser flows.

## 9. Recommended work

1. Remove `.flask_secret` from Git tracking, rotate the key, and review/rotate admin credentials.
2. Disable debug mode outside local development and serve production through a WSGI server.
3. Add `.gitignore`; untrack bytecode and secrets.
4. Add dependency manifest and tests.
5. Review carousel/project content and verify external image availability.
6. Add CSRF protection and login throttling before public exposure.
7. Consider a production Tailwind build and a database if traffic/concurrent edits grow.
