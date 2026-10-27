# Scroll-led homepage refinement

**Post-release correction:** the user's existing browser exposed a stale-root-asset upgrade defect missed by fresh-profile checks. [ASSET_REFRESH_FIX.md](ASSET_REFRESH_FIX.md) records the real-cache reproduction, versioned entrypoints/static revalidation repair and verification against the actual running site. The optional story now stays hidden if its styling/JavaScript fails, rather than exposing raw copy; the earlier no-JavaScript all-copy-visible description below is historical.

27 October 2026. The request was to give the homepage a premium scroll-animation experience. This extends the existing frontend rather than replacing the product, hero invitation or planning workflows.

## Delivered presentation

A full-width midnight/navy interlude follows the original ivory hero. Its native sticky viewport tells four chapters: **Imagine → Plan → Adapt → Approve**. Scrolling continuously rotates and raises the CSS 3D composition, separates its architectural planes and moves orbital details. The editorial text advances by chapter; chapter buttons also support native keyboard activation. Floating budget, guest and milestone values consume the existing explicitly fictional demo response. No financial figure is fabricated or calculated by this presentation module.

The original hero gains a separate shallow scroll-depth wrapper around its existing arrival/pointer/idle layers. Existing feature visuals use native CSS view timelines where supported, with their ordinary layout as fallback. A thin homepage reading-progress indicator follows actual page position. The existing ivory/navy/lavender/gold materials, typography, planning CTA and direct product access remain.

Scrolling is never intercepted: no wheel/touch cancellation, virtual scroll library, scroll snapping, forced auto-advance or perpetual animation loop. The module coalesces event bursts into one pending frame, reads geometry before applying transforms, updates the scene only while it intersects the viewport, cancels pending work when hidden and does not render workspace routes. No new dependency, WebGL renderer, backend route or asset download.

## Accessibility and responsive behavior

- Native chapter buttons expose `aria-current="step"` and `aria-controls`; only the active enhanced text chapter is visible. No continuously announced live region. Decorative artwork is `aria-hidden`.
- Shared **Pause motion** honors the existing stored scene preference and freezes scrubbed decorative transforms. Editorial view-timeline effects also stop; chapter content remains reachable. No synthetic input is required for ordinary scrolling.
- Reduced motion, Save-Data and viewports at most 650px tall get a non-pinned layout with all four chapters visible. Without JavaScript, the static HTML already contains all copy and a native onward link.
- Mobile uses a shorter 280svh journey instead of desktop 340svh, with a smaller vertical composition and reachable chapter/pause/onward controls. Native scrolling and the onward link allow users to leave the sequence directly.

## Actual verification

Baseline: the prior verified tree was 546 tests / 99.10% with all 16 browser groups. Git metadata is absent. `.planora-scroll-baseline-20261027T111252Z.zip` preserves 141 source/config/doc files before edits, excluding runtime databases, credentials and artifacts. Five previous verified homepage captures were copied into `.artifacts/scroll-experience/before/`; these are preserved prior captures, not a newly claimed pre-edit browser measurement.

| Command actually executed | Result |
| --- | --- |
| `.\.venv\Scripts\python -m pytest tests/integration/test_frontend.py tests/integration/test_planora_frontend.py tests/integration/test_structure.py -q` | 14 passed. |
| `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90` | **546 passed, 2 existing warnings, 43.96s; 99.10% combined statement/branch coverage**. No Python source/test change. |
| `.\.venv\Scripts\python -m ruff check app tests scripts` | Passed. |
| `.\.venv\Scripts\python -m ruff format --check app tests scripts` | 77 files already formatted. |
| `Get-ChildItem frontend -Recurse -Filter *.js \| ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw 'Frontend syntax error' } }` | All 21 scripts passed; final added module separately rechecked after its small policy extension. |
| `Get-ChildItem tests/browser -Filter *.mjs \| ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE -ne 0) { throw 'Browser syntax error' } }` | All 9 scripts passed; final added test separately rechecked after strengthening keyboard/media assertions. |
| `node tests/browser/test_money_display.mjs` / `node tests/browser/test_decision_metrics.mjs` | Exact currencies, large cents, signed/zero baselines and rounded deltas passed. |
| `.\.venv\Scripts\python -m scripts.check_structure` | Passed: 48 acyclic application modules; original contracts retained. |
| `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe` | **Final: exit 0, all 17 checkpoint groups passed, zero runtime exceptions.** Tests use their own temp DB/profile/Uvicorn process, not live event data. All prior 16 groups and every existing assertion retained. |
| `Invoke-WebRequest http://127.0.0.1:8000/ -UseBasicParsing` and `/static/modules/scroll-story.js` | Live HTML contains the new journey; module HTTP 200. Existing server remains running; no backend refresh or DB operation was needed. |

The first browser run completed original workspace/restart/cinematic/motion/invitation checks and all new four-chapter transform/pause/five-width checks, then hit a fixture timing race immediately after media emulation: CDP acknowledged before the new module's media-change callback ran. The test now waits for the actual static-mode signal before asserting it, retaining all assertions. Subsequent final run includes native Enter activation, shared pause/view-timeline shutdown, four distinct computed 3D transforms, sticky top positioning, 1440/1024/768/390/320 overflow/reachable controls, all-visible reduced/short-screen fallback and unchanged saved event list.

After captures: `.artifacts/scroll-experience/after/chapter-{1,2,3,4}-1440.png`, `chapter-adapt-{1024,768,390,320}.png`, `reduced-motion-320.png`. Desktop and mobile images were opened for review; mobile floating-card spacing was improved after the first review. Existing local layout observations remained **CLS 0 at all five widths**. This does not establish production Core Web Vitals, cross-browser/FPS/battery results or formal assistive-technology certification.

## File inventory and scope

Created: `frontend/modules/scroll-story.js`, `frontend/styles/scroll-story.css`, `tests/browser/scroll_story_smoke.mjs`, `docs/SCROLL_EXPERIENCE.md`.

Modified: `frontend/index.html`, `frontend/app.js`, `frontend/style.css`, `tests/browser/planora_product_smoke.mjs`, `README.md`, `docs/UPGRADE_AUDIT.md`, `docs/UPGRADE_PLAN.md`.

No file removed or moved. Backend/Python tests, APIs, exact calculations, provider boundaries, security, SQLite schema/path, original contract fixture and dependency files remain unchanged. Existing actual intake/expenses/scenarios/Rescue/approval/retry/restart workflows are retained. No sample was inserted into the live database by this visual change. Two existing Starlette/HTTPX and google-genai warnings remain unsuppressed; live Gemini, Docker and hosted ingress remain unverified. SQLite/cookie/per-process quota deployment limitations remain as documented.

Launch remains `.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers`. Refresh `http://127.0.0.1:8000/` and scroll past the hero to enter the new sequence.
