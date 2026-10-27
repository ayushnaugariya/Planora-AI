"""Vendor editing retains owned child identities, progress and financial records."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import main
from tests.integration.test_workspaces import create


def test_vendor_edit_persists_and_stales_previews(client):
    event = create(client)
    url = f"/api/events/{event['id']}"
    vendor = event["vendors"][0]
    preview = client.post(
        url + "/scenarios", json={"revision": 1, "parameters": {"type": "guest_count", "guest_count": 42}}
    ).json()
    body = dict(revision=1, name="Garden studio", contact="hello@example.test", booking_status="booked")
    result = client.patch(url + f"/vendors/{vendor['id']}", json=body)
    assert result.status_code == 200, result.text
    saved = result.json()
    assert saved["vendors"][0] == {**vendor, **{k: v for k, v in body.items() if k != "revision"}}
    for key in ("tasks", "expenses", "details", "plan", "budget_summary"):
        assert saved[key] == event[key]
    assert client.get(url).json() == saved
    assert client.get(url + f"/scenarios/{preview['id']}").json()["stale"]
    assert client.patch(url + f"/vendors/{vendor['id']}", json=body).status_code == 409


@pytest.mark.parametrize(
    "override",
    [
        {"name": "x" * 81},
        {"contact": "x" * 201},
        {"booking_status": "confirmed_live"},
        {"revision": True},
        {"budget": 1},
        {"name": None},
    ],
)
def test_vendor_edit_validation(client, override):
    event = create(client)
    body = dict(revision=1, name="", contact="", booking_status="unbooked") | override
    assert (
        client.patch(f"/api/events/{event['id']}/vendors/{event['vendors'][0]['id']}", json=body).status_code
        == 422
    )


def test_vendor_ownership_and_foreign_child_rejection(client):
    event, other = create(client), create(client)
    body = dict(revision=1, name="Name", contact="", booking_status="shortlisted")
    url = f"/api/events/{event['id']}/vendors/"
    assert client.patch(url + str(uuid4()), json=body).status_code == 404
    assert client.patch(url + other["vendors"][0]["id"], json=body).status_code == 404
    with TestClient(main.app) as stranger:
        assert stranger.patch(url + event["vendors"][0]["id"], json=body).status_code == 404
