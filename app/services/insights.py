"""Explainable saved-state guidance. No inferred market prices or mutation authority."""


def planning_attention(workspace):
    summary = workspace.budget_summary
    parts = []
    for warning in summary.warnings[:2]:
        parts.append(warning.message)
    if summary.missing_categories:
        labels = {line.key: line.label for line in workspace.plan.budget_lines}
        parts.append(
            "Collect missing all-in prices for: "
            + ", ".join(labels.get(key, key) for key in summary.missing_categories[:3])
            + "."
        )
    missing = [vendor for vendor in workspace.vendors if not vendor.name or not vendor.contact]
    if missing:
        parts.append(f"{len(missing)} saved vendor group(s) still need contact details.")
    tasks = sorted(
        (
            task
            for task in workspace.tasks
            if not task.completed and workspace.plan.timeline[task.milestone_index].category != "event"
        ),
        key=lambda task: workspace.plan.timeline[task.milestone_index].due,
    )
    if tasks:
        item = workspace.plan.timeline[tasks[0].milestone_index]
        parts.append(f"Earliest open milestone: {item.title} ({item.due.isoformat()}).")
    if not parts:
        parts.append("No saved pricing gaps or open milestones were found; reconfirm supplier commitments.")
    return "Saved-state priorities: " + " ".join(parts)[:650]
