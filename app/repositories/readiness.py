"""Consistent owned event/scenario read snapshot; no readiness persistence."""

from uuid import UUID

from app.core.errors import RevisionConflict
from app.repositories.workspaces import WorkspaceRepository
from app.schemas.scenarios import Scenario
from app.schemas.workspaces import EventWorkspace


def snapshot(
    repo: WorkspaceRepository, owner: str, event_id: UUID, revision: int
) -> tuple[EventWorkspace, list[Scenario]]:
    with repo._connection() as connection:
        connection.execute("BEGIN")
        base = repo._read(connection, owner, str(event_id))
        if base.revision != revision:
            raise RevisionConflict
        rows = connection.execute(
            "SELECT id FROM scenarios WHERE event_id=? AND owner=? ORDER BY rowid DESC",
            (str(event_id), owner),
        ).fetchall()
        previews = [repo._scenario(connection, owner, str(event_id), row[0]) for row in rows]
    return base, previews
