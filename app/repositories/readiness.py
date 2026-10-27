"""Consistent owned event/scenario read snapshot; no readiness persistence."""

from app.core.errors import RevisionConflict


def snapshot(repo, owner, event_id, revision):
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
