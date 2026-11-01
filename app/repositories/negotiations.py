"""One explicitly saved, versioned user-reviewed message per owned event/vendor."""

import sqlite3
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException

from app.core.errors import RevisionConflict, UnsupportedSchema
from app.repositories.workspaces import WorkspaceRepository
from app.schemas.negotiation import DraftSave, NegotiationDraft
from app.schemas.workspaces import EventWorkspace
from app.services.negotiation import vendor_for


def _table(connection: sqlite3.Connection) -> tuple[int] | None:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='negotiation_drafts'"
    ).fetchone()


def _read(
    connection: sqlite3.Connection, owner: str, event: EventWorkspace, vendor_id: UUID
) -> NegotiationDraft | None:
    if not _table(connection):
        return None
    row = connection.execute(
        "SELECT format_version,revision,document FROM negotiation_drafts "
        "WHERE event_id=? AND vendor_id=? AND owner=?",
        (str(event.id), str(vendor_id), owner),
    ).fetchone()
    if row is None:
        return None
    try:
        draft = NegotiationDraft.model_validate_json(row[2])
        if (
            row[0] != 1
            or draft.draft_revision != row[1]
            or draft.event_id != event.id
            or draft.vendor_id != vendor_id
        ):
            raise ValueError("Draft integrity mismatch")
    except ValueError as exc:
        raise UnsupportedSchema from exc
    draft.stale = draft.saved_event_revision != event.revision
    return draft


def read(repo: WorkspaceRepository, owner: str, event_id: UUID, vendor_id: UUID) -> NegotiationDraft | None:
    with repo._connection() as connection:
        connection.execute("BEGIN")
        event = repo._read(connection, owner, str(event_id))
        vendor_for(event, vendor_id)
        return _read(connection, owner, event, vendor_id)


def save(
    repo: WorkspaceRepository, owner: str, event_id: UUID, vendor_id: UUID, body: DraftSave
) -> NegotiationDraft:
    if not body.approved:
        raise HTTPException(status_code=422, detail="Explicitly save the reviewed draft; this never sends it")
    with repo._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        event = repo._read(connection, owner, str(event_id))
        vendor = vendor_for(event, vendor_id)
        if event.revision != body.revision:
            raise RevisionConflict
        if body.expense_id:
            category = event.plan.vendors[vendor.group_index].key
            if not any(
                e.id == body.expense_id
                and e.category_key == category
                and e.vendor_id in (None, vendor.id)
                and not e.cancelled
                for e in event.expenses
            ):
                raise HTTPException(
                    status_code=404, detail="Selected expense is not in this event/vendor category"
                )
        if body.vendor_quote_id and not any(q.id == body.vendor_quote_id for q in vendor.quotes):
            raise HTTPException(status_code=404, detail="Selected quotation is not in this vendor record")
        old = _read(connection, owner, event, vendor_id)
        if old is None and _table(connection):
            collision = connection.execute(
                "SELECT 1 FROM negotiation_drafts WHERE event_id=? AND vendor_id=?",
                (str(event.id), str(vendor_id)),
            ).fetchone()
            if collision:
                raise UnsupportedSchema("Draft ownership integrity mismatch")
        expected = old.draft_revision if old else 0
        if body.draft_revision != expected:
            raise RevisionConflict
        connection.execute(
            "CREATE TABLE IF NOT EXISTS negotiation_drafts (event_id TEXT NOT NULL "
            "REFERENCES events(id) ON DELETE CASCADE, vendor_id TEXT NOT NULL, owner TEXT NOT NULL, "
            "format_version INTEGER NOT NULL CHECK(format_version=1), revision INTEGER NOT NULL, "
            "document TEXT NOT NULL, PRIMARY KEY(event_id,vendor_id))"
        )
        draft = NegotiationDraft(
            event_id=event.id,
            vendor_id=vendor_id,
            saved_event_revision=event.revision,
            draft_revision=expected + 1,
            updated_at=datetime.now(UTC),
            scenario=body.scenario,
            message=body.message,
            target_price=body.target_price,
            instruction=body.instruction,
            expense_id=body.expense_id,
            vendor_quote_id=body.vendor_quote_id,
        )
        connection.execute(
            "INSERT INTO negotiation_drafts(event_id,vendor_id,owner,format_version,revision,document) "
            "VALUES(?,?,?,1,?,?) ON CONFLICT(event_id,vendor_id) DO UPDATE SET "
            "revision=excluded.revision,document=excluded.document",
            (str(event.id), str(vendor_id), owner, draft.draft_revision, draft.model_dump_json()),
        )
    return draft
