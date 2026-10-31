# Guest List & RSVP Manager and Vendor Negotiation Assistant

29 October 2026 (Asia/Calcutta). Implemented in the existing FastAPI/SQLite/vanilla-ES-module application. No login, public RSVP, communications transport, Event Day Command Center, website generator or homepage redesign was added. Existing uncommitted security/portal work was retained.

## Inspection and sequence

Read the current bug/security audit and inspected workspace ownership/revision checks, SQLite transactions/migrations, budget/expense/scenario accounting, quote analysis/comparison, saved design preferences, Gemini transport/strict outputs and workspace UI events/dirty-state guards. The pre-refactor OpenAPI fixture remains the compatibility authority. Baseline source hashes are private in `.artifacts/guests-negotiation/baseline-hashes.json`.

Fresh baseline: **708 tests passed, 2 existing warnings, 29.53s / 98.84% combined coverage**. Phase 1 guest backend/UI was implemented first; **24 guest tests** and its dedicated real-browser restart workflow passed before negotiation implementation began. The broader initial guest/workspace/contract targeted command passed **62 cases**. Phase 3 then implemented negotiation; its initial **30 tests** and dedicated browser workflow passed before full regression. Further ownership/concurrency/source-validation cases were added during verification. No failure was suppressed and no coverage threshold changed.

The guest workflow now has **25 Python cases** and negotiation **42**, **67 new cases** in total. Final full Python result: **775 passed, 2 existing warnings, 68.89s / 98.72% combined coverage**. The original 90% floor remains. Coverage changed from the baseline because the new routes/services add code; original cases remain. **Final complete browser suite passed all 26 checkpoint groups**, including all prior groups plus guest and negotiation workflows, with exit 0 and zero runtime exceptions.

## Guest behavior and integration

Each private guest record has a UUID, event UUID, name, optional email, Family/Friends/Colleagues/VIP/Other group, pending/confirmed/declined/maybe RSVP, 0-20 accompanying guests, dietary/access requirements, notes and timestamps. At most **500 primary guest records per event** are supported. Emails receive format validation, not deliverability verification. RSVPs are entered manually by the planner and apply to the named guest's entire party; there are no public response links, automated invitations or independent plus-one names/statuses.

The Guests workspace section retains the original planning-headcount/preferences and explicit What-if controls, then adds summary cards, a responsive list, case-insensitive name/email search, status/group filters, add/edit form, requirements/notes disclosures, loading/retry/error states and confirmed removal. User/guest text is rendered with existing text-node helpers, not HTML. Failed requests retain inputs. Leaving for a new event after confirming discard clears private unsaved fields. No guest PII is put in localStorage or passed to Gemini.

Counting rules:

- `records`: primary guest/party records.
- `total_invited`: all named guests plus their accompanying guests, including invitations later declined.
- `confirmed`, `pending`, `declined`, `maybe`: people in each status, including accompanying guests.
- `pending_responses`: primary parties still pending, not a count of their plus-ones.
- `expected_attendees`: confirmed people only; no invented attendance probabilities.
- `possible_attendees`: every non-declined person, including pending/maybe.
- Search/filter affects displayed records, never event-wide summary totals.

The saved **planning headcount remains separate**. RSVP writes do not silently update budget quantities, allocation, quotes, commitments or tasks. The explicit Review confirmed headcount button transfers a valid 2-5,000 total to the existing guest-count scenario form. Preview, reconfirmation, feasibility and approval use the original engine; simply reviewing it cannot apply a change. Counts outside that planning range leave the button disabled rather than silently clipping attendance. Readiness keeps its existing fourteen checks and states; its limitation wording now acknowledges the separate roster without treating RSVP evidence as a complete readiness certificate.

Guest mutations atomically save the child row plus the existing event revision/history through the original compare-and-swap checks. A small extraction of the existing `WorkspaceRepository._save` SQL allows the same write to participate in a child transaction; public repository/API contracts remain unchanged. Any guest edit therefore conservatively invalidates older scenario previews. Guest create uses a client UUID/payload fingerprint: exact retries return current saved data; changed payload, cross-event request-ID reuse or stale changes are rejected. History records the guest UUID, not removed names/emails/requirements. Missing/foreign records cannot be read or modified.

## Negotiation behavior and AI boundaries

The Vendors workspace has a new private assistant beside the existing vendor editors/Quote Analyzer. It supports lower-price requests, additional services within a quoted total, package discounts, payment terms, hidden-charge clarification, comparison of supplied offers and customized packages. Users select the saved vendor and an existing quoted expense/vendor quote; a unique linked quotation can be resolved automatically. Multiple possible quotes require explicit selection. Unlinked category expense selections are labeled for association review. Missing name/price/comparison evidence returns useful questions before calling the provider.

The context uses the actual event type/date/location, budget/category allowance, selected vendor and quoted amount, recorded scope, protected obligations/dietary/access needs, explicit optional target and custom request. Targets are requests, never assumed negotiated prices. Quote-target differences use Decimal; non-lower targets do not generate savings. Counteroffers are the user's supplied target, not invented market rates. Existing paid/committed amounts remain untouched.

Each analyzed quote now has Use in negotiation. It reuses the selected source and up to two other current analyzed offers, avoiding retyping their prices. The server reparses them with the existing labeled-text parser and rechecks revision, event/vendor/category membership, currencies, totals and duplicate sources. It can also compare up to three distinct owned quoted expenses in the same category. Different-currency supplied offers retain their currency and FX/terms warnings; no conversion, equivalence, price ranking or supplier availability is invented. Raw quote sources remain transient unless recorded through the existing reviewed ledger flow; negotiation does not create an independent document vault.

**One existing Gemini integration is reused.** The provider receives escaped user-role JSON with a fixed separate system instruction and can choose only allowed tactic IDs and cordial/concise tone for the exact revision. Its structured response rejects extra fields, unknown/duplicate actions, stale revisions, malformed/oversized text and protected-context/key echoes. The server composes professional vendor-facing wording and all numeric facts from recorded context. The UI explicitly labels Gemini strategy versus built-in strategy and server-grounded copy. Imported raw quote text, guest PII and vendor contact addresses do not reach the provider. Custom instructions/themes/preferences are data, never privileged instructions. This is constrained AI strategy plus grounded drafting, not unrestricted model-authored prose or a claim to solve prompt injection completely.

Missing credentials, provider errors, timeouts, quota errors and invalid outputs return the same usable deterministic drafting path. Regenerate changes the wording variant while preserving the recorded facts; it does not autosave. The message is editable. Copy uses the browser clipboard on user action, with text-selection fallback if clipboard access is unavailable. There is **no email, WhatsApp, send, booking, payment, acceptance or financial application endpoint**.

Explicit Save reviewed draft only stores one private text draft per event/vendor. It uses an independent draft revision, checks current event revision and keeps the original event/history/expenses/scenarios unchanged. Another tab's newer draft causes 409; refreshing metadata while editing does not silently advance the editor's write version. Reopen is explicit and preserves unsaved text until the user confirms replacement. Drafts survive browser/server restarts and are cascade-deleted with the event.

Saved drafts are **user-reviewed text**, not verified contractual evidence. The saved-event revision is the revision when text was last saved, not proof its statements are accurate. If the event changes, a reopened draft is marked stale. Editing/resaving text remains different from regenerating against current facts. Unrecorded analyzer sources must be reattached to regenerate; source uploads/comparison caches are not stored in the draft. The UI discloses this on reopen. The user must review identity, scope, prices and terms before manually communicating outside Planora.

## Persistence and migrations

The existing `EVENTRA_DB_PATH`, schema-2 workspace JSON, original event/scenario tables and supported v1-to-v2 migration are preserved. The default is still `data/eventra.sqlite3`; use an absolute durable path in deployment. No live database was reset, moved or cleared.

Two optional additive format-1 tables are created transactionally on the **first explicit write**:

- `guests`: primary key guest UUID, event foreign key with ON DELETE CASCADE, derived owner hash, format version and validated guest JSON; indexed by event/owner.
- `negotiation_drafts`: primary key event/vendor UUID pair, event foreign key with ON DELETE CASCADE, derived owner hash, format version, draft revision and validated text/metadata JSON. Vendor membership is checked against the existing owned workspace document; vendors are not duplicated into a new catalog.

Reading an older event before first use returns an empty roster/no saved draft and does not create a table. Existing event documents and API schemas gain no roster/draft fields. Malformed/unsupported stored rows and ownership/identity inconsistencies fail closed; no destructive repair is attempted. Guest edits and event CAS/history share one write transaction; draft save uses one transaction with its own CAS. SQLite's existing foreign-key enforcement removes child state on confirmed event deletion. Restart, rollback, concurrent writers, legacy reads, capacity, invalid data and cascade behavior are tested on temporary databases. Back up before rollout and do not run older writers that lack these feature tables/code against a shared deployment.

No new Python/npm dependency or credential is needed. There is no mandatory authentication change. All new routes use the existing anonymous Owner dependency, origin policy, security/CSP headers, no-store API responses, actual-byte 20,000-byte request cap, explicit proxy trust and bounded process-local rate limiting. Very large Unicode messages or combined quote sources can hit the unchanged byte cap before their character limits; requests fail clearly and UI inputs remain. No silent truncation or limit increase was used.

## APIs added

All prefixes below are under `/api/events/{event_id}` and require the owning browser cookie.

| Method/path | Purpose |
| --- | --- |
| GET `/guests` | Consistent roster, all-roster statistics and optional `q`, `rsvp`, `group` filtering. |
| GET `/guests/{guest_id}` | One owned guest in the requested event. |
| POST `/guests` | Validated create with event revision/client UUID; retry-safe. |
| PUT `/guests/{guest_id}` | Validated full guest edit/manual RSVP update with current event revision. |
| DELETE `/guests/{guest_id}` | Explicit matching guest confirmation and event revision. |
| POST `/vendors/{vendor_id}/negotiation` | Read-only grounded draft/strategy or missing-information response. |
| GET `/vendors/{vendor_id}/negotiation/draft` | Current private saved draft or null, with changed-event label. |
| PUT `/vendors/{vendor_id}/negotiation/draft` | Explicit approved private save with event/draft revision checks. No send/apply. |

API schemas/examples are available in the existing self-hosted `/api/docs`. Existing API contracts are checked unchanged by `scripts.check_structure`.

## Files in this stage

Created backend:
- `app/schemas/guests.py`, `app/repositories/guests.py`, `app/api/guests.py`.
- `app/schemas/negotiation.py`, `app/ai/negotiation.py`, `app/services/negotiation.py`, `app/repositories/negotiations.py`, `app/api/negotiations.py`.

Modified backend: `app/main.py` (router composition), `app/repositories/workspaces.py` (reuse existing CAS write inside child transactions), `app/services/readiness.py` (accurate limitation prose only).

Created frontend: `frontend/modules/guests.js`, `frontend/modules/negotiation.js`, `frontend/styles/people-vendors.css`.

Modified frontend: `frontend/app.js` (mounts/dirty guards), `frontend/modules/state.js` (new private draft dirty flags), `frontend/modules/coordination.js` (roster availability wording), `frontend/modules/signature-intelligence.js` (analyzer handoff buttons), `frontend/style.css` (scoped workspace import), `frontend/index.html` (obsolete workspace-only RSVP paragraph). Existing landing markup/3D assets/controllers/styles are otherwise unchanged.

Created tests: `tests/integration/test_guests.py`, `tests/integration/test_negotiation.py`, `tests/browser/guest_manager_smoke.mjs`, `tests/browser/negotiation_smoke.mjs`.

Modified tests: `tests/browser/planora_product_smoke.mjs` imports/invokes both new checkpoints and replaces one obsolete Not tracked assertion with positive roster/empty-state checks. All unrelated assertions/timeouts/coverage thresholds remain. Created this report; README, the current upgrade audit/plan, the dated bug-audit status note and `docs/BUDGET_RULES.md` are updated. No dependency manifest, Docker, CI or runtime database file was changed for these features.

## Verification commands and results

```powershell
$env:COVERAGE_FILE = '.artifacts/guests-negotiation/baseline.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
$env:COVERAGE_FILE = '.artifacts/guests-negotiation/final.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_guests.py tests/integration/test_workspaces.py tests/integration/test_structure.py
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_guests.py
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_negotiation.py
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_guests.py tests/integration/test_negotiation.py
.venv/Scripts/python.exe -B -m ruff check app tests scripts --no-cache
.venv/Scripts/python.exe -B -m ruff format --check app tests scripts
.venv/Scripts/python.exe -B -m scripts.check_structure
.venv/Scripts/python.exe -B -m pip check
.venv/Scripts/python.exe -B -m scripts.evaluate_planning
.venv/Scripts/python.exe -B -m scripts.evaluate_intelligence
.venv/Scripts/python.exe -B -m scripts.evaluate_readiness
$featureScripts = @(Get-ChildItem frontend -Recurse -Filter *.js) + @(Get-ChildItem tests/browser -Filter *.mjs)
foreach ($featureScript in $featureScripts) { node --check $featureScript.FullName }
node --check vendor/swagger-ui-5.34.0/swagger-ui-bundle.js
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
node tests/browser/test_event_portal_geometry.mjs
node .artifacts/guests-negotiation/guest-driver.mjs .venv/Scripts/python.exe
node .artifacts/guests-negotiation/negotiation-driver.mjs .venv/Scripts/python.exe
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe
node tests/browser/asset_upgrade_smoke.mjs http://127.0.0.1:8000
.venv/Scripts/python.exe -B -m scripts.audit_release
git diff --check
```

The dedicated local drivers compose checked-in assertions with the existing temporary-server/profile/SQLite browser harness. Full regression uses the checked-in original driver. These start real Uvicorn processes at isolated ports and keep user databases untouched. Logs are private in `.artifacts/guests-negotiation/`. No success is inferred from a test file merely existing.

Recorded verification findings: the first guest browser fixture needed an explicit automated confirmation response for its discard action; this was corrected without changing production confirmation behavior or timeouts. The clipboard assertion normalizes Windows CRLF/LF differences while still comparing exact message content. New SQLite test helpers initially used transaction-only context managers, producing ResourceWarnings; they now explicitly close connections, not suppress warnings. The final two warnings are the preexisting Starlette/HTTPX TestClient and google-genai `_UnionGenericAlias` deprecations. A provisional full browser run correctly failed the old assertion that RSVPs were unavailable; it was replaced by positive current-feature checks, not deleted without replacement.

Ruff passed; **113 files already formatted**; syntax passed **45 authored frontend/browser scripts plus the pinned Swagger bundle**. Original exact-cent currency/delta and portal geometry tests passed. All **30 offline evaluation cases** passed; pip check reports no broken requirements. Import/API check reports **68 acyclic application modules and original contracts unchanged**. Final full browser: **26/26 groups passed**, zero runtime exceptions. Python compilation and the local release-candidate private-path/secret-pattern/size check passed. All recorded original landing/3D source/style/asset hashes match the baseline; reversing only the obsolete workspace RSVP paragraph restores the exact original index HTML hash. No landing content was replaced.

## Setup and deployment boundary

Use the existing environment and database; no new credentials/dependency install is required:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers
```

Restart an older running process to load these backend routes, then open a saved event's Guests or Vendors section. Keep the ownership cookie and the same database path to reopen records. Gemini remains optional through the existing server-side `GEMINI_API_KEY`/`GOOGLE_API_KEY`; no key gives complete built-in drafting. Valid live Gemini/model availability was not tested; injected provider success/failures and the existing structured transport tests were run.

Local feature verification does not make the project production/multi-instance ready. It still needs one durable writable SQLite instance/worker, stable TLS/cookie origin, correctly trusted ingress and the existing proxy-server launch policy. Process-local quotas/cache, anonymous-cookie recovery, storage retention/backup and server-calendar-day limitations remain. Docker, hosted CI, live Gemini and Vercel durability/ingress were not verified. Public RSVP/email sending, account login, Event Day Command Center and Event Website Generator remain outside this task.

Additional browser coverage found and repaired a real new-feature cleanup defect: non-workspace views do not emit the section event, so confirmed new-event discard initially left private guest inputs in the hidden form. Both feature modules now observe the existing busy/state lifecycle to clear discarded private state; the regression verifies inputs are cleared and saved records remain unchanged. No lifecycle timeouts/assertions were relaxed.


Final verification limitations: Docker is unavailable (`Get-Command docker -ErrorAction SilentlyContinue` found no executable), so no Docker build/runtime pass is claimed. This application has no npm production build or configured TypeScript/Python static type-check command; JS syntax, Python compilation, real server startup, schema/import checks and full browser rendering were executed. Compilation used `.venv/Scripts/python.exe -m compileall -q app scripts tests` with `PYTHONPYCACHEPREFIX` pointed at ignored `.artifacts/guests-negotiation/pycache`, then removed. The existing already-running development server was not restarted; restart it to load these new backend routes. No deployment, commit or push was performed.

The existing warm-cache/homepage asset regression also exited 0: cached-root upgrade recovery, actual homepage computed styling/sticky transforms and stylesheet-failure fallback passed with no runtime errors or event writes. Its cleanup reported an owned temporary browser profile still locked by Windows; the profile was retained privately, not deleted forcibly or included in Git. `git diff --check` passed with existing CRLF-to-LF normalization notices.
