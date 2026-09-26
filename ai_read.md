# AI Read — Workspace Scan

> Auto-generated workspace overview for AI/agent context.
> Scanned: 2026-09-26 · Repo: `C:\Productivity\Coding\gembonf compra` · Branch `main` @ `0fc3047`
> Updated: 2026-09-26 — retro "Gembong OS" feature pass on `templates/index.html` (uncommitted).

---

## 1. What this project is

**Gembong IT** — a single-page marketing/landing site for an Indonesian IT services company
(Yogyakarta). Retro **pixel-art / 8-bit arcade aesthetic** (Press Start 2P font, navy + gold
palette, HP bars, scanlines, "PRESS START TO CONTINUE").

Stack: **Flask 3.1.1 (Python 3.12)** + Jinja2 templates + **Tailwind CDN** + vanilla JS.
Content (the hero carousel) is stored in a flat **`data.json`** file and edited through a
password-protected `/admin` panel.

Language of site content: **Indonesian (`lang="id"`)**.

**"Gembong OS" features** (added 2026-09-26, see §4a):
- **Boot sequence** on page load (typing POST log, click-to-skip, skipped for reduced-motion/JS-off)
- **Scroll = EXP** HUD bar + `ACHIEVEMENT UNLOCKED` toasts (IntersectionObserver per section)
- **8-bit SFX** via WebAudio (hover/click/achievement jingles), `SFX ON/OFF` toggle in nav (localStorage)
- **Contact terminal** — fake CLI (`help/about/services/projects/contact/hire/whoami/ls/sudo/clear`)
- **Pixel SVG sprites** — gem logo, cloud/lock, IG/IN/WA icons (no emoji, no image files)

---

## 2. File map

```
gembonf compra/
├── app.py                 # Flask app, all routes + data I/O (118 lines)
├── data.json              # Persistent store: {"carousel": [...4 slides, user-managed]}
├── index.html             # LEGACY static copy (469 lines) — NOT used by Flask, still git-tracked
├── templates/
│   ├── index.html         # Public page (1006 lines, Jinja) — retro features added here
│   └── admin.html         # Login + carousel editor (291 lines, Jinja) — MODIFIED, uncommitted
├── __pycache__/           # app.cpython-312.pyc — tracked in git (should be ignored)
└── .git/
```

| File | Lines | Role |
|---|---|---|
| `app.py` | 118 | Flask routes, auth, load/save of `data.json` |
| `templates/index.html` | 1006 | Public landing page (hero, about, carousel, terminal, footer) |
| `templates/admin.html` | 291 | Admin login + slide editor (text/image modes) |
| `index.html` | 469 | Superseded static version; diverged from template version |
| `data.json` | 32 | Carousel content: **4 slides** (slide 1 = image mode, user-edited) |

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
- Retro-feature classes: `.pixel-art` (crisp-edge SVGs), `#bootScreen`/`.boot-*`,
  `.toast`/`#toastLayer`, `.term-window`/`.term-body`/`.term-chip`
- Mobile: `@media(max-width:639px)` override block, hamburger menu JS;
  `@media(prefers-reduced-motion:reduce)` kills animations + smooth scroll
- Sections: TOP HUD (SYS/NET/EXP bars) → NAV (logo gem, links, **SFX toggle**) → HERO (`#home`) →
  ABOUT (`#about`) → PROJECTS carousel (`#projects`) → **CONTACT TERMINAL (`#contact`)** → FOOTER
- Carousel JS: `moveCarousel/goToSlide`, autoplay every 4 s, `translateX(-idx*100%)`,
  slides render `text` (title + desc + HP bar) or `image` (bg-image + dark overlay)

### 4a. "Gembong OS" feature layer (last `<script>` in `templates/index.html`)

| Object | Role |
|---|---|
| `Sfx` | WebAudio square-wave engine; `hover/click/achievement` jingles; `localStorage['gembong_sfx']`; resumed on first `pointerdown` |
| `sfxBtn` (nav) | `SFX ON/OFF` toggle, `aria-pressed`, persisted |
| `Toast` | `unlock(key,title,sub)` — deduped `ACHIEVEMENT UNLOCKED` popups + jingle |
| `boot()` | IIFE: types `#bootLines` POST log, `body.booting` scroll-lock, click-to-skip, respects reduced-motion, no-JS safe (hidden until JS activates) |
| `updateExp()` | scroll % → `#expFill` + `#lvlLabel` (LVL 1–5), rAF-throttled; `scroll-master` at 100% |
| `ACHIEVEMENTS` | IntersectionObserver (threshold .2) on `#about/#projects/#contact/footer` |
| `terminal()` | IIFE: `CMDS` map (help/about/services/projects/contact/hire/whoami/ls/sudo/clear), ↑/↓ history, chips (`data-cmd`), links built via DOM (`textContent` only — no user-input HTML) |

---

## 5. Git state

- Remote: `https://github.com/asda1-max/gembong-compra.git` · branch `main` (tracks `origin/main`)
- History: `first stone → vv2 → goat → sys.moni → dad → flask integration → carousel → 0fc3047 carousel and admin`
- **`0fc3047` (user, 2026-09-26)** committed: admin save fixes (`app.py`, `templates/admin.html`),
  `ai_read.md`, recompiled `.pyc`, and `data.json` now at **4 slides** (saved via the fixed admin panel)
- **Uncommitted:** `templates/index.html` (+552 / −14) — the retro "Gembong OS" feature pass (§4a)
- Line-ending warnings: LF ↔ CRLF churn (`core.autocrlf` in play)
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

1. ~~Fix the admin save-path key mismatch~~ ✅ done + committed by user in `0fc3047`
   (suite of 26+ checks in a temp copy, `test_save.py`, not committed).
2. **Smoke-test the retro features in a real browser** (uncommitted `templates/index.html`):
   boot sequence → skip → achievement toast, SFX toggle persistence, scroll EXP/level,
   terminal commands + history, mobile layout. JS passes `node --check` (3 blocks) and render
   checks pass, but no browser execution yet.
3. Commit the `templates/index.html` feature pass after the smoke test.
4. Add `.gitignore` (`__pycache__/`, `*.pyc`), untrack the committed `.pyc`.
5. Add `requirements.txt` (`flask==3.1.1`) and remove/rename root `index.html`.
6. Externalize credentials (`FLASK_ADMIN_USER`/`FLASK_ADMIN_PASS` env) and set a real secret key.
