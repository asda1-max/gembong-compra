# AI Read - Workspace Guide

> Updated 2026-10-08 for the current workspace. This document describes tracked source files and does not include secrets or private runtime data.

## Project Overview

Gembong IT is an Indonesian-language company profile and portfolio website implemented as a Flask application with Jinja templates, vanilla JavaScript, and CSS. The visual design is retro arcade by default, with `modern` and `professional` visitor-selectable themes. Tailwind Play CDN and Google Fonts are loaded by the pages at runtime.

The app provides a public home page, project repository, services/FAQ and contact form, plus a session-protected admin dashboard. Content and admin authentication are stored in local JSON files created at runtime. Uploaded carousel images are stored under `static/uploads/`.

## Workspace Layout

```text
gembong-compra/
├── app.py                         # Flask app, storage helpers, form collectors and routes
├── ai_read.md                     # This project context document
├── README.md                      # Setup, run and deployment notes
├── requirements.txt               # Python runtime dependencies
├── index.html                     # Legacy static copy; not served by Flask
├── static/
│   ├── theme.css                  # Modern/professional theme skins and transitions
│   └── theme.js                   # Visitor theme selection and page transitions
├── templates/
│   ├── admin.html                 # Admin login and dashboard UI
│   ├── hud_navbar.html            # Shared public navigation/HUD include
│   ├── index.html                 # Flask home page, carousel and contact terminal
│   ├── info.html                  # Services, FAQ and contact form
│   └── projects.html              # Project listing, search and status filters
└── tests/
    └── test_admin_image_upload.py # unittest checks for admin image inputs and carousel output
```

Runtime files (`data.json`, `auth.json`, `.flask_secret`, and uploaded images) are intentionally ignored by Git. `.gitignore` also excludes virtual environments, Python bytecode, and pytest cache. Do not add secrets or private runtime data to documentation or version control.

## Architecture and Routes

`app.py` is a single-module Flask application. It normalizes persisted content on load and writes JSON atomically using a temporary file, `fsync`, and `os.replace`. The generated session secret is saved locally when `FLASK_SECRET_KEY` is unset. Admin passwords are hashed with Werkzeug; a legacy plaintext password field is migrated on load.

Public routes:

- `GET /` - home page and configurable carousel
- `GET /projects` - project repository listing
- `GET /info` - services, FAQ, contact details and message form
- `POST /contact` - validates name/message and stores a contact submission

Admin routes:

- `GET|POST /admin` - login or dashboard
- `POST /admin/save` - carousel, content and interval
- `POST /admin/projects/save` - project records
- `POST /admin/contact/save` - contact details
- `POST /admin/appearance/save` - default theme
- `POST /admin/password` - admin username/password change
- `POST /admin/messages/<index>/delete` - remove a stored contact message
- `GET /admin/logout` - clear admin session state

Dashboard tabs are Appearance, Projects, Contact, Messages, and Account. Appearance contains default style, Hero/About Us copy, and carousel settings in that order. Each carousel slide can optionally redirect to an HTTP(S) URL or same-site path when clicked. Carousel image uploads accept JPG/JPEG, PNG, GIF, and WEBP extensions and are saved using randomized filenames. JSON storage is suitable for a small single-instance site; atomic replacement does not prevent concurrent lost updates.

## Data and Configuration

- `data.json` is created on first use and holds carousel slides, projects, contact messages, contact details, content, carousel interval, and default theme.
- `auth.json` is created on first admin authentication load. Initial username/password come from `GEMBONG_ADMIN_USER` and `GEMBONG_ADMIN_PASS`, defaulting to `admin` / `gembong2024`; change the initial credentials immediately.
- `.flask_secret` is generated if `FLASK_SECRET_KEY` is not provided. For deployment, provide a strong `FLASK_SECRET_KEY` through the environment instead.
- Carousel interval is stored in seconds and clamped to 15-86400 seconds (15 seconds to 24 hours). Available themes are `retro`, `modern`, and `professional`.
- Current runtime content is not assumed in this document because those local files may be absent and are excluded from the tracked workspace.

## Frontend Behavior

- The public home page includes the carousel, contact terminal, boot sequence, achievements, sound effects, and scroll-based HUD progress. Carousel autoplay starts only after the carousel has entered the viewport once; it then pauses while the browser tab is hidden.
- The admin chooses the site's default visual theme. Visitors can override it per browser; `static/theme.js` stores the override under localStorage key `gembong_theme`.
- `templates/hud_navbar.html` is the shared public navigation and includes mobile-menu behavior.
- The contact form posts asynchronously to `/contact`; submissions are stored locally and do not trigger email delivery.
- Tailwind Play CDN and Google Fonts require network access. Tailwind Play CDN is convenient for development, not a production CSS build pipeline.
- Root `index.html` is a legacy static snapshot. The Flask route `/` renders `templates/index.html` instead.

## Setup, Run and Tests

Python 3.10+ and pip are expected. Create/activate a virtual environment, then install dependencies and run the application:

```sh
python -m pip install -r requirements.txt
python app.py
```

Direct execution starts Flask's development server with debug enabled, bound to `0.0.0.0:9012`. Use this only for local development; deploy through a production WSGI server and disable debug mode.

Run the existing standard-library test suite with:

```sh
python -m unittest discover -s tests
```

The tests use Flask's test client. They verify the admin image field is upload-only and that the home page does not render the removed dark image overlay. Tests may initialize local runtime JSON files if they do not already exist.

## Security and Operational Notes

- Never publish `.flask_secret`, `auth.json`, passwords, or contact submissions. Rotate credentials and session secrets if they have been exposed.
- The default initial admin password is known; change it on first login and set admin credentials through environment variables before first startup on a new deployment.
- Do not expose the development server or Werkzeug debugger to the public internet.
- Session cookies set `HttpOnly` and `SameSite=Lax`. No CSRF protection or login throttling is implemented in the reviewed routes.
- Contact messages and site content are stored in local JSON files. There is no database, email integration, or multi-process concurrency control.
- Uploaded filenames are sanitized and randomized, but file type checking is extension-based; validate uploads more strongly before accepting untrusted public traffic.

## Useful Follow-up Work

1. Use a production WSGI server, disable debug, and configure secret/admin values in the deployment environment.
2. Add CSRF protection and login throttling before public exposure.
3. Add stronger upload validation and request size limits.
4. Expand tests to cover authentication, form collectors, data normalization, contact submissions, and admin mutations.
5. Consider a database if concurrent edits or traffic outgrow local JSON storage, and a production Tailwind build if CDN dependence is undesirable.
