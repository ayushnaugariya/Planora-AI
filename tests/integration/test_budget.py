"""Authoritative Decimal accounting and version-1 migration compatibility."""

import json
import sqlite3
from contextlib import closing
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import main
from app.core.errors import UnsupportedSchema
from app.repositories.workspaces import WorkspaceRepository
from app.schemas.budget import ExpenseRecord, ExpenseValues
from app.schemas.workspaces import EventWorkspace
from app.services.budget import calculate_budget
from tests.integration.test_workspaces import create, db_execute


def record(event, **changes):
    return ExpenseRecord(
        event_id=event.id,
        category_key="venue",
        description="Venue",
        currency=event.details.currency,
        **changes,
    )


def test_decimal_rounding_and_distinct_financial_stages(client):
    event = EventWorkspace.model_validate(create(client))
    expense = record(
        event,
        quantity="3",
        unit_amount="10.125",
        tax="0.005",
        fee="0.004",
        quoted_amount="40",
        committed_amount="35",
        paid_amount="10",
    )
    event.expenses = [expense]
    assert expense.line_total == Decimal("30.40")
    assert expense.payment_status == "part_paid"
    summary = calculate_budget(event)
    assert summary.estimated_cost == Decimal("30.40")
    assert summary.quoted_cost == 40 and summary.committed_spending == 35
    assert summary.actual_spending == 10 and summary.projected_cost == 35
    assert summary.remaining_funds == 59965 and summary.cash_remaining == 59990
    assert summary.outstanding_commitments == 25
    assert summary.contingency_reserve == 4800
    assert summary.reconciled
    assert "catering" in summary.missing_categories
    assert any(w.code == "quote_difference" and expense.id in w.expense_ids for w in summary.warnings)


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", "-1"),
        ("unit_amount", "-0.01"),
        ("paid_amount", "NaN"),
        ("fee", "Infinity"),
        ("tax", 1.2),
        ("description", " "),
        ("currency", "JPY"),
    ],
)
def test_invalid_expense_values(field, value):
    with pytest.raises(ValidationError):
        ExpenseValues.model_validate(
            {"category_key": "venue", "description": "Venue", "currency": "INR", field: value}
        )


def test_unknown_cost_payment_floor_and_overruns(client):
    event = EventWorkspace.model_validate(create(client))
    first = record(event, paid_amount="70000")
    second = record(event, unit_amount="100", committed_amount="50", paid_amount="60")
    event.expenses = [first, second]
    event.plan.budget_lines[1].amount = 100000
    result = event.budget_summary
    assert result.projected_cost == 70060
    assert first.id in result.unknown_expenses
    assert {"overallocated", "overspent", "category_overrun", "overpaid"} <= {w.code for w in result.warnings}
    assert second.payment_status == "paid" and first.payment_status == "payment_recorded"
    assert result.actual_spending == sum(c.paid for c in result.categories)


def test_cancelled_estimates_do_not_erase_commitments_or_payments(client):
    event = EventWorkspace.model_validate(create(client))
    event.expenses = [
        record(
            event,
            unit_amount="1000",
            quoted_amount="2000",
            committed_amount="500",
            paid_amount="100",
            cancelled=True,
        )
    ]
    result = event.budget_summary
    assert result.estimated_cost == result.quoted_cost == 0
    assert result.projected_cost == 500 and result.actual_spending == 100


def test_v1_migration_keeps_ids_history_progress_and_legacy_expenses(client, tmp_path):
    raw = create(client)
    raw.pop("budget_summary")
    raw["schema_version"] = 1
    expense_id = str(uuid4())
    raw["expenses"] = [{"id": expense_id, "category_key": "venue", "description": "Legacy", "amount": 123}]
    raw["tasks"][0]["completed"] = True
    path = tmp_path / "v1.sqlite3"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TABLE events(id TEXT PRIMARY KEY, owner TEXT, revision INTEGER, document TEXT)"
        )
        connection.execute(
            "INSERT INTO events VALUES(?,?,?,?)", (raw["id"], "owner", raw["revision"], json.dumps(raw))
        )
        connection.execute("PRAGMA user_version=1")
    repo = WorkspaceRepository(path)
    migrated = repo.get("owner", raw["id"])
    assert str(migrated.expenses[0].id) == expense_id
    assert migrated.expenses[0].estimate == 123 and migrated.expenses[0].provenance == "legacy"
    assert migrated.expenses[0].event_id == migrated.id
    assert migrated.history[0].revision == 1 and migrated.tasks[0].completed
    repo.initialize()
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        saved = connection.execute("SELECT document FROM events").fetchone()[0]
        assert "budget_summary" not in saved and "line_total" not in saved


def test_bad_v1_migration_rolls_back_schema_and_document(tmp_path):
    path = tmp_path / "bad.sqlite3"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE events(id TEXT, document TEXT)")
        connection.execute("INSERT INTO events VALUES('keep','{}')")
        connection.execute("PRAGMA user_version=1")
    with pytest.raises(UnsupportedSchema):
        WorkspaceRepository(path).initialize()
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
        assert connection.execute("SELECT document FROM events").fetchone()[0] == "{}"


def test_summary_is_derived_not_an_independent_database_total(client):
    event = create(client)
    document = db_execute(client, "SELECT document FROM events")[0][0]
    assert "budget_summary" not in document
    assert event["budget_summary"]["total_budget"] == "60000"


def add(client, event, **values):
    data = {
        "category_key": "venue",
        "description": "Venue cost",
        "currency": event["details"]["currency"],
        "unit_amount": "100.00",
        **values,
    }
    request = {"revision": event["revision"], "request_id": str(uuid4()), "expense": data}
    response = client.post(f"/api/events/{event['id']}/budget/expenses", json=request)
    assert response.status_code == 201, response.text
    return response.json(), request


def test_expense_crud_reconciliation_and_idempotent_retry(client):
    event = create(client)
    saved, body = add(client, event, quoted_amount="120", committed_amount="110", paid_amount="20")
    url = f"/api/events/{event['id']}/budget"
    expense = saved["expenses"][0]
    assert expense["line_total"] == "100.00" and expense["payment_status"] == "part_paid"
    assert client.get(url + "/expenses").json() == saved["expenses"]
    assert client.get(url + f"/expenses/{expense['id']}").json() == expense
    assert client.get(url).json() == saved["budget_summary"]
    assert client.get(url + "/warnings").json() == saved["budget_summary"]["warnings"]
    assert client.post(url + "/expenses", json=body).json() == saved
    conflict = {**body, "expense": {**body["expense"], "description": "Different"}}
    assert client.post(url + "/expenses", json=conflict).status_code == 409
    values = {**body["expense"], "paid_amount": "110", "unit_amount": "101.005"}
    changed = client.put(
        url + f"/expenses/{expense['id']}", json={"revision": saved["revision"], "expense": values}
    )
    assert changed.status_code == 200
    updated = changed.json()
    assert updated["expenses"][0]["id"] == expense["id"]
    assert updated["expenses"][0]["created_at"] == expense["created_at"]
    assert updated["expenses"][0]["line_total"] == "101.01"
    assert updated["budget_summary"]["actual_spending"] == "110.00"
    assert updated["budget_summary"]["projected_cost"] == "110.00"
    assert updated["expenses"][0]["payment_status"] == "paid"
    response = client.request(
        "DELETE",
        url + f"/expenses/{expense['id']}",
        json={"revision": updated["revision"], "confirm_id": expense["id"]},
    )
    assert response.status_code == 200
    assert response.json()["expenses"] == [] and response.json()["budget_summary"]["projected_cost"] == "0.00"
    assert client.get(url + f"/expenses/{expense['id']}").status_code == 404


@pytest.mark.parametrize(
    "overrides",
    [
        {"currency": "USD"},
        {"category_key": "unknown"},
        {"vendor_id": str(uuid4())},
        {"line_total": "0"},
        {"unit_amount": "-1"},
        {"quantity": "-1"},
    ],
)
def test_invalid_api_costs_leave_event_unchanged(client, overrides):
    event = create(client)
    response = client.post(
        f"/api/events/{event['id']}/budget/expenses",
        json={
            "revision": 1,
            "request_id": str(uuid4()),
            "expense": {"description": "Bad", "category_key": "venue", "currency": "INR", **overrides},
        },
    )
    assert response.status_code == 422
    assert client.get(f"/api/events/{event['id']}").json() == event


def test_allocations_sync_views_and_survive_regeneration(client):
    event = create(client)
    url = f"/api/events/{event['id']}"
    response = client.patch(
        url + "/budget/allocations",
        json={
            "revision": 1,
            "allocations": [
                {"key": "venue", "label": "Venue", "amount": 100},
                {"key": "custom", "label": "Travel extras", "amount": 100000},
            ],
        },
    )
    assert response.status_code == 200
    saved = response.json()
    assert "overallocated" in [w["code"] for w in saved["budget_summary"]["warnings"]]
    assert next(v["budget"] for v in saved["plan"]["vendors"] if v["key"] == "venue") == 100
    rebuilt = client.post(url + "/regenerate", json={"revision": saved["revision"]}).json()
    assert rebuilt["plan"]["budget_lines"] == saved["plan"]["budget_lines"]
    assert rebuilt["allocations_manual"]
    duplicate = {
        "revision": rebuilt["revision"],
        "allocations": [{"key": "venue", "label": "V", "amount": 1}] * 2,
    }
    assert client.patch(url + "/budget/allocations", json=duplicate).status_code == 422


def test_refunds_stale_writes_and_currency_conversion_are_not_silent(client):
    event, body = add(client, create(client), paid_amount="30", cost_basis="per_guest")
    url = f"/api/events/{event['id']}"
    eid = event["expenses"][0]["id"]
    assert event["expenses"][0]["quantity"] == "30"
    assert (
        client.put(
            url + f"/budget/expenses/{eid}",
            json={"revision": event["revision"], "expense": {**body["expense"], "paid_amount": "29"}},
        ).status_code
        == 422
    )
    assert (
        client.request(
            "DELETE",
            url + f"/budget/expenses/{eid}",
            json={"revision": event["revision"], "confirm_id": str(uuid4())},
        ).status_code
        == 422
    )
    assert (
        client.post(
            url + "/budget/expenses", json={**body, "request_id": str(uuid4()), "revision": 1}
        ).status_code
        == 409
    )
    assert (
        client.patch(
            url, json={"revision": event["revision"], "details": {**event["details"], "currency": "USD"}}
        ).status_code
        == 422
    )
    assert client.get(url).json() == event


def test_child_ownership_storage_failure_and_restart(client):
    event, body = add(client, create(client))
    other = create(client, title="Other")
    child = event["expenses"][0]["id"]
    assert client.get(f"/api/events/{other['id']}/budget/expenses/{child}").status_code == 404
    other_path = f"/api/events/{other['id']}/budget/expenses/{child}"
    assert (
        client.put(other_path, json={"revision": other["revision"], "expense": body["expense"]}).status_code
        == 404
    )
    assert (
        client.request(
            "DELETE", other_path, json={"revision": other["revision"], "confirm_id": child}
        ).status_code
        == 404
    )
    assert client.get(f"/api/events/{other['id']}").json() == other
    with TestClient(main.app) as stranger:
        assert stranger.get(f"/api/events/{event['id']}/budget").status_code == 404
    token = client.cookies.get("eventra_workspace_session")
    with TestClient(main.app) as reopened:
        reopened.cookies.set("eventra_workspace_session", token)
        assert reopened.get(f"/api/events/{event['id']}").json() == event
        db_execute(
            reopened,
            "CREATE TRIGGER no_cost_changes BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'blocked'); END",
        )
        response = reopened.request(
            "DELETE",
            f"/api/events/{event['id']}/budget/expenses/{child}",
            json={"revision": event["revision"], "confirm_id": child},
        )
        assert response.status_code == 503
        assert reopened.get(f"/api/events/{event['id']}").json() == event


def test_unknown_unit_cost_still_counts_known_fees_and_unallocated_records(client):
    event = EventWorkspace.model_validate(create(client))
    event.expenses = [record(event, tax="10", fee="5", paid_amount="7")]
    assert event.budget_summary.projected_cost == 15
    event.expenses[0].category_key = "unallocated"
    result = event.budget_summary
    assert result.projected_cost == 15 and any(w.code == "unallocated_category" for w in result.warnings)


def test_commitment_and_payment_discrepancies_do_not_double_count(client):
    event = EventWorkspace.model_validate(create(client))
    event.expenses = [
        record(event, unit_amount="100", quoted_amount="100", committed_amount="150", paid_amount="20"),
        record(event, unit_amount="100", paid_amount="150"),
    ]
    summary = event.budget_summary
    assert {"commitment_difference", "paid_exceeds_price"} <= {warning.code for warning in summary.warnings}
    assert summary.projected_cost == 300 and summary.actual_spending == 170
    assert summary.outstanding_commitments == 130
