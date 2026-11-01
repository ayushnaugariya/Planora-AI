"""Saved workspace contracts, separate from the existing generation API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.schemas.budget import BudgetSummary, ExpenseRecord
from app.schemas.planning import Plan, PlanRequest, clean_text


class EventDetails(PlanRequest):
    """Persisted preferences remain readable after the event date has passed."""

    model_config = ConfigDict(extra="forbid")
    venue_preferences: str = Field(default="", max_length=300)
    cultural_requirements: str = Field(default="", max_length=300)
    accessibility_requirements: str = Field(default="", max_length=300)
    assumptions: str = Field(default="", max_length=500)
    unresolved_decisions: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def _check_date(self) -> EventDetails:
        # New/rebuilt plans still pass through PlanRequest's future-date check.
        return self

    @field_validator(
        "venue_preferences",
        "cultural_requirements",
        "accessibility_requirements",
        "assumptions",
        "unresolved_decisions",
    )
    @classmethod
    def _clean_context(cls, value: str) -> str:
        return clean_text(value)

    def planning_request(self) -> PlanRequest:
        return PlanRequest.model_validate(self.model_dump(include=set(PlanRequest.model_fields)))


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LegacyProgress(StrictInput):
    """Explicit import of the old template-index progress, never the plan itself."""

    timeline: list[int] = Field(default_factory=list, max_length=100)
    vendors: list[str] = Field(default_factory=list, max_length=100)


class EventCreate(StrictInput):
    details: EventDetails
    legacy_progress: LegacyProgress | None = None


class TaskState(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    milestone_index: int
    completed: bool = False
    priority: Literal["normal", "high"] = "normal"
    depends_on: list[UUID] = Field(default_factory=list)


class ChecklistState(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    item_index: int
    completed: bool = False


class VendorQuote(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    amount: int = Field(ge=0)
    note: str = Field(default="", max_length=500)


class VendorState(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    group_index: int
    name: str = ""
    contact: str = ""
    booking_status: Literal["unbooked", "shortlisted", "booked", "cancelled"] = "unbooked"
    quotes: list[VendorQuote] = Field(default_factory=list)
    checklist: list[ChecklistState] = Field(default_factory=list)


class ChatEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: Literal["user", "assistant"]
    text: str
    created_at: datetime
    source: Literal["gemini", "offline"] | None = None


class RevisionEntry(BaseModel):
    revision: int
    created_at: datetime
    summary: str


class EventWorkspace(BaseModel):
    schema_version: Literal[2] = 2
    id: UUID = Field(default_factory=uuid4)
    revision: int = 1
    created_at: datetime
    updated_at: datetime
    generated_at: datetime
    details: EventDetails
    plan: Plan
    tasks: list[TaskState]
    vendors: list[VendorState]
    expenses: list[ExpenseRecord] = Field(default_factory=list)
    allocations_manual: bool = False
    chat: list[ChatEntry] = Field(default_factory=list)
    history: list[RevisionEntry] = Field(default_factory=list)

    @computed_field
    @property
    def budget_summary(self) -> BudgetSummary:
        from app.services.budget import calculate_budget

        return calculate_budget(self)


class EventSummary(BaseModel):
    id: UUID
    title: str
    event_date: str
    revision: int
    updated_at: datetime


class ProgressUpdate(StrictInput):
    completed_tasks: list[UUID] = Field(max_length=100)
    completed_checks: list[UUID] = Field(max_length=200)


class EventUpdate(StrictInput):
    revision: int = Field(ge=1)
    details: EventDetails | None = None
    title: str | None = Field(default=None, max_length=80)
    progress: ProgressUpdate | None = None

    @model_validator(mode="after")
    def _one_operation(self) -> EventUpdate:
        if sum(value is not None for value in (self.details, self.title, self.progress)) != 1:
            raise ValueError("Provide exactly one of details, title, or progress")
        return self


class RevisionRequest(StrictInput):
    revision: int = Field(ge=1)


class EventDelete(RevisionRequest):
    confirm_id: UUID


class EventChat(RevisionRequest):
    question: str = Field(min_length=2, max_length=400)

    @field_validator("question", mode="before")
    @classmethod
    def _question(cls, value: object) -> object:
        return clean_text(value) if isinstance(value, str) else value
