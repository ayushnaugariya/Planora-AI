"""Workspace durability, identity, transaction and API compatibility tests."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date, timedelta
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import main
from app.api.dependencies import COOKIE
from app.core import security
from app.core.errors import RevisionConflict, StorageUnavailable, UnsupportedSchema
from app.repositories.workspaces import WorkspaceRepository
from app.schemas import planning as models
from app.schemas.workspaces import EventDetails, EventWorkspace
from tests.conftest import payload
from tests.integration.test_ai_and_api import GOOD, FakeLLM
from tests.security.test_request_limits import asgi_request, assert_security_headers, request_chunks


def create(client, **overrides):
    response = client.post("/api/events", json={"details": payload(**overrides)})
    assert response.status_code == 201, response.text
    assert_security_headers(response)
    return response.json()


def db_execute(client, sql, parameters=()):
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as connection, connection:
        return connection.execute(sql, parameters).fetchall()


def test_create_list_reopen_complete_workspace(client):
    event = create(
        client,
        venue_preferences="Garden",
        cultural_requirements="Family ceremony",
        accessibility_requirements="Step-free access",
        assumptions="40 seats available",
        unresolved_decisions="Choose the menu",
    )
    assert client.get(f"/api/events/{event['id']}").json() == event
    assert client.get("/api/events").json()[0]["id"] == event["id"]
    assert event["details"]["cultural_requirements"] == "Family ceremony"
    assert event["details"]["accessibility_requirements"] == "Step-free access"
    assert event["details"]["venue_preferences"] == "Garden"
    assert event["details"]["assumptions"] == "40 seats available"
    assert event["details"]["unresolved_decisions"] == "Choose the menu"
    assert event["history"][0]["revision"] == event["revision"] == 1
    assert event["created_at"] == event["updated_at"] == event["generated_at"]
    assert event["expenses"] == []
    assert sum(line["amount"] for line in event["plan"]["budget_lines"]) == 60_000
    ids = [
        event["id"],
        *[task["id"] for task in event["tasks"]],
        *[vendor["id"] for vendor in event["vendors"]],
    ]
    ids += [item["id"] for vendor in event["vendors"] for item in vendor["checklist"]]
    assert len(set(ids)) == len(ids)
    assert all(UUID(value) for value in ids)


def test_cookie_is_not_an_event_record_or_api_key(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-not-for-event-storage")
    response = client.get("/api/events")
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie and "Max-Age=31536000" in cookie
    event = create(client)
    document, owner = db_execute(client, "SELECT document, owner FROM events")[0]
    assert client.cookies.get(COOKIE) not in document + owner
    assert "secret-not-for-event-storage" not in document
    assert "owner" not in event


def test_workspace_survives_repository_and_application_reconnection(client):
    event = create(client)
    path = client.app.state.workspace_repository.path
    owner = db_execute(client, "SELECT owner FROM events")[0][0]
    assert WorkspaceRepository(path).get(owner, event["id"]).model_dump(mode="json") == event
    token = client.cookies.get(COOKIE)
    with TestClient(main.app) as reopened:
        reopened.cookies.set(COOKIE, token)
        assert reopened.get(f"/api/events/{event['id']}").json() == event
        assert reopened.get("/api/events").json()[0]["id"] == event["id"]


def test_update_one_event_preserves_other_and_child_ids(client):
    event, other = create(client), create(client, title="Another event")
    completed_task = next(
        task
        for task in event["tasks"]
        if event["plan"]["timeline"][task["milestone_index"]]["category"] != "event"
    )
    completed_check = event["vendors"][0]["checklist"][0]
    url = f"/api/events/{event['id']}"
    response = client.patch(
        url,
        json={
            "revision": 1,
            "progress": {
                "completed_tasks": [completed_task["id"]],
                "completed_checks": [completed_check["id"]],
            },
        },
    )
    assert response.status_code == 200
    progress = response.json()
    changed = {
        **event["details"],
        "budget": 123457,
        "guest_count": 67,
        "event_date": (date.today() + timedelta(days=12)).isoformat(),
    }
    response = client.patch(url, json={"revision": 2, "details": changed})
    assert response.status_code == 200, response.text
    updated = response.json()
    assert [task["id"] for task in updated["tasks"]] == [task["id"] for task in event["tasks"]]
    assert [v["id"] for v in updated["vendors"]] == [v["id"] for v in event["vendors"]]
    assert [v["checklist"] for v in updated["vendors"]] == [v["checklist"] for v in progress["vendors"]]
    assert next(task for task in updated["tasks"] if task["id"] == completed_task["id"])["completed"]
    assert sum(line["amount"] for line in updated["plan"]["budget_lines"]) == 123457
    assert updated["revision"] == 3 and len(updated["history"]) == 3
    assert updated["generated_at"] != event["generated_at"]
    assert client.get(url).json() == updated
    assert client.get(f"/api/events/{other['id']}").json() == other
    amounts = {line["key"]: line["amount"] for line in updated["plan"]["budget_lines"]}
    assert all(v["budget"] == amounts[v["key"]] for v in updated["plan"]["vendors"])
    assert all(
        date.today().isoformat() <= task["due"] <= changed["event_date"]
        for task in updated["plan"]["timeline"]
    )


def test_saved_regeneration_chat_and_calendar(client):
    event = create(client)
    client.app.state.llm = FakeLLM(GOOD)
    url = f"/api/events/{event['id']}"
    response = client.post(url + "/regenerate", json={"revision": 1})
    assert response.status_code == 200
    rebuilt = response.json()
    assert rebuilt["plan"]["ai_source"] == "gemini"
    assert client.get(url).json() == rebuilt
    client.app.state.llm = None
    response = client.post(url + "/chat", json={"revision": 2, "question": "Where can I save money?"})
    assert response.status_code == 200
    saved = response.json()
    assert len(saved["chat"]) == 2
    assert saved["chat"][0]["role"] == "user" and saved["chat"][1]["source"] == "offline"
    assert client.get(url).json() == saved
    response = client.get(url + "/ics")
    assert response.status_code == 200 and response.text.startswith("BEGIN:VCALENDAR")
    assert_security_headers(response)
    assert all(task["due"].replace("-", "") in response.text for task in saved["plan"]["timeline"])


def test_historical_events_remain_readable_renameable_and_chattable(client, monkeypatch):
    event = create(client)

    class LaterDate(date):
        @classmethod
        def today(cls):
            return date.today() + timedelta(days=500)

    monkeypatch.setattr(models, "date", LaterDate)
    with pytest.raises(ValidationError):
        models.PlanRequest.model_validate(event["details"])
    url = f"/api/events/{event['id']}"
    assert client.get(url).json() == event
    assert client.post(url + "/regenerate", json={"revision": 1}).status_code == 422
    assert client.get(url).json() == event
    renamed = client.patch(url, json={"revision": 1, "title": "A new name"}).json()
    assert renamed["plan"]["title"] == renamed["details"]["title"] == "A new name"
    assert client.post(url + "/chat", json={"revision": 2, "question": "budget?"}).status_code == 200


@pytest.mark.parametrize(
    "update",
    [
        {"details": {"guest_count": 1}},
        {"title": "x" * 81},
        {},
        {"title": "Name", "progress": {}},
        {"progress": {"completed_tasks": [str(uuid4())], "completed_checks": []}},
        {"expense_edit": 42},
    ],
)
def test_invalid_updates_are_not_partial_writes(client, update):
    event = create(client)
    url = f"/api/events/{event['id']}"
    if "details" in update:
        update = {"details": {**event["details"], **update["details"]}}
    response = client.patch(url, json={"revision": 1, **update})
    assert response.status_code == 422
    assert_security_headers(response)
    assert client.get(url).json() == event


def test_type_change_does_not_discard_child_data(client):
    event = create(client)
    url = f"/api/events/{event['id']}"
    response = client.patch(
        url, json={"revision": 1, "details": {**event["details"], "event_type": "wedding"}}
    )
    assert response.status_code == 422
    assert client.get(url).json() == event


def test_stale_mutations_and_delete_require_current_revision(client):
    event = create(client)
    url = f"/api/events/{event['id']}"
    renamed = client.patch(url, json={"revision": 1, "title": "Renamed"}).json()
    assert client.patch(url, json={"revision": 1, "title": "Lost update"}).status_code == 409
    assert client.post(url + "/regenerate", json={"revision": 1}).status_code == 409
    assert client.request("DELETE", url, json={"revision": 1, "confirm_id": event["id"]}).status_code == 409
    assert client.get(url).json() == renamed


def test_confirmed_delete_removes_only_that_document(client):
    event, other = create(client), create(client, title="Keep this event")
    url = f"/api/events/{event['id']}"
    assert client.request("DELETE", url, json={"revision": 1, "confirm_id": str(uuid4())}).status_code == 422
    assert client.get(url).json() == event
    response = client.request("DELETE", url, json={"revision": 1, "confirm_id": event["id"]})
    assert response.status_code == 204 and response.content == b""
    assert_security_headers(response)
    assert client.get(url).status_code == 404
    assert client.patch(url, json={"revision": 1, "title": "Missing"}).status_code == 404
    assert client.get(f"/api/events/{other['id']}").json() == other
    assert [row["id"] for row in client.get("/api/events").json()] == [other["id"]]


def test_cookie_isolation_not_just_unpredictable_event_ids(client):
    event = create(client)
    with TestClient(main.app) as other:
        assert other.get("/api/events").json() == []
        url = f"/api/events/{event['id']}"
        assert other.get(url).status_code == 404
        assert other.patch(url, json={"revision": 1, "title": "Stolen"}).status_code == 404
        assert (
            other.request("DELETE", url, json={"revision": 1, "confirm_id": event["id"]}).status_code == 404
        )
    assert client.get(f"/api/events/{event['id']}").json() == event


@pytest.mark.parametrize(
    "headers",
    [
        {"origin": "https://evil.test"},
        {"sec-fetch-site": "cross-site"},
        {"origin": "null"},
    ],
)
def test_cross_origin_workspace_mutations_rejected(client, headers):
    response = client.post("/api/events", json={"details": payload()}, headers=headers)
    assert response.status_code == 403
    assert client.get("/api/events").json() == []


def test_same_origin_and_https_cookie_flags(client):
    assert (
        client.post(
            "/api/events", json={"details": payload()}, headers={"origin": "http://testserver"}
        ).status_code
        == 201
    )
    with TestClient(main.app, base_url="https://testserver") as secure:
        response = secure.get("/api/events")
        assert "Secure" in response.headers["set-cookie"]
        assert response.json() == []


def test_explicit_legacy_import_retains_matching_progress(client):
    response = client.post(
        "/api/events",
        json={
            "details": payload(),
            "legacy_progress": {
                "timeline": [0],
                "vendors": ["venue:0"],
            },
        },
    )
    assert response.status_code == 201
    event = response.json()
    assert event["tasks"][0]["completed"]
    venue = next(v for v in event["vendors"] if event["plan"]["vendors"][v["group_index"]]["key"] == "venue")
    assert venue["checklist"][0]["completed"]
    assert "imported" in event["history"][0]["summary"]


@pytest.mark.parametrize(
    "progress",
    [
        {"timeline": [-1]},
        {"timeline": [999]},
        {"vendors": ["unknown:0"]},
        {"timeline": [8]},
    ],
)
def test_bad_legacy_import_does_not_create_partial_event(client, progress):
    response = client.post("/api/events", json={"details": payload(), "legacy_progress": progress})
    assert response.status_code == 422
    assert client.get("/api/events").json() == []


def test_create_and_save_failure_never_report_success(client, monkeypatch):
    repo = client.app.state.workspace_repository
    with monkeypatch.context() as scoped:
        scoped.setattr(repo, "create", Mock(side_effect=StorageUnavailable))
        response = client.post("/api/events", json={"details": payload()})
        assert response.status_code == 503
        assert_security_headers(response)
    assert client.get("/api/events").json() == []
    event = create(client)
    url = f"/api/events/{event['id']}"
    with monkeypatch.context() as scoped:
        scoped.setattr(repo, "save", Mock(side_effect=StorageUnavailable))
        assert client.patch(url, json={"revision": 1, "title": "Not saved"}).status_code == 503
        assert client.post(url + "/chat", json={"revision": 1, "question": "budget?"}).status_code == 503
    assert client.get(url).json() == event


def test_sqlite_transaction_failure_rolls_back_document_and_history(client):
    event = create(client)
    db_execute(
        client,
        "CREATE TRIGGER reject_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'blocked'); END",
    )
    url = f"/api/events/{event['id']}"
    response = client.patch(url, json={"revision": 1, "title": "Cannot commit"})
    assert response.status_code == 503 and "blocked" not in response.text
    assert client.get(url).json() == event


def test_initialization_is_idempotent_and_does_not_replace_data(client):
    event = create(client)
    path = client.app.state.workspace_repository.path
    WorkspaceRepository(path).initialize()
    WorkspaceRepository(path).initialize()
    assert db_execute(client, "PRAGMA user_version") == [(2,)]
    assert client.get(f"/api/events/{event['id']}").json() == event


@pytest.mark.parametrize("unknown_version", [False, True])
def test_unknown_schema_never_reinitialized(tmp_path, unknown_version):
    path = tmp_path / "unknown.sqlite3"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE precious_data(value TEXT)")
        connection.execute("INSERT INTO precious_data VALUES ('keep')")
        if unknown_version:
            connection.execute("PRAGMA user_version=99")
    with pytest.raises(UnsupportedSchema):
        WorkspaceRepository(path).initialize()
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("SELECT * FROM precious_data").fetchall() == [("keep",)]


def test_unavailable_database_keeps_stateless_planner_usable(tmp_path, monkeypatch):
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("keep")
    monkeypatch.setenv("EVENTRA_DB_PATH", str(blocked / "events.sqlite3"))
    security._hits.clear()
    with TestClient(main.app) as client:
        client.app.state.llm = None
        assert client.get("/healthz").status_code == 200
        assert client.post("/api/plan", json=payload()).status_code == 200
        response = client.get("/api/events")
        assert response.status_code == 503
        assert_security_headers(response)
    assert blocked.read_text() == "keep"


@pytest.mark.parametrize("damage", ["json", "revision"])
def test_corrupt_workspace_not_silently_overwritten(client, damage):
    event = create(client)
    if damage == "json":
        db_execute(client, "UPDATE events SET document='{}'")
    else:
        db_execute(client, "UPDATE events SET revision=99")
    response = client.get(f"/api/events/{event['id']}")
    assert response.status_code == 503


def test_repository_atomic_revision_check_with_concurrent_writers(client):
    event = create(client)
    owner = db_execute(client, "SELECT owner FROM events")[0][0]
    path = client.app.state.workspace_repository.path

    def attempt(name):
        workspace = EventWorkspace.model_validate(event)
        workspace.revision = 2
        workspace.details.title = name
        try:
            WorkspaceRepository(path).save(owner, workspace, 1)
            return "saved"
        except RevisionConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(attempt, ["First", "Second"])) == ["conflict", "saved"]
    workspace = WorkspaceRepository(path).get(owner, event["id"])
    with pytest.raises(RevisionConflict):
        WorkspaceRepository(path).save(owner, workspace, workspace.revision)


def test_workspace_routes_keep_actual_request_limit(client):
    body = json.dumps({"details": payload()}).encode()
    response, received = asgi_request(request_chunks([body + b" " * 20_001, b"unread"]), path="/api/events")
    assert response.status_code == 413 and len(received) == 1
    assert_security_headers(response)
    assert client.get("/api/events").json() == []


def test_historical_schema_and_future_creation_validation_are_separate():
    details = EventDetails.model_validate(payload(event_date=(date.today() - timedelta(days=1)).isoformat()))
    with pytest.raises(ValidationError):
        details.planning_request()


def test_cloud_run_does_not_report_ephemeral_sqlite_saves_as_durable(tmp_path, monkeypatch):
    path = tmp_path / "must-not-create.sqlite3"
    monkeypatch.setenv("K_SERVICE", "eventra")
    monkeypatch.setenv("EVENTRA_DB_PATH", str(path))
    security._hits.clear()
    with TestClient(main.app) as client:
        client.app.state.llm = None
        assert client.get("/healthz").status_code == 200
        assert client.post("/api/plan", json=payload()).status_code == 200
        response = client.post("/api/events", json={"details": payload()})
        assert response.status_code == 503
        assert_security_headers(response)
    assert not path.exists()
