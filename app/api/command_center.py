"""Event-scoped operations and read-only copilot; existing Rescue owns financial previews."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import Owner, repository
from app.core.errors import RevisionConflict
from app.repositories import command_center
from app.schemas.command_center import CopilotRequest, CopilotResult, DayDashboard, DayMutation, DayResult
from app.services.event_day_copilot import advise

router = APIRouter(prefix="/api/events/{event_id}/command-center", tags=["event day"])


@router.get("", response_model=DayDashboard)
def get_dashboard(event_id: UUID, request: Request, owner: Owner) -> DayDashboard:
    return command_center.read(repository(request), owner, event_id)


@router.post("/operations", response_model=DayResult)
def save_operation(event_id: UUID, body: DayMutation, request: Request, owner: Owner) -> DayResult:
    return command_center.mutate(repository(request), owner, event_id, body)


@router.post("/copilot", response_model=CopilotResult)
def copilot(event_id: UUID, body: CopilotRequest, request: Request, owner: Owner) -> CopilotResult:
    view = command_center.read(repository(request), owner, event_id)
    if view.revision != body.revision:
        raise RevisionConflict
    return advise(view, body, request.app.state.llm)


@router.get("/incidents/{incident_id}/analysis", response_model=CopilotResult)
def incident_analysis(event_id: UUID, incident_id: UUID, request: Request, owner: Owner) -> CopilotResult:
    view = command_center.read(repository(request), owner, event_id)
    body = CopilotRequest(revision=view.revision, question="Review this incident and recovery consequences")
    return advise(view, body, incident_id=incident_id)
