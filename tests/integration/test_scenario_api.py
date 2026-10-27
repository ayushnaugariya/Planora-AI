"""Saved previews, approval, concurrency, rollback and child ownership."""

import json
from datetime import date, timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app import main
from app.core.errors import RevisionConflict
from app.services.workspaces import next_revision
from tests.integration.test_workspaces import create, db_execute
from tests.unit.test_scenarios import known_event


def seed_known(client):
    event = known_event(client)
    owner = db_execute(client, "SELECT owner FROM events WHERE id=?", (str(event.id),))[0][0]
    next_revision(event, "Test fixture: explicit confirmed zero-cost records")
    client.app.state.workspace_repository.save(owner, event, 1)
    return event.model_dump(mode="json")


def preview(client, event, **params):
    response = client.post(
        f"/api/events/{event['id']}/scenarios", json={"revision": event["revision"], "parameters": params}
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_saved_scenario_isolation_compare_and_approved_application(client):
    event = seed_known(client)
    url = f"/api/events/{event['id']}"
    scenario = preview(
        client, event, type="additional_function", name="Welcome gathering", estimated_cost="100"
    )
    assert scenario["feasibility"] == "feasible"
    assert client.get(url).json() == event
    path = url + f"/scenarios/{scenario['id']}"
    assert client.get(path).json() == scenario
    assert client.get(path + "/compare").json() == scenario
    assert client.get(url + "/scenarios").json() == [scenario]
    assert (
        client.post(path + "/apply", json={"revision": event["revision"], "approved": False}).status_code
        == 422
    )
    assert client.get(url).json() == event
    response = client.post(path + "/apply", json={"revision": event["revision"], "approved": True})
    assert response.status_code == 200, response.text
    saved = response.json()
    assert saved["revision"] == event["revision"] + 1
    assert len(saved["expenses"]) == len(event["expenses"]) + 1
    assert saved["budget_summary"]["projected_cost"] == "100.00"
    assert "Approved scenario" in saved["history"][-1]["summary"]
    assert client.get(url).json() == saved
    assert client.get(path).json()["status"] == "applied"
    assert (
        client.post(path + "/apply", json={"revision": event["revision"], "approved": True}).json() == saved
    )
    assert client.post(path + "/discard").status_code == 409


def test_discarded_and_stale_previews_do_not_change_event(client):
    event = seed_known(client)
    url = f"/api/events/{event['id']}"
    scenario = preview(client, event, type="guest_count", guest_count=40)
    path = url + f"/scenarios/{scenario['id']}"
    assert client.post(path + "/discard").json()["status"] == "discarded"
    assert client.post(path + "/discard").status_code == 200
    assert client.post(path + "/apply", json={"revision": 2, "approved": True}).status_code == 409
    assert client.get(url).json() == event
    another = preview(client, event, type="guest_count", guest_count=45)
    renamed = client.patch(url, json={"revision": 2, "title": "Changed since preview"}).json()
    stale_path = url + f"/scenarios/{another['id']}"
    assert client.get(stale_path).json()["stale"]
    assert client.post(stale_path + "/apply", json={"revision": 2, "approved": True}).status_code == 409
    assert client.get(url).json() == renamed


@pytest.mark.parametrize(
    "parameters,status",
    [
        ({"type": "budget_reduction", "percent": "10"}, "infeasible"),
        ({"type": "additional_function", "name": "Unpriced"}, "indeterminate"),
    ],
)
def test_non_feasible_scenarios_cannot_be_approved(client, parameters, status):
    event = seed_known(client)
    scenario = preview(client, event, **parameters)
    assert scenario["feasibility"] == status
    url = f"/api/events/{event['id']}"
    assert (
        client.post(
            url + f"/scenarios/{scenario['id']}/apply", json={"revision": 2, "approved": True}
        ).status_code
        == 422
    )
    assert client.get(url).json() == event


def test_failed_application_rolls_back_event_and_scenario_together(client):
    event = seed_known(client)
    scenario = preview(client, event, type="additional_function", name="Reception", estimated_cost="50")
    url = f"/api/events/{event['id']}"
    path = url + f"/scenarios/{scenario['id']}"
    db_execute(
        client,
        "CREATE TRIGGER reject_apply BEFORE UPDATE ON scenarios BEGIN SELECT RAISE(ABORT,'blocked'); END",
    )
    assert client.post(path + "/apply", json={"revision": 2, "approved": True}).status_code == 503
    assert client.get(url).json() == event
    assert client.get(path).json()["status"] == "pending"


def test_scenario_ownership_and_event_delete_cascade(client):
    event = seed_known(client)
    other = create(client)
    scenario = preview(client, event, type="guest_count", guest_count=50)
    wrong = f"/api/events/{other['id']}/scenarios/{scenario['id']}"
    assert client.get(wrong).status_code == 404
    assert client.post(wrong + "/apply", json={"revision": 1, "approved": True}).status_code == 404
    with TestClient(main.app) as stranger:
        assert stranger.get(f"/api/events/{event['id']}/scenarios").status_code == 404
        assert stranger.get(f"/api/events/{event['id']}/scenarios/{scenario['id']}").status_code == 404
    assert (
        client.request(
            "DELETE", f"/api/events/{event['id']}", json={"revision": 2, "confirm_id": event["id"]}
        ).status_code
        == 204
    )
    assert db_execute(client, "SELECT id FROM scenarios") == []


def test_recheck_before_transaction_rejects_racing_write(client, monkeypatch):
    event = seed_known(client)
    scenario = preview(client, event, type="guest_count", guest_count=45)
    repo = client.app.state.workspace_repository
    original = repo.apply_scenario

    def race(owner, event_id, scenario_id, expected_revision, proposed):
        changed = repo.get(owner, event_id)
        next_revision(changed, "Concurrent edit")
        repo.save(owner, changed, expected_revision)
        return original(owner, event_id, scenario_id, expected_revision, proposed)

    monkeypatch.setattr(repo, "apply_scenario", race)
    response = client.post(
        f"/api/events/{event['id']}/scenarios/{scenario['id']}/apply", json={"revision": 2, "approved": True}
    )
    assert response.status_code == 409
    assert client.get(f"/api/events/{event['id']}").json()["details"]["guest_count"] == 30


def test_expired_date_or_changed_preview_requires_regeneration(client):
    event = seed_known(client)
    scenario = preview(client, event, type="guest_count", guest_count=45)
    url = f"/api/events/{event['id']}/scenarios/{scenario['id']}"
    raw = db_execute(client, "SELECT document FROM scenarios")[0][0]
    damaged = json.loads(raw)
    damaged["evaluated_on"] = (date.today() - timedelta(days=1)).isoformat()
    db_execute(client, "UPDATE scenarios SET document=?", (json.dumps(damaged),))
    assert client.get(url).json()["stale"]
    assert client.post(url + "/apply", json={"revision": 2, "approved": True}).status_code == 409
    damaged = json.loads(raw)
    damaged["proposed_values"]["guest_count"] = 999
    db_execute(client, "UPDATE scenarios SET document=?", (json.dumps(damaged),))
    assert client.post(url + "/apply", json={"revision": 2, "approved": True}).status_code == 409


def test_scenario_creation_rechecks_revision_and_bad_records_are_safe(client, monkeypatch):
    event = seed_known(client)
    repo = client.app.state.workspace_repository
    with monkeypatch.context() as scoped:
        scoped.setattr(repo, "create_scenario", Mock(side_effect=RevisionConflict))
        response = client.post(
            f"/api/events/{event['id']}/scenarios",
            json={"revision": 2, "parameters": {"type": "guest_count", "guest_count": 50}},
        )
        assert response.status_code == 409
    scenario = preview(client, event, type="guest_count", guest_count=50)
    db_execute(client, "UPDATE scenarios SET document='{}'")
    assert client.get(f"/api/events/{event['id']}/scenarios/{scenario['id']}").status_code == 503
