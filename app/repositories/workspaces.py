"""Owned workspace/scenario persistence and transactional CAS operations."""

from __future__ import annotations

from datetime import date

from pydantic import ValidationError

from app.core.errors import RevisionConflict, UnsupportedSchema, WorkspaceNotFound
from app.db.sqlite import SQLiteStore
from app.schemas.scenarios import Scenario
from app.schemas.workspaces import EventSummary, EventWorkspace

EXPENSE_DERIVED = {"line_total", "estimate", "payment_status"}
WORKSPACE_DERIVED = {"budget_summary": True, "expenses": {"__all__": EXPENSE_DERIVED}}
SCENARIO_DERIVED = {"expense_changes": {"__all__": {"before": EXPENSE_DERIVED, "after": EXPENSE_DERIVED}}}


class WorkspaceRepository(SQLiteStore):
    @staticmethod
    def _decode(document: str) -> EventWorkspace:
        try:
            return EventWorkspace.model_validate_json(document)
        except ValidationError as exc:
            raise UnsupportedSchema("Invalid saved workspace") from exc

    @staticmethod
    def _check_record(workspace, event_id, revision):
        if str(workspace.id) != str(event_id) or workspace.revision != revision:
            raise UnsupportedSchema("Workspace identity/revision integrity check failed")

    @staticmethod
    def _read(connection, owner: str, event_id: str) -> EventWorkspace:
        row = connection.execute(
            "SELECT document, revision FROM events WHERE id=? AND owner=?", (event_id, owner)
        ).fetchone()
        if row is None:
            raise WorkspaceNotFound
        workspace = WorkspaceRepository._decode(row[0])
        WorkspaceRepository._check_record(workspace, event_id, row[1])
        return workspace

    def create(self, owner: str, workspace: EventWorkspace, *, if_absent: bool = False) -> EventWorkspace:
        with self._connection() as connection:
            if if_absent:
                connection.execute("BEGIN IMMEDIATE")
                exists = connection.execute(
                    "SELECT 1 FROM events WHERE id=?", (str(workspace.id),)
                ).fetchone()
                if exists:
                    # Retry returns current state, never overwrites an edited demo.
                    return self._read(connection, owner, str(workspace.id))
            connection.execute(
                "INSERT INTO events(id, owner, revision, document) VALUES (?, ?, ?, ?)",
                (
                    str(workspace.id),
                    owner,
                    workspace.revision,
                    workspace.model_dump_json(exclude=WORKSPACE_DERIVED),
                ),
            )
        return workspace

    def get(self, owner: str, event_id: str) -> EventWorkspace:
        with self._connection() as connection:
            return self._read(connection, owner, event_id)

    def list(self, owner: str) -> list[EventSummary]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT id, document, revision FROM events WHERE owner=?", (owner,)
            ).fetchall()
        events = []
        for event_id, document, revision in rows:
            workspace = self._decode(document)
            self._check_record(workspace, event_id, revision)
            events.append(workspace)
        events.sort(key=lambda event: event.updated_at, reverse=True)
        return [
            EventSummary(
                id=event.id,
                title=event.plan.title,
                event_date=event.details.event_date.isoformat(),
                revision=event.revision,
                updated_at=event.updated_at,
            )
            for event in events
        ]

    def save(self, owner: str, workspace: EventWorkspace, expected_revision: int) -> EventWorkspace:
        with self._connection() as connection:
            # Acquire the write lock before checking existence/revision; the
            # complete document and history are committed or rolled back together.
            connection.execute("BEGIN IMMEDIATE")
            self._save(connection, owner, workspace, expected_revision)
        return workspace

    @staticmethod
    def _save(connection, owner, workspace, expected_revision):
        """CAS write inside an existing transaction, also used by owned child edits."""
        current = WorkspaceRepository._read(connection, owner, str(workspace.id))
        if current.revision != expected_revision:
            raise RevisionConflict
        if workspace.revision != expected_revision + 1:
            raise RevisionConflict
        connection.execute(
            "UPDATE events SET revision=?, document=? WHERE id=? AND owner=?",
            (
                workspace.revision,
                workspace.model_dump_json(exclude=WORKSPACE_DERIVED),
                str(workspace.id),
                owner,
            ),
        )

    def delete(self, owner: str, event_id: str, expected_revision: int) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            current = self._read(connection, owner, event_id)
            if current.revision != expected_revision:
                raise RevisionConflict
            # All child state and audit entries live in this owned document:
            # deletion cannot leave orphan records or affect any other event.
            connection.execute("DELETE FROM events WHERE id=? AND owner=?", (event_id, owner))

    @staticmethod
    def _scenario(connection, owner, event_id, scenario_id):
        row = connection.execute(
            "SELECT document FROM scenarios WHERE id=? AND event_id=? AND owner=?",
            (scenario_id, event_id, owner),
        ).fetchone()
        if row is None:
            raise WorkspaceNotFound
        try:
            result = Scenario.model_validate_json(row[0])
        except ValidationError as exc:
            raise UnsupportedSchema("Invalid saved scenario") from exc
        if str(result.event_id) != event_id:
            raise UnsupportedSchema("Scenario event integrity check failed")
        return result

    def create_scenario(self, owner, scenario):
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            event = self._read(connection, owner, str(scenario.event_id))
            if event.revision != scenario.base_revision:
                raise RevisionConflict
            connection.execute(
                "INSERT INTO scenarios(id,event_id,owner,document) VALUES(?,?,?,?)",
                (
                    str(scenario.id),
                    str(scenario.event_id),
                    owner,
                    scenario.model_dump_json(exclude=SCENARIO_DERIVED),
                ),
            )
        return scenario

    def get_scenario(self, owner, event_id, scenario_id):
        with self._connection() as connection:
            event = self._read(connection, owner, event_id)
            scenario = self._scenario(connection, owner, event_id, scenario_id)
            scenario.stale = event.revision != scenario.base_revision or scenario.evaluated_on != date.today()
            return scenario

    def create_scenario_batch(self, owner, scenarios, request_id):
        """Save a bounded recovery assessment atomically, with request-ID retry checks."""
        if not 1 <= len(scenarios) <= 3:
            raise ValueError("A recovery assessment requires one to three options")
        first = scenarios[0]
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            event = self._read(connection, owner, str(first.event_id))
            if any(item.event_id != event.id or item.base_revision != event.revision for item in scenarios):
                raise RevisionConflict
            # IDs are derived from a request UUID plus option index. A retry must
            # have the exact same option set/parameters, including omitted slots.
            from uuid import uuid5

            expected_ids = {str(uuid5(request_id, str(i))) for i in range(len(scenarios))}
            if {str(item.id) for item in scenarios} != expected_ids:
                raise ValueError("Recovery option IDs must match the request slots")
            for i in range(len(scenarios), 3):
                if connection.execute(
                    "SELECT 1 FROM scenarios WHERE id=?", (str(uuid5(request_id, str(i))),)
                ).fetchone():
                    raise RevisionConflict
            # Each caller supplies all slots; existing IDs may never be overwritten.
            saved = []
            for item in scenarios:
                row = connection.execute(
                    "SELECT owner,event_id,document FROM scenarios WHERE id=?", (str(item.id),)
                ).fetchone()
                if row:
                    if row[0] != owner or row[1] != str(event.id):
                        raise RevisionConflict
                    prior = self._scenario(connection, owner, str(event.id), str(item.id))
                    if prior.base_revision != item.base_revision or prior.parameters != item.parameters:
                        raise RevisionConflict
                    prior.stale = prior.evaluated_on != date.today()
                    saved.append(prior)
                else:
                    saved.append(item)
            if any(a is not b for a, b in zip(saved, scenarios, strict=True)):
                if any(a is b for a, b in zip(saved, scenarios, strict=True)):
                    raise RevisionConflict
                return saved
            for item in scenarios:
                connection.execute(
                    "INSERT INTO scenarios(id,event_id,owner,document) VALUES(?,?,?,?)",
                    (str(item.id), str(item.event_id), owner, item.model_dump_json(exclude=SCENARIO_DERIVED)),
                )
        return scenarios

    def list_scenarios(self, owner, event_id):
        with self._connection() as connection:
            event = self._read(connection, owner, event_id)
            rows = connection.execute(
                "SELECT id FROM scenarios WHERE event_id=? AND owner=? ORDER BY rowid DESC", (event_id, owner)
            ).fetchall()
            result = [self._scenario(connection, owner, event_id, row[0]) for row in rows]
        for scenario in result:
            scenario.stale = event.revision != scenario.base_revision or scenario.evaluated_on != date.today()
        return result

    def discard_scenario(self, owner, event_id, scenario_id):
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._read(connection, owner, event_id)
            scenario = self._scenario(connection, owner, event_id, scenario_id)
            if scenario.status == "applied":
                raise RevisionConflict
            scenario.status = "discarded"
            connection.execute(
                "UPDATE scenarios SET document=? WHERE id=? AND owner=?",
                (scenario.model_dump_json(exclude=SCENARIO_DERIVED), scenario_id, owner),
            )
        return scenario

    def apply_scenario(self, owner, event_id, scenario_id, expected_revision, proposed):
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            event = self._read(connection, owner, event_id)
            scenario = self._scenario(connection, owner, event_id, scenario_id)
            if scenario.status == "applied":
                return event
            if (
                scenario.status != "pending"
                or scenario.feasibility != "feasible"
                or event.revision != expected_revision
                or scenario.base_revision != expected_revision
                or scenario.evaluated_on != date.today()
                or proposed.id != event.id
                or proposed.revision != expected_revision + 1
            ):
                raise RevisionConflict
            connection.execute(
                "UPDATE events SET revision=?,document=? WHERE id=? AND owner=?",
                (proposed.revision, proposed.model_dump_json(exclude=WORKSPACE_DERIVED), event_id, owner),
            )
            scenario.status, scenario.applied_revision = "applied", proposed.revision
            connection.execute(
                "UPDATE scenarios SET document=? WHERE id=? AND event_id=? AND owner=?",
                (scenario.model_dump_json(exclude=SCENARIO_DERIVED), scenario_id, event_id, owner),
            )
        return proposed
