from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import main
from app.core import security
from app.schemas.planning import PlanRequest
from app.services import planning as service


def make_req(**over) -> PlanRequest:
    base = dict(
        event_type="wedding",
        title="Asha and Ravi",
        event_date=date.today() + timedelta(days=300),
        guest_count=150,
        budget=1_200_000,
        currency="INR",
        formality="semi_formal",
    )
    base.update(over)
    return PlanRequest(**base)


def payload(**over) -> dict:
    base = dict(
        event_type="birthday",
        title="Mira's 8th",
        event_date=(date.today() + timedelta(days=45)).isoformat(),
        guest_count=30,
        budget=60000,
        currency="INR",
        formality="casual",
        priorities=["food"],
        dietary=["vegetarian"],
        interests="dinosaurs",
        theme="Jurassic",
    )
    base.update(over)
    return base


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("EVENTRA_DB_PATH", str(tmp_path / "events.sqlite3"))
    security._hits.clear()
    service.clear_cache()
    with TestClient(main.app) as c:
        c.app.state.llm = None  # force offline mode regardless of env
        yield c
