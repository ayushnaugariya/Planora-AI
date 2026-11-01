"""Grounded read-only attention and dependency impact, shared by incidents and copilot."""

from uuid import UUID

from fastapi import HTTPException

from app.ai.command_center import order
from app.ai.gemini import LLM
from app.schemas.command_center import CopilotRequest, CopilotResult, DayDashboard, DayRecommendation
from app.services.command_center import affected_tasks


def advise(
    view: DayDashboard, body: CopilotRequest, client: LLM | None = None, incident_id: UUID | None = None
) -> CopilotResult:
    tasks = {t.id: t for t in view.tasks}
    if body.task_id is not None and body.task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task does not belong to this event")
    incidents = sorted(
        (i for i in view.incidents if i.status != "resolved"),
        key=lambda i: ({"critical": 0, "high": 1, "medium": 2, "low": 3}[i.severity], str(i.id)),
    )
    if incident_id:
        selected = next((i for i in view.incidents if i.id == incident_id), None)
        if selected is None:
            raise HTTPException(status_code=404, detail="Incident does not belong to this event")
        incidents = [selected]
    candidates, reports = [], []
    warnings = [
        "Read-only advice. No task, time, budget, scenario, arrival or message was changed.",
        "Only recorded dependencies are known. Durations, vendor availability and prices are not verified.",
        "Use an explicit operational Save for status/expected-time changes. Financial or event-date "
        "changes require Event Rescue / Scenario Studio preview and approval.",
    ]
    for incident in incidents[:5]:
        affected = affected_tasks(view, incident.task_id, incident.vendor_id)
        reports.append(f"{incident.severity} / {incident.status}: {incident.description}")
        candidates.append(
            DayRecommendation(
                id=f"incident:{incident.id}",
                label=f"Review {incident.severity} {incident.category} incident",
                explanation=f"{len(affected)} open tasks are linked directly or by recorded prerequisites. "
                "Confirm the cause and an owner. Use Event Rescue for a user-supplied replacement or "
                "date alternative. Delay does not establish cancellation, fees or replacement availability.",
                task_ids=affected,
            )
        )
    if body.task_id:
        root = tasks[body.task_id]
        affected = affected_tasks(view, root.id)
        candidates.append(
            DayRecommendation(
                id=f"delay:{root.id}",
                label=f"Explore a {body.delay_minutes}-minute delay: {root.title}",
                explanation=f"Hypothesis only: {len(affected)} open linked tasks may be affected. "
                "No durations or slack are assumed; downstream start times cannot be calculated reliably. "
                "Review the expected start with each responsible person before explicitly saving a change.",
                task_ids=affected,
            )
        )
    for task in view.tasks:
        if len(candidates) >= 9:
            break
        if task.status in ("blocked", "delayed", "in_progress") or task.overdue:
            candidates.append(
                DayRecommendation(
                    id=f"task:{task.id}",
                    label=f"Check {task.title}",
                    explanation=f"Reported status: {task.status}. "
                    "Confirm prerequisites, the owner and an expected time; do not silently move the plan.",
                    task_ids=[task.id],
                )
            )
    for vendor in view.vendors:
        if len(candidates) >= 11:
            break
        if vendor.status in ("expected", "delayed"):
            candidates.append(
                DayRecommendation(
                    id=f"vendor:{vendor.vendor_id}",
                    label=f"Confirm arrival: {vendor.name}",
                    explanation="No arrival recorded. Check the saved contact manually; no message is sent. "
                    + (
                        "An expected time is recorded."
                        if vendor.expected_at
                        else "Expected arrival is unknown; ask before setting it."
                    ),
                    task_ids=vendor.task_ids,
                )
            )
    upcoming = next((t for t in view.tasks if t.status == "upcoming" and not t.overdue), None)
    if upcoming and len(candidates) < 12:
        candidates.append(
            DayRecommendation(
                id=f"next:{upcoming.id}",
                label=f"Prepare next: {upcoming.title}",
                explanation="Next in saved-time order. Untimed items have no inferred start time.",
                task_ids=[upcoming.id],
            )
        )
    if not candidates:
        candidates.append(
            DayRecommendation(
                id="verify",
                label="Verify operational details",
                explanation="Add missing times, owners and arrival expectations. No urgent issue identified "
                "from recorded data; this does not establish real-world readiness.",
            )
        )
    ids, source = order(view.revision, body.question, candidates, client)
    by_id = {c.id: c for c in candidates}
    # Provider relevance ordering must never bury recorded critical incidents.
    critical = {f"incident:{i.id}" for i in incidents if i.severity == "critical"}
    ids = [key for key in ids if key in critical] + [key for key in ids if key not in critical]
    return CopilotResult(
        event_id=view.event_id,
        revision=view.revision,
        source=source,
        confirmed=[
            f"Saved event: {view.title}; date {view.event_date}; revision {view.revision}.",
            f"{view.stats.total} tasks; {view.stats.completed} marked completed; "
            f"{view.stats.vendors_arrived}/{view.stats.vendors_expected} required arrivals recorded.",
            f"{view.stats.open_incidents} unresolved incidents; {view.stats.critical_incidents} critical.",
        ],
        operational_updates=reports,
        recommendations=[by_id[key] for key in ids],
        warnings=warnings,
    )
