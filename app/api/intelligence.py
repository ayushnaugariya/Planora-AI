"""Integrated read-only intelligence and explicitly reviewed quote/design recording."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.api.budget import commit_budget, find_expense, validate_expense
from app.api.dependencies import Owner, current, repository
from app.core.errors import RevisionConflict
from app.repositories.design_preferences import read_preferred, save_preferred
from app.schemas.budget import ExpenseRecord, ExpenseValues
from app.schemas.intelligence import (
    DecisionRequest,
    DecisionResponse,
    DelayAnalysis,
    DelayRequest,
    DesignRequest,
    DesignSave,
    DesignStudio,
    PreferredDesign,
    QuoteAnalysis,
    QuoteImport,
    QuoteRequest,
)
from app.schemas.workspaces import EventWorkspace
from app.services.decisions import decide
from app.services.design import concept, studio
from app.services.quote_analysis import analyze_quote
from app.services.timeline_intelligence import delay_analysis

router = APIRouter(prefix="/api/events/{event_id}/intelligence", tags=["event intelligence"])


@router.post("/decide", response_model=DecisionResponse)
def decision(event_id: UUID, body: DecisionRequest, request: Request, owner: Owner) -> DecisionResponse:
    base = current(request, owner, event_id, body.revision)
    return decide(base, body.question, getattr(request.app.state, "llm", None))


def quote_context(
    request: Request, owner: str, event_id: UUID, body: QuoteRequest | QuoteImport
) -> EventWorkspace:
    base = current(request, owner, event_id, body.revision)
    validate_expense(
        base,
        ExpenseValues(
            category_key=body.category_key,
            description="Quote analysis",
            currency=base.details.currency,
            vendor_id=body.vendor_id,
        ),
    )
    if body.vendor_id is not None:
        vendor = next(item for item in base.vendors if item.id == body.vendor_id)
        if base.plan.vendors[vendor.group_index].key != body.category_key:
            raise HTTPException(status_code=422, detail="Choose a vendor in the selected service category")
    return base


@router.post("/quotes/analyze", response_model=QuoteAnalysis)
def quote_analysis(event_id: UUID, body: QuoteRequest, request: Request, owner: Owner) -> QuoteAnalysis:
    return analyze_quote(quote_context(request, owner, event_id, body), body)


@router.post("/quotes/record", response_model=EventWorkspace)
def record_quote(event_id: UUID, body: QuoteImport, request: Request, owner: Owner) -> EventWorkspace:
    if not body.approved:
        raise HTTPException(status_code=422, detail="Review the source and explicitly approve recording")
    base = repository(request).get(owner, str(event_id))
    fingerprint = hashlib.sha256(
        body.model_dump_json(exclude={"revision", "request_id", "approved"}).encode()
    ).hexdigest()
    prefix = f"Reviewed quote {body.request_id}: "
    marker = prefix + fingerprint
    prior = next((entry for entry in base.history if entry.summary.startswith(prefix)), None)
    if prior:
        if prior.summary != marker:
            raise RevisionConflict
        return base
    base = quote_context(request, owner, event_id, body)
    analysis = analyze_quote(base, body)
    if not analysis.importable:
        raise HTTPException(
            status_code=422, detail="Resolve quote inconsistencies and missing costs before recording"
        )
    old = find_expense(base, body.expense_id) if body.expense_id else None
    candidates = [
        item for item in base.expenses if item.category_key == body.category_key and not item.cancelled
    ]
    if old is None and candidates:
        raise HTTPException(
            status_code=422, detail="Select an existing expense to avoid counting its cost twice"
        )
    if old and (old.category_key != body.category_key or old.cancelled):
        raise HTTPException(status_code=422, detail="Choose an active expense in the selected category")
    values = (
        ExpenseValues.model_validate(old.model_dump(include=set(ExpenseValues.model_fields)))
        if old
        else ExpenseValues(
            category_key=body.category_key,
            description=f"Reviewed quote: {analysis.vendor_name or body.filename}"[:150],
            currency=base.details.currency,
        )
    )
    if (
        body.record_as == "commitment"
        and old
        and old.committed_amount is not None
        and analysis.comparable_total < old.committed_amount
    ):
        raise HTTPException(status_code=422, detail="Existing commitment cannot be silently reduced")
    values.quoted_amount = analysis.comparable_total
    if body.record_as == "commitment":
        values.committed_amount = analysis.comparable_total
    # A quoted deposit is a payment condition, never evidence of money paid.
    values.vendor_id = body.vendor_id if body.vendor_id is not None else values.vendor_id
    review_note = f"Reviewed {body.filename}; SHA256 {analysis.source_hash}. Source excerpt: {body.text}"
    values.notes = ((values.notes + "\n" if values.notes else "") + review_note)[:500]
    record = ExpenseRecord(
        **values.model_dump(),
        id=old.id if old else body.request_id,
        event_id=base.id,
        created_at=old.created_at if old else datetime.now(UTC),
        priced_for_guests=base.details.guest_count,
        creation_fingerprint=old.creation_fingerprint
        if old
        else hashlib.sha256(values.model_dump_json().encode()).hexdigest(),
    )
    if old:
        base.expenses[base.expenses.index(old)] = record
    else:
        if len(base.expenses) >= 200 or any(item.id == record.id for item in base.expenses):
            raise HTTPException(status_code=422, detail="Expense capacity or request identity conflict")
        base.expenses.append(record)
    return commit_budget(request, owner, base, body.revision, marker)


@router.post("/design", response_model=DesignStudio)
def design(event_id: UUID, body: DesignRequest, request: Request, owner: Owner) -> DesignStudio:
    return studio(
        current(request, owner, event_id, body.revision),
        body.brief,
        getattr(request.app.state, "llm", None),
        body.colors,
    )


@router.get("/design/preferred", response_model=PreferredDesign | None)
def preferred(event_id: UUID, request: Request, owner: Owner) -> PreferredDesign | None:
    return read_preferred(repository(request), owner, event_id)


@router.post("/design/preferred", response_model=PreferredDesign)
def prefer(event_id: UUID, body: DesignSave, request: Request, owner: Owner) -> PreferredDesign:
    if not body.approved:
        raise HTTPException(status_code=422, detail="Explicit design confirmation is required")
    base = current(request, owner, event_id, body.revision)
    result = PreferredDesign(
        event_id=base.id,
        base_revision=base.revision,
        brief=body.brief,
        concept=concept(base, body.style, body.colors),
    )
    return save_preferred(repository(request), owner, result)


@router.post("/timeline", response_model=DelayAnalysis)
def timeline(event_id: UUID, body: DelayRequest, request: Request, owner: Owner) -> DelayAnalysis:
    return delay_analysis(current(request, owner, event_id, body.revision), body)
