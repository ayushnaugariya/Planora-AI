"""One authoritative Decimal reconciliation service for saved events and scenarios."""

from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException

from app.schemas.budget import Allocation, BudgetSummary, BudgetWarning, CategorySummary, ExpenseRecord, cents
from app.schemas.planning import BudgetLine
from app.schemas.workspaces import EventWorkspace
from app.services import engine

ZERO = Decimal("0.00")


def effective_cost(expense: ExpenseRecord) -> Decimal:
    if expense.cancelled:
        return max(expense.paid_amount, expense.committed_amount or ZERO)
    preferred = expense.committed_amount
    if preferred is None:
        preferred = expense.quoted_amount
    if preferred is None:
        preferred = expense.estimate
    if preferred is None:
        preferred = expense.tax + expense.fee
    return max(expense.paid_amount, preferred or ZERO)


def calculate_budget(workspace: EventWorkspace) -> BudgetSummary:
    categories = []
    warnings = []
    unknown = []
    missing = []
    lines = list(workspace.plan.budget_lines)
    known_keys = {line.key for line in lines}
    for item in workspace.expenses:
        if item.category_key not in known_keys:
            lines.append(
                BudgetLine(key=item.category_key, label=item.category_key, amount=0, percent=0, per_guest=0)
            )
            known_keys.add(item.category_key)
            warnings.append(
                BudgetWarning(
                    code="unallocated_category",
                    category_key=item.category_key,
                    expense_ids=[item.id],
                    message=(
                        f"Expense category {item.category_key} has no allocation; "
                        "its costs are still counted."
                    ),
                )
            )
    for line in lines:
        records = [item for item in workspace.expenses if item.category_key == line.key]
        active = [item for item in records if not item.cancelled]
        estimated = sum((item.estimate or ZERO for item in active), ZERO)
        quoted = sum((item.quoted_amount or ZERO for item in active), ZERO)
        committed = sum((item.committed_amount or ZERO for item in records), ZERO)
        paid = sum((item.paid_amount for item in records), ZERO)
        projected = sum((effective_cost(item) for item in records), ZERO)
        if (
            line.key != "contingency"
            and (line.amount > 0 or line.key in ("venue", "catering"))
            and not active
        ):
            missing.append(line.key)
            warnings.append(
                BudgetWarning(
                    code="missing_cost",
                    category_key=line.key,
                    message=f"{line.label}: no active cost records; affordability is unknown.",
                )
            )
        if projected > line.amount:
            warnings.append(
                BudgetWarning(
                    code="category_overrun",
                    category_key=line.key,
                    expense_ids=[item.id for item in records],
                    message=(
                        f"{line.label}: projected {projected} exceeds allocation {line.amount} "
                        f"by {projected - line.amount}."
                    ),
                )
            )
        for item in active:
            if item.estimate is None and item.quoted_amount is None and item.committed_amount is None:
                unknown.append(item.id)
                warnings.append(
                    BudgetWarning(
                        code="unknown_expense",
                        expense_ids=[item.id],
                        category_key=line.key,
                        message=(
                            f"{item.description}: final cost is unknown; "
                            f"paid {item.paid_amount} is only a floor."
                        ),
                    )
                )
            if item.estimate is not None and item.quoted_amount is not None:
                difference = item.quoted_amount - item.estimate
                if abs(difference) >= max(Decimal(1), item.estimate * Decimal("0.20")):
                    warnings.append(
                        BudgetWarning(
                            code="quote_difference",
                            expense_ids=[item.id],
                            category_key=line.key,
                            message=(
                                f"{item.description}: quote {item.quoted_amount} differs "
                                f"from estimate {item.estimate} by {difference}."
                            ),
                        )
                    )
            if item.committed_amount is not None and item.paid_amount > item.committed_amount:
                warnings.append(
                    BudgetWarning(
                        code="overpaid",
                        expense_ids=[item.id],
                        category_key=line.key,
                        message=(
                            f"{item.description}: paid {item.paid_amount} exceeds "
                            f"commitment {item.committed_amount}."
                        ),
                    )
                )
            reference = item.quoted_amount if item.quoted_amount is not None else item.estimate
            if item.committed_amount is not None and reference is not None:
                difference = item.committed_amount - reference
                if abs(difference) >= max(Decimal(1), reference * Decimal("0.20")):
                    warnings.append(
                        BudgetWarning(
                            code="commitment_difference",
                            expense_ids=[item.id],
                            category_key=line.key,
                            message=(
                                f"{item.description}: commitment {item.committed_amount} "
                                f"differs from prior price {reference} by {difference}."
                            ),
                        )
                    )
            if (
                item.committed_amount is None
                and reference is not None
                and item.paid_amount - reference >= max(Decimal(1), reference * Decimal("0.20"))
            ):
                warnings.append(
                    BudgetWarning(
                        code="paid_exceeds_price",
                        expense_ids=[item.id],
                        category_key=line.key,
                        message=(
                            f"{item.description}: paid {item.paid_amount} "
                            f"exceeds prior price {reference} by {item.paid_amount - reference}."
                        ),
                    )
                )
            if (
                item.cost_basis == "per_guest"
                and item.priced_for_guests != workspace.details.guest_count
                and (
                    item.quoted_amount is not None
                    or item.committed_amount is not None
                    or item.estimated_amount is not None
                )
            ):
                unknown.append(item.id)
                warnings.append(
                    BudgetWarning(
                        code="reconfirm_price",
                        expense_ids=[item.id],
                        category_key=line.key,
                        message=(
                            f"{item.description}: all-in estimate/quote/commitment needs "
                            f"reconfirming for {workspace.details.guest_count} guests."
                        ),
                    )
                )
        categories.append(
            CategorySummary(
                key=line.key,
                label=line.label,
                allocation=Decimal(line.amount),
                estimated=estimated,
                quoted=quoted,
                committed=committed,
                paid=paid,
                projected=projected,
                remaining=Decimal(line.amount) - projected,
                expense_ids=[item.id for item in records],
                per_guest_allocation=cents(Decimal(line.amount) / workspace.details.guest_count),
            )
        )
    total = Decimal(workspace.details.budget)
    allocated = sum((item.allocation for item in categories), ZERO)
    projected = sum((item.projected for item in categories), ZERO)
    reserve = next((item.allocation for item in categories if item.key == "contingency"), ZERO)
    reserve_used = next((item.projected for item in categories if item.key == "contingency"), ZERO)
    remaining_reserve = max(ZERO, reserve - reserve_used)
    if allocated > total:
        warnings.append(
            BudgetWarning(
                code="overallocated",
                message=f"Allocation {allocated} exceeds budget {total} by {allocated - total}.",
            )
        )
    if projected > total:
        warnings.append(
            BudgetWarning(
                code="overspent",
                message=f"Projected spending {projected} exceeds budget {total} by {projected - total}.",
            )
        )
    if projected + remaining_reserve > total:
        warnings.append(
            BudgetWarning(
                code="reserve_shortfall",
                message=(
                    "Projected spending plus protected reserve exceeds budget by "
                    f"{projected + remaining_reserve - total}."
                ),
            )
        )
    paid = sum((item.paid for item in categories), ZERO)
    return BudgetSummary(
        currency=workspace.details.currency,
        total_budget=total,
        planned_allocation=allocated,
        estimated_cost=sum((item.estimated for item in categories), ZERO),
        quoted_cost=sum((item.quoted for item in categories), ZERO),
        committed_spending=sum((item.committed for item in categories), ZERO),
        actual_spending=paid,
        outstanding_commitments=sum(
            (max(ZERO, (item.committed_amount or ZERO) - item.paid_amount) for item in workspace.expenses),
            ZERO,
        ),
        projected_cost=projected,
        unallocated_funds=total - allocated,
        remaining_funds=total - projected,
        cash_remaining=total - paid,
        contingency_reserve=reserve,
        contingency_remaining=remaining_reserve,
        spendable_remaining=total - projected - remaining_reserve,
        categories=categories,
        warnings=warnings,
        missing_categories=missing,
        unknown_expenses=list(dict.fromkeys(unknown)),
        planned_per_guest=cents(allocated / workspace.details.guest_count),
    )


def set_allocations(workspace: EventWorkspace, allocations: list[Allocation]) -> None:
    keys = [item.key for item in allocations]
    if len(set(keys)) != len(keys):
        raise HTTPException(status_code=422, detail="Allocation keys must be unique")
    old = {item.key: item for item in workspace.plan.budget_lines}
    for item in allocations:
        if item.key in old:
            old[item.key].amount = item.amount
            old[item.key].label = item.label
        else:
            workspace.plan.budget_lines.append(
                BudgetLine(key=item.key, label=item.label, amount=item.amount, percent=0, per_guest=0)
            )
    workspace.allocations_manual = True


def sync_budget(
    workspace: EventWorkspace, *, refresh_narrative: bool = True, mutation_time: datetime | None = None
) -> None:
    """Synchronize all legacy derived display fields without changing allocations."""
    plan = workspace.plan
    plan.budget, plan.currency, plan.guest_count = (
        workspace.details.budget,
        workspace.details.currency,
        workspace.details.guest_count,
    )
    plan.per_guest = float(cents(Decimal(plan.budget) / plan.guest_count))
    for line in plan.budget_lines:
        line.percent = float((Decimal(line.amount) * 100 / plan.budget).quantize(Decimal("0.1")))
        line.per_guest = float(cents(Decimal(line.amount) / plan.guest_count))
    amounts = {line.key: line.amount for line in plan.budget_lines}
    for vendor in plan.vendors:
        vendor.budget = amounts[vendor.key]
    for expense in workspace.expenses:
        if expense.cost_basis == "per_guest" and expense.quantity != Decimal(plan.guest_count):
            expense.quantity = Decimal(plan.guest_count)
            expense.updated_at = mutation_time or datetime.now(UTC)
    plan.health_score, plan.warnings = engine.assess(
        workspace.details, date.today(), plan.timeline_compressed, plan.days_until
    )
    if refresh_narrative:
        core = engine.Core(
            days_until=plan.days_until,
            per_guest=plan.per_guest,
            health_score=plan.health_score,
            compressed=plan.timeline_compressed,
            warnings=plan.warnings,
            budget=plan.budget_lines,
            timeline=plan.timeline,
            vendors=plan.vendors,
        )
        extras = engine.fallback_extras(workspace.details, core)
        summary = calculate_budget(workspace)
        plan.summary = (
            f"Budget {summary.total_budget} {plan.currency}. "
            f"Projected recorded cost {summary.projected_cost}; "
            f"paid {summary.actual_spending}; remaining {summary.remaining_funds}. "
            + (
                "Pricing is incomplete; affordability is not established."
                if summary.missing_categories or summary.unknown_expenses
                else "Amounts reflect recorded costs; confirm assumptions with vendors."
            )
        )
        plan.ideas, plan.tips, plan.ai_source = extras.ideas, extras.tips, "offline"
