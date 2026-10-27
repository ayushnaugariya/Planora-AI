# Structural refactor ledger

This is a behavior-preserving reorganization, not a product stage. Rescue and new product features are excluded. All paths are relative to the repository root.

## Baseline and safety

The supplied directory is not a Git checkout: `git status --short` returned `fatal: not a git repository`. No Git restore/reset/clean was used. Before source edits a uniquely named `.refactor-baseline-*.zip` source-only archive was created, containing original files, SHA-256 hashes and Python imports. It excludes virtual environments/caches, credentials and runtime databases. Existing `*.zip` Git exclusion protects this local recovery artifact; Docker exclusion is updated too. The original files are the baseline regardless of their unknown commit status.

Fresh baseline command: `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90`: **422 passed, 2 warnings, 34.30s; 98.86% combined statement/branch coverage**. The warnings are Starlette/HTTPX TestClient and google-genai/Python deprecations. No tests were assumed passing from old reports.

Before moves the default `data/eventra.sqlite3` did not exist and `EVENTRA_DB_PATH` was unset. No data directory/database will be moved, reset or initialized by this refactor. All startup/migration tests use temporary explicit paths. The database path remains project-root `data/eventra.sqlite3` by default; configured relative paths retain their current-working-directory meaning and absolute overrides remain unchanged. SQLite user_version/workspace version remains 2, including transactional 0/1→2 initialization/migration, foreign keys, ownership and revision/application transactions.

## Initial directory tree

```text
app/{__init__,main,models,engine,ai,workspace_ai,service,cache,
     workspace_models,workspaces,storage,budget_models,budget,budget_api,
     scenario_models,scenarios,scenario_api,proxy,rate_limits,request_limits}.py
static/{index.html,style.css,app.js}
tests/{__init__,conftest,test_engine,test_cache,test_frontend,test_ai_and_api,
       test_workspace_ai,test_workspaces,test_budget,test_scenarios,
       test_scenario_api,test_security,test_request_limits,test_ai_boundaries}.py
tests/{browser_workspace_smoke,test_money_display}.mjs
docs/{UPGRADE_AUDIT,UPGRADE_PLAN,BUDGET_RULES}.md
.github/workflows/ci.yml
.env.example, .gitignore, .dockerignore, Dockerfile
README.md, LICENSE, pyproject.toml, requirements{,-dev}.txt
```

Local caches/virtual environment/coverage are excluded from this source tree. No AGENTS.md, existing scripts or Git metadata was found.

## Proposed source-to-destination map (recorded before moves)

| Source | Destination / retained responsibility |
| --- | --- |
| `static/index.html`, `static/style.css`, `static/app.js` | Same basenames in `frontend/`; bytes unchanged, public URLs stay `/static/*`. |
| `app/models.py` | `app/schemas/planning.py`; existing Pydantic domain/DTO shapes kept together. |
| `app/budget_models.py` | `app/schemas/budget.py` |
| `app/workspace_models.py` | `app/schemas/workspaces.py` |
| `app/scenario_models.py` | `app/schemas/scenarios.py` |
| `app/engine.py` | `app/services/engine.py`; existing deterministic calculations and tightly coupled offline templates retained. |
| `app/service.py` | `app/services/planning.py` |
| `app/cache.py` | `app/core/cache.py` |
| `app/budget.py` | `app/services/budget.py` |
| `app/scenarios.py` | `app/services/scenarios.py` |
| `app/ai.py` | `app/ai/gemini.py`; adapter, prompt/output protections and legacy chat kept cohesive. |
| `app/workspace_ai.py` | `app/ai/workspace.py` |
| `app/proxy.py`, `app/rate_limits.py`, `app/request_limits.py` | Same basenames in `app/core/`. |
| `app/main.py` paths/settings | `app/core/config.py`; root-anchored assets/default database path. |
| `app/main.py` guard/header/limiter glue | `app/core/security.py`; same state and middleware order. |
| `app/main.py` exception handlers | `app/api/errors.py`; registration stays in main. |
| `app/main.py` legacy planner/chat/ICS handlers | `app/api/planning.py`; names/contracts unchanged. |
| `app/workspaces.py` owner/current/repository dependencies | `app/api/dependencies.py` |
| `app/workspaces.py` reconciliation/import/revision helpers | `app/services/workspaces.py`; removes service→route dependency. |
| `app/workspaces.py` HTTP handlers/generation bridge | `app/api/workspaces.py` |
| `app/budget_api.py`, `app/scenario_api.py` | `app/api/budget.py`, `app/api/scenarios.py` |
| `app/storage.py` shared exceptions | `app/core/errors.py` |
| `app/storage.py` connection/initialization lifecycle | `app/db/sqlite.py`; same per-instance lock/state/context manager. |
| `app/storage.py` existing migration SQL | `app/db/migrations.py`; same SQL/transaction semantics. |
| `app/storage.py` CRUD/CAS/scenario operations | `app/repositories/workspaces.py`; inherits the existing moved SQLite lifecycle. |
| `app/main.py` | Stays entry point; app metadata, lifespan, static mounting and router/middleware/error wiring. |
| `tests/test_engine.py`, `tests/test_cache.py`, `tests/test_scenarios.py` | Same basenames in `tests/unit/`; existing fixtures/assertions retained. |
| `tests/test_ai_and_api.py`, `tests/test_workspace_ai.py`, `tests/test_workspaces.py`, `tests/test_budget.py`, `tests/test_scenario_api.py`, `tests/test_frontend.py` | Same basenames in `tests/integration/`; mixed files stay intact rather than being rewritten. |
| `tests/test_security.py`, `tests/test_request_limits.py`, `tests/test_ai_boundaries.py` | Same basenames in `tests/security/`. |
| `tests/browser_workspace_smoke.mjs`, `tests/test_money_display.mjs` | Same basenames in `tests/browser/`; only location/root references change. |
| `tests/conftest.py`, `tests/__init__.py` | Stay central; import references update. |

Necessary package `__init__.py` files are added. No separate ORM/domain-model layer, empty models/data directories, duplicate services or legacy import shims are planned. Internal Python import paths change; `app.main:app`, HTTP API schemas, function names, `/static` URLs, browser storage keys/cookies and database location remain compatible.

## Entry points, imports and configuration

The original entry is `uvicorn app.main:app --reload --no-proxy-headers`; Docker uses `app.main:app`, PORT and the same no-proxy flag. CI installs existing requirements/tools then runs Ruff and pytest over tests/. Static hosting originally resolves root/static from main; it will resolve root/frontend through core config without deriving database paths from asset placement.

Original dependency shape: main imports everything; workspaces combines dependencies/services/routes; budget/scenario APIs import workspaces helpers; scenarios imports workspaces.reconcile; workspace computed budget_summary uses a deliberate deferred budget import. After moves: API→services/repositories/schemas/core; services→schemas/core/AI; repositories→db/schemas/core; AI→engine/schemas; no services→API imports. Deferred computed-field imports are retained. No duplicate budget engine or second SQLite backend is introduced.

Environment names/semantics remain: GEMINI_API_KEY / GOOGLE_API_KEY, GEMINI_MODEL, GEMINI_TIMEOUT_MS, LOG_LEVEL, RATE_LIMIT, RATE_WINDOW, RATE_MAX_CLIENTS, TRUSTED_PROXY_CIDRS, legacy TRUST_PROXY migration behavior, EVENTRA_DB_PATH, K_SERVICE, PORT. FORWARDED_ALLOW_IPS remains inert in the supported no-proxy launch. Existing positive bounds, exact defaults and Cloud Run storage rejection are preserved; no key values are inspected or archived.

## Verification approach

Each logical group is followed by relevant existing tests. `tests/fixtures/api_contract.json` records the actual pre-move OpenAPI schema without starting storage; a regression checks exact contract equality. Frontend bytes and original assertion/case inventory are preserved. A read-only structure-check script will validate acyclic top-level imports and OpenAPI equality. Final checks include complete coverage, Ruff, JS syntax, exact-cent display, actual browser/server restarts and temporary-database migration/startup tests. Docker availability is probed; no unsupported runtime success will be claimed.

Final tree, complete file ledger, executed commands/results and any deviations follow after implementation.

## Actual commands and results

| Stage / command actually executed | Actual result |
| --- | --- |
| `git status --short` | Failed: supplied directory is not a Git repository. No reset/restore/clean/commit used. Source-only archive preserves the supplied files. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` before edits | **422 passed**, 2 warnings, 34.30s; **98.86%**. |
| `.\.venv\Scripts\python -m pytest tests/test_engine.py tests/test_budget.py tests/test_workspaces.py tests/test_scenarios.py tests/test_scenario_api.py --tb=short` | Schema group: **170 passed**, 4.72s. |
| `.\.venv\Scripts\python -m pytest tests/test_frontend.py tests/test_ai_and_api.py tests/test_request_limits.py --tb=short` | Frontend group: **80 passed**, 1.83s; JS syntax and exact-cent runner also passed. |
| `.\.venv\Scripts\python -m pytest tests/test_engine.py tests/test_cache.py tests/test_ai_and_api.py tests/test_workspace_ai.py tests/test_ai_boundaries.py tests/test_budget.py tests/test_workspaces.py tests/test_scenarios.py tests/test_scenario_api.py --tb=short` | Services/AI group: **300 passed**, 17.19s after correcting the import alias issue below. |
| `.\.venv\Scripts\python -m pytest tests/test_workspaces.py tests/test_budget.py tests/test_scenario_api.py --tb=short` | SQLite group: **71 passed**, 6.76s. |
| `.\.venv\Scripts\python -m pytest tests/test_ai_and_api.py tests/test_security.py tests/test_request_limits.py tests/test_workspaces.py tests/test_scenario_api.py tests/test_budget.py --tb=short` | HTTP/core group: **220 passed**, 14.08s after updating mocks to the actual moved handler. |
| `.\.venv\Scripts\python -m pytest tests/unit tests/integration tests/security --tb=short` | All moved original cases: **422 passed**, 2 warnings, 24.98s. |
| `.\.venv\Scripts\python -m pytest tests/integration/test_structure.py --tb=short` | **7 passed**, 0.42s. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` final | **429 passed**, 2 warnings, 34.60s; **98.88% combined statement/branch coverage**. 1,845 statements/13 missed; 486 branches/13 partial. Existing floor remains 90%. |
| `.\.venv\Scripts\python -m pytest tests/integration/test_workspaces.py tests/integration/test_budget.py -k 'migration or initialize or startup or unsupported or cloud or restart' --tb=short` | **6 passed**, 56 deselected, 0.55s. No actual workspace database used. |
| `.\.venv\Scripts\ruff check app tests --fix` | Import grouping/unused-import cleanup: 38 fixed, zero remaining. Earlier diagnostic run exposed misplaced module docstrings/imports; fixed rather than suppressed. |
| `.\.venv\Scripts\ruff check . --fix` then `.\.venv\Scripts\ruff format .` | One new long test decorator needed formatting; format resolved it. Last format pass: 1 reformatted, 60 unchanged. No lint policy was relaxed; original engine prose exception moved to its new path. |
| `.\.venv\Scripts\ruff check .` | **All checks passed.** |
| `.\.venv\Scripts\ruff format --check .` | **61 files already formatted.** |
| `.\.venv\Scripts\python -m scripts.check_structure` | **PASS: 36 app modules, acyclic import-time graph, exact original OpenAPI contract.** No lifespan/database initialization. |
| `node --check frontend/app.js` | Passed. |
| `node --check tests/browser/browser_workspace_smoke.mjs` | Passed. |
| `node --check tests/browser/test_money_display.mjs` | Passed. |
| `node tests/browser/test_money_display.mjs` | Passed exact-cent, large-total and negative-fraction rendering checks. |
| `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe` | **Passed all seven checkpoints, exit 0.** Real Edge/Uvicorn; both browser/server restarts, saved progress/chat, isolation/rebuild/failed save/delete, expenses/metrics, scenario reject/approve and legacy import. Temporary profile/database and owned subprocesses; local process access outside the restricted sandbox. |
| `docker --version` | Failed: Docker executable is not installed. Build/runtime not attempted or claimed. Dockerfile/ignore/launch settings inspected, paths updated and launcher regression retained. |

Independent archive comparisons additionally verified: all **189 original test functions and their parameter decorators**, **635 original assertions** (normalizing only canonical moved module references), byte-identical frontend HTML/CSS/JS, and identical migration-statement AST/SQL/version checks. The actual full suite, not cache contents, establishes passing cases. Initial services/AI test collection failed because a mechanical rewrite doubled one Gemini import path; the alias was corrected. The first HTTP/core test run had 16 mock-target errors/204 passing cases because body-limit tests still patched main.build_plan; they now patch the real app.api.planning.build_plan and retain every unread-tail/no-handler assertion. No functional failure was hidden or test removed.

## Compatibility, configuration and limits

- Local launch from the repository root: `.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers`. Linux/activated-venv equivalent: `uvicorn app.main:app --reload --no-proxy-headers`.
- Static source is frontend, public root/assets remain `/`, `/static/app.js`, `/static/style.css`. HTML links, storage keys and all frontend bytes are unchanged. The Docker image now copies frontend to `/srv/frontend`; project-root config still resolves database storage at `/srv/data`.
- `EVENTRA_DB_PATH` remains authoritative. Unset: absolute project-root `data/eventra.sqlite3`; explicitly relative: interpreted against current working directory as before; absolute: unchanged. Use an absolute durable path in deployment. This refactor requires no schema bump; existing version-2 databases reopen and original v1 migration logic is retained. Tests never open/reset the user's configured/default database.
- Middleware order remains outer server error → trusted proxy → guard → 20,000-byte actual-body cap → gzip → exceptions/router. Security/no-store/early errors, anonymous-cookie ownership, all finance/scenario/approval/retry rules and R6 boundaries are retained. Per-process quotas, SQLite single-instance and Cloud Run save rejection remain explicit.
- Internal Python module paths changed; no unneeded legacy wrappers were retained. External HTTP/JSON/OpenAPI, `app.main:app`, static URLs, persisted documents and environment names stay compatible. Code importing old private flat modules must adopt this map. Existing deferred computed-summary imports are intentional; no new import-time cycles were introduced.
- No separate app/models layer was created: existing Pydantic classes provide both domain shapes and validation, and duplicating them would add risk. Existing offline fallback/templates stay in the engine. Mixed test files remain intact in the best-fitting group.
- CI's existing recursive pytest/Ruff commands discover the new groups; no remote CI execution is claimed. Dependencies and coverage threshold are unchanged. No Docker/container/cloud/live-Gemini verification is claimed. Both existing dependency deprecation warnings remain unsuppressed. No new feature, frontend redesign, account/storage backend or Rescue workflow was added.
- `.gitignore` additionally excludes env variants while retaining `.env.example`; runtime data/SQLite files and the recovery ZIP stay ignored. Docker also excludes archives/caches/env variants. With no Git metadata, tracked/untracked status could not be established; no claim is made that Git has verified exclusions against an index.
- `app/__init__.py` changed only line-ending normalization; its module text is unchanged. Other retained modifications are configuration/docs/import wiring as enumerated below.

## Final tree and exact file ledger

Generated from actual files and the archived pre-edit hashes. The local recovery archive is `.refactor-baseline-20261026T103752740361Z.zip` (ignored, not application source).

```text
+-- .github/
|   \-- workflows/
|       \-- ci.yml
+-- app/
|   +-- ai/
|   |   +-- __init__.py
|   |   +-- gemini.py
|   |   \-- workspace.py
|   +-- api/
|   |   +-- __init__.py
|   |   +-- budget.py
|   |   +-- dependencies.py
|   |   +-- errors.py
|   |   +-- planning.py
|   |   +-- scenarios.py
|   |   \-- workspaces.py
|   +-- core/
|   |   +-- __init__.py
|   |   +-- cache.py
|   |   +-- config.py
|   |   +-- errors.py
|   |   +-- proxy.py
|   |   +-- rate_limits.py
|   |   +-- request_limits.py
|   |   \-- security.py
|   +-- db/
|   |   +-- __init__.py
|   |   +-- migrations.py
|   |   \-- sqlite.py
|   +-- repositories/
|   |   +-- __init__.py
|   |   \-- workspaces.py
|   +-- schemas/
|   |   +-- __init__.py
|   |   +-- budget.py
|   |   +-- planning.py
|   |   +-- scenarios.py
|   |   \-- workspaces.py
|   +-- services/
|   |   +-- __init__.py
|   |   +-- budget.py
|   |   +-- engine.py
|   |   +-- planning.py
|   |   +-- scenarios.py
|   |   \-- workspaces.py
|   +-- __init__.py
|   \-- main.py
+-- docs/
|   +-- BUDGET_RULES.md
|   +-- REFACTOR_MAP.md
|   +-- UPGRADE_AUDIT.md
|   \-- UPGRADE_PLAN.md
+-- frontend/
|   +-- app.js
|   +-- index.html
|   \-- style.css
+-- scripts/
|   +-- __init__.py
|   \-- check_structure.py
+-- tests/
|   +-- browser/
|   |   +-- browser_workspace_smoke.mjs
|   |   \-- test_money_display.mjs
|   +-- fixtures/
|   |   \-- api_contract.json
|   +-- integration/
|   |   +-- __init__.py
|   |   +-- test_ai_and_api.py
|   |   +-- test_budget.py
|   |   +-- test_frontend.py
|   |   +-- test_scenario_api.py
|   |   +-- test_structure.py
|   |   +-- test_workspace_ai.py
|   |   \-- test_workspaces.py
|   +-- security/
|   |   +-- __init__.py
|   |   +-- test_ai_boundaries.py
|   |   +-- test_request_limits.py
|   |   \-- test_security.py
|   +-- unit/
|   |   +-- __init__.py
|   |   +-- test_cache.py
|   |   +-- test_engine.py
|   |   \-- test_scenarios.py
|   +-- __init__.py
|   \-- conftest.py
+-- .dockerignore
+-- .env.example
+-- .gitignore
+-- Dockerfile
+-- LICENSE
+-- README.md
+-- pyproject.toml
+-- requirements-dev.txt
\-- requirements.txt
```

Runtime `data/` remains absent until normal configured startup; virtual environments/caches/coverage and the ignored recovery ZIP are omitted. No empty placeholder directories were created.

### Moved or split source files (35)

| Original | Current primary destination | Note |
| --- | --- | --- |
| `app/ai.py` | `app/ai/gemini.py` | Moved; references updated |
| `app/budget.py` | `app/services/budget.py` | Moved; references updated |
| `app/budget_api.py` | `app/api/budget.py` | Moved; references updated |
| `app/budget_models.py` | `app/schemas/budget.py` | Moved; references updated |
| `app/cache.py` | `app/core/cache.py` | Moved; references updated |
| `app/engine.py` | `app/services/engine.py` | Moved; references updated |
| `app/models.py` | `app/schemas/planning.py` | Moved; references updated |
| `app/proxy.py` | `app/core/proxy.py` | Moved; references updated |
| `app/rate_limits.py` | `app/core/rate_limits.py` | Moved; references updated |
| `app/request_limits.py` | `app/core/request_limits.py` | Moved; references updated |
| `app/scenario_api.py` | `app/api/scenarios.py` | Moved; references updated |
| `app/scenario_models.py` | `app/schemas/scenarios.py` | Moved; references updated |
| `app/scenarios.py` | `app/services/scenarios.py` | Moved; references updated |
| `app/service.py` | `app/services/planning.py` | Moved; references updated |
| `app/storage.py` | `app/repositories/workspaces.py` | Persistence retained; lifecycle/migrations/errors extracted as listed below |
| `app/workspace_ai.py` | `app/ai/workspace.py` | Moved; references updated |
| `app/workspace_models.py` | `app/schemas/workspaces.py` | Moved; references updated |
| `app/workspaces.py` | `app/api/workspaces.py` | HTTP retained; dependencies and child/revision helpers extracted below |
| `static/app.js` | `frontend/app.js` | Byte-identical assets |
| `static/index.html` | `frontend/index.html` | Byte-identical assets |
| `static/style.css` | `frontend/style.css` | Byte-identical assets |
| `tests/browser_workspace_smoke.mjs` | `tests/browser/browser_workspace_smoke.mjs` | Only launch comment/path changed; all lifecycle/workflow assertions retained |
| `tests/test_ai_and_api.py` | `tests/integration/test_ai_and_api.py` | Moved; references updated |
| `tests/test_ai_boundaries.py` | `tests/security/test_ai_boundaries.py` | Moved; references updated |
| `tests/test_budget.py` | `tests/integration/test_budget.py` | Moved; references updated |
| `tests/test_cache.py` | `tests/unit/test_cache.py` | Moved; references updated |
| `tests/test_engine.py` | `tests/unit/test_engine.py` | Moved; references updated |
| `tests/test_frontend.py` | `tests/integration/test_frontend.py` | Moved; references updated |
| `tests/test_money_display.mjs` | `tests/browser/test_money_display.mjs` | Moved; references updated |
| `tests/test_request_limits.py` | `tests/security/test_request_limits.py` | Moved; references updated |
| `tests/test_scenario_api.py` | `tests/integration/test_scenario_api.py` | Moved; references updated |
| `tests/test_scenarios.py` | `tests/unit/test_scenarios.py` | Moved; references updated |
| `tests/test_security.py` | `tests/security/test_security.py` | Moved; references updated |
| `tests/test_workspace_ai.py` | `tests/integration/test_workspace_ai.py` | Moved; references updated |
| `tests/test_workspaces.py` | `tests/integration/test_workspaces.py` | Moved; references updated |

### Created files (24)

- `app/ai/__init__.py`
- `app/api/__init__.py`
- `app/api/dependencies.py`
- `app/api/errors.py`
- `app/api/planning.py`
- `app/core/__init__.py`
- `app/core/config.py`
- `app/core/errors.py`
- `app/core/security.py`
- `app/db/__init__.py`
- `app/db/migrations.py`
- `app/db/sqlite.py`
- `app/repositories/__init__.py`
- `app/schemas/__init__.py`
- `app/services/__init__.py`
- `app/services/workspaces.py`
- `docs/REFACTOR_MAP.md`
- `scripts/__init__.py`
- `scripts/check_structure.py`
- `tests/fixtures/api_contract.json`
- `tests/integration/__init__.py`
- `tests/integration/test_structure.py`
- `tests/security/__init__.py`
- `tests/unit/__init__.py`

### Modified files retained at the same path (10)

- `.dockerignore`
- `.gitignore`
- `Dockerfile`
- `README.md`
- `app/__init__.py`
- `app/main.py`
- `docs/UPGRADE_AUDIT.md`
- `docs/UPGRADE_PLAN.md`
- `pyproject.toml`
- `tests/conftest.py`

### Unchanged retained files (7)

- `.env.example`
- `.github/workflows/ci.yml`
- `LICENSE`
- `docs/BUDGET_RULES.md`
- `requirements-dev.txt`
- `requirements.txt`
- `tests/__init__.py`

Old source paths above no longer contain implementations; cache bytecode is not an import shim. No compatibility wrapper duplicates business logic. Necessary new package initializers contain documentation only. The new check script/test/fixture verify structure and contracts, not product features.

## Final preservation check

The final source tree contains 62 app/frontend/test/script files, including the captured contract fixture. SHA-256 comparison found no changes to those files during the documentation pass. UTF-8/local-document links were validated for README, audit, plan, unchanged accounting rules and this ledger; the final full tree uses portable ASCII branches. The default database remains absent. No required work beyond the structural refactor was started, and no tests were rerun merely for documentation-only edits.
