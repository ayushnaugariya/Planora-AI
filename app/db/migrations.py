"""Existing transactional SQLite schema 0/1 to 2 migration."""

import json

from app.core.errors import UnsupportedSchema
from app.schemas.workspaces import EventWorkspace


def migrate(connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version not in (0, 1, 2):
        raise UnsupportedSchema("Unsupported workspace schema version")
    if version == 0:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        if tables:
            raise UnsupportedSchema("Refusing to initialize a nonempty unversioned database")
        connection.execute(
            "CREATE TABLE events (id TEXT PRIMARY KEY, owner TEXT NOT NULL, "
            "revision INTEGER NOT NULL CHECK(revision > 0), document TEXT NOT NULL)"
        )
        connection.execute("CREATE INDEX events_owner ON events(owner)")
        connection.execute("PRAGMA user_version=1")
    if version < 2:
        for event_id, document in connection.execute("SELECT id, document FROM events").fetchall():
            try:
                raw = json.loads(document)
                raw["schema_version"] = 2
                for expense in raw.get("expenses", []):
                    if "amount" in expense:
                        amount = expense.pop("amount")
                        expense.update(
                            event_id=event_id,
                            currency=raw["details"]["currency"],
                            unit_amount=str(amount),
                            provenance="legacy",
                            created_at=raw["created_at"],
                            updated_at=raw["updated_at"],
                        )
                EventWorkspace.model_validate(raw)
            except (ValueError, KeyError, TypeError) as exc:
                raise UnsupportedSchema("Cannot safely migrate workspace data") from exc
            connection.execute("UPDATE events SET document=? WHERE id=?", (json.dumps(raw), event_id))
        connection.execute(
            "CREATE TABLE scenarios (id TEXT PRIMARY KEY, event_id TEXT NOT NULL "
            "REFERENCES events(id) ON DELETE CASCADE, "
            "owner TEXT NOT NULL, document TEXT NOT NULL)"
        )
        connection.execute("CREATE INDEX scenarios_event ON scenarios(event_id, owner)")
        connection.execute("PRAGMA user_version=2")
