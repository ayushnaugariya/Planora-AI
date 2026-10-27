"""Grounded recovery options using the existing engine, never an alternate apply path."""

from datetime import UTC, date, datetime
from decimal import ROUND_CEILING
from uuid import uuid5

from fastapi import HTTPException

from app.schemas.budget import Allocation
from app.schemas.rescue import RecoveryOption, RescueAssessment
from app.schemas.scenarios import BudgetReduction, DateChange, GuestChange, VendorCancellation
from app.services.budget import calculate_budget
from app.services.engine import allocate
from app.services.scenarios import simulate


def _budget_options(base, target):
    if target >= base.details.budget:
        raise HTTPException(status_code=422, detail="The reduced target must be below the saved budget")
    summary = calculate_budget(base)
    lines = base.plan.budget_lines
    categories = {item.key: item for item in summary.categories}
    # A proposed allowance never drops below recorded projected exposure.
    # Retain the existing reserve; insufficient targets remain visibly infeasible.
    floors = [int(categories[line.key].projected.to_integral_value(rounding=ROUND_CEILING)) for line in lines]
    for i, line in enumerate(lines):
        if line.key == "contingency":
            floors[i] = max(floors[i], line.amount)
    if sum(floors) > target:
        return [
            (
                "Reassess recorded obligations",
                "The target cannot cover recorded exposure and the reserve. Negotiate before reallocating.",
                BudgetReduction(type="budget_reduction", amount=base.details.budget - target),
            )
        ]
    remaining = max(0, target - sum(floors))
    flexible = [
        max(0, line.amount - floors[i]) if line.key != "contingency" else 0 for i, line in enumerate(lines)
    ]
    results = []
    for priority in (False, True):
        weights = [weight * (2 if priority and lines[i].priority else 1) for i, weight in enumerate(flexible)]
        if not any(weights):
            weights = [int(line.key != "contingency") for line in lines]
        extra = allocate(remaining, weights)
        allocations = [
            Allocation(key=line.key, label=line.label, amount=floors[i] + extra[i])
            for i, line in enumerate(lines)
        ]
        params = BudgetReduction(
            type="budget_reduction", amount=base.details.budget - target, allocations=allocations
        )
        if any(params == prior[2] for prior in results):
            continue
        results.append(
            (
                "Protect your priorities" if priority else "Rebalance flexible allowances",
                "Keep recorded exposure and the reserve, then weight remaining "
                "allowances toward saved priorities."
                if priority
                else (
                    "Keep recorded exposure and the reserve, then distribute remaining "
                    "allowances proportionally."
                ),
                params,
            )
        )
    return results


def assess(base, body, today=None):
    today = today or date.today()
    days = (base.details.event_date - today).days
    urgency = "immediate" if days <= 7 else "soon" if days <= 30 else "planning"
    affected = []
    next_steps = [
        "Review each saved preview. Nothing changes until a feasible current preview is explicitly approved."
    ]
    constraints = [
        f"Saved revision {base.revision}; {base.details.guest_count} guests; {days} day(s) to the event.",
        "Prices and availability are not independently verified. Existing "
        "commitments and payments are retained.",
    ]
    if body.kind == "budget_reduction":
        candidates = _budget_options(base, body.target_budget)
        affected = [line.label for line in base.plan.budget_lines]
        next_steps.append(
            "Confirm any unpriced records and renegotiate costs before relying "
            "on reduced allowances; this does not guarantee savings."
        )
    elif body.kind == "guest_change":
        counts = list(
            dict.fromkeys(
                count for count in (body.guest_count, body.alternative_guest_count) if count is not None
            )
        )
        candidates = [
            (
                f"Plan for {count} guests",
                "Scale only explicitly per-guest expenses; retain fixed costs and confirmed commitments.",
                GuestChange(type="guest_count", guest_count=count),
            )
            for count in counts
        ]
        affected = ["Guest count", "Per-guest expense quantities", "Planning timeline and vendor guidance"]
        next_steps.append(
            "Supply an acceptable alternative headcount for a second defensible "
            "option. Reconfirm capacity and any fixed quotes."
        )
    elif body.kind == "timeline_risk":
        dates = list(
            dict.fromkeys(day for day in (body.event_date, body.alternative_event_date) if day is not None)
        )
        candidates = [
            (
                f"Move to {day.isoformat()}",
                "Rebuild deadlines around your proposed date while retaining "
                "completion and existing commitments.",
                DateChange(type="event_date", event_date=day),
            )
            for day in dates
        ]
        affected = ["Event date", "Task deadlines", "Vendor booking deadlines"]
        next_steps.append(
            "Supply another acceptable date for comparison. Booked vendors must "
            "reconfirm; this is not an availability check."
        )
    else:
        vendor = next((item for item in base.vendors if item.id == body.vendor_id), None)
        if vendor is None:
            raise HTTPException(status_code=404, detail="Vendor is not in this event")
        group = base.plan.vendors[vendor.group_index]
        if body.kind == "venue_unavailable" and group.key != "venue":
            raise HTTPException(
                status_code=422, detail="Choose this event's venue group for a venue incident"
            )
        affected = [group.label, *group.checklist]
        quotes = body.quotes or [None]
        candidates = []
        for quote in quotes:
            candidates.append(
                (
                    quote.label if quote else "Establish replacement assumptions",
                    "Preview cancellation and a user-supplied replacement; no supplier "
                    "is invented or booked.",
                    VendorCancellation(
                        type="vendor_cancellation",
                        vendor_id=vendor.id,
                        cancellation_fee=body.cancellation_fee,
                        replacement_cost=quote.amount if quote else None,
                        replacement_confirmed=quote.confirmed if quote else False,
                    ),
                )
            )
        next_steps.extend(
            [
                "Confirm cancellation terms, refund/release of committed exposure "
                "and all-in replacement pricing.",
                "Contact actual suppliers to verify capacity, date and service scope "
                "before marking a replacement confirmed.",
            ]
        )
    options = []
    created = datetime.now(UTC)
    for i, (title, approach, parameters) in enumerate(candidates):
        _, scenario = simulate(base, parameters, uuid5(body.request_id, str(i)), created, today)
        options.append(
            RecoveryOption(
                title=title,
                approach=approach,
                tradeoffs=[
                    "Allowances are planning limits, not negotiated prices or guaranteed savings.",
                    "Any change to the event or evaluation day makes this preview stale.",
                ],
                scenario=scenario,
            )
        )
    return RescueAssessment(
        event_id=base.id,
        revision=base.revision,
        incident=body.description,
        urgency=urgency,
        urgency_reason=f"Saved event date: {base.details.event_date.isoformat()}; no live monitoring.",
        constraints=constraints,
        affected=affected,
        next_steps=next_steps,
        options=options,
    )
