"""Pure simulation isolation, pricing limits, schedules and dependency constraints."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import TypeAdapter, ValidationError

from app.schemas.budget import ExpenseRecord
from app.schemas.scenarios import ScenarioParameters
from app.schemas.workspaces import EventWorkspace
from app.services.scenarios import simulate
from tests.integration.test_workspaces import create


def known_event(client):
    event = EventWorkspace.model_validate(create(client))
    event.expenses = [
        ExpenseRecord(
            event_id=event.id,
            category_key=line.key,
            description=f"Confirmed {line.label}",
            currency=event.details.currency,
            unit_amount="0",
            priced_for_guests=event.details.guest_count,
        )
        for line in event.plan.budget_lines
        if line.key != "contingency"
    ]
    return event


def run(event, **parameters):
    inputs = TypeAdapter(ScenarioParameters).validate_python(parameters)
    return simulate(event, inputs, uuid4(), datetime.now(UTC))


def test_guest_simulation_scales_only_explicit_unit_model_and_is_isolated(client):
    event = known_event(client)
    catering = next(item for item in event.expenses if item.category_key == "catering")
    catering.cost_basis, catering.quantity, catering.unit_amount = "per_guest", Decimal(30), Decimal("10")
    before = event.model_dump_json()
    proposed, preview = run(event, type="guest_count", guest_count=70)
    assert event.model_dump_json() == before
    assert proposed.details.guest_count == 70 and preview.proposed_budget.projected_cost == 700
    assert next(item for item in proposed.expenses if item.id == catering.id).quantity == 70
    assert next(item for item in proposed.expenses if item.id == catering.id).updated_at == preview.created_at
    assert next(item for item in proposed.expenses if item.id == catering.id).provenance == "scenario"
    assert proposed.expenses[0].quantity == 1
    assert preview.feasibility == "feasible"
    assert preview.expense_changes[0].id == catering.id
    assert preview.proposed_values["guest_count"] == 70


def test_unknown_pricing_and_per_guest_quote_reconfirmation(client):
    event = EventWorkspace.model_validate(create(client))
    assert run(event, type="guest_count", guest_count=100)[1].feasibility == "indeterminate"
    known = known_event(client)
    record = known.expenses[0]
    record.cost_basis, record.unit_amount, record.quoted_amount = "per_guest", Decimal(1), Decimal(20)
    proposed, preview = run(known, type="guest_count", guest_count=50)
    assert preview.feasibility == "indeterminate"
    assert proposed.expenses[0].quoted_amount == 20
    assert "reconfirm_price" in [warning.code for warning in preview.proposed_budget.warnings]


def test_budget_reduction_never_silently_reallocates(client):
    event = known_event(client)
    proposed, preview = run(event, type="budget_reduction", percent="10")
    assert proposed.details.budget == 54000 and preview.feasibility == "infeasible"
    assert {line.key: line.amount for line in proposed.plan.budget_lines} == {
        line.key: line.amount for line in event.plan.budget_lines
    }
    venue = event.plan.budget_lines[0]
    proposed, preview = run(
        event,
        type="budget_reduction",
        amount="6000",
        allocations=[{"key": venue.key, "label": venue.label, "amount": venue.amount - 6000}],
    )
    assert preview.feasibility == "feasible"
    assert preview.proposed_budget.planned_allocation == 54000
    assert event.details.budget == 60000


def test_impossible_budget_and_decimal_target_rounding(client):
    event = known_event(client)
    assert run(event, type="budget_reduction", amount="60000")[1].feasibility == "infeasible"
    assert run(event, type="budget_reduction", amount="1.50")[0].details.budget == 59999


def test_budget_change_updates_existing_health_heuristic_without_reallocating(client):
    event = known_event(client)
    allocations = [
        {"key": line.key, "label": line.label, "amount": 24000 if line.key == "catering" else 0}
        for line in event.plan.budget_lines
    ]
    proposed, preview = run(event, type="budget_reduction", amount="36000", allocations=allocations)
    assert preview.feasibility == "feasible"
    assert proposed.plan.health_score < event.plan.health_score
    assert sum(line.amount for line in proposed.plan.budget_lines) == 24000


def test_date_change_preserves_completed_ids_and_finds_urgent_work(client):
    event = known_event(client)
    event.tasks[0].completed = True
    proposed, preview = run(
        event, type="event_date", event_date=(date.today() + timedelta(days=3)).isoformat()
    )
    assert [task.id for task in proposed.tasks] == [task.id for task in event.tasks]
    assert proposed.tasks[0].completed
    assert proposed.plan.event_date == date.today() + timedelta(days=3)
    assert preview.affected_tasks and any("Urgent" in warning for warning in preview.warnings)
    assert preview.feasibility == "feasible"
    assert (
        run(event, type="event_date", event_date=(date.today() - timedelta(days=1)).isoformat())[
            1
        ].feasibility
        == "infeasible"
    )
    event.vendors[0].booking_status = "booked"
    assert (
        run(event, type="event_date", event_date=(date.today() + timedelta(days=90)).isoformat())[
            1
        ].feasibility
        == "indeterminate"
    )


@pytest.mark.parametrize("case", ["cycle", "missing", "order", "completed"])
def test_impossible_dependencies_are_not_financially_approved(client, case):
    event = known_event(client)
    first, second = event.tasks[:2]
    first.depends_on = [second.id]
    if case == "cycle":
        second.depends_on = [first.id]
    elif case == "missing":
        first.depends_on = [uuid4()]
    elif case == "completed":
        first.completed = True
    assert (
        run(event, type="event_date", event_date=(date.today() + timedelta(days=20)).isoformat())[
            1
        ].feasibility
        == "infeasible"
    )


def test_vendor_cancellation_is_isolated_and_tracks_dependent_tasks(client):
    event = known_event(client)
    vendor = next(v for v in event.vendors if event.plan.vendors[v.group_index].key == "venue")
    event.expenses[0].vendor_id = vendor.id
    venue_task = next(
        task for task in event.tasks if event.plan.timeline[task.milestone_index].category == "venue"
    )
    event.tasks[-2].depends_on = [venue_task.id]
    proposed, preview = run(event, type="vendor_cancellation", vendor_id=str(vendor.id))
    assert preview.feasibility == "indeterminate" and vendor.booking_status == "unbooked"
    assert next(v for v in proposed.vendors if v.id == vendor.id).booking_status == "cancelled"
    assert {venue_task.id, event.tasks[-2].id} <= {task.id for task in preview.affected_tasks}
    assert (
        run(
            event,
            type="vendor_cancellation",
            vendor_id=str(vendor.id),
            cancellation_fee="0",
            replacement_cost="50",
            replacement_confirmed=True,
        )[1].feasibility
        == "feasible"
    )
    event.expenses[0].committed_amount = Decimal(10)
    assert (
        run(
            event,
            type="vendor_cancellation",
            vendor_id=str(vendor.id),
            cancellation_fee="0",
            replacement_cost="50",
            replacement_confirmed=True,
        )[1].feasibility
        == "indeterminate"
    )


def test_category_cost_and_additional_function_impacts(client):
    event = known_event(client)
    proposed, preview = run(event, type="category_cost", category_key="catering", amount="123.45")
    assert preview.feasibility == "feasible" and preview.proposed_budget.projected_cost == Decimal("123.45")
    assert preview.expense_changes
    assert event.budget_summary.projected_cost == 0
    assert run(event, type="additional_function", name="Welcome dinner")[1].feasibility == "indeterminate"
    assert (
        run(event, type="additional_function", name="Welcome dinner", estimated_cost="100")[1].feasibility
        == "feasible"
    )
    assert (
        run(event, type="additional_function", name="Welcome dinner", estimated_cost="999999")[1].feasibility
        == "infeasible"
    )
    event.expenses.append(event.expenses[0].model_copy(update={"id": uuid4()}))
    assert (
        run(event, type="category_cost", category_key="venue", amount="30")[1].feasibility == "indeterminate"
    )


def test_foreign_scenario_children_and_bad_inputs_rejected(client):
    event = known_event(client)
    for parameters in [
        {"type": "vendor_cancellation", "vendor_id": str(uuid4())},
        {"type": "category_cost", "category_key": "venue", "expense_id": str(uuid4()), "amount": "5"},
        {"type": "additional_function", "category_key": "unknown", "name": "Test"},
    ]:
        with pytest.raises(HTTPException):
            run(event, **parameters)
    for parameters in [
        {"type": "guest_count", "guest_count": -1},
        {"type": "budget_reduction"},
        {"type": "budget_reduction", "amount": "0"},
        {"type": "category_cost", "category_key": "venue", "amount": "-1"},
    ]:
        with pytest.raises(ValidationError):
            run(event, **parameters)


def test_legacy_guest_assumptions_unpriced_categories_and_contract_floors(client):
    event = known_event(client)
    event.expenses[0].provenance = "legacy"
    assert run(event, type="guest_count", guest_count=50)[1].feasibility == "indeterminate"
    event.expenses[0].provenance = "manual"
    event.expenses[0].committed_amount = Decimal("100")
    event.expenses[0].paid_amount = Decimal("30")
    proposed, preview = run(event, type="category_cost", category_key="venue", amount="20")
    assert preview.feasibility == "indeterminate" and preview.proposed_budget.projected_cost == 100
    assert proposed.expenses[0].paid_amount == 30
    event.expenses = [record for record in event.expenses if record.category_key != "venue"]
    assert run(event, type="category_cost", category_key="venue", amount="50")[1].feasibility == "feasible"


def test_overdue_work_and_record_limits_remain_visible(client):
    event = known_event(client)
    event.plan.timeline[0].due = date.today() - timedelta(days=1)
    assert any(
        "Previously overdue" in warning
        for warning in run(
            event, type="event_date", event_date=(date.today() + timedelta(days=4)).isoformat()
        )[1].warnings
    )
    while len(event.expenses) < 200:
        event.expenses.append(event.expenses[0].model_copy(update={"id": uuid4()}))
    assert (
        run(event, type="additional_function", name="Too many", estimated_cost="0")[1].feasibility
        == "infeasible"
    )
