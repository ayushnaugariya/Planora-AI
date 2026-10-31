"""Cross-feature regressions established during the final integration audit."""

import json
import sqlite3
from contextlib import closing
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import main
from app.schemas.command_center import DayDocument, OperationalTask
from tests.integration.test_command_center import write
from tests.integration.test_workspaces import create
from tests.security.test_request_limits import assert_security_headers


@pytest.mark.parametrize("kind", ["planning_task", "vendor_check"])
def test_legacy_progress_preserves_command_center_event_completion(client, kind):
    event = create(client)
    milestone = next(
        t for t in event["tasks"] if event["plan"]["timeline"][t["milestone_index"]]["category"] == "event"
    )
    result, _ = write(client, event, "task", {"status": "completed"}, milestone["id"])
    event = result["workspace"]
    actual = next(t for t in result["dashboard"]["tasks"] if t["id"] == milestone["id"])[
        "actual_completed_at"
    ]
    planning = next(t for t in event["tasks"] if t["id"] != milestone["id"])
    progress = {
        "completed_tasks": [planning["id"]] if kind == "planning_task" else [],
        "completed_checks": [event["vendors"][0]["checklist"][0]["id"]] if kind == "vendor_check" else [],
    }
    response = client.patch(
        f"/api/events/{event['id']}", json={"revision": event["revision"], "progress": progress}
    )
    assert response.status_code == 200, response.text
    saved = response.json()
    assert next(t for t in saved["tasks"] if t["id"] == milestone["id"])["completed"], (
        "Saving unrelated legacy progress must not undo event-day completion"
    )
    view = client.get(f"/api/events/{event['id']}/command-center").json()
    item = next(t for t in view["tasks"] if t["id"] == milestone["id"])
    assert item["status"] == "completed" and item["actual_completed_at"] == actual
    assert saved["budget_summary"] == event["budget_summary"] and saved["details"] == event["details"]
    # The legacy contract still excludes event-category IDs; only Command Center manages those.
    rejected = client.patch(
        f"/api/events/{event['id']}",
        json={
            "revision": saved["revision"],
            "progress": {"completed_tasks": [milestone["id"]], "completed_checks": []},
        },
    )
    assert rejected.status_code == 422
    assert_security_headers(rejected)


def test_stored_task_capacity_rejects_retired_metadata_without_500_or_data_loss(client):
    event = create(client)
    # Retired overlays are a supported persisted shape (the projection deliberately hides them).
    # A future template rebuild must not turn a bounded new operation into an unhandled serializer error.
    document = DayDocument(
        event_id=event["id"],
        tasks=[OperationalTask(id=uuid4(), title=f"Retired milestone {n}") for n in range(200)],
    )
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as connection, connection:
        connection.execute(
            "CREATE TABLE event_day (event_id TEXT PRIMARY KEY REFERENCES events(id) "
            "ON DELETE CASCADE,owner TEXT NOT NULL,format_version INTEGER NOT NULL,document TEXT NOT NULL)"
        )
        owner = connection.execute("SELECT owner FROM events WHERE id=?", (event["id"],)).fetchone()[0]
        connection.execute(
            "INSERT INTO event_day VALUES(?,?,1,?)", (event["id"], owner, document.model_dump_json())
        )
    with TestClient(main.app, cookies=client.cookies, raise_server_exceptions=False) as browser:
        before = browser.get(f"/api/events/{event['id']}/command-center")
        assert before.status_code == 200
        response = browser.post(
            f"/api/events/{event['id']}/command-center/operations",
            json={
                "revision": 1,
                "request_id": str(uuid4()),
                "approved": True,
                "operation": {"kind": "task", "id": str(uuid4()), "value": {"title": "New operation"}},
            },
        )
        assert response.status_code == 422, response.text
        assert_security_headers(response)
        assert browser.get(f"/api/events/{event['id']}").json() == event
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as connection:
        assert (
            connection.execute("SELECT document FROM event_day").fetchone()[0] == document.model_dump_json()
        )


@pytest.mark.parametrize("damage", ["identity", "revision"])
@pytest.mark.parametrize("listing", [False, True])
def test_workspace_row_metadata_mismatch_fails_closed(client, damage, listing):
    one, two = create(client), create(client)
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as connection, connection:
        document = json.loads(
            connection.execute("SELECT document FROM events WHERE id=?", (one["id"],)).fetchone()[0]
        )
        if damage == "identity":
            document["id"] = two["id"]
        else:
            document["revision"] = 99
        stored = json.dumps(document)
        connection.execute("UPDATE events SET document=? WHERE id=?", (stored, one["id"]))
    response = client.get("/api/events" if listing else f"/api/events/{one['id']}")
    assert response.status_code == 503, response.text
    assert_security_headers(response)
    assert client.get(f"/api/events/{two['id']}").json() == two
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as connection:
        assert (
            connection.execute("SELECT document FROM events WHERE id=?", (one["id"],)).fetchone()[0] == stored
        )
