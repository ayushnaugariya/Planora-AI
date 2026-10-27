# Planora AI invitation experience

27 October 2026 (client timezone). The request asks for a more memorable, bolder homepage while retaining the good existing UI. Inspected current CSS 3D/motion policy, homepage markup, module composition, previous artifacts and retained browser assertions. Git metadata is absent; `.planora-portal-baseline-20261026T195014Z.zip` preserves 120 source files before edits, excluding runtime data, keys and artifacts. Previous screenshots are copied into `.artifacts/portal-experience/before/`.

Implementation: retain existing scene/workspace controls and add an optional 3D envelope opening interaction, a more dimensional architectural arrival and spatial planning cards. Cards must use the existing fictional demo response, not made-up financial/availability figures. Native keyboard controls, static reduced-motion behavior, pause/visibility policy, responsive clipping and real planning CTAs remain. No backend/schema/API/dependency changes are needed. Verify actual browser rendering and interaction at desktop/tablet/narrow mobile widths, then run the existing complete regressions and document results.

## Result and boundaries

The homepage retains its ivory/navy/lavender editorial layout, botanical architecture, original hotspots, budget link and planning CTA. A finite perspective camera arrival now introduces the composition. A sealed paper envelope sits in front of the invitation. **Open the invitation** unfolds its flap, lifts the card, spreads the architectural planes, raises concentric floor contours and reveals spatial guest/date/priority cards. Folding reverses the presentation. Existing bounded pointer tilt, independent idle layers and native pause control remain.

The new module subscribes to the existing `planora:demo-data` event. Guest count, date and priority come from the calculated fictional example; the module performs no network writes or browser financial calculations. Saved workspaces and provider integrations are untouched. Missing demo data leaves neutral placeholders rather than invented facts.

The control is a native button with expanded/controls/described-by relationships. Closed facts are hidden and inert; opening announces the fictional state. Escape folds and returns focus, stopping propagation so unrelated shell Escape handling cannot steal focus. Native Enter activation is browser-tested with actual CDP key events. Reduced motion removes the arrival and opening transitions; paused/static policies show the complete scene rather than leaving a dim initial animation frame. Touch retains a simpler composition; the priority card is omitted on narrow screens. No new render loop, external library, remote asset, scroll hijack, loader or CTA gate was introduced.

## Commands and actual evidence

Commands executed from the project root with the existing venv, Node and Edge:

| Command | Actual result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` before edits | 496 passed, 2 warnings, 39.66s; 99.04%. |
| Same complete Python command after implementation | **496 passed, 2 warnings, 61.08s; 99.04% combined statement/branch coverage**. Original coverage floor unchanged. |
| `.\.venv\Scripts\python -m ruff check app tests scripts` | All checks passed. |
| `.\.venv\Scripts\python -m ruff format --check app tests scripts` | 69 files already formatted. |
| `Get-ChildItem frontend -Recurse -Filter *.js \| ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw "JavaScript syntax failed: $($_.FullName)" } }` | All 17 frontend scripts passed. Repeated after the final JS edits. |
| `Get-ChildItem tests/browser -Filter *.mjs \| ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw "Browser script syntax failed: $($_.FullName)" } }` | All 6 scripts passed. Repeated after the final browser-test edits. |
| `node tests/browser/test_money_display.mjs` | Passed unchanged exact-cent tests including large totals and negative fractions. |
| `.\.venv\Scripts\python -m scripts.check_structure` | Passed: 44 modules, acyclic imports, original HTTP contracts retained. |
| `.\.venv\Scripts\python -m compileall -q app` | Passed. |
| `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe` | **Final complete run: exit 0, all 14 checkpoint groups passed, zero runtime exceptions.** Includes native keyboard opening/folding, five-width open-scene overflow, real demo facts, no-transition/static fully visible reduced-motion arrival, event nonmutation and all retained product/browser/server-restart assertions. An earlier complete 14-group run also passed before the extra arrival assertions/captures. |
| `(Invoke-WebRequest http://127.0.0.1:8000/ -UseBasicParsing).StatusCode` | 200 from the existing local application. |

Intermediate failures are retained as evidence: the new Enter test initially omitted native key codes, so Edge did not perform native button activation. The fixture now dispatches full Enter down/up events and pairs Escape down/up; it still asserts actual activation/focus. Three restricted-sandbox browser attempts timed out at `Runtime.enable` on a blank page, before navigating to the application. An isolated diagnostic also failed to start Edge's debugging listener in that sandbox. Running the same existing isolated browser command outside that restriction succeeded. A later full rerun exposed an existing reload readiness race: the new document's time origin was visible before its submit button had parsed. The fixture now requires `submit-btn?.disabled === false` instead of dereferencing a missing button. This strengthens readiness and retains the same product assertions. No runtime-error filter, assertion removal, application timeout change or weaker test was introduced. Test servers/profiles/databases are temporary and separate from the live app.

Artifacts: `.artifacts/portal-experience/before/` preserves earlier screenshot references. `after/` contains closed/open desktop, open 1024/768/390/320 and reduced-motion captures; desktop and 320px images were opened for visual inspection. Existing motion checks also observed **CLS 0 at 1440/1024/768/390/320**, with no horizontal overflow. These are local observations, not production performance certification.

Final-run `opening-frames/frame-00.png` through `frame-07.png`, `opening.json` and `opening.html` provide eight actual Edge screenshots with timestamps spanning 3,912ms and a local playback/scrubbing viewer. All eight files were checked before generating the viewer. This is a short frame sequence, not encoded video or an FPS benchmark. Desktop, 390px and 320px invitation compositions were opened for visual review. The app remains available at `http://127.0.0.1:8000/`; refresh to load the enhancement.

## File inventory and remaining limitations

Created: `frontend/modules/portal.js`, `frontend/styles/portal.css`, `tests/browser/portal_smoke.mjs`, `docs/PORTAL_EXPERIENCE.md`.

Modified: `frontend/app.js`, `frontend/style.css`, `tests/browser/planora_product_smoke.mjs`, `tests/browser/motion_refinement_smoke.mjs` (reload-readiness fixture only), `README.md`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md`.

No original source file was removed or moved. Comparison against the 120-file source baseline archive confirmed unchanged backend and baseline Python test files. APIs, schema/migrations, configured SQLite path, ownership, budget reconciliation, scenarios, approval, stale/retry protection, AI boundaries and infrastructure security remain. No runtime database was reset, relocated or overwritten.

Launch: `.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers`. Default database: `<project>/data/eventra.sqlite3`, overridden by `EVENTRA_DB_PATH`. Existing single-instance SQLite, cookie recovery and per-process quota limitations still apply. Live Gemini, Docker, hosted ingress/CI, mobile thermal/FPS testing, formal assistive-technology checks and browsers other than local Edge were not verified. The two existing Starlette/HTTPX and google-genai deprecation warnings remain unsuppressed.
