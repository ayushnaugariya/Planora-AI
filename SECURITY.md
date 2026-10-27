# Security and responsible disclosure

## Reporting

Do not post credentials, cookies, user databases or exploit details in public issues. If the eventual GitHub repository has private vulnerability reporting enabled, use **Security ? Report a vulnerability**. No private maintainer email or repository URL has been provided; request a private reporting channel from the maintainer before sending sensitive material. This document does not promise response times or a supported-version policy.

## Existing boundaries

- Saved events are scoped by an HttpOnly, SameSite=Strict anonymous cookie (Secure over HTTPS); only an owner hash reaches SQLite. Event UUIDs alone are not authorization. There are no accounts, recovery or cross-device access.
- Mutations retain origin checks, current revision validation and strict request schemas. Scenario application requires current owner/event/revision/day, feasibility, explicit approval and transactional revalidation. Replay cannot apply twice.
- Actual received body chunks are bounded at 20,000 bytes. Early errors retain security headers. Workspace responses are no-store; static assets revalidate. CSP, frame denial and nosniff remain unchanged.
- Forwarded headers are ignored unless the socket peer matches explicit `TRUSTED_PROXY_CIDRS`. Keep Uvicorn `--no-proxy-headers`; do not trust wildcards or enable legacy `TRUST_PROXY`. An ingress must overwrite forwarding headers and prevent bypass. Hosted ingress behavior is not certified.
- The locked sliding-window limiter expires idle clients and bounds state; at capacity it rejects new clients rather than disabling quotas. Quotas/cache are per process, reset at restart and multiply with workers/replicas.
- Shared bounded AI transport separates instructions from user-role data, validates structured output/allowed values, rejects exact active prompt/key echoes and falls back offline. User text is not executable authority. Prompt injection/narrative correctness are not completely solved.
- Supported quote analysis accepts bounded labeled text rather than arbitrary document execution. Review is required before recording costs. Readiness analysis writes nothing; optional AI orders only validated server actions.

## Public release hygiene

Real credentials belong only in private environment configuration. `.env.example` contains empty keys; `.env`, runtime SQLite, browser profiles/logs, screenshots and backup archives are ignored. Ignoring a file does not untrack it or erase history. The release audit detects ignored-but-tracked files and obvious credential patterns but is not a comprehensive secret/PII/history/dependency scanner. Review its JSON manifest and staged content manually.

If a credential has been shared or committed, rotate/revoke it at its issuer. Removing a working-tree file does not undo exposure. Review all branches/tags/history before publication; do not rewrite an existing published history without explicit approval. Never paste a secret value into audit reports or issues.

The product currently requires durable single-instance SQLite and TLS outside localhost. Serverless ephemeral persistence, multi-instance quotas, production account security and independent supplier/contract verification are not implemented. See [deployment requirements](docs/DEPLOYMENT.md). Dependency consistency tests are not vulnerability scans; use a separately verified advisory scanner before a production release.
