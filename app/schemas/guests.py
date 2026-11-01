"""Private event roster; planning headcount is a separately approved decision."""

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.planning import clean_text
from app.schemas.workspaces import EventWorkspace, StrictInput

RSVP = Literal["pending", "confirmed", "declined", "maybe"]
GuestGroup = Literal["Family", "Friends", "Colleagues", "VIP", "Other"]


class GuestValues(StrictInput):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(default="", max_length=254)
    group: GuestGroup = "Other"
    rsvp: RSVP = "pending"
    plus_ones: int = Field(default=0, ge=0, le=20, strict=True)
    dietary: str = Field(default="", max_length=300)
    accessibility: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=500)

    @field_validator("name", "email", "dietary", "accessibility", "notes", mode="before")
    @classmethod
    def _text(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def _email(cls, value: str | None) -> str | None:
        if value and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter an email address or leave it blank")
        return value


class Guest(GuestValues):
    id: UUID
    event_id: UUID
    created_at: datetime
    updated_at: datetime
    creation_fingerprint: str = ""


class GuestCreate(StrictInput):
    revision: int = Field(ge=1, strict=True)
    request_id: UUID
    guest: GuestValues


class GuestUpdate(StrictInput):
    revision: int = Field(ge=1, strict=True)
    guest: GuestValues


class GuestDelete(StrictInput):
    revision: int = Field(ge=1, strict=True)
    confirm_id: UUID


class GuestStats(StrictInput):
    records: int
    total_invited: int
    confirmed: int
    pending: int
    pending_responses: int
    declined: int
    maybe: int
    expected_attendees: int
    possible_attendees: int


class GuestList(StrictInput):
    event_id: UUID
    revision: int
    guests: list[Guest]
    stats: GuestStats


class GuestMutation(StrictInput):
    workspace: EventWorkspace
    roster: GuestList
