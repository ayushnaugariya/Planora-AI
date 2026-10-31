# Deployment requirements and limits

The existing FastAPI entry point is `app.main:app`; HTML/ES modules/CSS are served directly from `frontend/`. No Node production process, npm dependencies, bundler or frontend build is required. Python runtime dependencies remain in `requirements.txt`; their version ranges are unchanged. The optional exact CI snapshot targets Windows/CPython 3.14.2, not a universal production lockfile.

## Durable saved-event deployment

Use one application instance/worker and a durable, writable SQLite file. The default is `<project>/data/eventra.sqlite3`; set an absolute `EVENTRA_DB_PATH` outside local development. The default is anchored to the project, while explicit relative paths use the launch working directory. Keep the same database and ownership cookie across restarts. Host bind mounts must permit the container user to write the directory and SQLite journal files.

Start locally with `python -m uvicorn app.main:app --reload --no-proxy-headers`. A single-instance deployment omits reload, binds to its intended interface/port and retains `--no-proxy-headers`. Configure TLS at a verified ingress and restrict direct backend access. No production hosting or multi-user readiness certification is claimed.

Startup transactionally migrates supported v1 data to workspace schema 2; unsupported/malformed data fails without reset. Preferred concepts have an additive lazy versioned table; readiness is derived with no new storage. Back up before upgrades using SQLite's backup API, or stop the application before copying the file. Restore only while stopped and preserve the browser cookie. There is no downgrade, automatic backup, account recovery or shared-database migration tool. Never remove a database to make startup appear successful.

## Existing Docker image

`Dockerfile` copies the backend/frontend, creates `/srv/data` for its unprivileged user, and starts Uvicorn with `${PORT:-8080}` and `--no-proxy-headers`. The runtime image does not include tests, development artifacts or keys. These are prospective local commands; the Docker CLI is unavailable in the recorded environment, so build, volume ownership and runtime persistence are **not verified**:

```sh
docker build -t planora-ai .
docker volume create planora-data
docker run --rm -p 8080:8080 -v planora-data:/srv/data planora-ai
```

Without durable storage, container replacement loses the database. A named volume is an example, not a backup or multi-instance solution. Test file ownership, backup/restore and actual replacement persistence in the target environment. Do not embed credentials or inject them into image layers. Runtime manifests currently use ranges; Docker dependency resolution is not hash-locked/reproduced by this cleanup.

## Proxy and rate-limit configuration

Empty `TRUSTED_PROXY_CIDRS` trusts only the socket peer; arbitrary client forwarding headers cannot select a quota identity. Explicit canonical proxy IPs/CIDRs must match a verified network topology. Wildcard/universal trust and legacy `TRUST_PROXY=1` fail. Uvicorn must preserve the socket peer. Trusted ingress must overwrite, not blindly append, forwarding metadata; strip untrusted headers and prevent bypass. Preserve Host/protocol correctly for origin/cookie checks. No Cloud Run address ranges or forwarded-header order is assumed.

Defaults: 30 requests / 60 seconds / 10,000 clients. Bounds: limit <=10,000, window <=86,400, clients <=100,000 and limit ? clients <=1,000,000. Idle entries expire; state saturation rejects new clients. Quotas/cache are process-local and reset at restart; multiple workers or replicas multiply the effective quota. They are not distributed abuse/DDoS protection.

## Cloud Run and Vercel

When Cloud Run sets `K_SERVICE`, saved-event SQLite APIs return 503 rather than promising durable saves on an ephemeral/multi-instance filesystem. Stateless planning/health can remain available, but the complete saved-workspace product cannot be claimed deployed there. Do not unset the guard to make unsupported saves appear functional.

Vercel bootstrap metadata now explicitly selects `app.main:app`, declares the same runtime dependencies in `pyproject.toml` as in `requirements.txt`, and keeps static files in the function with CDN promotion disabled so existing cache/security middleware still runs. This addresses dependency/entrypoint discovery; it does not add durable storage. The complete persistent Python/SQLite application still has no verified Vercel deployment. See [bootstrap diagnosis and verification](VERCEL_DIAGNOSIS.md). A future serverless/multi-instance architecture would need a separately approved durable shared database and migration, account/security design, distributed quotas and target-specific testing. A local SQLite file must not be treated as durable serverless storage.

## Release verification

Check startup/health/OpenAPI/static assets offline, ownership, exact ledger, database migration/failure behavior and browser/server restart using the existing temporary test harness. Live Gemini, Docker, hosted CI/ingress, performance/availability and provider billing have not been verified by local tests. The [release audit](GITHUB_RELEASE_AUDIT.md) lists exact executed checks and remaining risks.


## Published invitations (30 October 2026)

The Event Website feature adds `/e/<random-slug>` and separate `/api/public/websites/<slug>` data/RSVP routes on the same FastAPI origin. No new environment variable, package, CDN, frontend build or separate hosting process is required. Local URLs work only where the local server is reachable; external sharing requires a reachable canonical TLS host and the same durable SQLite deployment described above. The owner UI builds absolute links from its current origin; server-provided paths are relative. Verify proxy/Host/protocol handling before sharing real data. Do not use a temporary serverless SQLite file as durable publication/RSVP storage.

Publish only reviewed public fields. These are unlisted public links, not password protection. HTML/data/error responses are no-store; original CSP and quotas remain, including the new HTML path. Unpublish revokes server access immediately; visible public clients recheck every 15 seconds and on tab return, but printed/downloaded copies cannot be recalled. Public responses are unverified and need host review; global process-local IP quotas, party/roster/receipt caps and duplicate checks are not distributed spam or identity verification. No automatic email or invitation transport is present. Existing Cloud Run storage fail-closed policy is preserved. Production ingress/storage, hosted CI, Docker and live Gemini remain unverified. See [EVENT_WEBSITES.md](EVENT_WEBSITES.md) for schema, routes, setup and actual local execution evidence.
