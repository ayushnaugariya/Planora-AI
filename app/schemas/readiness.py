"""Read-only evidence and bounded AI references, never an authority to apply changes."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.budget import BudgetInput

Destination = Literal["budget", "vendors", "timeline", "checklist", "scenarios", "rescue", "settings"]
CheckState = Literal["pass", "attention", "unknown"]


class ReadinessRequest(BudgetInput):
    revision: int = Field(ge=1, strict=True)
    explain: bool = Field(default=False, strict=True)


class ReadinessCheck(BudgetInput):
    id: str
    title: str
    status: CheckState
    evidence: list[str]
    destination: Destination


class ReadinessDimension(BudgetInput):
    id: str
    title: str
    state: Literal["attention", "incomplete", "clear"]
    passed: int
    total: int
    checks: list[ReadinessCheck]


class ReadinessAction(BudgetInput):
    check_id: str
    title: str
    evidence: list[str]
    potential_impact: str
    destination: Destination
    priority: int = Field(ge=0, le=2)


class ReadinessReport(BudgetInput):
    event_id: UUID
    revision: int
    evaluated_on: date
    state: Literal["attention_needed", "incomplete_evidence", "recorded_checks_clear"]
    explanation: str
    passed: int
    total: int
    dimensions: list[ReadinessDimension]
    actions: list[ReadinessAction] = Field(min_length=3, max_length=3)
    ordering_source: Literal["offline", "gemini"] = "offline"
    limitations: list[str]


class ReadinessOrdering(BudgetInput):
    revision: int = Field(strict=True)
    check_ids: list[str] = Field(min_length=3, max_length=3)
