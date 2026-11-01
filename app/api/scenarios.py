"""Owned scenario previews and explicit, revision-checked application."""

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request

from app.api.dependencies import Owner, current, repository
from app.core.errors import RevisionConflict
from app.schemas.scenarios import Interpretation, InterpretRequest, Scenario, ScenarioApply, ScenarioCreate
from app.schemas.workspaces import EventWorkspace
from app.services.scenarios import simulate
from app.services.workspaces import next_revision

router = APIRouter(prefix="/api/events/{event_id}/scenarios", tags=["scenarios"])


@router.post("", response_model=Scenario, status_code=201)
def create_scenario(event_id: UUID, body: ScenarioCreate, request: Request, owner: Owner) -> Scenario:
    base = current(request, owner, event_id, body.revision)
    _, preview = simulate(base, body.parameters, uuid4(), datetime.now(UTC))
    return repository(request).create_scenario(owner, preview)


@router.get("", response_model=list[Scenario])
def list_scenarios(event_id: UUID, request: Request, owner: Owner) -> list[Scenario]:
    return repository(request).list_scenarios(owner, str(event_id))


@router.get("/{scenario_id}", response_model=Scenario)
@router.get("/{scenario_id}/compare", response_model=Scenario)
def get_scenario(event_id: UUID, scenario_id: UUID, request: Request, owner: Owner) -> Scenario:
    return repository(request).get_scenario(owner, str(event_id), str(scenario_id))


@router.post("/{scenario_id}/discard", response_model=Scenario)
def discard_scenario(event_id: UUID, scenario_id: UUID, request: Request, owner: Owner) -> Scenario:
    return repository(request).discard_scenario(owner, str(event_id), str(scenario_id))


@router.post("/{scenario_id}/apply", response_model=EventWorkspace)
def apply_scenario(
    event_id: UUID, scenario_id: UUID, body: ScenarioApply, request: Request, owner: Owner
) -> EventWorkspace:
    if not body.approved:
        raise HTTPException(status_code=422, detail="Explicit approval is required")
    repo = repository(request)
    saved = repo.get_scenario(owner, str(event_id), str(scenario_id))
    base = repo.get(owner, str(event_id))
    if saved.status == "applied":
        return base
    if (
        saved.status != "pending"
        or saved.stale
        or body.revision != saved.base_revision
        or saved.evaluated_on != date.today()
    ):
        raise RevisionConflict
    proposed, fresh = simulate(base, saved.parameters, saved.id, saved.created_at)
    if fresh.feasibility != "feasible":
        raise HTTPException(
            status_code=422, detail="Only a financially and structurally feasible scenario can be applied"
        )
    if fresh.model_dump(exclude={"stale"}) != saved.model_dump(exclude={"stale"}):
        raise RevisionConflict
    next_revision(proposed, f"Approved scenario {saved.id}: {saved.parameters.type}")
    return repo.apply_scenario(owner, str(event_id), str(scenario_id), body.revision, proposed)


@router.post("/interpret", response_model=Interpretation)
def interpret_scenario(
    event_id: UUID, body: InterpretRequest, request: Request, owner: Owner
) -> Interpretation:
    from app.ai.workspace import interpret

    base = current(request, owner, event_id, body.revision)
    return interpret(body.question, base, getattr(request.app.state, "llm", None))
