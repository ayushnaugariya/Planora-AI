"""Stable child reconciliation, explicit legacy progress and revision changes."""

from datetime import UTC, datetime

from fastapi import HTTPException

from app.schemas.workspaces import (
    ChecklistState,
    EventWorkspace,
    LegacyProgress,
    RevisionEntry,
    TaskState,
    VendorState,
)


def reconcile(workspace: EventWorkspace | None, plan):
    """Keep child identity/status by semantic template key, never by position alone."""
    old_tasks = {}
    old_vendors = {}
    if workspace:
        for task in workspace.tasks:
            milestone = workspace.plan.timeline[task.milestone_index]
            old_tasks[(milestone.category, milestone.title)] = task
        for vendor in workspace.vendors:
            old_vendors[workspace.plan.vendors[vendor.group_index].key] = vendor
    tasks = []
    for i, milestone in enumerate(plan.timeline):
        task = old_tasks.get((milestone.category, milestone.title))
        tasks.append(task.model_copy(update={"milestone_index": i}) if task else TaskState(milestone_index=i))
    task_ids = {task.id for task in tasks}
    for task in tasks:
        task.depends_on = [item for item in task.depends_on if item in task_ids]
    vendors = []
    for i, group in enumerate(plan.vendors):
        old = old_vendors.get(group.key)
        checks = {}
        if old:
            old_group = workspace.plan.vendors[old.group_index]
            checks = {old_group.checklist[item.item_index]: item for item in old.checklist}
        checklist = [
            checks[text].model_copy(update={"item_index": j})
            if text in checks
            else ChecklistState(item_index=j)
            for j, text in enumerate(group.checklist)
        ]
        vendors.append(
            old.model_copy(update={"group_index": i, "checklist": checklist})
            if old
            else VendorState(group_index=i, checklist=checklist)
        )
    return tasks, vendors


def import_progress(workspace: EventWorkspace, progress: LegacyProgress) -> None:
    tasks = {task.milestone_index: task for task in workspace.tasks}
    checks = {
        f"{workspace.plan.vendors[v.group_index].key}:{item.item_index}": item
        for v in workspace.vendors
        for item in v.checklist
    }
    if any(i not in tasks or workspace.plan.timeline[i].category == "event" for i in progress.timeline):
        raise HTTPException(status_code=422, detail="Legacy task progress does not match this plan")
    if any(key not in checks for key in progress.vendors):
        raise HTTPException(status_code=422, detail="Legacy vendor progress does not match this plan")
    for i in progress.timeline:
        tasks[i].completed = True
    for key in progress.vendors:
        checks[key].completed = True


def next_revision(workspace: EventWorkspace, summary: str) -> None:
    workspace.revision += 1
    workspace.updated_at = datetime.now(UTC)
    workspace.history.append(
        RevisionEntry(revision=workspace.revision, created_at=workspace.updated_at, summary=summary)
    )
