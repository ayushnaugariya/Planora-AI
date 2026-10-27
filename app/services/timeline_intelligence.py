"""Read-only dependency propagation, without invented durations or mutation authority."""

from datetime import timedelta

from fastapi import HTTPException

from app.schemas.intelligence import DelayAnalysis, DelayedTask
from app.services.scenarios import dependency_reasons


def delay_analysis(base, body):
    tasks = {task.id: task for task in base.tasks}
    if body.task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task does not belong to this event")
    root = tasks[body.task_id]
    if root.completed or base.plan.timeline[root.milestone_index].category == "event":
        raise HTTPException(
            status_code=422, detail="Choose an open planning task; event dates use Scenario Studio"
        )
    issues, proposed, affected = dependency_reasons(base), {}, set()
    assumptions = [
        "Read-only analysis. Saved deadlines, completion and budgets have not changed.",
        f"Supplied buffer: {body.buffer_days} day(s) after affected prerequisites; no duration inferred.",
        "Only recorded prerequisite links are propagated. "
        "Owners, durations, supplier capacity and day-of scheduling are not modeled.",
        "Use a date-change scenario or Event Rescue for reviewed event-date alternatives.",
    ]
    if not any(task.depends_on for task in tasks.values()):
        assumptions.append("No prerequisite links are recorded; downstream impacts may be missing.")

    def due(key):
        if key in proposed:
            return proposed[key]
        task = tasks[key]
        original = base.plan.timeline[task.milestone_index].due
        prerequisites = [due(parent) for parent in task.depends_on]
        value = original
        if key == root.id:
            value = original + timedelta(days=body.delay_days)
            affected.add(key)
        elif not task.completed and any(parent in affected for parent in task.depends_on):
            value = max(original, max(prerequisites) + timedelta(days=body.buffer_days))
            affected.add(key)
        proposed[key] = value
        return value

    impacts = []
    if not issues:
        for key in tasks:
            due(key)
        for key in sorted(affected, key=lambda item: (proposed[item], str(item))):
            task = tasks[key]
            milestone = base.plan.timeline[task.milestone_index]
            impacts.append(
                DelayedTask(
                    id=key,
                    title=milestone.title,
                    original_due=milestone.due,
                    proposed_due=proposed[key],
                    beyond_event=proposed[key] > base.details.event_date,
                )
            )
        if any(item.beyond_event for item in impacts):
            issues.append(
                "A proposed deadline crosses the saved event date; this is not a valid recovery schedule."
            )
    return DelayAnalysis(
        event_id=base.id, revision=base.revision, impacts=impacts, issues=issues, assumptions=assumptions
    )
