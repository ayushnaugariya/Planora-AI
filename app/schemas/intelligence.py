"""Bounded proposals and evidence; existing workspace/scenario contracts stay unchanged."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.budget import BudgetInput, Money, Quantity
from app.schemas.planning import Currency, clean_text
from app.schemas.scenarios import Scenario


class DecisionRequest(BudgetInput):
    revision: int = Field(ge=1, strict=True)
    question: str = Field(min_length=2, max_length=400)

    @field_validator("question", mode="before")
    @classmethod
    def _clean(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value


class DecisionCard(BudgetInput):
    title: str
    explanation: str
    evidence: list[str]
    operational_impact: list[str]
    tradeoffs: list[str]
    assumptions: list[str]
    uncertainty: str
    approval_required: bool = True
    preview: Scenario | None = None


class DecisionResponse(BudgetInput):
    event_id: UUID
    revision: int
    source: Literal["gemini", "offline"]
    clarification: str | None = None
    recommendations: list[DecisionCard]


class QuoteRequest(BudgetInput):
    revision: int = Field(ge=1, strict=True)
    filename: str = Field(
        default="quote.txt",
        min_length=5,
        max_length=84,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_. -]*\.[tT][xX][tT]$",
    )
    media_type: Literal["text/plain"] = "text/plain"
    text: str = Field(min_length=2, max_length=6000)
    category_key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,29}$")
    vendor_id: UUID | None = None

    @field_validator("filename")
    @classmethod
    def _filename(cls, value: str) -> str:
        if ".." in value:
            raise ValueError("Choose a simple text filename")
        return value

    @field_validator("text")
    @classmethod
    def _text(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 10000 or "\x00" in value or value.startswith(("%PDF", "PK\x03")):
            raise ValueError("Only bounded UTF-8 plain text quotations are supported")
        if len(value.splitlines()) > 80 or any(len(line) > 400 for line in value.splitlines()):
            raise ValueError("Quotation has too many or excessively long lines")
        return value


class QuoteLine(BudgetInput):
    description: str
    quantity: Quantity
    unit_price: Money
    total: Money
    source: str


class QuoteAnalysis(BudgetInput):
    filename: str
    source_text: str
    source_hash: str
    currency: Currency | None
    vendor_name: str | None
    category_key: str
    items: list[QuoteLine]
    subtotal: Money | None
    tax: Money | None
    fee: Money | None
    reported_total: Money | None
    comparable_total: Money | None
    deposit: Money | None
    terms: dict[str, str]
    payments: list["PaymentMilestone"]
    evidence: dict[str, str]
    issues: list[str]
    missing: list[str]
    importable: bool


class PaymentMilestone(BudgetInput):
    due: date
    amount: Money
    source: str


class QuoteImport(QuoteRequest):
    request_id: UUID
    approved: bool = Field(strict=True)
    expense_id: UUID | None = None
    record_as: Literal["quote", "commitment"] = "quote"


Style = Literal["botanical", "modern", "warm"]


class DesignRequest(BudgetInput):
    revision: int = Field(ge=1, strict=True)
    brief: str = Field(min_length=2, max_length=300)
    colors: list[Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]] = Field(
        default_factory=list, max_length=4
    )

    @field_validator("brief", mode="before")
    @classmethod
    def _brief(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value


class DesignSave(DesignRequest):
    style: Style
    approved: bool = Field(strict=True)


class DesignConcept(BudgetInput):
    style: Style
    title: str
    palette: list[str]
    directions: dict[str, str]
    budget_links: list[dict[str, str]]
    assumptions: list[str]


class DesignStudio(BudgetInput):
    event_id: UUID
    revision: int
    brief: str
    ranking_source: Literal["gemini", "offline"]
    concepts: list[DesignConcept]


class PreferredDesign(BudgetInput):
    format_version: Literal[1] = 1
    event_id: UUID
    base_revision: int
    brief: str
    concept: DesignConcept
    stale: bool = False


class DelayRequest(BudgetInput):
    revision: int = Field(ge=1, strict=True)
    task_id: UUID
    delay_days: int = Field(ge=0, le=90, strict=True)
    buffer_days: int = Field(default=0, ge=0, le=14, strict=True)


class DelayedTask(BudgetInput):
    id: UUID
    title: str
    original_due: date
    proposed_due: date
    beyond_event: bool


class DelayAnalysis(BudgetInput):
    event_id: UUID
    revision: int
    impacts: list[DelayedTask]
    issues: list[str]
    assumptions: list[str]
    can_apply: Literal[False] = False
