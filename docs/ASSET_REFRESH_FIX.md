# Cached frontend upgrade repair

27 October 2026. The user reported raw stacked story text and no animation on the actual running site. Prior isolated browser checks used fresh profiles and missed the warmed-cache upgrade path.

## Finding and repair

`/` revalidated its HTML, while `/static/style.css` and `/static/app.js` used stable URLs with no explicit Cache-Control. A browser could reuse older root assets alongside new markup. That produces exactly the reported failure mode: new chapter HTML with no new styles or mount function. The server had the files; verifying only HTTP 200 and fresh profiles was insufficient.

The entry stylesheet and module now have an explicit release query in `frontend/index.html`. This escapes already cached unversioned roots on an ordinary navigation. Static responses now include `Cache-Control: no-cache`, preserving ETag/304 revalidation and all existing security headers. API `no-store` is unchanged. Original static URLs remain usable and return the same source files.

The optional story starts hidden in HTML. Its module reveals it only after detecting the new stylesheet's readiness marker. If CSS or JavaScript fails, the rest of the homepage and primary planning action remain available without exposing raw storyboard text. Reduced-motion mode still shows the readable static sequence when the enhancement loads. **The optional sequence is now hidden without JavaScript**, superseding the earlier all-copy-visible fallback description.

No database, money, ownership, approval, API schema, provider or rate-limit logic changed. The one asset-path validation test now resolves URL paths with `urlsplit`, preserving its file-existence assertion for versioned HTML URLs.

## Reproduced and verified

`node tests/browser/asset_upgrade_smoke.mjs http://127.0.0.1:8000` uses an isolated real Edge profile and a local read-only proxy. It first serves older root assets with an actual one-day browser cache lifetime. Navigating to legacy unversioned markup reuses those cached responses (request count stays at two), reproducing missing story styling/initialization. Navigating to the repaired HTML recovers the correct background and enhanced scene **without clearing browser cache**.

The same script then visits the actual `127.0.0.1:8000` site directly, verifies the navy computed background, sticky viewport and different 3D transforms at two scroll positions, and saves `.artifacts/asset-upgrade/live-homepage-fixed.png`. It deliberately blocks the story stylesheet with cache disabled and confirms that the story stays hidden while the planning link remains visible. Restoration reloads the scene correctly. No event mutations are allowed by the proxy; the live check uses a separate anonymous browser profile and only read requests. No runtime exceptions occurred.

Artifacts: `.artifacts/asset-upgrade/reproduced-stale-assets.png` and `live-homepage-fixed.png`. The latter was opened for visual inspection. This is evidence from the running local site, not just a separately launched test application.

Commands executed:

- `.\.venv\Scripts\python -m pytest tests/integration/test_asset_refresh.py tests/integration/test_frontend.py tests/integration/test_planora_frontend.py tests/integration/test_structure.py -q`: **19 passed**.
- `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90`: **551 passed, 2 existing warnings, 35.32s; 99.10% combined coverage**.
- `.\.venv\Scripts\python -m ruff check app tests scripts`: passed.
- `.\.venv\Scripts\python -m ruff format --check app tests scripts`: 78 files already formatted.
- `node --check frontend/modules/scroll-story.js` and `node --check tests/browser/asset_upgrade_smoke.mjs`: passed.
- `node tests/browser/test_money_display.mjs` / `node tests/browser/test_decision_metrics.mjs`: passed unchanged.
- `.\.venv\Scripts\python -m scripts.check_structure`: passed, 48 modules and original contracts retained.
- The real-cache/live-site browser command above: all three checks passed, exit 0. Initial run left a locked temporary profile; the final runner waits for its owned browser shutdown and retries cleanup. It never touches the user's browser profile.
- `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe`: **exit 0; all 17 checkpoint groups passed**, including actual scroll transforms, preferences, planning/Rescue and browser/server restarts; zero runtime exceptions.
- Final syntax sweep checked all 21 frontend and 10 browser scripts successfully.

## File inventory and maintenance

Created: `tests/integration/test_asset_refresh.py`, `tests/browser/asset_upgrade_smoke.mjs`, `docs/ASSET_REFRESH_FIX.md`.

Changed: `app/core/security.py` (static cache headers only), `frontend/index.html` (versioned roots and hidden optional section), `frontend/modules/scroll-story.js` (style-readiness guard), `frontend/styles/scroll-story.css` (readiness marker), `tests/integration/test_planora_frontend.py` (query-aware asset resolution), `README.md`, `docs/SCROLL_EXPERIENCE.md`.

No file removed; no assertions suppressed. Root release versions should advance with future entrypoint changes; all dependencies now revalidate on subsequent requests. This is a small local release/cache repair, not an atomic hashed asset pipeline or production CDN certification. Live Gemini/Docker/hosted deployment remain unverified; existing two deprecation warnings remain. No user data was reset and no unrelated server/browser process was stopped.
