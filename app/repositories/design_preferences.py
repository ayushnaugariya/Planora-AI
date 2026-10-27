"""One owned preferred concept per event, checked against the current event revision."""

from pydantic import ValidationError

from app.core.errors import RevisionConflict, UnsupportedSchema
from app.db.design_preferences import ensure_design_schema
from app.schemas.intelligence import PreferredDesign


def save_preferred(repo, owner, preference):
    with repo._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        event = repo._read(connection, owner, str(preference.event_id))
        if event.revision != preference.base_revision:
            raise RevisionConflict
        ensure_design_schema(connection)
        old = connection.execute(
            "SELECT owner,format_version,document FROM design_preferences WHERE event_id=?",
            (str(event.id),),
        ).fetchone()
        if old:
            try:
                prior = PreferredDesign.model_validate_json(old[2])
                if old[0] != owner or old[1] != 1 or prior.event_id != event.id:
                    raise ValueError("Unsupported existing design record")
            except ValueError as exc:
                raise UnsupportedSchema from exc
        connection.execute(
            "INSERT INTO design_preferences(event_id,owner,format_version,document) VALUES(?,?,1,?) "
            "ON CONFLICT(event_id) DO UPDATE SET owner=excluded.owner, "
            "format_version=excluded.format_version,document=excluded.document",
            (str(event.id), owner, preference.model_dump_json()),
        )
    return preference


def read_preferred(repo, owner, event_id):
    with repo._connection() as connection:
        event = repo._read(connection, owner, str(event_id))
        if not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='design_preferences'"
        ).fetchone():
            return None
        row = connection.execute(
            "SELECT format_version,document FROM design_preferences WHERE event_id=? AND owner=?",
            (str(event_id), owner),
        ).fetchone()
        if row is None:
            return None
        try:
            result = PreferredDesign.model_validate_json(row[1])
            if row[0] != 1 or result.event_id != event.id:
                raise ValueError("Unsupported design format")
        except (ValueError, ValidationError) as exc:
            raise UnsupportedSchema from exc
    result.stale = result.base_revision != event.revision
    return result
