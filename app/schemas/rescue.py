"""Rescue input is untrusted data; output contains existing validated scenarios."""

from datetime import date
from typing import Literal, Self
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.budget import BudgetInput, Money
from app.schemas.planning import clean_text
from app.schemas.scenarios import Scenario


class ReplacementQuote(BudgetInput):
    label: str = Field(min_length=1, max_length=80)
    amount: Money | None = None
    confirmed: bool = Field(default=False, strict=True)

    @field_validator("label", mode="before")
    @classmethod
    def _label(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value


class RescueRequest(BudgetInput):
    revision: int = Field(ge=1, strict=True)
    request_id: UUID
    kind: Literal[
        "vendor_cancellation",
        "venue_unavailable",
        "budget_reduction",
        "guest_change",
        "timeline_risk",
        "service_failure",
    ]
    description: str = Field(min_length=2, max_length=500)
    target_budget: int | None = Field(default=None, ge=1000, le=100_000_000, strict=True)
    guest_count: int | None = Field(default=None, ge=2, le=5000, strict=True)
    alternative_guest_count: int | None = Field(default=None, ge=2, le=5000, strict=True)
    event_date: date | None = None
    alternative_event_date: date | None = None
    vendor_id: UUID | None = None
    cancellation_fee: Money | None = None
    quotes: list[ReplacementQuote] = Field(default_factory=list, max_length=3)

    @field_validator("description", mode="before")
    @classmethod
    def _description(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def _required(self) -> Self:
        field = {
            "budget_reduction": "target_budget",
            "guest_change": "guest_count",
            "timeline_risk": "event_date",
            "vendor_cancellation": "vendor_id",
            "venue_unavailable": "vendor_id",
            "service_failure": "vendor_id",
        }[self.kind]
        if getattr(self, field) is None:
            raise ValueError(f"{field} is required for this incident")
        if any((self.cancellation_fee or 0) + (quote.amount or 0) > 100_000_000 for quote in self.quotes):
            raise ValueError("Combined replacement and cancellation costs exceed the supported amount")
        return self


class RecoveryOption(BudgetInput):
    title: str
    approach: str
    tradeoffs: list[str]
    scenario: Scenario


class RescueAssessment(BudgetInput):
    event_id: UUID
    revision: int
    incident: str
    urgency: Literal["immediate", "soon", "planning"]
    urgency_reason: str
    constraints: list[str]
    affected: list[str]
    next_steps: list[str]
    options: list[RecoveryOption]
