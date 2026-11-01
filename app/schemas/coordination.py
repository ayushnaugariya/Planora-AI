"""Bounded vendor editing; no browser-supplied financial or ownership fields."""

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.planning import clean_text
from app.schemas.workspaces import StrictInput


class VendorUpdate(StrictInput):
    revision: int = Field(ge=1, strict=True)
    name: str = Field(default="", max_length=80)
    contact: str = Field(default="", max_length=200)
    booking_status: Literal["unbooked", "shortlisted", "booked", "cancelled"]

    @field_validator("name", "contact", mode="before")
    @classmethod
    def _clean(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value
