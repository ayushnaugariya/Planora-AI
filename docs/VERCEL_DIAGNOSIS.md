# Vercel function startup diagnosis

28 October 2026 (Asia/Calcutta). The owner reported `500 FUNCTION_INVOCATION_FAILED` after deploying commit `cc07efd`. Read-only requests confirmed the same platform error at `/` and `/healthz`. No deployment, commit, push, credential change or data migration was performed by this fix.

## Evidence and confirmed configuration defect

The supplied **build log**, not runtime traceback, says Python 3.12 was selected from `pyproject.toml`, dependencies were installed from that file, static-file collection failed, then deployment completed. Before this fix, `[project]` had **no `dependencies`**. All four actual runtime requirements existed only in `requirements.txt`. The manifest chosen by the reported build therefore did not declare the application runtime packages. This is a confirmed deployment metadata defect and a strong explanation for import/static-collection failure; the exact remote Python exception remains unobserved, so a successful redeployment is not claimed.

A regression test was run before editing metadata: it failed because the TOML dependency list was empty while the requirements file contained FastAPI, Uvicorn, Pydantic and Google GenAI. A second new test failed because explicit entrypoint/static policy metadata was absent. Auto-detection can normally find `app/main.py`; explicit metadata is added to remove ambiguity, not because missing explicit configuration alone proved the crash.

SQLite storage is a separate issue. A local offline check simulating an unwritable database returned homepage/health 200 and workspace listing 503. Existing startup catches storage initialization failures. Consequently the public function failure was not attributed to SQLite without a traceback.

## Minimal change

- `pyproject.toml`: add `[project].dependencies` with **exactly the existing four requirement specifiers**, without changing versions or adding a product dependency.
- Explicit `[tool.vercel] entrypoint = "app.main:app"`; existing Uvicorn entrypoint and local APIs remain untouched.
- `[tool.vercel.fastapi.static] cdn = false, exclude = false`: keep runtime frontend files and existing security/cache middleware instead of bypassing it through CDN promotion. No `public/` copy, duplicate frontend or `vercel.json` rewrite.
- `tests/integration/test_deployment_metadata.py`: prevent drift between the two supported manifests, import the configured entrypoint and verify it resolves to the original FastAPI object with the intended static policy.
- `docs/DEPLOYMENT.md` and this diagnosis: record the actual scope and persistent-storage limitation.

References: [Vercel Python dependencies and entrypoint configuration](https://vercel.com/docs/functions/runtimes/python), [FastAPI entrypoint/static/middleware behavior](https://vercel.com/docs/frameworks/backend/fastapi). The provider's supported `tool.vercel` metadata is used; no opaque extra build command or forced proxy trust is introduced.

## Verification

Before fix: two new regression checks failed (empty TOML runtime dependencies / absent explicit metadata). After fix: `.\.venv\Scripts\python -B -m pytest -p no:cacheprovider tests/integration/test_deployment_metadata.py tests/integration/test_structure.py tests/integration/test_asset_refresh.py -o addopts='' -q` passed **14 tests**, one existing TestClient warning. This includes actual HTTP frontend asset/cache behavior and original API/import contract preservation.

`.\.venv\Scripts\python -B -m ruff check app tests scripts --no-cache` passed; format check reported **99 files already formatted**. `python -B -m scripts.check_structure` retained **60 acyclic application modules and every original API contract**. Full command: `python -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90` with `COVERAGE_FILE=.artifacts/release/vercel-fix.coverage`: **684 passed, 2 existing warnings, 22.96s; 98.78% combined coverage**. The original 90% floor/exclusions remain. No original test, application logic, middleware, finance, persistence or API schema was modified. Browser end-to-end tests are not rerun for this metadata-only change; the earlier full 21-group result is historical, not a new deployment test.

There is no installed Vercel CLI or authenticated provider log access in this environment. A fresh Linux/Python 3.12 provider dependency install/build, live Gemini and hosted persistence were not executed or verified locally. Local tests use the existing Windows/Python 3.14.2 validation environment. The initial public errors were read-only checks of the old deployment, not a successful check of these changes.

## Owner deployment check

Commit/push the specific changed metadata, tests and deployment documentation to the linked repository. Vercel should create a new deployment from that commit; do not merely redeploy old `cc07efd`. Confirm its build log installs the runtime packages. If retrying manually, use the new commit and disable reuse of the previous build cache.

Then check `/healthz`, `/`, `/static/style.css`, `/static/app.js` and `/api/openapi.json`. If function errors persist, open **project Logs ? failing invocation ? Python traceback**, not just the build log, and inspect the actual exception. Keep keys/cookies private.

This change does not provide persistent SQLite on Vercel. Saved workspaces, expense/scenario/Rescue/readiness/design workflows still require a separately approved durable backend/database solution. Do not point SQLite at `/tmp` and present it as durable, upload the local user database, relax proxy trust, or weaken approvals to make a demo appear functional.
