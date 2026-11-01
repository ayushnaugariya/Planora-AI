# Repository evaluation readiness

1 November 2026. Scope: the working tree at commit `212ac2e` plus the changes listed in section 2. It is measured against the six hackathon evaluation parameters and the submission rule *public GitHub repository, total size below 10 MB*. Every result below was executed in this review unless it is explicitly attributed to an earlier report.

## 1. Baseline findings (before any change)

| Area | Finding |
| --- | --- |
| Git state | Branch `main`, clean working tree, local `main` = `origin/main` = `212ac2e`. Three commits in history. |
| **Repository visibility** | `gh repo view` reports **`PRIVATE`**. The submission rules exclude private repositories, so this is a **blocker**. Changing it is a remote setting left to the owner (section 11). |
| Size | Tracked files: 3,945,719 bytes. Packed history: 1.35 MiB. The largest file is the self-hosted Swagger bundle (1.68 MB). The local-only `.venv` (121 MB), `data/` database, `.artifacts/` and nine `.planora-*-baseline-*.zip` backups are git-ignored and were never committed. |
| Secrets / data in history | No `.env`, database, key or archive was ever added (`git log --diff-filter=A`). A pattern scan of every commit (Google/OpenAI/GitHub/AWS/Slack keys, private-key blocks, quoted secrets) found only a deliberate test sentinel in `tests/security/test_ai_boundaries.py`. `.env.example` holds placeholders only. |
| Tests | On a fresh worktree of `212ac2e`: **896 passed, 2 warnings, 98.31% statement+branch coverage**, matching `FINAL_AUDIT.md`. |
| Lint / structure | Ruff passed; 127 files formatted; 79 modules acyclic with the original HTTP contracts intact; 52 JS/MJS files pass `node --check`. |
| Problem statement | The Challenge 5 statement is recorded in `README.md` and `docs/READINESS_INTELLIGENCE.md`. No other official requirement text is in the repository. |
| README | Accurate but hard to evaluate: feature-stage history came before setup; the problem mapping had no evidence links; there was no diagram. Literal `?` bytes replaced the quote marks around the problem statement and the `×` in the rate-limit row. |
| Dev setup | `requirements-dev.txt` omitted `pytest-cov` and `ruff`, so the README told users to install them ad hoc. |
| Accessibility | Static markup had labelled inputs, named buttons, alt text, skip links, live regions and reduced-motion fallbacks. However, the landing, event-list and creation views, the invitation page and the API docs page had no `main` landmark (only the workspace view had one). |

**Environment note.** In this sandbox, pytest's default temp root (`%TEMP%\pytest-of-<user>`) is access-denied, which turns 629 tests into setup *errors*. This comes from the host, not the code. All runs below pass `--basetemp=<scratch dir>`.

## 2. Changes made

| File | Change | Parameter |
| --- | --- | --- |
| `README.md` | Rewritten for evaluators: problem → solution → requirement/feature/evidence table, features, how it works, Mermaid architecture diagram, stack, AI used-for / not-used-for table, setup, environment, tests, demo walkthrough, security, limitations. Fixed the corrupted characters. No capability was added or inflated. | Alignment, Code Quality |
| `docs/README.md` (new) | Index separating current specs and feature references from dated historical reports. | Code Quality |
| `docs/REPOSITORY_EVALUATION_READINESS.md` (new) | This report. | All |
| `requirements-dev.txt` | Added `pytest-cov>=5` and `ruff>=0.6`, which the documented commands already require (both were pinned in `requirements-ci.txt`). One install command now reproduces the dev environment. No runtime dependency changed. | Testing, Code Quality |
| `frontend/index.html` | Added `role="main"` to `#landing-view`, `#events-view` and `#creation-view`. `shell.js` shows exactly one of these views or the workspace (`<main>`) at a time, so there is always exactly one exposed main landmark. Attribute-only change: no visual, style or 3D-landing change. | Accessibility |
| `frontend/invitation.html` | Added `role="main"` to the `#public-event` root, which the existing skip link targets. | Accessibility |
| `frontend/api-docs.html` | Changed the Swagger container from `div` to a labelled `main`. `api-docs.js` still finds it by `#swagger-ui`. | Accessibility |
| `frontend/modules/guests.js` | Fixed a corrupted character in the guest badge ("Public RSVP ? unverified" → "Public RSVP · unverified"), found while recording the demo video. Text-only change; `node --check` and 104 frontend/guest/website tests pass. | Code Quality |

No Python source, schema, route, database location, ownership model, AI prompt, financial calculation or landing-page style was changed.

## 3. Code quality

Reviewed: route modules (`app/api`, 61 decorated routes, 52 with the owner dependency), services, repositories, schemas, the AI layer, configuration and frontend modules.

- **Separation is already sound.** Routes delegate to `services/` (deterministic logic) and `repositories/` (owner-scoped SQL with compare-and-swap). The AI layer is isolated in `app/ai` behind an `LLM` protocol with offline fallbacks. Configuration is centralized in `app/core/config.py`.
- **Ruff** (`E,F,W,I,B,UP,S,SIM`) and format checks pass. An extra `F401/F841/ARG` sweep found no unused imports or variables. Its four `ARG001` hits were checked: three are FastAPI exception-handler signatures that must accept `exc`, and one is the stable `engine.assess(today=…)` parameter used by callers. None was removed.
- **Known complexity, left intentionally:** `services/readiness.py::readiness` (337 lines, a declarative table of 14 checks), `scenarios.simulate` (221), `budget.calculate_budget` (220). They hold the exact-cent and scenario rules that `docs/BUDGET_RULES.md`, the offline evaluation fixtures and 98% coverage protect. Splitting them would be a stylistic refactor of verified financial logic, which this task forbids. They are the first candidates for a future, separately tested refactor.
- **Type hints:** 188 of 281 functions in `app/` have no return annotation, mostly route handlers and repository helpers. Annotations were **not** added in bulk. On FastAPI routes a return annotation can become an inferred `response_model` and change responses, and no static type checker is configured to verify the rest. Request and response contracts are already enforced through Pydantic models and explicit `response_model=` arguments.

## 4. Security findings and fixes

No new vulnerability was reproduced, so no security fix was made and none is claimed. The checks verified in this review:

| Check | Evidence |
| --- | --- |
| Secrets | None in history or in the working tree (section 1). `.gitignore` covers `.env*` (except `.env.example`), keys, credentials, databases, logs, archives and browser profiles. |
| SQL | No f-string, `%` or `.format` query construction in `app/`. All values are parameterized. |
| XSS | No `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval` or `new Function` in `frontend/` (vendor bundle excluded). |
| Headers (live server) | CSP `default-src 'self'; script-src 'self'; … frame-ancestors 'none'`, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`. |
| Cookies / CSRF | Owner cookie `HttpOnly`, `SameSite=Strict`, `Secure` on HTTPS (`app/api/dependencies.py`). Cross-origin state changes are rejected with 403. |
| Public endpoints | An unknown `/e/<slug>` returns 404. Public schemas are allowlisted snapshots (covered by `tests/integration/test_websites.py`). |
| Test isolation | The `client` fixture forces `app.state.llm = None` and a temporary `EVENTRA_DB_PATH`, so a developer's key or database is never used. |

**Remaining (carried from `FINAL_AUDIT.md` R1–R4, still open):**
- SQLite durability requires a single instance.
- Rate limits are process-local, and public RSVPs are unverified.
- There is no account recovery.
- No dependency CVE audit has been run, because `pip-audit` is not installed.
- No HSTS header is sent; it is expected from the TLS terminator.
- Hosted TLS and ingress are unverified.

## 5. Efficiency

The following were inspected. No bottleneck was confirmed, so nothing was changed speculatively.

- **AI:** Gemini is called only for narrative and suggestions, never for calculations. Repeat requests use the thread-safe TTL cache (`app/core/cache.py`). Missing keys, timeouts and errors fall back deterministically without retry storms.
- **Database:** indexes exist on `events(owner)`, `scenarios(event_id, owner)` and `guests(event_id, owner)`. Public slug lookup uses the `UNIQUE` constraint's implicit index. Other child tables are keyed by `event_id`.
- **HTTP:** `GZipMiddleware` (≥1000 bytes). Static files and the index are served `no-cache`, so they revalidate rather than re-download. Workspace JSON is `no-store` for privacy.
- **Frontend:** no framework or bundle, with native ES modules. WebGL portal loads lazily near its section and pauses off-screen; static artwork under reduced motion or data saving.
- **Money:** exact-cent `Decimal`/HALF_UP accounting is preserved, and the exact-money Node checks pass.

## 6. Testing results (this review, final tree)

| Check | Result |
| --- | --- |
| Full Python suite + coverage (`--cov-fail-under=90`) | **896 passed, 2 warnings, 53.6 s, 98.31%** (3947 statements, 1094 branches). Identical to the clean baseline. |
| Ruff lint / format | Passed / 127 files already formatted |
| Structure and HTTP contracts | PASS, 79 acyclic modules |
| JavaScript syntax | 52 authored JS/MJS files pass `node --check` |
| Exact-money, decision-delta, portal-geometry Node checks | All PASS |
| Offline AI evaluations | planning 10/10, intelligence 10/10, readiness 10/10 |
| `pip check` | No broken requirements |
| Startup (temp DB, offline) | `/healthz`, `/`, `/api/docs`, `/api/openapi.json`, `/static/app.js` → 200; unknown `/e/<slug>` → 404 |
| Real-browser regression (Edge + Uvicorn) | **30 checkpoint groups passed, 0 failures, exit 0.** Includes landing, 3D/WebGL portal and reduced motion, ownership isolation, restart persistence, public invitation and RSVP, and self-hosted Swagger with zero CSP violations |
| `git diff --check` | Clean |
| Real database `data/eventra.sqlite3` | SHA-256 `61f08f21…a4ddd6ac6` is unchanged before and after |

The two warnings are the existing Starlette/HTTPX `TestClient` deprecation and a google-genai deprecation. No test, assertion, coverage floor or timeout was modified.

## 7. Accessibility improvements

These are described in section 2: a single `main` landmark on every page and view. Existing support that was verified, not added: `lang="en"`, skip links, labelled inputs (a parser check found no unlabelled control or nameless button), `aria-live`/`role="alert"` status regions, labelled navigation, keyboard tab controls, `:focus-visible` styles in seven stylesheets, and `prefers-reduced-motion` handling in eight stylesheets and six modules, including static fallbacks for the 3D landing. Formal WCAG and screen-reader certification has not been performed.

## 8. Problem-statement alignment

Statement (Challenge 5, owner-supplied): *"Create a GenAI-powered planning assistant that helps users organize weddings, birthdays, and community events with budgets, timelines, vendor checklists, and personalized ideas."*

| Requirement | Planora AI feature | Implementation evidence |
| --- | --- | --- |
| GenAI-powered planning assistant | Gemini narrative, NL intake, grounded Q&A, ranked suggestions, negotiation and invitation copy, each with an offline fallback | `app/ai/*`; `tests/security/test_ai_boundaries.py`; `scripts/evaluate_*` |
| Weddings, birthdays, community events | `EventType` = wedding, birthday, community (+ anniversary, baby shower) | `app/schemas/planning.py`; `frontend/modules/wizard.js` |
| Budgets | Allocation, Budget Guardian ledger (Decimal/HALF_UP), scenarios and Rescue | `app/services/budget.py`, `scenarios.py`; `docs/BUDGET_RULES.md`; `tests/integration/test_budget.py` |
| Timelines | Dated milestones and checklists, `.ics`/print export, delay analysis, Event Day Command Center | `engine.build_timeline`; `timeline_intelligence.py`; `command_center.py` |
| Vendor checklists | Per-category vendor checklist, vendor records, Quote Analyzer, Negotiation Assistant | `engine.build_vendors`; `quote_analysis.py`; `negotiation.py` |
| Personalized ideas | Event-type ideas adjusted to guests, formality and budget; optional Gemini narrative; Design Studio; invitation themes | `engine.compute` (`ideas`); `design.py`; `websites.py` |

**Differentiation.** AI personalizes and explains a deterministic, reproducible plan; it never does the arithmetic. Every money-affecting change is an isolated preview that needs explicit approval. The workspace persists and grows with the event: guests, negotiations, the event-day command center and a published invitation with RSVP.

**Not implemented** (as stated in the README): accounts, sending email or messages, PDF/OCR, photo uploads, seating, payments, and live vendor availability.

## 9. Repository size

| Measure | Value | Method |
| --- | --- | --- |
| Files a clone would contain (tracked + new, non-ignored) | **258 files, 3,958,766 bytes (≈3.78 MiB)**, including this report | `git ls-files -co --exclude-standard` summed with `du -b` |
| Full git history, packed | **1.35 MiB** | bare clone + `git gc --aggressive`, `size-pack` |
| Local working directory, all files | ≈145 MB | dominated by the ignored `.venv` (121 MB); never pushed |
| GitHub's own `diskUsage` | 464 KB (as reported by `gh repo view`) | GitHub metric, which lags and is computed differently; not a measurement made here |

The repository is well below 10 MB. The largest file is the 1.68 MB Swagger UI bundle, which is needed for the CSP-compatible `/api/docs`.

## 10. Remaining limitations

- The GitHub repository is **private**, so it would not be evaluated as it stands.
- No dependency CVE scan and no dedicated secret scanner (gitleaks/trufflehog) were available; pattern-based scanning was used instead.
- Docker, hosted deployment, live Gemini, formal WCAG and production load are unverified.
- The large engine functions noted in section 3 remain.
- The problem statement text is owner-supplied; no official source for it is in the repository.

## 11. Submission checklist

- [x] Repository content below 10 MB (3.78 MiB files; 1.35 MiB packed history)
- [x] No secrets, databases, virtual environments or backups tracked or in history
- [x] `.env.example` holds placeholders only; `.env` is ignored
- [x] README leads with the problem statement, solution and evidence mapping
- [x] Full test suite, lint, format, structure, JS, evaluations and startup verified
- [x] Landing page, guest-first ownership and database untouched
- [ ] **Owner action:** commit these changes and push to `origin/main`
- [ ] **Owner action:** make the repository public (`gh repo edit ayushnaugariya/Planora-AI --visibility public --accept-visibility-change-consequences`), then confirm in a signed-out browser
- [ ] Optional: run `pip-audit` and a secret scanner before publishing

## 12. Round 2: improvements after the first evaluation

The first AI evaluation (95.88/100: Code Quality 86, Security 99, Efficiency 100, Testing 100, Accessibility 96, Problem Statement Alignment 99) ran on commit `212ac2e`, before any change in this report was pushed. Round 2 targets Code Quality, Accessibility and Security without changing behavior.

| Area | Change | Evidence |
| --- | --- | --- |
| Code Quality: frontend readability | Over-long one-line JavaScript was reflowed with a whitespace-only formatter. Breaks are inserted only after `(` `[` `{` `,` `;` or before `)` `]` `}`, never inside strings or templates, so automatic semicolon insertion cannot change. The longest line fell from 1,910 to 765 characters (the remaining long lines are UI copy strings and the WebGL shader source). | Each file's whitespace-stripped token stream is identical before and after; `node --check` passes on all files; 30/30 browser groups pass |
| Code Quality: Python typing | Return and parameter annotations added to every function in `app/` (281 of 281). Types come from runtime observation of the full test suite. Routes received their existing explicit `response_model` as the return type. | Generated OpenAPI schema is byte-identical to `212ac2e`; ruff, structure check and 910 tests pass |
| Security | Added `Cross-Origin-Resource-Policy: same-origin`, `X-Permitted-Cross-Domain-Policies: none`, a stricter `Permissions-Policy`, and HSTS on HTTPS responses only (including 413/429/500 paths). | `tests/security/test_transport_headers.py` (3 tests) |
| Accessibility | A live-DOM audit (accessible names, duplicate IDs, ARIA references, alt text, heading order, WCAG AA contrast) ran across 13 workspace tabs, the landing, events and create views, mobile, the public invitation and `/api/docs`. It found 54 issues, mostly 4.2:1 purple and grey text. Minimal colour adjustments brought every one to at least 4.5:1, decorative glyphs were hidden from screen readers, and Swagger UI got local contrast overrides, named expand buttons and corrected heading levels. Re-audit: 0 issues. | `tests/integration/test_accessibility.py` (11 tests) |

Round 2 verification: **910 passed, 2 warnings, 98.34% coverage**; ruff and format clean (129 files); 79 acyclic modules with original contracts; 52 JS files pass `node --check`; offline evaluations 30/30; exact-money, decision and geometry Node checks pass; **30/30 real-browser groups**; the real database hash is unchanged. Repository content is about 4.0 MB.
