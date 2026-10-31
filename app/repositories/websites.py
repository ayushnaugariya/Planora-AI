"""Owned drafts, approved snapshots, stable unlisted links and transactional roster submissions."""

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException

from app.core.errors import RevisionConflict, UnsupportedSchema
from app.repositories import command_center, design_preferences, guests
from app.schemas.guests import GuestValues
from app.schemas.websites import (
    ResponseAcknowledgement,
    ScheduleItem,
    WebsiteRecord,
    WebsiteState,
)
from app.services.websites import defaults, preview_hash, project


def _exists(connection, table="event_websites"):
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()


def _schema(connection):
    connection.execute(
        "CREATE TABLE IF NOT EXISTS event_websites (event_id TEXT PRIMARY KEY "
        "REFERENCES events(id) ON DELETE CASCADE, owner TEXT NOT NULL, format_version INTEGER NOT NULL "
        "CHECK(format_version=1), revision INTEGER NOT NULL, slug TEXT NOT NULL UNIQUE, "
        "document TEXT NOT NULL)"
    )


def _decode(row):
    try:
        event_id, owner, version, revision, slug, text = row
        record = WebsiteRecord.model_validate_json(text)
        if (
            version != 1
            or str(record.event_id) != event_id
            or record.revision != revision
            or record.slug != slug
            or (record.published is None) != (record.published_at is None)
        ):
            raise ValueError("Website identity/format mismatch")
        return owner, record
    except (ValueError, TypeError) as exc:
        raise UnsupportedSchema from exc


def _read(connection, owner, event_id):
    if not _exists(connection):
        return None
    row = connection.execute("SELECT * FROM event_websites WHERE event_id=?", (str(event_id),)).fetchone()
    if row is None:
        return None
    stored_owner, record = _decode(row)
    if stored_owner != owner:
        raise UnsupportedSchema
    return record


def _state(base, record, initial=None, suggested=None):
    return WebsiteState(
        event_id=base.id,
        event_revision=base.revision,
        revision=record.revision if record else 0,
        stale=bool(record and record.saved_event_revision != base.revision),
        draft=record.draft if record else initial or defaults(base),
        public_path=f"/e/{record.slug}" if record else None,
        published=record.published if record else None,
        published_at=record.published_at if record else None,
        suggested_schedule=suggested or [],
    )


def read(repo, owner, event_id):
    with repo._connection() as connection:
        connection.execute("BEGIN")
        base = repo._read(connection, owner, str(event_id))
        record = _read(connection, owner, base.id)
    day = command_center.read(repo, owner, event_id)
    preferred = design_preferences.read_preferred(repo, owner, event_id) if record is None else None
    suggestions = [
        ScheduleItem(title=t.title, date=t.planned_start.date(), start_at=t.planned_start)
        for t in day.tasks
        if t.planned_start is not None
    ][:30]
    return _state(base, record, defaults(base, preferred, day) if record is None else None, suggestions)


def mutate(repo, owner, event_id, body, operation):
    with repo._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        base = repo._read(connection, owner, str(event_id))
        record = _read(connection, owner, base.id)
        fingerprint = hashlib.sha256(
            (operation + body.model_dump_json(exclude={"request_id"})).encode()
        ).hexdigest()
        if record and record.last_request == body.request_id:
            if record.last_fingerprint != fingerprint:
                raise RevisionConflict
            return _state(base, record)
        if (operation != "unpublish" and body.event_revision != base.revision) or body.revision != (
            record.revision if record else 0
        ):
            raise RevisionConflict
        if operation == "save":
            if record is None:
                record = WebsiteRecord(
                    event_id=base.id,
                    revision=1,
                    saved_event_revision=base.revision,
                    slug=secrets.token_urlsafe(24),
                    draft=body.config,
                    last_request=body.request_id,
                    last_fingerprint=fingerprint,
                )
            else:
                record.draft = body.config
                record.saved_event_revision = base.revision
                record.revision += 1
        else:
            if record is None:
                raise RevisionConflict
            if operation == "publish":
                if body.preview_hash != preview_hash(record.draft):
                    raise HTTPException(
                        status_code=409, detail="Preview the current saved draft before publishing"
                    )
                record.published = project(record.draft, secrets.token_urlsafe(18))
                record.published_at = datetime.now(UTC)
            else:
                record.published = record.published_at = None
            record.revision += 1
        record.last_request, record.last_fingerprint = body.request_id, fingerprint
        _schema(connection)
        connection.execute(
            "INSERT INTO event_websites VALUES(?,?,1,?,?,?) ON CONFLICT(event_id) DO UPDATE SET "
            "revision=excluded.revision,document=excluded.document",
            (str(base.id), owner, record.revision, record.slug, record.model_dump_json()),
        )
        return _state(base, record)


def _published(connection, slug):
    if not _exists(connection):
        raise HTTPException(status_code=404, detail="Invitation not available")
    row = connection.execute(
        "SELECT w.* FROM event_websites w JOIN events e ON e.id=w.event_id "
        "AND e.owner=w.owner WHERE w.slug=?",
        (slug,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Invitation not available")
    owner, record = _decode(row)
    if record.published is None:
        raise HTTPException(status_code=404, detail="Invitation not available")
    return owner, record


def public_read(repo, slug):
    with repo._connection() as connection:
        return _published(connection, slug)[1].published


def _identity(name, email):
    text = "email:" + email.casefold() if email else "name:" + name.casefold()
    return hashlib.sha256(text.encode()).hexdigest()


def submit(repo, slug, body):
    with repo._connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        owner, record = _published(connection, slug)
        public = record.published
        if not public.rsvp.enabled:
            raise HTTPException(status_code=403, detail="Public responses are not enabled")
        if body.edition != public.edition:
            raise HTTPException(status_code=409, detail="This invitation changed. Reload before responding")
        if body.attendees > public.rsvp.max_attendees or (public.rsvp.email_required and not body.email):
            raise HTTPException(status_code=422, detail="Check the party-size limit and required email")
        base = repo._read(connection, owner, str(record.event_id))
        key = hashlib.sha256(str(body.request_id).encode()).hexdigest()
        identity = _identity(body.name, body.email)
        fingerprint = hashlib.sha256(body.model_dump_json(exclude={"request_id"}).encode()).hexdigest()
        if _exists(connection, "website_responses"):
            old = connection.execute(
                "SELECT fingerprint FROM website_responses WHERE event_id=? AND request_key=?",
                (str(base.id), key),
            ).fetchone()
            if old:
                if old[0] != fingerprint:
                    raise HTTPException(status_code=409, detail="Use a new request for a different response")
                return ResponseAcknowledgement()
            duplicate = connection.execute(
                "SELECT 1 FROM website_responses WHERE event_id=? AND identity_key=?",
                (str(base.id), identity),
            ).fetchone()
            if duplicate:
                return ResponseAcknowledgement()
            count = connection.execute(
                "SELECT COUNT(*) FROM website_responses WHERE event_id=?", (str(base.id),)
            ).fetchone()[0]
            if count >= 1000:
                raise HTTPException(status_code=429, detail="Response capacity reached. Contact the host")
        roster = guests._rows(connection, owner, base.id)
        # No public caller can claim/edit an existing private party by knowing its name/email.
        if any(_identity(g.name, g.email) == identity for g in roster):
            return ResponseAcknowledgement()
        values = GuestValues(
            name=body.name,
            email=body.email,
            rsvp=body.rsvp,
            plus_ones=body.attendees - 1,
            dietary=body.dietary,
            notes="Public website response (unverified). " + body.message,
        )
        guest = guests.add_public(connection, repo, owner, base, values)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS website_responses (event_id TEXT NOT NULL "
            "REFERENCES event_websites(event_id) ON DELETE CASCADE, request_key TEXT NOT NULL, "
            "identity_key TEXT NOT NULL, fingerprint TEXT NOT NULL, guest_id TEXT "
            "REFERENCES guests(id) ON DELETE SET NULL, PRIMARY KEY(event_id,request_key), "
            "UNIQUE(event_id,identity_key))"
        )
        connection.execute(
            "INSERT INTO website_responses VALUES(?,?,?,?,?)",
            (str(base.id), key, identity, fingerprint, str(guest.id)),
        )
        return ResponseAcknowledgement()
