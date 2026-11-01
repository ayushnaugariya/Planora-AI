# Final pre-submission code review

1 November 2026, Asia/Calcutta. Reviewed branch `main`, HEAD
`654e036d9d2dd7e6a54ed4b5c23f882bdbb57c16`, plus the existing uncommitted
optimization. Review only: application code, tests, existing documentation,
untracked images, index, branch history and remote settings were not changed.
This requested review report is the only added source/documentation file;
isolated verification evidence is under ignored `.artifacts/`.

## Executive Summary

**READY AFTER MINOR FIXES.** The optimization is focused, and the named-options
refactor preserves the existing guard behavior. Fresh verification passes
**910 Python tests, 98.34% coverage**, lint, formatting, JavaScript syntax,
original API/structure checks, startup and exact-cent checks. The wizard's new
keyboard/error behavior works, including a fresh Tab/Enter walkthrough through
every stage and saving a temporary event.

One reproducible accessibility issue remains: **saving a vendor after the first
vendor loses focus to the document body**. The renderer closes that vendor's
section on save, so the replacement opener cannot receive focus. The new smoke
test only edits the first vendor and therefore passes despite this defect.
The first-vendor save, Escape and Close cases pass separately.

There is no identified Critical or High defect in this diff and no reproduced
security, financial, ownership or database regression. Fix the later-vendor focus
case and cover it with a matching-opener assertion before the final commit.
No fix was applied by this review. The earlier optimization report's ready
recommendation is superseded by this review's more specific finding.

## Findings

### Critical

None identified within the reviewed diff and checks.

### High

None identified within the reviewed diff and checks. This does not establish
production readiness or replace the deployment limitations in `FINAL_AUDIT.md`.

### Medium

**M1 — Saving a later vendor still loses keyboard focus.**

- **Location:** `frontend/modules/coordination.js:8` (close handler, especially
  line 13), interacting with unchanged `frontend/modules/plan-views.js:140`.
- **Issue:** `applyWorkspace` rebuilds the vendor list before closing the dialog.
  `renderVendors` opens only the first `<details>` (`open: vi === 0`). For a later
  vendor, its replacement edit button is inside a closed section. The close
  handler finds that button, but calling `focus()` cannot restore focus to it.
  A nonempty `getClientRects()` is not a sufficient focusability check here.
- **Evidence:** an isolated Edge/Uvicorn comparison saved the first and second
  vendors. First: `focusedTag: BUTTON`, matching vendor UUID, `groupOpen: true`.
  Second: `focusedTag: BODY`, `focusedVendor: null`, `groupOpen: false`.
  The second button even reported `openerRects: 1`, yet focus was not restored.
  Both dialogs initially focused `vendor-dialog-close`. The vendor save itself
  succeeded; event details, budget summary and task completion were unchanged.
  Evidence: `.artifacts/pre-submission-review-browser.txt`.
- **Impact:** keyboard and screen-reader users lose their place after a common
  save operation. The advertised focus repair is incomplete. This was an
  existing focus problem that the optimization only partially fixes; it is not
  evidence of a new persistence or security regression.
- **Recommended action:** preserve the edited section's expansion through the
  render, or open the matching replacement section before focusing its edit
  button. Retain the guards for missing/disabled elements and reopened dialogs.
  Add a regression using at least the second vendor and compare focus with the
  UUID captured **before** opening/saving. Do not redesign the renderer.

### Low

**L1 — The vendor test can accept the wrong restoration target.**

- **Location:** `tests/browser/planora_product_smoke.mjs:85` and `:89`–`:90`.
- **Issue/evidence:** the test chooses the first `[data-vendor-id]`, then accepts
  any vendor button as the focused element after save. It records `editedVendor`
  from that resulting focus, rather than from the button used to open the dialog.
  A handler that always focuses the first vendor could pass. This also leaves
  M1's later-vendor case untested.
- **Impact:** passing tests overstate matching-opener coverage.
- **Recommended action:** capture the intended vendor UUID before the save and
  assert that exact UUID afterward; exercise a later expanded section. Keep the
  existing real Escape and Close checks. No test was modified in this review.

**L2 — The accessibility-tree assertion is broader than its message.**

- **Location:** `tests/browser/optimization_smoke.mjs:28`–`:31`.
- **Issue/evidence:** `tree.nodes.some(node => node.description?.value)` accepts
  any nonempty description in the partial accessibility tree. The response can
  include related nodes; this does not specifically prove that the invalid date
  field exposes the current error text. Earlier DOM assertions do correctly
  check that field's `aria-invalid` and its reference to the visible error.
- **Impact:** the additional accessibility-tree assertion could pass after a
  future regression in which only another related node has a description.
- **Recommended action:** identify the requested input's accessibility node and
  compare its description with the actual error text. This is a nonblocking
  test-strengthening suggestion; the current field association passed the
  browser check. It is not a claim that current screen-reader output is broken.

### Informational

**I1 — Passing counts do not establish complete interaction coverage.**

- **Location:** `docs/FINAL_EVALUATION_OPTIMIZATION.md`, Testing results and final
  recommendation; prior log `.artifacts/optimization-final-browser.txt`.
- **Evidence:** the prior log contains 32 `PASS` checkpoint lines. The current
  Python rerun independently confirms 910 tests and 98.34% coverage. M1 remains
  reproducible despite those results.
- **Impact/action:** retain the actual numbers, but qualify the vendor-focus
  claim and update the recommendation after an approved fix and rerun. No official
  AI evaluator was invoked; no score improvement is claimed.

## Code Quality Review

The reported list matches the actual optimization: **11 tracked modifications
plus two untracked additions = 13 files**. The seven existing images are separate.
After adding this requested review report, there are 14 intended changed/new
source, test and documentation files to consider for a later commit.

| Reviewed file | Review result |
| --- | --- |
| `README.md` | Changes only the current-report link; earlier report remains linked. |
| `docs/README.md` | Adds the optimization-report index entry and labels the earlier optimization as historical. |
| `docs/FINAL_EVALUATION_OPTIMIZATION.md` | Read in full; counts/size scope are explicit, but the vendor-focus and readiness conclusions need qualification by M1. |
| `frontend/app.js` | Named destructured options replace positional defaults. Guard body, comparison logic and no-argument default behavior are unchanged. |
| `frontend/modules/command-center.js` | Former fourth `true` maps correctly to `ignoreCommandDraft:true`. |
| `frontend/modules/coordination.js` | Small native-dialog close handler, no dependency or new state framework; incomplete later-vendor handling is M1. |
| `frontend/modules/guests.js` | Former second `true` maps correctly to `ignoreGuestDraft:true`. |
| `frontend/modules/negotiation.js` | Former third `true` maps correctly to `ignoreNegotiationDraft:true`. |
| `frontend/modules/quote-comparison.js` | Both former first-argument `true` calls map correctly to `ignoreQuoteDraft:true`. |
| `frontend/modules/website-editor.js` | Former fifth `true` maps correctly to `ignoreWebsiteDraft:true`; existing unpublish exception is preserved. |
| `frontend/modules/wizard.js` | Local navigation/error helpers remove actual duplication, preserve original descriptions, respect composition/cancellation, and retain native controls. No unrelated business logic changes. |
| `tests/browser/optimization_smoke.mjs` | New focused keyboard/error checks are useful; accessibility-tree assertion can be more specific (L2). |
| `tests/browser/planora_product_smoke.mjs` | Adds the new module and focus checks without removing or weakening existing assertions; matching-opener coverage has L1/M1 gaps. |

All six exclusion calls across five editor modules were checked. A repository-wide
search found no remaining positional boolean call to `hasUnsavedDetails`.
All other callers retain no-argument checks. The five defaults remain false;
expense, allocation, scenario, quote, guest, negotiation, command and website draft
guards retain their original meaning. Function injection into module factories
is unchanged. No API schema, response shape or persistent structure changed.

There is no unrelated file splitting, new dependency, broad formatting pass or
new abstraction. Existing error catches and `finally` cleanup remain in place.
M1 is the only reproduced application issue in the reviewed change area.

## Accessibility Review

**Wizard:** Enter interception now applies only to text-like inputs before review,
not Back/Continue buttons, selects, radio/checkbox controls or textareas. It respects
`isComposing` and prior cancellation. Native Back works; both directions focus a
visible `h2` with `tabIndex=-1`. Invalid controls receive `aria-invalid` and a
description pointing to the existing `role=alert` error. Correction clears stale
validation and restores any previous description. Native form labels remain.

The existing focused browser regression passed freshly. An additional in-memory
review check used Tab and native Enter through all five steps and saved a temporary
event successfully. `frontend/styles/tokens.css` retains the global 3px
`:focus-visible` outline; no focus style changed. The test's IME case is a synthetic
composing key event, not an OS-level input-method test. Live announcements were
checked structurally and through the browser accessibility tree, not with a human
screen-reader session.

**Vendor dialog:** remains a native labelled `<dialog>` opened with `showModal()`;
the heading, Close name and form labels are present. Opening focused Close in
the review checks. The existing focused first-vendor regression freshly passed
save, native Escape and Close restoration. Native modal document-inertness is
retained; no custom trap was added. Exhaustive browser-chrome/focus-cycle and
assistive-technology testing is not claimed. Saving a later vendor fails M1.

No complete WCAG audit or certification was performed.

## Test Review

The new tests provide meaningful coverage: native CDP Enter and Escape exercise
browser behavior, the Back assertion checks direction, the visible-heading
assertion checks focus, and invalid-date assertions check the specific input and
visible error. Correcting the date must clear invalid state. Existing application
tests were neither removed nor loosened, and no package was introduced.

The IDs used by the wizard are stable application IDs; the vendor UUID selector
is appropriate once the expected UUID is recorded independently. L1 demonstrates
how the first-vendor selector and post-save expectation can mask incorrect
behavior. L2 is a weaker additional assertion rather than a reason to discard
the otherwise useful wizard regression.

Tests use temporary databases/profiles, no live Gemini credentials, bounded waits
and a known Chrome/Edge CDP environment. Browser platform and event behavior still
matter; this is not a cross-browser/device certification. The prior full browser
log supports **32 checkpoint groups**, not 32 independent test cases. That full
screenshot-producing suite was not rerun in this review; focused existing checks
and an independent later-vendor reproduction were run instead, preserving prior
artifacts. Full Python verification was rerun with separate coverage/temp outputs.

## Security and Data Safety

No Python application, security policy, database, schema, financial service,
ownership dependency, public invitation renderer/transport, RSVP handler or
dependency manifest changed. The website editor's only change is its correctly
mapped unsaved-edit exclusion. Command Center task behavior is likewise unchanged.
The complete Python suite includes the existing security and isolation regressions.

A fresh pattern scan of all non-ignored text candidates found no credential or
private-path matches. `git ls-files -ci --exclude-standard` is empty: no ignored
file is tracked. This is a scoped pattern review, not a comprehensive secret/PII or
CVE certification. No new comprehensive history/advisory scan was run; the complete
existing branch-history bundle was verified read-only against current local refs.

The real database SHA-256 matches the original optimization value:
`61f08f210106b48c462cc4d9861cc45e054af9f2b71e17349e41da1a4ddd6ac6`.
All new test writes targeted isolated temporary databases. The vendor reproduction
also compared event details, budget summary and task state before/after, unchanged.
No real event was published, invitation sent or guest record altered.

## Repository Submission Review

Current branch is `main`; `main` and local `origin/main` point at `654e036`.
No fetch, staging, commit, push, reset, deletion of user files, history rewrite or
remote configuration change was performed. Git's CRLF-to-LF notices are consistent
with the existing `.gitattributes`; `git diff --check` exits 0.

GitHub's fresh connector response reports
[ayushnaugariya/Planora-AI](https://github.com/ayushnaugariya/Planora-AI) as
`private:false`, `visibility:public`, with server-reported `size:1241` KiB. This
metric differs from unpacked source/clone size. Signed-out access to the owner's
final pushed commit remains a final manual check.

Before adding this review report, the source was **4,036,911 bytes**, exactly the
previous report's value. All non-ignored files including seven existing images
were **5,875,997 bytes**. The existing history bundle is **1,207,718 bytes**;
`git bundle verify` passes and its two refs match current `main`/`origin/main`.
Thus the previous **5,244,629-byte source-plus-packed-history estimate is verified**
for that earlier source snapshot. It represents existing branch history before a
future owner commit, not the byte size of a future GitHub clone.

Current size snapshot including this review report (decimal bytes):

| Measure | Bytes | MB |
| --- | ---: | ---: |
| Reviewed source including this new review report (264 files) | 4,059,168 | 4.059 |
| All non-ignored files including seven images (271 files) | 5,898,254 | 5.898 |
| Existing packed branch-history bundle | 1,207,718 | 1.208 |
| Raw local .git including tool snapshots | 4,480,094 | 4.480 |
| Full local working tree excluding .git, including ignored data | 368,493,188 | 368.493 |
| Reviewed source + existing packed branch history | 5,266,886 | 5.267 |
| Reviewed source + raw local .git | 8,539,262 | 8.539 |
| All non-ignored files + raw local .git | 10,378,348 | 10.378 |

Source and packed branch history have ample headroom below decimal 10,000,000
bytes. Source plus raw local `.git` also fits. Adding the existing images to that
raw-local-Git interpretation exceeds 10 MB, while adding them to the measured
packed-history estimate remains below it. The large ignored working tree is not
the Git submission. Do not upload the entire local project folder.

Largest required tracked file: self-hosted Swagger JavaScript, **1,684,244 bytes**;
its CSS is **187,576 bytes**. Neither should be removed. `.venv`, runtime `data`,
profiles, caches, logs, backups and review evidence remain ignored and should
remain outside the submission. The existing ignore rules cover these paths.

**Commit scope after an approved fix:** the 13 files in the review table plus
this requested `docs/FINAL_PRE_SUBMISSION_REVIEW.md`; include the two currently
untracked optimization report/test module explicitly. Review any later fix diff
before staging. No staging command was executed by this review.

**Keep separate from this code-review commit:**

| Existing untracked image | Bytes | Inspection result |
| --- | ---: | --- |
| `1.png` | 638,420 | Landing artwork screenshot. |
| `2.png` | 586,584 | Fictional cinematic experience screenshot. |
| `Planora-AI-post/1-invitation-website.jpg` | 106,720 | Fictional invitation preview. |
| `Planora-AI-post/2-what-if-scenarios.jpg` | 135,214 | Fictional scenario comparisons. |
| `Planora-AI-post/3-ai-negotiation-draft.jpg` | 157,400 | Fictional vendor draft. |
| `Planora-AI-post/4-planning-dashboard.jpg` | 142,307 | Fictional dashboard; example-domain contact. |
| `Planora-AI-post/5-guest-rsvp.jpg` | 72,441 | Blank public RSVP form. |

All seven were opened and visually inspected again; all hashes match the prior
optimization manifest. No visible credentials or real personal data were found.
They total **1,839,086 bytes** and are legitimate optional marketing assets, not
garbage. They need not be deleted or ignored. Leave them untracked for this focused
commit unless the owner intentionally chooses a separate documentation/media
commit. The release scanner's binary-review flags are expected for these files;
they are not evidence of detected credentials. Visual inspection does not certify
all embedded image metadata.

## Verification Results

Fresh commands, executed from `D:\Projects\eventra`:

```powershell
git status --short
git diff --stat
git diff --check
git diff
git branch --show-current
git log -4 --oneline
git count-objects -v
git ls-files -ci --exclude-standard
git bundle verify .artifacts/optimization-submission-history.bundle
git bundle list-heads .artifacts/optimization-submission-history.bundle
git rev-parse main origin/main

$env:PYTHONDONTWRITEBYTECODE='1'
$env:GIT_CEILING_DIRECTORIES='D:\Projects\eventra\.artifacts'
$env:COVERAGE_FILE='D:\Projects\eventra\.artifacts\pre-submission-review.coverage'
.\.venv\Scripts\python -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90 --basetemp=.artifacts/pre-submission-review-pytest
.\.venv\Scripts\python -m ruff check --no-cache app tests scripts
.\.venv\Scripts\python -m ruff format --check --no-cache app tests scripts
.\.venv\Scripts\python -B -m scripts.check_structure
.\.venv\Scripts\python -m pip check

$scripts = @(Get-ChildItem frontend -Recurse -Filter *.js) + @(Get-ChildItem tests/browser -Filter *.mjs)
foreach ($script in $scripts) { node --check $script.FullName; if ($LASTEXITCODE -ne 0) { throw "Syntax failed: $($script.FullName)" } }
node --check vendor/swagger-ui-5.34.0/swagger-ui-bundle.js
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
node tests/browser/test_event_portal_geometry.mjs

$env:TEMP='D:\Projects\eventra\.artifacts'
$env:TMP=$env:TEMP
node .artifacts/optimization-focused.mjs .venv/Scripts/python.exe
node .artifacts/optimization-vendor-focused.mjs .venv/Scripts/python.exe
```

| Check | Actual outcome in this review |
| --- | --- |
| Diff whitespace | Pass, exit 0. |
| Full Python suite | **910 passed, 2 warnings, 80.86 seconds**. |
| Coverage | **98.34%**, unchanged 90% gate; separate coverage output. |
| Ruff / formatting | Pass / 129 files already formatted. |
| JavaScript syntax | 53 authored files and vendored Swagger pass. |
| Structure / original API contracts | 79 acyclic application modules, pass. |
| Money / decision metrics / portal geometry | All three Node checks pass. |
| Dependency consistency | `pip check`: no broken requirements. |
| Existing focused wizard check | Pass, including Back, Enter, composition guard, focus and accessible errors. |
| Extra keyboard completion check | Tab/Enter traverses every step and saves an isolated event. |
| Existing focused first-vendor check | Save/Escape/Close restoration passes. |
| Independent later-vendor comparison | **M1 reproduced**: later save succeeds but leaves BODY focused. |
| Isolated startup | `/healthz`, `/`, `/api/docs`, `/api/openapi.json`, `/static/app.js`: 200; unavailable invitation: 404. |
| Source/private-path patterns | No matches; seven reviewed binary images separate. |
| Real database | SHA-256 unchanged. |

Additional browser review bodies were supplied in memory to
`node --input-type=module - .venv/Scripts/python.exe`, reusing the existing CDP/server
harness and temporary data. For M1 the body expands vendor 0 or 1, opens and saves
the dialog, waits for close/busy completion, then records the exact saved vendor's
section state and `document.activeElement`. The keyboard body imports the checked-in
wizard regression and adds Tab/native Enter through the remaining stages. These
did not edit either checked-in browser test. The initial temporary reviewer harness
attempts needed normalization of CRLF boundaries and a less prescriptive native
Tab assertion; those failed attempts are not counted as passing verification.

Logs: `.artifacts/pre-submission-review-tests.txt`,
`pre-submission-review-wizard.txt`, `pre-submission-review-first-vendor.txt`,
`pre-submission-review-keyboard-complete.txt` and
`pre-submission-review-browser.txt`. The full 32-group browser log is from the
previous optimization, not a fresh full-suite run. Offline AI evaluation scripts
were not rerun in this review; their prior 30/30 result remains historical and
their implementation/fixtures were not changed. There is no frontend build step.
No live Gemini, hosted deployment, CVE audit or full WCAG audit was performed.

## Final Recommendation

**READY AFTER MINOR FIXES.** Approve and implement only the targeted later-vendor
focus repair and corresponding independent expected-UUID regression, then rerun
the relevant browser checks and review that small diff. L2 is optional hardening.
Afterward the intended source/test/documentation files are suitable for the
owner's manual commit and push, subject to the disclosed submission-size scope.
No other refactor or feature work is justified by this review.

No fix, existing-file edit, commit or push was performed. The official AI
evaluation score has not been rerun and no improvement is asserted.
