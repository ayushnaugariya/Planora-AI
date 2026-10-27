"""Request-boundary regressions using actual ASGI receive messages."""

import asyncio
import json
from unittest.mock import Mock

import httpx
import pytest

from app import main
from app.api import planning
from app.core import security
from tests.conftest import payload
from tests.integration.test_ai_and_api import GOOD, FakeLLM


def request_chunks(chunks):
    return [
        {"type": "http.request", "body": chunk, "more_body": i < len(chunks) - 1}
        for i, chunk in enumerate(chunks)
    ]


def asgi_request(messages, *, headers=(), path="/api/plan", method="POST"):
    """Do not let an HTTP test transport aggregate chunks or repair metadata."""
    received = []
    sent = []

    async def run():
        remaining = iter(messages)

        async def receive():
            message = next(remaining, None)
            if message is None:
                # A connected client has nothing else to send. A buggy reader
                # must time out rather than receiving an invented disconnect.
                await asyncio.Event().wait()
            received.append(message)
            return message

        async def send(message):
            sent.append(message)

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.4"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "root_path": "",
            "query_string": b"",
            "headers": [(b"content-type", b"application/json"), *headers],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }
        await asyncio.wait_for(main.app(scope, receive, send), timeout=3)

    asyncio.run(run())
    starts = [message for message in sent if message["type"] == "http.response.start"]
    assert len(starts) == 1
    content = b"".join(
        message.get("body", b"") for message in sent if message["type"] == "http.response.body"
    )
    return httpx.Response(starts[0]["status"], headers=starts[0]["headers"], content=content), received


def padded_body(size, *, title="Mira's 8th"):
    body = json.dumps(payload(title=title), ensure_ascii=False).encode("utf-8")
    assert len(body) <= size
    return body + b" " * (size - len(body))


def assert_security_headers(response):
    for name, value in security.SECURITY_HEADERS.items():
        assert response.headers[name] == value
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("size", [19_999, 20_000, 20_001])
@pytest.mark.parametrize("title", ["Birthday", "\u00e9" * 40], ids=["ascii", "utf8"])
def test_actual_body_byte_boundaries(client, size, title):
    body = padded_body(size, title=title)
    response, received = asgi_request(request_chunks([body[:10_000], body[10_000:]]))

    assert len(received) == 2
    assert_security_headers(response)
    if size > 20_000:
        assert response.status_code == 413
        assert response.json() == {"error": "Request too large"}
    else:
        assert response.status_code == 200
        assert response.json()["title"] == title
        assert sum(line["amount"] for line in response.json()["budget_lines"]) == 60_000


@pytest.mark.parametrize("length", [None, b"0", b"1", b"invalid", b"-1", b"\xb2", b"20000, 20000"])
@pytest.mark.parametrize("multi_chunk", [False, True], ids=["single-chunk", "multi-chunk"])
def test_oversized_actual_chunks_stop_before_processing(client, monkeypatch, length, multi_chunk):
    handler = Mock(side_effect=AssertionError("oversized body reached the handler"))
    monkeypatch.setattr(planning, "build_plan", handler)
    llm = FakeLLM(GOOD)
    client.app.state.llm = llm
    body = padded_body(20_001)
    chunks = [body[:10_000], body[10_000:20_000], body[20_000:]] if multi_chunk else [body]
    # This valid JSON whitespace tail must remain unread after crossing the cap.
    messages = request_chunks([*chunks, b" " * 10_000])
    headers = [] if length is None else [(b"content-length", length)]
    headers.append((b"transfer-encoding", b"chunked"))

    response, received = asgi_request(messages, headers=headers)

    assert response.status_code == 413
    assert response.json() == {"error": "Request too large"}
    assert len(received) == len(chunks)
    handler.assert_not_called()
    assert llm.calls == []
    assert_security_headers(response)


@pytest.mark.parametrize("length", [b"20001", b"00020001", b" 20001 ", b"9" * 5000])
def test_oversized_declared_length_rejects_without_reading(client, length):
    response, received = asgi_request(request_chunks([b"{}"]), headers=[(b"content-length", length)])

    assert response.status_code == 413
    assert response.json() == {"error": "Request too large"}
    assert received == []
    assert_security_headers(response)


def test_conflicting_lengths_cannot_hide_oversized_declaration(client):
    response, received = asgi_request(
        request_chunks([b"{}"]), headers=[(b"content-length", b"1"), (b"content-length", b"20001")]
    )

    assert response.status_code == 413
    assert received == []
    assert_security_headers(response)


@pytest.mark.parametrize("length", [b"0", b"1", b"invalid", b"-1", b"\xb2", b"0" * 5000])
def test_bad_or_understated_metadata_uses_actual_body(client, length):
    body = json.dumps(payload()).encode()
    response, _ = asgi_request(
        request_chunks([body[:50], b"", body[50:]]), headers=[(b"content-length", length)]
    )

    assert response.status_code == 200
    assert response.json()["budget"] == 60_000
    assert_security_headers(response)


@pytest.mark.parametrize("partial", [b"", b'{"title": "unfinished'])
def test_disconnect_never_processes_partial_body(client, monkeypatch, partial):
    handler = Mock()
    monkeypatch.setattr(planning, "build_plan", handler)
    messages = []
    if partial:
        messages.append({"type": "http.request", "body": partial, "more_body": True})
    messages.append({"type": "http.disconnect"})

    response, received = asgi_request(messages)

    assert response.status_code == 400
    assert response.json() == {"detail": "There was an error parsing the body"}
    assert len(received) == len(messages)
    handler.assert_not_called()
    assert_security_headers(response)


@pytest.mark.parametrize("size", [100, 20_001])
def test_malformed_json_obeys_size_limit_before_validation(client, size):
    response, _ = asgi_request(request_chunks([b"!" * size]))

    assert response.status_code == (413 if size > 20_000 else 422)
    assert response.json()["error"] == ("Request too large" if size > 20_000 else "Invalid input")
    assert_security_headers(response)


def test_rate_limit_rejection_retains_headers_without_reading_body(client, monkeypatch):
    monkeypatch.setattr(security, "RATE_LIMIT", 1)
    security.rate_limited("127.0.0.1")

    response, received = asgi_request(request_chunks([b"{}"]), headers=[(b"content-length", b"2")])

    assert response.status_code == 429
    assert response.json() == {"error": "Too many requests. Please slow down."}
    assert int(response.headers["retry-after"]) >= 1
    assert received == []
    assert_security_headers(response)


@pytest.mark.parametrize("path", ["/api/plan", "/api/chat", "/api/ics"])
def test_valid_streamed_api_requests(client, path):
    data = {"question": "Where can I save money?", "plan": payload()} if path == "/api/chat" else payload()
    body = json.dumps(data).encode()
    response, _ = asgi_request(request_chunks([body[:1], body[1:50], body[50:]]), path=path)

    assert response.status_code == 200
    assert_security_headers(response)
    if path == "/api/ics":
        assert response.text.startswith("BEGIN:VCALENDAR")
        assert "attachment" in response.headers["content-disposition"]
    elif path == "/api/chat":
        assert response.json()["answer"]
    else:
        assert response.json()["budget"] == 60_000


@pytest.mark.parametrize("path", ["/", "/healthz", "/static/app.js", "/api/docs", "/api/openapi.json"])
def test_existing_unprotected_paths_do_not_consume_body(client, path):
    response, received = asgi_request(
        request_chunks([b"x" * 20_001]), headers=[(b"content-length", b"20001")], path=path, method="GET"
    )

    assert response.status_code == 200
    assert received == []
    assert response.headers["x-content-type-options"] == "nosniff"
    if path == "/":
        assert response.headers["cache-control"] == "no-cache"


def test_origin_preflight_behavior_is_unchanged(client):
    response = client.options(
        "/api/plan", headers={"origin": "https://example.test", "access-control-request-method": "POST"}
    )

    assert response.status_code == 405
    assert "access-control-allow-origin" not in response.headers
    assert_security_headers(response)
