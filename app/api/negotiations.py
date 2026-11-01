"""Owned generation and explicit private draft storage. No delivery/apply endpoint."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import Owner, current, repository
from app.repositories import negotiations
from app.schemas.negotiation import DraftSave, NegotiationDraft, NegotiationInput, NegotiationResult
from app.services.negotiation import generate

router = APIRouter(
    prefix="/api/events/{event_id}/vendors/{vendor_id}/negotiation", tags=["vendor negotiation drafts"]
)


@router.post("", response_model=NegotiationResult)
def generate_message(
    event_id: UUID, vendor_id: UUID, body: NegotiationInput, request: Request, owner: Owner
) -> NegotiationResult:
    return generate(
        current(request, owner, event_id, body.revision),
        vendor_id,
        body,
        getattr(request.app.state, "llm", None),
    )


@router.get("/draft", response_model=NegotiationDraft | None)
def get_draft(event_id: UUID, vendor_id: UUID, request: Request, owner: Owner) -> NegotiationDraft | None:
    return negotiations.read(repository(request), owner, event_id, vendor_id)


@router.put("/draft", response_model=NegotiationDraft)
def save_draft(
    event_id: UUID, vendor_id: UUID, body: DraftSave, request: Request, owner: Owner
) -> NegotiationDraft:
    return negotiations.save(repository(request), owner, event_id, vendor_id, body)
