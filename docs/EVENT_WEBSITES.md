# Event Website & Invitation Generator

30 October 2026, Asia/Calcutta. Implemented in the existing FastAPI/SQLite/vanilla-module application. Existing uncommitted Event Portal, security, Guest Manager, Negotiation and Command Center work was preserved. No account system, new provider, frontend dependency, database replacement or landing/3D redesign was introduced.

## Current implementation

Saved-event navigation now includes **Event Website**, at `#/event/<event UUID>/website`. The owner can use the existing event, choose a theme, edit public details, save a private draft, preview the actual shared renderer, review the visibility summary, explicitly approve and publish. Draft edits do not update the live snapshot. Updates require another preview/approval. Unpublish immediately makes the public HTML/data/RSVP endpoints unavailable; republish retains the stable link.

Four deterministic themes are implemented: **Ethereal**, **Modern Minimal**, **Celebration**, and **Editorial Luxe**. They have distinct type/layout/background treatments and support title/subtitle, invitation/welcome/introduction, date, an optional aware start time/countdown, selected schedule, host names, venue, dress code, RSVP and bundled cover/gallery artwork. Accent input is a validated six-digit hex color; button foreground is chosen for contrast. No AI-generated HTML, CSS, JavaScript or executable template is accepted.

The editor and public page use the **same renderer**, not a visual approximation. Preview RSVP controls are disabled. The public page includes loading/error/retry and native print controls; print CSS hides form/actions. A shareable website URL and print layout are available. **PDF/image file generation and user-photo uploads are not implemented.** The existing app has no safe upload/storage pipeline; illustrations use only three allowlisted local assets, with no remote URLs, raw SVG, data URLs, filesystem paths or arbitrary uploads accepted.

## Reuse and safe defaults

- Event name, type, date and city come from the owned existing event. A saved Design Studio palette supplies the default accent when available. The event type selects a suitable initial theme.
- The configured Command Center timezone is reused; otherwise the public editor explicitly uses **UTC**. A recorded start on the existing event-category milestone is reused only when it matches the event date in that timezone. Ordinary setup/arrival times do not become an invented event start.
- Existing event-category milestone titles/dates seed the draft schedule. The owner can explicitly select saved timed operations or add/edit/remove public entries. Private task UUIDs, owners, notes, incidents and vendor records are not imported into public schedule items. Public times are user-entered, not inferred durations or external availability.
- Venue preferences are not treated as a confirmed venue address. Missing names/addresses/host names/dress code remain editable and empty. City is reused but venue visibility starts off.
- Hosts, venue, schedule, dress code, gallery and public RSVP are **off by default**. Cover defaults to typography only. Title, date, invitation and optional introduction are part of the explicitly reviewed public page. Public party size defaults to one; the host may allow 1–21 people including the respondent, matching the existing maximum 20 plus-ones.
- Time editors disclose that inputs use the browser timezone. Stored aware timestamps display in the configured event timezone. Nonexistent DST times are rejected; unchanged timestamps retain their exact value rather than being rounded on unrelated edits. As with the Command Center, a newly entered ambiguous fall-back time uses the browser's first-offset interpretation; use an explicit API offset for the second occurrence.
- Date-only invitations do not invent a midnight start/countdown. Countdown runs only when a real start time exists. Public pages need JavaScript, consistent with the existing frontend; a noscript explanation is supplied.

## Public/private boundary and approval

`WebsiteConfig` is an owner-only draft. `PublicWebsite` is a separate explicit allowlist; it does not inherit or serialize `EventWorkspace`, guest records or operational state. Hidden host/venue/dress fields become null, hidden schedule/gallery become empty lists, and disabled RSVP instructions are removed from the network projection. Budgets, expenses, quote prices, guest/contact lists, internal event/task/vendor IDs, incidents, planning notes, prompt strings and owner hashes/cookies never enter that projection automatically.

Owners may type their own text into public fields. Anything deliberately entered there can become public after approval; no automatic DLP or guarantee against an owner publishing their own sensitive text is claimed. The preview/disclosure is the review boundary. Private workspace fields are never copied wholesale, and there is no free-form AI prompt accepting private context.

Publication requires the original owner cookie, matching website/event revisions, literal `approved: true`, and a SHA-256 hash of the current public preview. The hash binds the reviewed public content; it is not an authentication credential. A changed/unsaved preview cannot publish a different stored draft. Frontend publication remains disabled until the current draft is saved, previewed and explicitly checked. A stale event or website revision conflicts. The server applies the same checks independently of UI state.

Unpublish requires owner, website revision and explicit approval, but deliberately does **not** depend on an unrelated newer event revision: an incoming RSVP must not prevent privacy revocation. It is also allowed while other private editor inputs are unsaved. Other ordinary save/preview/publish actions retain the existing unsaved-workspace guard. Unpublishing does not discard private drafts or those other inputs.

Public slugs are 24 cryptographically random bytes (`secrets.token_urlsafe(24)`, 32 URL characters), separate from database UUIDs. The relative route is `/e/<slug>`; the management UI combines it with the current browser origin. No arbitrary Host/forwarding header is used to construct an absolute server URL. The host still must configure its canonical public TLS origin/verified proxy correctly.

These are publicly accessible **unlisted links**, not password-protected websites. Anyone with the link can read the approved information. `noindex,noarchive` is an indexing preference, not access control. All `/api/` and `/e/` responses, including 404/429, use `no-store`; original CSP/security headers remain unchanged. `/e/` is also covered by the existing bounded IP quota. API requests retain the actual-chunk 20,000-byte cap. Existing proxy trust and process-local rate-limit bounds are unchanged.

The HTML route checks publication before serving the public shell; unpublished/invalid links return a fixed friendly 404 with no event data. Public data and RSVP routes recheck the current snapshot. The public script checks for updates every 15 seconds while visible, and on returning to the tab. An unpublished page clears its rendered content and disables printing when that check returns 404. Backend revocation is immediate; previously downloaded/printed/copied information cannot be recalled. Snapshot updates replace old displayed details and reset the response form, requiring review of the changed invitation.

## Public RSVP and the existing Guest Manager

There is one guest system. An accepted new public response creates a normal `Guest` row through a controlled create-only helper in the existing guest repository. Fields use the existing RSVP states, party/plus-one arithmetic, optional dietary requirements and private notes. Group is Other; notes and a roster badge identify **Public RSVP · unverified**. The owner reviews it through the existing Guest Manager.

The public API accepts only request UUID, current publication edition, name, email, RSVP, party size, dietary requirements and message. It accepts no event/guest ID, group/privilege, budget, revision, payment, owner or update operation. No internal child ID is returned. Email may be host-required or optional; syntax is checked, not identity or deliverability.

The generic acknowledgement is the same for new and matching prior entries. Matching email (case-insensitive), or matching name when email is absent, leaves the prior guest unchanged. Knowing a private guest's email cannot claim or edit that party. A response UUID/fingerprint prevents exact retry duplication and rejects changed reuse; duplicate identity requests are acknowledged without overwriting. Deleted guest rows leave idempotency tombstones so a replay cannot recreate them. Name/email matching is best-effort deduplication, not verified identity; aliases/shared names and intentional abuse still require host review. Public visitors must contact the host to change a response.

The publication edition changes on every publish. A stale form or another event's edition is rejected. Unpublished or disabled RSVP is rejected. The existing 500-primary-guest capacity and 0–20 plus-one bound remain. At most 1000 unique response receipts per event are retained; saturation returns 429 and preserves records. There is no silent disablement of validation. Existing IP rate limiting and same-origin mutation checks apply; no distributed quota, CAPTCHA, email verification, public invitation delivery or anti-spam certification is claimed. An open public RSVP link can attract unwanted registrations up to these limits; unpublish or disable RSVP and review the roster.

`BEGIN IMMEDIATE` covers current publication/edition/capacity/dedup checks, guest insert, event revision/history, CAS and receipt. Any failure rolls back all of them. New RSVP changes the guest roster and conservatively stales older event/scenario previews, but **does not change planned headcount, budget, expenses, vendors, tasks or money calculations**. There is no public write path to private event details or a scenario apply operation.

## Optional Gemini content

Website creation, rendering, preview, saving and publishing never call or require Gemini. **Suggest invitation copy** is separate and adds editable unsaved text; it never saves or publishes.

The existing Gemini transport/roles/timeout/output bounds are reused. Only event-type, theme and tone enums plus a server schema reach the model. No title, date, venue, guest information, internal notes, arbitrary prompt or private operational context is sent. Gemini selects validated opening/closing IDs; the server composes wording using the edited public title and date. This is bounded AI selection with grounded server composition, not unrestricted model-authored prose. It cannot invent a venue, schedule, supplier, price, approval or executable code.

Missing credentials, quota/permission failures, timeouts, empty/malformed/non-object outputs, unknown fields/values and code-like outputs use built-in wording. Logs contain the exception class only. Successful enum recipes use the existing bounded TTL cache (64 entries, five minutes) to avoid repeat calls. Copy may be generated for unsaved drafts, but every output still needs review/save/preview/approval. Tests inject provider outcomes; valid live Gemini/model/quota behavior was not exercised.

## Storage and API inventory

Two additive lazy tables; no database reset, move, existing-table replacement, workspace schema change or `user_version` bump:

| Table | Purpose / relationships |
| --- | --- |
| `event_websites` | Event PK/FK (`ON DELETE CASCADE`), owner hash, independent website revision, unique indexed slug, format 1 and validated document containing separate draft/published snapshots and last-operation receipt. |
| `website_responses` | Event FK to website (cascade), hashed request/identity keys, payload fingerprint and private guest FK (`ON DELETE SET NULL`); composite primary key and unique event/identity index. Stores deduplication metadata, not a second guest list. |

Old databases read without creating these tables. First private draft save creates the website table inside its transaction; first accepted response creates the receipt table with guest/event changes. Website changes have independent CAS and do not revise the financial workspace. Exact immediate retries return current state; an older operation replay after another edit conflicts rather than undoing or republishing. Malformed/unsupported/identity-mismatched stored documents fail closed. The live database was not changed by tests.

Private endpoints, all owner-scoped:

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/events/{event_id}/website` | Saved/default private config, status/link and optional schedule suggestions |
| PUT | same | Save a private versioned draft |
| POST | same + `/preview` | Validate/project current editor config; return public preview/hash, no save |
| POST | same + `/publish` | Explicitly approve the reviewed saved snapshot |
| POST | same + `/unpublish` | Explicitly revoke public access; retain slug/draft |
| POST | same + `/content` | Optional bounded copy selection/fallback, no writes |

Public endpoints have no ownership-cookie dependency:

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/e/{slug}` | Published page shell or fixed friendly 404 |
| GET | `/api/public/websites/{slug}` | Only the approved `PublicWebsite` projection |
| POST | same + `/rsvp` | Controlled create-only roster response; generic 202 acknowledgement |

## Files changed in this stage

Created backend: `app/schemas/websites.py`, `app/services/websites.py`, `app/repositories/websites.py`, `app/ai/website_copy.py`, `app/api/websites.py`.

Modified backend: `app/main.py` (router composition); `app/api/dependencies.py` (extract the unchanged origin check for safe reuse); `app/core/security.py` (extend no-store/quota to the new public HTML path); `app/repositories/guests.py` (controlled insertion into the original roster and workspace transaction).

Created frontend: `frontend/modules/event-site-renderer.js`, `frontend/modules/website-editor.js`, `frontend/invitation.html`, `frontend/invitation-unavailable.html`, `frontend/invitation.js`, `frontend/styles/event-site.css`, `frontend/styles/website-editor.css`.

Modified frontend: `frontend/index.html` (workspace tab/panel only); `frontend/app.js` (module mount and appended dirty guard); `frontend/modules/state.js`; `frontend/modules/shell.js` (view metadata); `frontend/modules/guests.js` (unverified public-response badge); `frontend/style.css` (scoped imports).

Created tests/report: `tests/integration/test_websites.py`, `tests/browser/website_smoke.mjs`, this report. Modified `tests/browser/planora_product_smoke.mjs` to append the new checkpoint without removing/changing existing assertions. Documentation updates: README, upgrade audit/plan, bug/security audit, budget rules and deployment requirements.

No dependencies or environment variables were added. Existing dirty files from earlier stages remain; this inventory describes this stage only.

## Verification

Clean starting baseline: **817 passed, 2 existing warnings, 42.65 seconds; 98.56% combined coverage**. Original tests and the 90% coverage threshold remain unchanged. **Final verification: 889 passed, 2 unchanged warnings in 136.26 seconds; 98.31% combined statement/branch coverage. All 817 original cases remain; 72 new cases were added.** The coverage denominator increased with the new feature; the 90% gate was not reduced. **Full browser: 28/28 checkpoint groups passed, exit 0, zero runtime exceptions.** Ruff passed; 126 Python files already formatted; 51 authored JS/browser scripts plus the pinned Swagger bundle passed syntax. Original exact-cent/delta/geometry checks, 30/30 offline evaluation cases, 79-module acyclic/original-HTTP-contract check, pip consistency, Python compilation and the local release-candidate check passed. All 16 recorded landing/3D source/style/artwork hashes match; removing only the workspace tab/panel restores the exact original index HTML hash. Private logs, source hashes and desktop/mobile screenshots are under ignored `.artifacts/event-websites/`.

Focused feature suite: **72 passed, 1 existing warning, 29.17 seconds**. Cases include four-theme lifecycle, visibility/network allowlist, preview/approval/revision binding, stable URL and republish, every private operation's ownership, anonymous cookie behavior, malformed IDs/records, event/guest isolation, capacity/concurrency/rollback/retry, party validation, original budget preservation, guest-delete tombstones, cascade deletion, existing event start reuse, same-origin/body/rate headers, injected provider success/quota/permission/timeout/malformed/code output and fallback/cache behavior.

The dedicated real browser exited 0 with four shared-renderer theme previews under unchanged CSP, blocked remote HTTPS, explicit publication, private edits versus live snapshots, anonymous public RSVP into Guest Manager, exact budget isolation, print CSS, 320/390/768/1440 widths, failed-input retention, unpublish/republish, cookie ownership and browser/server restart. Full regression also includes an already-open public page clearing after revocation.

Initial focused failures identified missing no-store on new `/e/` error responses; the existing policy/quota was extended to that path. Other provisional cases ran before the new public HTML file existed during UI construction. They were rerun after implementation. The first dedicated browser fixture restored the owner cookie without its expiry, making it session-only and losing ownership at browser close. The fixture now restores its original persistent expiry; application cookie policy and restart assertions were not weakened. No existing test was deleted or relaxed.

Executed commands (PowerShell, from the repository root):

```powershell
$env:COVERAGE_FILE='.artifacts/event-websites/baseline.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_websites.py
$env:COVERAGE_FILE='.artifacts/event-websites/final.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -B -m ruff check app tests scripts --no-cache
.venv/Scripts/python.exe -B -m ruff format --check app tests scripts
.venv/Scripts/python.exe -B -m scripts.check_structure
.venv/Scripts/python.exe -B -m pip check
$websiteScripts=@(Get-ChildItem frontend -Recurse -Filter *.js)+@(Get-ChildItem tests/browser -Filter *.mjs)
foreach($websiteScript in $websiteScripts){node --check $websiteScript.FullName}
node --check vendor/swagger-ui-5.34.0/swagger-ui-bundle.js
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
node tests/browser/test_event_portal_geometry.mjs
.venv/Scripts/python.exe -B -m scripts.evaluate_planning
.venv/Scripts/python.exe -B -m scripts.evaluate_intelligence
.venv/Scripts/python.exe -B -m scripts.evaluate_readiness
node .artifacts/event-websites/browser-driver.mjs .venv/Scripts/python.exe
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe
.venv/Scripts/python.exe -B -m scripts.audit_release
$env:PYTHONPYCACHEPREFIX=(Join-Path (Get-Location) '.artifacts/event-websites/pycache')
.venv/Scripts/python.exe -m compileall -q app scripts tests
Remove-Item Env:PYTHONPYCACHEPREFIX
git diff --check
```

The ignored dedicated driver composes the existing checked-in Uvicorn/Edge harness and geometry-aware pointer helpers with the new checked-in assertions. It does not change debugging timeouts. Both drivers use isolated temporary databases/profiles. The complete driver retains existing guest/negotiation/Command Center/budget/scenario/Rescue/security/docs/landing checks.

## Setup and remaining deployment limits

Restart an older running server to load the routes; no package or new key is required for this stage:

```powershell
cd D:\Projects\eventra
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --no-proxy-headers
```

Open `http://127.0.0.1:8000`, open/create a saved event, then **Event Website**. Save, preview, check publication approval and publish. Keep the existing owner cookie and `EVENTRA_DB_PATH` (default `<project>/data/eventra.sqlite3`). Localhost links work only where that local server is reachable; a publicly reachable TLS deployment is required to share externally. No server was deployed, committed or pushed by this task.

Storage still requires a single durable writable SQLite instance/worker and stable ownership cookie. Proxy ingress/canonical hostname/TLS must be verified by the deployer. Quotas/cache are process-local; no distributed abuse protection, backup/retention certification, account recovery, email/invitation transport, verified RSVP identity, custom image storage or publishing-domain management was added. There is no production/serverless persistence certification. Existing Cloud Run fail-closed storage behavior remains. Vercel durability/ingress, hosted CI, live Gemini, Docker runtime/build, formal accessibility and production performance remain unverified. Two preexisting Starlette/HTTPX and google-genai deprecation warnings remain. No prompt-injection-completely-solved claim is made.
