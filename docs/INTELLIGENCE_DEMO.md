# Judge walkthrough: facts, choices and proof

Start from the project directory:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers
```

Open `http://127.0.0.1:8000/`. No key is required; optional `GEMINI_API_KEY` enables the existing provider. Model and timeout remain `GEMINI_MODEL` / `GEMINI_TIMEOUT_MS`. The database remains `data/eventra.sqlite3` or `EVENTRA_DB_PATH`; retain the anonymous ownership cookie. There is no npm build, new dependency or required image provider.

1. **Open real saved facts.** Use **Try the full saved demo** on the homepage, acknowledging its separate fictional workspace. Inspect its Budget Guardian: estimates, commitment and deposit are distinct. This never resets another event. The original read-only landing illustration is separate.
2. **Ask a grounded question.** In **AI copilot**, use the new **Analyze my saved event** control with `Reduce budget by 10%`, `What if 30 more guests attend?`, or `What should I prioritize next?`. Cards show revision, recorded evidence, total budget versus projected cost, affected allowances, assumptions and uncertainty. Reduced allowances are not claimed as negotiated savings.
3. **Review before reality.** Select **Save isolated preview for review**. This uses Scenario Studio; the event is still unchanged. Review before/after, approve only a current feasible preview, or discard. The existing transaction/retry checks own application; the assistant never applies itself.
4. **Read a quotation.** In **Vendors**, open the quote analyzer. Choose a service category and vendor record, then load a supported UTF-8 `.txt` or paste labeled text. The example below uses USD; use the saved event's actual currency. Monetary values are plain decimal strings, not currency symbols or thousands separators. Replace dates with appropriate exact dates.

```text
Vendor: Example Kitchen
Service: Catering
Currency: USD
Item: Dinner and service | 60 | 20
Subtotal: 1200
Tax: 0
Fee: 0
All-in total: 1200
Deposit: 200
Payment: 2027-01-15 | 1200
Cancellation: Confirm whether deposit is retained
Inclusions: Dinner, service and tableware
Overtime: Not included
Valid until: 2027-01-20
```

5. **Compare terms and record deliberately.** Analyze another quote in the same category; the UI keeps up to three sources. Open original text/evidence and inspect inclusions, payment/cancellation/overtime terms, missing fields and reconciliation issues. Lowest price is not a vendor recommendation. Select the existing expense when one already represents this service. Choose **quote only** or explicitly **full commitment**, check the review box, then record. The quoted deposit is **not** recorded as paid. The ledger updates through the existing reconciliation/CAS transaction. No booking or supplier availability is claimed.
6. **Design within the facts.** In **Ideas & inspiration**, describe an atmosphere and optionally enter up to four `#RRGGBB` colors. Compare the three built-in concept recipes and their local CSS mood boards. Gemini, if available, only orders the allowed styles; this is labeled. Each concept links to actual category allowances and recorded exposure; none invents a concept price. Save a preferred concept. It persists separately, without changing money or existing event notes. Use its quote link to request real pricing before changing spend.
7. **Explain a delay.** In **Timeline & calendar**, select an open milestone, delay and explicit prerequisite buffer. The analysis propagates only saved dependency links and identifies dates crossing the event. Where links are absent, it says so. This is a read-only planning analysis, not a schedulable day-of run sheet; use Event Rescue/date scenarios for reviewed event-date alternatives.
8. **Respect the obligation.** In Event Rescue, analyze cancellation of a vendor whose linked quote was just explicitly committed. The existing commitment remains; contractual release/refunds are unresolved. The recovery can remain indeterminate and application stays disabled. A demo that invented a free cancellation would be wrong. Use the original uncommitted entertainment example to show a feasible real approval path.
9. **Verify persistence.** Reload, restart the server using the same SQLite path/profile, then reopen the event and preferred design. The quote/commitment, scenario statuses and concept persist. Other events remain intact. A later event revision marks the concept's budget snapshot stale and requires regenerated context before relying on those allowances.

Repeatable evaluations:

```powershell
.\.venv\Scripts\python -m scripts.evaluate_planning
.\.venv\Scripts\python -m scripts.evaluate_intelligence
```

Each reports ten actual offline constraint cases. They test structure, grounding, financial correctness and nonmutation; they are not live Gemini accuracy scores.

The exact official challenge statement remains unverified. Do not present generated inspiration as photography, supplier quotes as independently verified, static templates as free-form live AI creativity, or SQLite as a multi-instance account system. General PDFs/OCR, RSVPs/seating, vendor catalog matching, sustainability metrics and live notifications are not delivered. See [INTELLIGENCE_UPGRADE.md](INTELLIGENCE_UPGRADE.md) for evidence, changed files and optional-feature decisions. No repository was published and no submission was made.
