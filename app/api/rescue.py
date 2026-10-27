"""Rescue assessment saves isolated previews; existing scenario endpoints own approval."""

from uuid import UUID

from fastapi import APIRouter, Request

from app.api.dependencies import Owner, current, repository
from app.schemas.rescue import RescueAssessment, RescueRequest
from app.services.rescue import assess

router = APIRouter(prefix="/api/events/{event_id}/rescue", tags=["rescue"])


@router.post("", response_model=RescueAssessment, status_code=201)
def assess_incident(event_id: UUID, body: RescueRequest, request: Request, owner: Owner):
    base = current(request, owner, event_id, body.revision)
    result = assess(base, body)
    saved = repository(request).create_scenario_batch(
        owner, [option.scenario for option in result.options], body.request_id
    )
    for option, scenario in zip(result.options, saved, strict=True):
        option.scenario = scenario
    return result
