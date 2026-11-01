"""Separate private drafts and allowlisted public invitation contracts."""

from datetime import date, datetime
from typing import Literal, Self
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, Field, field_validator, model_validator

from app.schemas.guests import RSVP, GuestValues
from app.schemas.planning import EventType, clean_text
from app.schemas.workspaces import StrictInput

Theme = Literal["ethereal", "modern_minimal", "celebration", "editorial_luxe"]
Artwork = Literal["none", "botanical", "celebration", "venue"]


class WebsiteText(StrictInput):
    @field_validator("*", mode="before")
    @classmethod
    def clean(cls, value: object) -> object:
        if isinstance(value, str):
            value.encode("utf-8")
            return clean_text(value)
        return value


class ScheduleItem(WebsiteText):
    title: str = Field(min_length=1, max_length=120)
    date: date
    start_at: AwareDatetime | None = None


class WebsiteConfig(WebsiteText):
    theme: Theme = "ethereal"
    accent: str = Field(default="#7863b4", pattern=r"^#[0-9a-fA-F]{6}$")
    event_type: EventType
    title: str = Field(min_length=1, max_length=120)
    subtitle: str = Field(default="", max_length=160)
    event_date: date
    start_at: AwareDatetime | None = None
    timezone: str = Field(default="UTC", min_length=1, max_length=80)
    welcome: str = Field(default="You're invited", max_length=160)
    invitation: str = Field(min_length=2, max_length=1200)
    description: str = Field(default="", max_length=1000)
    hosts: str = Field(default="", max_length=160)
    venue_name: str = Field(default="", max_length=160)
    venue_address: str = Field(default="", max_length=300)
    city: str = Field(default="", max_length=60)
    dress_code: str = Field(default="", max_length=240)
    rsvp_instructions: str = Field(default="Please share your response with the host.", max_length=300)
    show_hosts: bool = Field(default=False, strict=True)
    show_venue: bool = Field(default=False, strict=True)
    show_schedule: bool = Field(default=False, strict=True)
    show_dress_code: bool = Field(default=False, strict=True)
    show_gallery: bool = Field(default=False, strict=True)
    rsvp_enabled: bool = Field(default=False, strict=True)
    rsvp_email_required: bool = Field(default=True, strict=True)
    max_attendees: int = Field(default=1, ge=1, le=21, strict=True)
    schedule: list[ScheduleItem] = Field(default_factory=list, max_length=30)
    cover: Artwork = "none"
    gallery: list[Artwork] = Field(default_factory=list, max_length=3)

    @field_validator("timezone")
    @classmethod
    def valid_zone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Use an installed IANA timezone") from exc
        return value

    @model_validator(mode="after")
    def consistent_time(self) -> Self:
        if self.start_at and self.start_at.astimezone(ZoneInfo(self.timezone)).date() != self.event_date:
            raise ValueError("Start time must match the event date in the selected timezone")
        return self


class PublicVenue(StrictInput):
    name: str
    address: str
    city: str


class PublicRSVP(StrictInput):
    enabled: bool
    email_required: bool
    max_attendees: int
    instructions: str


class PublicWebsite(StrictInput):
    """Never inherit the workspace, guest, draft or operational model."""

    edition: str
    theme: Theme
    accent: str
    event_type: EventType
    title: str
    subtitle: str
    event_date: date
    start_at: AwareDatetime | None
    timezone: str
    welcome: str
    invitation: str
    description: str
    hosts: str | None
    venue: PublicVenue | None
    dress_code: str | None
    schedule: list[ScheduleItem]
    cover: Artwork
    gallery: list[Artwork]
    rsvp: PublicRSVP


class WebsiteRecord(StrictInput):
    format_version: Literal[1] = 1
    event_id: UUID
    revision: int = Field(ge=1)
    saved_event_revision: int
    slug: str = Field(pattern=r"^[A-Za-z0-9_-]{32}$")
    draft: WebsiteConfig
    published: PublicWebsite | None = None
    published_at: AwareDatetime | None = None
    last_request: UUID
    last_fingerprint: str


class WebsiteState(StrictInput):
    event_id: UUID
    event_revision: int
    revision: int
    stale: bool
    draft: WebsiteConfig
    public_path: str | None
    published: PublicWebsite | None
    published_at: datetime | None
    suggested_schedule: list[ScheduleItem] = Field(default_factory=list)


class DraftRequest(StrictInput):
    event_revision: int = Field(ge=1, strict=True)
    revision: int = Field(ge=0, strict=True)
    request_id: UUID
    config: WebsiteConfig


class ApprovalRequest(StrictInput):
    event_revision: int = Field(ge=1, strict=True)
    revision: int = Field(ge=1, strict=True)
    request_id: UUID
    approved: Literal[True]

    @field_validator("approved", mode="before")
    @classmethod
    def human_approval(cls, value: object) -> object:
        if value is not True:
            raise ValueError("Explicit human approval is required")
        return value


class PublishRequest(ApprovalRequest):
    preview_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class WebsitePreview(StrictInput):
    website: PublicWebsite
    preview_hash: str
    public_path: str | None


class PublicResponse(WebsiteText):
    request_id: UUID
    edition: str = Field(min_length=8, max_length=40)
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(default="", max_length=254)
    rsvp: RSVP
    attendees: int = Field(ge=1, le=21, strict=True)
    dietary: str = Field(default="", max_length=300)
    message: str = Field(default="", max_length=400)

    @field_validator("email")
    @classmethod
    def email_format(cls, value: str | None) -> str | None:
        return GuestValues._email(value)


class ResponseAcknowledgement(StrictInput):
    message: str = (
        "Thank you. New responses are added to the host's guest list. "
        "A matching existing entry is left unchanged; contact the host to change a previous response."
    )


class ContentRequest(StrictInput):
    revision: int = Field(ge=0, strict=True)
    event_revision: int = Field(ge=1, strict=True)
    config: WebsiteConfig
    tone: Literal["warm", "formal", "playful"] = "warm"


class CopyRecipe(StrictInput):
    opening: Literal["together", "occasion", "celebrate"]
    closing: Literal["company", "memories", "welcome"]


class WebsiteCopy(StrictInput):
    source: Literal["offline", "gemini"]
    welcome: str
    invitation: str
    description: str
    rsvp_instructions: str
