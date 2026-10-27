# Planora AI motion refinement

## Baseline and implementation plan

The uploaded motion brief and two reference images guide this continuation. The airy vaulted venue informs architectural ribbing, floral depth and ivory/gold light; the budget reference informs tactile surfaces and a clear allocation chart. Reference customer figures/branding are not copied into the product. Existing CSS 3D, editorial typography, actual demo/scenario/Rescue workflows and backend remain.

Inspection found short entrance animations, one-shot section reveals, bounded desktop pointer response and static reduced-motion fallback already implemented. Missing pieces: idle layered movement, independent invitation/floral motion, a user pause control, deliberate data/Rescue transitions and tests at 1024/320px. Native CSS animation and existing IntersectionObserver/rAF suffice; no library/framework or backend changes are needed.

Fresh Python baseline: **496 passed, 2 warnings, 35.91s / 99.04%** using `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90`. Git metadata is absent; `.planora-motion-baseline-20261026T131447Z.zip` preserves 116 source files before edits, excluding secrets/runtime SQLite/artifacts. A fresh browser baseline passed all 11 existing checkpoint groups after the reload fixture correction described below. Its 22 screenshots are preserved in `.artifacts/motion-refinement/before/` before feature changes.

1. Preserve all original scene transforms inside independent depth/ambient wrappers. Add subtle CSS idle movement, bounded pointer interpolation/lighting and invitation tilt, with pause/resume, viewport/visibility shutdown and static reduced-motion/touch modes. Add local reference-inspired vaulted detailing; no external runtime assets.
2. Refine entrances, scroll/list reveals, navigation/buttons, demo allocation chart and actual example-value transitions. Preserve all authoritative money strings and use only server-provided allocation shares for visual geometry. Add clear demo recovery compare/review/discard/simulated-approval transitions; actual Rescue success still waits for the existing backend response.
3. Add focused real-browser checks for idle movement/independent transforms/pause/hidden/offscreen, 1440/1024/768/390/320 layouts, touch/reduced motion, error state retention and original workspace/approval/restart regressions. Save before/after screenshots and a short CDP frame sequence recording under `.artifacts/motion-refinement/`. Run full coverage/lint/format/JS/exact-cent checks and document actual results.

Inspiration consulted: [Codrops Image Tilt Effect](https://tympanus.net/codrops/2015/05/28/image-tilt-effect/) and its primary demo describe independently moving depth layers; [Awwwards Studio Ouam hover typography](https://www.awwwards.com/inspiration/studio-ouam-various-hover-text-animation) is a motion reference. Awwwards homepage/category retrieval timed out; no unseen live interaction is claimed. No code, photography, external fonts or libraries were copied from these sources.

## Delivered implementation

The existing architectural hero and all its original material/position transforms are retained. Six enhancement wrappers independently move paper, primary flowers, background flowers, glass and two petals. CSS supplies slow 9–18 second movements with small amplitudes; a named-duration/easing system supplies entry, stagger, hover/press, tab, expand, comparison, loading and confirmed-state feedback. No new framework, library, WebGL renderer or application render loop was introduced.

Pointer input is clamped to small angles/offsets, coalesced into one pending frame, and interpolated by CSS transitions. Bounds are cached until resize/scroll/reset, rather than repeatedly querying layout for every pointer update. The invitation gets its own small tilt and lighting follows the same bounded coordinates. Touch pointer events cannot drive parallax. Compact/coarse/limited-core devices use only slower invitation/budget movement. Save-Data/reduced-motion preferences reduce the scene further. Offscreen/hidden states pause every ongoing decorative CSS animation and cancel pending pointer work. Reduced motion removes ambient movement entirely. The visible pause control persists only a boolean preference in browser storage, reserves layout space in static HTML, and cannot override the user's reduced-motion preference. Without JavaScript, the original scene/content remain and ambient enhancement never starts.

The supplied venue reference is reflected in a local, original vaulted lattice inside the nested arch, subtle contact shadows and separated floral/paper planes. The budget reference informs the calculated fictional allocation ring and its material palette. None of its customer names, guest counts, amounts or percentage figures were copied as product data. The ring uses server-provided category percentages and the server's planned-allocation amount; it is explicitly **planned allocation**, not paid spending. Bars now use actual server share percentages rather than a visually doubled scale. Final currency strings still use the unchanged exact-cent formatter.

Example counters interpolate only bounded fictional display values, cancel superseded/disconnected work, finish immediately when reduced/hidden, and end at the exact supplied string. They retain the previous actual demo total when revisiting the budget; a proposed recovery display starts at the original server snapshot and ends at the proposed snapshot. Real workspace totals remain direct server-derived displays, not browser financial calculations.

The existing demo now reveals its disruption/options/review/resolution states with coordinated finite transitions, exposes unchanged recorded commitments/trade-offs and supports explicit demo discard. It remains prominently fictional and cannot write an event. Existing actual Rescue retains the same backend pipeline: success styling is set only for the confirmed `Scenario applied and saved.` event, not loading, input edits or a failed request. The browser deliberately blocks a real apply request, verifies error feedback and unchanged saved event/options, then lets the original approved transaction succeed. No success animation substitutes for a server response.

## Actual verification

All commands ran from `D:\Projects\eventra` using the existing venv and Node/Edge infrastructure. Browser tests use their own temporary server, DB and profile; the pre-existing local development server/data were not reset or replaced.

| Command executed | Actual result |
| --- | --- |
| `git status --short` | No Git metadata. Source-only baseline archive created before edits. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` (baseline) | 496 passed, 2 warnings, 35.91s; 99.04%. |
| `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe` (baseline with reload barrier) | All 11 existing checkpoint groups passed; fresh before screenshots copied. |
| Complete Python coverage command above (final application) | **496 passed, 2 warnings, 21.11s; 99.04% combined statement/branch coverage**. Original 90% floor unchanged. No backend/Python test file changed. |
| `.\.venv\Scripts\python -m ruff check app tests scripts` | Passed. |
| `.\.venv\Scripts\python -m ruff format --check app tests scripts` | 69 files already formatted. |
| `Get-ChildItem frontend -Recurse -Filter *.js \| ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw "JavaScript syntax failed: $($_.FullName)" } }` | All 16 frontend scripts passed. |
| `Get-ChildItem tests/browser -Filter *.mjs \| ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw "Browser script syntax failed: $($_.FullName)" } }` | All 5 browser/formatter scripts passed. |
| `node tests/browser/test_money_display.mjs` | Passed all unchanged large-total/negative-fraction/null/explicit-currency expectations. |
| `.\.venv\Scripts\python -m scripts.check_structure` | 44 modules, acyclic imports, original HTTP contracts retained. |
| `.\.venv\Scripts\python -m compileall -q app` | Passed. |
| `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe` (final application) | **All 13 checkpoint groups passed, zero runtime exceptions** in the isolated browser. Includes all original expense/workspace/scenario/Rescue/stale/approval/retry/browser/server-restart assertions, previous cinematic/language checks, and the two new motion/failure-feedback groups. |
| Local `Invoke-WebRequest http://127.0.0.1:8000/` verification | HTTP 200; the updated static motion control is present. Existing local app is still running. |

Failures were investigated. The first pre-change browser run raced a reload and waited for the blocked-demo error in the wrong lifecycle state; a fresh-document `performance.timeOrigin` barrier plus explicit scroll restoration repaired that fixture without removing its fallback assertions. A later isolated-profile Edge run exposed errors from an injected `chrome-extension://...` content script. The owned browser runner now uses `--disable-extensions`; no runtime-error filtering was added, and its original zero-error assertion remains. Diagnostics were expanded. Subsequent baseline/final workflows passed. These failures are recorded instead of claiming every intermediate attempt passed.

## Screenshot, recording and layout findings

All new artifacts are ignored runtime verification files under `.artifacts/motion-refinement/`:

- `before/`: 22 fresh baseline product/cinematic screenshots.
- `after/homepage-{1440,1024,768,390,320}.png` and `after/scene-{1440,1024,768,390,320}.png`.
- `after/reduced-motion.png`, `after/budget-allocation.png`, `after/recovery-review.png`.
- `layout-observations.json`: buffered browser LayoutShift observations on fresh local loads. **CLS 0 / zero observed entries at all five tested widths**. No horizontal page overflow was observed. The assertion remains below 0.1, not disabled; the actual measured values were all zero. This is local load evidence, not a general performance certification.
- `recording-frames/frame-00.png` through `frame-11.png`, `recording.json` and `recording.html`: 12 **actual browser captures** spanning 2,844 ms, with a local play/pause/frame-scrub viewer. This is a short frame-sequence recording, not an encoded MP4/WebM or an FPS benchmark. Open `recording.html` locally; no application endpoint or deployed inline script was added for the viewer.

Desktop and narrow 320px scene/allocation screenshots were opened for visual review; tablet/mobile and reduced-motion captures remain available alongside the full product screenshots. Idle movement was verified from changing computed independent transforms with no pointer input; pause was verified by unchanged transforms across time and persisted reload state. Hidden behavior was tested through a simulated `document.hidden` visibility event and offscreen behavior through real scrolling; touch used CDP touch input, and reduced motion used actual emulated CSS media. This does not claim testing every OS background-tab scheduling behavior or device.

The primary CTA stays an ordinary working link with the original wizard handler and no dependency on motion completion. No scroll hijacking, cursor replacement, external fonts/photos, endless JavaScript renderer, or oversized backdrop filter was introduced. Continuous decoration has a pause control; keyboard labels/focus and existing navigation remain. Formal assistive-technology auditing, mobile battery/thermal load, production Core Web Vitals and multi-browser FPS were not measured.

## File inventory and preserved scope

Created: `frontend/assets/venue-lattice.svg`, `frontend/styles/motion-refinement.css`, `tests/browser/motion_refinement_smoke.mjs`, `docs/MOTION_REFINEMENT.md`.

Modified: `frontend/index.html`, `frontend/style.css`, `frontend/modules/cinematic.js`, `frontend/modules/demo.js`, `frontend/modules/motion.js`, `tests/browser/browser_workspace_smoke.mjs`, `tests/browser/cinematic_smoke.mjs`, `tests/browser/planora_product_smoke.mjs`, `README.md`, `docs/CINEMATIC_BUILD.md`, `docs/PLANORA_BUILD.md`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md`.

No original file was deleted or moved. All `app/` files, all baseline Python tests, original contracts, DB schema/migrations, dependency and Docker files remain byte-identical to the archive. API contracts, stored workspaces, ownership, exact arithmetic, six scenarios, approval/stale/transaction/retry guarantees, prompt boundaries, provider attribution, fallback, actual body cap, proxy trust, bounded rate limiting and security/no-store headers remain. No real event was created or modified by the landing demonstration.

Launch and data configuration are unchanged: `.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers`; default `<project>/data/eventra.sqlite3` or configured `EVENTRA_DB_PATH`. No runtime DB was deleted, reset, relocated or overwritten. SQLite remains durable-single-instance only; cookie loss has no recovery and quotas are per process. Live Gemini, hosted deployment/CI/ingress and Docker were not exercised for this presentation-only stage. Two existing dependency deprecations remain unsuppressed; broader prompt injection protection and competition placement are not guaranteed.
