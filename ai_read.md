# AI Read — Workspace Scan

> Auto-generated workspace overview for AI/agent context.
> Scanned: 2026-09-26 · Repo: `C:\Productivity\Coding\gembonf compra` · Branch `main` @ `660bcc2`

---

## 1. What this project is

**Gembong IT** — a single-page marketing/landing site for an Indonesian IT services company
(Yogyakarta). Retro **pixel-art / 8-bit arcade aesthetic** (Press Start 2P font, navy + gold
palette, HP bars, scanlines, "PRESS START TO CONTINUE").

Stack: **Flask 3.1.1 (Python 3.12)** + Jinja2 templates + **Tailwind CDN** + vanilla JS.
Content (the hero carousel) is stored in a flat **`data.json`** file and edited through a
password-protected `/admin` panel.

Language of site content: **Indonesian (`lang="id"`)**.

---

## 2. File map

```
gembonf compra/
├── app.py                 # Flask app, all routes + data I/O (118 lines)
├── data.json              # Persistent store: {"carousel": [...3 slides]}
├── index.html             # LEGACY static copy (469 lines) — NOT used by Flask, still git-tracked
├── templates/
│   ├── index.html         # Public page (468 lines, Jinja)
│   └── admin.html         # Login + carousel editor (291 lines, Jinja) — MODIFIED, uncommitted
├── __pycache__/           # app.cpython-312.pyc — tracked in git (should be ignored)
└── .git/
```

| File | Lines | Role |
|---|---|---|
| `app.py` | 118 | Flask routes, auth, load/save of `data.json` |
| `templates/index.html` | 468 | Public landing page (hero, about, carousel, footer) |
| `templates/admin.html` | 291 | Admin login + slide editor (text/image modes) |
| `index.html` | 469 | Superseded static version; diverged from template version |
| `data.json` | 25 | Carousel content, currently 3 slides (slide 1 = image mode) |

**Missing:** `requirements.txt`, `README.md`, `.gitignore`, tests, CI, `Procfile`/Docker.

---

## 3. Architecture / routes

```
app.py
├── CAROUSEL                 # default slide data (3 hardcoded slides)
├── DATA_FILE                # <project>/data.json
├── load_data() / save_data()# plain json read/write, no locking, non-atomic
│
├── GET  /          → render templates/index.html(carousel)
├── GET|POST /admin → login form, or dashboard if session.logged_in
├── POST /admin/save→ parses slides from form → save_data() → re-render admin
└── GET  /admin/logout → session.pop('logged_in')
```

**Auth model:** session cookie (`FLASK_SECRET_KEY` env, fallback hardcoded
`'gembong-it-secret-change-in-prod'`, `app.py:7`). Credentials hardcoded at `app.py:88`
(`admin` / `gembong2024`). No CSRF tokens, no rate limiting, no password hashing.

**Data flow:**
1. `templates/admin.html` renders one `.slide-card` per slide with inputs named `slides[N][field]`.
2. JS can add/remove slides client-side (`ADD SLIDE` / `REMOVE`), toggle TEXT vs IMAGE mode.
3. Submit → `POST /admin/save` (`app.py:96-108`) → `collect_slides()` groups `slides[<token>][field]`
   per card → writes `data.json` → public page reads it at `/`.

---

## 4. Design system (for UI work)

- CSS vars: `--navy:#0d1b4c`, `--gold:#d4af0e`, `--gold-light:#f2c94c`, `--cream:#d9d1a8`
- Font: `'Press Start 2P'` everywhere (`font-display` / `font-script` classes)
- Tailwind loaded via `https://cdn.tailwindcss.com` (CDN, dev only — no build step)
- Reusable classes in `templates/index.html <style>`: `.pixel-btn`, `.pixel-btn-gold`,
  `.pixel-btn-glass`, `.pixel-border`, `.glass`, `.stat-box`, `.tag-pill`, `.hp-bar`,
  `.particle`, `.pixel-diamond`, `.grid-overlay`, `.scanlines`, `.cursor-blink`
- Mobile: heavy `@media(max-width:639px)` override block (lines 78–105), hamburger menu JS
- Sections: TOP HUD → NAV (sticky) → HERO (`#home`) → ABOUT (`#about`) →
  PROJECTS carousel (`#projects`, `#contact` anchor lives here) → FOOTER
- Carousel JS: `moveCarousel/goToSlide`, autoplay every 4 s, `translateX(-idx*100%)`,
  slides render `text` (title + desc + HP bar) or `image` (bg-image + dark overlay)

---

## 5. Git state

- Remote: `https://github.com/asda1-max/gembong-compra.git` · branch `main` (tracks `origin/main`)
- History (all 2026-09-25/26): `first stone → vv2 → goat → sys.moni → dad → flask integration → carousel`
- **Uncommitted — admin bug fixes (2026-09-26 session):** `app.py`, `templates/admin.html`
  - `app.py`: new `collect_slides()` parses `slides[<token>][field]` per card (see §6 FIXED-1)
  - `admin.html`: `applyMode()` disables inactive field sections; `addSlide()` emits unique
    `slides[<id>][...]` names and inserts the card **above** the button row (`#formActions`)
  - Earlier uncommitted rewrite kept: `slideCount` → `slideNextId`, `reindexSlides()` → `refreshLabels()`
- `ai_read.md` is new/untracked; `__pycache__/app.cpython-312.pyc` shows modified (recompiled)
- Line-ending warnings: LF ↔ CRLF churn on `templates/admin.html` (`core.autocrlf` in play)
- `__pycache__/app.cpython-312.pyc` is committed; no `.gitignore`

---

## 6. Verified findings (tested with Flask test client)

### ✅ FIXED-1 — Saving the admin form wiped `data.json` (data loss)
**Was:** server-rendered inputs used indexed names (`slides[0][title]`) while `app.py` read
`request.form.getlist("slides[][title]")` — a literal key match that never matched indexed
names, so clicking **SAVE CHANGES** on a fresh page erased all carousel content.

**Fix:** new `collect_slides()` in `app.py` (regex `^slides\[([^\]]*)\]\[(title|desc|hp|mode|image)\]$`)
groups submitted fields **per card token** in DOM order, accepting both indexed and legacy
empty-bracket names, with defaults for missing fields. `addSlide()` now emits unique indexed
names (`slides[<id>][field]`, id from `slideNextId`) instead of `slides[][...]`, which would
otherwise collapse all JS-added cards into one token.
Also: empty/garbage POSTs are **rejected** (error alert in dashboard) instead of writing `[]`,
and image-mode `desc` is no longer dropped on save (the admin UI offers it and the public
template renders it).

**Verified:** 26-case test suite — no-op save round-trip keeps all 3 slides, edits persist,
add/remove-slide token ordering (incl. sparse tokens), empty POST rejected without data loss,
legacy `slides[][...]` names still accepted, HP parsing (`abc`/`inf`→80, `-5`→0, `999`→100).

### ✅ FIXED-2 — Image-mode save blocked by hidden `required` inputs
**Was:** switching to IMAGE mode only added CSS `hidden` to `.text-fields`; the `required`
title/desc/hp inputs stayed in the form → browsers abort submit with *"invalid form control
... is not focusable"*, so the save button did nothing. Also, both sections submitted the
**same** field names, doubling `title`/`desc` arrays and corrupting alignment.

**Fix:** `applyMode(card, mode)` in `templates/admin.html` now hides **and `disabled`-s** the
inactive section's inputs (disabled = not submitted, barred from constraint validation).
Runs on page load for every card (fixes the pre-existing bug where a card saved in image mode
still displayed the text fields), on `setMode()`, and on `addSlide()`.

### ✅ FIXED-3 — Added slides appeared below the SAVE CHANGES button
**Was:** `addSlide()` used `form.appendChild(card)`, appending after the button row.
**Fix:** the button row has `id="formActions"` and the new card is inserted with
`form.insertBefore(card, formActions)` — cards stay above the buttons.

### 🟠 HIGH — Security posture
- Hardcoded admin password `app.py:88`; hardcoded Flask secret fallback `app.py:7`
- `app.run(debug=True)` at `app.py:118` (Werkzeug debugger = RCE risk if exposed)
- No CSRF protection on `/admin/save`; no login rate limiting; session cookie lacks
  `HttpOnly`/`SameSite` tuning (Flask defaults apply)

### 🟡 MEDIUM — Robustness
- ~~`admin_save` int()/KeyError on bad or ragged input~~ → handled by `collect_slides()` (defaults + clamp)
- `POST /admin` while logged in redirects to `admin_save` (`app.py:79-80`), which only
  accepts POST → redirect chain lands on **405** (dead branch)
- `save_data()` is non-atomic (truncate + write) — a crash mid-write corrupts `data.json`
- Root `index.html` duplicates the template and has drifted (20 insertions/21 deletions);
  it is never served — dead weight / confusion risk
- No dependency manifest: environment has Flask 3.1.1, but nothing pins it

### 🟢 LOW / nits
- Carousel `dots` NodeList is captured once (`templates/index.html:431`); fine only because
  dot count is server-rendered
- `goToSlide(i)` has no bounds guard; `total === 0` would cause `% 0` → `NaN` index
- Social links in footer are `href="#"` placeholders
- Image slide URL in `data.json` is a Brave-search proxied vecteezy thumbnail (hotlinked,
  may expire/hotlink-block)
- Tailwind Play CDN prints a console warning and is unsuitable for production

---

## 7. How to run

```powershell
pip install flask          # Python 3.12, Flask 3.1.1 observed; no requirements.txt yet
python app.py              # debug server on http://127.0.0.1:5000
```
- Public site: `/` · Admin: `/admin` (`admin` / `gembong2024`)
- Data edits persist to `data.json` immediately (no DB)

---

## 8. Suggested next steps

1. ~~Fix the save-path key mismatch~~ ✅ done (see §6 FIXED-1..3); suite of 26 checks passes
   in a temp copy (`test_save.py`, not committed). Consider committing it as a real test.
2. Add `.gitignore` (`__pycache__/`, `*.pyc`), untrack the committed `.pyc`.
3. Add `requirements.txt` (`flask==3.1.1`) and remove/rename root `index.html`.
4. Externalize credentials (`FLASK_ADMIN_USER`/`FLASK_ADMIN_PASS` env) and set a real secret key.
5. Review + commit (or revert) the now-extended uncommitted changes in `app.py` / `templates/admin.html`.
6. Smoke-test `/admin` in a real browser (mode toggle, add/remove, save) — JS changes were
   syntax-checked with `node --check` and DOM logic reviewed, but not executed in a browser.
