"""Workspace service and additive API; legacy generation endpoints are untouched."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import ValidationError

from app.api.dependencies import Owner, current, repository
from app.schemas.planning import clean_text
from app.schemas.workspaces import (
    ChatEntry,
    EventChat,
    EventCreate,
    EventDelete,
    EventDetails,
    EventSummary,
    EventUpdate,
    EventWorkspace,
    RevisionEntry,
    RevisionRequest,
)
from app.services import engine
from app.services.budget import sync_budget
from app.services.planning import build_plan
from app.services.workspaces import import_progress, next_revision, reconcile

router = APIRouter(prefix="/api/events", tags=["workspaces"])


def generated(details: EventDetails, request: Request):
    try:
        preferences = details.planning_request()
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail="Choose an event date from today through the next 3 years"
        ) from exc
    return build_plan(preferences, getattr(request.app.state, "llm", None))


@router.post("", response_model=EventWorkspace, status_code=201)
def create_event(body: EventCreate, request: Request, owner: Owner):
    plan = generated(body.details, request)
    now = datetime.now(UTC)
    tasks, vendors = reconcile(None, plan)
    workspace = EventWorkspace(
        created_at=now,
        updated_at=now,
        generated_at=now,
        details=body.details,
        plan=plan,
        tasks=tasks,
        vendors=vendors,
        history=[RevisionEntry(revision=1, created_at=now, summary="Created event and saved generated plan")],
    )
    if body.legacy_progress is not None:
        import_progress(workspace, body.legacy_progress)
        workspace.history[0].summary = "Created event with explicitly imported browser progress"
    return repository(request).create(owner, workspace)


@router.get("", response_model=list[EventSummary])
def list_events(request: Request, owner: Owner):
    return repository(request).list(owner)


@router.get("/{event_id}", response_model=EventWorkspace)
def get_event(event_id: UUID, request: Request, owner: Owner):
    return repository(request).get(owner, str(event_id))


@router.patch("/{event_id}", response_model=EventWorkspace)
def update_event(event_id: UUID, body: EventUpdate, request: Request, owner: Owner):
    workspace = current(request, owner, event_id, body.revision)
    if body.details is not None:
        # A type change would discard existing task/vendor records. Require a
        # new event instead; this stage never silently removes saved child data.
        if body.details.event_type != workspace.details.event_type:
            raise HTTPException(status_code=422, detail="Create another event to change its type")
        if workspace.expenses and body.details.currency != workspace.details.currency:
            raise HTTPException(
                status_code=422,
                detail="Cannot change currency with recorded expenses; conversion is not supported",
            )
        plan = generated(body.details, request)
        if workspace.allocations_manual:
            plan.budget_lines = workspace.plan.budget_lines
        workspace.tasks, workspace.vendors = reconcile(workspace, plan)
        workspace.details, workspace.plan = body.details, plan
        workspace.generated_at = datetime.now(UTC)
        sync_budget(workspace, refresh_narrative=bool(workspace.expenses or workspace.allocations_manual))
        summary = "Updated event details and saved rebuilt plan"
    elif body.title is not None:
        workspace.details.title = clean_text(body.title)
        workspace.plan.title = (
            workspace.details.title or workspace.details.event_type.replace("_", " ").title()
        )
        summary = "Renamed event"
    else:
        task_ids = {
            task.id
            for task in workspace.tasks
            if workspace.plan.timeline[task.milestone_index].category != "event"
        }
        check_ids = {item.id for vendor in workspace.vendors for item in vendor.checklist}
        if (
            not set(body.progress.completed_tasks) <= task_ids
            or not set(body.progress.completed_checks) <= check_ids
        ):
            raise HTTPException(status_code=422, detail="Progress contains unknown task or checklist IDs")
        for task in workspace.tasks:
            # Legacy controls manage planning steps only. Command Center owns
            # event-category completion, which an unrelated checklist save must retain.
            if task.id in task_ids:
                task.completed = task.id in body.progress.completed_tasks
        for vendor in workspace.vendors:
            for item in vendor.checklist:
                item.completed = item.id in body.progress.completed_checks
        summary = "Saved checklist progress"
    next_revision(workspace, summary)
    return repository(request).save(owner, workspace, body.revision)


@router.post("/{event_id}/regenerate", response_model=EventWorkspace)
def regenerate_event(event_id: UUID, body: RevisionRequest, request: Request, owner: Owner):
    workspace = current(request, owner, event_id, body.revision)
    return update_event(
        event_id, EventUpdate(revision=body.revision, details=workspace.details), request, owner
    )


@router.post("/{event_id}/chat", response_model=EventWorkspace)
def event_chat(event_id: UUID, body: EventChat, request: Request, owner: Owner):
    workspace = current(request, owner, event_id, body.revision)
    plan = workspace.plan
    core = engine.Core(
        days_until=plan.days_until,
        per_guest=plan.per_guest,
        health_score=plan.health_score,
        compressed=plan.timeline_compressed,
        warnings=plan.warnings,
        budget=plan.budget_lines,
        timeline=plan.timeline,
        vendors=plan.vendors,
    )
    from app.ai.workspace import answer as workspace_answer

    answer, source = workspace_answer(body.question, workspace, core, getattr(request.app.state, "llm", None))
    now = datetime.now(UTC)
    workspace.chat.extend(
        [
            ChatEntry(role="user", text=body.question, created_at=now),
            ChatEntry(role="assistant", text=answer, source=source, created_at=now),
        ]
    )
    next_revision(workspace, "Saved planning conversation")
    return repository(request).save(owner, workspace, body.revision)


@router.get("/{event_id}/ics")
def event_ics(event_id: UUID, request: Request, owner: Owner):
    workspace = repository(request).get(owner, str(event_id))
    body = engine.to_ics(
        workspace.plan.title,
        workspace.plan.timeline,
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        calendar_id=str(workspace.id),
    )
    return Response(
        body,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="eventra-timeline.ics"'},
    )


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: UUID, body: EventDelete, request: Request, owner: Owner):
    if body.confirm_id != event_id:
        raise HTTPException(status_code=422, detail="Event deletion requires its matching confirmation ID")
    repository(request).delete(owner, str(event_id), body.revision)
    return Response(status_code=204)
