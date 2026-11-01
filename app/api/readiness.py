"""Owned revision-checked readiness analysis. No event, scenario or history writes."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import Owner, repository
from app.repositories.readiness import snapshot
from app.schemas.readiness import ReadinessReport, ReadinessRequest
from app.services.decisions import explain_readiness
from app.services.readiness import readiness

router = APIRouter(prefix="/api/events/{event_id}/readiness", tags=["readiness"])


@router.post("", response_model=ReadinessReport)
def analyze(event_id: UUID, body: ReadinessRequest, request: Request, owner: Owner) -> ReadinessReport:
    base, previews = snapshot(repository(request), owner, event_id, body.revision)
    report = readiness(base, previews)
    return explain_readiness(base, report, getattr(request.app.state, "llm", None) if body.explain else None)
