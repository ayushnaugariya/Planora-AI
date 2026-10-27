from datetime import date, timedelta

from app.core.cache import TTLCache
from app.services import planning as service
from tests.conftest import make_req, payload
from tests.integration.test_ai_and_api import GOOD, FakeLLM


def test_cache_hit_miss_and_expiry():
    c: TTLCache[int] = TTLCache(maxsize=2, ttl=10)
    assert c.get("a", now=0) is None
    c.set("a", 1, now=0)
    assert c.get("a", now=5) == 1
    assert c.get("a", now=10) is None  # expired exactly at ttl
    assert len(c) == 0


def test_cache_evicts_least_recently_used():
    c: TTLCache[int] = TTLCache(maxsize=2, ttl=100)
    c.set("a", 1, now=0)
    c.set("b", 2, now=0)
    c.get("a", now=1)  # a is now most recent
    c.set("c", 3, now=2)
    assert c.get("a", now=3) == 1
    assert c.get("b", now=3) is None
    assert c.get("c", now=3) == 3


def test_cache_clear():
    c: TTLCache[int] = TTLCache()
    c.set("a", 1)
    c.clear()
    assert len(c) == 0


def test_identical_requests_call_gemini_once(client):
    service.clear_cache()
    llm = FakeLLM(GOOD)
    client.app.state.llm = llm
    first = client.post("/api/plan", json=payload()).json()
    second = client.post("/api/plan", json=payload()).json()
    assert len(llm.calls) == 1
    assert first["ai_source"] == second["ai_source"] == "gemini"
    assert first["ideas"] == second["ideas"]


def test_different_requests_are_not_shared(client):
    llm = FakeLLM(GOOD)
    client.app.state.llm = llm
    client.post("/api/plan", json=payload(guest_count=30))
    client.post("/api/plan", json=payload(guest_count=31))
    assert len(llm.calls) == 2


def test_failures_are_not_cached(client):
    client.app.state.llm = FakeLLM(exc=RuntimeError("boom"))
    assert client.post("/api/plan", json=payload()).json()["ai_source"] == "offline"
    client.app.state.llm = FakeLLM(GOOD)
    assert client.post("/api/plan", json=payload()).json()["ai_source"] == "gemini"


def test_key_depends_on_date_and_request():
    req = make_req()
    today = date.today()
    assert service.cache_key(req, today) == service.cache_key(req, today)
    assert service.cache_key(req, today) != service.cache_key(req, today + timedelta(days=1))
    assert service.cache_key(req, today) != service.cache_key(make_req(guest_count=151), today)


def test_large_responses_are_gzipped(client):
    r = client.post("/api/plan", json=payload(), headers={"accept-encoding": "gzip"})
    assert r.status_code == 200
    assert r.headers.get("content-encoding") == "gzip"
    assert "default-src 'self'" in r.headers["content-security-policy"]
