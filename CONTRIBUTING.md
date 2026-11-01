# Contributing

Contributions are welcome under the [Planora AI Source-Available License v1.0](LICENSE).
You may work locally and use a clearly attributed GitHub fork to submit a pull
request to this repository. You retain ownership of your own contributions and
grant the project the permissions described in the license when submitting them.
Do not submit code you lack permission to contribute. Direct pushes require
maintainer access; a fork or pull request does not grant that access. General
redistribution, commercial use and use in another product require separate written
permission. Existing third-party and earlier-version license rights remain intact.

Planora AI extends an existing Eventra application. Preserve working APIs, accounting, ownership and approval rather than replacing architecture for preference. Read [README](README.md), [budget rules](docs/BUDGET_RULES.md), [upgrade plan](docs/UPGRADE_PLAN.md) and the relevant dated report before changing behavior.

Use a virtual environment and the documented setup. The pinned `requirements-ci.txt` is the recorded Windows/CPython 3.14.2 validation environment; other platforms use the normal manifests and require their own checks. Never use a personal database or real vendor/user data in tests. Existing pytest and browser fixtures use temporary SQLite files and fake providers.

Before proposing changes, run full pytest/coverage (retain the existing 90% floor), Ruff lint/format, both Node exact-cent scripts, frontend/browser syntax checks, the three offline evaluations and `scripts.check_structure`. Run the real-browser suite for workflow, persistence, keyboard or layout changes. Exact commands are in the README. Explain commands not executed, provider/deployment assumptions and any remaining warnings.

Do not weaken tests or change financial rules merely to pass them. AI text is untrusted; use server schemas, deterministic calculations and the original explicit scenario approval/CAS transaction. New routes must retain ownership, no-store, bounded request and security protections. Add focused regression tests for demonstrated defects.

Keep `.env`, credentials, cookies, logs, profiles, runtime databases, archives and generated screenshots out of commits. Use synthetic reserved-domain contacts and clearly labeled fictional assumptions. Run `python -m scripts.audit_release` and inspect staged diffs before a public PR/release. Never publish test recordings containing private data. Report suspected security issues privately as described in [SECURITY.md](SECURITY.md).

A contribution should describe the concrete behavior, its reason, relevant checks and limitations. Preserve existing user changes and never reset/migrate a database destructively. License and attribution files must remain intact.
