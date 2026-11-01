"""Optional additive table migration; existing workspace user_version remains 2."""

import sqlite3


def ensure_design_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS design_preferences ("
        "event_id TEXT PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE, "
        "owner TEXT NOT NULL, format_version INTEGER NOT NULL CHECK(format_version=1), "
        "document TEXT NOT NULL)"
    )
