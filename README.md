# Planora AI

A GenAI-powered Celebration & Event Planner for weddings, birthdays and community events. Planora builds budgets, dated timelines, vendor checklists and personalized ideas, then keeps the event in an editable workspace with grounded decision support.

**Numbers and approvals belong to the server.** Gemini provides optional narrative or validated suggestions; it cannot change authoritative money, bypass ownership, or apply a scenario. A deterministic offline planner remains available without credentials.

## Problem and solution

The supplied Challenge 5 statement is: ?Create a GenAI-powered planning assistant that helps users organize weddings, birthdays, and community events with budgets, timelines, vendor checklists, and personalized ideas.? Planora connects these capabilities in one saved workspace. The statement was supplied by the project owner; independent competition publication, public submission eligibility and any participant-count/ranking claims have not been verified.

## Implemented features

| Capability | Actual behavior |
| --- | --- |
| Event creation | Five-step wizard and reviewed natural-language intake; supported event types include weddings, birthdays, community events, anniversaries and baby showers. |
| Persistent workspaces | SQLite event details, plans, progress, vendor records, expense ledger, chat, history and isolated previews. Reopen by browser cookie and event URL. |
| Budget Guardian | Editable expenses and category allowances; exact-cent estimates, quotes, commitments and cumulative paid amounts; missing-price and exposure warnings. |
| Scenario Studio / Digital Twin | Six isolated types: budget reduction, guest count, date, supplier cancellation, venue/catering cost and additional function. Compare, discard, or explicitly approve a feasible current preview. |
| Event Rescue | Grounded recovery options reuse the same scenario calculations and atomic approval path. Unresolved prices, confirmations or liabilities stay indeterminate. |
| Decision Engine | Evidence-backed recommendations, uncertainty and optional isolated proposals. No automatic write or invented savings. |
| Quote Analyzer | Bounded labeled UTF-8 `.txt`/paste, exact reconciliation, source evidence, terms and up to three source comparisons. Explicitly reviewed quote/commitment recording; a deposit quote is not money paid. No PDF/OCR or universal contract parser. |
| Design Studio | Three local CSS mood-board recipes, editable brief/palette, actual saved allowance links and a reopenable preferred concept. Optional Gemini orders allowed styles; these are not photos or priced vendor offerings. |
| Timeline intelligence | Dated milestones/checklists, calendar/print export, recorded dependency checks and read-only delay/buffer analysis. No invented owners, durations or event-day schedule. |
| Event Readiness Intelligence | Five dimensions, fourteen pass/attention/unknown evidence checks and three next actions linked to existing workflows. A check count is not a readiness score or a fully-ready certificate. |
| Frontend | Responsive vanilla HTML/CSS/ES modules, cinematic CSS 3D/scroll sequence, keyboard controls, shared motion pause and static reduced-motion fallbacks. No npm install or asset build. |

The homepage illustration is **fictional and read-only**. **Try the full saved demo** requires acknowledgment and creates a separate fictional workspace through normal owned APIs. Demo prices and supplier confirmations are assumptions, not verified market data. Other events are not reset.

## Quick start

Python **3.11+** is declared by the project. Local verification uses **CPython 3.14.2** on Windows. Node is needed only for JavaScript/browser checks (tested **25.9.0**, with built-in fetch/WebSocket). Git is needed for the release audit. No Gemini key is required.

### Windows PowerShell

Run from the repository root; activation is unnecessary:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt ruff pytest-cov
.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers
```

For the exact recorded Windows/Python 3.14.2 dependency snapshot, install `-r requirements-ci.txt` instead. It pins the already-tested runtime and validation packages; it is not a universal Linux/macOS lockfile. The normal runtime/development manifests retain their existing version ranges.

### Standard Python / POSIX shell

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt ruff pytest-cov
python -m uvicorn app.main:app --reload --no-proxy-headers
```

Open **http://127.0.0.1:8000/**. Health: `/healthz`; API documentation: `/api/docs`; OpenAPI: `/api/openapi.json`. The application entry point remains `app.main:app`. Frontend files are served by FastAPI at `/` and `/static/*`.

## Configuration and persistence

`.env.example` contains safe defaults and empty credentials. The app reads environment variables; it **does not automatically load `.env`**. Export them, or copy the template to the ignored `.env` and explicitly launch with `--env-file .env`. Never commit a real key.

```powershell
# Optional: use a local secret source rather than committing a key.
# $env:GEMINI_API_KEY = <your privately supplied credential>
$env:GEMINI_MODEL = 'gemini-2.5-flash'
.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers
```

| Variable | Default / behavior |
| --- | --- |
| `GEMINI_API_KEY` | Optional; blank means offline. `GOOGLE_API_KEY` is the existing alias; use one credential. |
| `GEMINI_MODEL` / `GEMINI_TIMEOUT_MS` | `gemini-2.5-flash` / `20000`; existing provider model/timeout. |
| `EVENTRA_DB_PATH` | `<project>/data/eventra.sqlite3`. An explicitly relative path is relative to the process working directory; use an absolute durable path in deployment. |
| `RATE_LIMIT` / `RATE_WINDOW` / `RATE_MAX_CLIENTS` | `30` / `60` seconds / `10000`. Positive bounded settings; limit ? clients must not exceed 1,000,000. |
| `TRUSTED_PROXY_CIDRS` | Empty: socket-peer identity only. Explicit trusted IPs/canonical CIDRs only; no wildcard trust. Always retain `--no-proxy-headers`. |
| `LOG_LEVEL` | `INFO`; provider failures log exception classes, not raw credentials/output. |
| `K_SERVICE` / `PORT` | Cloud Run platform guard / Docker startup port (8080). When `K_SERVICE` is present, SQLite workspace APIs fail closed. Do not unset it to claim durable Cloud Run workspaces. |

Startup preserves the existing schema-2 workspace database and transactionally migrates supported v1 data. Preferred designs use an additive optional format-1 table. Readiness creates no table. Unsupported/malformed databases fail without destructive reset. **Never delete or replace the database to fix startup.** Back up using SQLite's backup API, or stop the application before copying it. Keep backups and browser profiles private.

An HttpOnly, SameSite=Strict cookie scopes saved events to this browser profile; only its one-way owner hash is stored. HTTPS uses Secure cookies. Clearing the cookie loses access: accounts, recovery and cross-device sharing are not implemented. Direct event links retain the original `#/event/<id>/<section>` routes. Persisted data survives server restarts only when the same database path and ownership cookie remain available.

## Architecture and AI boundaries

```text
app/
  main.py          ASGI entry point and middleware/router composition
  api/             routes, ownership/revision dependencies, error handlers
  core/            configuration, body limits, proxy trust, rate limits, cache
  schemas/         existing domain and request/response validation
  services/        planning, exact budget, scenarios, Rescue and intelligence
  ai/              Gemini transport/prompts, strict parsing and offline paths
  db/              SQLite connections and migrations
  repositories/    owned persistence, CAS transactions and read snapshots
frontend/          index.html, app.js, style.css, modules/, styles/, assets/
tests/             unit/, integration/, security/, browser/, fixtures/
scripts/           contract/import checks, offline evaluations, release audit
docs/              accounting rules, implementation evidence and demo guides
.github/workflows/ tested-environment CI recipe (hosted run unverified)
data/              private runtime database; ignored, never part of the release
```

FastAPI/Pydantic and SQLite provide the backend; Google GenAI is optional. There is no frontend framework or npm dependency. Original whole-unit allocation behavior and Decimal/HALF_UP expense accounting remain intact. See [budget and scenario rules](docs/BUDGET_RULES.md).

Gemini user data and fixed server instructions use separate roles/configuration. Context/output bounds, strict server-defined schemas, allowed actions and exact prompt/key-echo rejection constrain model responses; failures use deterministic fallback. Imported quote text does not reach the provider. Readiness AI may only order the same three validated action IDs within urgency tiers. These protections do **not** establish that prompt injection is completely solved or that all narrative is correct.

AI cannot override saved-event ownership, revision/day checks, feasibility, approval or transactional application. An isolated preview is not an applied improvement. Paid/committed obligations survive cancellation; quoted deposits never become paid transactions. Actual quote sources and full incident descriptions are not a persistent document/incident vault.

## Testing and evaluation

Release-preparation verification on **28 October 2026**: **682 tests passed, 98.78% combined statement/branch coverage**, two existing warnings; all **21 browser checkpoint groups** passed. The fresh pre-cleanup baseline was 670 / 98.78%; twelve release-audit regressions were added without changing original tests. Current release-preparation results and exact file/size evidence are in [GITHUB_RELEASE_AUDIT.md](docs/GITHUB_RELEASE_AUDIT.md); hosted CI and live Gemini are not claimed verified.

```powershell
.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90
.\.venv\Scripts\python -m ruff check app tests scripts
.\.venv\Scripts\python -m ruff format --check app tests scripts
.\.venv\Scripts\python -m scripts.check_structure
Get-ChildItem frontend -Recurse -Filter *.js | ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw 'JavaScript syntax failed' } }
Get-ChildItem tests/browser -Filter *.mjs | ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw 'Browser syntax failed' } }
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
.\.venv\Scripts\python -m scripts.evaluate_planning
.\.venv\Scripts\python -m scripts.evaluate_intelligence
.\.venv\Scripts\python -m scripts.evaluate_readiness
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe
.\.venv\Scripts\python -m scripts.audit_release
```

The browser harness creates temporary databases/profiles and owns its Uvicorn process. It checks real UI workflows, approvals, other-event isolation, reduced motion, responsive layouts and browser/server restarts. It needs Edge at the default Windows path, or `EVENTRA_BROWSER_BINARY` / an explicit third argument for Chrome/Edge elsewhere. On POSIX, pass `.venv/bin/python` and the browser executable. Restricted environments may block browser debugging. No Gemini key is needed; evaluations measure offline constraints, not model accuracy.

CI uses the pinned Windows/Python/Node validation snapshot, runs the full Python/JS/evaluation/browser checks and the release audit without API credentials. A workflow file is not evidence of a successful hosted run. Review [CONTRIBUTING.md](CONTRIBUTING.md) before changing behavior or tests.

## Judge walkthrough

1. Launch offline and use **Try the full saved demo**, acknowledging fictional data.
2. In **Overview**, inspect Readiness evidence, unknowns and three action links.
3. Review Guardian amounts; compare isolated alternatives in Scenario Studio or Event Rescue.
4. Apply only after explicit approval of a feasible, current proposal; reopen/restart to confirm persistence.
5. Explore bounded quote analysis, saved design concepts and recorded-link delay analysis.

Detailed guides: [core demo](docs/JUDGE_DEMO.md), [intelligence workflows](docs/INTELLIGENCE_DEMO.md), [readiness approval/restart demo](docs/READINESS_DEMO.md). Historical implementation counts live in their dated reports rather than being current product claims.

## Deployment, security and release

The complete saved product needs **one instance/worker with durable writable SQLite storage**, a stable external URL, TLS outside localhost and explicit trusted ingress. An ephemeral container or serverless filesystem does not provide workspace durability. Cloud Run currently disables saved-event operations; **Vercel is not configured or verified for this SQLite architecture**. Docker build/runtime and hosted deployment remain unverified here. See [deployment requirements](docs/DEPLOYMENT.md).

The application retains its actual 20,000-byte request cap, security headers/CSP, no-store workspace responses, origin checks, explicit proxy trust and bounded/locked rate limiter. Quotas/cache are process-local. It is not an account system, distributed quota service or certified production multi-user platform. Security reporting and release hygiene: [SECURITY.md](SECURITY.md).

General PDFs/OCR, RSVP/seating rosters, verified vendor matchmaking, quantitative sustainability scores, live notifications, day-of task ownership, payment processing/refunds/FX, custom prerequisite editing and account recovery remain unsupported/deferred. Live Gemini, formal accessibility certification, high-volume/production performance, hosted CI and public competition submission compliance remain unverified. No users, awards, rankings or model accuracy are claimed.

Use the [release checklist and publishing commands](docs/GITHUB_RELEASE_CHECKLIST.md). The audit verifies a disposable Git candidate index; local `.venv`, databases, secrets, screenshots, profiles and backup archives are excluded and retained privately. No repository was committed, pushed or published by this cleanup.

## License

The existing [MIT license](LICENSE), copyright 2026 Ayush, is preserved unchanged. Check dependency licenses and your rights to any future contributed imagery or data before redistribution.
