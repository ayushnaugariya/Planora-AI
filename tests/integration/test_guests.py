"""Private guest lifecycle, RSVP arithmetic and transactional ownership boundaries."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import main
from app.core.errors import StorageUnavailable
from app.repositories.workspaces import WorkspaceRepository
from tests.integration.test_workspaces import create
from tests.security.test_request_limits import assert_security_headers


def endpoint(event):
    return f"/api/events/{event['id']}/guests"


def add(client, event, **values):
    body = {
        "revision": event["revision"],
        "request_id": str(uuid4()),
        "guest": {"name": "Asha Rao", "email": "asha@example.org", **values},
    }
    response = client.post(endpoint(event), json=body)
    assert response.status_code == 201, response.text
    assert_security_headers(response)
    return response.json(), body


def test_guest_lifecycle_stats_search_filters_and_confirmed_preview_boundary(client):
    event = create(client)
    first, original = add(
        client,
        event,
        rsvp="confirmed",
        plus_ones=2,
        group="Family",
        dietary="Vegan",
        accessibility="Step-free",
        notes="Private",
    )
    event = first["workspace"]
    assert event["details"]["guest_count"] == 30
    assert event["budget_summary"] == client.get(f"/api/events/{event['id']}/budget").json()
    second, _ = add(client, event, name="Emi", email="emi@example.org", rsvp="pending", plus_ones=1)
    event = second["workspace"]
    third, _ = add(client, event, name="Declined", rsvp="declined", plus_ones=3)
    event = third["workspace"]
    fourth, _ = add(client, event, name="Maybe", rsvp="maybe")
    event = fourth["workspace"]
    stats = fourth["roster"]["stats"]
    assert stats == dict(
        records=4,
        pending_responses=1,
        total_invited=10,
        confirmed=3,
        pending=2,
        declined=4,
        maybe=1,
        expected_attendees=3,
        possible_attendees=6,
    )
    found = client.get(
        endpoint(event), params={"q": "ASHA@EXAMPLE", "rsvp": "confirmed", "group": "Family"}
    ).json()
    assert len(found["guests"]) == 1 and found["stats"] == stats
    guest = found["guests"][0]
    assert guest["event_id"] == event["id"] and guest["dietary"] == "Vegan"
    assert client.get(endpoint(event) + f"/{guest['id']}").json() == guest
    assert client.get(endpoint(event), params={"q": "' OR 1=1--"}).json()["guests"] == []
    values = {**original["guest"], "name": "Asha Updated", "rsvp": "declined", "plus_ones": 0}
    result = client.put(
        endpoint(event) + f"/{guest['id']}", json={"revision": event["revision"], "guest": values}
    ).json()
    event = result["workspace"]
    assert result["roster"]["stats"]["expected_attendees"] == 0
    assert result["roster"]["guests"][0]["created_at"] == guest["created_at"]
    assert (
        client.request(
            "DELETE",
            endpoint(event) + f"/{guest['id']}",
            json={"revision": event["revision"], "confirm_id": str(uuid4())},
        ).status_code
        == 422
    )
    removed = client.request(
        "DELETE",
        endpoint(event) + f"/{guest['id']}",
        json={"revision": event["revision"], "confirm_id": guest["id"]},
    )
    assert removed.status_code == 200 and removed.json()["roster"]["stats"]["records"] == 3
    assert client.get(endpoint(event) + f"/{guest['id']}").status_code == 404
    assert client.get(f"/api/events/{event['id']}").json()["details"] == first["workspace"]["details"]


def test_roster_empty_does_not_migrate_and_guest_restart_and_parent_delete_cascade(client):
    event = create(client)
    repo = client.app.state.workspace_repository
    assert client.get(endpoint(event)).json()["stats"]["records"] == 0
    with closing(sqlite3.connect(repo.path)) as c, c:
        assert not c.execute("SELECT name FROM sqlite_master WHERE name='guests'").fetchone()
    result, _ = add(client, event, plus_ones=1)
    event = result["workspace"]
    with TestClient(main.app, cookies=client.cookies) as restarted:
        assert restarted.get(endpoint(event)).json() == result["roster"]
        assert restarted.get(f"/api/events/{event['id']}").json() == event
        assert (
            restarted.request(
                "DELETE",
                f"/api/events/{event['id']}",
                json={"revision": event["revision"], "confirm_id": event["id"]},
            ).status_code
            == 204
        )
    with closing(sqlite3.connect(repo.path)) as c, c:
        assert c.execute("SELECT COUNT(*) FROM guests").fetchone()[0] == 0
        assert c.execute("PRAGMA user_version").fetchone()[0] == 2


def test_guest_retries_stale_writes_and_atomic_rollback(client, monkeypatch):
    event = create(client)
    saved, body = add(client, event)
    assert client.post(endpoint(event), json=body).json() == saved
    assert client.post(endpoint(event), json={**body, "guest": {"name": "Changed retry"}}).status_code == 409
    assert client.post(endpoint(event), json={**body, "request_id": str(uuid4())}).status_code == 409
    event = saved["workspace"]

    def fail(*_):
        raise StorageUnavailable

    monkeypatch.setattr(WorkspaceRepository, "_save", fail)
    response = client.post(
        endpoint(event), json={**body, "revision": event["revision"], "request_id": str(uuid4())}
    )
    assert response.status_code == 503
    assert client.get(endpoint(event)).json() == saved["roster"]
    assert client.get(f"/api/events/{event['id']}").json() == event


def test_foreign_guests_and_other_owner_never_read_or_write(client):
    one, two = create(client), create(client)
    result, _ = add(client, one)
    guest = result["roster"]["guests"][0]
    url = endpoint(two) + f"/{guest['id']}"
    assert client.get(url).status_code == 404
    assert client.put(url, json={"revision": 1, "guest": {"name": "Intruder"}}).status_code == 404
    assert client.request("DELETE", url, json={"revision": 1, "confirm_id": guest["id"]}).status_code == 404
    with TestClient(main.app) as stranger:
        for method, path, body in [
            ("GET", endpoint(one), None),
            ("GET", endpoint(one) + f"/{guest['id']}", None),
            (
                "POST",
                endpoint(one),
                {"revision": 2, "request_id": str(uuid4()), "guest": {"name": "Intruder"}},
            ),
            ("PUT", endpoint(one) + f"/{guest['id']}", {"revision": 2, "guest": {"name": "Intruder"}}),
            ("DELETE", endpoint(one) + f"/{guest['id']}", {"revision": 2, "confirm_id": guest["id"]}),
        ]:
            assert stranger.request(method, path, json=body).status_code == 404
    assert client.get(endpoint(one)).json() == result["roster"]
    assert client.get(f"/api/events/{two['id']}").json() == two


@pytest.mark.parametrize(
    "patch",
    [
        {"name": " "},
        {"name": "x" * 101},
        {"email": "invalid"},
        {"email": "x@y"},
        {"plus_ones": -1},
        {"plus_ones": 21},
        {"plus_ones": True},
        {"plus_ones": 1.5},
        {"rsvp": "yes"},
        {"group": "Unknown"},
        {"notes": "x" * 501},
        {"event_id": str(uuid4())},
        {"owner": "forged"},
    ],
)
def test_invalid_guests_never_create_records(client, patch):
    event = create(client)
    response = client.post(
        endpoint(event), json={"revision": 1, "request_id": str(uuid4()), "guest": {"name": "Name", **patch}}
    )
    assert response.status_code == 422
    assert_security_headers(response)
    assert client.get(endpoint(event)).json()["stats"]["records"] == 0
    assert client.get(f"/api/events/{event['id']}").json() == event


def test_concurrent_guest_writes_preserve_one_revision(client):
    event = create(client)

    def insert(i):
        return client.post(
            endpoint(event), json={"revision": 1, "request_id": str(uuid4()), "guest": {"name": f"Guest {i}"}}
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(insert, range(2))) == [201, 409]
    roster = client.get(endpoint(event)).json()
    assert roster["revision"] == 2 and roster["stats"]["records"] == 1


@pytest.mark.parametrize("rsvp", ["pending", "confirmed", "declined", "maybe"])
def test_each_rsvp_counts_party_and_plus_ones(client, rsvp):
    result, _ = add(client, create(client), rsvp=rsvp, plus_ones=2)
    stats = result["roster"]["stats"]
    assert stats[rsvp] == stats["total_invited"] == 3
    assert stats["expected_attendees"] == (3 if rsvp == "confirmed" else 0)


def test_guest_capacity_is_bounded_and_corrupt_saved_data_fails_closed(client):
    from app.schemas.guests import Guest

    event = create(client)
    saved, body = add(client, event)
    repo = client.app.state.workspace_repository
    record = Guest.model_validate(saved["roster"]["guests"][0])
    with closing(sqlite3.connect(repo.path)) as c, c:
        owner = c.execute("SELECT owner FROM events WHERE id=?", (event["id"],)).fetchone()[0]
        for _ in range(499):
            guest = record.model_copy(update={"id": uuid4()})
            c.execute(
                "INSERT INTO guests VALUES(?,?,?,1,?)",
                (str(guest.id), event["id"], owner, guest.model_dump_json()),
            )
    response = client.post(endpoint(event), json={**body, "revision": 2, "request_id": str(uuid4())})
    assert response.status_code == 422
    assert client.get(f"/api/events/{event['id']}").json() == saved["workspace"]
    with closing(sqlite3.connect(repo.path)) as c, c:
        c.execute("UPDATE guests SET document='{}' WHERE id=?", (str(record.id),))
    assert client.get(endpoint(event)).status_code == 503


def test_guest_edits_invalidate_existing_preview_and_do_not_touch_budget(client):
    event = create(client)
    prefix = f"/api/events/{event['id']}"
    preview = client.post(
        prefix + "/scenarios", json={"revision": 1, "parameters": {"type": "guest_count", "guest_count": 25}}
    ).json()
    saved, _ = add(client, event)
    assert saved["workspace"]["budget_summary"] == event["budget_summary"]
    assert saved["workspace"]["tasks"] == event["tasks"]
    assert client.get(prefix + f"/scenarios/{preview['id']}").json()["stale"]
    assert (
        client.post(
            prefix + f"/scenarios/{preview['id']}/apply", json={"revision": 1, "approved": True}
        ).status_code
        == 409
    )


def test_guest_request_id_cannot_move_or_overwrite_another_event_record(client):
    first, second = create(client), create(client)
    saved, original = add(client, first)
    response = client.post(endpoint(second), json={**original, "revision": 1})
    assert response.status_code == 409
    assert client.get(endpoint(first)).json() == saved["roster"]
    assert client.get(endpoint(second)).json()["stats"]["records"] == 0
