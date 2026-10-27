"""Proxy identity and bounded rate-limit security regressions."""

import json
import os
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.core import config, security
from app.core.proxy import ProxyPolicy
from app.core.rate_limits import SlidingWindowLimiter, rate_settings
from tests.conftest import payload
from tests.security.test_request_limits import asgi_request, assert_security_headers, request_chunks


def scope(peer="10.0.0.2", headers=()):
    return {"type": "http", "scheme": "http", "client": (peer, 1234), "headers": list(headers)}


def forwarded(value):
    return [(b"x-forwarded-for", value)]


def test_untrusted_forwarding_headers_cannot_rotate_client_quota(client, monkeypatch):
    monkeypatch.setattr(security, "RATE_LIMIT", 2)
    codes = [
        client.post("/api/plan", json=payload(), headers={"x-forwarded-for": f"198.51.100.{i}"}).status_code
        for i in range(3)
    ]
    assert codes == [200, 200, 429]


def test_inactive_client_queues_expire_without_revisiting_each_client(client):
    for i in range(100):
        assert security.rate_limited(str(i), now=0) == 0
    assert security.rate_limited("new", now=security.RATE_WINDOW) == 0
    assert list(security._hits) == ["new"]


def test_unique_client_flood_does_not_grow_state_past_capacity(client):
    results = [security.rate_limited(str(i), now=0) for i in range(10_001)]
    assert len(security._hits) <= 10_000
    assert results[-1] > 0


@pytest.mark.parametrize("peer", ["192.0.2.1", "::ffff:192.0.2.1", "2001:db8::1"])
def test_direct_peer_ignores_all_forwarding_headers(peer):
    headers = forwarded(b"198.51.100.5") + [
        (b"x-forwarded-proto", b"https"),
        (b"forwarded", b"for=198.51.100.6;proto=https"),
        (b"x-real-ip", b"198.51.100.7"),
    ]
    expected = "192.0.2.1" if "ffff" in peer else peer
    assert ProxyPolicy().resolve(scope(peer, headers)) == (expected, "http")


@pytest.mark.parametrize(
    "value,expected",
    [
        (b"198.51.100.1", "198.51.100.1"),
        (b"198.51.100.1, 10.2.3.4", "198.51.100.1"),
        (b"192.0.2.5, 198.51.100.1, 10.2.3.4", "198.51.100.1"),
        (b"10.99.0.1, 198.51.100.1", "198.51.100.1"),
        (b"10.99.0.1, 10.2.3.4", "10.0.0.2"),
        (b"\t2001:0db8:0:0::1\t", "2001:db8::1"),
        (b"::ffff:198.51.100.1", "198.51.100.1"),
    ],
)
def test_trusted_chain_stops_at_nearest_untrusted_address(value, expected):
    assert ProxyPolicy("10.0.0.0/8").resolve(scope(headers=forwarded(value))) == (expected, "http")


@pytest.mark.parametrize(
    "value",
    [
        b"",
        b" ",
        b"unknown",
        b"_hidden",
        b"198.51.100.1:443",
        b"[2001:db8::1]",
        b"fe80::1%eth0",
        b"010.0.0.1",
        b"192.0.2.1,,10.2.3.4",
        b"192.0.2.1,",
        b"garbage, 198.51.100.1",
        b"\xff",
        b"192.0.2.1\r\n",
        b"a" * 2049,
        b",".join([b"192.0.2.1"] * 33),
    ],
)
def test_malformed_forwarding_uses_shared_peer_bucket(value):
    assert ProxyPolicy("10.0.0.2").resolve(scope(headers=forwarded(value))) == ("10.0.0.2", "http")


def test_duplicate_missing_and_unsupported_headers_never_invent_identity():
    policy = ProxyPolicy("10.0.0.2")
    for headers in ([], forwarded(b"192.0.2.1") * 2, [(b"forwarded", b"for=192.0.2.1")]):
        assert policy.resolve(scope(headers=headers)) == ("10.0.0.2", "http")
    assert policy.resolve(scope("192.0.2.1", forwarded(b"10.0.0.2"))) == ("192.0.2.1", "http")


def test_forwarding_limits_accept_exact_boundaries():
    policy = ProxyPolicy("10.0.0.2")
    for value in (b" " * 2036 + b"198.51.100.1", b",".join([b"198.51.100.1"] * 32)):
        assert policy.resolve(scope(headers=forwarded(value)))[0] == "198.51.100.1"
    data = scope()
    del data["client"]
    assert policy.resolve(data) == ("unknown", "http")


@pytest.mark.parametrize("peer", [None, (), ("not-an-ip", 1), ("fe80::1%zone", 1)])
def test_invalid_or_missing_peer_uses_one_unknown_bucket(peer):
    data = scope(headers=forwarded(b"192.0.2.1"))
    data["client"] = peer
    assert ProxyPolicy("10.0.0.2").resolve(data) == ("unknown", "http")


def test_ipv6_and_mapped_proxy_peers_are_canonical():
    policy = ProxyPolicy("2001:db8::/32,10.0.0.2")
    assert policy.resolve(scope("2001:db8::2", forwarded(b"192.0.2.1")))[0] == "192.0.2.1"
    assert policy.resolve(scope("::ffff:10.0.0.2", forwarded(b"192.0.2.1")))[0] == "192.0.2.1"


@pytest.mark.parametrize("value", [b"https,http", b"https ", b"HTTPS", b"ftp", b""])
def test_ambiguous_or_invalid_scheme_is_ignored(value):
    assert ProxyPolicy("10.0.0.2").resolve(scope(headers=[(b"x-forwarded-proto", value)]))[1] == "http"


def test_scheme_requires_one_value_from_a_trusted_peer():
    headers = [(b"x-forwarded-proto", b"https")]
    policy = ProxyPolicy("10.0.0.2")
    assert policy.resolve(scope(headers=headers))[1] == "https"
    assert policy.resolve(scope(headers=headers * 2))[1] == "http"
    assert policy.resolve(scope("192.0.2.1", headers))[1] == "http"


@pytest.mark.parametrize(
    "cidrs",
    [
        "*",
        "0.0.0.0/0",
        "::/0",
        "localhost",
        "10.0.0.1/8",
        "10.0.0.1,",
        "x" * 4097,
        ",".join(["10.0.0.1"] * 33),
    ],
)
def test_unsafe_proxy_configuration_fails_clearly(cidrs):
    with pytest.raises(ValueError, match="TRUSTED_PROXY_CIDRS"):
        ProxyPolicy(cidrs)


def test_deployment_does_not_implicitly_enable_proxy_trust():
    assert not ProxyPolicy.from_env({"K_SERVICE": "eventra", "FORWARDED_ALLOW_IPS": "*"}).networks
    assert not ProxyPolicy.from_env({"TRUST_PROXY": "0"}).networks
    with pytest.raises(ValueError, match="Remove TRUST_PROXY"):
        ProxyPolicy.from_env({"TRUST_PROXY": "1"})
    assert ProxyPolicy.from_env({"TRUSTED_PROXY_CIDRS": "10.0.0.2"}).networks


def test_trusted_proxy_api_keys_use_resolved_clients_not_spoofed_prefix(client, monkeypatch):
    monkeypatch.setattr(config.PROXY_POLICY, "networks", ProxyPolicy("10.0.0.2").networks)
    monkeypatch.setattr(security, "RATE_LIMIT", 2)
    with TestClient(main.app, client=("10.0.0.2", 1234)) as proxy:
        proxy.app.state.llm = None
        codes = [
            proxy.post(
                "/api/plan",
                json=payload(),
                headers={
                    "x-forwarded-for": f"192.0.2.{i}, 198.51.100.1",
                },
            ).status_code
            for i in range(3)
        ]
        assert codes == [200, 200, 429]
        assert (
            proxy.post("/api/plan", json=payload(), headers={"x-forwarded-for": "198.51.100.2"}).status_code
            == 200
        )
    assert set(security._hits) == {"198.51.100.1", "198.51.100.2"}


def test_trusted_https_preserves_secure_cookie_and_origin_check(client, monkeypatch):
    monkeypatch.setattr(config.PROXY_POLICY, "networks", ProxyPolicy("10.0.0.2").networks)
    headers = {
        "x-forwarded-proto": "https",
        "x-forwarded-for": "198.51.100.1",
        "origin": "https://testserver",
    }
    with TestClient(main.app, client=("10.0.0.2", 1234)) as proxy:
        proxy.app.state.llm = None
        response = proxy.post("/api/events", json={"details": payload()}, headers=headers)
        assert response.status_code == 201
        cookie = response.headers["set-cookie"].lower()
        assert "secure" in cookie and "httponly" in cookie and "samesite=strict" in cookie
        assert_security_headers(response)
        headers["origin"] = "https://attacker.invalid"
        assert proxy.post("/api/events", json={"details": payload()}, headers=headers).status_code == 403
    assert (
        client.post(
            "/api/events",
            json={"details": payload()},
            headers={"x-forwarded-proto": "https", "origin": "https://testserver"},
        ).status_code
        == 403
    )


def check(limiter, key, now, *, limit=2, window=60, capacity=2):
    return limiter.check(key, now=now, limit=limit, window=window, capacity=capacity)


def test_sliding_window_exact_expiry_retry_rounding_and_denied_requests():
    limiter = SlidingWindowLimiter()
    assert check(limiter, "a", 0) == 0
    assert check(limiter, "a", 1) == 0
    assert check(limiter, "a", 59.1) == 1
    assert list(limiter.hits["a"]) == [0, 1]
    assert check(limiter, "a", 60) == 0
    assert list(limiter.hits["a"]) == [1, 60]
    assert check(limiter, "a", 60.5) == 1
    assert check(limiter, "a", 61) == 0
    assert check(limiter, "a", 121) == 0
    assert list(limiter.hits["a"]) == [121]


def test_capacity_never_evicts_active_quotas_and_denied_keys_do_not_accumulate():
    limiter = SlidingWindowLimiter()
    assert check(limiter, "a", 0) == 0
    assert check(limiter, "b", 1) == 0
    assert check(limiter, "a", 2) == 0
    assert list(limiter.hits) == ["b", "a"]
    for i in range(1000):
        assert check(limiter, str(i), 4) == 57
    assert check(limiter, "a", 4) == 56
    assert list(limiter.hits) == ["b", "a"]
    assert check(limiter, "b", 5) == 0  # Existing client may use remaining quota.
    assert check(limiter, "new", 61) == 1  # a's last admitted request expires at 62.
    assert check(limiter, "new", 62) == 0
    assert list(limiter.hits) == ["b", "new"]


def test_cleanup_expires_idle_keys_even_when_hot_client_is_denied():
    limiter = SlidingWindowLimiter()
    for i in range(1000):
        assert check(limiter, str(i), 0, capacity=1001) == 0
    assert check(limiter, "hot", 1, capacity=1001, limit=1) == 0
    assert check(limiter, "hot", 60, capacity=1001, limit=1) == 1
    assert list(limiter.hits) == ["hot"]


def test_concurrent_same_client_and_expiry_admit_exact_quota():
    limiter = SlidingWindowLimiter()
    with ThreadPoolExecutor(max_workers=16) as pool:
        first = list(pool.map(lambda _: check(limiter, "a", 0, limit=7), range(80)))
        assert first.count(0) == 7
        assert len(limiter.hits["a"]) == 7
        second = list(pool.map(lambda _: check(limiter, "a", 60, limit=7), range(80)))
        assert second.count(0) == 7
        assert len(limiter.hits["a"]) == 7


def test_concurrent_unique_clients_never_exceed_capacity_or_reset_quotas():
    limiter = SlidingWindowLimiter()
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda i: check(limiter, str(i), 0, capacity=8), range(100)))
        assert results.count(0) == len(limiter.hits) == 8
        admitted = list(limiter.hits)
        again = list(pool.map(lambda key: check(limiter, key, 1, capacity=8), admitted * 8))
        assert again.count(0) == 8
    assert sum(map(len, limiter.hits.values())) == 16


@pytest.mark.parametrize(
    "name,value",
    [
        ("RATE_LIMIT", "0"),
        ("RATE_LIMIT", "-1"),
        ("RATE_LIMIT", "1.5"),
        ("RATE_LIMIT", "10001"),
        ("RATE_LIMIT", ""),
        ("RATE_LIMIT", "９"),
        ("RATE_LIMIT", "9" * 5000),
        ("RATE_WINDOW", "0"),
        ("RATE_WINDOW", "86401"),
        ("RATE_MAX_CLIENTS", "0"),
        ("RATE_MAX_CLIENTS", "100001"),
    ],
)
def test_invalid_rate_configuration_fails_closed(name, value):
    with pytest.raises(ValueError, match=name):
        rate_settings({name: value})


def test_default_and_bounded_rate_configuration():
    assert rate_settings({}) == (30, 60, 10000)
    assert rate_settings({"RATE_LIMIT": "10000", "RATE_WINDOW": "86400", "RATE_MAX_CLIENTS": "100"}) == (
        10000,
        86400,
        100,
    )
    with pytest.raises(ValueError, match="must not exceed"):
        rate_settings({"RATE_LIMIT": "101"})


def test_supplied_launchers_preserve_the_original_transport_peer():
    root = Path(__file__).resolve().parents[2]
    docker = (root / "Dockerfile").read_text(encoding="utf-8")
    command = json.loads(next(line[4:] for line in docker.splitlines() if line.startswith("CMD ")))[-1]
    assert "--no-proxy-headers" in command
    assert "--forwarded-allow-ips" not in command
    runner = (root / "tests/browser/browser_workspace_smoke.mjs").read_text(encoding="utf-8")
    assert '"--no-proxy-headers"' in runner


def test_capacity_rejection_preserves_headers_and_does_not_read_payload(client, monkeypatch):
    monkeypatch.setattr(security, "RATE_MAX_CLIENTS", 1)
    security.rate_limited("192.0.2.1")
    response, read = asgi_request(request_chunks([b"{}", b"unread"]), path="/api/events")
    assert response.status_code == 429 and read == []
    assert response.json() == {"error": "Too many requests. Please slow down."}
    assert int(response.headers["retry-after"]) >= 1
    assert_security_headers(response)


@contextmanager
def live_server(tmp_path, trusted):
    """Real HTTP/ASGI boundary, isolated storage, no credentials or ambient proxy."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = {
        **os.environ,
        "GEMINI_API_KEY": "",
        "GOOGLE_API_KEY": "",
        "K_SERVICE": "",
        "EVENTRA_DB_PATH": str(tmp_path / "server.sqlite3"),
        "RATE_LIMIT": "2",
        "RATE_WINDOW": "60",
        "RATE_MAX_CLIENTS": "10",
        "TRUST_PROXY": "0",
        "TRUSTED_PROXY_CIDRS": trusted,
        # This setting must be inert because the supported launch disables the
        # server's own proxy processing, retaining the transport peer for ours.
        "FORWARDED_ALLOW_IPS": "*",
    }
    with (tmp_path / "server.log").open("w+", encoding="utf-8") as output:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-proxy-headers",
            ],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            stdout=output,
            stderr=output,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=2, trust_env=False) as wire:
                deadline = time.monotonic() + 10
                while True:
                    try:
                        assert wire.get("/healthz").status_code == 200
                        break
                    except httpx.TransportError:
                        if process.poll() is not None or time.monotonic() >= deadline:
                            output.seek(0)
                            pytest.fail("Uvicorn did not start: " + output.read())
                        time.sleep(0.05)
                yield wire
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.mark.parametrize("trusted,expected", [("", [200, 200, 429]), ("127.0.0.1", [200, 200, 200])])
def test_real_server_preserves_peer_and_applies_only_configured_trust(tmp_path, trusted, expected):
    with live_server(tmp_path, trusted) as wire:
        responses = [
            wire.post(
                "/api/plan",
                json=payload(),
                headers={
                    "x-forwarded-for": f"198.51.100.{i}",
                },
            )
            for i in range(3)
        ]
        assert [response.status_code for response in responses] == expected
        for response in responses:
            assert_security_headers(response)
        if trusted:
            # The trusted ingress appends the nearest untrusted client after
            # any original header. Rotating that original prefix cannot evade.
            codes = [
                wire.post(
                    "/api/plan",
                    json=payload(),
                    headers={
                        "x-forwarded-for": f"192.0.2.{i}, 198.51.100.250",
                    },
                ).status_code
                for i in range(3)
            ]
            assert codes == [200, 200, 429]
