# GitHub release checklist

Prepared 28 October 2026 (Asia/Calcutta). These are owner-run release steps, not actions performed by the cleanup. No Git repository/remote/commit existed in this workspace at inspection; nothing has been pushed or published. See [audit evidence](GITHUB_RELEASE_AUDIT.md).

## Before publishing

- [ ] Read the audit's actual local results and unresolved warnings. Hosted CI, Docker, live Gemini and target deployment are not certified.
- [ ] Retain a private backup of the real database and its ownership browser profile. Do not upload either.
- [ ] Run the README's complete test/lint/syntax/evaluation/browser commands in your release environment. Record actual failures/skips.
- [ ] Run `python -m scripts.audit_release` from the repository root. Review `.artifacts/release/release-manifest.json`: candidate paths, pattern findings, ignored-but-tracked files, raw/Git-blob bytes and temporary Git overhead. The script does not initialize or stage the real repository.
- [ ] Manually inspect staged source/config/fixtures/documentation for credentials, private links, personal details and real user data. Pattern matching cannot certify absence. Historical reports retain local paths and intentionally fictional examples; review them before publication.
- [ ] Check the existing MIT license/copyright and any rights/attribution for future imagery or contributions. No new license was invented.
- [ ] Confirm the eventual GitHub repository is public and below the competition's 10 MB requirement. The local candidate gate uses the stricter decimal 10,000,000-byte limit; it cannot certify a remote that does not exist yet.
- [ ] Verify any demo video is accessible and correctly labeled. Public repository/video URLs and the official submission rules are not supplied or verified by this cleanup.
- [ ] Do not claim verified vendor availability/prices, model accuracy, fully-ready events, production accounts/multi-instance persistence, awards or rankings.

## Commands for this workspace (Git currently absent)

First create an **empty public repository in your own GitHub account**, without an auto-created README/license/initial commit. Copy its exact HTTPS or SSH clone URL. Do not put a token/password in that URL. The following commands intentionally include an owner-run commit/push; the assistant has not executed them:

```powershell
# From the project root, after all local checks pass:
git init
git branch -M main
git add --all
git status --short
git diff --cached --stat
git diff --cached --check
git ls-files -ci --exclude-standard
# The last command must be empty. Review the full staged diff privately.
.\.venv\Scripts\python -m scripts.audit_release
# Only after you have inspected the actual staged content:
git commit -m "Prepare Planora AI for public release"
$releaseRemote = Read-Host 'Paste the exact clone URL of your empty GitHub repository'
git remote add origin $releaseRemote
git remote -v
git push -u origin main
```

If any check fails, stop and resolve it. Do not force-push, reset branches or overwrite an existing remote. A push failure is not authorization to rewrite a remote history. An existing nonempty remote needs a separate review/merge decision.

## If Git exists by the time you publish

Preserve its branches/remotes and inspect them before staging:

```powershell
git status --short
git remote -v
git log --oneline --max-count=10
git count-objects -vH
git ls-files -ci --exclude-standard
.\.venv\Scripts\python -m scripts.audit_release
```

Ignored files can already be tracked. If a private path is tracked, review it and explicitly remove **only that path from the index** with `git rm --cached -- <reviewed-path>`; keep the local file. This does not remove previous commits or revoke a credential. If secrets were exposed, revoke/rotate them and inspect every branch/tag/history. Large/secret published history may need a separately approved rewrite or a new clean repository; no history rewrite is authorized by this checklist.

## After the owner publishes

- [ ] Open the actual GitHub URL without authentication to confirm public accessibility.
- [ ] Inspect GitHub's reported repository size and clone/object size/history; adding commits or binaries can change the local pre-release measurement.
- [ ] Confirm GitHub Actions actually ran and passed. A workflow file alone is not a successful CI run.
- [ ] Inspect the remote tree: no `.env`, databases, cookies, browser recordings/profiles, cache, `.venv`, archives or local logs.
- [ ] Run a clean clone in a separate directory using a fresh virtual environment and a new database. Never overwrite the original local DB with demo data.
- [ ] Verify demo-video access and actual submission limits yourself. Publishing is not a competition submission; no attempt has been consumed here.
