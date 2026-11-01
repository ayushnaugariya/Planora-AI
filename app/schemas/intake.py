"""A bounded partial brief, separate from saved event creation and its authority."""

from datetime import date
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.budget import BudgetInput
from app.schemas.planning import Currency, EventType, Plan, clean_text


class IntakeRequest(BudgetInput):
    description: str = Field(min_length=2, max_length=1200)

    @field_validator("description", mode="before")
    @classmethod
    def _description(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value


class BriefFields(BudgetInput):
    event_type: EventType | None = None
    event_date: date | None = None
    guest_count: int | None = Field(default=None, ge=2, le=5000, strict=True)
    budget: int | None = Field(default=None, ge=1000, le=100_000_000, strict=True)
    currency: Currency | None = None
    title: str | None = Field(default=None, max_length=80)
    city: str | None = Field(default=None, max_length=60)
    theme: str | None = Field(default=None, max_length=80)
    priorities: list[Literal["food", "venue", "photography", "music", "decor", "experience"]] = Field(
        default_factory=list, max_length=3
    )

    @field_validator("title", "city", "theme")
    @classmethod
    def _text(cls, value: str | None) -> str | None:
        return clean_text(value) if value is not None else None


class EventBrief(BudgetInput):
    fields: BriefFields
    source: Literal["gemini", "offline"]
    missing: list[str]
    questions: list[str]
    assumptions: list[str]
    explanation: str
    preview: Plan | None
