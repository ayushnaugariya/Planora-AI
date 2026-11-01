# Final vendor accessibility fix

1 November 2026, Asia/Calcutta. Scope: the targeted follow-up to M1, L1 and L2
in `FINAL_PRE_SUBMISSION_REVIEW.md`. That review is retained as a historical
snapshot. This pass preserves the earlier uncommitted optimization and existing
untracked images. No commit, push or history change is authorized or performed.

## Root cause

Saving vendor details calls `applyWorkspace`, which replaces the vendor-list DOM
before the native dialog closes. The renderer opens only the first vendor's
`<details>` section. Later sections close, so their edit buttons are no longer
focusable, even when `getClientRects()` reports a nonempty rectangle. The old
close handler tried only that button and could leave focus on `<body>`.

The first vendor's replacement edit button stayed visible, which concealed the
defect in a test that edited only that vendor. That test also derived its expected
UUID from the post-save focus instead of establishing the intended target before
the action.

## Exact files changed in this follow-up

| File | Targeted change |
| --- | --- |
| `frontend/modules/coordination.js` | Restore to the matching visible edit button, section summary or deliberate Vendors-panel fallback. |
| `tests/browser/optimization_smoke.mjs` | Add the shared vendor regression and strengthen the invalid date's exact accessibility-tree error assertion. |
| `tests/browser/planora_product_smoke.mjs` | Invoke the shared vendor regression in the existing product flow; retain its original first-vendor saved-value assertions and all subsequent workflows. |
| `docs/FINAL_EVALUATION_OPTIMIZATION.md` | Record this follow-up and qualify the earlier partial repair/result. |
| `docs/FINAL_ACCESSIBILITY_FIX.md` | This report. |

This is an incremental five-file scope, not a claim that the working tree was
otherwise clean. Existing application changes and the prior review report remain.
No renderer, schema, API, security, financial or dependency change was needed.

## Focus-management fix

The existing close handler retains its single animation-frame callback, allowing
the save/render/busy cycle to finish. It captures the closing vendor UUID and
resolves the replacement elements for that UUID, rather than keeping a detached
DOM reference. A reopened dialog suppresses restoration.

The target order is deliberate:

1. The matching edit button, when its vendor section is open.
2. That section's native `<summary>`, which remains visible and keyboard-operable
   when the section closes, or when its edit button is hidden.
3. The existing `#panel-vendors` tab panel, which is labelled by the Vendors tab
   and already has `tabindex="0"`, when the opener has disappeared entirely or
   the more specific targets cannot receive focus.

Each candidate must be present, enabled and have layout rectangles; after calling
`focus()`, the handler verifies `document.activeElement` before accepting it.
Thus geometry alone cannot silently certify success. No candidate is `<body>`.
No new timeout, focus trap, landmark, ARIA workaround or expansion-state change
was introduced. Native dialog and disclosure semantics remain intact. Pointer
save/cancel behavior, saved vendor values and the API request are preserved.

The actual workflow populates/edits existing per-category vendor records through
the existing PATCH operation; this change does not add a separate vendor-creation
feature. The regression records initially blank contacts and re-edits a populated
contact through that same supported workflow.

## Regression proof and test changes

Before modifying the close handler, the strengthened focused test passed its
strict wizard checks and first-vendor assertions, then failed waiting for the
**second vendor's own summary** to receive focus after save. The test used a
1440x960 viewport matching the full product suite. Evidence:
`.artifacts/final-accessibility-before.txt` and
`.artifacts/final-accessibility-before-errors.txt` (exit 1).
The timeout expression names the second vendor UUID and its summary; it is not
an unrelated assertion or an arbitrary focused element.

With the fix, `checkVendorFocus` runs within the existing product checkpoint and:

- Captures vendor UUIDs from the saved event before any dialog save. Expected
  edit-button/summary expressions are established before each action.
- Saves the first, actual second and all remaining vendor sections (six in the
  birthday fixture). It asserts the exact expected focus target, non-body focus,
  visible keyboard control and retained section state. In particular, the second
  section is **closed**, with its own summary focused.
- Reads the saved event back and checks the matching vendor's exact name,
  contact and booking status. It re-edits the populated second vendor and checks
  that new contact value and summary focus again.
- Preserves native Escape and Close checks for every vendor, comparing focus
  with the UUID established before the dialog was opened.
- Hides a triggering button to verify its section-summary fallback, then removes
  the opener to verify the labelled-panel fallback. The test reloads authoritative
  data afterward to restore its test-only DOM removal.
- Confirms event details, budget summary and task completion are unchanged.

The wizard assertion now checks the actual empty required date's native
`validationMessage`, the referenced visible `#form-error`, matching error text and
`aria-invalid="true"`. It obtains the date's backend DOM node ID, requests the
accessibility node without relatives, selects that exact node and asserts its
description equals the field's error and its invalid property is true. Another
element's unrelated description can no longer satisfy this assertion. The
existing correction/back/Enter/composition assertions remain.

No existing assertion was weakened to pass. No Python test was added or removed,
and browser checkpoint counts are not inflated by the expanded assertions.

## Actual verification

Relevant browser checks were run before the full verification suite.

| Check | Result |
| --- | --- |
| Before-fix strengthened regression | Fails specifically at second-vendor summary restoration, exit 1. |
| Corrected focused regression | Pass: specific date accessibility node, all six vendor saves, re-edit, Escape/Close and hidden/removed-opener fallbacks, exit 0. |
| Full Python suite / coverage | **910 passed, 2 unchanged warnings, 47.13 seconds; 98.34% coverage**, unchanged 90% gate. |
| Full Edge/Uvicorn browser suite | **32 checkpoint groups passed, exit 0**, including all six vendor sections, exact date error node, restart, ownership, public RSVP and cinematic/reduced-motion workflows; no runtime exceptions. |
| Ruff / format | Pass / 129 Python files already formatted. |
| JavaScript syntax | 53 authored scripts and the vendored Swagger bundle pass. |
| Structure / original HTTP contracts | Pass: 79 acyclic application modules and frozen contracts retained. |
| Exact-cent / decision metrics / portal geometry | All three Node checks pass. |
| Offline AI evaluations | Planning 10/10, intelligence 10/10, readiness 10/10. |
| Package consistency | `pip check`: no broken requirements. |
| Startup and real database checksum | `/healthz`, `/`, `/api/docs`, `/api/openapi.json`, `/static/app.js`: 200; unknown invitation: 404. Real database SHA-256 unchanged. |
| Diff whitespace | Pass; existing line-ending normalization notices only. |

A focused-harness attempt initially used the default small viewport and did not
reach the vendor tab; the before-fix reproduction above uses the product suite's
desktop viewport. After expanding to all sections, one intermediate focused run
timed out on a focus expectation; a diagnostic rerun passed the same assertions
without code or assertion changes. These attempts are not counted as successful
verification or attributed to an unproven environmental cause. Final complete
results are recorded separately rather than replacing the before-fix evidence.
The final full suite passed the same expanded assertions; the earlier isolated
timeout was not reproduced in that run. The final browser harness retained one
ignored temporary profile because Windows still locked it after process shutdown;
this is recorded in its log and did not change the exit status or application data.

Commands (PowerShell, project root; isolated evidence under `.artifacts`):

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP='D:\Projects\eventra\.artifacts'
$env:TMP=$env:TEMP
node .artifacts/final-accessibility-focused.mjs .venv/Scripts/python.exe
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe

$env:GIT_CEILING_DIRECTORIES='D:\Projects\eventra\.artifacts'
$env:COVERAGE_FILE='D:\Projects\eventra\.artifacts\final-accessibility.coverage'
.\.venv\Scripts\python -m pytest -p no:cacheprovider --cov --cov-report=term-missing --cov-fail-under=90 --basetemp=.artifacts/final-accessibility-pytest
.\.venv\Scripts\python -m ruff check --no-cache app tests scripts
.\.venv\Scripts\python -m ruff format --check --no-cache app tests scripts
.\.venv\Scripts\python -B -m scripts.check_structure
node tests/browser/test_money_display.mjs
node tests/browser/test_decision_metrics.mjs
node tests/browser/test_event_portal_geometry.mjs
.\.venv\Scripts\python -B -m scripts.evaluate_planning
.\.venv\Scripts\python -B -m scripts.evaluate_intelligence
.\.venv\Scripts\python -B -m scripts.evaluate_readiness
.\.venv\Scripts\python -m pip check
git diff --check
```

All authored JS/MJS files were also enumerated and passed to `node --check`, as
was `vendor/swagger-ui-5.34.0/swagger-ui-bundle.js`. The focused wrapper reuses the
existing CDP/server/pointer helpers and imports the checked-in regressions; it is
ignored execution evidence, not a new dependency or production test framework.
Logs: `.artifacts/final-accessibility-focused*.txt`,
`final-accessibility-tests.txt`, `final-accessibility-browser*.txt`.

## Preservation and remaining limitations

No backend logic, event ownership, public invitation privacy, RSVP workflow,
budget arithmetic, database schema, AI behavior, landing design, dependency or
security control changed. Test databases and browser profiles are isolated; the
real database is never the test target. Existing untracked images remain untouched.

The real database SHA-256 remains
`61f08f210106b48c462cc4d9861cc45e054af9f2b71e17349e41da1a4ddd6ac6`.
The GitHub connector still reports `visibility:public`, `private:false`; no remote
setting was changed. Repository-size measurements in earlier reports are dated
snapshots, not the byte count of a future owner commit.

This is a scoped Edge/CDP regression, not a complete WCAG or cross-browser audit.
It does not certify every screen reader, native input method or browser-chrome
focus cycle. Existing single-instance SQLite, anonymous-session recovery and
unverified public-RSVP limitations remain. No hosted deployment, live Gemini or
dependency CVE certification was performed. The official AI evaluation was not
rerun; no score improvement is claimed.

## Submission conclusion

**READY TO COMMIT AND PUSH after the owner's diff review.** The confirmed
second-vendor defect is fixed: its closed section's own summary receives focus.
The strengthened pre-fix regression reproduced the defect, and the corrected
focused and full browser runs verify meaningful visible targets, exact vendor
data, and deliberate hidden/removed-opener fallbacks. M1, L1 and L2 from the prior
review are addressed by this five-file follow-up.

The actual final results are **910 Python tests passed, 98.34% coverage and 32
browser checkpoint groups passed**, with lint, formatting, syntax, contracts,
exact-cent checks, offline evaluations and startup also passing. Existing source
plus the measured packed branch history remains below 10 MB; ignored local test
profiles/evidence are outside the submission. Source scanning found no secret or
private-path patterns, and all seven existing image hashes remain unchanged.

No commit or push has been performed. Review all intended changes from the prior
optimization plus this targeted follow-up before the owner's manual submission.
The official AI evaluation has not been rerun.
