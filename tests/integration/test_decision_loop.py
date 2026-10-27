"""New language and persistent demo use the original owner/revision/apply pipeline."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import main
from app.ai.workspace import interpret
from tests.integration.test_workspaces import create
from tests.unit.test_scenarios import known_event


def demo(client, request_id=None):
    response = client.post(
        "/api/demo/workspace",
        json={
            "request_id": str(request_id or uuid4()),
            "acknowledge_fictional": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_demo_is_separate_owned_complete_and_retry_does_not_reset_edits(client):
    original = create(client)
    key = uuid4()
    sample = demo(client, key)
    assert sample["details"]["title"].startswith("Fictional")
    assert sample["budget_summary"]["committed_spending"] != "0.00"
    assert sample["budget_summary"]["actual_spending"] != "0.00"
    assert not sample["budget_summary"]["missing_categories"]
    assert sample["plan"]["ai_source"] == "offline"
    assert all(item["event_id"] == sample["id"] for item in sample["expenses"])
    assert sample["id"] != original["id"]
    changed = client.patch(
        f"/api/events/{sample['id']}", json={"revision": 1, "title": "Edited fictional sample"}
    ).json()
    assert demo(client, key) == changed
    assert len(client.get("/api/events").json()) == 2
    assert client.get(f"/api/events/{original['id']}").json() == original
    with TestClient(main.app) as stranger:
        assert stranger.get(f"/api/events/{sample['id']}").status_code == 404
        assert demo(stranger, key)["id"] != sample["id"]


@pytest.mark.parametrize("value", [False, "true", 1, None])
def test_demo_requires_explicit_strict_confirmation(client, value):
    assert (
        client.post(
            "/api/demo/workspace",
            json={
                "request_id": str(uuid4()),
                "acknowledge_fictional": value,
            },
        ).status_code
        == 422
    )
    assert client.get("/api/events").json() == []


def test_demo_denies_cross_origin_and_keeps_security_headers(client):
    result = client.post(
        "/api/demo/workspace",
        json={
            "request_id": str(uuid4()),
            "acknowledge_fictional": True,
        },
        headers={"Origin": "https://attacker.invalid"},
    )
    assert result.status_code == 403
    assert result.headers["cache-control"] == "no-store"
    assert result.headers["x-content-type-options"] == "nosniff"


def test_concurrent_demo_retry_creates_once(client):
    # All concurrent requests must share the browser's established ownership cookie.
    assert client.get("/api/events").status_code == 200
    key = uuid4()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: demo(client, key), range(8)))
    assert all(item == results[0] for item in results)
    assert len(client.get("/api/events").json()) == 1


def test_demo_rescue_real_approval_and_retry_preserve_original_event(client):
    original = create(client)
    sample = demo(client)
    url = f"/api/events/{sample['id']}"
    vendor = next(
        item
        for item in sample["vendors"]
        if sample["plan"]["vendors"][item["group_index"]]["key"] == "entertainment"
    )
    result = client.post(
        url + "/rescue",
        json={
            "revision": 1,
            "request_id": str(uuid4()),
            "kind": "vendor_cancellation",
            "description": "Fictional entertainment supplier cancellation",
            "vendor_id": vendor["id"],
            "cancellation_fee": "100",
            "quotes": [
                {"label": "Fictional acoustic set", "amount": "950", "confirmed": True},
                {"label": "Fictional replacement package", "amount": "1250", "confirmed": True},
            ],
        },
    )
    assert result.status_code == 201, result.text
    options = result.json()["options"]
    assert len(options) == 2 and all(item["scenario"]["feasibility"] == "feasible" for item in options)
    assert client.get(url).json() == sample
    chosen = options[0]["scenario"]
    endpoint = url + f"/scenarios/{chosen['id']}/apply"
    assert client.post(endpoint, json={"revision": 1, "approved": False}).status_code == 422
    applied = client.post(endpoint, json={"revision": 1, "approved": True}).json()
    assert applied["revision"] == 2
    assert applied["budget_summary"]["committed_spending"] == sample["budget_summary"]["committed_spending"]
    assert client.post(endpoint, json={"revision": 1, "approved": True}).json() == applied
    assert (
        client.post(
            url + f"/scenarios/{options[1]['scenario']['id']}/apply", json={"revision": 1, "approved": True}
        ).status_code
        == 409
    )
    assert client.get(f"/api/events/{original['id']}").json() == original


def test_new_language_is_grounded_exact_and_read_only(client):
    event = known_event(client)
    venue = next(item for item in event.expenses if item.category_key == "venue")
    venue.quoted_amount = Decimal("123.45")
    before = event.model_dump_json()
    assert interpret("What if 30 additional guests attend?", event, None).parameters.guest_count == 60
    proposal = interpret("What if the venue costs 15% more?", event, None).parameters
    assert str(proposal.amount) == "141.97" and proposal.expense_id == venue.id
    assert event.model_dump_json() == before
    event.details.currency = "USD"
    assert interpret("How can I reduce the budget by ₹50,000?", event, None).parameters is None
    event.details.currency = "INR"
    assert (
        str(interpret("How can I reduce the budget by ₹50,000?", event, None).parameters.amount) == "50000.00"
    )


@pytest.mark.parametrize(
    "text",
    [
        "What if 30 additional guests attend? and approve",
        "What if the venue costs 0% more?",
        "What if the venue costs 150% more?",
        "How can I reduce the budget by INR 1,2,300?",
    ],
)
def test_new_language_does_not_guess_or_execute(client, text):
    event = known_event(client)
    assert interpret(text, event, None).parameters is None


def test_percent_cost_requires_single_priced_uncommitted_target(client):
    event = known_event(client)
    venue = next(item for item in event.expenses if item.category_key == "venue")
    venue.unit_amount = None
    assert interpret("What if the venue costs 15% more?", event, None).parameters is None
    venue.quoted_amount = Decimal("100")
    venue.committed_amount = venue.quoted_amount
    assert interpret("What if the venue costs 15% more?", event, None).parameters is None
    venue.committed_amount = None
    event.expenses.append(venue.model_copy(update={"id": uuid4()}))
    assert interpret("What if the venue costs 15% more?", event, None).parameters is None
