"""Owned, revisioned expense operations backed by the existing workspace repository."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import Owner, current, repository
from app.core.errors import RevisionConflict, WorkspaceNotFound
from app.schemas.budget import (
    AllocationUpdate,
    BudgetSummary,
    BudgetWarning,
    ExpenseCreate,
    ExpenseDelete,
    ExpenseRecord,
    ExpenseUpdate,
    ExpenseValues,
)
from app.schemas.workspaces import EventWorkspace
from app.services.budget import calculate_budget, set_allocations, sync_budget
from app.services.workspaces import next_revision

router = APIRouter(prefix="/api/events/{event_id}/budget", tags=["budget"])


def find_expense(workspace: EventWorkspace, expense_id: UUID) -> ExpenseRecord:
    for item in workspace.expenses:
        if item.id == expense_id and item.event_id == workspace.id:
            return item
    raise WorkspaceNotFound


def validate_expense(workspace: EventWorkspace, values: ExpenseValues) -> None:
    if values.currency != workspace.details.currency:
        raise HTTPException(
            status_code=422, detail="Expense currency must match the event; conversion is not supported"
        )
    if values.category_key not in {line.key for line in workspace.plan.budget_lines}:
        raise HTTPException(status_code=422, detail="Choose an existing budget category")
    if values.vendor_id is not None and values.vendor_id not in {vendor.id for vendor in workspace.vendors}:
        raise HTTPException(status_code=422, detail="Vendor does not belong to this event")


def commit_budget(
    request: Request, owner: str, workspace: EventWorkspace, revision: int, summary: str
) -> EventWorkspace:
    sync_budget(workspace)
    next_revision(workspace, summary)
    return repository(request).save(owner, workspace, revision)


@router.get("", response_model=BudgetSummary)
def budget_summary(event_id: UUID, request: Request, owner: Owner) -> BudgetSummary:
    return calculate_budget(repository(request).get(owner, str(event_id)))


@router.get("/warnings", response_model=list[BudgetWarning])
def budget_warnings(event_id: UUID, request: Request, owner: Owner) -> list[BudgetWarning]:
    return budget_summary(event_id, request, owner).warnings


@router.get("/expenses", response_model=list[ExpenseRecord])
def list_expenses(event_id: UUID, request: Request, owner: Owner) -> list[ExpenseRecord]:
    return repository(request).get(owner, str(event_id)).expenses


@router.get("/expenses/{expense_id}", response_model=ExpenseRecord)
def get_expense(event_id: UUID, expense_id: UUID, request: Request, owner: Owner) -> ExpenseRecord:
    return find_expense(repository(request).get(owner, str(event_id)), expense_id)


@router.post("/expenses", response_model=EventWorkspace, status_code=201)
def add_expense(event_id: UUID, body: ExpenseCreate, request: Request, owner: Owner) -> EventWorkspace:
    workspace = repository(request).get(owner, str(event_id))
    fingerprint = hashlib.sha256(body.expense.model_dump_json().encode()).hexdigest()
    existing = next((item for item in workspace.expenses if item.id == body.request_id), None)
    if existing:
        if existing.creation_fingerprint != fingerprint:
            raise RevisionConflict
        return workspace
    if workspace.revision != body.revision:
        raise RevisionConflict
    validate_expense(workspace, body.expense)
    if len(workspace.expenses) >= 200:
        raise HTTPException(status_code=422, detail="This workspace supports at most 200 expense records")
    record = ExpenseRecord(
        **body.expense.model_dump(),
        event_id=workspace.id,
        id=body.request_id,
        creation_fingerprint=fingerprint,
        priced_for_guests=workspace.details.guest_count,
    )
    workspace.expenses.append(record)
    return commit_budget(
        request, owner, workspace, body.revision, f"Added expense {record.id}: {record.description}"
    )


@router.put("/expenses/{expense_id}", response_model=EventWorkspace)
def edit_expense(
    event_id: UUID, expense_id: UUID, body: ExpenseUpdate, request: Request, owner: Owner
) -> EventWorkspace:
    workspace = current(request, owner, event_id, body.revision)
    old = find_expense(workspace, expense_id)
    validate_expense(workspace, body.expense)
    if body.expense.paid_amount < old.paid_amount:
        raise HTTPException(
            status_code=422, detail="Refunds/payment reversals are not supported; paid totals cannot decrease"
        )
    record = ExpenseRecord(
        **body.expense.model_dump(),
        id=old.id,
        event_id=workspace.id,
        created_at=old.created_at,
        updated_at=datetime.now(UTC),
        provenance="manual",
        creation_fingerprint=old.creation_fingerprint,
        priced_for_guests=workspace.details.guest_count,
        cancelled=old.cancelled,
    )
    workspace.expenses[workspace.expenses.index(old)] = record
    return commit_budget(
        request,
        owner,
        workspace,
        body.revision,
        (
            f"Updated expense {record.id}; estimate {old.estimate} to {record.estimate}; "
            f"quote {old.quoted_amount} to {record.quoted_amount}; "
            f"commitment {old.committed_amount} to {record.committed_amount}; "
            f"paid {old.paid_amount} to {record.paid_amount}"
        ),
    )


@router.delete("/expenses/{expense_id}", response_model=EventWorkspace)
def delete_expense(
    event_id: UUID, expense_id: UUID, body: ExpenseDelete, request: Request, owner: Owner
) -> EventWorkspace:
    workspace = current(request, owner, event_id, body.revision)
    old = find_expense(workspace, expense_id)
    if body.confirm_id != expense_id:
        raise HTTPException(status_code=422, detail="Confirm the expense ID before deleting the record")
    workspace.expenses.remove(old)
    return commit_budget(
        request,
        owner,
        workspace,
        body.revision,
        f"Deleted expense record {old.id}; removed paid record {old.paid_amount} (not a refund)",
    )


@router.patch("/allocations", response_model=EventWorkspace)
def update_allocations(
    event_id: UUID, body: AllocationUpdate, request: Request, owner: Owner
) -> EventWorkspace:
    workspace = current(request, owner, event_id, body.revision)
    original = {line.key: line.amount for line in workspace.plan.budget_lines}
    set_allocations(workspace, body.allocations)
    return commit_budget(
        request,
        owner,
        workspace,
        body.revision,
        "Updated explicit allocations; no rebalance: "
        + "; ".join(f"{item.key} {original.get(item.key, 0)} to {item.amount}" for item in body.allocations),
    )
