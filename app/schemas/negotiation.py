"""Negotiation is private advice/draft text, never a financial action or sending authority."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.budget import Money
from app.schemas.intelligence import QuoteRequest
from app.schemas.planning import Currency, clean_text
from app.schemas.workspaces import StrictInput

NegotiationKind = Literal[
    "lower_price",
    "additional_services",
    "package_discount",
    "payment_terms",
    "hidden_charges",
    "compare_offers",
    "custom_package",
]
Tactic = Literal[
    "scope_options",
    "itemized_total",
    "payment_schedule",
    "package_options",
    "equivalent_scope",
    "protect_access",
    "confirm_terms",
]


class NegotiationInput(StrictInput):
    revision: int = Field(ge=1, strict=True)
    scenario: NegotiationKind = "lower_price"
    expense_id: UUID | None = None
    vendor_quote_id: UUID | None = None
    target_price: Money | None = None
    instruction: str = Field(default="", max_length=400)
    variant: int = Field(default=0, ge=0, le=2, strict=True)
    source: QuoteRequest | None = None
    comparisons: list[QuoteRequest] = Field(default_factory=list, max_length=2)
    comparison_expense_ids: list[UUID] = Field(default_factory=list, max_length=3)

    @field_validator("instruction", mode="before")
    @classmethod
    def _text(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value


class NegotiationFacts(StrictInput):
    vendor_name: str
    category: str
    currency: Currency
    quote: Decimal | None
    quote_source: str
    target: Decimal | None
    requested_reduction: Decimal | None
    counteroffer: Decimal | None
    event_budget: Decimal
    category_allowance: Decimal
    scope: list[str]
    terms: dict[str, str]
    comparisons: list[str]
    protected: list[str]


class NegotiationResult(StrictInput):
    event_id: UUID
    vendor_id: UUID
    revision: int
    facts: NegotiationFacts
    missing: list[str]
    warnings: list[str]
    source: Literal["gemini", "offline"]
    approach: str
    suggestions: list[str]
    message: str | None


class NegotiationStrategy(StrictInput):
    revision: int = Field(strict=True)
    tone: Literal["cordial", "concise"]
    tactics: list[Tactic] = Field(min_length=1, max_length=3)


class DraftSave(StrictInput):
    revision: int = Field(ge=1, strict=True)
    draft_revision: int = Field(ge=0, strict=True)
    approved: bool = Field(strict=True)
    scenario: NegotiationKind
    message: str = Field(min_length=2, max_length=8000)
    target_price: Money | None = None
    instruction: str = Field(default="", max_length=400)
    expense_id: UUID | None = None
    vendor_quote_id: UUID | None = None

    @field_validator("message", "instruction", mode="before")
    @classmethod
    def _text(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value


class NegotiationDraft(StrictInput):
    event_id: UUID
    vendor_id: UUID
    saved_event_revision: int
    draft_revision: int
    updated_at: datetime
    scenario: NegotiationKind
    message: str
    target_price: Decimal | None
    instruction: str
    expense_id: UUID | None
    vendor_quote_id: UUID | None
    stale: bool = False
