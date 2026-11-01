"""Owned, revision-checked edits of existing vendor records."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import Owner, current, repository
from app.schemas.coordination import VendorUpdate
from app.schemas.workspaces import EventWorkspace
from app.services.workspaces import next_revision

router = APIRouter(prefix="/api/events/{event_id}/vendors", tags=["vendors"])


@router.patch("/{vendor_id}", response_model=EventWorkspace)
def update_vendor(
    event_id: UUID, vendor_id: UUID, body: VendorUpdate, request: Request, owner: Owner
) -> EventWorkspace:
    event = current(request, owner, event_id, body.revision)
    vendor = next((item for item in event.vendors if item.id == vendor_id), None)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor is not in this event")
    vendor.name, vendor.contact, vendor.booking_status = body.name, body.contact, body.booking_status
    next_revision(event, "Vendor contact and booking status updated")
    return repository(request).save(owner, event, body.revision)
