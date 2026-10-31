# Planora AI final integration, security and readiness audit

30 October 2026, Asia/Calcutta. Scope: the current **uncommitted working tree**, not a hosted release or only the last Git commit.

## 1. Executive summary

The existing product is suitable for a **supervised local hackathon demo** after restarting the server. Core planning, exact-cent budgets, guest management, negotiation, Command Center, approved public invitations/RSVP, and existing Rescue/scenario workflows have real persistence and regression coverage. They are not merely interface mockups.

**Production readiness is not established.** A restricted public demo is conditional on verified TLS/proxy configuration, one durable SQLite instance/worker, backups, fictional/minimal data, abuse/cost controls and a hosted smoke test. An unrestricted real-user deployment is not recommended on current evidence. Passing local tests does not certify security, identity, supplier facts, scalability or external availability.

Four reproducible defects were repaired, with seven new Python regression cases and two new browser checkpoint groups. No new product feature, login, dependency, database migration/location change, ownership replacement or landing redesign was introduced. Existing uncommitted user changes were retained. Tests used isolated temporary databases/browser profiles; the real database was inspected read-only.

Fresh starting verification: **889 passed, 2 warnings, 188.55 seconds; 98.31% combined statement/branch coverage**. Final measured verification: **896 passed, 2 unchanged warnings, 143.87 seconds; 98.31% coverage**, with the existing **90% gate unchanged**. The full browser regression completed **30 checkpoint groups**, retaining the 28 existing groups and adding actual cross-checklist and public-timeout checks. Final execution details and boundaries follow below.

## 2. Architecture and repository reviewed

Starting inventory: **233 files** under `app`, `frontend`, `tests`, `scripts` and `docs`, excluding bytecode. All **79 application Python modules** parse/import without cycles; the original frozen HTTP contracts remain intact. Route inventory found **61 decorated declarations in `app/api`**, of which **52 have the explicit owner dependency**. These are declaration counts, not a count of unique paths or proof of security by counting.

The nine other API declarations are deliberate stateless/read-only boundaries: fictional demo illustration, brief extraction, health, legacy plan/chat/calendar, and the three public invitation routes. Entry-point root/docs/static routes were reviewed separately. New products were not inferred from documentation: actual handlers, schemas, repository calls, renderers and controls were traced.

Reviewed documentation: README, `BUG_SECURITY_AUDIT.md`, `GUESTS_NEGOTIATION.md`, `EVENT_DAY_COMMAND_CENTER.md`, `EVENT_WEBSITES.md`, upgrade audit/plan, budget rules, deployment/security guidance, dependency manifests, CI, Docker and ignore/release configuration. Third-party Swagger assets were checked through existing pinned-asset/license/source/inclusion tests; this is not a line-by-line independent audit of that upstream bundle.

| Layer | Actual architecture and reviewed boundary |
| --- | --- |
| Entry point | `app/main.py`; proxy → security guard → actual-chunk body cap → gzip → router. Router composition, startup error handling, local Swagger and static serving retained. |
| HTTP/contracts | `app/api`, `app/schemas`; owner dependencies on private event operations, strict child/request schemas, UUID membership, current revisions and explicit approvals. |
| Business logic | `app/services`; one deterministic budget/scenario engine, largest-remainder allocations, Decimal/HALF_UP ledger and server-grounded advice. AI is not an accounting or apply engine. |
| AI | Existing `app/ai/gemini.py` transport, structured user role and separate system instructions, prompt/output bounds and fallbacks; saved advice/intake/decision/design/readiness/negotiation/Command Center/website paths inspected. |
| Persistence | `app/db` and repositories; SQLite schema 2, supported v1 migration, parameterized values, owner-scoped reads, CAS/write transactions and additive format-1 feature tables. No database replacement. |
| Frontend | Existing HTML/CSS/ES modules; state, hash routing, text-node helpers, shared API transport, unsaved guards, loading/error/retry paths, domain editors and deterministic website renderer. No npm production build or new bundler. |
| Release | Windows CI snapshot, runtime requirements, Python 3.12 Docker definition, `.env.example`, private-file ignore rules, candidate-index audit and deployment limitations inspected. Hosted execution is separate and unverified. |

### Consistency and overlap

- Guest/Command Center writes advance the event revision and conservatively stale older scenarios. Website drafts/publication and negotiation drafts have independent versions; they do not mutate the financial ledger. This separation is intentional.
- Public pages use a separate allowlisted snapshot; owner-only drafts, guest records, quotes, budgets and incidents are not serialized into it. Private changes cannot silently update the published snapshot.
- The legacy checklist owns planning-step completion; Command Center additionally owns the event-category milestone. Their overlap caused F1 below and is now explicitly preserved in both browser requests and backend updates.
- Public page fetches duplicated transport behavior and lacked its timeout. They now reuse the existing client. No separate RSVP/guest database or second AI/provider system was added.
- Date-only planning/scenario freshness uses the existing server calendar convention. Command Center/public website times are aware and can use a configured IANA timezone. Their readiness/phase measures are explicitly different from the original planning heuristic and the fourteen-check readiness report; they are not interchangeable scores.
- Template tasks and custom event-day operations share the Command Center projection. Financial scenarios still operate on original planning state; no minute-by-minute automatic rescheduling engine or inferred duration was found or claimed.

## 3. Workflows exercised

| Workflow | Actual traced/executed checks | Boundary/limitation |
| --- | --- | --- |
| Core events | Real browser create, edit/rebuild, rename, checklist/chat, multi-event isolation, confirmed delete, browser reload and browser/server restart; stale revision, owned UUID and migration tests. | Type changes require a new event; currency conversion is not supported. |
| Budget Guardian / scenarios / Rescue | Expense CRUD, explicit allocations, Decimal/cents, paid/committed floors, reserve/exposure warnings, all six isolated scenario types, compare/discard/approval, stale/day rejection, rollback and idempotent application. Real browser approval/restart tests retained. | Unknown quotes/contracts remain indeterminate. No payments/refunds, FX or independently verified supplier prices. |
| Guests | Add/edit/remove/search/group/status filters, four RSVP states, plus-one counts, dietary/accessibility/notes, totals, failure retention, ownership and restart persistence. | Confirmed roster totals remain separate from saved planning headcount. Public responses are unverified. |
| Negotiation | Existing quote selection and actual Quote Analyzer handoff/comparisons, server-grounded generation, edit/regenerate/copy, explicitly saved versioned draft, stale/conflicting edits and restart. | No email/WhatsApp/call/booking/payment transport. Generated requests are not achieved savings or agreed terms. |
| Command Center | Existing/custom task status/notes/time/owner/vendor/dependencies, original/expected/actual distinction, arrivals, incidents/Rescue handoff, deterministic readiness and activity, CAS/concurrency/rollback/retries. New browser test completes the event milestone and saves both legacy timeline and vendor checklists without losing it. | Operator reports are not live verification. Retired metadata retains storage capacity; there is no archive UI. |
| Invitations | All four themes, editor/default data, actual shared preview, hash/approval-bound publish, isolated private edits, update/unpublish/republish/stable URL, separate anonymous browser RSVP → original roster, hidden-field privacy, print CSS, failure retention and restart. Already-open public page revocation remains covered. | Public URLs are unlisted, not password protected. Printing/downloaded copies cannot be recalled. No personal-image uploads or PDF/image export. |
| Public retry | New real browser intercepts public GET and RSVP before response headers. Actual AbortController timeout reveals retry controls, retains input and request UUID, then saves exactly one guest after retry, without budget changes. | The 45-second client fetch timeout is not a certification of every response-body/network/ingress deadline. |
| AI / fallback | Injected valid output, missing client/credentials, timeout/permission/quota exceptions, empty/malformed/non-object/extra/stale/foreign/code-like outputs, role/data separation and approval/ownership/math protections. Thirty offline evaluation fixtures retained. | No valid live Gemini request, real quota outage or provider accuracy certification. Semantic/narrative correctness is not completely solved. |
| UI / landing | Desktop/tablet/mobile routes, 320–1440 widths, keyboard/menus, reduced motion, CSS 3D/scroll/WebGL fallback/idle checks and static failure handling. | Not a formal WCAG/screen-reader, hardware FPS or production Core Web Vitals assessment. |

## 4. Security findings by severity

No **Critical** exploit was reproduced in this local scope. That does not prove none exists. High items below are open deployment/abuse readiness gaps, not invented remote exploits or claims of fixed vulnerabilities.

| ID / severity | Evidence and effect | Status |
| --- | --- | --- |
| F1 — Medium, cross-feature integrity | Command Center can mark the event-category milestone complete. Legacy browser progress included its ID, which the old endpoint rejects (422); a valid legacy planning-only update instead cleared that completion because it reset every task. Two API regressions failed before repair. | **Fixed.** Browser sends only legacy planning IDs; backend updates those tasks only. Event-day completion and actual timestamp survive unrelated saves. Existing event-ID rejection contract retained. Real browser timeline/vendor saves verified. |
| F2 — Medium, public UI reliability | Public invitation GET/RSVP used raw fetch with no abort deadline. A deliberately stalled request left loading/disabled form without a retry; the pre-fix browser failed waiting for error controls. | **Fixed for the reproduced stall.** Reuse the existing 45-second API client, retain explicit no-store and public timeout wording, attach status to HTTP errors for 404 revocation. Actual timed-out GET/POST recovery, retained payload/UUID and one-row save verified. |
| F3 — Low, bounded-state reliability | A valid stored `DayDocument` at its 200-overlay cap can retain metadata for retired templates. Adding an otherwise permitted visible task caused an unhandled model-validation 500 after appending entry 201. This needs that stored history shape; it is not a demonstrated remote ownership exploit or common current-template workflow. | **Fixed.** Check persisted capacity before adding a new overlay; return 422 with headers and retain all records. Isolated fixture reproduces 500 before repair and verifies rollback/no deletion after repair. |
| F4 — Medium, stored-record integrity | Direct workspace reads checked revision but not document UUID versus SQL row UUID; listing checked neither metadata field. Schema-valid inconsistent stored data could return a misleading event identity/revision. Three of four targeted cases failed before repair. Requires preexisting storage inconsistency/corruption; not a remotely reproduced IDOR. | **Fixed.** Shared row/document identity and revision check on direct reads and listing; safe 503, no automatic data repair, other event unchanged. Valid existing data preserved. |
| R1 — High, deployment/data durability | SQLite file persistence requires one durable instance/worker; serverless/container replacement or multiple hosts do not provide a shared durable store. Cloud Run `K_SERVICE` deliberately disables saved workspaces. No hosted storage/replacement test or Docker run was available. | **Open readiness blocker.** Use supported durable hosting and test replacement/restart, correct volume permissions and backups before real public use. Do not unset guards to hide unsupported saves. |
| R2 — High, public abuse/resource readiness | IP quota is bounded and locked but process-local. Public RSVP intentionally accepts unverified registrations within 500-guest/1000-receipt and party caps. Anonymous event creation and workspace history/chat/scenario retention have no global storage/user budget. Distributed traffic/cost/spam controls are not verified. | **Open.** Restrict a demo, use fictional/minimal data and operator monitoring; verify ingress/concurrency/provider-budget/storage controls before unrestricted traffic. No CAPTCHA/identity/quota product feature was added in this audit. |
| R3 — Medium, recovery/retention | No account/cookie recovery, automatic backup/restore certification or comprehensive retention mechanism. Owner cookie expires after 365 days and valid requests do not renew it; events may be planned up to three years ahead. Stored data can outlive access credentials. | **Open known limitation.** Preserve the browser profile/cookie and storage; test backups. Ownership recovery/session lifecycle belongs in the later explicitly scoped authentication/recovery milestone. |
| R4 — Medium, release assurance | Hosted TLS/canonical-host/trusted ingress, Secure-cookie behavior at that ingress, Linux/Python 3.12 Docker resolution, dependency advisories, live Gemini/costs and production load have no execution evidence here. Runtime manifests use version ranges. | **Unverified.** Complete the target-environment checklist below. `pip check` is dependency consistency, not a CVE audit. |
| I1 — Informational | Public schemas are separate, hidden fields omitted/null, secrets not returned, UUID child membership and all 52 private owner dependencies retained. SQL values are parameterized, output uses text nodes, image/code inputs are constrained. | Existing protections inspected and negative tests pass; not a complete penetration test. |
| I2 — Informational | `/healthz` reports stateless liveness even if saved storage is unavailable. Scenario evaluation uses server-calendar day; public/operational timezones and phase/readiness assumptions are disclosed. | Intended behavior retained. Do not use health alone as proof of a functioning persistent/public product. |
| I3 — Low maintenance warning | Starlette/HTTPX TestClient deprecation and google-genai `_UnionGenericAlias` deprecation remain. No dependency advisory tool is installed. | Not suppressed or “fixed” through a speculative dependency upgrade. Plan controlled dependency maintenance and an advisory scan. |

### Specific boundary checks

- Owner cookie: random 32-byte bearer token; HttpOnly/SameSite=Strict, Secure on verified HTTPS, only its hash in storage. UUID alone does not authorize access. Direct/foreign event, guest, vendor, incident, scenario, website and negotiation access tests remain.
- CSRF/CORS: same-origin/fetch-site checks and cookie policy retained; no new permissive CORS. Public RSVP uses the same origin check and does not create an ownership session or expose guest records.
- Proxy/quota: forwarding headers are ignored unless the socket peer matches configured canonical networks. Malformed/spoofed/all-trusted chains fail safely; wildcard trust is rejected. Sliding-window expiry, high cardinality, capacity rejection and concurrency tests pass.
- Body/headers: actual ASGI chunks are counted before bounded buffering; missing/misleading lengths, streaming/disconnect/oversize and early-rejection tests pass. CSP, nosniff, frame denial, referrer policy and API/public no-store remain. Middleware order unchanged.
- XSS/SQL/URLs: no user-controlled eval/HTML execution or arbitrary backend URL-fetch/upload route was found in the inspected paths. Model text is untrusted display data. Quote import is bounded labeled text; website image keys/hex colours are allowlisted. Script source scans are supporting evidence, not a proof against all injection classes.
- AI: server roles/configuration separate from untrusted content; bounded/validated outputs and offline fallback. Imported quote sources stay local; guest roster is not supplied to AI. Some legacy planning paths intentionally send owner-provided event preferences/questions to the configured provider; use fictional/minimal data unless provider/privacy handling is appropriate.
- Transactions: event/child/receipt/history writes use CAS and appropriate SQLite transactions. Publication snapshots are independent of drafts; every public access/RSVP checks current publication/edition. No automatic send, financial application or publication path was added.

## 5. Repairs and exact changed files

Production files changed **only in this audit**:

1. `app/api/workspaces.py`: preserve event-category completion during legacy progress updates.
2. `frontend/app.js`: exclude event-category IDs from the legacy progress request, matching its unchanged schema/rules.
3. `app/services/command_center.py`: explicit stored-overlay capacity rejection before mutation/serialization.
4. `app/repositories/workspaces.py`: validate row/document UUID and revision for get/list.
5. `frontend/modules/api.js`: optional cache/timeout-message context and HTTP error status, while retaining the existing 45-second timeout and existing call defaults.
6. `frontend/invitation.js`: reuse that client for public fetches; retain retry, no-store and unpublication clearing behavior.

Created tests: `tests/integration/test_final_audit.py` (7 cases), `tests/browser/final_audit_smoke.mjs` (2 groups). Modified `tests/browser/planora_product_smoke.mjs` only to import/append those groups; earlier assertions/timeouts remain. The timeout fixture accelerates the **test document's** existing 45-second timer to one second; production timeouts were not shortened and the test verifies actual abort/retry behavior, not just prompt wording.

Created this report. README and upgrade audit/plan link to this current outcome; earlier feature reports remain dated historical evidence. No financial engine, AI prompt/strategy, request schema, security policy/order, dependency, deployment manifest, database definition/location or original landing file was changed by these repairs.

Hash comparison: **the entire `frontend/index.html` and all 16 recorded landing/3D source/style/artwork files remain byte-for-byte unchanged** from this audit's starting tree. Existing dirty feature/portal/security files were not discarded, reset, committed or pushed.

## 6. Executed verification and evidence

Private logs/source hashes/route inventory are under ignored `.artifacts/final-audit/`. They contain local fixture execution evidence and are not bundled as public release data.

| Check | Actual result |
| --- | --- |
| Clean baseline full Python + coverage | 889 passed; 2 existing warnings; 188.55s; 98.31%. |
| Pre-fix new regressions | 3 failed (two checklist preservation cases plus capacity); separate row-metadata run 3 failed/1 passed. Stalled public-page browser timed out waiting for retry controls. |
| Targeted security/new-feature regression | 326 passed; 2 existing warnings; 76.43s after the first repairs. |
| Persistence/metadata targeted | 44 passed; 1 existing warning; 5.73s. |
| Final new Python regressions | 7 passed; 1 existing warning; 1.63s. |
| Final full Python + coverage | **896 passed; 2 existing warnings; 143.87s; 98.31%**. Original 889 retained; floor 90% unchanged. |
| Full real Edge/Uvicorn browser | **30 checkpoint groups passed**, zero runtime exceptions; includes original 28, real cross-checklist updates, intercepted timeout/retry, restart/public/privacy tests. |
| Ruff lint / formatting | Passed; **127 files already formatted**. |
| JS syntax | **52 authored scripts** and the pinned Swagger bundle checked with Node. |
| Structure / original HTTP contracts | Passed; **79 acyclic modules**, frozen original contracts retained. |
| Exact money / decision delta / portal geometry | All existing Node checks passed. |
| Offline AI evaluations | **30/30 cases passed** across planning, intelligence and readiness. |
| Dependency consistency / Python compilation | `pip check` and `compileall` passed. |
| Candidate release / diff | Local candidate inclusion/size/private-path/obvious-secret-pattern audit and `git diff --check` passed. This does not certify Git history, all PII, CVEs or hosted CI. |
| Existing real database, read-only | Schema 2; quick_check `ok`; zero foreign-key violations; **3/3 workspace documents validated**; current tables `events`, `scenarios`. New feature tables are lazy; their creation/migration/cascade behavior was tested on temporary data, not added to this file. |

No npm production build, TypeScript checker or configured Python static type checker exists; none is claimed passed. Real Uvicorn startup/health/static/API loads and schema/migration/import checks were executed through the existing harness and suite. Docker is unavailable (`Get-Command docker` found no executable); `python -m pip_audit --version` returned **No module named pip_audit**. No container/advisory/hosted/live-provider pass is claimed.

Exact executed commands, from `D:\Projects\eventra`:

```powershell
git status --short
$env:COVERAGE_FILE='.artifacts/final-audit/baseline.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_final_audit.py
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_final_audit.py -k metadata_mismatch
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_final_audit.py tests/integration/test_command_center.py tests/integration/test_websites.py tests/security
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_final_audit.py tests/integration/test_workspaces.py
$env:COVERAGE_FILE='.artifacts/final-audit/final.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -B -m ruff check app tests scripts --no-cache
.venv/Scripts/python.exe -B -m ruff format --check app tests scripts
.venv/Scripts/python.exe -B -m scripts.check_structure
.venv/Scripts/python.exe -B -m pip check
$auditScripts=@(Get-ChildItem frontend -Recurse -Filter *.js)+@(Get-ChildItem tests/browser -Filter *.mjs)
foreach($auditScript in $auditScripts){node --check $auditScript.FullName}
node --check vendor/swagger-ui-5.34.0/swagger-ui-bundle.js
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
node tests/browser/test_event_portal_geometry.mjs
.venv/Scripts/python.exe -B -m scripts.evaluate_planning
.venv/Scripts/python.exe -B -m scripts.evaluate_intelligence
.venv/Scripts/python.exe -B -m scripts.evaluate_readiness
node .artifacts/final-audit/timeout-driver.mjs .venv/Scripts/python.exe
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe
$env:PYTHONPYCACHEPREFIX=(Join-Path (Get-Location) '.artifacts/final-audit/pycache')
.venv/Scripts/python.exe -m compileall -q app scripts tests
Remove-Item Env:PYTHONPYCACHEPREFIX
.venv/Scripts/python.exe -B -m scripts.audit_release
git diff --check
Get-Command docker -ErrorAction SilentlyContinue
.venv/Scripts/python.exe -m pip_audit --version
```

The ignored timeout driver composes the original temporary-server/profile harness and pointer helpers with the checked-in timeout assertions. Baseline/failure/final logs are distinct; failed reproduction runs were not hidden. Native line-ending normalization notices from Git are not test failures. No test assertions, coverage floor or browser debugging timeouts were weakened.

## 7. Known limits and unverified areas

- One durable SQLite instance/worker; no distributed persistence/quota, hosted ingress/storage replacement or disaster-recovery test. Backups and filesystem permissions/encryption/retention need deployment verification.
- Anonymous bearer-cookie access, no account recovery/sharing/session-recovery workflow. Keep the same browser profile and DB. Login/signup remains expressly outside this audit.
- Unverified public RSVPs, open-link sharing and best-effort duplicate matching; no delivery, CAPTCHA or identity verification. Host review remains necessary.
- Finite guest/expense/operational/receipt caps, no operational-history archive UI; some other workspace/history/scenario storage remains unbounded. Global traffic/disk/cost limits are not established.
- Mixed disclosed calendar conventions; no verified vendor availability, prices, minute-duration scheduling, payment processing/refund/FX or emergency monitoring.
- The client timeout covers stalled fetch/request establishment; response-body/ingress/network concurrency/deadline behavior was not comprehensively tested. Already downloaded public information cannot be recalled.
- Gemini failure tests are injected/offline. No live credentials/model availability/provider accuracy or billing check. Some legacy narrative remains advisory rather than formally semantically validated.
- Full WCAG/screen-reader, real device/hardware performance, load/soak, network penetration, supply-chain/CVE/Git-history/PII scans and hosted CI are unverified. Two existing deprecations remain.

## 8. Production deployment checklist

- [ ] Freeze/review the tested working tree and candidate manifest before the owner commits/releases it; protect keys, DBs, logs, browser profiles and archives. No commit/push/deployment was performed here.
- [ ] Resolve/install and test runtime dependencies for the actual OS/Python target; run an available advisory scanner and review the pinned Swagger asset update policy. Windows consistency tests do not certify the Python 3.12 Linux image.
- [ ] Provision a single durable writable `EVENTRA_DB_PATH`, correct directory/journal permissions and capacity monitoring. Keep the ownership context; verify real restart/container-replacement persistence and transactional failure behavior.
- [ ] Perform a backup and restore drill, protect backups/cookies and establish retention/recovery procedures. Do not delete/recreate the database to resolve a startup problem.
- [ ] Configure canonical TLS origin/HTTPS redirects and applicable ingress headers, validate Secure-cookie/origin behavior, explicitly trust only verified proxy addresses and block backend bypass. Retain Uvicorn `--no-proxy-headers`; never use wildcard trust to make a deployment appear functional.
- [ ] Use deployment ingress/concurrency/body/time/resource protections, a verified provider spending budget and operational alerts. Process-local IP limits and `/healthz` alone are insufficient for persistent-product readiness.
- [ ] For any public demo, use minimal/fictional data, restrict access/traffic as appropriate, approve only intentional public fields and verify live update/unpublish/RSVP/cookie boundaries from another browser/client.
- [ ] Keep AI optional; if enabled, verify the chosen live model, quota/failure behavior and data-handling suitability without exposing credentials. Offline demo remains available.
- [ ] Run the full regression and an end-to-end hosted smoke/restart test for the actual release. Address open High readiness items before real-user production use.

These unchecked items are prerequisites and unverified work, not actions already completed or new features silently implemented.

## 9. Recommended next steps before the hackathon demo

1. Restart from the current repository root and use the existing browser profile. Confirm the owned saved-event list and offline mode; keep a separate fictional demonstration workspace.
2. Rehearse one coherent path: create → budget/guest edits → quote-based negotiation → Command Center → invitation preview/publish/public RSVP → explicit What-if/Rescue review. Demonstrate approvals and unknown-price limits rather than implying autonomous execution.
3. Use a reachable, properly configured durable TLS host only if an external link is needed; otherwise present locally. Keep real guest/private operational data out of an unverified public environment.
4. Keep backup/profile access and a deterministic offline fallback ready. Schedule the explicitly separate authentication/recovery and deployment-assurance work after the demo scope is stable.

Exact local restart (stop an older running instance with Ctrl+C in its own terminal first):

```powershell
cd D:\Projects\eventra
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Open `http://127.0.0.1:8000`. No new package or environment variable is required. `.env` is not auto-loaded; use the existing explicit `--env-file .env` option only if that is how local secrets/configuration are maintained. The default database remains `<project>/data/eventra.sqlite3`. No real event was automatically published and no vendor/guest message was sent by this audit.
