"""One owned additive document; operations, activity, receipts and workspace CAS are atomic."""

import hashlib
from datetime import UTC, datetime

from app.core.errors import RevisionConflict, UnsupportedSchema
from app.schemas.command_center import DayDocument, DayResult, Receipt
from app.services.command_center import apply_operation, dashboard
from app.services.workspaces import next_revision


def _read(connection, owner, event_id):
    if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='event_day'").fetchone():
        return DayDocument(event_id=event_id)
    row = connection.execute(
        "SELECT format_version,document FROM event_day WHERE event_id=? AND owner=?", (str(event_id), owner)
    ).fetchone()
    if row is None:
        return DayDocument(event_id=event_id)
    try:
        document = DayDocument.model_validate_json(row[1])
        if row[0] != 1 or document.event_id != event_id:
            raise ValueError("Event-day identity/format mismatch")
        for values, key in (
            (document.tasks, "id"),
            (document.arrivals, "vendor_id"),
            (document.incidents, "id"),
            (document.receipts, "id"),
        ):
            if len({getattr(v, key) for v in values}) != len(values):
                raise ValueError("Duplicate identities")
        if any(a.event_id != event_id for a in document.activity):
            raise ValueError("Activity identity mismatch")
        return document
    except (ValueError, TypeError) as exc:
        raise UnsupportedSchema from exc


def read(repo, owner, event_id):
    with repo._connection() as connection:
        connection.execute("BEGIN")
        base = repo._read(connection, owner, str(event_id))
        return dashboard(base, _read(connection, owner, base.id))


def mutate(repo, owner, event_id, body):
    with repo._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        base = repo._read(connection, owner, str(event_id))
        document = _read(connection, owner, base.id)
        fingerprint = hashlib.sha256(body.model_dump_json(exclude={"request_id"}).encode()).hexdigest()
        old = next((r for r in document.receipts if r.id == body.request_id), None)
        if old:
            if old.fingerprint != fingerprint:
                raise RevisionConflict
            return DayResult(workspace=base, dashboard=dashboard(base, document))
        if base.revision != body.revision:
            raise RevisionConflict
        apply_operation(base, document, body, datetime.now(UTC))
        document.receipts.append(Receipt(id=body.request_id, fingerprint=fingerprint))
        # Strictly validate before serializing, including all bounded collections.
        document = DayDocument.model_validate(document.model_dump())
        connection.execute(
            "CREATE TABLE IF NOT EXISTS event_day (event_id TEXT PRIMARY KEY "
            "REFERENCES events(id) ON DELETE CASCADE, owner TEXT NOT NULL, "
            "format_version INTEGER NOT NULL CHECK(format_version=1), document TEXT NOT NULL)"
        )
        collision = connection.execute(
            "SELECT owner FROM event_day WHERE event_id=?", (str(base.id),)
        ).fetchone()
        if collision and collision[0] != owner:
            raise UnsupportedSchema
        connection.execute(
            "INSERT INTO event_day VALUES(?,?,1,?) ON CONFLICT(event_id) DO UPDATE SET "
            "document=excluded.document",
            (str(base.id), owner, document.model_dump_json()),
        )
        next_revision(base, f"Event day: {document.activity[-1].description}")
        repo._save(connection, owner, base, body.revision)
        return DayResult(workspace=base, dashboard=dashboard(base, document))
