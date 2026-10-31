# Planora AI implementation plan


## Final integration/security audit - 30 October 2026

No new product feature or authentication work. [FINAL_AUDIT.md](FINAL_AUDIT.md) records inspection, four reproduced repairs, exact file changes, test evidence and production prerequisites. Repaired legacy checklist/event-day completion interoperability, public fetch timeout/retry, retained-overlay capacity handling, and workspace row/document identity/revision consistency. Original API contracts, actual-byte limits, ownership, approvals, budget calculations, SQLite path/schema and user changes remain intact. The full index HTML and 16 landing/3D files are byte-identical to the starting tree.

Fresh baseline **889 / 98.31%**; final **896 passed / 98.31%**, two unchanged warnings, original 90% floor. Seven new Python regressions and two new browser groups; **30/30 complete browser checkpoints passed**, zero runtime exceptions. Ruff/format (127 files), 52 authored JS checks plus vendor syntax, 79-module original-contract/import check, exact-cent/geometry, 30 offline evaluations, compilation, pip consistency and candidate release checks passed. The real database was read only: schema 2, quick_check OK, zero FK violations, 3/3 workspaces valid.

Ready for a supervised local/offline demo after restart. Restricted public demo requires verified durable single-instance TLS hosting and abuse/backup/cost controls; production readiness is not established. Docker/advisory tooling, hosted CI, live Gemini, target ingress/storage replacement, recovery/retention and load/security certification remain unverified. Anonymous-cookie recovery/authentication stays a separate later milestone. No automatic publish, communication, commit, push or deployment was performed.


## Event Website and Invitation Generator - 30 October 2026

Implemented and locally verified end to end: four deterministic themes (Ethereal, Modern Minimal, Celebration, Editorial Luxe), existing event/date/start/timezone/palette reuse, explicit public schedule selection, editable invitation copy, visibility controls, local cover/gallery artwork, shared actual preview renderer, literal approval and preview-hash-bound publication. Draft changes stay private; updates require another approval. Stable cryptographically random `/e/<slug>` links support unpublish/republish, with dedicated allowlisted public schemas and no private record serialization.

Public RSVP is a controlled create-only entry into the existing Guest Manager, not another guest database. Inputs, edition, party limits, ownership boundaries, cross-origin writes, retries, duplicate identities and capacity are checked transactionally; no prior guest is publicly claimable/overwritable. Notes/badges identify unverified public responses. Guest revision/history and receipt commit together, with no automatic budget/headcount change. Revocation is independent of newer RSVP event revisions. Two lazy additive tables preserve the database path, existing schema/user_version 2 and data. No dependencies or environment variables were added.

Gemini optionally selects validated copy variants from enum-only context; the server inserts reviewed title/date. Missing credentials, provider quota/permission/timeout/malformed/code-like output use built-in text. Creation/publication is independent of AI. No executable AI templates, raw private-context prompting, arbitrary image URLs or new provider.

Fresh baseline **817 passed / 98.56%**, two existing warnings. Final **889 passed / 98.31%**, two unchanged warnings, **72 new cases**, original 90% floor retained. Full real-browser **28/28 checkpoint groups**, zero runtime exceptions: original workflows plus four-theme/CSP preview, anonymous public RSVP into Guest Manager, open-page revocation, budgets/privacy, widths 320?1440, print CSS, failure retention and browser/server restart. Ruff/format (126 files), 51 authored JS checks plus vendor syntax, 79-module original-contract/import check, exact-cent/geometry, 30 offline evaluation cases, compilation, pip consistency and release-candidate checks passed. All 16 landing/3D source/artwork/style hashes remain unchanged; removing only the workspace tab/panel restores the exact baseline index HTML hash.

Exact nine endpoints, file inventory, schema/publication rules, commands, actual results, setup and limitations: [EVENT_WEBSITES.md](EVENT_WEBSITES.md). This section supersedes older dated missing-website/public-RSVP findings below. Existing uncommitted work was retained; no account system, homepage redesign, deployment, commit or push was introduced.

Remaining scope: no custom photo uploads/storage, PDF/image-file export, invitation delivery, verified RSVP identity/update portal, distributed abuse protection or cookie/account recovery. Open RSVP can receive unwanted registrations within the existing quotas/caps; host review is required. Public snapshots need JavaScript; already downloaded copies cannot be recalled. SQLite remains one durable instance/worker; TLS/canonical host/proxy ingress, live Gemini, Docker, hosted CI and production/serverless deployment are unverified.


## Event Day Command Center ? 29 October 2026

Implemented locally as an additive owned operational overlay linked to existing task/vendor UUIDs. Includes five task statuses, user-entered owners/locations/aware times, locked original start/end versus expected times, completion synchronization with the existing checklist, validated prerequisites, custom operations, four vendor-arrival states, persistent incidents/activity, transparent readiness, optional IANA timezone and 30-second visible-view polling. No planned deadline, budget or ledger mutation is introduced.

One optional format-1 `event_day` table is created inside the first approved write. Workspace JSON/SQLite user_version 2 and the database path stay intact. Existing ownership, request/security headers, proxy/limiter, CAS, migration and scenario approval protections remain. Approval checkbox + literal approval, revision CAS, transaction and request receipts prevent silent/stale/duplicate updates. Every real operation conservatively invalidates older previews. Boundaries: 200 tasks, 100 incidents, 1000 retained operations; saturation rejects new writes rather than erasing history.

Incident assessment and copilot are read-only. Gemini can only order known IDs; fixed server facts/wording, schema/revision checks, priority enforcement and deterministic fallback remain in control. The explicit Rescue handoff transfers actual context, clears old cost/date assumptions and requires ordinary assessment/review/approval. No invented suppliers, prices, schedule durations, automatic contact or AI execution. `tzdata` is the sole new dependency for missing Windows IANA data.

Acceptance verified: focused 42-case lifecycle/ownership/security/concurrency/rollback/corruption/timezone/AI suite; real task/arrival/incident/Rescue browser workflow including approval, failure retention, 320?1440 widths and browser/server restart. Full-suite outcomes and exact files/commands are recorded in [EVENT_DAY_COMMAND_CENTER.md](EVENT_DAY_COMMAND_CENTER.md). That report supersedes earlier dated missing-feature statements below. Existing dirty user changes and all 16 recorded landing/3D source/style/artwork hashes were preserved. No account system, website generator, deployment or new financial engine was introduced.

Final measured Python: **817 passed, 2 existing warnings, 88.28s; 98.56% coverage**, unchanged 90% floor. Full real-browser **27/27 checkpoints passed**, zero runtime exceptions. Ruff and format (120 files), 47 authored JS checks plus vendor syntax, 74-module original-contract/import check, exact-cent/geometry, 30 offline evaluation cases, pip consistency, compilation and release-candidate checks passed. Original 775 cases retained, 42 new cases. The removed-prerequisite rebuild edge case is regression-tested: unfinished dependent work stays blocked until explicitly reviewed.

Remaining limits: single durable SQLite instance/worker; local quota/cache, no cookie recovery, no activity archive past the explicit capacity; user-reported operations rather than external live monitoring. Phase is calendar-based, times are entered in the explicitly disclosed browser timezone, and no downstream minute schedule is fabricated without durations. Live Gemini, Docker, hosted CI, formal accessibility/performance and production deployment are unverified.

Updated 29 October 2026. Based on [UPGRADE_AUDIT.md](UPGRADE_AUDIT.md). Completed stages have execution evidence below; future roadmap items remain proposals, not authorization to implement them.

## Current Guest List/RSVP and Vendor Negotiation implementation - 29 October 2026

Guest CRUD, groups/search/filters, manual party RSVP/plus-one statistics, requirements and confirmed removal are implemented in the existing workspace. Owned guest rows and event revision/history commit atomically; explicit confirmed-count review reuses the existing scenario/approval path. No automatic budget/headcount update. Negotiation reuses actual saved quote/event context and current Quote Analyzer sources, covers seven request types, uses constrained Gemini tactics/tone with grounded server composition or offline fallback, and supports editable/copyable, explicitly saved/versioned private drafts. It never sends communications or writes ledger amounts.

Two optional format-1 child tables, created transactionally on first write, preserve the existing SQLite path, schema-2 workspace JSON, supported legacy migration and original API contracts. No login, day-of command center, public website/RSVP or homepage/3D redesign. Existing uncommitted work is preserved. Fresh baseline **708 / 98.84%**; final Python **775 passed / 98.72%**, two existing warnings; **67 new cases**. Final full browser **26/26 groups**, zero runtime exceptions; Ruff/format, 45 authored JS scripts plus vendor syntax, exact-cent/geometry checks, 30 offline evaluations, compilation and release-candidate checks passed. Phase order, exact files/commands, counting rules, rollback/CAS, deployment limits and manual setup: [GUESTS_NEGOTIATION.md](GUESTS_NEGOTIATION.md). Live Gemini/Docker/hosted verification remain unclaimed; durable single-instance SQLite is still required.

## Current bug hunt and security repairs - 28 October 2026

Five reproduced defects repaired: unexpected-500 security/no-store headers; lone-CR calendar escaping; cross-event/calendar reexport UID identity; mobile public Escape/closed-sidebar focus; and historical R12 API-docs CSP breakage. Swagger now uses pinned, licensed local assets and external bootstrap under the unchanged strict CSP, with no external schema validator. No financial rule, database migration, authentication requirement or product feature was added. Existing uncommitted Event Portal work is retained.

Fresh baseline **684 / 98.78%**; final Python **708 passed / 98.84%**, two existing warnings, 24 added cases. Final full browser **24/24 groups**, zero runtime exceptions; Ruff/format, JS/vendor syntax, exact-cent, offline evaluations, original contracts, startup/compilation and release-candidate checks passed. Remaining limitations, exact commands, file inventory, data/security inspection and honest workflow capability matrix: [BUG_SECURITY_AUDIT.md](BUG_SECURITY_AUDIT.md). Guest/RSVP rosters, negotiation messaging, event-day command center and public website publishing remain unsupported; no placeholder implementations. SQLite remains durable single-instance only; live Gemini/hosted/Docker verification is not claimed.

## Current Event Portal - 28 October 2026

Implemented as an additive landing chapter between workflow and the original studio preview. Native WebGL2/GLSL geometry, analytic metallic/glass shading, scroll camera passage and ordered architectural assembly; pointer lighting, native chapter/pause/creation controls. Existing flower/invitation and product architecture remain unchanged. No dependency, backend, financial, persistence, security or API contract changes.

Verified: baseline/final Python **684 passed / 98.78%**, two existing warnings; full browser **22 groups passed**, no runtime exceptions; Ruff, 39 JS syntax checks, original exact-cent checks and new geometry checks passed. Acceptance: real 3D pixels and camera traversal; all original content/CTAs intact; no API writes; lazy renderer, bounded mobile pixels/geometry, stopped idle/hidden rendering; reduced motion/Save-Data/short-screen static modes; GPU failure/context-loss/stylesheet-failure fallback; desktop/tablet/mobile keyboard and overflow checks. Execution evidence, complete files, baseline/final commands and any remaining limitations: [EVENT_PORTAL.md](EVENT_PORTAL.md). Hardware performance/hosted deployment remain unverified. Do not treat visual polish as production-readiness certification.

## Current Event Readiness Intelligence ? 27 October 2026

Delivered through an additive read-only endpoint and overview component. Evidence and exact verification commands: [READINESS_INTELLIGENCE.md](READINESS_INTELLIGENCE.md). Repeatable demonstration: [READINESS_DEMO.md](READINESS_DEMO.md).

| Requirement | Actual implementation / acceptance |
| --- | --- |
| Inspection and data support | Saved Guardian, task/checklist, vendor, scenario and Rescue models inspected. Original health heuristic retained; unsupported availability/incident/RSVP/owner data not invented. |
| Transparent readiness | 14 pass/attention/unknown checks, five dimension states, unweighted evidence count and conditional overall state. Unknown never passes. Real-world risk coverage remains unknown. |
| AI explanation/prioritization | Existing Decision Engine plus shared bounded roles/strict output. Only the same three valid server actions may be reordered within urgency tiers; all facts and explanation stay deterministic. Missing/failed/invalid provider uses offline ordering. |
| Actionable dashboard | Native evidence disclosures, three action links to original workflows, confirmed revision/date, read/loading/error/source labels, stale-response guards and refresh on saved changes/reentry. No duplicated editors or hidden application. |
| Integrity | One SQLite owned read snapshot; stale revision 409, foreign event 404, strict body 422. No readiness persistence/migration, finance/apply/retry/security/dependency changes. |
| Demonstration | Existing opt-in fictional saved demo uses real endpoint. Confirmed vendor update and the original scenario approval workflow change readiness evidence; incomplete facts prevent fully-ready claims. Restart recomputes from persisted state. |
| Verification | Baseline 620 / 98.71%; final Python **670 / 98.78%**, two unchanged warnings; **50** targeted cases and **30/30** offline evaluation cases passed. Ruff (96 files), 23 frontend/12 browser syntax, exact-cent, 60-module original-contract and compilation checks passed. Final complete browser run passed all **21 groups**, zero runtime exceptions. Fixture investigations are recorded in the evidence ledger. |
| Remaining limits | Server-calendar date, manual external/day refresh, no comprehensive incident register or independent supplier verification. Native keyboard/responsive checks do not establish formal accessibility certification. Live Gemini/Docker/hosted deployment and independent official submission compliance remain unverified. |

## Previous intelligence-layer completion — 27 October 2026

The attached intelligence brief and optional-feature discovery request are implemented as a bounded core extension. [INTELLIGENCE_UPGRADE.md](INTELLIGENCE_UPGRADE.md) records inspection, execution, actual evidence, full inventory and optional feasibility decisions. [INTELLIGENCE_DEMO.md](INTELLIGENCE_DEMO.md) gives exact setup and judge steps.

| Requirement | Actual status / acceptance |
| --- | --- |
| AI Decision Engine | Implemented: structured evidence, clarification, totals/allowances versus spend, operational impacts, uncertainty and optional isolated proposals. Reuses existing interpreter, simulation and Rescue budget alternatives; save/review/apply remains original. No advice mutation. |
| Quote Analyzer / integration | Implemented supported UTF-8 `.txt`/paste workflow: bounded labels, exact line arithmetic/reconciliation, source evidence, terms and payments, three-source comparison retaining source currency. Explicit quote/commitment recording preserves notes/paid/obligations and rejects stale/duplicate-changed/foreign data. No PDF/OCR or universal parser claim. |
| Design Studio | Implemented local mood boards/recipes, editable brief/validated palette and saved preferred concept with reopenable directions/budget snapshot. Optional Gemini only orders allowed styles. Linked quote workflow, no fabricated imagery/pricing or silent allowance updates. |
| Intelligent Timeline | Implemented read-only recorded-link delay propagation, explicit buffers and event-date/cycle/missing-link constraints. Existing milestones/tasks/exports preserved; no inferred owners/durations or schedulable day-of engine. |
| Digital Twin / Guardian / Rescue | Existing calculators/CRUD/approval retained and integrated. New decision previews and reviewed quotes feed the same services. Committed-vendor cancellation remains indeterminate without contractual resolution; no invented release/refund. |
| Persistence / security | Original contracts/migrations/schema 2 retained; one lazy optional format-1 preference table with owned revision checks/cascade/rollback/unsupported-format protections. Existing R3/R4/R6, actual body cap, CSP/cache repair, source isolation and retry protections preserved. |
| Verification | Baseline 551 / 99.10%; final Python **620 / 98.71%**, two unchanged warnings. Both offline evaluations passed 10/10; final browser run passed 19 groups including full preferred-design reopening, zero runtime exceptions. Ruff (89 files), 22 frontend/11 browser syntax checks, exact-cent/structure/compilation checks passed; exact commands/failures recorded in ledger. Every original Python assertion retained. |
| Optional discoveries | Existing headcount/preferences/forecast and planning progress retained. RSVP/seating, matchmaker, quantitative sustainability and live command center deferred for missing actual models/provenance/delivery semantics. No placeholder screens. |
| Official / release boundaries | Exact official statement not identified from supplied materials/public program pages. No public Git URL/metadata, video accessibility or submission compliance verified. No publish/submit action. Live Gemini/Docker/hosted deployment remain unverified; SQLite single-instance limits remain. |

Follow-ups require explicit scoped work: verified catalog/roster/privacy inputs, consented live-provider evaluation, document storage/payment schedules, real day-of timing/owners, and release/deployment readiness. Do not expand feature count from the optional list without this evidence.

## Previous scroll-led homepage completion — 27 October 2026

The requested premium scroll-animation frontend is implemented without changing the product engine. Full evidence: [SCROLL_EXPERIENCE.md](SCROLL_EXPERIENCE.md).

| Requirement | Actual status / acceptance |
| --- | --- |
| Native scroll storytelling / depth | Implemented and browser-verified. Four pinned editorial chapters, scrubbed architecture/invitation/orbital transforms, hero depth, chapter navigation and progress indicator. Ordinary page scrolling retained; no virtual-scroll library. |
| Responsive / motion preferences | Verified at 1440/1024/768/390/320. Reachable controls, no page overflow, shared pause freezes decoration; static all-visible reduced-motion and short-height modes. Native Enter navigation tested. No-JavaScript static copy exists in HTML. |
| Preserve actual product/data | Verified all prior workflows and saved-state nonmutation. Values use existing fictional demo facts; no network writes or financial calculations. No backend/schema/dependency/contract/Python test changes. |
| Validation / evidence | 546 Python tests / 99.10%, two existing warnings; lint/format, JS/currency/delta/import checks passed; complete browser suite passed all 17 groups. Desktop/mobile chapter/static captures reviewed; five-width local CLS observations zero. Wider performance, assistive tech, live Gemini and hosted deployment remain unverified. |

Stop at the verified homepage refinement; no additional product feature or deployment is part of this request.

## Previous autonomous decision-loop completion — 27 October 2026

The attached autonomous brief authorizes this focused product extension. [AUTONOMOUS_BUILD.md](AUTONOMOUS_BUILD.md) records source preservation, baseline, staged changes, full file inventory, exact commands and limitations. [JUDGE_DEMO.md](JUDGE_DEMO.md) provides startup/configuration and the repeatable presentation.

| Requirement | Actual status / acceptance |
| --- | --- |
| Natural-language event planning | Implemented and verified. Strict bounded partial brief; labeled Gemini/offline extraction; missing-fact questions; exact existing planner preview; reviewed transfer to original wizard; separate explicit save. Stateless intake is not a persisted multi-turn conversation. |
| Grounded What-if / Digital Twin | Existing six commands retained. New additional-guest/currency-cut/percentage venue/catering interpretation uses saved facts/Decimal ledger; ambiguity, commitments and FX prompt clarification. New six-row saved snapshot comparison shows exact cost/difference/percentage/reserve/status; zero percentages are undefined. |
| Signature Rescue workflow | Existing real assessment/options/approval engine reused and verified. New explicitly created separate fictional workspace supplies illustrative expenses/commitment/deposit and cancellation assumptions; assess, compare, approve, reload/restart and original-event nonmutation are browser-tested. Retry-safe creation requires the established owner cookie. |
| Budget Guardian | Existing exact expense CRUD/lifecycle/overrun/missing-cost/reserve/reconciliation behavior retained and regression-tested. New comparison is display-only. Payment reminders remain missing because due-date schedules are not modeled; no inferred market savings/fraud claims. |
| Documents and design studio | Existing supplied-quote comparison and saved conceptual ideas retained. General OCR/uploads, contract parsing, image-provider integration and a new concept versioning workflow are deferred; no unsupported UI claims or dependencies introduced. |
| Security / data compatibility | Verified existing contracts/security tests; two additive routes only. No migration/schema change; default/configured SQLite path retained. Role/schema/output boundaries, owner/revision checks, approval, re-simulation, stale/day checks, rollback and retry stay authoritative. No secret/raw provider exception output. |
| Evaluation / tests | Fresh baseline 496 / 99.04%; final **546 / 99.10%**, two unchanged warnings. Ten offline constraint cases, lint/format, JS syntax, exact currencies/deltas, 48-module contract/import and complete 16-group browser/restart suite passed. No original assertion weakened. |
| Presentation / deployment | Existing cinematic identity retained; desktop/mobile new surfaces and reduced motion verified locally. Project server refreshed after integrity-checked backup; schema 2 and all live documents preserved. Docker/live Gemini/hosted CI/ingress and broader assistive/performance certification remain unverified. |

Completed scope stops at this verified core loop. Follow-ups are live-provider evaluation, bounded source-backed document ingestion if justified, account recovery/durable deployment, and reproducible dependencies/CI. No automatic permission to deploy, contact vendors or make payments is implied.

## Previous invitation experience completion — 27 October 2026

The latest presentation request is implemented within the existing frontend. See [PORTAL_EXPERIENCE.md](PORTAL_EXPERIENCE.md) for the source archive, complete file list, actual commands and intermediate failures.

| Requirement | Actual status / acceptance |
| --- | --- |
| Stronger dimensional arrival and interaction | Implemented and browser-verified: finite camera arrival, paper envelope/flap, lifted invitation, spread arches and spatial detail cards. Native opening/folding is reversible; original planning controls remain. |
| Honest demo content / saved-state isolation | Implemented and verified: reads existing calculated demo facts; no write API. Browser asserts actual 60-guest example and unchanged saved event list. |
| Keyboard and reduced-motion behavior | Implemented and verified: native Enter, Escape/focus return, expanded/controls attributes, closed inert facts and zero-duration reduced-motion opening. Pause/static arrival handling is included; final additional assertions are recorded in the ledger. |
| Responsive visual behavior | Verified locally at 1440/1024/768/390/320: no horizontal overflow when open, saved screenshots and desktop/320px visual review. Existing local CLS observations are zero. Broader devices/FPS remain unverified. |
| Preserve application regressions | 496 Python tests / 99.04%; Ruff lint/format, JS/exact-cent/import-contract checks passed; complete Edge/Uvicorn suite passed 14 checkpoint groups. All baseline Python tests and backend files unchanged. |
| Scope/deployment | No new feature/backend/schema/dependency changes; no runtime DB modifications. Existing SQLite/cookie/quota/provider/deployment limits remain. Stop after presentation verification. |

## Previous homepage motion refinement completion

The uploaded motion brief is implemented. The [motion report](MOTION_REFINEMENT.md) records the 116-file pre-edit archive, fresh baseline, exact commands, reference choices, complete file list, failures/corrections and artifacts.

| Requirement | Actual status / acceptance |
| --- | --- |
| Preserve the editorial CSS 3D scene and product | Implemented and verified. Original transforms/controls remain; all backend and baseline Python files are byte-identical. No schema/API/data/dependency migration. |
| Idle layered motion, tilt, lighting and material detail | Implemented and verified. Six independent motion wrappers, small CSS floats/sways, one pending pointer frame and cached geometry. Native pause preference persists; compact/coarse devices simplify. Local vaulted SVG reflects the reference without using its customer/financial data. |
| Reduced motion, touch, visibility and offscreen | Implemented and verified locally. Actual reduced-motion CSS, CDP touch input, real offscreen scrolling and a simulated hidden visibility event check static/paused states. OS-wide scheduling/device certification remains unverified. |
| Entrance, scroll, navigation, forms and comparison feedback | Implemented and browser-verified. Named easing/durations, short reveals/stagger, button/tab/details feedback and unchanged functional CTAs. No scrolling/motion gate is added to planning. |
| Budget / Rescue previews and genuine success | Implemented and verified. The fictional ring/bars use server shares, transitions finish at exact server strings, demo discard changes no event. Actual failed apply retains saved state/options and error tone; success tone appears after the original backend confirms application. |
| Responsive and visual evidence | Implemented and verified at 1440/1024/768/390/320. No horizontal overflow; local load CLS observations all zero. 22 before screenshots, 13 after screenshots, metrics JSON and 12-frame browser recording/viewer saved under `.artifacts/motion-refinement/`. |
| Regression checks | 496 Python tests, 99.04% coverage; lint/format (69 files), 16 frontend/5 browser syntax checks, exact-cent, 44-module/contract, compileall and all 13 browser checkpoint groups passed. Existing assertions remain. |
| Production/live-provider certification | Not verified. No Docker/live Gemini/hosted CI/real ingress or broad performance/accessibility claim. Existing deployment limitations and two dependency warnings remain explicit. |

This stage ends at verified motion refinement. Deployment/backup/ingress/provider verification remains the next priority; no additional product feature stage is started.

## Previous cinematic refinement completion

The latest cinematic brief extends the completed product. Fresh baseline **474 / 99.01%**; final code **496 tests passed, 2 warnings, 40.04s / 99.04% coverage**. The complete [cinematic ledger](CINEMATIC_BUILD.md) records source archive, approach comparison, file inventory, screenshots, commands, actual failures/corrections and limits.

| Requirement | Status and acceptance evidence |
| --- | --- |
| Audit, fresh baseline and data preservation | Implemented and verified. 107-file source archive before edits because Git metadata is absent. All baseline Python tests and original engines/API/schema/storage/security/dependencies retained. No runtime DB reset/move. |
| Distinctive cinematic 3D hero | Implemented and verified as CSS 3D. Layered architecture, invitation, botanical art, materials and perspective; no WebGL dependency or real-time photorealism claim. Real CSS matrix3d/browser screenshots inspected. |
| Inspiration → planning → intelligence → recovery | Implemented and verified. Four accessible scene controls expose dates/milestone/budget/recovery using the existing calculated fictional demo and link to its explicit review/approval flow. No real event mutation. |
| Motion, responsiveness and fallback | Implemented and verified locally. Finite entrance/reveal/microinteractions, bounded fine-pointer parallax, actual reduced motion/offscreen reset, touch stillness, 1440/768/390 checks, disabled-script and blocked artwork/demo fallback screenshots. Formal device/load/accessibility certification not verified. |
| Existing wizard and complete workspace | Implemented and verified. Original creation, switching, finance, vendor/progress/chat/legacy import, six scenarios/Rescue apply/discard/stale and browser/server restart assertions retained and pass. Workspace typography/context/comparison styling refined. |
| Missing AI language and personalized insights | Implemented and verified within bounded grammar. Relative saved guest count, explicit ISO dates, prefixed percentage reduction and single category quote; missing values/ambiguous records clarify. Copilot explains actual saved warnings/gaps/earliest task. 113 targeted AI/security tests passed. Broader arbitrary-language understanding/live Gemini not verified. |
| Written-quote comparison | Implemented and verified. Two existing isolated category-cost previews, canonical server money, original review/approval, partial-save error/retained draft/event-switch guard tested. No atomic-batch, FX or availability claim. |
| Regression/security integrity | Implemented and verified. Final full suite 496 / 99.04%, Ruff lint/format (69 files), JS/exact-cent checks, 44-module acyclic/original-contract checker, compileall and all 11 real-browser checkpoint groups passed. No tests suppressed or old Python tests changed. |
| Deployment/live provider readiness | Not verified. Docker executable absent; hosted CI/real ingress/live credentials not tested. Durable single-instance SQLite, cookie ownership/recovery limits and existing Cloud Run fail-closed behavior remain explicit. |

No additional feature stage is begun after verification. Next priority remains deployment/backup recovery and real ingress/provider validation from the prior plan. Individual RSVPs, external supplier integrations, account recovery and a persisted incident-description log remain separate unimplemented scopes.

## Previous master-build completion and acceptance

The latest attached master build request authorized the product/frontend transformation and functional Event Rescue, superseding earlier instructions to defer it. **474 tests passed, 2 warnings, 33.95s; 99.01% combined statement/branch coverage** on the final code, versus a freshly measured **429 / 98.88%** baseline. The [complete build ledger](PLANORA_BUILD.md) records the exact commands, all files, verification failures/corrections, inspected screenshots, launch/data configuration and limits. Older “missing Rescue”, “unchanged frontend” and future phase descriptions below refer to earlier snapshots, not the current tree.

| Requirement / phase | Classification | Verified acceptance and dependencies |
| --- | --- | --- |
| Repository audit, safe baseline and archive | Implemented and verified | Read existing source/docs/contracts/security/storage; measured baseline before edits. Git metadata absent; source-only ignored archive retained 76 original files. Original Python tests/engines/security/AI/migrations/contracts/dependencies remain byte-identical. No runtime DB reset/move. |
| Design system, shell and modular frontend | Implemented and verified | Local navy/ivory/violet tokens, original artwork/icons, responsive sidebar, safe module imports, hash navigation/direct reload/back, focused screens. All frontend JS syntax, original browser assertions and new responsive routes passed. |
| Landing, motion and interactive demonstration | Implemented and verified | Visible entrance/reveal/microinteractions, reduced motion, useful CTAs, responsive main navigation, actual engine-calculated explicitly fictional demo. Demo approval was verified to leave real saved events unchanged. No fabricated customers/availability. |
| Five-step creation/review wizard | Implemented and verified | Visible progress, valid bounded supported fields, back/continue retain entries, review, real save/error path and actual workspace opening. Browser drove the visible steps/submit. |
| Complete saved workspaces / event switcher | Implemented and verified (single instance) | Existing cookie ownership/CAS stable IDs, saved details/plan/progress/chat/expenses/history, two-event isolation, browser/server restart, full-detail rebuild and explicit legacy import. Existing SQLite/version/path rules retained. Cookie recovery/multi-instance guarantees are absent. |
| Budget Guardian and editable expenses | Implemented and verified | Existing expense CRUD/quotes/commitments/payments/allocations, server authoritative Decimal summaries and exact-cent large/negative formatting retained. Failed inputs retained; new overview identifies missing prices. |
| Persistent vendor contact/status editing | Implemented and verified | New strict owned current-revision PATCH; bounded fields/enums; foreign child/owner and stale edits rejected. Browser saved/reopened real values; checklist/expense identities preserved. External availability/booking is missing, not implied. |
| Guest planning | Partially implemented (explicit scope) | Saved headcount/dietary/accessibility display and real guest-count preview routing exist. Individual guest records/RSVP/seating workflows are missing and clearly marked. |
| Checklist, timeline/calendar and settings | Implemented and verified | Real saved completion, search/status filtering, date display, original calendar/print, rename/delete/import/edit details. Browser verified progress, filters, routes and restart; destructive actions keep confirmation. |
| All six isolated What-If types and approval | Implemented and verified | Existing complete unit/API/browser tests retained. Shared comparison shows server-derived financial/task changes; strict approval, owner/base revision/day/feasibility/re-simulation/transactional apply/retry/discard remain unchanged. |
| Functional Event Rescue | Implemented and verified within recorded data | Six incident types; deterministic incident/urgency/constraints/affected records; multiple distinct supplied/defensible options; comparison/review/explicit approve or discard; clear unknown/infeasible/stale states. Options save atomically as existing scenarios. Browser exercised actual exact-cost approval, discarded nonmutation, stale rejection and restart. No competing apply engine. |
| Separate incident-description history | Missing (accurately disclosed) | Existing scenario history/statuses persist; transient descriptions/assessments are not a separate incident log. A reliable new log would require its own schema/retention/API work, not a frontend claim. |
| Grounded Gemini copilot / natural language | Implemented and verified offline/provider-fake; live provider not verified | Existing chat and interpretation use preserved R6 boundaries/output validation/fallback. Source attribution reflects actual result. Quick prompts and interpreter handoff cannot mutate the event or bypass approval. No credentials/live success evidence. |
| R3/R4/R6 and request/security regression | Implemented and verified | Original core/AI files unchanged and full adversarial suite passed. New endpoints reuse ownership/current revision/no-store; input fields strict and bounded. No suppressed warnings/tests. |
| Responsive/accessibility/performance refinement | Implemented and verified locally, broader audit not verified | Desktop 1440, tablet 768, mobile 390 overflow/navigation/Escape checks; reduced-motion style verified; 13 screenshots captured and reviewed; local SVG and zero new JS dependencies. Formal assistive-technology/multi-browser/load audit remains unverified. |
| Startup/migrations/DB configuration | Implemented and verified locally | Original schema 2 and v1 migration unchanged; complete suite and actual Uvicorn restarts pass; root/relative/absolute paths retained. Runtime DB exists; inspected read-only and left in place, not reset or used by browser test. |
| Docker, hosted CI/ingress, durable deployment | Not verified | Docker executable unavailable. Existing CI/Dockerfile inspected, no hosted run claimed. Need durable writable single-instance storage, backups and actual raw-peer trusted-proxy validation; Cloud Run saves remain disabled. |

Focused command: `.\.venv\Scripts\python -m pytest tests/unit/test_rescue.py tests/integration/test_rescue.py tests/integration/test_coordination.py tests/integration/test_planora_frontend.py tests/integration/test_structure.py -q` — **52 passed**. Final full command: `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` — **474 passed / 99.01%**. Ruff `check app tests scripts` passed; `format --check app tests scripts` reported 66 already formatted. All 14 frontend JS files passed `node --check`; browser runner/product module syntax and production exact-cent tests passed. `python -m scripts.check_structure` verified 42 acyclic app modules and retained original HTTP contracts. `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe` passed all nine checkpoint groups with no runtime exceptions, including additional desktop/mobile/Rescue/browser/server-restart acceptance. `compileall -q app` passed. The build ledger contains the full commands and Docker failure, rather than assuming historic counts.

**Next priority (not implemented here): validate deployment and recovery.** On the chosen single-instance host, mount a durable absolute SQLite path, verify permission/backup/restore without destructive reset, test trusted ingress headers/raw peer with `--no-proxy-headers`, and verify actual Gemini success plus graceful outage. Acceptance must include restart/redeployment retaining owned workspaces/expenses/scenarios, foreign-cookie rejection, backup restore in a separate test location, unchanged security headers/body/rate limits and truthful provider status. Distributed storage/quotas, account recovery, RSVP records and a separate incident log remain separate scopes.

## Historical stage records

Earlier implementation stages are historical evidence. **The structural refactor is verified with 429 passing tests, 98.88% combined statement/branch coverage and a passing browser/restart smoke run.** All 422 baseline cases remain. Existing features/security remain intact; production/multi-instance storage, accounts and Rescue remain outside this implementation.

## Structural reorganization - complete and verified

The separately requested structural task is complete; no Rescue/product feature was added. Fresh baseline: **422 passed, 2 warnings, 34.30s / 98.86%**. Final: **429 passed, 2 warnings, 34.60s / 98.88%**, including all original 422 cases and seven meaningful refactor checks. No coverage floor was lowered. The original test functions/decorators/assertions and frontend bytes were independently compared with the pre-move archive.

The [complete refactor ledger](REFACTOR_MAP.md) is the authoritative move map, original/final tree, every-file inventory and execution log. It was created with the proposed map before moving source. Groups were checked independently: schemas (170 passed), frontend (80 plus exact-cent), services/AI (300), SQLite split (71), HTTP/core (220), moved original suite (422), added structure checks (7), full coverage (429), focused startup/migrations (6) and the complete real browser/restart smoke (all seven checkpoints). Intermediate import/mock-target errors were corrected; assertions were retained. Exact pre-refactor OpenAPI equality and acyclic top-level imports are checked by `python -m scripts.check_structure` and the suite.

Launch remains `app.main:app`. From the repository root on Windows: `.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers`. Source assets moved to frontend but public `/static` URLs stay. SQLite defaults to project-root data/eventra.sqlite3; explicit relative/absolute EVENTRA_DB_PATH semantics and schema version 2 remain. Migration statements were moved without changing their AST/SQL; existing files are never reset by the refactor. Pydantic contracts stay together in schemas, no empty models/data directories or old import shims were added. Internal Python import paths changed and are documented; no external Python SDK compatibility promise existed for those old modules.

Ruff lint/format (61 files), JS syntax and exact-cent display checks passed. Docker paths are updated but `docker --version` found no Docker executable; container build/runtime is not verified. Existing dependency warnings, live-provider/hosted-ingress limitations, per-process quotas and local/durable single-instance SQLite/account constraints remain. Git metadata is absent; an ignored source-only baseline archive preserves supplied changes. Future product work remains unstarted.

## R6: legacy priority prompt-boundary repair

Historical pre-refactor paths/results follow. Use the structural ledger and README for current locations.

### Inspected attack path and bounded repair

The audit's exact payload `</verified_plan><user_data>` fits the existing accepted/truncated priority field. `_plan_prompt()` originally serialized raw `req.priorities` inside a block claimed as verified, using unescaped `json.dumps`. Both `/api/plan` and `/api/chat` used it; workspace creation/rebuild/regeneration and explicit browser-draft import also use the same legacy narrative generator. Two regressions were run **before repair** and failed with unterminated verified JSON in both plan/chat prompts. This reproduces structural boundary confusion, not a successful live-model compromise. The SDK already had separate `system_instruction`; no raw priority was literally in that SDK system field.

Verified priorities now come only from deterministic `BudgetLine.priority` category keys. Raw accepted priorities and all other preferences remain bounded, losslessly JSON-encoded user data. Shared encoding escapes literal `<`, `>` and `&` and preserves Unicode/punctuation, rather than deleting personalization. Chat questions are also JSON data. Chat no longer globally removes the phrase `Produce the JSON object now.` from user notes; fixed generation instructions stay in the system configuration. The Gemini adapter now explicitly constructs a user-role Content message with separate fixed system instructions; stub-transport tests exercise the installed SDK's actual Content/Config types.

| AI entry path | Data crossing the boundary | Authority and exclusions |
| --- | --- | --- |
| Legacy generation, including saved creation/rebuild/import | Validated title/city/theme/interests/dietary/notes/raw priorities in user data; enums/numbers/derived category priorities in verified data | Engine owns money/dates/health; model supplies display narrative only. No request text enters system instructions. |
| Legacy stateless chat | Same context plus a bounded serialized question | Advisory text only, no tools or mutation API. |
| Saved-workspace chat | Current numeric ledger/tasks/dependencies/vendor IDs/status; full bounded preferences and question as user data | Existing strict action enum/current revision/category whitelist; server renders financial/task facts. Vendor contact/quote notes, expense descriptions/notes, generated prose and previous chat are not fed back. |
| Scenario interpretation | Current numeric context and bounded user request, static server schema | Existing strict discriminated commands only; interpretation never creates/previews/applies a change. Saved owner/revision/feasibility/approval checks remain separate and authoritative. |

There is no vendor-message ingestion, document retrieval or tool-execution feature to invent or secure here. Existing vendor quote-note foundation fields are excluded, as are imported/generated descriptions not part of supported intake. Tests verify those exclusions with distinct adversarial markers; supported imported event notes remain data. Import cannot supply privileged/generated plan state.

### Output and failure containment

All four call paths use a shared 128,000-character outbound-context and 16,000-character provider-text cap; existing API field bounds, cleaning and the 20,000-byte request limit remain. Over-limit context/output falls back offline. Exact active-prompt/system-instruction/configured-key echoes are rejected, including JSON-decoded nested strings before display clamping. A dedicated regression reproduced a JSON-escaped system echo passing the first raw-only check; the final check validates decoded values too. This is an exact-echo guard, not semantic detection of every paraphrase or disclosure.

Legacy narrative parsing now validates private strict/extra-forbidden provider schemas before retaining the existing length/count clamping and minimum useful output rules. Unknown top-level/nested fields and wrong types are rejected rather than coerced/dropped. Narrative category strings remain bounded display labels, not action permissions. Structured advice/interpretation retain existing action/command enums, reference/revision validation and strict extra-field rejection. JSON duplicate keys, non-finite constants, root arrays and oversized malformed text are rejected; supported fenced/prose-wrapped single objects still work. No public API schema changed.

Only exception classes are logged on AI failures, including SDK initialization; no exception payload, traceback, raw prompt/output or key is logged by these paths. Missing credentials and provider errors keep deterministic fallback. Credentials remain SDK authentication only, never prompt fields. Model roles, data encoding and instructions reduce boundary confusion but are not a complete prompt-injection defense. Validly shaped legacy prose can still give false or manipulated advice; a regression explicitly shows that such prose cannot alter deterministic numeric fields or saved operational state.

### Verification and remaining scope

The new file contains **69 adversarial cases**; all 353 earlier cases are retained unchanged. Tests cover priority injection on both legacy paths, all preference fields, imported/extended/vendor/generated content, structured SDK roles, Unicode/multiline/controls/oversize, strict output/duplicates/types/values, exact echoes, secrets/errors/no-key behavior, fixed numeric results and read-only interpretation followed by ownership/approval/feasibility/stale/retry enforcement.

| Actual executed command | Result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest tests/test_ai_boundaries.py --tb=short` before production changes | **2 failed**, one existing warning, 0.21s; verified JSON boundary broken on both legacy plan/chat paths. |
| `.\.venv\Scripts\python -m pytest tests/test_ai_boundaries.py -k json_encoded_internal --tb=short` before decoded echo fix | **1 failed**, 68 deselected, 0.98s; escaped instruction echo was accepted as Gemini narrative. |
| `.\.venv\Scripts\ruff format app/ai.py app/workspace_ai.py tests/test_ai_boundaries.py` | 1 reformatted, 2 unchanged. Subsequent targeted format commands covered `app/ai.py tests/test_ai_boundaries.py` and the new test file; final pass left both unchanged. |
| `.\.venv\Scripts\python -m pytest tests/test_ai_boundaries.py tests/test_ai_and_api.py tests/test_workspace_ai.py --tb=short` | Initial repair 55 passed/1.72s; expanded corrected run 120 passed/9.22s. |
| `.\.venv\Scripts\python -m pytest tests/test_ai_boundaries.py tests/test_ai_and_api.py tests/test_workspace_ai.py tests/test_security.py tests/test_request_limits.py --tb=short` final | **240 passed**, 2 warnings, 20.12s. Earlier expanded run was 239 passed before the escaped-echo regression/fix. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` final | **422 passed**, 2 warnings, 27.58s; **98.86% combined statement/branch coverage**. `app/ai.py` rounds to 97%, `app/workspace_ai.py` 98%, proxy/limiter each 100%. Intermediate pre-echo-fix run was 421/98.85%, not the final result. |
| `.\.venv\Scripts\ruff check .` | All checks passed. |
| `.\.venv\Scripts\ruff format --check .` | 38 files already formatted (tool output). |
| `node --check static/app.js` | Passed. |
| `node --check tests/browser_workspace_smoke.mjs` | Passed. |
| `node --check tests/test_money_display.mjs` | Passed. |
| `node tests/test_money_display.mjs` | Exact-cent/large-total/negative-fraction display passed. |
| `node tests/browser_workspace_smoke.mjs .venv/Scripts/python.exe` | Final run **passed all seven checkpoints, exit 0**, using actual Edge/Uvicorn, the same temporary profile/database, both browser/server restarts, expenses/metrics, scenario comparison/reject/approve and legacy import. Earlier restart attempts failed; diagnosis and runner fixes are explained below. |

The warnings are unsuppressed: existing Starlette/HTTPX TestClient deprecation and an installed google-genai `_UnionGenericAlias` deprecation surfaced by the new real SDK-type/stub-transport test on Python 3.14. No SDK network call or credential success is claimed. The failed browser run retained its own locked temporary profile; after verifying no Edge process used that exact profile, its exact path was checked under the temporary directory and removed. No user browser/profile or development database was touched.

Two test-development failures were investigated without product changes: response JSON contains intentionally read-only computed expense fields, so the test fixture now reloads the canonical repository model; Pydantic already rejects lone Unicode surrogates, so tests assert that rejection and valid Unicode round trips. Neither required weakening input validation. The escaped echo regression caused an additional focused production fix and final verification rerun.

Changed files: `app/ai.py`, `app/workspace_ai.py`, new `tests/test_ai_boundaries.py`, `tests/browser_workspace_smoke.mjs`, `README.md`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md` (**7 total**). No dependency, product engine/budget/scenario/repository/middleware/schema or frontend implementation changed. Browser-runner changes are limited to readiness/diagnostics and owned-process/profile cleanup; all existing workflow assertions remain. No Event Rescue Mode work was started. Prompt injection is not claimed solved; live Gemini, hosted ingress, remote CI, Docker runtime, shared production storage/accounts and the existing local SQLite limitations remain unverified/unimplemented as previously documented.

Browser investigation: repeated attempts failed after the first workflow with Edge exit 21 / Windows singleton-lock error 32. Readiness polling could also stop on an empty debugging page list. The runner now waits for a real debuggable page, captures bounded startup/termination diagnostics, permits graceful profile flushing, checks actual OS process liveness after tree/native termination (not just stale exitCode), handles signalCode, and removes only its own stale lock after process exit. Final cleanup runs even on shutdown failure. Background mode is disabled for the test browser. This preserves the same cookie/localStorage/database and every persistence assertion. Exact known failed-run temporary directories were verified under the temporary parent with no matching Edge process and removed; no user profile/data was touched. Earlier passing Python runs were not substituted for the final browser result.

Final documentation validation passed UTF-8/local-link checks for README, audit, plan and the unchanged budget rules. The source inventory has 39 app/static/test files excluding bytecode; compared with Stage 4, only the two AI modules and browser runner changed, plus the new adversarial test file. All other feature/engine/test source is preserved. The default development database remains absent. Final lint/format/JS checks were rerun after runner changes; the final complete-tree suite is the 422/98.86%/27.58s run above.

## Stage 4: R3/R4 security hardening — completed

Historical Stage 4 evidence follows. R6 above supersedes its next-task status; proxy/limiter deployment limitations remain unchanged.

Inspection confirmed the audit's exact defects in `app/main.py`: `TRUST_PROXY` defaults to enabled and uses the last raw XFF value without verifying the socket peer; Docker additionally enables Uvicorn's wildcard forwarded-header trust. The limiter inserts a deque for each key, expires timestamps only on that key's next request, and its nominal 10,000-key pruning removes only already-empty deques. There is no lock or safe full-capacity policy. The initial Stage 4 full-suite rerun passed **280 tests / 98.05%** (15.48s, existing TestClient warning).

The proposed steps were implemented separately: proxy identity/launch settings first, then limiter internals, followed by expanded unit/API/wire/browser checks. No dependency, product API schema, database version, budget rule or frontend implementation changed. Rescue was excluded.

### R3: policy and deployment contract

New `app/proxy.py` resolves identity before the existing guard constructs its Request. `TRUSTED_PROXY_CIDRS` defaults to empty, including under `K_SERVICE`; no proxy, Cloud Run hop order or private network is implicitly trusted. Allowlist entries must be explicit IPs/canonical CIDRs (at most 32, 4,096 configuration characters). Wildcards/universal ranges/hostnames/scoped addresses are rejected. Legacy `TRUST_PROXY=1` fails clearly with migration guidance; empty/0 grants no trust. `Forwarded`, `X-Real-IP` and forwarded Host have no authority.

Only a trusted socket peer can supply XFF. One header of at most 2,048 bytes/32 bare-IP hops is validated completely; IPv4, IPv6 and mapped IPv4 canonicalize to stable keys. The nearest untrusted hop from the right becomes the client; spoofed prefixes cannot override it. Missing/duplicate/malformed/oversized/all-trusted chains fall back to the peer, never a newly invented identity. Unknown transport peers share an `unknown` bucket. Only a trusted peer's single exact `http`/`https` Proto value changes the scheme, preserving HTTPS cookie/origin behavior. The trusted ingress must append/replace the true connecting address, overwrite Proto, preserve public Host and prevent conflicting headers. Restrict access to the backend and allowlist only actual proxies.

The image, README local commands and browser runner now use **`--no-proxy-headers`**. This is required: an upstream ASGI component that rewrites the peer before our policy removes the evidence needed for trust decisions. No double processing or wildcard Uvicorn trust is supported. Real Uvicorn tests deliberately set `FORWARDED_ALLOW_IPS=*` and verify it is inert with this flag. Empty trust conservatively shares ingress quotas until deployment-specific peers are verified/configured. Docker/cloud/real hosted topology were not executed or inferred.

Middleware order is now outer server-error handling → **trusted identity → existing guard → actual-body boundary → gzip → exception/router handling**. The original guard/body/gzip ordering and early-response helper remain intact. No new outer-500 header guarantee is claimed.

### R4: state bound, expiry and saturation

New `app/rate_limits.py` retains sliding-window semantics. A lock covers clock sampling, cleanup, quota checks and admission; an OrderedDict orders queues by last admitted timestamp. On each protected request, fully expired clients are removed from the front and the current client's old timestamps are pruned. Exact boundary timestamps expire. Denials do not append timestamps, refresh retention or create new keys. Cleanup is request-driven; with no traffic, expired entries may remain until the next protected request, within the hard bound.

`RATE_MAX_CLIENTS` defaults to 10,000. At capacity, existing clients retain their quotas and new clients get the existing 429/error/security/no-store shape plus a rounded-up Retry-After until the earliest whole slot can expire. No active quota is evicted/reset and no unbounded rejection map is created. Availability for new clients is deliberately reduced during saturation. Rate settings must be positive integers with limit ≤10,000, window ≤86,400 seconds, clients ≤100,000, and limit × clients ≤1,000,000. Default structural state is at most 10,000 entries/300,000 admitted timestamps; this is not a measured RSS claim. The browser harness explicitly uses a small compatible capacity with its higher test quota.

Limits are still process-local and restart-resetting; workers/replicas multiply quotas. This stage is not a distributed limiter or multi-instance production-readiness claim. Workspace anonymous cookies, schema v2, single-instance SQLite and Cloud Run fail-closed storage are unchanged.

### Executed commands and acceptance evidence

| Command | Actual result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` before changes | **280 passed**, one existing warning, 15.48s; **98.05%**. |
| `.\.venv\Scripts\python -m pytest tests/test_security.py --tb=short` before fixes | **3 failed**, 0.23s: direct rotating XFF returned 200 instead of 429; 100 idle entries survived expiry; 10,001 clients exceeded the nominal 10,000 bound. |
| `.\.venv\Scripts\ruff format app/main.py app/proxy.py app/rate_limits.py tests/test_security.py` | 3 files reformatted, 1 unchanged. Subsequent targeted format commands covered `app/proxy.py tests/test_security.py` (1 reformatted/1 unchanged) and `tests/test_security.py` (unchanged). |
| `.\.venv\Scripts\python -m pytest tests/test_security.py tests/test_ai_and_api.py tests/test_request_limits.py --tb=short` after initial fixes | 79 passed, one existing warning, 1.69s. |
| `.\.venv\Scripts\python -m pytest tests/test_security.py --tb=short` after expanded unit/API checks | 69 passed, one existing warning, 0.41s. |
| `.\.venv\Scripts\python -m pytest tests/test_security.py tests/test_request_limits.py tests/test_ai_and_api.py --tb=short` final | **149 passed**, one existing warning, 6.27s (earlier wire-test run: 147 passed/9.85s). |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` final | **353 passed**, one existing warning, 20.00s; **98.43% combined statement/branch coverage**. New proxy and limiter modules each 100%; all 280 existing cases retained unchanged. |
| `.\.venv\Scripts\ruff check .` | All checks passed. |
| `.\.venv\Scripts\ruff format --check .` | 37 files already formatted (tool output). |
| `node --check static/app.js` | Passed. |
| `node --check tests/browser_workspace_smoke.mjs` | Passed. |
| `node --check tests/test_money_display.mjs` | Passed. |
| `node tests/test_money_display.mjs` | Passed exact-cent/large-total/negative-subunit display checks. |
| `node tests/browser_workspace_smoke.mjs .venv/Scripts/python.exe` | Restricted attempt started Uvicorn but failed at CDP `Runtime.enable` timeout. Unchanged runner repeated with local process/network access: **all seven output checkpoints passed, exit 0**. |

`tests/test_security.py` adds **73** cases. Coverage includes direct/spoofed/trusted/chained/mapped/IPv6 clients; absent/invalid/duplicate/oversized forwarding and exact parsing bounds; unsupported/unsafe proxy settings; trusted HTTPS Secure/HttpOnly/SameSite cookies and origin enforcement; real HTTP/Uvicorn direct and trusted configurations; exact sliding expiry and Retry-After; inactive cleanup on denied hot traffic; high-cardinality saturation without key growth/eviction; concurrent same-key admission/expiry and distinct-key capacity; bounded positive configuration; capacity rejection headers and unread bodies. Supported launcher flags have regression assertions. Deterministic clocks are explicit in limiter tests; no test threshold or existing test was weakened.

The real browser uses temporary DB/profile and its own Uvicorn process, with keys disabled. It passed creation/progress/chat/rename/reopen, second-event isolation/rebuild/failed save/delete, expense editing/metrics/allocation/cancel-confirm behavior, scenario isolation/reject/approval and two full browser/server restarts preserving financial/scenario state, plus explicit legacy import. This validates product regressions and startup, not complete accessibility/mobile/print/calendar imports or hosted deployments.

### Exact changed files and remaining work

New: `app/proxy.py`, `app/rate_limits.py`, `tests/test_security.py`.

Modified: `app/main.py`, `Dockerfile`, `.env.example`, `tests/browser_workspace_smoke.mjs`, `README.md`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md` (**10 files total**). Browser changes are launch/configuration only; existing workflow assertions remain. Existing application feature modules, production frontend, budget rules, dependency declarations and all old Python test files were preserved.

The existing Starlette/HTTPX TestClient deprecation warning remains; no suppression or dependency migration was introduced. Live Gemini, Docker runtime, hosted CI, real ingress semantics and cloud durability remain unverified. R6 legacy generation priority-text prompt boundary remains the next focused security task (`app/ai.py`, targeted AI/API tests); test that no accepted priority can introduce trusted prompt delimiters while preserving generated numbers/fallback/old contracts. Per-process quotas, saturation availability, misconfigured outer proxy processors, account recovery/shared storage and the audit's other release limits remain explicit. Event Rescue Mode was not started.

Final document checks passed for UTF-8 and local file links. All 38 files under app/static/tests (excluding bytecode) were hash-checked unchanged during documentation. Compared with the Stage 3 source snapshot, only existing `app/main.py` and the browser launch/config changed, plus the three new security files; production frontend and feature modules were preserved. The default development database `data/eventra.sqlite3` remains absent. Tests were not rerun after documentation-only edits.

## Stage 3: Budget Guardian and isolated What-if — completed locally

This is historical Stage 3 evidence. Stage 4 above supersedes its R3/R4 next-task status and test totals; accounting/product scope remains unchanged.

### Scope, architecture and migration

The attached Stage 3 request authorized implementation without another approval gate. Initial inspection and a rerun confirmed the supplied **209 passing tests / 97.12% coverage** baseline. The existing FastAPI/Pydantic/plain-JavaScript architecture, engine, AI adapter, cache, request-size middleware and legacy generation schemas were retained. No dependency was added. The work extends the workspace envelope rather than replacing the application.

- `app/budget_models.py`, `app/budget.py` and `app/budget_api.py` provide strict expense inputs, one Decimal reconciliation service and owned/revisioned expense/allocation operations. Authoritative summaries are calculated, not independently stored. Stable record IDs, created/updated timestamps, provenance, lifecycle amounts and history survive reopening/restarts.
- `app/scenario_models.py`, `app/scenarios.py` and `app/scenario_api.py` provide validated commands, pure deep-copy calculation, persisted previews and explicit approval. Simulation reuses the existing budget/date engine and task reconciliation. It does not call Gemini or write the original event.
- `app/workspace_ai.py` supplies complete current financial/task/vendor context, validated advice actions and validated scenario interpretation. Server rendering supplies all monetary/task facts. Model interpretation only fills a reviewable structured form; it never creates or applies a scenario. Missing/invalid provider output falls back safely and identifies its source. Live Gemini credentials were not exercised.
- `app/storage.py` migrates SQLite/workspace schema **1 → 2 transactionally**, preserving IDs/history/progress and translating old expense `amount` into estimated unit amounts with `legacy` provenance. New scenarios have an event foreign key with cascading deletion. Malformed data/unknown versions roll back without resetting the database. Derived current budget/expense fields are excluded from stored JSON. **Stop the previous application and back up the database before upgrade; downgrade is unsupported.**
- Existing anonymous-cookie ownership, cross-origin checks, 20,000-byte actual-body limit, security headers, atomic revision checks and Cloud Run fail-closed behavior remain. SQLite supports local/durable single-instance use only. Tests use temporary databases; the browser runner also uses its own profile and Uvicorn process.

Accounting rules and unsupported financial cases are specified in [BUDGET_RULES.md](BUDGET_RULES.md). Money uses Decimal strings and HALF_UP cent rounding; event budgets/allocations retain whole-unit compatibility. Estimates, quotes, commitments and payments are separate stages of one expense. Projected exposure uses the selected stage with a paid floor, never their sum. Missing pricing remains unknown; fixed fees remain a known lower bound. Manual allocations never silently rebalance and survive rebuilds. Guardian warnings permit incomplete/overallocated editing states; such a state cannot be approved as a feasible scenario.

### Functional UI and approval boundary

The existing Budget tab now edits saved expenses, quantity/unit model, fixed taxes/fees, all-in quotation/commitment/cumulative payment, notes and category allocations. It displays server summaries, per-category/per-guest figures, explained warnings and reconciliation. Confirmed delete is a record correction, not a refund. Failed saves retain inputs; creation retries reuse the request UUID. Decimal-string/BigInt formatting preserves cents even above JavaScript's exact-number range.

The What-if tab supports six structured types: budget reduction, guest count, event date, vendor cancellation, venue/catering cost change and additional function. A budget reduction may include explicit proposed allocation edits; it does not invent cuts. Fixed prices do not scale with guests, recorded per-guest prices do, and all-in/legacy assumptions require reconfirmation. Missing cancellation/replacement information is indeterminate; supplier availability is never invented. Dependencies, dates, reserve and known financial violations are deterministic constraints.

Every saved preview shows original/proposed details, metrics/allocations, expense changes, affected tasks/dependencies, vendor status, warnings and feasibility reasons. Creation/comparison/discard leave the event unchanged. Application requires a checked approval control **and** a feasible, pending, owned preview at the current event revision and evaluation day. The server recalculates and compares the full preview before applying; the repository rechecks revision/status/date inside the transaction. Event + history + scenario status commit together or roll back together. An applied retry cannot apply twice; any event revision conservatively stales pending previews. No silent rebase or automatic application exists. Unsaved input is guarded and obsolete preview fetches cannot replace current state.

### Additive API inventory

All paths start with `/api/events/{event_id}` and enforce the existing owner boundary; foreign/missing event or child IDs are hidden behind 404. Event mutations and preview creation/interpretation require a revision; discard changes only the owned preview status without an event write. Conflicts return 409, validation 422, unavailable storage 503. An already-applied retry returns the current event without another write.

| Method and suffix | Contract |
| --- | --- |
| `GET /budget` | Complete derived budget summary. |
| `GET /budget/warnings` | Explained warnings with record/category/amount references. |
| `GET /budget/expenses` | List the event's stable expense records. |
| `GET /budget/expenses/{expense_id}` | Retrieve one owned record. |
| `POST /budget/expenses` | Revision, request UUID and validated expense; 201 with committed workspace. Exact retries do not duplicate records/revisions; changed payload under the same key conflicts. |
| `PUT /budget/expenses/{expense_id}` | Revision and replacement editable expense values; server owns IDs/timestamps/totals. |
| `DELETE /budget/expenses/{expense_id}` | Revision and matching confirmation UUID; return committed workspace. |
| `PATCH /budget/allocations` | Explicit partial allocation updates; no automatic balancing. |
| `POST /scenarios` | Revision and discriminated typed parameters; 201 with separate saved preview. |
| `GET /scenarios` | List saved previews and current stale status. |
| `GET /scenarios/{scenario_id}` | Retrieve preview. |
| `GET /scenarios/{scenario_id}/compare` | Retrieve the full persisted before/after comparison. |
| `POST /scenarios/{scenario_id}/discard` | Mark pending preview discarded; no event mutation. Applied previews cannot be discarded. |
| `POST /scenarios/{scenario_id}/apply` | Current revision and explicit true approval; return actual committed workspace. |
| `POST /scenarios/interpret` | Revision/question → validated suggested parameters or structured-form fallback; read-only. |

### Acceptance criteria and evidence

All 209 previous test cases remain. The only changed old assertion expects schema version 2 after migration instead of 1. No tests were weakened and the coverage gate remains 90%.

| Stage 3 acceptance | Verified evidence |
| --- | --- |
| 1–2: expense CRUD and reconciliation after mutation | `tests/test_budget.py`: API CRUD, stable IDs, summaries derived on read, every lifecycle mutation and allocation propagation; browser add/edit/delete/metrics. |
| 3–6: Decimal rounding, lifecycle separation, overrun detection, no double counting | Budget unit/API cases cover cent ties, invalid binary-float input, partial paid/commitment floors, quote discrepancies, cancelled liabilities, missing costs/known fees and orphan categories. `tests/test_money_display.mjs` covers exact UI cents including large and negative values. |
| 7–8: invalid-write isolation and restart persistence | Invalid category/vendor/currency/amounts, stale writes, real SQLite abort, idempotent retries, v1 migration/rollback, fresh repository reads; real browser and server restart retain expense/summary state. |
| 9–12: create/read/isolate/guest/budget previews | `tests/test_scenarios.py`, `tests/test_scenario_api.py`: unchanged original document, exact per-guest models, fixed-cost preservation, missing/reconfirmation assumptions, Decimal reduction and explicit allocations. |
| 13–16: dates, vendor dependencies, infeasible/indeterminate | Existing timeline engine, preserved completed IDs, overdue/urgent work, cyclic/missing/reversed dependencies, cancellation/transitive tasks, expense limit, contract floors, known violations versus unknown prices. |
| 17–22: stale rejection, approval, discard, rollback, retry, history | Scenario API cases verify revision/day expiry, changed preview rejection, explicit true approval, atomic SQLite-trigger rollback, racing write conflict, discarded/non-feasible rejection, no duplicate application and saved change history. Browser verifies checkbox alone does not mutate, reject retains original and approved guest change updates the actual saved form/ledger. |
| 23–24: event and child ownership | Budget/scenario foreign-session and cross-event expense/vendor/scenario checks; event deletion cascades scenarios without removing unrelated events. |
| 25–27: security and existing contracts/workflows | All previous request-limit/security/generation/workspace tests retained in the full suite. Extended browser smoke retains event creation, progress, saved chat, two-event isolation, rebuild, failed-save recovery, delete, legacy import and restarts. |
| 28: no-key operation | Deterministic budget/simulations and browser smoke run without keys. `tests/test_workspace_ai.py` verifies offline interpretation and invalid/stale/fabricated provider responses with fakes; no live success claim. |

### Final commands actually executed

These are the final runs after code changes; subsequent edits are documentation only.

| Command | Actual final result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest tests/test_budget.py --tb=short` | **25 passed**, one existing warning, 1.19s. |
| `.\.venv\Scripts\python -m pytest tests/test_scenarios.py tests/test_scenario_api.py --tb=short` | **24 passed**, one existing warning, 3.47s. |
| `.\.venv\Scripts\python -m pytest tests/test_workspace_ai.py --tb=short` | **22 passed**, one existing warning, 1.41s. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` | **280 passed**, one existing Starlette/HTTPX TestClient deprecation warning, 16.83s; **98.05% combined statement/branch coverage**. |
| `.\.venv\Scripts\ruff check .` | All checks passed. |
| `.\.venv\Scripts\ruff format --check .` | 34 files already formatted (tool-reported). |
| `node --check static/app.js` | Passed. |
| `node --check tests/browser_workspace_smoke.mjs` | Passed. |
| `node --check tests/test_money_display.mjs` | Passed. |
| `node tests/test_money_display.mjs` | Passed; exact-cent rendering, large totals, negative subunit/large values and unknowns. |
| `node tests/browser_workspace_smoke.mjs .venv/Scripts/python.exe` | **Passed**, exit 0, real Edge 155 + actual Uvicorn startup/HTTP APIs. All earlier workspace checks plus expense/allocations, failed-input retention, infeasible preview, isolated reject, explicit approval, and another browser/server restart retaining financial/scenario state. |

The browser runner uses Node built-ins, temporary SQLite/profile, disabled provider keys and owned subprocesses; no npm dependency or real workspace data. The final browser run required local process/network access outside the restricted sandbox. This is workflow evidence, not a full mobile/keyboard/screen-reader/print/calendar-import certification. No Docker/cloud/hosted-CI or live Gemini validation was run. Earlier intermediate test/harness failures were corrected before these final passes; no failure was suppressed.

After documentation updates, `.\.venv\Scripts\python -m coverage report` read the existing final artifact without rerunning tests: 1,661 statements, 21 missed, 446 branches and 18 partial branches (the terminal rounds total coverage to 98%; the full run reported 98.05%). A SHA-256 comparison of all 35 files under `app`, `static` and `tests` (excluding bytecode caches) found no changes during this documentation pass. A read-only UTF-8/local-link check passed for all four documents, and `data/eventra.sqlite3` does not exist; test data stayed isolated.

### Exact Stage 3 changed files (25)

| Change | Files |
| --- | --- |
| New budget modules | `app/budget_models.py`, `app/budget.py`, `app/budget_api.py` |
| New scenario/AI modules | `app/scenario_models.py`, `app/scenarios.py`, `app/scenario_api.py`, `app/workspace_ai.py` |
| Existing application integration | `app/main.py`, `app/storage.py`, `app/workspace_models.py`, `app/workspaces.py` |
| Existing frontend | `static/index.html`, `static/app.js`, `static/style.css` |
| New tests | `tests/test_budget.py`, `tests/test_scenarios.py`, `tests/test_scenario_api.py`, `tests/test_workspace_ai.py`, `tests/test_money_display.mjs` |
| Existing tests | `tests/test_workspaces.py` (migration version assertion), `tests/browser_workspace_smoke.mjs` (extended real workflows) |
| Documentation | `README.md`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md`, new `docs/BUDGET_RULES.md` |

The supplied directory has no Git metadata; this inventory is the session's edits, not a claimed Git diff. Original engine/legacy models/AI adapter/service/cache/request-limit source and dependency files were preserved.

### Remaining gaps and single next recommended task

Stage 3 is complete within the documented local/single-instance boundary. Refunds/negative credits, FX conversion, installment/payment transaction ledgers, tax-rate calculation, payment processing, accounts/recovery, shared production storage, automatic backups, archive/undo, custom task/dependency editors, full vendor-management UI, arbitrary combined scenarios and Event Rescue Mode remain unimplemented. Feasibility is conditional on recorded pricing/assumptions; it does not establish vendor availability or market affordability. Old heuristic health scoring remains a heuristic; it is recomputed after budget changes, not replaced with operational risk intelligence. Live Gemini, containers, hosted CI and deployed durability remain unverified.

**Historical Stage 3 next task: R3/R4 hardening.** It is now complete with affected files, acceptance evidence and results in Stage 4 above. Rescue can later reuse the scenario approval transaction after a separately scoped implementation; it was not started.

## Persistent event workspace stage — historical completion evidence

This section records Stage 2 at schema version 1. Stage 3 above supersedes its expense/scenario/AI limitations and migrates storage to version 2; the historical 209-test results are not the latest results.

The owner's attached implementation request explicitly selected this stage ahead of remaining proxy/AI roadmap work. The existing engine, AI adapter and legacy `/api/plan`, `/api/chat`, `/api/ics` contracts were preserved. No dependency was added.

### Canonical state, persistence and deployment boundary

- Python's standard-library SQLite stores one complete owned `EventWorkspace` document per stable event UUID. All nested task/vendor/checklist UUIDs, chat and history are committed in the same transaction. The repository in `app/storage.py` opens/closes short-lived connections; the service/API in `app/workspaces.py` does not put SQL in route callers or the engine.
- Preferences include all original request fields plus venue, cultural/accessibility requirements, assumptions and unresolved decisions. A stored `Plan` is the sole generated budget/date/narrative snapshot; it is not re-created when reopening. Task and checklist state points to that snapshot with stable IDs and indices. Regeneration matches semantic category/title/checklist keys, preserving IDs and completion. Type changes require a new event to avoid discarding saved child state.
- Expense, vendor contact/quote/booking, task priority/dependency structures are available in the persisted schema, initially empty/default where the old application had no such user data. **There is no expense/quote/custom-task editor or endpoint in this stage.** New metadata is stored, but the existing Gemini prompt still uses the original preference fields; put relevant AI instructions in Notes.
- Each successful mutation appends a timestamped change summary and advances a revision. Updates and deletion compare the expected revision inside a SQLite write transaction; stale writes return 409. Failed generation/validation/commit never partially replaces a document or returns a successful save. Missing or other-session IDs return 404. Storage errors return 503, while stateless APIs remain available.
- An HttpOnly/SameSite=Strict one-year random browser cookie (Secure on HTTPS) supplies the ownership boundary; SQLite stores only its SHA-256 owner reference. IDs alone grant no access. Cross-origin browser mutations are rejected. This is an **anonymous local/demo session boundary**, not account authentication, cross-device access or verified production multi-user security. Losing cookies loses access; account recovery is absent.
- `EVENTRA_DB_PATH` defaults to `<project>/data/eventra.sqlite3`. Startup safely initializes schema version 1; subsequent startups preserve records. Unknown versions or nonempty unversioned databases are rejected without overwriting them. No automatic downgrade or destructive migration exists. Keep the database/browser profile private and back up before future migrations.
- The existing Cloud Run target is not a durable SQLite deployment. When `K_SERVICE` is present, workspace storage fails closed with 503 without creating an ephemeral database; legacy generation still works. Single-instance containers must mount writable durable storage. Docker creates `/srv/data` for its unprivileged user; runtime/volume behavior was inspected but not verified with Docker. A shared production database remains a future deployment task.

### UI and compatibility

The existing form and tabs remain. A saved-events toolbar supports list/open/new/rename/confirmed delete; loading, empty, success, conflict and error states are visible. Save and build saves preferences and generation atomically; checklist changes and conversations are also persisted. The selected ID is a browser pointer, not the source of event data. Failed saves keep form edits or restore checkbox state. Unsaved details are not erased by progress/chat saves.

`Import browser draft` is explicit and retains all old localStorage keys; invalid/unmatched progress is rejected before creating a row. The real-browser test verifies import does not happen automatically, original browser data remains and an existing saved event is unchanged. Old local key collisions cannot be reconstructed with certainty; no old chat was persisted by the original application and it cannot be recovered. Historical events remain readable/renameable/progress-saveable/chattable, while regeneration still needs a valid current/future event date. Generated day counts/health/narrative remain saved snapshots until rebuilt; the UI shows the generation timestamp.

### New API operations

| Operation | Contract / behavior |
| --- | --- |
| `POST /api/events` | Validated `details`, optional explicit `legacy_progress`; server generates and saves the complete workspace, 201 only after commit. |
| `GET /api/events` | Current anonymous session's saved-event summaries. |
| `GET /api/events/{id}` | Actual persisted complete workspace, not a regenerated substitute. |
| `PATCH /api/events/{id}` | Expected `revision` plus exactly one of `details`, `title`, or `progress`. Full details rebuild/save together; rename alone retains the existing generated narrative snapshot. |
| `POST /api/events/{id}/regenerate` | Expected revision; save the generated result before success. |
| `POST /api/events/{id}/chat` | Expected revision and bounded question; persist both question and answer before returning the workspace. |
| `GET /api/events/{id}/ics` | Export the saved timeline, including historical snapshots. |
| `DELETE /api/events/{id}` | Expected revision and matching `confirm_id`; 204 after atomic permanent deletion of the whole document, including child/history/chat state. No archive/undo yet. |

All new routes inherit the unchanged actual-byte 20,000-byte boundary and security/no-store headers. Requests send small operations, never the growing complete workspace; response snapshots may exceed 20KB and are gzip-compatible. Original API schemas remain unchanged.

### Acceptance evidence and commands actually executed

| Requested acceptance | Evidence |
| --- | --- |
| 1–4: create/list/retrieve/reconnect/save generated results | `tests/test_workspaces.py`: complete round trips, fresh repository/application connections, saved regenerated AI/offline snapshots. Browser test closes browser and restarts a real Uvicorn process using the same temporary DB/profile. |
| 5–6: isolate events; reject invalid input without partial writes | Two-event tests, invalid UUID/progress/details/operations, session isolation, stable child identity, invalid type change and revision conflicts. Browser test changes one event without affecting another. |
| 7: deletion integrity | Confirmation ID/revision required; stale/foreign deletion denied; whole document removed, unrelated event preserved. Browser tests cancellation and confirmed deletion. |
| 8–9: calculations and old APIs | All original 172 cases retained; rebuilt totals, vendor links and timeline bounds checked. No engine/AI/schema replacement. |
| 10: failure handling | Injected create/save/chat storage failures and actual SQLite abort trigger; 503 with no persisted partial changes/history. Browser blocks a save request and confirms edits remain while stored state is unchanged. |
| 11: initialization/migration | Temporary clean/idempotent initialization, rejection of future schema/unversioned existing data, corruption errors and unavailable directory without destroying data. |
| 12: body limit/headers | Original 45 body-boundary cases retained; additional `/api/events` streamed over-limit case and security/no-store assertions. |

| Command | Actual result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest tests/test_ai_and_api.py tests/test_request_limits.py --tb=short` | 76 passed during initial backend integration. |
| `.\.venv\Scripts\python -m pytest tests/test_workspaces.py --tb=short` | Initial 36 workspace cases passed; a subsequent Cloud Run fail-closed case brings workspace cases to 37. |
| `.\.venv\Scripts\ruff format app/workspace_models.py app/workspaces.py app/storage.py app/main.py tests/conftest.py` | Formatting applied to new/changed Python files; additional targeted format passes covered `tests/test_workspaces.py`. |
| `.\.venv\Scripts\python -m pytest tests/test_workspaces.py tests/test_request_limits.py --tb=short` | **82 passed**, one existing deprecation warning, 2.69s. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` | Final **209 passed**, one existing Starlette/HTTPX warning, 7.15s; **97.12%** combined statement/branch coverage. Storage/workspace service/models each report 100% in this run. A prior 209-case run took 2.96s; the intermediate pre-deployment-guard run was 208 passed/97.11%. |
| `.\.venv\Scripts\ruff check .` | All checks passed. |
| `.\.venv\Scripts\ruff format --check .` | 22 files already formatted (tool output). |
| `node --check static/app.js` and `node --check tests/browser_workspace_smoke.mjs` | Passed. |
| `node tests/browser_workspace_smoke.mjs .venv/Scripts/python.exe` | Final run **passed all four stages**: create/progress/chat/rename/refresh; second-event isolation/rebuild/failed-save/confirmed deletion; complete browser and Uvicorn process restart; explicit legacy import preserving old browser data. |

The browser runner uses only Node built-ins, a temporary DB/profile and a local Uvicorn subprocess, with keys disabled. Initial restricted-process/CDP attempts were unavailable; an initial accessible run submitted before deferred JS finished loading. The harness was corrected to wait for application readiness and use finite connection/CDP timeouts. The final passing run used Windows Edge 155 with local network/process access outside the restricted sandbox. No hosted browser, Docker/cloud or live Gemini success is claimed.

### Exact changed files and remaining gaps

New: `app/storage.py`, `app/workspace_models.py`, `app/workspaces.py`, `tests/test_workspaces.py`, `tests/browser_workspace_smoke.mjs`.

Modified: `app/main.py`, `tests/conftest.py` (temporary DB isolation), `static/index.html`, `static/app.js`, `static/style.css`, `.env.example`, `.gitignore`, `.dockerignore`, `Dockerfile`, `README.md`, `docs/UPGRADE_PLAN.md`, `docs/UPGRADE_AUDIT.md`.

Remaining: account authentication/recovery, shared production database, Docker/hosted durability verification, archive/undo, automatic backup/migrations beyond v1, expense editing, custom task/vendor/quote workflows, isolated scenarios, Rescue/approval, full AI workspace grounding and live credential validation. Proxy trust/limiter cleanup remain open. No next implementation stage was started.

## Verified roadmap status and dependencies

The labels are literal: **implemented and verified**, **partially implemented**, **missing**, and **not verified**. Future acceptance criteria are requirements to satisfy, not evidence of existing functionality. The detailed product register and actual probe results are in [UPGRADE_AUDIT.md](UPGRADE_AUDIT.md#requirement-status-register).

| Roadmap item | Status | Evidence / unsatisfied requirements | Dependencies before completion |
| --- | --- | --- | --- |
| 1. Theme-fallback repair | Implemented and verified | `req.theme[:62]` preserves composed title validity; 37 added cases cover boundaries/Unicode/event types and API fallback/success. No schema/calculation change. | Complete; retain regression suite. |
| 2. Actual body-size cap and consistent headers | Implemented and verified | New bounded ASGI request middleware counts actual chunks before routing; early 413/429 and disconnect errors retain security/no-store headers. 45 focused regressions pass alongside all 127 prior cases. R2 and early-rejection R5 repaired. | Complete; details, command results and scope limits below. |
| 3. Proxy trust and bounded limiter | Implemented and verified in supported raw-peer configuration | Stage 4 explicit default-empty IP/CIDR trust, strict canonical chain parsing, no-proxy launcher, locked expiry/capacity, safe 429 admission and positive configuration. Unit/API/real-Uvicorn tests pass. | Deployment-specific trusted ingress topology must still be verified; no distributed quota or hosted readiness claim. |
| 4. AI trust/context and request consistency | Partially implemented | R6 is repaired with SDK-role/stub-transport, strict output and adversarial tests. Saved advice/interpretation retain canonical context/enum/approval boundaries. Some intake validation, provider concurrency/coalescing and remote transport remain open. | Preserve R6 tests; align remaining validation, bound provider concurrency/costs and separately verify configured live behavior. |
| 5. Persistent workspaces | Implemented and verified for local/single-instance demo | SQLite repository, stable IDs, anonymous session scoping, full save/open/list/update/delete, explicit import, revisions/history and real browser/server restart verified. Archive, accounts and automatic recovery are not implemented. | Shared production database and hosted/container durability remain unverified; see completed stage above. |
| 6. Editable budgets/expenses | Implemented and verified | Stage 3 CRUD, strict Decimal inputs, all lifecycle amounts, derived reconciliation/warnings, manual allocation policy, atomic revisions, retry safety and browser/server restart. No refunds/FX/payment processor or automatic balancing. | Complete within BUDGET_RULES; preserve tests and backup before v2 migration. |
| 7. Saved timeline and vendor operations | Partially implemented | Stable IDs/completion and saved export persist. Linked expense quotes/commitments/payments and date/cancellation previews now work. Custom task/dependency editors, vendor contact/shortlist/booking UI, payment-due ledger and stable calendar UIDs remain missing. | Existing workspace/Guardian/scenario services; explicit operational deadline and timezone policies for further edits. |
| 8. Isolated scenarios | Implemented and verified | Six types, pure simulation, saved comparison, feasibility reasons, explicit apply/discard, stale-revision/day rejection, transactional rollback/retry/history and API/browser isolation tests. | Complete for the six Stage 3 commands, conditional on recorded constraints. Arbitrary combined/priority scenarios are outside this stage. |
| 9. Event Rescue Mode | Missing | Scenario approval/rejection/atomic application primitives exist and are verified; automated risk-to-rescue-proposal workflow and reversal/undo do not. Health/warnings alone are not Rescue. | Reuse items 5–8 and define risk policy, rescue proposal generation, review and reversal as a separately approved slice. |
| 10. Planora identity/accessibility/release | Partially implemented | Existing semantic UI, static checks, CI and Docker configuration are present. Planora branding, reproducible lock/dependency setup, browser/container CI, migration UX and hosted persistence are missing. Browser accessibility, remote CI, container runtime and cloud/live Gemini release evidence not verified. | Working product slices; usable browser/container runner, hosted storage and configured provider; preserve existing API/local data compatibility. |

Additional verification requirements within those items:

| Requirement | Status | Current boundary / acceptance still needed |
| --- | --- | --- |
| Original generation APIs, deterministic engine rules and offline fallback preserved | Implemented and verified | All 209 pre-Stage-3 cases remain in the 280-pass run; legacy generation engine/routes/schemas/AI adapter were preserved. |
| Numeric consistency after changing total/guests/date and regenerating | Implemented and verified | Current 60,000→123,457 INR / 30→67 guest / 45→12 day probes satisfy totals, vendor links, per-guest rounding and date bounds; ICS contains revised dates. This is not persistent-edit consistency. |
| Consistency after expense/allocation edits and save/reopen | Implemented and verified | One Decimal service feeds API/UI/advice/scenarios; category totals/shares/per-guest/vendor allowances follow saved allocations. Browser/server restart retains actual records and summaries. Arbitrary custom task edits remain outside scope. |
| Browser draft import/checklist save/restore | Implemented and verified | Browser smoke explicitly imports legacy values without deleting them; saved progress survives reopen/restart. Ambiguous old identity collisions cannot be repaired automatically. |
| Gemini request/parse/success and failures through injected client | Implemented and verified | FakeLLM tests cover plan/chat success, exceptions, malformed/thin output and fallback; numbers remain engine-owned. This does not authenticate a provider. |
| Missing-key default behavior | Implemented and verified | Neither key is set; `default_client()` returns None and current in-process API probes return offline plans without provider calls. |
| Real valid Gemini credentials/model success and actual authorization/network failures | Not verified | Neither supported key is set. Before claiming live readiness, run opt-in plan/chat smoke calls with externally configured valid credentials, record source=gemini and numeric invariants, then confirm graceful credential/provider failure without exposing keys. Fake 401/timeout tests alone do not establish live behavior. |
| SDK adapter/real timeout handling | Not verified | SDK config shape was accepted; suite does not execute real adapter transport. Stub transport tests and optional live timeout behavior remain needed. |
| Budget/timeline/vendor manual operations | Partially implemented | Expense/allocation/lifecycle payment edits, saved completion, date previews and cancellation are implemented with ownership checks. Custom task and full vendor-management editors/payment-due workflows remain missing. |
| Scenario fork/compare/save/apply/discard/revision rejection | Implemented and verified | Stage 3 pure engine, persisted preview APIs/UI, explicit approval, expiry/revision/ownership checks, rollback and idempotent application. |
| Rescue detect/propose/preview/approve/reject/apply/rollback/history/undo | Missing | Every operation requires item 9; verify no mutation before approval, exact approved diff, atomicity, retries and stale-revision rejection. |
| Workspace contract fields, access control, revisions, migrations, recovery and legacy import | Partially implemented | Schema v2 and transactional v1 migration, anonymous owner boundary, revisions, import/restart and corruption rollback are verified. Account recovery, automatic backups and shared production storage remain missing. |
| Calendar generation/API | Implemented and verified | Structure/escaping/folding/API tests and saved timeline export; live calendar import/stable UID behavior remains a gap. |
| Browser download/calendar import, print/mobile/keyboard/screen-reader usability | Not verified | Real browser workspace/Guardian/scenario workflows pass, but do not establish all download/print/responsive/assistive-technology behavior. |
| Local startup; local suite/lint/format | Implemented and verified | Prior Uvicorn real HTTP checks and recorded post-fix commands below; source preserved. |
| Docker build/non-root runtime, remote CI and durable deployed save/redeploy | Not verified | Configuration exists; no Docker/cloud/remote-CI execution. Local restart durability is verified, but Cloud Run workspace storage remains deliberately disabled. |

### Earlier audit-only validation and evidence reuse (historical)

Recorded post-fix commands on the current code were `.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` (**127 passed, one Starlette/HTTPX deprecation warning, 95.28%**), `.venv\Scripts\ruff check .` (**all checks passed**) and `.venv\Scripts\ruff format --check .` (**16 files already formatted**, as reported by the tool). The previous full run completed in 0.63 seconds.

This follow-up did not rerun or change tests/lint/format unnecessarily. It re-read `.coverage` using `.venv\Scripts\python -m coverage report` and the coverage API (95.28%); checked 127 cached node IDs, no cached failures, and coverage timestamps newer than application/tests; and inspected actual source against the completed fix. The recorded command output, not the cache alone, establishes the passing result. A before/after hash comparison of all 26 non-document source/static/configuration/license files verifies that this documentation update preserved them. No source, tests, schemas, dependencies or deployment files were changed.

## Guardrails

- Extend the existing FastAPI/Pydantic/Python engine/plain-JavaScript application. No rewrite, frontend framework migration, replacement calculation engine, or speculative integration.
- Preserve existing routes, request/response fields, five event types, four currencies, exact integer totals, priority weighting, contingency policy, compression rules, offline planning, checklist progress, chat, print, ICS, and passing tests except where a demonstrated defect requires a documented correction.
- Keep computed numbers and validated mutations outside Gemini. Model output is advisory content or a proposal, never an implicit approval.
- Make each change independently reviewable. Add targeted regressions for real risks, run the existing suite and CI checks, and document contract changes.
- Do not silently turn localStorage into database state or introduce unauthenticated saved-event endpoints. Account/session ownership and hosted storage choices must be settled as part of the workspace slice.

## Prioritized roadmap

This table retains the original sequencing with current scope corrections. Completed status/evidence is in the register above; Rescue and remaining release work are future acceptance criteria, not implemented behavior.

| Order | Deliverable | Likely affected files | Exit criteria / meaningful acceptance checks |
| --- | --- | --- | --- |
| 1 — P0 | Repair fallback for accepted theme lengths (exact task below) | `app/engine.py`, `tests/test_engine.py`, `tests/test_ai_and_api.py` | Valid 80-character themes return complete plans with no client or failed client; all existing calculation tests pass. |
| 2 — P0 | Enforce real request-body limits and preserve response headers | `app/main.py`, `tests/test_ai_and_api.py`; a small middleware module only if it improves isolation | Count actual body bytes, including missing Content-Length/chunked delivery; over-limit requests return 413 before parsing/AI. Rejection/success responses retain security and no-store headers. Normal JSON/ICS/gzip remain compatible. Test real ASGI chunk sequences, not only TestClient's aggregated body. |
| 3 — P0, completed Stage 4 | Correct proxy trust and bound limiter state | `app/main.py`, `app/proxy.py`, `app/rate_limits.py`, `.env.example`, README, Docker/browser launcher and `tests/test_security.py` | Direct spoofing denied, explicit trusted chains resolve correctly, malformed data conservatively aggregates, expiry/concurrency/capacity/config tests pass and full existing product suite remains green. See Stage 4 for deployment limits. |
| 4 — P1 | Tighten AI trust/context and request consistency | `app/ai.py`, `app/models.py`, `static/app.js`, engine/API tests; browser test setup | User-controlled priority text cannot create trusted prompt tags. Sanitized empty questions rejected. Integer/date validation matches API. Full relevant verified budget/timeline/vendor context reaches chat. Old replies cannot appear in a new plan. SDK shape, invalid output, timeout, and offline paths covered. Coalesce duplicate in-flight generation without caching failures. |
| 5 — P1 | Persistent event workspace vertical slice | Add `app/workspaces.py`, `app/storage.py`, migrations and persistence tests; extend `app/models.py`, `app/main.py`, `app/service.py`, `static/*`, requirements/config/docs as needed | Create/list/open/save/archive an owned workspace with stable IDs and revision. Reload and server restart retain state; another owner cannot read/write it; stale revision writes return conflict. Storage failures are visible. Existing generation API still works. Import legacy intake/progress explicitly with schema checks; ambiguous collisions are not silently merged. |
| 6 — P1, completed Stage 3 | Editable and consistent budget workspace | Budget models/service/API, workspace/storage integration, `static/*`, API/browser tests | Strict Decimal expense stages, whole-unit manual allocations, one derived summary and current advice, atomic revisioned writes, browser/server restart. Explicit no-auto-balancing policy permits warned incomplete/overallocated editing states; invalid inputs never partially save. |
| 7 — P1 | Saved timeline and vendor operations | Workspace models/service/storage, targeted `app/engine.py` helpers, `static/*`, persistence/API/browser tests | Tasks retain stable IDs through edits/reordering; completion survives reload. Vendor records support names/contact, shortlist/booked status, quotes and payment due information. Vendor category references are valid; quoted/paid amounts stay separate from planned allowances. Date changes preview rescheduling effects. Calendar exports use current saved tasks and stable IDs. Resolve venue milestone/book-by semantics with explicit regression coverage. |
| 8 — P1, completed Stage 3 scope | What-if scenarios | `app/scenarios.py` plus additive schemas/routes/storage/UI/tests | Six Stage 3 types, pure isolated calculation, saved stable previews and before/after effects, conditional feasibility, explicit approval/rejection, stale-base/day checks, transaction/idempotency/history. Priority changes, arbitrary composition and custom scenario naming remain outside the selected scope. |
| 9 — P1 | Approval-based Event Rescue Mode | Add `app/rescue.py` plus proposal schemas/storage/routes/UI/tests; reuse scenario validation | Detect declared risks from workspace state; show reasoned proposed edits and before/after effects. Pending/rejected proposals mutate nothing. Explicit approval atomically applies only the displayed validated change set to the matching revision. Repeated approval is idempotent; changed workspace requires a new preview and approval. Record history and offer reversal as a new revision. No external contact, booking, payment or messages. |
| 10 — P2, before final demo | Planora identity, accessibility, release validation | `static/*`, prompt/metadata strings in `app/*`, README/config/CI/Docker/dependency files and focused browser checks | Planora AI displayed consistently; existing storage imported through a migration, not abandoned. Browser smoke for create/edit/save/reopen/scenario/approve/reject plus keyboard tabs, labels, focus, mobile overflow, print and ICS download. Dependency baseline reproducible, CI green, container starts non-root, hosted persistence survives a redeploy, live Gemini demo has an offline failure path. |

Orders 2–4 should be small fixes, not one large refactor. Budget/timeline/vendor work depends on the workspace contract. Scenario and Rescue share the same validated calculation and change-application path. Display rebranding can be scheduled earlier after approval, but must not substitute for these product capabilities.

## Original proposed workspace contract (implemented subset described above)

Keep generation models intact and add a separate envelope for saved state:

- `EventWorkspace`: stable event ID, owner/session reference, schema version, monotonically increasing revision, created/updated timestamps, original `PlanRequest`, generated baseline and AI provenance, and editable operational state.
- Budget allocations keyed by existing category keys. Store whole currency units; derive shares/per-guest/vendor allowances centrally. Store quotes/payments separately so planned allocation is not confused with spending.
- Timeline tasks and vendor checklist items with durable IDs, not array positions. Store completion, custom deadlines and notes without mutating global templates.
- Scenarios reference an event and baseline revision with isolated overrides and a computed comparison.
- Rescue proposals reference event/revision, risk evidence, explicit change operations, previewed effects, status, and approval/application history.

The original proposed save-only-when-balanced policy was superseded by the Stage 3 explicit manual-allocation policy: valid nonnegative whole-unit edits can be saved while unallocated/overallocated amounts remain visible warnings. No rebalance/lock control was added and no other line silently changes. Scenario approval rejects known allocation/category/reserve violations. Manual allocations survive later rebuilds; total/guest/date scenarios show consequences before explicit application. See BUDGET_RULES for the implemented contract.

Generated defaults and user overrides need separate representation so regeneration cannot discard edits. Saved historical event data must remain readable after the event passes; do not reuse the current future-only creation validator as a universal persistence loader. Browser-local and server dates must have an explicit event/workspace timezone policy before overdue/rescue behavior is added.

## Storage and security decisions for the workspace slice

The current implementation chooses a protected anonymous browser session for the local/single-instance demo, with ownership checks on read/mutation and cross-origin mutation rejection. Event IDs alone are not authorization. Account sign-in/recovery and a production security review remain future work.

Use a small repository boundary so engine/AI code does not depend on database queries. SQLite is suitable for local single-instance development, but the existing Cloud Run instructions need a durable shared database choice for hosted workspaces. Include migrations, transaction/revision checks, deployment credentials, backup/recovery, and an explicit data deletion path in that slice. Do not add several database backends preemptively.

Implemented legacy import validates shapes and known template indices, is explicitly confirmed, and keeps the original local keys even after success. Title/date/type collisions cannot be inferred reliably and remain a manual-recovery limitation. No automatic index reassignment or deletion occurs.

## Scenario and approval invariants

Items 1–5 are implemented and tested for Stage 3. Item 6 is a future Rescue/undo requirement; undo is not implemented. Item 7 bounds future Rescue scope.

1. Preview generation is read-only. Baseline totals, tasks, vendor state and revision remain unchanged.
2. Every suggested operation is schema-validated and recalculated by Python; narrative cannot establish numeric truth or confer approval.
3. Approval is an explicit user action tied to a stored proposal and exact base revision. Reject/cancel/no approval means no mutation.
4. Apply validates ownership and revision inside the transaction, writes all changes together, increments revision once, and records the applied operations.
5. Repeated approval cannot apply changes twice; partial failures roll back. Baseline changes invalidate old previews.
6. Undo creates a new validated revision; it does not erase history or overwrite later changes silently.
7. Rescue has no automatic vendor outreach, contract signing, payment, email, or external side effects in this scope.

## Verification policy

For each approved slice, run existing tests, Ruff lint/format checks and the configured >=90% Python coverage gate. Preserve the 90 existing cases rather than replacing them to make new behavior pass. Add tests that demonstrate the actual defect or domain invariant; coverage percentage alone is insufficient.

Add browser tests when implementing workspace interactions, covering persistence, synchronized budget/vendor values, stale responses, keyboard navigation and approval behavior. Add repository integration tests for ownership, restart durability, transaction rollback and revision conflicts. Exercise the actual Gemini adapter with a stubbed SDK transport; use an explicitly configured live smoke check for the final demo, never a required network-dependent unit test. Verify a container separately because this audit could not run Docker.

## Exact first implementation task — completed

The owner's `continue` instruction approved this task. The boundary regression first reproduced the existing failure at a 63-character theme. The fix reserves space for the surrounding title text and quotes, displaying up to 62 theme characters while retaining all 80 in the request and Gemini prompt. Only `app/engine.py` and the two test files listed below changed in application/test code.

Verification: **127 tests passed**, including all 90 original cases and 37 new parameterized cases; **95.28% combined statement/branch coverage**; Ruff lint and format checks passed. The existing Starlette/HTTPX deprecation warning remains. No live Gemini call was needed or made.

**Task:** Fix offline theme-idea title construction so every currently accepted 0–80-character theme can generate a schema-valid complete plan, including when Gemini fails.

**Demonstrated defect:** A valid 80-character theme reaches `fallback_extras()` in `app/engine.py`. The title `Style it around '<theme>'` exceeds `Idea.title`'s existing maximum of 80. Both offline generation and Gemini failure then return HTTP 500 instead of a complete fallback plan.

**Implementation boundary:** Bound the composed title to the existing response limit, keeping the current wording unchanged whenever it fits. Preserve the full theme in `PlanRequest` and Gemini context. Do not lower the request maximum, relax `Idea.title`, alter budget/timeline/vendor/health calculations, or change response fields.

**Affected files:**

- `app/engine.py` — adjust only fallback theme-idea title construction.
- `tests/test_engine.py` — regression coverage for composed-title boundaries and unchanged normal output.
- `tests/test_ai_and_api.py` — endpoint regressions for no-client and failed/malformed-AI fallback.

**Acceptance tests:**

1. Across all five event types, a maximum-length ASCII or Unicode theme yields valid `AIExtras` with no title over 80 characters; test the exact fit boundary and first overrun as well as 80 characters.
2. A normal short theme preserves the existing title `Style it around 'Jurassic'`; empty theme preserves current behavior with no added theme idea.
3. `POST /api/plan` with a valid 80-character theme and no LLM returns 200, `ai_source=offline`, a nonempty summary/tips/ideas, timeline/vendors, and exact budget-line total.
4. The same request returns 200 and a valid offline plan when the LLM raises a timeout or supplies malformed/thin JSON. A valid Gemini success path remains unchanged.
5. Generated numeric core for the same request remains equal to `engine.compute(req)`; full theme remains accepted by `PlanRequest` and available to the prompt.
6. All existing 90 tests still pass, new regressions pass, coverage remains >=90%, and Ruff lint/format checks pass.

**Historical approval boundary:** The owner approved this first task and the later request-body task separately; both completed. Workspace and Stage 3 expense/scenario work were subsequently authorized and completed as recorded above. Rescue remains unimplemented.

## Request-body security task — completed

**Task:** Enforce the existing **20,000-byte API request-body limit on actual received bytes**, including bodies without Content-Length, and attach the existing common security/no-store headers to early rejections. This addresses reproduced R2 and the directly adjacent R5 rejection-path gap; it is a bounded reliability/security repair, not a feature redesign.

**Why first:** A 25,268-byte streamed JSON body bypassed the advertised cap and returned 200. The existing test covers only an oversized declared Content-Length. The current code remains unchanged in this area. Fixing that boundary protects current parsing/AI endpoints before adding saved state or larger competition traffic. Proxy trust and limiter cleanup remain the subsequent P0 tasks, not part of this change.

**Actual affected files:** `app/main.py` (registration, safe declared-length check, common response-header helper); new `app/request_limits.py` (bounded ASGI receive/replay and shared protected-path predicate); new `tests/test_request_limits.py` (raw ASGI boundary/regression tests); this document and `docs/UPGRADE_AUDIT.md`. The raw-chunk tests use a separate focused module instead of extending the already large AI/API test module. No existing tests, schemas, dependency files, engine, AI adapter or frontend files changed.

**Dependencies:** Existing `MAX_BODY_BYTES`, `SECURITY_HEADERS`, rate limiter and ASGI/FastAPI request path. Existing Python/HTTPX test dependencies suffice; no database, credentials, frontend migration or new product feature is required. Implement against actual ASGI receive chunks so TestClient's aggregated content cannot give false confidence.

**Acceptance criteria:**

1. Valid JSON API bodies at/below 20,000 received bytes retain existing behavior; a 20,001-byte body returns 413. Test bytes, including multibyte UTF-8, not character count.
2. Over-limit declared-length bodies and missing-Content-Length multi-chunk bodies both return the same safe 413 error. Reading stops as soon as the cap is exceeded; no unbounded accumulation and no downstream handler/AI call. An oversized malformed JSON body returns 413 before semantic validation.
3. Under-limit streamed bodies remain readable exactly once by normal request parsing. Real ASGI `http.request` sequences with `more_body` true/false cover a boundary crossed in a later chunk; disconnects do not hang the request or become successful plans.
4. Existing security headers and API `Cache-Control: no-store` appear on ordinary 200/422 and early 413/429 responses; 429 retains `Retry-After`. Error bodies do not expose user input. Preserve current protected-route scope and gzip/ICS behavior.
5. Valid `/api/plan`, `/api/chat`, `/api/ics`, root/static and health checks remain compatible. All existing **127 tests**, new focused regressions, Ruff lint/format checks and the >=90% coverage gate pass; no tests are weakened or replaced.

### Implementation and verified behavior

The middleware order remains outer FastAPI server-error handling, then **existing guard → request-body boundary → existing gzip → exception/router handling**. The guard retains the existing protected-path rules and checks declared lengths/rate limits before body reading. Both early guard rejections use the same `secure_response()` header helper as normal responses. The body boundary is inside the guard, so its 413/400 responses receive the same headers automatically; it is outside gzip, matching the previous guard's uncompressed early-rejection behavior.

`RequestBodyLimitMiddleware` counts actual bytes and retains at most 20,000 body bytes in its accumulator. It checks chunk length before copying, rejects the first over-limit chunk and never drains the unread tail or invokes the downstream app on an oversized body. A received chunk may itself be larger than the limit because ASGI servers choose chunk sizes; the middleware does not copy that chunk into its buffer. A complete allowed body is replayed once through an ASGI receive function for existing request parsing, without touching private Starlette request attributes. The replay adds only a bounded copy of the allowed body.

Content-Length is an optional conservative fast rejection, never the enforcement authority. Decimal values are compared as strings after whitespace/leading-zero normalization, avoiding huge-integer conversion errors; all duplicate values are checked. Malformed/non-ASCII/negative values are ignored as length assertions while actual byte enforcement remains active. Transfer-Encoding is not parsed here: the ASGI server supplies decoded request chunks. These tests exercise contradictory/malformed headers directly at ASGI level; they do not claim an HTTP server will accept invalid wire framing.

An `http.disconnect` before the complete body returns the existing FastAPI-compatible 400 parsing error without processing a partial plan. Valid multi-chunk plan/chat/ICS requests, exact byte boundaries including UTF-8, unprotected root/static/health/docs routes, gzip, validation errors, rate rejection/Retry-After, and the application's existing no-CORS preflight behavior passed. There is no new CORS policy. This task does not change the separate outer 500 exception-handler path or claim new 500-header coverage.

### Commands actually executed and results

| Command | Actual result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest tests/test_request_limits.py --maxfail=1 --tb=short` before the fix | Reproduced the bug: **1 failed, 2 passed**; actual 20,001-byte body without Content-Length returned 200 rather than 413. |
| `.\.venv\Scripts\python -m pytest tests/test_request_limits.py --tb=short` during implementation | First run: 43 passed, 2 failed because the new helper call omitted the chat/ICS path argument. Corrected that test harness routing; no production/API regression was hidden. |
| `.\.venv\Scripts\ruff format app/main.py app/request_limits.py tests/test_request_limits.py` | 2 files reformatted, 1 unchanged. |
| `.\.venv\Scripts\ruff check app/main.py app/request_limits.py tests/test_request_limits.py` | All checks passed. |
| `.\.venv\Scripts\python -m pytest tests/test_request_limits.py --tb=short` after correction | **45 passed**, one pre-existing Starlette/HTTPX deprecation warning, 0.65s. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` | **172 passed**, same warning, 0.89s; **95.37%** combined statement/branch coverage. New request-limit module rounded coverage 96%; main module 94%. All 127 prior cases preserved. |
| `.\.venv\Scripts\ruff check .` | All checks passed. |
| `.\.venv\Scripts\ruff format --check .` | 18 files already formatted, as reported by the tool. |

No new dependencies, test suppressions or limit changes. No live Gemini, browser, container or cloud verification was added or claimed. Future roadmap item 3 (proxy trust and bounded limiter state) remains open; it was not implemented as part of this isolated task.
