# Planora AI repository cleanup and GitHub release audit

28 October 2026 (Asia/Calcutta). Scope: the existing working project, source-only candidate, local generated artifacts and release documentation. This is release preparation, not a product rewrite or publication. No Git metadata, branch, remote or commit history existed at inspection (`git status --short` reported not a Git repository). No real repository was initialized, staged, committed, pushed or force-pushed.

## Inspection and preservation

Read the original README, budget/scenario rules, implementation/audit/plan and intelligence/readiness/demo/refactor/security/deployment evidence. Inspected every source group, actual manifests, GitHub workflow, Docker settings, environment reads and asset references. The architecture already matches logical `app/{api,core,schemas,services,ai,db,repositories}` and modular `frontend/`, with tests split by concern. No source relocation or abstraction change was warranted. Entry point remains `app.main:app`; root/static/API contracts, existing launch paths, browser keys and default database path remain unchanged.

A recoverable source/config/documentation backup is `.planora-release-baseline-20261027T185142Z.zip` (178 files; timestamp is UTC). Generated caches were separately backed up in `.artifacts/release/cleanup-cache-backup.zip`. Both are private/ignored, not release assets. The complete cache manifest and safe deletion inventory are recorded locally and summarized in [deleted-file inventory](CLEANUP_DELETED_FILES.md). No user database, environment, source, fixture, screenshot evidence or archive was deleted to reduce the public candidate.

Preserved all application features: creation/intake, ownership, expense CRUD/exact-cent reconciliation, six isolated scenario types, approval/stale/day/atomic/retry checks, Rescue, supported quote analysis, saved designs, dependency delay analysis, readiness, offline fallback and cinematic/keyboard/reduced-motion controls. No application Python/frontend files, original tests, schemas/contracts, financial rules, middleware, migrations or deployment architecture were changed by this stage. All original dependency manifests and the existing MIT license (copyright 2026 Ayush) remain unchanged.

## Classification and cleanup decisions

| Group | Actual decision / reason |
| --- | --- |
| `app/`, `frontend/`, original tests/fixtures/evaluations | Keep; executable product, real regression tests, supported fixtures and required assets. Three local SVG assets and inline icons remain. No general screenshot/asset deletion rule. |
| `docs/` historical reports and plans | Keep; large audit/plan files contain migration/security/accounting and validation history. They are not current metrics; the README now points to dated evidence rather than repeating conflicting old counts. Local machine paths in historical evidence are retained for owner review, not required to run the app. |
| Existing runtime/development dependency manifests | Keep every dependency. FastAPI/Pydantic serve validation/API, Uvicorn launches the server, Google GenAI provides optional AI, pytest/HTTPX provide tests. Standard extras also support the documented explicit env-file launch. No unused dependency was demonstrated. |
| `.venv/` | Keep locally and ignore; removing it would unnecessarily break the current developer/test setup. Never include it in Git. |
| `data/`, SQLite/journals/backups | Keep private locally; ignored. No DB reset, replacement, dump publication or schema modification. |
| Existing source ZIP baselines | Preserve ignored recoverable backups; their contents are not certified for publication. Not moved/deleted. |
| `.artifacts/` screenshots, logs, temporary drivers/profiles | Preserve ignored local evidence; browser tests generate them. Their content can contain private context, so they are excluded wholesale from Git. No claim that all local artifacts are redundant. |
| Project `__pycache__`, `.pyc`, pytest/Ruff caches and `.coverage` | Recoverably remove generated files only after validation. A backed-up exact deletion list is provided; tests recreate them. Virtual-environment/package caches are excluded from cleanup. |
| Unknown-purpose files | Retain. No unexplained file, example, migration, demo case or attribution was deleted. |

Moved files: **none**; no import, API, template, static path or database-path changes were needed. Deleted product/source/test/documentation files: **none**. Only verified generated caches listed in the deletion inventory are removed.

## Release improvements

- README consolidated into actual features, supplied Challenge 5 statement, architecture/stack, optional AI and boundaries, Windows/standard Python setup, environment/persistence, testing/demo, deployment/security and MIT license. Stale headline counts and duplicative history are no longer presented as current verification. Detailed historical reports remain linked/preserved.
- `.gitignore` now also excludes additional caches/coverage outputs, build/Node outputs, machine/editor configuration, private credential/key files, database formats/journals, local backups/archives and logs/temp evidence. `.env.example` remains explicitly included. `.dockerignore` also excludes private keys, local machine/cache/database/backup context; the Dockerfile is unchanged. `.gitattributes` defines portable source line endings and binary handling; no existing files were mechanically reformatted.
- `.env.example` contains only empty credentials and safe defaults, including the actual Google alias, timeout and logging. It explains that `.env` is not implicitly loaded and that Cloud Run's guard must not be bypassed.
- Added `CONTRIBUTING.md`, `SECURITY.md`, [deployment notes](DEPLOYMENT.md), a [release checklist with exact owner-run publishing commands](GITHUB_RELEASE_CHECKLIST.md), and a reproducible release-candidate audit.
- `requirements-ci.txt` captures the exact **already installed** 44-package Windows/CPython 3.14.2 validation environment. It is not a universal cross-platform/hash-verified lockfile. Original runtime ranges remain; no package was upgraded/removed/installed by the no-index dry-run.
- Updated CI to the recorded Python 3.14.2/Node 25.9.0 Windows environment, read-only repository permission, no AI credentials, temporary DB, pinned installed requirements, Python/coverage/Ruff/JS/evaluations/exact-cent/browser-restart and release audit. Workflow YAML is checked locally; an actual hosted GitHub run remains unverified. Action version tags are not immutable commit-SHA pins.

## Actual Git inclusion and repository size

`scripts/audit_release.py` creates a disposable bare Git directory/index under ignored `.artifacts/release/`, points its worktree at this project, asks Git for candidate files respecting `.gitignore`, scans those files, then actually stages them in that disposable index and verifies membership. It measures raw candidate bytes, actual staged Git blob bytes via `cat-file`, and the disposable metadata/object footprint. It deletes only its own temporary index. The user's root repository/index/remotes are never changed. Git is required; no Git LFS or external service is used.

The conservative gate is raw source bytes plus disposable Git metadata under **10,000,000 bytes**, stricter than 10 MiB. All current candidate files are text (including SVG); binary candidates fail for manual review rather than being silently discarded. In an existing real Git repository, ignored-but-tracked files also fail the audit without being untracked automatically. Object-size statistics and shallow status are reported, but full historical secret contents are not scanned.

Initial measured working tree: **5,998 files / 152,669,303 bytes**, dominated by local `.venv` (Ruff executable 27,012,400 bytes, cryptography binary 9,897,472 bytes, Pydantic binary 5,549,056 bytes), private artifacts and backups. These are not release files. At that stage Git's candidate was **185 files / 1,457,865 raw bytes**, with 558,933 bytes of disposable Git metadata; about 2.02 MB combined. Final candidate/file/size findings are recorded after all documents and cleanup below. Actual tracked/history size is **not applicable**, not silently claimed zero: there is no real Git repository. A not-yet-created public GitHub repository's size/accessibility cannot be certified by local preparation.

The full reproducible, redacted manifest is `.artifacts/release/release-manifest.json`, generated by `python -m scripts.audit_release`. Largest candidate files are the retained upgrade plan/audit, engine, frontend entry and dated reports. No runtime SQLite, archives, browser screenshots/profiles, local environment or credentials enter the tested disposable index.

## Security audit summary

- Candidate checks include private key headers, recognizable Google/GitHub/AWS token formats, embedded URL credentials and long literal credential assignments. Output contains only file/line/category, never matched secret values. No obvious credential-pattern finding was detected in the initial/current candidate scans. This is not a comprehensive secret/PII/advisory/history scan or a certification of security.
- `.env` is absent at root inspection; `.env.example` has empty keys. Only environment-based optional Gemini credentials are used. No real secret was identified or removed, so no specific exposed credential is claimed to require rotation. If the owner discovers a past exposure, revoke/rotate it; ignoring/removing a file cannot erase history.
- Runtime database contents, ownership cookies, private profiles/logs and backups were intentionally not exported or published. The retained license name and synthetic fixture contacts are existing attribution/test material; historical local paths remain for owner review. Arbitrary future sensitive text may not match automated patterns.
- All current product security remains unchanged: actual body-chunk cap, headers/CSP, no-store, origin checks, explicit proxy trust, bounded concurrency-safe limiter, saved ownership, strict validation and explicit transactional approval. Anonymous ownership is not account recovery or production multi-user authentication.
- No Git history existed to inspect/rewrite. No claim of removing secrets from historical/public Git objects is made. Dependency consistency is checked; no external vulnerability/advisory scanner or live Gemini call was executed.

## Validation ledger

Fresh pre-cleanup command `.\.venv\Scripts\python -m pytest --cov --cov-report=term-missing --cov-fail-under=90`: **670 passed, 2 warnings, 51.50s; 98.78%**. All original tests and the coverage floor/exclusions are retained. Twelve new release tests verify real Git exclusion, private tracked-file rejection without modifying the actual index, no accidental real commit/remote, secret redaction/failure, private-path recognition and safe-template/binary-review behavior. Final targeted run: **12 passed, one existing warning** (the earlier 11-case stage also passed).

| Command actually executed | Actual result |
| --- | --- |
| `.\.venv\Scripts\python -B -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90` final | **682 passed, 2 warnings, 51.75s; 98.78%**. `COVERAGE_FILE` was explicitly set to `.artifacts/release/final.coverage` to retain evidence without recreating root caches. Earlier canonical runs passed 681 / 98.78% in 28.74s and 55.36s before the final fail-closed regression was added. App coverage scope and original 90% threshold remain unchanged. |
| `.\.venv\Scripts\python -B -m pytest -p no:cacheprovider tests/integration/test_release_audit.py -o addopts='' -q` | **12 passed**; includes actual disposable index and tracked-private-file protection. |
| `.\.venv\Scripts\python -m ruff check app tests scripts` | Passed. |
| `.\.venv\Scripts\python -m ruff format --check app tests scripts` | **98 files already formatted**. |
| `node --check` on every frontend/browser JS/MJS via PowerShell enumeration | **35 files passed: 23 frontend / 12 browser**. The combined discovery command later returned 1 only because `Get-Command docker` found no Docker CLI; syntax checks completed successfully. |
| `node tests/browser/test_money_display.mjs` / `node tests/browser/test_decision_metrics.mjs` | Exact-cent, large/negative/zero/delta/percentage assertions passed. |
| `.\.venv\Scripts\python -m scripts.evaluate_planning`, `scripts.evaluate_intelligence`, `scripts.evaluate_readiness` | **10/10 each (30 offline cases)**. No live-model accuracy score. |
| `.\.venv\Scripts\python -m scripts.check_structure` | **60 acyclic app modules; every original OpenAPI operation/component retained**. |
| `node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe` | **All 21 checkpoint groups passed, exit 0, zero runtime exceptions**. Includes complete workflows, approval, errors, original-event isolation, accessibility/responsiveness/reduced motion and multiple browser/server restarts. Ran outside sandbox because restricted CDP cannot initialize reliably. |
| `.\.venv\Scripts\python -m pip --disable-pip-version-check install --dry-run --no-index -r requirements-ci.txt` | All requirements already satisfied. No network index, install, upgrade or removal. |
| `.\.venv\Scripts\python -m pip check` | No broken requirements. Not a vulnerability scan. |
| Local YAML parsing/structure checks | Workflow parses, read-only permissions and empty credentials verified. No hosted execution claim. |
| `python -B -m scripts.audit_release` final | Disposable actual-index membership, private-path/token patterns, Git blob sizes and conservative size gate pass; final measurement summarized below. `-B` avoids recreating removed project bytecode. |

Python/browser logs and explicit exit-status files are retained privately in `.artifacts/release/`. The cache archive was CRC-checked before removing **173 generated files / 3,609,909 bytes across 16 cache/output targets**. Absolute/resolved target paths were checked within the project before native PowerShell deletion. All listed files were verified absent, and every local `data/` file was byte-identical before/after cache deletion. A final validation subprocess/development reload regenerated 60 already-listed bytecode paths; these were separately backed up/CRC-checked and removed again. The public deletion list counts distinct paths, not repeated cache instances. No fake success, removed assertion or hosted verification claim substitutes for execution.

## Final cleanup and release snapshot

- **188 public candidate files**, approximately **1.5 MB of source** (about 1.48 MB of actual staged Git blobs); approximately **2.1 MB including disposable Git objects/index metadata**, comfortably below the conservative decimal 10 MB gate. These rounded values remain valid after adding this measurement paragraph; exact regenerable bytes and hashes are in the ignored JSON manifest. This is evidence from Git's real disposable index, not a claim about a nonexistent public remote.
- Working-tree footprint remains approximately **150 MB** because the local environment, database, recoverable backups and browser evidence were intentionally retained privately. Reducing the local directory to 10 MB is neither necessary nor safe; those files are excluded from the public candidate.
- Automated candidate pattern/private-path checks pass with **no findings**. No ignored database, archive, screenshot, profile, environment or credential file is staged in the disposable index. Real tracked/history size remains not applicable because root Git is absent.
- Root `.git` is still absent, source/API/test-contract/financial/migration/security files are byte-identical to the recoverable baseline, original tests are unchanged, no project bytecode directories remain, and all local database files stayed byte-identical across cleanup. No source file or required asset was removed.
- The actual running server returned **200** for `/healthz`, `/api/openapi.json`, `/`, `/static/app.js`, `/static/style.css` and all three SVG assets. OpenAPI includes readiness; root/static assets still return `no-cache`, and OpenAPI retains `no-store`. The GET-only asset-upgrade smoke test passed all three cache/render/failure-fallback checks, zero runtime errors.
- New/updated public documentation links were checked against actual files. The native full browser suite's temporary databases verified offline startup, ownership, approvals, migrations/failure behavior, complete saved state, browser/server restarts and other-event isolation; the user database was not substituted with a fixture.

Modified existing files: `.dockerignore`, `.env.example`, `.gitignore`, `README.md`, `.github/workflows/ci.yml`.

Created public files: `.gitattributes`, `CONTRIBUTING.md`, `SECURITY.md`, `requirements-ci.txt`, `scripts/audit_release.py`, `tests/integration/test_release_audit.py`, `docs/DEPLOYMENT.md`, `docs/GITHUB_RELEASE_AUDIT.md`, `docs/GITHUB_RELEASE_CHECKLIST.md`, `docs/CLEANUP_DELETED_FILES.md`. Source paths moved: none. The complete generated-file deletion list is linked above; private archives/manifests/logs are not release files.

The release helper additionally refuses unreadable existing `.git` metadata instead of mistaking it for an absent repository, and refuses evidence-directory symlinks escaping the project. Its fixed executable/argument-only Git subprocess does not use a shell or network operation. These guards do not scan or rewrite an existing history.

## Remaining release/deployment limits

Full saved workspaces require durable writable **single-instance/worker SQLite** and the original browser cookie; no shared multi-instance database/account recovery exists. Default path is `<project>/data/eventra.sqlite3`; use an absolute durable path in deployment. Unsupported databases fail without reset. Cloud Run's `K_SERVICE` disables workspace APIs; Vercel is not configured or validated for this architecture. No misleading serverless config was added.

Docker CLI/build/runtime, hosted CI/ingress, live Gemini/availability/billing, formal accessibility certification and production security/performance remain unverified. Runtime dependency ranges and action tags retain resolution/supply-chain limitations; the CI snapshot is platform-specific and not a hash-locked universal dependency guarantee. Existing Starlette/HTTPX and google-genai deprecation warnings remain unsuppressed. The supplied challenge statement is documented, but actual public repository/video/submission eligibility must be verified by the owner. Nothing was committed, uploaded, pushed, published or submitted by this task.
