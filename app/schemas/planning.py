"""Request and response schemas. All user input is validated here."""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

EventType = Literal["wedding", "birthday", "community", "anniversary", "baby_shower"]
Currency = Literal["INR", "USD", "EUR", "GBP"]
Formality = Literal["casual", "semi_formal", "formal"]

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(value: str) -> str:
    """Strip control characters and collapse whitespace."""
    value = _CONTROL.sub("", value)
    return re.sub(r"[ \t]+", " ", value).strip()


class PlanRequest(BaseModel):
    event_type: EventType
    title: str = Field(default="", max_length=80)
    event_date: date
    guest_count: int = Field(ge=2, le=5000)
    budget: int = Field(ge=1000, le=100_000_000, description="Whole currency units")
    currency: Currency = "INR"
    city: str = Field(default="", max_length=60)
    formality: Formality = "semi_formal"
    priorities: list[str] = Field(default_factory=list, max_length=6)
    dietary: list[str] = Field(default_factory=list, max_length=6)
    interests: str = Field(default="", max_length=300)
    theme: str = Field(default="", max_length=80)
    notes: str = Field(default="", max_length=500)

    @field_validator("title", "city", "interests", "theme", "notes")
    @classmethod
    def _clean(cls, v: str) -> str:
        return clean_text(v)

    @field_validator("priorities", "dietary")
    @classmethod
    def _clean_list(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for item in v:
            item = clean_text(item).lower()[:30]
            if item and item not in out:
                out.append(item)
        return out

    @model_validator(mode="after")
    def _check_date(self) -> PlanRequest:
        today = date.today()
        if self.event_date < today:
            raise ValueError("event_date must be today or in the future")
        if self.event_date > today + timedelta(days=365 * 3):
            raise ValueError("event_date must be within the next 3 years")
        return self


class BudgetLine(BaseModel):
    key: str
    label: str
    amount: int
    percent: float
    per_guest: float
    priority: bool = False
    tip: str = ""


class Milestone(BaseModel):
    title: str
    due: date
    days_before_event: int
    category: str
    note: str = ""


class VendorGroup(BaseModel):
    key: str
    label: str
    book_by: date
    budget: int
    checklist: list[str]
    ask: list[str]
    red_flags: list[str]


class Idea(BaseModel):
    title: str = Field(max_length=80)
    description: str = Field(max_length=300)
    category: str = Field(default="general", max_length=30)


class Warning_(BaseModel):
    level: Literal["info", "warn", "risk"]
    message: str


class AIExtras(BaseModel):
    """Shape that Gemini must return. Validated before use."""

    summary: str = Field(max_length=600)
    ideas: list[Idea] = Field(max_length=8)
    tips: list[str] = Field(max_length=6)


class Plan(BaseModel):
    title: str
    event_type: EventType
    event_date: date
    days_until: int
    guest_count: int
    budget: int
    currency: Currency
    per_guest: float
    health_score: int
    timeline_compressed: bool
    warnings: list[Warning_]
    budget_lines: list[BudgetLine]
    timeline: list[Milestone]
    vendors: list[VendorGroup]
    ideas: list[Idea]
    summary: str
    tips: list[str]
    ai_source: Literal["gemini", "offline"]


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=400)
    plan: PlanRequest

    @field_validator("question")
    @classmethod
    def _clean(cls, v: str) -> str:
        return clean_text(v)


class ChatResponse(BaseModel):
    answer: str
    source: Literal["gemini", "offline"]
