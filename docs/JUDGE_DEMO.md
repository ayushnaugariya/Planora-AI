# Planora AI: a decision you can verify

## Start

From `D:\Projects\eventra`:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers
```

For a clean environment, run these before starting the server:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt ruff pytest-cov
```

These are setup instructions, not a claim that this stage recreated or reinstalled the existing environment. There is no npm/build step. Open `http://127.0.0.1:8000/`. Gemini is optional: set `GEMINI_API_KEY` in the launching process to enable it. The default model is `gemini-2.5-flash`, configurable through `GEMINI_MODEL`; `GEMINI_TIMEOUT_MS` defaults to 20000. No credential is required for this demo. Provider labels always distinguish Gemini from built-in extraction/planning.

Default SQLite location: `<project>/data/eventra.sqlite3`; `EVENTRA_DB_PATH` overrides it. Use durable local/single-instance storage and keep the anonymous browser ownership cookie. Do not delete the database or clear cookies between demonstration steps. See README for trusted-proxy/rate-limit/hosting requirements. Schema remains version 2 with no new migration.

## A three-minute judge journey

1. **Imagine.** Open the homepage and use **Open the invitation**. The architectural motion is optional; **Plan my event** remains directly accessible. Reduced-motion preferences are respected.
2. **Plan.** Select **Plan my event**. Enter `A wedding in Mumbai on YYYY-MM-DD for 120 guests with a budget of INR 800000. Theme: candlelit garden`, replacing the date with one within the next 3 years. Select **Shape my event brief**. Missing facts become questions, not hidden guesses. The budget categories and dated milestones use the original deterministic planner.
3. **Review.** Inspect the unsaved brief, source label and calculated allowances. Select **Use reviewed brief in the wizard**. Adjust the form if needed, then explicitly save. This creates a normal owned workspace; extraction itself wrote nothing.
4. **Recover.** Return home and scroll to the interactive example. Select **Try the full saved demo**, acknowledging that it creates a separate fictional workspace. All costs, deposits, supplier confirmations and replacement prices are illustrative. Existing events are retained. The app opens Event Rescue with a prefilled fictional entertainment cancellation, a $100 fee and two replacement assumptions ($950/$1,250).
5. **Simulate.** Select **Find a way forward**. Two isolated options are saved; the event is unchanged. The baseline projected cost is **$11,040.00**. The $950 replacement plus $100 fee produces **$10,819.80**, a **-$220.20 / -1.99%** change; the $1,250 replacement plus fee produces **$11,119.80**, a **$79.80 / 0.72%** change. These are conditional recorded-cost calculations, not market savings guarantees.
6. **Compare.** Open **Scenario Studio** to see the saved side-by-side cost/difference/percentage/reserve/status table. Select **Review** on an option. Inspect category/expense/task consequences, assumptions and feasibility. Apply remains disabled until explicit approval.
7. **Approve and verify.** Check the approval box and apply the current feasible preview. Success appears only after the backend transaction confirms. The event revision advances, and the other preview becomes stale. Original commitments/deposits remain. Reload, then stop and relaunch Uvicorn with the same DB path. Reopen the same fictional event: the applied status, amounts and revision persist. Other saved events are unchanged.

To repeat, deliberately create another fictional workspace; creation never resets old events. If creation's response is lost, retry in the same browser session: the stored request UUID returns that sample's current state instead of overwriting it. Cookie loss creates a new owner and has no recovery; retry identity cannot cross that boundary.

## Technical differentiators and honest limits

- A single Decimal ledger and scenario engine serve both actual workspaces and the demo. No separate mocked financial apply path exists in the saved demo.
- AI extracts reviewed inputs; exact allocations/dates/financial feasibility remain deterministic. No model output can authorize an owned write or scenario application.
- SQLite compare-and-swap, explicit approval, day/revision revalidation, re-simulation, atomic application and replay protection remain authoritative. Demo creation is also transactionally idempotent for an established owner/request UUID.
- Money remains Decimal strings and exact cents. The comparison uses BigInt for display-only differences/rounded percentages, including huge values and zero baselines.
- Missing pricing, commitments, confirmations or provider access are visible limitations. There is no live vendor availability, contract/OCR ingestion, payment due-date scheduler, RSVP table, generated venue photography, cross-device account recovery or distributed deployment claim.

Evaluation: `.\.venv\Scripts\python -m scripts.evaluate_planning` runs ten repeatable offline structural/financial constraint cases. It does not measure live Gemini accuracy. Full implementation, commands and artifact paths are recorded in [AUTONOMOUS_BUILD.md](AUTONOMOUS_BUILD.md).
