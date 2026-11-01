"""Isolated deterministic simulations. This module never writes or calls Gemini."""

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID, uuid5

from fastapi import HTTPException

from app.schemas.budget import ExpenseRecord
from app.schemas.scenarios import (
    AdditionalFunction,
    BudgetReduction,
    CategoryCost,
    DateChange,
    ExpenseChange,
    GuestChange,
    Scenario,
    ScenarioParameters,
    TaskImpact,
    VendorCancellation,
)
from app.schemas.workspaces import EventWorkspace
from app.services import engine
from app.services.budget import calculate_budget, set_allocations, sync_budget
from app.services.workspaces import reconcile


def dependency_reasons(workspace: EventWorkspace) -> list[str]:
    tasks = {task.id: task for task in workspace.tasks}
    reasons = []
    visited, visiting = set(), set()

    def visit(task_id: UUID) -> None:
        if task_id in visiting:
            reasons.append("Task dependencies contain a cycle.")
            return
        if task_id in visited:
            return
        visiting.add(task_id)
        task = tasks[task_id]
        for prerequisite in task.depends_on:
            if prerequisite not in tasks:
                reasons.append(f"Task {task_id} references missing prerequisite {prerequisite}.")
                continue
            earlier = tasks[prerequisite]
            if task.completed and not earlier.completed:
                reasons.append(f"Completed task {task_id} has an unfinished prerequisite.")
            if (
                not earlier.completed
                and not task.completed
                and workspace.plan.timeline[earlier.milestone_index].due
                > workspace.plan.timeline[task.milestone_index].due
            ):
                reasons.append(f"Task {task_id} is scheduled before its prerequisite {prerequisite}.")
            visit(prerequisite)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in tasks:
        visit(task_id)
    return list(dict.fromkeys(reasons))


def values(workspace: EventWorkspace) -> dict[str, object]:
    return {
        "budget": workspace.details.budget,
        "guest_count": workspace.details.guest_count,
        "event_date": workspace.details.event_date.isoformat(),
        "vendors": {str(vendor.id): vendor.booking_status for vendor in workspace.vendors},
        "allocations": {line.key: line.amount for line in workspace.plan.budget_lines},
    }


def simulate(
    base: EventWorkspace,
    parameters: ScenarioParameters,
    scenario_id: UUID,
    created_at: datetime,
    today: date | None = None,
) -> tuple[EventWorkspace, Scenario]:
    today = today or date.today()
    proposed = base.model_copy(deep=True)
    reasons = dependency_reasons(base)
    unresolved = []
    warnings = []
    affected_categories = set()

    def new_expense(category: str, description: str, amount: Decimal | None, suffix: str) -> ExpenseRecord:
        if category not in {line.key for line in proposed.plan.budget_lines}:
            raise HTTPException(status_code=422, detail="Scenario category does not belong to this event")
        expense = ExpenseRecord(
            id=uuid5(scenario_id, suffix),
            event_id=base.id,
            category_key=category,
            description=description,
            currency=base.details.currency,
            unit_amount=amount,
            provenance="scenario",
            created_at=created_at,
            updated_at=created_at,
        )
        proposed.expenses.append(expense)
        return expense

    if isinstance(parameters, BudgetReduction):
        reduction = (
            parameters.amount
            if parameters.amount is not None
            else Decimal(base.details.budget) * parameters.percent / 100
        )
        proposed.details.budget = int(
            (Decimal(base.details.budget) - reduction).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        )
        if parameters.allocations is not None:
            set_allocations(proposed, parameters.allocations)
        proposed.allocations_manual = True
        warnings.append(
            "Budget target is rounded to whole units. Allocations change only when explicitly supplied."
        )
        adjustable = [line.label for line in base.plan.budget_lines if line.key != "contingency"]
        warnings.append("Review adjustable allowances without automatic changes: " + ", ".join(adjustable))
    elif isinstance(parameters, GuestChange):
        proposed.details.guest_count = parameters.guest_count
        if any(expense.provenance == "legacy" and not expense.cancelled for expense in base.expenses):
            unresolved.append(
                "Legacy amounts have no explicit guest-cost model; reconfirm them by editing the records."
            )
        warnings.append(
            "Only explicit per-guest quantities scale; fixed costs, quotes, "
            "commitments and paid totals are retained."
        )
    elif isinstance(parameters, DateChange):
        proposed.details.event_date = parameters.event_date
        if any(vendor.booking_status == "booked" for vendor in base.vendors):
            unresolved.append(
                "Booked vendors must reconfirm the proposed date; availability has not been checked."
            )
    elif isinstance(parameters, CategoryCost):
        candidates = [
            expense
            for expense in proposed.expenses
            if expense.category_key == parameters.category_key and not expense.cancelled
        ]
        target = (
            next((item for item in candidates if item.id == parameters.expense_id), None)
            if parameters.expense_id
            else (candidates[0] if len(candidates) == 1 else None)
        )
        if parameters.expense_id and target is None:
            raise HTTPException(status_code=404, detail="Expense is not in this event/category")
        if not candidates:
            new_expense(
                parameters.category_key,
                f"Hypothetical {parameters.category_key} cost",
                parameters.amount,
                "category",
            )
        elif target is None:
            unresolved.append("Choose the specific expense ID when a category has multiple records.")
        else:
            target.quoted_amount = parameters.amount
            target.updated_at = created_at
            target.provenance = "scenario"
            if max(target.committed_amount or 0, target.paid_amount) > parameters.amount:
                unresolved.append(
                    "Existing commitment/payment exceeds the hypothetical quote "
                    "and is not released by this scenario."
                )
        affected_categories.add(parameters.category_key)
    elif isinstance(parameters, AdditionalFunction):
        new_expense(parameters.category_key, parameters.name, parameters.estimated_cost, "function")
        affected_categories.add(parameters.category_key)
        if parameters.estimated_cost is None:
            unresolved.append("Additional function has no supplied pricing assumption.")
    elif isinstance(parameters, VendorCancellation):
        vendor = next((vendor for vendor in proposed.vendors if vendor.id == parameters.vendor_id), None)
        if vendor is None:
            raise HTTPException(status_code=404, detail="Vendor is not in this event")
        vendor.booking_status = "cancelled"
        category = proposed.plan.vendors[vendor.group_index].key
        affected_categories.add(category)
        for expense in proposed.expenses:
            if expense.vendor_id == vendor.id:
                expense.cancelled = True
                if expense.committed_amount or expense.paid_amount:
                    unresolved.append(
                        "Cancelled vendor has paid/committed exposure; "
                        "contractual release or refund is unconfirmed."
                    )
        if parameters.cancellation_fee is None or parameters.replacement_cost is None:
            unresolved.append(
                "Cancellation fee and replacement price are required assumptions; no price is invented."
            )
        else:
            new_expense(
                category,
                "Replacement and cancellation fee (user assumption)",
                parameters.cancellation_fee + parameters.replacement_cost,
                "replacement",
            )
        if not parameters.replacement_confirmed:
            unresolved.append(
                "Replacement availability is not confirmed by the user; "
                "no live vendor availability is claimed."
            )

    valid_budget = 1000 <= proposed.details.budget <= 100_000_000
    if len(proposed.expenses) > 200:
        reasons.append("Scenario would exceed the 200-expense workspace limit.")
    valid_date = today <= proposed.details.event_date <= today + timedelta(days=365 * 3)
    if not valid_budget:
        reasons.append("Proposed budget is outside the supported 1,000–100,000,000 whole-unit range.")
    if isinstance(parameters, DateChange) and not valid_date:
        reasons.append("Proposed event date must be today through the next three years.")
    if valid_date and (isinstance(parameters, (GuestChange, DateChange))):
        core = engine.compute(proposed.details, today)
        proposed.plan.days_until, proposed.plan.health_score = core.days_until, core.health_score
        proposed.plan.timeline_compressed, proposed.plan.warnings = core.compressed, core.warnings
        proposed.plan.event_date, proposed.plan.timeline = proposed.details.event_date, core.timeline
        proposed.plan.vendors = engine.build_vendors(proposed.details, proposed.plan.budget_lines, today)
        proposed.tasks, proposed.vendors = reconcile(base, proposed.plan)
    if valid_budget:
        sync_budget(proposed, mutation_time=created_at)
    summary = calculate_budget(proposed)
    fatal_codes = {"overallocated", "overspent", "category_overrun", "reserve_shortfall"}
    reasons.extend(w.message for w in summary.warnings if w.code in fatal_codes)
    if summary.missing_categories or summary.unknown_expenses:
        unresolved.append(
            "Essential/allocated costs are missing or require reconfirmation; "
            "arithmetic alone cannot establish feasibility."
        )
    reasons.extend(dependency_reasons(proposed))
    impacted = (
        {
            task.id
            for task in proposed.tasks
            if proposed.plan.timeline[task.milestone_index].category in affected_categories | {"vendors"}
        }
        if affected_categories
        else set()
    )
    while True:
        expanded = impacted | {task.id for task in proposed.tasks if set(task.depends_on) & impacted}
        if expanded == impacted:
            break
        impacted = expanded
    original_tasks = {task.id: task for task in base.tasks}
    effects = []
    for task in proposed.tasks:
        old_task = original_tasks[task.id]
        old = base.plan.timeline[old_task.milestone_index]
        new = proposed.plan.timeline[task.milestone_index]
        if old.due != new.due or task.id in impacted:
            effects.append(
                TaskImpact(
                    id=task.id,
                    title=new.title,
                    original_due=old.due,
                    proposed_due=new.due,
                    completed=task.completed,
                    dependencies=task.depends_on,
                )
            )
        if not task.completed and new.category != "event":
            if old.due < today:
                warnings.append(f"Previously overdue task: {old.title} ({old.due}).")
            if new.due <= today + timedelta(days=2):
                warnings.append(f"Urgent unfinished task: {new.title} ({new.due}).")
    old_expenses = {item.id: item for item in base.expenses}
    for item in proposed.expenses:
        if item.id in old_expenses and item.model_dump() != old_expenses[item.id].model_dump():
            item.updated_at, item.provenance = created_at, "scenario"
    changes = [
        ExpenseChange(id=item.id, before=old_expenses.get(item.id), after=item)
        for item in proposed.expenses
        if item.model_dump() != (old_expenses[item.id].model_dump() if item.id in old_expenses else None)
    ]
    reasons, unresolved = list(dict.fromkeys(reasons)), list(dict.fromkeys(unresolved))
    preview = Scenario(
        id=scenario_id,
        event_id=base.id,
        base_revision=base.revision,
        created_at=created_at,
        evaluated_on=today,
        parameters=parameters,
        original_values=values(base),
        proposed_values=values(proposed),
        original_budget=calculate_budget(base),
        proposed_budget=summary,
        budget_impact={
            key: getattr(summary, key) - getattr(calculate_budget(base), key)
            for key in ("total_budget", "projected_cost", "remaining_funds", "actual_spending")
        },
        expense_changes=changes,
        affected_tasks=effects,
        warnings=list(dict.fromkeys(warnings + unresolved + [w.message for w in summary.warnings])),
        reasons=reasons + unresolved,
        feasibility="infeasible" if reasons else "indeterminate" if unresolved else "feasible",
    )
    return proposed, preview
