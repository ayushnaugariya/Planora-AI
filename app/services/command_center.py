"""Deterministic event-day operations; no financial or scenario application authority."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.schemas.command_center import (
    Activity,
    Arrival,
    DayDashboard,
    DayStats,
    DayTask,
    DayVendor,
    Incident,
    OperationalTask,
)


def task_view(base, document):
    saved = {task.id: task.model_copy(deep=True) for task in document.tasks if task.custom}
    overlays = {task.id: task for task in document.tasks if not task.custom}
    for task in base.tasks:
        milestone = base.plan.timeline[task.milestone_index]
        old = overlays.get(task.id)
        value = old.model_copy(deep=True) if old else OperationalTask(id=task.id)
        value.title = milestone.title
        # Original checklist remains authoritative, including changes from other views.
        if task.completed:
            value.status = "completed"
        elif value.status == "completed":
            value.status = "upcoming"
            value.actual_completed_at = None
        value.depends_on = list(dict.fromkeys([*task.depends_on, *value.depends_on]))
        saved[task.id] = value
    active = set(saved)
    vendors = {v.id for v in base.vendors}
    for value in saved.values():
        if any(key not in active for key in value.depends_on) and value.status != "completed":
            value.status = "blocked"
        if value.vendor_id not in vendors:
            value.vendor_id = None
    return saved


def dashboard(base, document, now=None):
    now = now or datetime.now(UTC)
    zone = document.settings.timezone
    # Preserve the legacy server-calendar convention unless explicitly configured.
    day = now.astimezone(ZoneInfo(zone)).date() if zone else now.astimezone().date()
    assumptions = [
        "Status and arrival reports are user-provided, not live supplier verification.",
        "Original planning deadlines and budget are preserved. Expected times are operational updates.",
        "Date-based event phase is not proof that work is completed. No background notifications are sent.",
        "Planning milestones remain visible alongside custom operations; no durations are invented.",
        "A prerequisite removed by a plan rebuild remains visible as unavailable and blocks open "
        "dependent work until its prerequisites are explicitly reviewed.",
    ]
    if not zone:
        assumptions.append("No event timezone configured: using the existing server-local calendar day.")
    originals = {t.id: base.plan.timeline[t.milestone_index].due.isoformat() for t in base.tasks}
    tasks = []
    for value in task_view(base, document).values():
        effective = value.expected_start or value.planned_start
        tasks.append(
            DayTask(
                **value.model_dump(),
                original_due=originals.get(value.id),
                effective_start=effective,
                delay_minutes=max(0, int((value.expected_start - value.planned_start).total_seconds() // 60))
                if value.expected_start and value.planned_start
                else None,
                overdue=bool(
                    effective and effective < now and value.status not in ("completed", "in_progress")
                ),
            )
        )
    tasks.sort(key=lambda t: (t.effective_start is None, t.effective_start or now, t.title, str(t.id)))
    arrivals = {a.vendor_id: a for a in document.arrivals}
    vendors = []
    for vendor in base.vendors:
        group = base.plan.vendors[vendor.group_index]
        arrival = arrivals.get(vendor.id) or Arrival(vendor_id=vendor.id)
        vendors.append(
            DayVendor(
                **arrival.model_dump(),
                name=vendor.name or group.label,
                category=group.label,
                contact=vendor.contact,
                booking_status=vendor.booking_status,
                task_ids=[t.id for t in tasks if t.vendor_id == vendor.id],
            )
        )
    incidents = document.incidents
    active = sum(i.status != "resolved" for i in incidents)
    relevant = [v for v in vendors if v.status != "not_required"]
    complete = sum(t.status == "completed" for t in tasks)
    arrived = sum(v.status == "arrived" for v in relevant)
    checks = len(tasks) + len(relevant) + len(incidents)
    satisfied = complete + arrived + len(incidents) - active
    stats = DayStats(
        total=len(tasks),
        completed=complete,
        **{
            status: sum(t.status == status for t in tasks)
            for status in ("in_progress", "delayed", "blocked", "upcoming")
        },
        vendors_expected=len(relevant),
        vendors_arrived=arrived,
        vendors_outstanding=len(relevant) - arrived,
        open_incidents=active,
        critical_incidents=sum(i.severity == "critical" and i.status != "resolved" for i in incidents),
        readiness=(100 * satisfied // checks) if checks else None,
        satisfied_checks=satisfied,
        total_checks=checks,
    )
    return DayDashboard(
        event_id=base.id,
        revision=base.revision,
        title=base.plan.title,
        event_date=base.details.event_date.isoformat(),
        as_of=now,
        timezone=zone or "server-local (not configured)",
        phase="preparation"
        if day < base.details.event_date
        else "in_progress"
        if day == base.details.event_date
        else "completed",
        assumptions=assumptions,
        readiness_rule="Floor(100 × (completed tasks + arrived required vendors + resolved incidents) / "
        "(all tasks + required vendors + all incidents)). Equal-weight operational checks, "
        "not a safety guarantee. "
        "Not-required vendors are excluded. No checks means unknown.",
        tasks=tasks,
        vendors=vendors,
        incidents=incidents,
        activity=document.activity,
        stats=stats,
    )


def _member(key, keys, label):
    if key is not None and key not in keys:
        raise HTTPException(status_code=404, detail=f"{label} does not belong to this event")


def _graph(tasks):
    visiting, visited = set(), set()

    def visit(key):
        if key in visiting:
            raise HTTPException(status_code=422, detail="Task dependencies must not form a cycle")
        if key in visited:
            return
        visiting.add(key)
        for parent in tasks[key].depends_on:
            if parent in tasks:
                visit(parent)
        visiting.remove(key)
        visited.add(key)

    for key in tasks:
        visit(key)


def apply_operation(base, document, body, now):
    op = body.operation
    tasks = task_view(base, document)
    vendor_ids = {v.id for v in base.vendors}
    if len(document.activity) >= 1000:
        raise HTTPException(
            status_code=422, detail="Event-day activity capacity (1000) reached; records retained"
        )
    if op.kind == "task":
        if len(document.tasks) >= 200 and not any(task.id == op.id for task in document.tasks):
            raise HTTPException(
                status_code=422, detail="Stored task capacity (200) reached; existing records retained"
            )
        old = tasks.get(op.id)
        if old and old.custom and not op.value.title:
            raise HTTPException(status_code=422, detail="Custom tasks require a nonempty title")
        if old is None and (not op.value.title or len(tasks) >= 200):
            raise HTTPException(
                status_code=422, detail="A custom task needs a title; at most 200 total tasks"
            )
        _member(op.value.vendor_id, vendor_ids, "Vendor")
        for parent in op.value.depends_on:
            _member(parent, tasks, "Dependency")
        value = OperationalTask(**op.value.model_dump(), id=op.id, custom=old.custom if old else True)
        if old:
            value.title = old.title if not old.custom else value.title
            if old.status == "completed" and value.status not in ("completed", "upcoming"):
                raise HTTPException(
                    status_code=422, detail="Reopen a completed task as Upcoming before starting it"
                )
            if old.planned_start is not None and (value.planned_start, value.planned_end) != (
                old.planned_start,
                old.planned_end,
            ):
                raise HTTPException(
                    status_code=422, detail="Original time is locked; change the expected start instead"
                )
            value.actual_started_at = old.actual_started_at
            value.actual_completed_at = old.actual_completed_at
            original = next((t for t in base.tasks if t.id == op.id), None)
            if original:
                if not set(original.depends_on).issubset(value.depends_on):
                    raise HTTPException(
                        status_code=422, detail="Original prerequisites cannot be removed here"
                    )
                original.completed = value.status == "completed"
        tasks[op.id] = value
        _graph(tasks)
        if value.status in ("in_progress", "completed") and any(
            tasks[key].status != "completed" for key in value.depends_on
        ):
            raise HTTPException(status_code=422, detail="Complete recorded prerequisites first")
        if value.status == "in_progress" and value.actual_started_at is None:
            value.actual_started_at = now
        if value.status == "completed" and value.actual_completed_at is None:
            value.actual_completed_at = now
        if value.status == "upcoming":
            value.actual_started_at = value.actual_completed_at = None
        document.tasks = [t for t in document.tasks if t.id != op.id] + [value]
        description = f"Task {value.status}; original schedule retained"
    elif op.kind == "vendor":
        _member(op.id, vendor_ids, "Vendor")
        old = next((a for a in document.arrivals if a.vendor_id == op.id), None)
        if old and old.status == "arrived" and op.value.status == "delayed":
            raise HTTPException(
                status_code=422, detail="Correct arrival to Expected before marking it delayed"
            )
        value = Arrival(
            **op.value.model_dump(),
            vendor_id=op.id,
            actual_arrived_at=(old.actual_arrived_at if old and old.actual_arrived_at else now)
            if op.value.status == "arrived"
            else None,
        )
        document.arrivals = [a for a in document.arrivals if a.vendor_id != op.id] + [value]
        description = f"Vendor arrival {value.status}"
    elif op.kind == "incident":
        _member(op.value.task_id, tasks, "Task")
        _member(op.value.vendor_id, vendor_ids, "Vendor")
        old = next((i for i in document.incidents if i.id == op.id), None)
        if old is None and (len(document.incidents) >= 100 or op.value.status != "open"):
            raise HTTPException(status_code=422, detail="Create incidents Open; at most 100 incidents")
        if old and old.status == "resolved" and op.value.status not in ("resolved", "open"):
            raise HTTPException(status_code=422, detail="Reopen the incident before progressing it")
        value = Incident(
            **op.value.model_dump(),
            id=op.id,
            created_at=old.created_at if old else now,
            updated_at=now,
            resolved_at=(old.resolved_at if old and old.resolved_at else now)
            if op.value.status == "resolved"
            else None,
        )
        document.incidents = [i for i in document.incidents if i.id != op.id] + [value]
        description = f"Incident {value.status} ({value.severity})"
    else:
        document.settings = op.value
        description = "Event-day timezone updated"
    document.activity.append(
        Activity(
            id=body.request_id,
            event_id=base.id,
            kind=op.kind,
            reference_id=getattr(op, "id", None),
            description=description,
            created_at=now,
        )
    )


def affected_tasks(view, task_id=None, vendor_id=None):
    """Conservative dependency reachability, not invented minute-by-minute rescheduling."""
    keys = {
        t.id for t in view.tasks if t.id == task_id or (vendor_id is not None and t.vendor_id == vendor_id)
    }
    while True:
        more = keys | {t.id for t in view.tasks if any(p in keys for p in t.depends_on)}
        if more == keys:
            break
        keys = more
    return [t.id for t in view.tasks if t.id in keys and t.status != "completed"]
