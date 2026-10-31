# Planora AI bug hunt and security regression audit


Status update, 30 October 2026: the Event Website & Invitation Generator now provides private drafts and explicitly approved public snapshots, four deterministic themes, stable random links, revocation and controlled create-only RSVP into the existing roster. Public schemas exclude private event/guest/vendor/financial/operational data; CSP remains unchanged and no-store/quota cover the new public page path. [EVENT_WEBSITES.md](EVENT_WEBSITES.md) records exact security behavior, 72 new cases, 889 passing tests / 98.31% coverage and 28 passing browser checkpoints. Earlier website/RSVP missing-feature entries below are historical. Unverified identity/abuse and durable single-instance deployment limits remain.

Status update, 29 October 2026: Event Day Command Center now adds event-owned operational tasks/arrival/incident/activity persistence, human-approved writes, constrained AI ordering and a handoff to the existing Rescue approval flow. See [EVENT_DAY_COMMAND_CENTER.md](EVENT_DAY_COMMAND_CENTER.md) for current behavior and evidence. The audit matrix below is a historical snapshot; its missing event-day workflow finding is superseded by that report. Production, live provider and distributed storage readiness remain unverified.

Status update, 29 October 2026: the previously missing Guest List/RSVP Manager and Vendor Negotiation Assistant are now implemented. See [GUESTS_NEGOTIATION.md](GUESTS_NEGOTIATION.md) for their current scope and execution evidence. The workflow matrix below records the earlier 28 October audit snapshot.

28 October 2026, Windows / CPython 3.14.2 / Node 25.9.0 / Edge. This is a local audit and focused repair of the existing product. No login, new planning feature, financial engine, schema migration, event reset, commit, push or hosted deployment was added.

## Starting state and inspection

The working tree already contained the uncommitted Event Portal changes. They were retained. Baseline source hashes are private under `.artifacts/bug-audit/pre-fix-hashes.json`; this stage modifies the existing product only where listed below. The existing README, upgrade audit/plan, accounting rules, configuration, CI, Docker, Python modules, ES modules, HTML/styles, persistence/AI and existing regression infrastructure were reviewed.

The local route/control inventory contains **41 decorated route declarations and 180 static interactive elements**, with no duplicate static IDs. Dynamic editors and controls are defined in the frontend modules and exercised by the browser harness. Inventory: `.artifacts/bug-audit/inventory.json` (before the additional explicit docs handler). The original OpenAPI contract checker still passes; counting HTML controls is not proof that every possible interaction was tested.

Fresh baseline: **684 passed, 2 warnings, 24.20s; 98.78% combined statement/branch coverage**. No baseline test failed. The existing no-bundler frontend has no production asset build, package.json, TypeScript or configured static Python type checker. Python compilation, module/contract checks, JS syntax, strict schemas, real ASGI startup and actual browser rendering are the applicable local checks; no nonexistent build/type-check command is claimed successful.

## Findings and fixes

**Five reproducible defects identified; five fixed. No critical unresolved exploit was reproduced in this local scope. This is not a claim that no vulnerabilities exist.**

| ID | Reproduction / consequence | Root cause and repair | Regression |
| --- | --- | --- | --- |
| B1: unexpected-error response protection | Inject an unexpected exception into `/api/plan`: JSON 500 had no CSP/security headers or `Cache-Control: no-store`. | Starlette's outer server-error handler emits its response outside the HTTP guard. The generic handler now applies the same `secure_response` policy. Error body, middleware order, body cap, quota and normal error handlers stay intact. | Actual 500 and 503 responses must retain every existing security header/no-store and must not disclose the exception sentinel. |
| B2: calendar content-line boundary | A valid title containing a lone carriage return survives calendar escaping, leaving raw CR in exported data and exposing permissive importers to injected calendar properties. | Escape normalized CRLF and lone CR to LF, then the calendar text escape. Preserve existing comma/semicolon/backslash escaping and UTF-8 folding. | Both saved and stateless exports test CR, LF and CRLF, no lone CR or injected ATTENDEE content line, and retained headers. |
| B3: calendar identity collisions | Two different events exported in the same second share timestamp/index UIDs; reexports also change identity as the clock changes. Calendar importers can merge unrelated milestones or duplicate reexports. | UUID milestone namespaces replace timestamp identity. Saved export namespace uses the owned workspace UUID; stateless exports receive a fresh namespace because no persistent identity exists. DTSTAMP remains an export timestamp. | Distinct events/namespaces/identical stateless exports have disjoint UIDs; saved identity survives reexport/time/title changes. |
| B4: Escape/navigation | Real mobile browser: open public navigation, focus a link, press Escape; menu stays open. Global Escape also attempts sidebar focus restoration when no sidebar is open. | Limit sidebar dismissal/focus restoration to an open sidebar. Public navigation now closes on Escape and restores its own toggle focus. | Native keyboard checks for desktop focus retention, mobile public dismissal/toggle focus and closed-sidebar studio focus; existing sidebar Escape tests retained. |
| B5: API docs blocked by CSP (historical R12) | `/api/docs` returns self-only script/style CSP while its generated Swagger page requires a CDN and inline bootstrap. | Serve the same Swagger UI capability locally at the same URL, with external same-origin bootstrap, unchanged CSP, and no external validator. Pin official `swagger-ui-dist` 5.34.0 assets and retain Apache-2.0 LICENSE/NOTICE. Verify registry tarball SHA-512 before copying selected files. | Local-only asset/HTML tests plus real Swagger operation rendering/expansion with all external HTTPS requests blocked and zero CSP violations. |

Before repairs, the first new Python module produced **4 failed / 5 passed**, reproducing B1, two B2 paths and B3. The original mobile browser failed the public Escape assertion, reproducing B4. The new docs regression failed on the original inline bootstrap, reproducing B5. Original tests/assertions/coverage floor were not weakened or removed. A first docs browser fixture did not install its CSP observer because CDP Page events were disabled; enabling Page before new-document injection repaired the fixture without relaxing its assertions.

Saved calendar UIDs now remain stable for existing generated template milestone indices. Existing calendar files downloaded before this repair cannot be rewritten; a calendar client may require removing old duplicate entries and reimporting. Stateless exports intentionally cannot deduplicate independent plans without saved identity. This is not a two-way calendar synchronization feature.

## Product/data integrity and security inspection

| Area | Actual implementation and verification | Limits |
| --- | --- | --- |
| Events/tasks/vendors | Owner-hash queries, UUID child membership checks, revision CAS and stable task/vendor reconciliation. Browser create/edit/checklist/chat/rename/reload, multi-event isolation, delete and browser/server restart tests exercise saved state. | Tasks/vendor groups originate in templates. Arbitrary task creation and a general vendor catalog are not implemented. |
| Anonymous ownership | HttpOnly, SameSite=Strict browser cookie, Secure on HTTPS; only its hash reaches SQLite. Mutation Origin/fetch-site checks remain. Existing foreign-owner/event/child tests pass. No mandatory account was introduced. | Cookie loss means loss of access; no recovery, accounts or cross-device sharing. Trust/HTTPS depend on correctly configured ingress. |
| Database | Existing schema 2 retained. Read-only live database `quick_check` returned OK; foreign_key_check empty; all **3** live workspace documents validated. Temporary-database tests cover supported v1 migration, malformed schema fail-closed behavior, cascade deletion, CAS races/rollback and design preference migration. | No live database migration was required or performed; no live record was edited/deleted by this audit. SQLite still requires one durable instance/worker. No disaster-recovery certification. |
| Exact budget | Decimal/HALF_UP ledger, BigInt display, per-guest quantities, unknown-price/reconfirmation warnings, commitments/paid floors and protected reserve preserved. Existing CRUD, rounding, currency, guest-change and scenario tests pass. | Planned headcount is not RSVP attendance. Fixed/all-in prices require explicit reconfirmation; no FX/refunds/payment execution. |
| Timeline | Saved template deadlines/dependencies/completion, date scenarios, read-only delay propagation and corrected calendar export verified. | No persisted event-day task owners/durations/incident schedule; server calendar day rather than event timezone. |
| What-if/Rescue | Six commands deep-copy state; owner/revision/day checks, fresh recalculation, feasibility, approval, transaction and retry rules remain. Existing pending/discard/nonfeasible/stale/rollback/retry tests and real approve/restart workflows pass. | Unpriced or unreleased contractual exposure stays indeterminate; no automatic supplier contact, availability or liability release. |
| SQL/input/XSS | Persistence SQL values are parameterized; owned lookup/membership precedes child use. User/AI text uses DOM text nodes; strict structured actions and palette/category validation retained. Body/chunk/header/disconnect/proxy/quota tests pass. | Source review/tests are not a comprehensive penetration test or formal proof. No history/PII scan certification. |
| Public invitations | Existing homepage invitation is a fictional read-only animation; exports are owned calendar endpoints. No public event-site publishing or anonymous RSVP endpoints exist. | Workflow F cannot be called implemented. There is no public invitation data exposure surface to validate end to end. |
| UI/animations | Existing floral, invitation, scroll and WebGL portal assets/controllers remain. Browser tests cover desktop/tablet/mobile widths, forms, error retention, native dialogs/menu keys, reduced motion, context fallback, no idle portal renderer and persisted approvals. | Local checks do not establish complete screen-reader/WCAG, production FPS/Core Web Vitals or all-device certification. |
| Dependencies/release | pip dependency consistency and local release-candidate secret/path/size checks pass. Credentials/runtime DB/profiles/archives stay excluded. Pinned Swagger assets load only in API docs. | No exhaustive vulnerability-feed, supply-chain, full Git-history or hosted-CI audit was performed. Runtime version ranges and the pinned docs bundle require future security maintenance. |

AI review traced legacy generation/chat, saved advice and interpretation, intake, decision previews, design ordering and readiness ordering. Fixed server roles/configuration remain separate from escaped untrusted data. Provider outputs must match server schemas/allowed IDs and current revision; narrative never computes/apply money. Quote source text is parsed locally and does not go to Gemini. Exact prompt/key echoes are rejected, but semantic prompt injection is not claimed completely solved.

The additional provider matrix exercises six read-only analysis endpoints with permission/invalid-credential, timeout, provider-quota exceptions, empty/malformed/nonobject JSON, unauthorized-action output and malformed Unicode content. Every response remains usable and saved event documents, summaries, scenarios and preferred design remain unchanged. Private exception details do not reach responses or provider logs. These are injected failure tests, **not real invalid-key/timeout/quota calls to Google**. Missing credentials/offline paths and existing adversarial/ownership/approval tests also pass. Valid live Gemini credentials/model availability were not tested; optional `GEMINI_API_KEY`/`GOOGLE_API_KEY` is still required only for live AI.

## Requested end-to-end workflows: exact status

| Workflow | Verified scope | Unsupported remainder |
| --- | --- | --- |
| A: planning | Create owned event, generated tasks/vendor groups, edit vendor/status, budget/expense edit, checklist completion, save/reload and restart persistence. | Arbitrary task/vendor-group creation is not present; do not claim its UI was exercised. |
| B: guests | Saved headcount/dietary/accessibility; guest-count preview scales explicit per-guest quantities, requires reconfirmation of all-in costs, and applies only through approval; readiness reflects saved revision. | No individual guest records, RSVP edits or seating/capacity roster. Full requested workflow is incomplete. |
| C: Copilot | Saved contextual conversation plus Decision/Scenario Studio interpreted proposals, isolated review, explicit approval and persisted application. | Conversation itself cannot apply an action. No autonomous tool execution. |
| D: negotiation | Analyze labeled text sources, compare two quotations, explicitly record quote/commitment, preserve paid values and recalculate budget; actual browser tests pass. | No vendor message generator/sending or negotiation transport. Full requested workflow is incomplete. |
| E: event day | Persisted vendor status/checklist completion and read-only saved-dependency delay analysis are verified. | No command-center view, incident reporting/task ownership or automatic delay application/notifications. Full requested workflow is incomplete. |
| F: event website | Fictional landing invitation and owned calendar export verified. | No website generator, publish/save-public-link workflow or public RSVP. Full requested workflow is missing. |
| G: existing product | Guardian, six What-if types, Rescue, Design Studio, delay analysis and Readiness retain tests/browser approval/isolation/restart coverage. | Live external supplier/model accuracy and production multi-instance operation unverified. |

These missing capabilities were not turned into placeholder features during a bug-fix task.

## Files changed in this audit stage

Modified:
- `app/api/errors.py`: security policy on unexpected 500 responses.
- `app/services/engine.py`: calendar escaping and UID namespaces only; financial/timeline calculation code unchanged.
- `app/api/workspaces.py`: pass owned workspace calendar identity.
- `app/main.py`: same `/api/docs` GET/HEAD URL, self-hosted UI handler and narrow vendor mount.
- `Dockerfile`: include the required vendor assets in the existing image layout.
- `.github/workflows/ci.yml`: separate syntax check for the pinned vendor bundle; prior portal check retained.
- `frontend/modules/shell.js`: scoped Escape/menu focus repair.
- `tests/browser/planora_product_smoke.mjs`: retain original and portal checks; append audit navigation/docs checks.
- `tests/browser/event_portal_smoke.mjs`: add state diagnostics to the unchanged motion-transition assertion.
- `README.md`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md`: current findings/evidence.

Created:
- `tests/security/test_audit_regressions.py` (13 cases).
- `tests/security/test_audit_ai_failures.py` (8 failure-matrix cases across six endpoints).
- `tests/security/test_api_docs.py` (1 case).
- `tests/unit/test_calendar_regressions.py` (2 cases).
- `tests/browser/audit_regression_smoke.mjs` (navigation and strict-CSP docs checkpoints).
- `frontend/api-docs.html`, `frontend/api-docs.js`.
- `vendor/swagger-ui-5.34.0/swagger-ui-bundle.js`, `swagger-ui.css`, `LICENSE`, `NOTICE`, `swagger-ui-bundle.js.LICENSE.txt`, `README.md` (source/integrity/hashes/update policy).
- This report, `docs/BUG_SECURITY_AUDIT.md`.

**Database changes: none. Python/npm dependency manifest changes: none.** The docs UI previously fetched its browser dependency from a CDN; it now includes pinned licensed browser assets, approximately 1.88 MB. All existing uncommitted portal files and unrelated changes remain.

## Executed checks and evidence

Final Python verification: **708 passed, 2 unchanged warnings, 23.76s; 98.84% combined coverage**. All **24 new Python cases** pass, with every original case retained. The focused final repair/contract command passed **31 cases** before the vendor relocation, and the unchanged authored frontend checks passed **3/3** after relocation. **Final complete browser suite: 24/24 checkpoint groups, exit 0, zero runtime exceptions**, retaining all 22 prior groups plus navigation/docs checks. The required real-software-WebGL/policy run and dedicated navigation/docs checks also exited 0. Logs are private under `.artifacts/bug-audit/`; browser screenshots use the existing `.artifacts/` subdirectories. The ignored dedicated navigation/docs driver composes checked-in assertions with the existing temporary-server/CDP harness. All full browser runs use the checked-in original driver and isolated data.

```powershell
$env:COVERAGE_FILE = '.artifacts/bug-audit/baseline.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
$env:COVERAGE_FILE = '.artifacts/bug-audit/final.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/security/test_audit_regressions.py
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/security/test_api_docs.py
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/security/test_audit_ai_failures.py tests/security/test_audit_regressions.py tests/unit/test_calendar_regressions.py
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/security/test_api_docs.py tests/security/test_audit_regressions.py tests/security/test_audit_ai_failures.py tests/unit/test_calendar_regressions.py tests/integration/test_structure.py
.venv/Scripts/python.exe -B -m ruff check app tests scripts --no-cache
.venv/Scripts/python.exe -B -m ruff format --check app tests scripts
.venv/Scripts/python.exe -B -m pip check
.venv/Scripts/python.exe -B -m scripts.check_structure
.venv/Scripts/python.exe -B -m scripts.evaluate_planning
.venv/Scripts/python.exe -B -m scripts.evaluate_intelligence
.venv/Scripts/python.exe -B -m scripts.evaluate_readiness
$portalScripts = @(Get-ChildItem frontend -Recurse -Filter *.js) + @(Get-ChildItem tests/browser -Filter *.mjs)
foreach ($portalScript in $portalScripts) { node --check $portalScript.FullName }
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
node tests/browser/test_event_portal_geometry.mjs
node --check vendor/swagger-ui-5.34.0/swagger-ui-bundle.js
node .artifacts/bug-audit/navigation-driver.mjs .venv/Scripts/python.exe
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe
node tests/browser/asset_upgrade_smoke.mjs http://127.0.0.1:8000
.venv/Scripts/python.exe -B -m scripts.audit_release
git diff --check
```

Compilation executed with `PYTHONPYCACHEPREFIX` pointing to `.artifacts/bug-audit/pycache`: `.venv/Scripts/python.exe -m compileall -q app scripts tests`. The setting was removed afterward. The browser harness starts `uvicorn app.main:app --host 127.0.0.1 --port <temporary> --no-proxy-headers` and verifies actual HTTP/workspace behavior, including process restarts/migrations.

Docker was checked with `Get-Command docker -ErrorAction SilentlyContinue` and is unavailable, so no Docker build/runtime success is claimed. No frontend build/type-check command exists. No live Gemini, hosted Vercel/Cloud Run ingress, hosted CI or multi-instance behavior was verified. The two existing Python warnings are Starlette's HTTPX TestClient deprecation and google-genai's `_UnionGenericAlias` deprecation; they are not suppressed. Existing SQLite/cookie/proxy/process-local quota/cache limitations still apply. No claim of an error-free or production-certified application is made.


The first self-hosted assets were provisionally placed inside `frontend/`, whose application-specific recursive checks assume authored source and disallow third-party DOM internals/data URLs. A provisional full verification run stalled and was stopped, not reported as a pass; its precise stalled stack was not captured. The licensed distribution now lives separately under `vendor/`, with an explicit static mount and Docker copy. Existing source-safety tests are unchanged; the vendor code is checked separately for syntax/provenance and exercised with the real restrictive browser policy. A subsequent full Python run completed in 23.76s. One full browser run timed out while resuming the portal after a motion-policy change, with no runtime exceptions; focused required-WebGL/policy tests passed, transition-state diagnostics were added without changing assertions/timeouts, and the final sequential run passed all 24 groups. The earlier transition timeout remains recorded as an intermittent verification limitation, not a claimed repaired product defect. No production-load explanation is asserted without evidence.

Remaining deployment risks include process-local rate limits/cache, anonymous-cookie recovery limits and SQLite durability/single-instance requirements. Events, scenarios and chat/history have no per-owner retention quota; rate limits are not durable disk quotas. No arbitrary retention/deletion policy was introduced during this repair. Before exposing a high-volume deployment, durable storage, disk monitoring, quota/retention policy, actual ingress and optional live-provider behavior need separate verification. This audit does not establish an Internet-scale anonymous service.


Final additional checks: Ruff passed; format reported **103 files already formatted**; all **41 authored frontend/browser scripts plus the pinned vendor bundle** passed `node --check`; exact-cent currency, delta/percentage and portal geometry checks passed. All **30 offline evaluation cases** passed. `scripts.check_structure` verified **60 acyclic application modules and original API contracts**; pip check found no broken requirements; final Python compilation passed. The local disposable release-candidate audit passed with no private-path/secret-pattern findings and source/index size below its unchanged 10 MB limit. `git diff --check` passed with CRLF-to-LF normalization warnings only. No new feature, source test weakening or database mutation was used to obtain these results.

The final full coverage run used the command above with an additional `-vv` diagnostic flag. Before this final run, an intermediate complete run passed **707 / 98.84%** and 23 browser groups (before the API-docs repair); these intermediate results are superseded by **708 / 98.84% and 24 groups**. The initial 248-case security/body/engine/workspace targeted run passed; the new 23-case failure/calendar/security group passed before adding the docs case. Original clock/timing thresholds and coverage configuration remain unchanged.

The existing warm-cache/asset upgrade command also exited **0**: it reproduced and recovered the cached upgrade, checked the actual running homepage styling/sticky transforms with zero runtime errors and no event writes, and verified the stylesheet-failure fallback. The older already-running server was not restarted; backend manual verification should use a restarted process loading this working tree. The complete final browser suite used fresh servers and therefore tested the repaired backend.
