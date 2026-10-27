"""Orchestrates the engine (exact maths) and the AI layer (personalisation)."""

from __future__ import annotations

import hashlib
from datetime import date

from app.ai import gemini as ai
from app.core.cache import TTLCache
from app.schemas.planning import AIExtras, Plan, PlanRequest
from app.services import engine

# Only successful Gemini results are cached, so a transient failure is never
# served again from the cache and identical requests do not spend extra tokens.
_extras_cache: TTLCache[AIExtras] = TTLCache(maxsize=256, ttl=900)


def cache_key(req: PlanRequest, today: date) -> str:
    """Key on the full request plus today's date (the summary mentions days remaining)."""
    raw = f"{today.isoformat()}|{req.model_dump_json()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def clear_cache() -> None:
    _extras_cache.clear()


def build_plan(req: PlanRequest, client: ai.LLM | None, today: date | None = None) -> Plan:
    today = today or date.today()
    core = engine.compute(req, today)

    key = cache_key(req, today)
    cached = _extras_cache.get(key) if client is not None else None
    if cached is not None:
        extras, source = cached, "gemini"
    else:
        extras, source = ai.generate_extras(req, core, client)
        if source == "gemini":
            _extras_cache.set(key, extras)

    title = req.title or req.event_type.replace("_", " ").title()
    return Plan(
        title=title,
        event_type=req.event_type,
        event_date=req.event_date,
        days_until=core.days_until,
        guest_count=req.guest_count,
        budget=req.budget,
        currency=req.currency,
        per_guest=core.per_guest,
        health_score=core.health_score,
        timeline_compressed=core.compressed,
        warnings=core.warnings,
        budget_lines=core.budget,
        timeline=core.timeline,
        vendors=core.vendors,
        ideas=extras.ideas,
        summary=extras.summary,
        tips=extras.tips,
        ai_source=source,  # type: ignore[arg-type]
    )
