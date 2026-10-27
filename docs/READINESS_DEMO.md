# Readiness demonstration: evidence, approval, persistence

Start from the repository root:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload --no-proxy-headers
```

Open `http://127.0.0.1:8000/`. Keep the same browser ownership cookie and SQLite path (`data/eventra.sqlite3`, or `EVENTRA_DB_PATH`). No key, frontend build or new dependency is needed. Optional Gemini uses the existing key/model/timeout configuration; live-provider behavior has not been certified.

1. Use **Try the full saved demo** and acknowledge creation of a separate **Fictional** workspace. The existing saved-demo workflow creates the fixture through normal ownership/persistence. This feature does not modify that fixture, seed mock readiness values or reset any existing event. Complete/discard any initial sample recovery as in the original judge guide, then open **Overview**.
2. **Know where you stand** shows the actual saved revision, server assessment date, readiness state and check count. Explain that `6 / 14`, for example, means recorded checks, not 43% readiness or a probability. Exact counts depend on actual saved changes. Missing supplier facts, prerequisites and real-world contingency coverage remain incomplete.
3. Open the five evidence disclosures. They show actual budget/retained obligations and missing prices, saved vendor information, open/overdue milestones, prerequisites, checklist/requirements and current versus stale previews. The historical plan health heuristic remains separate. Use Tab and Enter on a disclosure, then on one of the three action links; it navigates into the original workflow without applying anything.
4. **Prioritize with AI** optionally orders the same three validated actions within urgency tiers. It cannot alter checks, money or state. Offline fallback is explicitly labeled. **Refresh saved evidence** performs a fresh read. A failed request clears stale evidence and reports the failure without claiming success.
5. For an approval demonstration, work **only in this fictional workspace**. In Guardian, identify the fictional cake estimate and note its exact original all-in amount. Verify it has no paid or committed amount. Explicitly confirm deleting just this uncommitted fictional estimate to simulate a missing cost entry; this is demo setup/data correction, not a cancellation or refund. Return to Overview: **Complete cost information** is now incomplete and the missing category is named.
6. Follow the existing Scenario Studio workflow: choose **Add an event function**, name it `Fictional reconfirmed cake service`, choose the same cake category, and supply the exact previously saved estimate as the explicitly fictional reconfirmed price. Create a preview. The event and readiness cost gap remain unchanged while that preview is pending. Review feasibility, budget/expense effects and assumptions. The Apply control stays disabled until explicit approval; if the preview is infeasible/indeterminate, resolve its actual reported constraints rather than bypass them. Check approval and apply through the existing server transaction.
7. Return to Overview. The confirmed new event revision now makes **Complete cost information** pass, with a higher recorded pass count. The pending preview alone did not produce that result. Other unknowns remain; the event must not become unconditionally fully ready. Reload and restart the server using the same DB path/profile. Reopen the same event: the approved expense/scenario persist and readiness is recomputed from them. Other saved events remain unchanged.

The automated browser demonstration also explicitly saves a fictional vendor cancellation and a subsequently confirmed fixture booking status through the original vendor editor, verifying the vendor dimension changes from attention to incomplete/clear. This tests recorded status, not live availability, booking or contract validity. Never mark a real supplier booked without actual confirmation merely to improve readiness.

Repeatable local checks:

```powershell
.\.venv\Scripts\python -m pytest tests/integration/test_readiness.py tests/integration/test_readiness_eval.py -o addopts='' -q
.\.venv\Scripts\python -m scripts.evaluate_readiness
node tests/browser/browser_workspace_smoke.mjs .venv/Scripts/python.exe
```

The browser harness uses temporary SQLite data, profiles and owned Uvicorn processes, with no user DB reset. See [READINESS_INTELLIGENCE.md](READINESS_INTELLIGENCE.md) for exact formula/data sources, security boundaries, evidence, test results, file inventory and limitations. Readiness is not an event-day command center, comprehensive risk register or certification of successful execution.
