"""Owned event-day overlays. The original planning API and schedule stay intact."""

from datetime import datetime
from typing import Annotated, Literal, Self
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, Field, field_validator, model_validator

from app.schemas.planning import clean_text
from app.schemas.workspaces import EventWorkspace, StrictInput

TaskStatus = Literal["upcoming", "in_progress", "completed", "delayed", "blocked"]
ArrivalStatus = Literal["expected", "arrived", "delayed", "not_required"]
IncidentStatus = Literal["open", "in_progress", "resolved"]
Severity = Literal["low", "medium", "high", "critical"]


class TextInput(StrictInput):
    @field_validator("*", mode="before")
    @classmethod
    def clean(cls, value: object) -> object:
        if isinstance(value, str):
            value.encode("utf-8")  # Reject lone surrogates before persistence/provider use.
            return clean_text(value)
        return value


class TaskDetails(TextInput):
    title: str = Field(default="", max_length=120)
    status: TaskStatus = "upcoming"
    responsible: str = Field(default="", max_length=100)
    vendor_id: UUID | None = None
    location: str = Field(default="", max_length=160)
    planned_start: AwareDatetime | None = None
    planned_end: AwareDatetime | None = None
    expected_start: AwareDatetime | None = None
    delay_reason: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=800)
    depends_on: list[UUID] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def times(self) -> Self:
        if self.planned_end and (not self.planned_start or self.planned_end < self.planned_start):
            raise ValueError("An end time requires a start time and must not precede it")
        if self.status == "delayed" and not self.delay_reason:
            raise ValueError("A delayed task needs a reason")
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("Duplicate dependencies")
        return self


class OperationalTask(TaskDetails):
    id: UUID
    custom: bool = False
    actual_started_at: AwareDatetime | None = None
    actual_completed_at: AwareDatetime | None = None


class ArrivalDetails(TextInput):
    status: ArrivalStatus = "expected"
    expected_at: AwareDatetime | None = None
    notes: str = Field(default="", max_length=800)


class Arrival(ArrivalDetails):
    vendor_id: UUID
    actual_arrived_at: AwareDatetime | None = None


class IncidentDetails(TextInput):
    category: Literal["vendor", "catering", "equipment", "weather", "venue", "guest", "timeline", "other"]
    severity: Severity = "medium"
    description: str = Field(min_length=2, max_length=800)
    responsible: str = Field(default="", max_length=100)
    status: IncidentStatus = "open"
    task_id: UUID | None = None
    vendor_id: UUID | None = None
    notes: str = Field(default="", max_length=800)


class Incident(IncidentDetails):
    id: UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime
    resolved_at: AwareDatetime | None = None


class DaySettings(TextInput):
    timezone: str | None = Field(default=None, max_length=80)

    @field_validator("timezone")
    @classmethod
    def timezone_exists(cls, value: str | None) -> str | None:
        if value:
            try:
                ZoneInfo(value)
            except (ZoneInfoNotFoundError, ValueError) as exc:
                raise ValueError("Use an installed IANA timezone, for example Asia/Kolkata") from exc
        return value or None


class TaskOperation(StrictInput):
    kind: Literal["task"]
    id: UUID
    value: TaskDetails


class VendorOperation(StrictInput):
    kind: Literal["vendor"]
    id: UUID
    value: ArrivalDetails


class IncidentOperation(StrictInput):
    kind: Literal["incident"]
    id: UUID
    value: IncidentDetails


class SettingsOperation(StrictInput):
    kind: Literal["settings"]
    value: DaySettings


class DayMutation(StrictInput):
    revision: int = Field(ge=1, strict=True)
    request_id: UUID
    approved: Literal[True]
    operation: Annotated[
        TaskOperation | VendorOperation | IncidentOperation | SettingsOperation, Field(discriminator="kind")
    ]

    @field_validator("approved", mode="before")
    @classmethod
    def explicit_approval(cls, value: object) -> object:
        if value is not True:
            raise ValueError("Explicit approval is required")
        return value


class Activity(StrictInput):
    id: UUID
    event_id: UUID
    kind: Literal["task", "vendor", "incident", "settings"]
    reference_id: UUID | None = None
    description: str
    created_at: AwareDatetime


class Receipt(StrictInput):
    id: UUID
    fingerprint: str


class DayDocument(StrictInput):
    format_version: Literal[1] = 1
    event_id: UUID
    settings: DaySettings = Field(default_factory=DaySettings)
    tasks: list[OperationalTask] = Field(default_factory=list, max_length=200)
    arrivals: list[Arrival] = Field(default_factory=list, max_length=100)
    incidents: list[Incident] = Field(default_factory=list, max_length=100)
    activity: list[Activity] = Field(default_factory=list, max_length=1000)
    receipts: list[Receipt] = Field(default_factory=list, max_length=1000)


class DayTask(OperationalTask):
    original_due: str | None = None
    effective_start: AwareDatetime | None = None
    delay_minutes: int | None = None
    overdue: bool = False


class DayVendor(Arrival):
    name: str
    category: str
    contact: str
    booking_status: str
    task_ids: list[UUID]


class DayStats(StrictInput):
    total: int
    completed: int
    in_progress: int
    delayed: int
    blocked: int
    upcoming: int
    vendors_expected: int
    vendors_arrived: int
    vendors_outstanding: int
    open_incidents: int
    critical_incidents: int
    readiness: int | None
    satisfied_checks: int
    total_checks: int


class DayDashboard(StrictInput):
    event_id: UUID
    revision: int
    title: str
    event_date: str
    as_of: datetime
    timezone: str
    phase: Literal["preparation", "in_progress", "completed"]
    assumptions: list[str]
    readiness_rule: str
    tasks: list[DayTask]
    vendors: list[DayVendor]
    incidents: list[Incident]
    activity: list[Activity]
    stats: DayStats


class DayResult(StrictInput):
    workspace: EventWorkspace
    dashboard: DayDashboard


class CopilotRequest(TextInput):
    revision: int = Field(ge=1, strict=True)
    question: str = Field(min_length=2, max_length=500)
    task_id: UUID | None = None
    delay_minutes: int = Field(default=30, ge=1, le=1440, strict=True)


class DayRecommendation(StrictInput):
    id: str
    label: str
    explanation: str
    task_ids: list[UUID] = Field(default_factory=list)


class CopilotResult(StrictInput):
    event_id: UUID
    revision: int
    source: Literal["offline", "gemini"]
    confirmed: list[str]
    operational_updates: list[str]
    recommendations: list[DayRecommendation]
    warnings: list[str]


class CopilotOrder(StrictInput):
    revision: int = Field(strict=True)
    ids: list[str] = Field(max_length=12)
