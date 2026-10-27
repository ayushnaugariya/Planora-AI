"""SQLite connection and initialization lifecycle, preserving existing locking."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import closing, contextmanager
from pathlib import Path

from app.core.errors import StorageUnavailable
from app.db.migrations import migrate


class SQLiteStore:
    def __init__(self, path: str | Path, *, enabled: bool = True):
        self.path = Path(path)
        self.enabled = enabled
        self._initialized = False
        self._lock = threading.Lock()

    def initialize(self) -> None:
        if not self.enabled:
            raise StorageUnavailable("SQLite workspaces require a durable single-instance deployment")
        with self._lock:
            if self._initialized:
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                migrate(connection)
            self._initialized = True

    @contextmanager
    def _connection(self):
        try:
            self.initialize()
            with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
                connection.execute("PRAGMA foreign_keys=ON")
                yield connection
        except (sqlite3.Error, OSError) as exc:
            raise StorageUnavailable from exc
