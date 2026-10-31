"""Owned private roster CRUD. RSVP changes never silently change planning headcount."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.dependencies import Owner, repository
from app.core.errors import WorkspaceNotFound
from app.repositories import guests
from app.schemas.guests import (
    RSVP,
    Guest,
    GuestCreate,
    GuestDelete,
    GuestGroup,
    GuestList,
    GuestMutation,
    GuestUpdate,
)

router = APIRouter(prefix="/api/events/{event_id}/guests", tags=["private guest roster"])


@router.get("", response_model=GuestList)
def list_guests(
    event_id: UUID,
    request: Request,
    owner: Owner,
    q: Annotated[str, Query(max_length=120)] = "",
    rsvp: RSVP | None = None,
    group: GuestGroup | None = None,
):
    return guests.read(repository(request), owner, event_id, q, rsvp, group)


@router.get("/{guest_id}", response_model=Guest)
def get_guest(event_id: UUID, guest_id: UUID, request: Request, owner: Owner):
    result = guests.read(repository(request), owner, event_id)
    guest = next((item for item in result.guests if item.id == guest_id), None)
    if guest is None:
        raise WorkspaceNotFound
    return guest


@router.post("", response_model=GuestMutation, status_code=201)
def add_guest(event_id: UUID, body: GuestCreate, request: Request, owner: Owner):
    return guests.write(repository(request), owner, event_id, body)


@router.put("/{guest_id}", response_model=GuestMutation)
def edit_guest(event_id: UUID, guest_id: UUID, body: GuestUpdate, request: Request, owner: Owner):
    return guests.write(repository(request), owner, event_id, body, guest_id=guest_id)


@router.delete("/{guest_id}", response_model=GuestMutation)
def remove_guest(event_id: UUID, guest_id: UUID, body: GuestDelete, request: Request, owner: Owner):
    return guests.write(repository(request), owner, event_id, body, guest_id=guest_id, delete=True)
