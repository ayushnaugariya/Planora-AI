# Budget Guardian accounting rules

All authoritative expense money uses Python Decimal, two decimal places, ROUND_HALF_UP. Send decimal API values as strings (integers also accepted); JSON floating-point numbers, NaN, infinity and negative amounts are rejected. Inputs may contain up to six decimal places and are rounded once on entry. Quantity supports three decimal places. Line total = round(quantity × rounded unit amount + rounded fixed tax + rounded fixed fee, 2). Unknown unit amounts produce an unknown line total, not a free expense.

The existing engine's whole-unit total budget and largest-remainder allocations are preserved. Editable category allocations remain nonnegative whole currency units for compatibility with the existing Plan schema. Shares/per-guest float fields in that schema are derived display values only. The Guardian summary's Decimal amounts are authoritative. Currency must match the event; no exchange conversion is performed.

## Definitions

- **Total event budget:** saved event budget, in its single currency.
- **Planned allocation:** sum of category allowances, including contingency; never treated as expenditure.
- **Estimate:** explicit all-in estimated amount, otherwise the calculated line total. Unknown is distinct from zero.
- **Quote:** an optional vendor all-in quotation for the same expense; it does not add another expense.
- **Commitment:** optional all-in contracted obligation, including deposits already paid.
- **Actual spending:** cumulative paid amount, including deposits/partial payments. Enter the cumulative total, not a payment increment.
- **Projected cost per active expense:** max(paid, commitment if known, otherwise quote if known, otherwise estimate if known, otherwise known fixed tax + fee as a lower bound). Estimates/quotes/commitments/payments are never summed as four expenses.
- **Remaining funds:** total budget minus total projected cost. It includes the protected reserve; unknown costs mean it is only provisional.
- **Cash remaining:** budget minus actual paid. **Outstanding commitments:** sum(max(commitment − paid, 0)) per expense, not a difference of unrelated category aggregates.
- **Unallocated funds:** total budget minus planned allocations; negative means over-allocation.
- **Contingency reserve:** the allowance whose key is `contingency`. **Contingency remaining:** max(reserve − contingency projected spending, 0). **Spendable remaining:** remaining funds minus contingency remaining.

All alternative lifecycle amounts are all-in, already including applicable taxes/fees; those are not added again. Payment status is derived: unpaid, part_paid, paid (relative to commitment), or payment_recorded when the full commitment is unknown. No independent status can falsely mark an unpaid bill as paid.

## Warnings and limits

Category cost above allowance, allocation above total, projection above total, reserve encroachment, paid above commitment, and material quote/estimate or commitment/prior-price differences (at least 20% and one whole currency unit) identify the relevant amounts and record IDs. Payments above the prior price are also warned when there is no full commitment; ordinary partial payments below the price are not flagged as discrepancies. Every positive-allowance non-reserve category, and always venue/catering, needs active cost information. An explicitly recorded zero cost is valid; a missing record or unknown cost is not proof of affordability. Reconciliation means sums match records, not that the event is affordable. Legacy records with no matching allocation are counted in a zero-allocation category, never omitted.

`per_guest` records use the event headcount as quantity. Fixed records keep their entered quantity. All-in quotes/commitments/manual estimates are not silently scaled when headcount changes; they require reconfirmation. Paid and committed totals are not erased by a scenario. Cancelled records no longer contribute estimates/quotes but retain paid/committed exposure.

Refunds, negative credits, currency conversion, installment transaction ledgers, tax-rate engines and payment processing are unsupported. Paid totals cannot decrease through edit. Confirmed deletion removes a record from current totals and records its ID/paid amount in history; it is a data correction, never a refund or movement of money. Each expense is scoped to its event and owner. Repeated create requests reuse a client UUID and validated-payload fingerprint; exact retries return the current saved result without duplicating the record or revision.

Manual allocations survive regeneration and never auto-rebalance. Over/under-allocation is permitted for editing and clearly warned. AI narrative is invalidated/replaced with current deterministic figures after financial mutations; Gemini does not calculate or write money.

Monetary API responses are Decimal strings. Currency formatting uses those strings and BigInt integer parts, preserving cents even for allowed aggregate values beyond JavaScript's exact-number range. Converting a value to Number is limited to bounded whole-unit allocation/guest inputs or legacy display fields; it is not used for authoritative ledger amounts or Guardian currency formatting.

## Isolated scenarios and feasibility

A preview is evaluated on a deep copy of the saved event at one event revision and calendar day. It persists separately; creating, reading, comparing, interpreting or discarding it does not update the event. It contains validated parameters, original/proposed values and budget summaries, exact deltas, expense changes, affected task dates/dependencies, warnings, reasons and status.

Supported commands:

- `budget_reduction`: positive Decimal amount or percent, exactly one. The target is rounded HALF_UP to a whole currency unit to preserve the existing event-budget contract. Preview shows that effective target. Allocations remain unchanged unless the user explicitly supplies proposed whole-unit allocation changes; no automatic proportional cut occurs. Adjustable category suggestions are advice only.
- `guest_count`: scale only explicit per-guest quantities at their recorded unit price, retain fixed quantities and paid/committed totals. All-in quotes/commitments/estimate overrides for another headcount require reconfirmation. Imported legacy totals have no defensible guest model until edited/reconfirmed.
- `event_date`: use the existing engine's date/compression rules and preserve completed task IDs/status. Flag overdue/urgent work and detect missing/cyclic/impossible prerequisite ordering. Booked vendors require date reconfirmation; no live availability is queried.
- `vendor_cancellation`: cancel only the hypothetical vendor; identify linked-category and transitive dependent tasks. Uncommitted estimates/quotes of linked cancelled expenses leave projection, but paid/committed exposure remains. Cancellation/replacement pricing and the user's replacement confirmation are required to resolve uncertainty. No replacement business or live availability is invented; retained contractual/refund uncertainty prevents a feasible claim.
- `category_cost`: hypothetical all-in venue/catering quote for a specific record (required when multiple records exist), or a new priced record if none exists. Existing commitments/payments cannot silently shrink; a lower hypothetical quote cannot release them.
- `additional_function`: a new hypothetical expense in a saved category; missing incremental pricing makes the scenario indeterminate, never free by default.

**Infeasible** means a known constraint fails: unsupported event budget/date, over-allocation, category overrun, projected overspending/reserve encroachment, impossible dependencies, or the 200-expense limit. **Indeterminate** means no known failure was found but essential pricing/reconfirmation is missing. **Feasible under known recorded constraints** means all these deterministic checks pass and needed prices/models are present. This is conditional on user-entered assumptions, not proof of market affordability, supplier capacity, booking availability, permits, weather, or contract validity. A zero remainder alone never establishes feasibility.

Application requires an explicit approval boolean, current owned event/scenario, matching base revision and evaluation day, and recalculation equal to the stored preview. The repository rechecks under a write transaction and commits event + revision/history + scenario applied status together. Failures roll back both. Exact retries of an already applied scenario return current saved state without applying twice. Discarded, stale, expired, infeasible or indeterminate previews cannot apply. Any event revision, even a chat update, conservatively invalidates pending previews. Create a fresh preview; no silent rebase exists.

## Storage and AI boundaries

### Rescue proposals (26 October 2026)

The cinematic-stage Scenario Studio quote comparison creates two ordinary `category_cost` previews from user-supplied all-in amounts in the saved event currency. It uses the existing scenario API, summaries and approval component; financial calculations, retained liabilities and feasibility rules are unchanged. These are two isolated saves, not an atomic comparison batch: if the second fails, the first remains in saved previews and the UI reports partial completion and retains the draft. Relative-guest language uses saved headcount and schema validation; no natural-language suggestion or quote comparison can apply itself. Missing date, quote or expense identity prompts clarification. FX conversion and independently verified pricing/availability remain unsupported.

Rescue does not add a financial or application engine. Its options are ordinary persisted scenarios and use the same `simulate`, summaries and explicit apply/discard routes. A reduced-budget assessment proposes whole-unit allowances with floors equal to the ceiling of each category's recorded projected exposure, preserving the existing contingency allowance. Remaining flexible allowance is distributed with the existing largest-remainder allocator, proportionally or with additional weight on saved priority categories. Duplicate policies are omitted. If the target cannot cover exposure and reserve, the existing allocations are retained in a visibly infeasible preview; no liability is erased. These are proposed spending limits, not negotiated prices, automatic savings or an event mutation. Only approval can apply the explicit proposal.

Guest/date alternatives and replacement quotes must be supplied by the user. Unknown fees, prices, confirmation or contractual release remain unresolved; no invented zero-cost replacement or external availability claim is permitted. Assessment saves one to three previews atomically with revision/owner/request-ID retry checks. The existing approval transaction remains the only Rescue application path. Incident descriptions/analysis are transient; saved planning previews/status/history persist without a new migration.

SQLite schema/workspace version 2 preserves v1 IDs, progress and history, translating legacy `amount` records into estimated unit amounts with `legacy` provenance. Initialization/migration is transactional; unknown or malformed schemas/data are rejected without destructive reset. Scenarios reference events with cascading deletion. Back up the database before upgrading; the previous application must not be used to write a version-2 database.

Derived current summaries, line totals, estimates and payment statuses are omitted from persisted event JSON and recalculated on read. Stored scenario summaries are immutable preview evidence tied to a base revision, not independent event totals or authority to apply. Existing anonymous-cookie scoping, 20KB actual-byte request cap, security headers and Cloud Run fail-closed behavior remain.

Gemini may select schema-validated advice actions and suggest schema-validated scenario parameters. The application renders all money and task facts from saved state; arbitrary model money/availability/approval claims are not accepted in workspace advice. Interpretation is read-only, reviewed in the structured form, and still needs preview + explicit approval. Offline interpretation accepts only a small unambiguous grammar (simple budget reduction or guest count); ambiguous/multiple instructions and unsafe numeric syntax fall back to the structured form. Provider tests use injected fakes; live Gemini availability is not claimed.
