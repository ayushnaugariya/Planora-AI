"""Fictional fixtures use the actual planner and ledger; no provider or storage access."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.schemas.budget import ExpenseRecord
from app.schemas.workspaces import EventDetails, EventWorkspace
from app.services.planning import build_plan
from app.services.workspaces import reconcile


def fictional_workspace(event_id: UUID) -> EventWorkspace:
    now = datetime.now(UTC)
    details = EventDetails(
        event_type="birthday",
        title="A midsummer gathering",
        currency="USD",
        budget=20000,
        guest_count=60,
        event_date=date.today() + timedelta(days=90),
        priorities=["food"],
    )
    plan = build_plan(details.planning_request(), None)
    tasks, vendors = reconcile(None, plan)
    event = EventWorkspace(
        id=event_id,
        created_at=now,
        updated_at=now,
        generated_at=now,
        details=details,
        plan=plan,
        tasks=tasks,
        vendors=vendors,
    )
    event.expenses = [
        ExpenseRecord(
            event_id=event.id,
            category_key=line.key,
            description=f"Fictional {line.label} estimate",
            currency=details.currency,
            unit_amount=Decimal(line.amount) * Decimal("0.60"),
            priced_for_guests=details.guest_count,
        )
        for line in plan.budget_lines
        if line.key != "contingency"
    ]
    vendor = next(item for item in vendors if plan.vendors[item.group_index].key == "entertainment")
    next(item for item in event.expenses if item.category_key == "entertainment").vendor_id = vendor.id
    return event
