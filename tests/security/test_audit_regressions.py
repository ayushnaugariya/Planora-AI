"""Reproduced audit regressions: safe unexpected errors and calendar boundaries."""

import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.api import planning
from app.core.errors import StorageUnavailable
from tests.conftest import payload
from tests.security.test_request_limits import assert_security_headers


@pytest.mark.parametrize(
    "error,status", [(RuntimeError("private sentinel"), 500), (StorageUnavailable(), 503)]
)
def test_server_failures_keep_headers_without_exposing_exception(client, monkeypatch, error, status):
    def fail(*_):
        raise error

    monkeypatch.setattr(planning, "build_plan", fail)
    with TestClient(main.app, raise_server_exceptions=False) as failing:
        response = failing.post("/api/plan", json=payload())
    assert response.status_code == status
    assert "private sentinel" not in response.text
    assert_security_headers(response)


@pytest.mark.parametrize("separator", ["\r", "\n", "\r\n"])
@pytest.mark.parametrize("saved", [False, True], ids=["stateless", "saved"])
def test_calendar_user_text_cannot_create_content_lines(client, separator, saved):
    details = payload(title=f"Party{separator}ATTENDEE:intruder@example.invalid")
    if saved:
        event = client.post("/api/events", json={"details": details}).json()
        response = client.get(f"/api/events/{event['id']}/ics")
    else:
        response = client.post("/api/ics", json=details)
    assert response.status_code == 200
    body = response.text
    assert "\r" not in body.replace("\r\n", ""), "Lone CR is not a valid calendar text escape"
    assert not any(line.startswith("ATTENDEE:") for line in body.splitlines())
    assert "\\nATTENDEE:" in body
    assert_security_headers(response)


def test_calendar_ids_are_unique_per_event_and_stable_after_reexport(client):
    first = client.post("/api/events", json={"details": payload()}).json()
    second = client.post("/api/events", json={"details": payload()}).json()

    def identifiers(event):
        return [
            line
            for line in client.get(f"/api/events/{event['id']}/ics").text.splitlines()
            if line.startswith("UID:")
        ]

    initial = identifiers(first)
    assert initial == identifiers(first), "Reexporting one workspace must retain milestone identity"
    assert set(initial).isdisjoint(identifiers(second)), "Separate events must never share calendar UIDs"


@pytest.mark.parametrize("saved", [False, True], ids=["stateless", "saved"])
@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"])
def test_invalid_unicode_input_is_validation_error_not_server_error(client, saved, surrogate):
    details = payload(title="Event " + surrogate)
    with TestClient(main.app, raise_server_exceptions=False) as failing:
        response = failing.post(
            "/api/events" if saved else "/api/plan",
            content=json.dumps({"details": details} if saved else details).encode("ascii"),
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422
        assert_security_headers(response)
        assert failing.get("/api/events").json() == [], (
            "Invalid text must not leave an unreadable saved event"
        )
