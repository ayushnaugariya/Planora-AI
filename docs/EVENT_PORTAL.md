# Planora Event Portal: independent WebGL landing chapter

28 October 2026 (Asia/Calcutta). This is an additive visual upgrade to the existing homepage, not a rewrite, studio redesign, separate demo page or backend change. The existing flower, petals, invitation, hero motion and previous scroll chapters remain unchanged.

## Inspection, placement and creative direction

The current frontend is static HTML/CSS and ES modules served by FastAPI, with CSS 3D hero/invitation layers and four existing scroll-story chapters. There is no React, npm build, WebGL library, model loader or animation dependency to extend. Flowers are in the original cinematic hero (`botanical-main` / `botanical-echo`, existing SVG/art layers); those source/style/assets are not edited.

The new section is between **Everything in its right place** (`#workflow`) and **Big-picture thinking. Beautifully clear details** (`#experience`), before the existing feature and Event Rescue sections. This creates an independent dark spatial chapter after the practical introduction, without replacing the floral first impression or existing product copy/navigation/CTAs.

The focal object is a nested optical portal: indexed toroidal/partial-ring meshes with distinct metallic and translucent shells, spatial separation and an actual perspective camera. An inner architectural pavilion and a dimensional milestone path assemble as the camera passes through. There are no new flowers, botanical shapes, spheres, particle fields, invitation centerpiece or floating dashboard cards.

## What scrolling does

The desktop section reserves 290 viewport heights (240 on compact widths) with a native sticky stage. Normal document scrolling drives one continuous clamped camera progress:

1. **Approach:** a monumental gold/silver/violet portal emerges against a directional atmospheric field. World geometry is visible through the aperture in a scattered state.
2. **Go beyond:** optical layers separate along Z and rotate within restrained bounds; the perspective camera moves toward and through the aperture. This is real mesh/camera movement, not a transformed image.
3. **Come together:** behind the portal, scattered beveled structural ribs settle into a coherent circular pavilion. A raised milestone path and connecting light bars join it. Copy changes to the new chapter's own harmony message; the existing page copy is untouched. Sticky layout releases into the original next section.

The camera moves from positive Z to negative Z, ending behind all portal layers and in front of the inner world. Cursor movement shifts the camera/light slightly on fine-pointer desktop devices; touch/compact devices use scroll only. Native chapter buttons jump to actual section positions, and the separate **Pause portal motion** control freezes the new renderer without modifying the original floral pause preference. Scrolling and the original creation/studio links remain available at every stage.

## Rendering and materials

**Libraries added: none.** Original native WebGL2/GLSL ES 3.0 code generates indexed torus/arc and rounded-box geometry. Vertex positions, normals, model/normal/view/perspective matrices and camera/light positions are real GPU inputs. The material shader combines GGX-style specular lighting, Fresnel/iridescent edge treatment, analytic environment softbox reflections and distance fog. The optical shell is alpha-composited after opaque geometry without writing depth. These are stylized environment/reflection/atmospheric approximations, not ray-traced reflections, a physical glass/refraction solver, volumetric simulation or a claim of photorealism.

The procedural environment background is secondary to the 3D geometry. No imported model, texture, external CDN, remote asset, tracking, AI call or event-data request is required. New artwork/shaders/geometry are original code; the static SVG is a clearly separate fallback, not the animated centerpiece.

## Resource and accessibility policy

- The lightweight controller mounts only this section; the renderer is dynamically imported near the section. Reduced motion, Save-Data and short viewports skip renderer import and context creation.
- Geometry uses shared buffers/VAOs. Compact devices use fewer ring segments/sides and architectural elements. Drawing resolution preserves aspect ratio and is bounded to approximately 1.1 million desktop / 0.5 million compact pixels, rather than unbounded DPR rendering.
- Rendering is input-driven: at most one pending animation frame for scroll/pointer/resize. There is no perpetual idle renderer or self-scheduling pointer loop. Hidden/offscreen scenes stop requesting frames; read-only buffers remain reusable until disposal.
- Resources/listeners/observers are cleaned up on genuine page exit. BFCache visibility restoration is handled. Media/data-saving preference changes release GPU buffers/programs and show static artwork. Paused state is stored under its own local key, with no workspace/storage-key changes.
- Initial WebGL failure uses static SVG with functional creation/continuation flow. Active context loss keeps the reserved stage height so the page does not collapse underneath the reader. Reduced-motion/fallback layouts remain readable and normal scrolling is never intercepted.
- Fixed stage sizing, intrinsic fallback image dimensions and a compositor-only reveal avoid animation-induced layout resizing. A CSS readiness marker keeps the optional section hidden if its stylesheet fails, preserving the primary page controls.
- Canvas is decorative/hidden from assistive technology; native section headings, explanatory copy, buttons, navigation and links carry meaning. Keyboard Enter, pause, chapter navigation, focus outlines and reduced motion are tested. No screen-reader/contrast certification or production FPS/Core Web Vitals/battery claim is made.

## Files

Created: `frontend/modules/event-portal.js` (lazy policy/controller), `frontend/modules/event-portal-renderer.js` (procedural meshes/materials/camera), `frontend/styles/event-portal.css`, `frontend/assets/event-portal.svg` (static fallback), `tests/browser/event_portal_smoke.mjs`, `tests/browser/test_event_portal_geometry.mjs`, and this report.

Modified: `frontend/index.html` (one new section plus root asset version), `frontend/app.js` (import/mount only), `frontend/style.css` (one scoped import), `tests/browser/planora_product_smoke.mjs` (additional assertions after original groups), `.github/workflows/ci.yml` (new geometry check), README and the current upgrade audit/plan links. No backend, schemas, dependencies, database files, financial rules, migrations, ownership, approval, CSP or original flower/invitation source/styles/assets changed.

## Executed validation

Fresh baseline command `python -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90` with a private artifact coverage file: **684 passed, 2 existing warnings, 41.79s; 98.78%**. Final same command: **684 passed, 2 warnings, 87.62s; 98.78%**. Original assertions and the 90% threshold remain unchanged. Runtime variation is not a performance result.

`python -B -m ruff check app tests scripts --no-cache` passed; format check reported **99 files already formatted**. `python -B -m scripts.check_structure` checked **60 acyclic application modules / unchanged original API contracts**. Both original Node exact-cent/delta checks passed. `node tests/browser/test_event_portal_geometry.mjs` passed mesh topology, valid 16-bit indices, unit normals, finite transforms, compact mesh budgets and clamped interpolation. Syntax checks passed on **39 frontend/browser scripts** (25 frontend JS / 14 browser MJS).

Dedicated real-browser software-WebGL test used the existing isolated Uvicorn/profile/database harness. Its test-only Chrome/Edge software renderer flags were supplied only to that temporary browser; no app/browser security policy was changed. It requires a real WebGL2 context and verifies distinct pixel output and visible lit geometry at four camera positions, positive-to-negative camera traversal, actual pointer response, bounded idle paint count, native Enter/pause/chapter controls, preserved height after context loss, five static widths, compact real-WebGL geometry/pixel budget and saved-event nonmutation. Separate injected initial-context refusal, reduced-motion/Save-Data no-import/no-context and actual blocked-stylesheet hiding checks passed. Driver/logs/screenshots are private under `.artifacts/event-portal/`.

An early software run exposed the cost of self-scheduling pointer smoothing, which was removed rather than increasing the original browser timeout. Camera framing/pixel bounds and transparent depth handling were corrected after actual screenshots. A new policy fixture initially read the old document after reload; it now waits for changed `performance.timeOrigin` and a completed new document, preserving every assertion. The complete browser run also exposed a reduced-motion-to-normal transition retaining the short static layout while the renderer loaded. The controller now restores the pending reserved layout immediately; the regression waits for the browser to deliver the media-change event before measuring the new layout and verifies resumed rendering. An initial full run timed out in an original mobile check; a sequential rerun passed that check, then exposed this transition defect. No original test was deleted, weakened or rewritten.

Final complete checked-in browser command passed all **22 checkpoint groups** (the original 21 plus the new portal), exited **0**, and recorded no runtime exceptions. It includes expense/scenario approval, original landing interactions, readiness/intelligence, isolation and browser/server restart persistence. The new portal rendered as WebGL in this full run, in addition to the separate required-software-WebGL/policy run. No frontend production build command exists in this no-bundler application: actual Uvicorn startup/HTTP assets, JS syntax, import/API contracts and browser rendering are the applicable runtime/build checks. Vercel deployment, hardware-specific performance, hosted CI and production-readiness certification remain unverified; existing SQLite deployment limits are unchanged.


### Exact validation commands and environment

Use the repository virtual environment: bare `python` on this machine resolves to Python 3.14 without Ruff (`No module named ruff`). That attempt failed; all successful Python validation uses `.venv/Scripts/python.exe` (the environment's `python` in the commands above).

```powershell
$env:COVERAGE_FILE = '.artifacts/event-portal/baseline.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
$env:COVERAGE_FILE = '.artifacts/event-portal/final.coverage'
.venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90
.venv/Scripts/python.exe -B -m ruff check app tests scripts --no-cache
.venv/Scripts/python.exe -B -m ruff format --check app tests scripts
.venv/Scripts/python.exe -B -m scripts.check_structure
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
node tests/browser/test_event_portal_geometry.mjs
$portalScripts = @(Get-ChildItem frontend -Recurse -Filter *.js) + @(Get-ChildItem tests/browser -Filter *.mjs)
foreach ($portalScript in $portalScripts) { node --check $portalScript.FullName }
node .artifacts/event-portal/portal-driver.mjs .venv/Scripts/python.exe
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe
node tests/browser/asset_upgrade_smoke.mjs http://127.0.0.1:8000
```

The ignored dedicated driver composes the checked-in portal tests with the original temporary-server/CDP harness and test-only software-WebGL flags. It is local execution evidence, not a new production dependency. Full browser verification uses the checked-in original driver. The two Python warnings are existing Starlette HTTPX TestClient and google-genai `_UnionGenericAlias` deprecations. Git reports CRLF-to-LF normalization warnings for modified text files; no database or secret is included.

The final cached-asset upgrade command also exited **0**: reproduced the stale warm-cache failure, confirmed versioned roots recover without clearing cache, verified computed styling/sticky transforms on the running homepage with zero runtime errors and no writes, and confirmed missing stylesheet keeps the optional story hidden with planning available. A direct GET of the running homepage returned **HTTP 200** and the new portal markup. Original homepage HTML (after removing only the addition/version token) and the recorded original floral/invitation source/style/asset hashes match the baseline.
