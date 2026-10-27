# Planora AI product transformation

Current continuation: [MOTION_REFINEMENT.md](MOTION_REFINEMENT.md) contains the motion-stage results, before/after screenshots and short recording: 496 Python tests / 99.04%, all 13 browser checkpoint groups, preserved backend/data/contracts. Older stage records below retain their measured historical results.

Latest continuation: [CINEMATIC_BUILD.md](CINEMATIC_BUILD.md) records the verified CSS 3D/AI refinement, **496 tests / 99.04% coverage**, all 11 browser checkpoint groups, current screenshots/file inventory and limits. The 474-test results below remain the original measured product-build history, not the current count.

## Audited baseline and scope

The attached master build request authorizes the frontend redesign and functional Event Rescue Mode. It supersedes prior stage instructions to stop before Rescue. Existing backend calculations, contracts, ownership, scenario validation and security remain authoritative.

Fresh baseline: 429 tests passed, two existing warnings, 26.32s, 98.88% combined statement/branch coverage. Git metadata is absent; `.planora-build-baseline-20261026T111103390513Z.zip` preserves all 76 current source/configuration/document files before changes. Runtime data, secrets, caches and previous archives are excluded. Correction to the initial inventory: an existing default runtime database is present (schema 2, creation predates this archive). It was inspected read-only; automated tests use explicit temporary databases. Its contents changed between read-only checks while pre-existing application processes were active, so runtime byte identity is not claimed. No reset, restoration, relocation or runtime-data cleanup was performed.

Inspection confirmed functioning event CRUD, stable IDs/revisions, anonymous-cookie ownership, exact Decimal ledger, manual allocations, six scenario types, isolated persisted previews and transactional approval/retry protection. Vendor name/contact/booking fields exist but have no editor. Individual guest/RSVP records do not exist. Rescue is absent. The current frontend is one document and an IIFE with real workflows; its handlers will be retained and separated into modules while its presentation/navigation is replaced.

## Implementation map and phase checks

1. Audit/baseline/archive (complete). Preserve original HTTP contract components; verify additive new routes without changing existing schemas or assertions.
2. Local design tokens, consistent native icons/artwork, motion utilities, responsive shell, module/API/state boundaries. No frontend framework or build dependency.
3. Complete editorial landing page and explicitly fictional interactive preview; accessible multi-step creation/review using the existing saved-event API. Hash routes preserve direct links/back/forward. All data/forms remain accessible if motion fails.
4. Real overview, Guardian, vendor editing, headcount/preferences, checklist/timeline/settings. Persist through existing services; retain all old field/control IDs and workflow assertions. Preserve exact-cent formatting.
5. Visual Scenario Studio retaining all six commands and original approval pipeline. Explicit before/after, assumptions, feasibility and stale errors.
6. Rescue incident assessment, multiple defensible options, persisted scenario previews, detailed review and explicit apply/discard through the existing scenario routes. Unknown pricing remains unknown. No competing financial/apply engine or automatic writes. Recovery previews/history persist in the existing scenarios table; incident analysis is regenerated, not falsely claimed as a stored incident log. No database relocation/reset/schema change is needed for this approach.
7. Grounded copilot and natural-language-to-structured previews; truthful per-answer provider/fallback status and preserved R6 boundaries.
8. Desktop/mobile/reduced-motion/keyboard refinements, actual browser screenshots/workflows, complete regressions/coverage/lint/JS/startup and documentation.

All eight phases have been completed within the limits stated below. No competitive outcome, live Gemini, external vendor availability, multi-instance SQLite durability or hosted deployment result is claimed.

## Delivered behavior and boundaries

The local light-theme interface now has an editorial illustrated landing page, finite entrance/reveal/microinteraction motion, fictional calculated budget/recovery demo, five-step reviewable wizard, hash routing, event gallery, desktop collapsible sidebar and mobile focus-contained navigation. `/` and `/static/*` remain the serving mechanism. Fourteen frontend JavaScript files and five token/component stylesheets replace the former presentation monolith without a framework/build step or added dependency. Existing control IDs, storage keys and saved workflows are retained.

Overview uses saved server summaries and explicitly identifies incomplete pricing. Budget Guardian retains exact-cent BigInt display, all expense/allocation handlers and authoritative Decimal totals. Vendor name/contact/status edits persist with owner/current-revision checks. Guests shows actual headcount, dietary/accessibility needs and opens a guest scenario; it clearly states individual RSVP records are not tracked. Checklist search/status filters retain complete saved progress. Timeline search retains existing milestone controls/calendar export. Settings keeps rename/delete/import/full-detail edits. Copilot retains actual saved chat and per-answer Gemini/offline attribution; quick prompts and a route to the existing structured interpreter do not authorize writes.

Rescue takes one of six incident kinds, a bounded description and relevant user-supplied budget/count/date/quote assumptions. It displays a deterministic assessment, date-based urgency, affected records, constraints and next steps. Budget recovery can propose two distinct allowance policies when saved priorities justify them; otherwise duplicate policies are omitted. Guest/date options come only from supplied alternatives. Vendor/venue/service recovery accepts up to three user quotes; missing price, fees or confirmation remain indeterminate. There is no external supplier search, booking or availability claim.

Every option is an existing `Scenario` generated by `services.scenarios.simulate`. A bounded new repository operation saves the whole option set transactionally with owner/revision/request-UUID retry checks. Assessment never updates the event. The UI reuses the original comparison/approval component and existing apply/discard endpoints, so server re-simulation, feasibility, current revision/day, explicit strict-boolean approval, atomic event/history/status application and already-applied retry behavior remain authoritative. Saved scenarios and applied/discarded statuses survive restarts. The transient incident analysis/description is not falsely represented as a separate persisted incident log.

New routes are only `GET /api/demo`, `PATCH /api/events/{event_id}/vendors/{vendor_id}` and `POST /api/events/{event_id}/rescue`. All original OpenAPI operations/components still match the untouched contract fixture exactly. The structure checker projects those original keys before comparison; new strict DTOs/routes have separate tests. This deliberately permits additive product APIs without relaxing any old contract assertion.

## Verification ledger (26 October 2026)

Commands below ran from `D:\Projects\eventra` using the existing Python 3.14.2 virtual environment and Node 25.9.0 / installed Edge. Browser tests spawn their own temporary SQLite file, profile and Uvicorn server with `--no-proxy-headers`; they do not use the pre-existing local server.

| Command actually executed | Actual result |
| --- | --- |
| `git status --short` | Not a Git repository; source archive created before edits. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` (baseline) | 429 passed, 2 warnings, 26.32s; 98.88%. |
| `.\.venv\Scripts\python -m pytest tests/integration/test_structure.py tests/integration/test_frontend.py tests/integration/test_scenario_api.py -q` | 20 passed after module extraction/additive endpoint integration. |
| `.\.venv\Scripts\python -m pytest tests/integration/test_rescue.py tests/integration/test_coordination.py tests/integration/test_structure.py -q` | 40 passed after corrections described below. |
| `.\.venv\Scripts\python -m pytest tests/unit/test_rescue.py tests/integration/test_rescue.py tests/integration/test_coordination.py tests/integration/test_planora_frontend.py tests/integration/test_structure.py -q` | 52 passed, 1 existing warning. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` (first expanded run) | 462 passed, 2 warnings, 32.39s; 98.55%. |
| Same complete coverage command (final code) | **474 passed, 2 warnings, 33.95s; 99.01% combined statement/branch coverage**. 2,070 statements / 546 branches; Rescue service/API/schema and vendor API/schema each 100% in this run. |
| `.\.venv\Scripts\python -m ruff check app tests scripts` | Passed. |
| `.\.venv\Scripts\python -m ruff format --check app tests scripts` | 66 files already formatted. |
| `Get-ChildItem frontend -Recurse -Filter *.js \| ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw "JavaScript syntax failed: $($_.FullName)" } }` | All 14 frontend files passed syntax checking. |
| `node --check tests/browser/browser_workspace_smoke.mjs`; `node --check tests/browser/planora_product_smoke.mjs` | Both passed. |
| `node tests/browser/test_money_display.mjs` | Passed existing large-total/negative-fraction/null cases plus explicit-currency case. |
| `.\.venv\Scripts\python -m scripts.check_structure` | 42 app modules, acyclic import-time graph; every original HTTP operation/component retained. |
| `.\.venv\Scripts\python -m compileall -q app` | Passed. |
| `.\.venv\Scripts\python -m pytest tests/integration/test_workspaces.py tests/integration/test_structure.py -k 'migration or database_path or startup or different_working' -q` | 3 selected database-path cases passed; this selector did not select the separate migration tests, which passed in the complete suite. |
| `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe` (final code) | All 9 checkpoint groups passed. Existing browser assertions retained, zero runtime exceptions. Includes original workflows plus real five-step creation, saved vendor edit, checklist filtering, fictional demo nonmutation, Rescue compare/approve/discard/stale rejection, saved history, further browser/server restart, direct-route reload, 390px mobile / 768px tablet / 1440px desktop overflow, mobile menu/Escape and reduced-motion checks. |
| `docker --version` | Failed: Docker executable unavailable. No build/runtime claim. |

`ruff format` and `ruff check --fix` were also used while authoring the new Python files; final lint/format checks above passed without suppressions. One-off PowerShell/Python/Node inspection and source-splitting scripts were used; no runtime dependency was added. The source archive comparison confirmed all **18 original Python test files**, the original contract fixture, engines, AI/security code, migration code, dependency files and Dockerfile are byte-identical. No original test assertion was removed. The money test setup follows its extracted production formatter; the browser runner adds diagnostic logging and the product test invocation.

Failures were investigated: an initial detached-DOM lookup during shell mounting caused startup failure and was repaired; initial new tests incorrectly tried validating response-only computed fields as persisted input and expected raw SQLite exceptions instead of the repository's `StorageUnavailable`, so the new fixtures/expectation were corrected; a bootstrap status transition incorrectly redirected direct workspace URLs and was repaired; mobile automation initially clicked during the sidebar transition and now waits for that finite transition before clicking. The first read-only runtime hash assertion failed after the live file changed concurrently; no data rollback was attempted. Final checks above passed. These are not hidden/suppressed failures.

Final follow-up browser assertions also verify actual history-back restoration, desktop ArrowDown tab navigation, sidebar collapse/expand and cancelling an event switch from an unsaved new draft. A restarted browser initially lost CDP desktop viewport emulation, so the keyboard fixture now explicitly reapplies 1440px before exercising desktop focus. The new draft cancellation case exposed a null-current-workspace access; it now restores an empty selection and retains draft text. The complete nine-checkpoint browser command passed again after that fix, as did final Ruff lint/format, changed-file JS syntax and exact-cent checks. No backend code changed after the recorded 474-test coverage run.

Two unsuppressed dependency warnings remain: Starlette's HTTPX TestClient deprecation and google-genai's Python `_UnionGenericAlias` deprecation. CI was inspected but not executed on a hosted runner. Live Gemini/provider credentials, real ingress/proxy topology, Docker runtime, cross-browser/screen-reader audits and production load are unverified. Anonymous-cookie ownership has no recovery/cross-device account; quotas are process-local; SQLite requires durable single-instance storage; `K_SERVICE` still disables workspace saves. Existing data/version/paths remain unchanged. Prompt injection is not claimed solved.

## Acceptance evidence and screenshots

The browser suite actually exercised creation through the visible five-step wizard, checked authoritative saved financial updates, performed feasible Rescue approval and asserted its exact `1000.15` projected amount, checked discard nonmutation and stale 409, and reopened complete state/history after a further server/browser restart. Its known zero-cost setup is an explicit **test fixture**, not production sample data or invented user prices. The landing demo is separately labeled fictional and uses a read-only, offline, storage-independent endpoint; simulated approval was verified to leave the real event list unchanged.

Ignored `.artifacts/planora/` contains inspected screenshots: `landing-desktop.png`, `landing-demo.png`, `wizard-review.png`, `overview-desktop.png`, `vendors-desktop.png`, `budget-desktop.png`, `rescue-desktop.png`, `rescue-review.png`, `landing-mobile.png`, `overview-mobile.png`, `budget-mobile.png`, `rescue-mobile.png`, `landing-reduced-motion.png`. These are local verification artifacts and are excluded from Git/Docker. No screenshot or fake-provider test proves live supplier or Gemini availability.

## Final source tree and file ledger

```text
app/
  main.py
  api/           # existing endpoints + coordination.py, demo.py, rescue.py
  core/          # unchanged request, proxy, rate, security and cache protections
  schemas/       # existing contracts + coordination.py, rescue.py
  services/      # original engines + deterministic rescue.py orchestration
  ai/            # unchanged Gemini, output validation and fallback
  db/            # unchanged SQLite lifecycle and migrations
  repositories/  # workspaces.py, with atomic recovery preview batches
frontend/
  index.html, app.js, style.css
  assets/celebration.svg
  modules/       # api, budget, coordination, copilot, demo, helpers, motion,
                 # plan-views, rescue, scenarios, shell, state, wizard
  styles/        # tokens, forms, landing, workspace, motion
tests/
  unit/          # original tests + test_rescue.py
  integration/   # original tests + test_coordination.py, test_rescue.py,
                 # test_planora_frontend.py
  security/      # original assertions unchanged
  browser/       # original runner/formatter + planora_product_smoke.mjs
  fixtures/      # original API contract, unchanged
docs/, scripts/, data/  # data is ignored runtime storage, never moved
```

No original file was deleted or moved. Existing frontend logic was extracted into the new modules; the original frontend entry URLs remain.

Modified files: `.dockerignore`, `.gitignore`, `README.md`, `app/main.py`, `app/repositories/workspaces.py`, `frontend/app.js`, `frontend/index.html`, `frontend/style.css`, `scripts/check_structure.py`, `tests/browser/browser_workspace_smoke.mjs`, `tests/browser/test_money_display.mjs`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md`, `docs/BUDGET_RULES.md`.

Created files: `app/api/coordination.py`, `app/api/demo.py`, `app/api/rescue.py`, `app/schemas/coordination.py`, `app/schemas/rescue.py`, `app/services/rescue.py`, `frontend/assets/celebration.svg`; `frontend/modules/api.js`, `budget.js`, `coordination.js`, `copilot.js`, `demo.js`, `helpers.js`, `motion.js`, `plan-views.js`, `rescue.js`, `scenarios.js`, `shell.js`, `state.js`, `wizard.js`; `frontend/styles/tokens.css`, `forms.css`, `landing.css`, `workspace.css`, `motion.css`; `tests/browser/planora_product_smoke.mjs`, `tests/integration/test_coordination.py`, `tests/integration/test_planora_frontend.py`, `tests/integration/test_rescue.py`, `tests/unit/test_rescue.py`, `docs/PLANORA_BUILD.md`.

## Launch and data location

From the repository root: `.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers`, then open `http://127.0.0.1:8000/`. Hash routes include `#/events`, `#/create`, `#/event/<id>/overview` and the other workspace sections; server paths/API contracts are unchanged. No asset build is needed.

Default database: `D:\Projects\eventra\data\eventra.sqlite3`. To use another existing durable file, set `$env:EVENTRA_DB_PATH = 'D:\EventraData\events.sqlite3'` before starting; explicit relative paths keep working-directory semantics. Do not reset or recreate existing files. No schema change is required; existing transactional v1-to-v2 migration remains. Keep the owning browser's cookies. Export Gemini credentials in the server environment only; without credentials the built-in planner/copilot/Rescue still operate within their documented limits.
