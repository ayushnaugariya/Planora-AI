# Event Day Command Center — 29 October 2026

## Scope and architecture

This feature adds the saved-event **Event Day** navigation item and `#/event/<UUID>/command` view. It reuses the FastAPI app, owner cookie dependency, SQLite store, workspace revision transaction, existing template task/vendor identities, Gemini transport, security middleware and Event Rescue. It does not change the homepage/3D experience, financial rules, original HTTP contracts or introduce accounts, messaging, a website generator or another financial engine.

The inspected starting tree already contained uncommitted Event Portal, bug-audit, Guest Manager and Negotiation Assistant work. Those changes were retained. Relevant sources reviewed included README, upgrade audit/plan, accounting rules, bug/security audit, guest/negotiation report, workspace schema/repository, coordination, timeline intelligence, Rescue/scenarios, AI adapters, frontend state/routing/helpers and the real-browser harness.

Before this stage, tasks had UUIDs, planning-date milestones, prerequisites, priority and completion; vendors had saved names/contact/booking/checklists. There was no durable event-day time/status overlay, arrival tracking, incident register or operational activity feed. Existing timeline delay analysis is in calendar days and explicitly excludes day-of durations; Rescue already offers isolated financial/date/replacement scenarios with approval. Those systems were preserved rather than replaced.

## Implemented behavior

- Unified timeline/checklist shows every existing milestone and explicitly labeled custom operations. Original planning dates remain visible. The five statuses are Upcoming, In Progress, Completed, Delayed and Blocked. Operators can enter responsible person, saved vendor association, venue area, notes, prerequisites, original start/end and a current expected start/deadline. No default task templates are automatically inserted or duplicated.
- Original start/end are locked after the first explicit save. Later expected-time changes preserve that baseline. Delays require a reason. Actual starts/completions are server timestamps. Prerequisites retired by a plan rebuild stay visible as unavailable and block unfinished dependent work until explicitly reviewed. Read projections do not mutate stored reports. Original task completion writes back to the existing `TaskState.completed`; edits through the old checklist are authoritative on subsequent Command Center reads. Existing completion with no recorded actual timestamp is displayed as unknown, never fabricated.
- Dependencies must belong to the same event, be unique and acyclic. Recorded original prerequisites cannot be removed through this overlay. Starting/completing work requires completed prerequisites. Completed work must be reopened as Upcoming before restarting; reopening clears current actual timestamps while the previous activity remains recorded.
- Vendor coordination shows only saved names, contacts, category and booking information. Expected arrival is unknown until supplied. Expected, Arrived, Delayed and Not Required are supported. Arrival uses the server clock; repeat Arrived updates preserve its timestamp. Correct Arrived to Expected before recording a delay. Related tasks are shown. No email, WhatsApp, calls or other transport is invoked.
- Incidents have category, Low/Medium/High/Critical severity, description, owner, related task/vendor, notes and Open/In Progress/Resolved status. New incidents start Open. Resolved incidents must reopen before progressing. Resolutions have server timestamps.
- Reported/updated open incidents trigger a read-only impact assessment. Manual Analyze impact is also available. Existing prerequisite reachability identifies potentially affected open tasks without inventing durations, slack or downstream clock times.
- **Review in Event Rescue** transfers the incident description and, when linked, its actual vendor into the existing Rescue form. It clears previous replacement costs/confirmations/date alternatives, does not infer cancellation or a zero fee, and does not submit automatically. Operators supply missing assumptions, assess an ordinary persisted Rescue preview, and use the original explicit approval path. Non-vendor incidents use the timeline-risk form and require a real user-supplied alternative date; this is not automatic weather, safety or emergency response.
- The copilot separates saved event context, user-reported incidents and recommendations. Delay hypotheses accept an owned task and 1–1440 minutes and identify possible affected tasks; they cannot calculate a reliable downstream schedule without durations. Gemini can only order all known recommendation IDs against the current revision. The server composes all wording and facts, keeps critical incidents first, rejects unexpected/duplicate/foreign/stale output, and falls back deterministically on missing credentials or provider failures. The question/context are untrusted JSON separate from fixed system instructions. There are no model tools or execution authority.
- Dashboard includes task counts, arrivals, active/critical incidents, current reported work, next saved-time-ordered task, status/responsibility filters, outstanding-vendor filter and persistent activity (latest first; last 50 by default, all available on request). All field text is rendered using DOM text nodes.
- Refresh is manual and every 30 seconds while the Command Center is visible and the document active. This is polling, not WebSocket collaboration or verified live monitoring. Unsaved forms are retained across refresh and errors; revision CAS rejects stale saves. Changing events/discarding an event clears private inputs. Other feature saves respect the new unsaved-form guard.
- Each operational write requires a literal `approved: true`, an explicit UI approval checkbox, a client request UUID and matching workspace revision. This expresses the human Save action, not authentication or proof of real-world correctness. Recommendation analysis never writes or applies anything.

## Readiness and clock rules

`floor(100 × (completed tasks + arrived required vendors + resolved incidents) / (all displayed tasks + required vendors + all incidents))`.

Every check has equal weight; Not Required vendors are excluded. No checks produces unknown, not a fabricated score. Unbooked vendor groups initially remain Expected conservatively; mark them Not Required if appropriate. This metric is an operational checklist ratio, not the separate saved-event readiness analysis, an AI confidence score, a safety certification or proof of supplier availability. Resolving incidents changes the ratio because recorded resolved incidents remain in its denominator.

An optional validated IANA timezone controls the event calendar phase and displayed times. Without one, preserve the existing **server-local calendar day** convention and show that assumption. Preparation is before the saved event date, In Progress is on that date, Completed is after it. The last label is calendar-based and does not claim every task/incident is finished. All original date-only milestones remain date-only; no event start/duration is inferred.

Time editors explicitly use the browser's timezone; their labels disclose it. They store aware timestamps and reject nonexistent local DST times. Existing exact timestamps are retained on unrelated edits rather than rounded to displayed minutes. Choosing a new ambiguous fall-back clock time uses the browser's first-offset interpretation; use an explicit offset through the API when the second occurrence is intended. Event timezone changes alter display/phase, never saved instants or the original budget/schedule.

`tzdata>=2025.2` is the only new dependency, justified because Windows Python in this environment had no IANA database. Installed validation version: **2026.6**, pinned in the existing CI snapshot. Standard-library `zoneinfo` performs conversions. No custom timezone arithmetic was introduced.

## Storage and endpoints

One additive lazy-initialized `event_day` table: primary-key `event_id`, event foreign key `ON DELETE CASCADE`, owner hash, format version 1 and a validated JSON document. The primary key indexes the event lookup; every read/write also checks the owner and parent event. The original workspace document and SQLite `user_version=2` remain unchanged. An old database's first read does not create this optional table. The first approved write creates it in the same transaction.

`BEGIN IMMEDIATE` covers parent ownership/revision recheck, task completion, operational document, activity, idempotency receipt and existing workspace CAS/history update. Any error rolls back everything, including initial DDL. Every new operation advances the workspace revision and conservatively invalidates previous AI/scenario previews. Exact retries return current state without duplicating an operation or log; changing a reused request's payload conflicts. Reads use a transaction for a consistent parent/child snapshot.

Capacity is explicit: at most **200 total visible tasks**, 100 incidents, 100 vendor overlays, 1000 operational activities/receipts per event, and at most 20 prerequisites per edited task. At activity capacity new operations are rejected with 422 and history retained; exact retries still work. There is no archival/retention/export UI for event-day records yet. Notes and API bodies remain bounded by schemas and the existing actual-byte 20,000-byte request limit. Invalid/unsupported persisted documents fail closed; no reset/repair is automatic.

All paths start `/api/events/{event_id}/command-center`:

| Method / suffix | Behavior |
| --- | --- |
| GET (base) | Consistent dashboard, derived facts and activity |
| POST `/operations` | Approved discriminated `task`, `vendor`, `incident` or `settings` operation, transactional saved workspace + dashboard |
| POST `/copilot` | Revision-checked, read-only advice and optional delay hypothesis |
| GET `/incidents/{incident_id}/analysis` | Owned incident impact; built-in grounded advice, no mutation |

Existing `/api/events/{event_id}/rescue` and scenario preview/apply/discard routes remain the only financial/date recovery path. No new approval bypass, communication endpoint or account was added.

## Files in this stage

Created backend: `app/schemas/command_center.py`, `app/services/command_center.py`, `app/services/event_day_copilot.py`, `app/repositories/command_center.py`, `app/ai/command_center.py`, `app/api/command_center.py`.

Created frontend: `frontend/modules/command-center.js`, `frontend/styles/command-center.css`.

Created tests/report: `tests/integration/test_command_center.py`, `tests/browser/command_center_smoke.mjs`, this document.

Modified composition/UI: `app/main.py` (router only), `frontend/app.js` (mount/dirty guard), `frontend/modules/state.js`, `frontend/modules/shell.js` (view metadata), `frontend/index.html` (workspace tab/panel only), `frontend/style.css` (scoped import), `tests/browser/planora_product_smoke.mjs` (retain all earlier checks and add Command Center).

Modified dependency/docs: `pyproject.toml`, `requirements.txt`, `requirements-ci.txt`, `README.md`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md`, `docs/BUG_SECURITY_AUDIT.md`, `docs/BUDGET_RULES.md`.

No changes to existing financial/scenario/Rescue calculations, security middleware, existing tables, database location, landing/3D files, deployment configuration or old tests' assertions/timeouts were needed. The preexisting dirty tree includes additional unrelated files from earlier stages; this list describes only this stage's edits.

## Validation evidence

Private logs, coverage and screenshots are under ignored `.artifacts/command-center/`. Browser tests use temporary SQLite databases/profiles and actual Uvicorn/Edge processes, preserving user records. Final verification: **817 passed, 2 existing warnings in 88.28 seconds; 98.56% combined statement/branch coverage**, with the unchanged 90% floor. The original 775 tests remain; 42 new cases were added. Full browser: **27/27 checkpoint groups passed**, zero runtime exceptions. Ruff passed, **120 files already formatted**; **47 authored JS/browser scripts** plus pinned Swagger syntax passed. Exact-cent/delta/geometry checks passed; **30/30 offline evaluation cases** passed. Import/contract check passed for **74 acyclic modules** with original contracts retained; pip dependency check, Python compilation and local release-candidate checks passed. All **16 recorded landing/3D source/style/artwork hashes** match the prior preserved snapshot. Desktop/mobile screenshots are saved privately alongside the logs.

Initial existing suite: **775 passed, 2 warnings, 86.82 seconds**. The automatically discovered source coverage was **95.71%**, including the new schema file created while this asynchronous baseline was running (116 unexecuted lines); therefore that percentage is not a clean original-source comparison. The preceding saved report's 98.72% is historical, not substituted for this measurement.

Final compatibility review additionally identified the removed-prerequisite edge case: custom work must not silently become unblocked when rebuilding an event retires a planning task. A dedicated regression now verifies the blocked projection, read immutability, unrelated updates and explicit prerequisite review.

Focused feature suite: **42 passed, 1 existing warning, 3.94 seconds**. Dedicated real-browser regression exited 0 with original request/debugging timeouts, including task approval, delays, actual arrival, incident resolution, actual Rescue preview, no advice mutation, blocked-network retention, widths 320–1440, exact budgets, browser/server restart and private draft discard. The first browser attempt timed out initializing CDP before loading the page under the sandbox; the unrestricted local-browser run exercised the application. The first dedicated driver's simplistic click helper missed the final mobile navigation action; replacing that private fixture helper with the existing geometry-aware helper fixed the fixture, without changing product code or weakening assertions.

Initial new Python failures also identified missing Windows timezone data and two fixture mistakes (duplicate approval argument and raw lone-surrogate encoding by HTTPX before sending). `tzdata` and correctly encoded test requests repaired them. A new stale-preview regression initially supplied an unsupported scenario request field; the test was corrected to the actual unchanged schema. These were investigated, not hidden or suppressed.

Executed commands:

```powershell
$env:COVERAGE_FILE='.artifacts/command-center/baseline.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -m pip install --disable-pip-version-check 'tzdata>=2025.2'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider tests/integration/test_command_center.py
$env:COVERAGE_FILE='.artifacts/command-center/final.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -B -m ruff check app tests scripts --no-cache
.venv/Scripts/python.exe -B -m ruff format --check app tests scripts
.venv/Scripts/python.exe -B -m scripts.check_structure
.venv/Scripts/python.exe -B -m pip check
.venv/Scripts/python.exe -B -m scripts.evaluate_planning
.venv/Scripts/python.exe -B -m scripts.evaluate_intelligence
.venv/Scripts/python.exe -B -m scripts.evaluate_readiness
$dayScripts=@(Get-ChildItem frontend -Recurse -Filter *.js)+@(Get-ChildItem tests/browser -Filter *.mjs)
foreach($dayScript in $dayScripts){node --check $dayScript.FullName}
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
node tests/browser/test_event_portal_geometry.mjs
node .artifacts/command-center/browser-driver.mjs .venv/Scripts/python.exe
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe
.venv/Scripts/python.exe -B -m scripts.audit_release
# Compilation used an ignored private output location.
$env:PYTHONPYCACHEPREFIX=(Join-Path (Get-Location) '.artifacts/command-center/pycache')
.venv/Scripts/python.exe -m compileall -q app scripts tests
Remove-Item Env:PYTHONPYCACHEPREFIX
node --check vendor/swagger-ui-5.34.0/swagger-ui-bundle.js
git diff --check
```

## Local use and deployment boundary

Install existing runtime requirements once for the new timezone database, then restart an older server:

```powershell
cd D:\Projects\eventra
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --no-proxy-headers
```

Open `http://127.0.0.1:8000`, reopen/create an event, then choose **Event Day**. Keep the owner cookie and existing `EVENTRA_DB_PATH` (default `data/eventra.sqlite3`). No live database is reset or moved. No additional secrets are required; Gemini remains optional through the existing server-side credential environment variables. Backup/restore and cookie recovery remain deployment responsibilities.

This is a single durable SQLite instance/worker feature. Process-local quotas/cache, anonymous-session recovery and retention limitations remain. Do not infer distributed coordination, persistent Vercel/serverless storage, emergency monitoring, vendor verification, formal accessibility/performance certification or production readiness. Live Gemini success/real quota failures, Docker runtime/build, hosted CI and production deployment are unverified. Local tests inject provider outcomes. Existing Starlette/HTTPX and google-genai deprecation warnings remain.
