"""Transparent recorded checks, not a weighted prediction of real-world event success."""

from datetime import date

from app.schemas.readiness import ReadinessAction, ReadinessCheck, ReadinessDimension, ReadinessReport
from app.services.scenarios import dependency_reasons


def readiness(base, previews=(), *, today=None):
    today = today or date.today()
    summary = base.budget_summary
    dimensions, candidates = [], []

    def dimension(key, title, specs):
        checks = []
        for check_id, label, status, evidence, destination, action, impact, critical in specs:
            checks.append(
                ReadinessCheck(
                    id=check_id, title=label, status=status, evidence=evidence, destination=destination
                )
            )
            candidates.append(
                ReadinessAction(
                    check_id=check_id,
                    title=action,
                    evidence=evidence,
                    potential_impact=impact,
                    destination=destination,
                    priority=0 if status == "attention" and critical else (1 if status != "pass" else 2),
                )
            )
        states = {item.status for item in checks}
        dimensions.append(
            ReadinessDimension(
                id=key,
                title=title,
                state="attention"
                if "attention" in states
                else "incomplete"
                if "unknown" in states
                else "clear",
                passed=sum(item.status == "pass" for item in checks),
                total=len(checks),
                checks=checks,
            )
        )

    labels = {line.key: line.label for line in base.plan.budget_lines}
    missing = [labels.get(key, key) for key in summary.missing_categories]
    warnings = [
        item.message for item in summary.warnings if item.code not in {"missing_cost", "unknown_expense"}
    ]
    dimension(
        "budget",
        "Budget evidence",
        [
            (
                "budget_constraints",
                "Recorded financial constraints",
                "attention" if warnings else "pass",
                [
                    f"Budget {summary.total_budget}; projected "
                    f"{summary.projected_cost}; paid {summary.actual_spending}; "
                    f"committed {summary.committed_spending}; protected reserve "
                    f"remaining {summary.contingency_remaining} "
                    f"{summary.currency}.",
                    *warnings,
                ],
                "budget",
                "Review the recorded budget constraints",
                "Resolve recorded overruns or discrepancies; no price reduction or savings is assumed.",
                True,
            ),
            (
                "budget_prices",
                "Complete cost information",
                "unknown" if missing or summary.unknown_expenses else "pass",
                [
                    f"Missing priced categories: {', '.join(missing) or 'none'}.",
                    f"Unknown expense prices: {len(summary.unknown_expenses)}.",
                ],
                "budget",
                "Complete and reconfirm all-in costs",
                "Replace unknown costs with actual quotes to make affordability "
                "assessable; deposits are not full costs.",
                False,
            ),
        ],
    )
    vendors = base.vendors
    unnamed = sum(not item.name.strip() or not item.contact.strip() for item in vendors)
    cancelled = sum(item.booking_status == "cancelled" for item in vendors)
    unbooked = sum(item.booking_status not in {"booked", "cancelled"} for item in vendors)
    linked = {
        item.vendor_id
        for item in base.expenses
        if not item.cancelled and (item.quoted_amount is not None or item.committed_amount is not None)
    }
    unpriced = sum(not item.quotes and item.id not in linked for item in vendors)
    dimension(
        "vendors",
        "Vendor evidence",
        [
            (
                "vendor_contacts",
                "Supplier identity and contact",
                "unknown" if unnamed or not vendors else "pass",
                [f"{len(vendors)} saved vendor groups; {unnamed} missing name or contact."],
                "vendors",
                "Complete supplier identities and contact details",
                "Make saved suppliers contactable; availability remains unverified.",
                False,
            ),
            (
                "vendor_booking",
                "Recorded booking status",
                "attention" if cancelled else "unknown" if unbooked or not vendors else "pass",
                [
                    f"{cancelled} cancelled; {unbooked} unbooked or shortlisted; "
                    f"{sum(item.booking_status == 'booked' for item in vendors)} marked booked."
                ],
                "rescue" if cancelled else "vendors",
                "Review cancelled supplier obligations" if cancelled else "Confirm supplier booking status",
                "Review replacements through Rescue when necessary; recorded status "
                "does not verify a contract.",
                True,
            ),
            (
                "vendor_costs",
                "Supplier quote or commitment evidence",
                "unknown" if unpriced or not vendors else "pass",
                [
                    f"{unpriced} of {len(vendors)} vendor groups have neither a saved "
                    "vendor quote nor a linked active expense quote/commitment."
                ],
                "vendors",
                "Collect written supplier terms and all-in quotations",
                "Identify financial terms before committing; a contact-only quote is "
                "not automatically in the ledger.",
                False,
            ),
        ],
    )
    tasks = [(task, base.plan.timeline[task.milestone_index]) for task in base.tasks]
    planning = [(task, milestone) for task, milestone in tasks if milestone.category != "event"]
    open_tasks = [(task, milestone) for task, milestone in planning if not task.completed]
    overdue = sorted(
        (milestone for _, milestone in open_tasks if milestone.due < today), key=lambda item: item.due
    )
    crossings = [milestone for _, milestone in open_tasks if milestone.due > base.details.event_date]
    dependencies = dependency_reasons(base)
    dimension(
        "timeline",
        "Timeline evidence",
        [
            (
                "timeline_overdue",
                "Open overdue milestones",
                "attention" if overdue else "pass" if planning else "unknown",
                [f"{len(overdue)} open planning milestones overdue as of {today.isoformat()}."]
                + [f"{item.title}: {item.due.isoformat()}." for item in overdue],
                "timeline",
                "Address overdue planning milestones",
                "Resolve or review actual deadlines; analysis does not reschedule tasks.",
                True,
            ),
            (
                "timeline_dependencies",
                "Saved dependency constraints",
                "attention"
                if dependencies
                else "pass"
                if any(task.depends_on for task in base.tasks)
                else "unknown",
                dependencies
                or [
                    "Recorded dependency checks found no conflicts."
                    if any(task.depends_on for task in base.tasks)
                    else "No prerequisite links recorded; downstream delay coverage is unknown."
                ],
                "timeline",
                "Review milestone prerequisites",
                "Use existing delay analysis; missing links cannot demonstrate a resilient schedule.",
                True,
            ),
            (
                "timeline_dates",
                "Event-date constraints",
                "attention" if crossings or base.details.event_date < today else "pass",
                [
                    f"Saved event date: {base.details.event_date.isoformat()}; "
                    f"{len(crossings)} open planning milestones after it."
                ]
                + [f"{item.title}: {item.due.isoformat()}." for item in crossings],
                "timeline",
                "Review dates against the event day",
                "Use a reviewed date scenario for event-date changes; no date is applied here.",
                True,
            ),
            (
                "timeline_progress",
                "Planning milestone completion",
                "unknown" if open_tasks or not planning else "pass",
                [
                    f"{len(planning) - len(open_tasks)} of {len(planning)} planning "
                    f"milestones complete; {len(open_tasks)} open."
                ]
                + [
                    f"Next: {item.title} ({item.due.isoformat()})."
                    for _, item in sorted(open_tasks, key=lambda pair: pair[1].due)[:3]
                ],
                "timeline",
                "Complete the next saved planning milestone",
                "Advance recorded planning progress without claiming task ownership or durations.",
                False,
            ),
        ],
    )
    checks = [check for vendor in vendors for check in vendor.checklist]
    incomplete = sum(not check.completed for check in checks)
    dimension(
        "planning",
        "Planning completeness",
        [
            (
                "planning_essentials",
                "Saved event essentials",
                "pass" if base.details.title.strip() and base.details.guest_count >= 2 else "unknown",
                [
                    f"Saved {base.details.event_type}; {base.details.guest_count} planned guests; "
                    f"{base.details.event_date.isoformat()}; {base.details.currency}."
                ],
                "settings",
                "Reconfirm saved event requirements",
                "Keep the planning inputs accurate; planned guest count is not an RSVP count.",
                False,
            ),
            (
                "planning_decisions",
                "Unresolved decisions and assumptions",
                "unknown" if base.details.unresolved_decisions or base.details.assumptions else "pass",
                [
                    "Unresolved decisions: " + (base.details.unresolved_decisions or "none recorded"),
                    "Assumptions: " + (base.details.assumptions or "none recorded"),
                ],
                "settings",
                "Review recorded assumptions and open decisions",
                "Clarify requirements before committing; empty optional fields do not "
                "confirm that requirements are absent.",
                False,
            ),
            (
                "planning_checklists",
                "Supplier checklist completion",
                "unknown" if incomplete or not checks else "pass",
                [f"{len(checks) - incomplete} of {len(checks)} saved supplier checklist items complete."],
                "checklist",
                "Complete the saved supplier checklists",
                "Record preparation evidence using the existing checklist workflow.",
                False,
            ),
        ],
    )
    pending = [item for item in previews if item.status == "pending"]
    current = [item for item in pending if item.base_revision == base.revision and item.evaluated_on == today]
    stale = len(pending) - len(current)
    dimension(
        "resilience",
        "Recovery review evidence",
        [
            (
                "resilience_previews",
                "Unreviewed alternatives",
                "unknown" if pending else "pass",
                [
                    f"{len(current)} current pending alternatives; {stale} stale/expired pending; "
                    f"{sum(item.status == 'applied' for item in previews)} applied; "
                    f"{sum(item.status == 'discarded' for item in previews)} discarded.",
                    "Current feasibility: "
                    f"{sum(item.feasibility == 'feasible' for item in current)} feasible, "
                    f"{sum(item.feasibility == 'infeasible' for item in current)} infeasible, "
                    f"{sum(item.feasibility == 'indeterminate' for item in current)} indeterminate.",
                ],
                "scenarios",
                "Review or discard saved alternatives",
                "A pending proposal is not an applied improvement; stale previews need fresh calculation.",
                False,
            ),
            (
                "resilience_coverage",
                "Real-world contingency coverage",
                "unknown",
                [
                    "Rescue incident descriptions and contract resolution are not "
                    "stored as an incident register. "
                    "Saved scenarios cannot prove contingency coverage or that a risk was resolved."
                ],
                "rescue",
                "Review a concrete event risk in Event Rescue",
                "Supply actual incident facts and alternative pricing; unresolved "
                "liabilities remain obligations.",
                False,
            ),
        ],
    )
    passed, total = sum(item.passed for item in dimensions), sum(item.total for item in dimensions)
    states = {item.state for item in dimensions}
    state = (
        "attention_needed"
        if "attention" in states
        else "incomplete_evidence"
        if "incomplete" in states
        else "recorded_checks_clear"
    )
    actions = sorted(candidates, key=lambda action: action.priority)[:3]
    return ReadinessReport(
        event_id=base.id,
        revision=base.revision,
        evaluated_on=today,
        state=state,
        explanation=f"{passed} of {total} recorded checks pass. "
        + (
            "Known constraints need attention; missing evidence remains incomplete."
            if state == "attention_needed"
            else "Missing evidence prevents a fully-ready conclusion."
        )
        + " Counts are not a weighted score, probability or guarantee of readiness.",
        passed=passed,
        total=total,
        dimensions=dimensions,
        actions=actions,
        limitations=[
            "Only saved, user-entered facts are assessed; prices, booking "
            "availability and contract terms are not independently verified.",
            "No numerical readiness score: unequal checks are not interchangeable "
            "points. Unknown checks never count as passes.",
            "Dates use the server calendar day, consistent with scenarios; event "
            "timezone/day-of timing is not modeled. Today is not overdue.",
            "Guest RSVPs are tracked separately and do not replace planning headcount. "
            "Task owners, weather, permits and comprehensive incident coverage remain "
            "unmodeled. This is not a fully-ready certification.",
            "Read-only snapshot. A later saved change or server day requires refresh; "
            "previews require their original review and explicit approval.",
        ],
    )
