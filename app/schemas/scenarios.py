"""Validated scenario commands and immutable preview contracts."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BeforeValidator, Field, field_validator, model_validator

from app.schemas.budget import Allocation, BudgetInput, BudgetSummary, ExpenseRecord, Money, exact_decimal
from app.schemas.planning import clean_text


class BudgetReduction(BudgetInput):
    type: Literal["budget_reduction"]
    amount: Money | None = None
    percent: Annotated[Decimal, BeforeValidator(exact_decimal), Field(gt=0, le=100)] | None = None
    allocations: list[Allocation] | None = Field(default=None, max_length=30)

    @model_validator(mode="after")
    def _reduction(self):
        if (self.amount is None) == (self.percent is None) or self.amount == 0:
            raise ValueError("Provide exactly one positive reduction amount or percentage")
        return self


class GuestChange(BudgetInput):
    type: Literal["guest_count"]
    guest_count: int = Field(ge=2, le=5000, strict=True)


class DateChange(BudgetInput):
    type: Literal["event_date"]
    event_date: date


class VendorCancellation(BudgetInput):
    type: Literal["vendor_cancellation"]
    vendor_id: UUID
    cancellation_fee: Money | None = None
    replacement_cost: Money | None = None
    replacement_confirmed: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def _combined_cost(self):
        if (self.cancellation_fee or 0) + (self.replacement_cost or 0) > 100_000_000:
            raise ValueError("Combined replacement and cancellation costs exceed the supported amount")
        return self


class CategoryCost(BudgetInput):
    type: Literal["category_cost"]
    category_key: Literal["venue", "catering"]
    amount: Money
    expense_id: UUID | None = None


class AdditionalFunction(BudgetInput):
    type: Literal["additional_function"]
    name: str = Field(min_length=1, max_length=100)
    category_key: str = Field(default="entertainment", pattern=r"^[a-z][a-z0-9_]{0,29}$")
    estimated_cost: Money | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _name(cls, value):
        return clean_text(value) if isinstance(value, str) else value


ScenarioParameters = Annotated[
    BudgetReduction | GuestChange | DateChange | VendorCancellation | CategoryCost | AdditionalFunction,
    Field(discriminator="type"),
]


class ScenarioCreate(BudgetInput):
    revision: int = Field(ge=1)
    parameters: ScenarioParameters


class ScenarioApply(BudgetInput):
    revision: int = Field(ge=1)
    approved: bool = Field(strict=True)


class ExpenseChange(BudgetInput):
    id: UUID
    before: ExpenseRecord | None
    after: ExpenseRecord | None


class TaskImpact(BudgetInput):
    id: UUID
    title: str
    original_due: date
    proposed_due: date
    completed: bool
    dependencies: list[UUID]


class Scenario(BudgetInput):
    id: UUID
    event_id: UUID
    base_revision: int
    created_at: datetime
    evaluated_on: date
    parameters: ScenarioParameters
    original_values: dict[str, Any]
    proposed_values: dict[str, Any]
    original_budget: BudgetSummary
    proposed_budget: BudgetSummary
    budget_impact: dict[str, Decimal] = Field(default_factory=dict)
    expense_changes: list[ExpenseChange]
    affected_tasks: list[TaskImpact]
    warnings: list[str]
    reasons: list[str]
    feasibility: Literal["feasible", "infeasible", "indeterminate"]
    status: Literal["pending", "discarded", "applied"] = "pending"
    applied_revision: int | None = None
    stale: bool = False


class InterpretRequest(BudgetInput):
    revision: int = Field(ge=1)
    question: str = Field(min_length=2, max_length=400)


class Interpretation(BudgetInput):
    parameters: ScenarioParameters | None
    source: Literal["gemini", "offline"]
    explanation: str
