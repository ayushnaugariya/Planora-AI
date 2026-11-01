"""Transport and cross-origin hardening headers on normal, error and static responses."""

from fastapi.testclient import TestClient

from app import main
from app.core.security import HSTS, SECURITY_HEADERS


def test_hardening_headers_on_page_api_and_static_responses(client):
    for path in ("/", "/healthz", "/api/events", "/static/app.js", "/e/not-a-published-slug"):
        response = client.get(path)
        assert response.headers["cross-origin-resource-policy"] == "same-origin", path
        assert response.headers["x-permitted-cross-domain-policies"] == "none", path
        assert "payment=()" in response.headers["permissions-policy"], path
        assert SECURITY_HEADERS["X-Frame-Options"] == response.headers["x-frame-options"]


def test_hsts_is_sent_only_over_https(client, tmp_path, monkeypatch):
    assert "strict-transport-security" not in client.get("/healthz").headers
    monkeypatch.setenv("EVENTRA_DB_PATH", str(tmp_path / "https.sqlite3"))
    with TestClient(main.app, base_url="https://testserver") as secure:
        secure.app.state.llm = None
        for path in ("/", "/healthz", "/e/not-a-published-slug"):
            assert secure.get(path).headers["strict-transport-security"] == HSTS, path


def test_hsts_on_rejected_https_requests(tmp_path, monkeypatch):
    monkeypatch.setenv("EVENTRA_DB_PATH", str(tmp_path / "reject.sqlite3"))
    with TestClient(main.app, base_url="https://testserver") as secure:
        secure.app.state.llm = None
        response = secure.post("/api/events", content=b"{}", headers={"content-length": "999999"})
        assert response.status_code == 413
        assert response.headers["strict-transport-security"] == HSTS
