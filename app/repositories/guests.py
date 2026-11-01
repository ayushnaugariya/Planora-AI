"""Roster documents and event revision/history commit in the same SQLite transaction."""

import hashlib
import sqlite3
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from app.core.errors import RevisionConflict, UnsupportedSchema, WorkspaceNotFound
from app.repositories.workspaces import WorkspaceRepository
from app.schemas.guests import (
    Guest,
    GuestCreate,
    GuestDelete,
    GuestList,
    GuestMutation,
    GuestStats,
    GuestUpdate,
    GuestValues,
)
from app.schemas.workspaces import EventWorkspace
from app.services.workspaces import next_revision


def _exists(connection: sqlite3.Connection) -> tuple[int] | None:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='guests'").fetchone()


def _schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS guests (id TEXT PRIMARY KEY, "
        "event_id TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE, owner TEXT NOT NULL, "
        "format_version INTEGER NOT NULL CHECK(format_version=1), document TEXT NOT NULL)"
    )
    connection.execute("CREATE INDEX IF NOT EXISTS guests_event ON guests(event_id, owner)")


def _rows(connection: sqlite3.Connection, owner: str, event_id: UUID) -> list[Guest]:
    if not _exists(connection):
        return []
    result = []
    for key, version, document in connection.execute(
        "SELECT id,format_version,document FROM guests WHERE event_id=? AND owner=? ORDER BY rowid",
        (str(event_id), owner),
    ):
        try:
            guest = Guest.model_validate_json(document)
            if version != 1 or str(guest.id) != key or guest.event_id != event_id:
                raise ValueError("Guest identity/format mismatch")
        except (ValueError, ValidationError) as exc:
            raise UnsupportedSchema from exc
        result.append(guest)
    return result


def roster(
    event: EventWorkspace, guests: list[Guest], q: str = "", rsvp: str | None = None, group: str | None = None
) -> GuestList:
    counts = {
        status: sum(1 + g.plus_ones for g in guests if g.rsvp == status)
        for status in ("pending", "confirmed", "declined", "maybe")
    }
    total = sum(counts.values())
    stats = GuestStats(
        records=len(guests),
        pending_responses=sum(g.rsvp == "pending" for g in guests),
        total_invited=total,
        **counts,
        expected_attendees=counts["confirmed"],
        possible_attendees=total - counts["declined"],
    )
    query = q.strip().casefold()
    filtered = [
        g
        for g in guests
        if (not query or query in g.name.casefold() or query in g.email.casefold())
        and (rsvp is None or g.rsvp == rsvp)
        and (group is None or g.group == group)
    ]
    return GuestList(event_id=event.id, revision=event.revision, guests=filtered, stats=stats)


def read(
    repo: WorkspaceRepository,
    owner: str,
    event_id: UUID,
    q: str = "",
    rsvp: str | None = None,
    group: str | None = None,
) -> GuestList:
    with repo._connection() as connection:
        connection.execute("BEGIN")
        event = repo._read(connection, owner, str(event_id))
        return roster(event, _rows(connection, owner, event.id), q, rsvp, group)


def add_public(
    connection: sqlite3.Connection,
    repo: WorkspaceRepository,
    owner: str,
    event: EventWorkspace,
    values: GuestValues,
) -> Guest:
    """Controlled create-only entry into the SAME roster, inside the publisher transaction."""
    if len(_rows(connection, owner, event.id)) >= 500:
        raise HTTPException(status_code=429, detail="Guest-list capacity reached. Contact the host")
    _schema(connection)
    now = datetime.now(UTC)
    guest = Guest(**values.model_dump(), id=uuid4(), event_id=event.id, created_at=now, updated_at=now)
    connection.execute(
        "INSERT INTO guests(id,event_id,owner,format_version,document) VALUES(?,?,?,1,?)",
        (str(guest.id), str(event.id), owner, guest.model_dump_json()),
    )
    revision = event.revision
    next_revision(event, "Added unverified public website RSVP to private guest list")
    repo._save(connection, owner, event, revision)
    return guest


def write(
    repo: WorkspaceRepository,
    owner: str,
    event_id: UUID,
    body: GuestCreate | GuestUpdate | GuestDelete,
    *,
    guest_id: UUID | None = None,
    delete: bool = False,
) -> GuestMutation:
    with repo._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        event = repo._read(connection, owner, str(event_id))
        guests = _rows(connection, owner, event.id)
        key = guest_id or body.request_id
        old = next((g for g in guests if g.id == key), None)
        fingerprint = hashlib.sha256(body.guest.model_dump_json().encode()).hexdigest() if not delete else ""
        if guest_id is None and old:
            if old.creation_fingerprint != fingerprint:
                raise RevisionConflict
            return GuestMutation(workspace=event, roster=roster(event, guests))
        if event.revision != body.revision:
            raise RevisionConflict
        if guest_id is not None and old is None:
            raise WorkspaceNotFound
        _schema(connection)
        if delete:
            if body.confirm_id != guest_id:
                raise HTTPException(status_code=422, detail="Confirm the matching guest ID before removing")
            connection.execute(
                "DELETE FROM guests WHERE id=? AND event_id=? AND owner=?", (str(key), str(event.id), owner)
            )
            guests.remove(old)
            operation = "Removed"
        else:
            if old is None and len(guests) >= 500:
                raise HTTPException(status_code=422, detail="This event supports at most 500 guest records")
            if old is None and connection.execute("SELECT 1 FROM guests WHERE id=?", (str(key),)).fetchone():
                raise RevisionConflict
            now = datetime.now(UTC)
            guest = Guest(
                **body.guest.model_dump(),
                id=key,
                event_id=event.id,
                created_at=old.created_at if old else now,
                updated_at=now,
                creation_fingerprint=old.creation_fingerprint if old else fingerprint,
            )
            if old:
                connection.execute(
                    "UPDATE guests SET document=? WHERE id=? AND event_id=? AND owner=?",
                    (guest.model_dump_json(), str(key), str(event.id), owner),
                )
                guests[guests.index(old)] = guest
            else:
                connection.execute(
                    "INSERT INTO guests(id,event_id,owner,format_version,document) VALUES(?,?,?,1,?)",
                    (str(key), str(event.id), owner, guest.model_dump_json()),
                )
                guests.append(guest)
            operation = "Updated" if old else "Added"
        next_revision(event, f"{operation} private guest record {key}")
        repo._save(connection, owner, event, body.revision)
        return GuestMutation(workspace=event, roster=roster(event, guests))
