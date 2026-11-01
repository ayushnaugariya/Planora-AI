"""Decimal-safe expense inputs and derived reconciliation contracts."""

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)

from app.schemas.planning import Currency, clean_text


def exact_decimal(value: object) -> object:
    if isinstance(value, (float, bool)):
        raise ValueError("Send decimal values as strings or integers, not floating-point numbers")
    return value


def cents(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


Money = Annotated[
    Decimal,
    BeforeValidator(exact_decimal),
    Field(ge=0, le=100_000_000, decimal_places=6),
    AfterValidator(cents),
]
Quantity = Annotated[Decimal, BeforeValidator(exact_decimal), Field(ge=0, le=5000, decimal_places=3)]


class BudgetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExpenseValues(BudgetInput):
    category_key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,29}$")
    description: str = Field(min_length=1, max_length=150)
    currency: Currency
    quantity: Quantity = Decimal(1)
    cost_basis: Literal["fixed", "per_guest"] = "fixed"
    unit_amount: Money | None = None
    tax: Money = Decimal("0.00")
    fee: Money = Decimal("0.00")
    estimated_amount: Money | None = None
    quoted_amount: Money | None = None
    committed_amount: Money | None = None
    paid_amount: Money = Decimal("0.00")
    vendor_id: UUID | None = None
    notes: str = Field(default="", max_length=500)

    @field_validator("description", "notes", mode="before")
    @classmethod
    def _clean(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value


class ExpenseRecord(ExpenseValues):
    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    provenance: Literal["manual", "legacy", "scenario"] = "manual"
    creation_fingerprint: str = ""
    priced_for_guests: int | None = None
    cancelled: bool = False

    @computed_field
    @property
    def line_total(self) -> Decimal | None:
        return (
            cents(self.quantity * self.unit_amount + self.tax + self.fee)
            if self.unit_amount is not None
            else None
        )

    @computed_field
    @property
    def estimate(self) -> Decimal | None:
        return self.estimated_amount if self.estimated_amount is not None else self.line_total

    @computed_field
    @property
    def payment_status(self) -> str:
        if not self.paid_amount:
            return "unpaid"
        if self.committed_amount is None:
            return "payment_recorded"
        return "paid" if self.paid_amount >= self.committed_amount else "part_paid"


class ExpenseCreate(BudgetInput):
    revision: int = Field(ge=1)
    request_id: UUID
    expense: ExpenseValues


class ExpenseUpdate(BudgetInput):
    revision: int = Field(ge=1)
    expense: ExpenseValues


class ExpenseDelete(BudgetInput):
    revision: int = Field(ge=1)
    confirm_id: UUID


class Allocation(BudgetInput):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,29}$")
    label: str = Field(min_length=1, max_length=60)
    amount: int = Field(ge=0, le=100_000_000, strict=True)

    @field_validator("label", mode="before")
    @classmethod
    def _label(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value


class AllocationUpdate(BudgetInput):
    revision: int = Field(ge=1)
    allocations: list[Allocation] = Field(min_length=1, max_length=30)


class BudgetWarning(BaseModel):
    code: str
    message: str
    expense_ids: list[UUID] = Field(default_factory=list)
    category_key: str | None = None


class CategorySummary(BaseModel):
    key: str
    label: str
    allocation: Decimal
    estimated: Decimal
    quoted: Decimal
    committed: Decimal
    paid: Decimal
    projected: Decimal
    remaining: Decimal
    expense_ids: list[UUID]
    per_guest_allocation: Decimal | None = None


class BudgetSummary(BaseModel):
    currency: Currency
    total_budget: Decimal
    planned_allocation: Decimal
    estimated_cost: Decimal
    quoted_cost: Decimal
    committed_spending: Decimal
    actual_spending: Decimal
    outstanding_commitments: Decimal
    projected_cost: Decimal
    unallocated_funds: Decimal
    remaining_funds: Decimal
    cash_remaining: Decimal
    contingency_reserve: Decimal
    contingency_remaining: Decimal
    spendable_remaining: Decimal
    categories: list[CategorySummary]
    warnings: list[BudgetWarning]
    missing_categories: list[str]
    unknown_expenses: list[UUID]
    reconciled: bool = True
    planned_per_guest: Decimal | None = None
