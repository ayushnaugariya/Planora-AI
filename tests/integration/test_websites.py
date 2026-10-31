"""Draft/snapshot privacy, explicit publication and same-roster anonymous submissions."""

import json
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import main
from app.ai import gemini, website_copy
from app.core import security
from app.core.errors import StorageUnavailable
from app.repositories.workspaces import WorkspaceRepository
from tests.integration.test_workspaces import create
from tests.security.test_request_limits import assert_security_headers


def endpoint(event):
    return f"/api/events/{event['id']}/website"


def draft(client, event, config=None):
    state = client.get(endpoint(event)).json()
    response = client.put(
        endpoint(event),
        json={
            "event_revision": state["event_revision"],
            "revision": state["revision"],
            "request_id": str(uuid4()),
            "config": config or state["draft"],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def preview(client, event, state, config=None):
    response = client.post(
        endpoint(event) + "/preview",
        json={
            "event_revision": state["event_revision"],
            "revision": state["revision"],
            "request_id": str(uuid4()),
            "config": config or state["draft"],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def publish(client, event, state=None):
    state = state or draft(client, event)
    shown = preview(client, event, state)
    body = {
        "event_revision": state["event_revision"],
        "revision": state["revision"],
        "request_id": str(uuid4()),
        "approved": True,
        "preview_hash": shown["preview_hash"],
    }
    response = client.post(endpoint(event) + "/publish", json=body)
    assert response.status_code == 200, response.text
    return response.json(), body


def public_url(state):
    return "/api/public/websites/" + state["public_path"].split("/")[-1]


def response_body(state, **over):
    return {
        "request_id": str(uuid4()),
        "edition": state["published"]["edition"],
        "name": "Asha Rao",
        "email": "asha@example.org",
        "rsvp": "confirmed",
        "attendees": 1,
        **over,
    }


def open_rsvp(client, event):
    state = client.get(endpoint(event)).json()
    state = draft(client, event, {**state["draft"], "rsvp_enabled": True, "max_attendees": 4})
    return publish(client, event, state)[0]


def test_defaults_reuse_event_private_context_not_copied_and_no_ddl(client):
    event = create(
        client, notes="PRIVATE_NOTES", theme="PRIVATE_THEME", accessibility_requirements="PRIVATE_ACCESS"
    )
    before = event
    response = client.get(endpoint(event))
    assert response.status_code == 200
    assert_security_headers(response)
    state = response.json()
    assert state["draft"]["title"] == event["plan"]["title"]
    assert state["draft"]["event_date"] == event["details"]["event_date"]
    assert state["draft"]["theme"] == "celebration"
    assert not state["draft"]["show_venue"] and not state["draft"]["rsvp_enabled"]
    assert not any(secret in response.text for secret in ["PRIVATE_NOTES", "PRIVATE_THEME", "PRIVATE_ACCESS"])
    assert state["public_path"] is None and state["revision"] == 0
    assert client.get(f"/api/events/{event['id']}").json() == before
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as c:
        assert not c.execute("SELECT 1 FROM sqlite_master WHERE name='event_websites'").fetchone()


@pytest.mark.parametrize("theme", ["ethereal", "modern_minimal", "celebration", "editorial_luxe"])
def test_themes_create_customize_preview_publish_private_draft_and_unpublish(client, theme):
    event = create(client)
    initial = client.get(endpoint(event)).json()
    config = {
        **initial["draft"],
        "theme": theme,
        "accent": "#136b59",
        "title": "Our public occasion",
        "hosts": "PRIVATE_HOSTS",
        "venue_name": "PRIVATE_VENUE",
        "venue_address": "PRIVATE_ADDRESS",
        "dress_code": "PRIVATE_DRESS",
        "gallery": ["botanical"],
        "show_gallery": False,
    }
    state = draft(client, event, config)
    slug = state["public_path"].split("/")[-1]
    assert re.fullmatch(r"[A-Za-z0-9_-]{32}", slug) and event["id"] not in state["public_path"]
    assert client.get(state["public_path"]).status_code == 404
    assert client.get(public_url(state)).status_code == 404
    shown = preview(client, event, state)
    assert shown["website"]["theme"] == theme
    assert shown["website"]["hosts"] is None and shown["website"]["venue"] is None
    state, body = publish(client, event, state)
    assert client.get(state["public_path"]).status_code == 200
    public = client.get(public_url(state))
    assert public.status_code == 200
    assert_security_headers(public)
    assert "set-cookie" not in public.headers
    assert public.json()["accent"] == "#136b59"
    for value in [
        event["id"],
        "PRIVATE_HOSTS",
        "PRIVATE_VENUE",
        "PRIVATE_ADDRESS",
        "PRIVATE_DRESS",
        "budget",
        "vendors",
        "expenses",
        "notes",
        "owner",
        "guest_id",
        "saved_event_revision",
    ]:
        assert value not in public.text
    assert client.post(endpoint(event) + "/publish", json=body).json() == state
    changed = draft(client, event, {**config, "title": "Unapproved change"})
    assert client.get(public_url(state)).json()["title"] == "Our public occasion"
    assert changed["public_path"] == state["public_path"]
    changed, _ = publish(client, event, changed)
    assert client.get(public_url(state)).json()["title"] == "Unapproved change"
    request = {
        "event_revision": changed["event_revision"],
        "revision": changed["revision"],
        "request_id": str(uuid4()),
        "approved": True,
    }
    unpublished = client.post(endpoint(event) + "/unpublish", json=request)
    assert unpublished.status_code == 200
    assert client.get(public_url(state)).status_code == client.get(state["public_path"]).status_code == 404
    reopened, _ = publish(client, event, unpublished.json())
    assert reopened["public_path"] == state["public_path"]
    assert client.get(f"/api/events/{event['id']}").json() == event


def test_visibility_projection_is_allowlisted_and_exact(client):
    event = create(client)
    initial = client.get(endpoint(event)).json()
    config = {
        **initial["draft"],
        "hosts": "Mira & Arun",
        "show_hosts": True,
        "venue_name": "Hall A",
        "venue_address": "123 Avenue",
        "city": "Pune",
        "show_venue": True,
        "show_schedule": True,
        "show_dress_code": True,
        "dress_code": "Garden formal",
        "show_gallery": True,
        "gallery": ["botanical", "venue"],
    }
    state, _ = publish(client, event, draft(client, event, config))
    public = client.get(public_url(state)).json()
    assert public["venue"] == {"name": "Hall A", "address": "123 Avenue", "city": "Pune"}
    assert public["hosts"] == "Mira & Arun" and public["dress_code"] == "Garden formal"
    assert public["gallery"] == ["botanical", "venue"] and public["schedule"]
    assert set(public) == {
        "edition",
        "theme",
        "accent",
        "event_type",
        "title",
        "subtitle",
        "event_date",
        "start_at",
        "timezone",
        "welcome",
        "invitation",
        "description",
        "hosts",
        "venue",
        "dress_code",
        "schedule",
        "cover",
        "gallery",
        "rsvp",
    }


@pytest.mark.parametrize("approved", [False, 1, "true", None])
def test_publication_requires_literal_approval(client, approved):
    event = create(client)
    state = draft(client, event)
    shown = preview(client, event, state)
    response = client.post(
        endpoint(event) + "/publish",
        json={
            "event_revision": state["event_revision"],
            "revision": state["revision"],
            "request_id": str(uuid4()),
            "approved": approved,
            "preview_hash": shown["preview_hash"],
        },
    )
    assert response.status_code == 422
    assert client.get(public_url(state)).status_code == 404


def test_preview_hash_stale_revisions_idempotency_and_concurrency(client):
    event = create(client)
    state = draft(client, event)
    wrong = preview(client, event, state, {**state["draft"], "title": "Unsaved"})
    body = {
        "event_revision": state["event_revision"],
        "revision": state["revision"],
        "request_id": str(uuid4()),
        "approved": True,
        "preview_hash": wrong["preview_hash"],
    }
    assert client.post(endpoint(event) + "/publish", json=body).status_code == 409
    shown = preview(client, event, state)
    body["preview_hash"] = shown["preview_hash"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda _: client.post(
                    endpoint(event) + "/publish", json={**body, "request_id": str(uuid4())}
                ),
                range(2),
            )
        )
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert (
        client.put(
            endpoint(event),
            json={"event_revision": 1, "revision": 1, "request_id": str(uuid4()), "config": state["draft"]},
        ).status_code
        == 409
    )
    assert (
        client.patch(f"/api/events/{event['id']}", json={"revision": 1, "title": "Changed"}).status_code
        == 200
    )
    assert (
        client.post(
            endpoint(event) + "/preview",
            json={"event_revision": 1, "revision": 2, "request_id": str(uuid4()), "config": state["draft"]},
        ).status_code
        == 409
    )


def test_ownership_no_public_cookie_and_stable_restart_and_cascade(client):
    event = create(client)
    state, _ = publish(client, event)
    with TestClient(main.app) as visitor:
        page = visitor.get(state["public_path"])
        assert page.status_code == 200
        assert page.headers["cache-control"] == "no-store"
        assert "set-cookie" not in page.headers
        assert visitor.get(public_url(state)).json() == state["published"]
        assert visitor.get(endpoint(event)).status_code == 404
        assert (
            visitor.post(
                endpoint(event) + "/publish",
                json={
                    "revision": state["revision"],
                    "event_revision": 1,
                    "request_id": str(uuid4()),
                    "approved": True,
                    "preview_hash": "0" * 64,
                },
            ).status_code
            == 404
        )
    with TestClient(main.app, cookies=client.cookies) as restarted:
        assert restarted.get(endpoint(event)).json() == state
        assert restarted.get(public_url(state)).json() == state["published"]
        assert (
            restarted.request(
                "DELETE", f"/api/events/{event['id']}", json={"revision": 1, "confirm_id": event["id"]}
            ).status_code
            == 204
        )
        assert restarted.get(public_url(state)).status_code == 404
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as c:
        assert c.execute("SELECT COUNT(*) FROM event_websites").fetchone()[0] == 0
        assert c.execute("PRAGMA user_version").fetchone()[0] == 2


@pytest.mark.parametrize("slug", ["guess", str(uuid4()), "a" * 33, "invalid-slug!", "'OR1=1--"])
def test_invalid_public_identifiers(client, slug):
    for path in [f"/e/{slug}", f"/api/public/websites/{slug}"]:
        response = client.get(path)
        assert response.status_code == 404
        assert_security_headers(response)


def test_rsvp_joins_existing_roster_and_never_changes_budget_or_private_entries(client):
    event = create(client)
    state = open_rsvp(client, event)
    with TestClient(main.app) as visitor:
        body = response_body(state, attendees=3, dietary="Vegan", message="Looking forward")
        response = visitor.post(public_url(state) + "/rsvp", json=body)
        assert response.status_code == 202, response.text
        assert_security_headers(response)
        assert list(response.json()) == ["message"] and "set-cookie" not in response.headers
        assert event["id"] not in response.text and "Asha" not in response.text
        assert visitor.post(public_url(state) + "/rsvp", json=body).json() == response.json()
        assert (
            visitor.post(public_url(state) + "/rsvp", json={**body, "message": "Different retry"}).status_code
            == 409
        )
        # Email knowledge cannot claim or overwrite the first party.
        assert (
            visitor.post(
                public_url(state) + "/rsvp", json=response_body(state, name="Impersonation", rsvp="declined")
            ).status_code
            == 202
        )
        assert visitor.get(f"/api/events/{event['id']}/guests").status_code == 404
    roster = client.get(f"/api/events/{event['id']}/guests").json()
    assert len(roster["guests"]) == 1
    guest = roster["guests"][0]
    assert guest["rsvp"] == "confirmed" and guest["plus_ones"] == 2
    assert guest["dietary"] == "Vegan" and "unverified" in guest["notes"]
    assert roster["stats"]["confirmed"] == 3
    saved = client.get(f"/api/events/{event['id']}").json()
    assert saved["revision"] == event["revision"] + 1
    for field in ["details", "plan", "budget_summary", "expenses", "vendors", "tasks"]:
        assert saved[field] == event[field]


@pytest.mark.parametrize(
    "patch",
    [
        {"attendees": 0},
        {"attendees": 22},
        {"attendees": True},
        {"attendees": 5},
        {"rsvp": "accepted"},
        {"name": ""},
        {"name": "a" * 101},
        {"email": "invalid"},
        {"email": ""},
        {"message": "a" * 401},
        {"owner": "injected"},
        {"event_id": str(uuid4())},
        {"guest_id": str(uuid4())},
    ],
)
def test_rsvp_validation_and_limits(client, patch):
    event = create(client)
    state = open_rsvp(client, event)
    response = client.post(public_url(state) + "/rsvp", json=response_body(state, **patch))
    assert response.status_code == 422, response.text
    assert client.get(f"/api/events/{event['id']}/guests").json()["guests"] == []


def test_rsvp_disabled_unpublished_stale_and_cross_event(client):
    one, two = create(client), create(client)
    state, _ = publish(client, one)
    assert client.post(public_url(state) + "/rsvp", json=response_body(state)).status_code == 403
    state = open_rsvp(client, one)
    other = open_rsvp(client, two)
    body = response_body(state)
    assert client.post(public_url(other) + "/rsvp", json=body).status_code == 409
    assert (
        client.post(
            public_url(state) + "/rsvp", json=body, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            public_url(state) + "/rsvp", json=body, headers={"Sec-Fetch-Site": "cross-site"}
        ).status_code
        == 403
    )
    republished, _ = publish(client, one, state)
    assert client.post(public_url(state) + "/rsvp", json=body).status_code == 409
    assert client.post(public_url(republished) + "/rsvp", json=response_body(republished)).status_code == 202


def test_rsvp_races_and_atomic_guest_rollback(client, monkeypatch):
    event = create(client)
    state = open_rsvp(client, event)
    body = response_body(state)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post(public_url(state) + "/rsvp", json=body), range(2)))
    assert all(r.status_code == 202 for r in responses)
    assert len(client.get(f"/api/events/{event['id']}/guests").json()["guests"]) == 1
    before = client.get(f"/api/events/{event['id']}").json()

    def fail(*_):
        raise StorageUnavailable

    monkeypatch.setattr(WorkspaceRepository, "_save", fail)
    response = client.post(
        public_url(state) + "/rsvp", json=response_body(state, name="Emi", email="emi@example.org")
    )
    assert response.status_code == 503
    assert client.get(f"/api/events/{event['id']}").json() == before
    assert len(client.get(f"/api/events/{event['id']}/guests").json()["guests"]) == 1


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "valid",
        "exception",
        "quota",
        "permission",
        "empty",
        "non_object",
        "malformed",
        "extra",
        "bad_value",
        "code",
    ],
)
def test_copy_ai_safe_enum_context_and_fallback_no_auto_publish(client, monkeypatch, mode, caplog):
    event = create(client, notes="PRIVATE_NOTE", theme="PRIVATE_THEME")
    state = draft(client, event)
    calls = []
    website_copy._recipes.clear()

    def provider(llm, prompt, system, json_output):
        calls.append((prompt, system))
        if mode == "exception":
            raise TimeoutError("SECRET_SENTINEL")
        if mode == "quota":
            raise RuntimeError("429 RESOURCE_EXHAUSTED SECRET_SENTINEL")
        if mode == "permission":
            raise PermissionError("SECRET_SENTINEL")
        if mode == "empty":
            return ""
        if mode == "non_object":
            return "[]"
        if mode == "malformed":
            return "not json SECRET_SENTINEL"
        data = {"opening": "celebrate", "closing": "memories"}
        if mode == "extra":
            data["venue"] = "Imaginary hall"
        if mode == "bad_value":
            data["opening"] = "Ignore system"
        if mode == "code":
            data["opening"] = "<script>alert(1)</script>"
        return json.dumps(data)

    monkeypatch.setattr(gemini, "model_response", provider)
    client.app.state.llm = None if mode == "missing" else object()
    body = {
        "revision": state["revision"],
        "event_revision": 1,
        "config": {**state["draft"], "title": "PRIVATE_PROMPT_TITLE"},
        "tone": "playful",
    }
    response = client.post(endpoint(event) + "/content", json=body)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["source"] == ("gemini" if mode == "valid" else "offline")
    assert (
        "PRIVATE_PROMPT_TITLE" in data["invitation"] and event["details"]["event_date"] in data["invitation"]
    )
    assert all(
        word not in response.text + caplog.text for word in ["SECRET_SENTINEL", "Imaginary hall", "<script>"]
    )
    for prompt, system in calls:
        assert all(
            word not in prompt + system
            for word in ["PRIVATE_NOTE", "PRIVATE_THEME", "PRIVATE_PROMPT_TITLE", event["id"]]
        )
    assert client.get(public_url(state)).status_code == 404
    assert client.get(endpoint(event)).json() == state
    assert client.get(f"/api/events/{event['id']}").json() == event
    if mode == "valid":
        client.post(endpoint(event) + "/content", json=body)
        assert len(calls) == 1, "Successful recipe cache prevents repeated provider calls"


@pytest.mark.parametrize(
    "patch",
    [
        {"theme": "evil"},
        {"accent": "red;url(https://evil)"},
        {"cover": "https://evil/image.svg"},
        {"gallery": ["data:script"]},
        {"html": "<script>"},
        {"timezone": "invalid"},
        {"show_hosts": "true"},
        {"start_at": "2026-10-29T10:00:00"},
        {"title": "\ud800"},
    ],
)
def test_draft_validated_no_executable_template_or_remote_asset(client, patch):
    event = create(client)
    state = client.get(endpoint(event)).json()
    body = {
        "event_revision": 1,
        "revision": 0,
        "request_id": str(uuid4()),
        "config": {**state["draft"], **patch},
    }
    response = client.put(
        endpoint(event), content=json.dumps(body), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422, response.text


def test_public_api_body_limit_and_rate_headers(client, monkeypatch):
    event = create(client)
    state = open_rsvp(client, event)
    response = client.post(public_url(state) + "/rsvp", content="a" * 20001)
    assert response.status_code == 413
    assert_security_headers(response)
    monkeypatch.setattr(security, "rate_limited", lambda ip: 12)
    response = client.post(public_url(state) + "/rsvp", json=response_body(state))
    assert response.status_code == 429 and response.headers["retry-after"] == "12"
    assert_security_headers(response)


def test_corrupt_website_fails_closed(client):
    event = create(client)
    state, _ = publish(client, event)
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as c, c:
        c.execute("UPDATE event_websites SET format_version=1,document=?", ('{"format_version":99}',))
    for path in [endpoint(event), public_url(state), state["public_path"]]:
        assert client.get(path).status_code == 503


@pytest.mark.parametrize(
    "method,suffix",
    [("PUT", ""), ("POST", "/preview"), ("POST", "/content"), ("POST", "/publish"), ("POST", "/unpublish")],
)
def test_every_management_operation_requires_original_owner(client, method, suffix):
    event = create(client)
    state = draft(client, event)
    common = {"event_revision": 1, "revision": state["revision"], "request_id": str(uuid4())}
    body = {**common, "config": state["draft"]}
    if suffix == "/content":
        body = {"event_revision": 1, "revision": state["revision"], "config": state["draft"]}
    if suffix in ("/publish", "/unpublish"):
        body = {**common, "approved": True}
        if suffix == "/publish":
            body["preview_hash"] = preview(client, event, state)["preview_hash"]
    with TestClient(main.app) as stranger:
        response = stranger.request(method, endpoint(event) + suffix, json=body)
        assert response.status_code == 404
        assert_security_headers(response)


def test_unpublish_survives_public_roster_revision_and_old_publish_cannot_replay(client):
    event = create(client)
    state, old_publish = publish(
        client,
        event,
        draft(client, event, {**client.get(endpoint(event)).json()["draft"], "rsvp_enabled": True}),
    )
    assert client.post(public_url(state) + "/rsvp", json=response_body(state)).status_code == 202
    assert client.get(f"/api/events/{event['id']}").json()["revision"] == 2
    # Revocation depends on ownership/website revision, not an unrelated newer RSVP.
    revoked = client.post(
        endpoint(event) + "/unpublish",
        json={
            "event_revision": 1,
            "revision": state["revision"],
            "request_id": str(uuid4()),
            "approved": True,
        },
    )
    assert revoked.status_code == 200, revoked.text
    assert client.get(public_url(state)).status_code == 404
    assert client.post(endpoint(event) + "/publish", json=old_publish).status_code == 409
    assert client.post(public_url(state) + "/rsvp", json=response_body(state)).status_code == 404


def test_retries_cannot_resurrect_deleted_party_and_receipts_cascade(client):
    event = create(client)
    state = open_rsvp(client, event)
    body = response_body(state)
    assert client.post(public_url(state) + "/rsvp", json=body).status_code == 202
    roster = client.get(f"/api/events/{event['id']}/guests").json()
    key = roster["guests"][0]["id"]
    assert (
        client.request(
            "DELETE",
            f"/api/events/{event['id']}/guests/{key}",
            json={"revision": roster["revision"], "confirm_id": key},
        ).status_code
        == 200
    )
    assert client.post(public_url(state) + "/rsvp", json=body).status_code == 202
    assert client.get(f"/api/events/{event['id']}/guests").json()["guests"] == []
    current = client.get(f"/api/events/{event['id']}").json()
    assert (
        client.request(
            "DELETE",
            f"/api/events/{event['id']}",
            json={"revision": current["revision"], "confirm_id": event["id"]},
        ).status_code
        == 204
    )
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as c:
        assert c.execute("SELECT COUNT(*) FROM website_responses").fetchone()[0] == 0


def test_manual_guest_email_cannot_be_claimed_publicly(client):
    event = create(client)
    response = client.post(
        f"/api/events/{event['id']}/guests",
        json={
            "revision": 1,
            "request_id": str(uuid4()),
            "guest": {
                "name": "Private Guest",
                "email": "asha@example.org",
                "rsvp": "declined",
                "notes": "PRIVATE_GUEST_NOTE",
            },
        },
    )
    assert response.status_code == 201
    event = response.json()["workspace"]
    before = response.json()["roster"]
    state = open_rsvp(client, event)
    assert (
        client.post(public_url(state) + "/rsvp", json=response_body(state, rsvp="confirmed")).status_code
        == 202
    )
    assert client.get(f"/api/events/{event['id']}/guests").json() == before
    assert "PRIVATE_GUEST_NOTE" not in client.get(public_url(state)).text


def test_public_optional_email_name_dedup_and_pending_states(client):
    event = create(client)
    config = client.get(endpoint(event)).json()["draft"]
    state, _ = publish(
        client, event, draft(client, event, {**config, "rsvp_enabled": True, "rsvp_email_required": False})
    )
    first = client.post(public_url(state) + "/rsvp", json=response_body(state, email="", rsvp="maybe"))
    assert first.status_code == 202
    assert (
        client.post(
            public_url(state) + "/rsvp", json=response_body(state, email="", name="ASHA RAO", rsvp="declined")
        ).status_code
        == 202
    )
    guests = client.get(f"/api/events/{event['id']}/guests").json()["guests"]
    assert len(guests) == 1 and guests[0]["rsvp"] == "maybe"


def test_response_storage_capacity_rejects_without_disabling_protection(client):
    event = create(client)
    state = open_rsvp(client, event)
    assert client.post(public_url(state) + "/rsvp", json=response_body(state)).status_code == 202
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as c, c:
        row = c.execute("SELECT * FROM website_responses").fetchone()
        c.executemany(
            "INSERT INTO website_responses VALUES(?,?,?,?,?)",
            [(row[0], f"key-{i}", f"identity-{i}", row[3], row[4]) for i in range(999)],
        )
    before = client.get(f"/api/events/{event['id']}").json()
    response = client.post(
        public_url(state) + "/rsvp", json=response_body(state, name="New", email="new@example.org")
    )
    assert response.status_code == 429
    assert client.get(f"/api/events/{event['id']}").json() == before


def test_roster_capacity_is_the_existing_500_limit(client):
    event = create(client)
    state = open_rsvp(client, event)
    assert client.post(public_url(state) + "/rsvp", json=response_body(state)).status_code == 202
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as c, c:
        row = c.execute("SELECT * FROM guests").fetchone()
        document = json.loads(row[4])
        records = []
        for i in range(499):
            key = str(uuid4())
            records.append(
                (
                    key,
                    row[1],
                    row[2],
                    1,
                    json.dumps({**document, "id": key, "name": f"Guest {i}", "email": f"{i}@example.org"}),
                )
            )
        c.executemany("INSERT INTO guests VALUES(?,?,?,?,?)", records)
    response = client.post(
        public_url(state) + "/rsvp", json=response_body(state, name="Over capacity", email="over@example.org")
    )
    assert response.status_code == 429
    assert client.get(f"/api/events/{event['id']}/guests").json()["stats"]["records"] == 500


def test_existing_event_start_and_timezone_are_reused_without_operational_notes(client):
    event = create(client)
    task = next(
        t for t in event["tasks"] if event["plan"]["timeline"][t["milestone_index"]]["category"] == "event"
    )
    response = client.post(
        f"/api/events/{event['id']}/command-center/operations",
        json={
            "revision": 1,
            "request_id": str(uuid4()),
            "approved": True,
            "operation": {
                "kind": "task",
                "id": task["id"],
                "value": {
                    "planned_start": event["details"]["event_date"] + "T12:00:00Z",
                    "notes": "PRIVATE_OPERATION_NOTE",
                },
            },
        },
    )
    assert response.status_code == 200, response.text
    response = client.get(endpoint(event))
    data = response.json()
    assert data["draft"]["start_at"] == event["details"]["event_date"] + "T12:00:00Z"
    assert (
        data["suggested_schedule"][0]["title"] == event["plan"]["timeline"][task["milestone_index"]]["title"]
    )
    assert "PRIVATE_OPERATION_NOTE" not in response.text and task["id"] not in response.text


def test_published_page_is_rate_limited_with_no_store_on_early_errors(client, monkeypatch):
    event = create(client)
    state, _ = publish(client, event)
    monkeypatch.setattr(security, "rate_limited", lambda ip: 7)
    response = client.get(state["public_path"])
    assert response.status_code == 429 and response.headers["retry-after"] == "7"
    assert_security_headers(response)


@pytest.mark.parametrize("mode", ["owner", "identity", "revision", "published_extra"])
def test_corrupt_saved_public_snapshot_fails_closed(client, mode):
    event = create(client)
    state, _ = publish(client, event)
    with closing(sqlite3.connect(client.app.state.workspace_repository.path)) as c, c:
        doc = json.loads(c.execute("SELECT document FROM event_websites").fetchone()[0])
        if mode == "owner":
            c.execute("UPDATE event_websites SET owner='invalid'")
        elif mode == "identity":
            doc["event_id"] = str(uuid4())
        elif mode == "revision":
            doc["revision"] = 99
        else:
            doc["published"]["guests"] = ["PRIVATE"]
        c.execute("UPDATE event_websites SET document=?", (json.dumps(doc),))
    assert client.get(endpoint(event)).status_code == 503
    assert client.get(public_url(state)).status_code == (404 if mode == "owner" else 503)
