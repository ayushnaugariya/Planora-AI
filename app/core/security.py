"""Existing header policy, process-local quota and request guard."""

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from app.core.config import MAX_BODY_BYTES, RATE_LIMIT, RATE_MAX_CLIENTS, RATE_WINDOW
from app.core.rate_limits import SlidingWindowLimiter
from app.core.request_limits import declared_body_too_large, protected_api_path

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; "
    "form-action 'self'; frame-ancestors 'none'"
)

SECURITY_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}

_limiter = SlidingWindowLimiter()

_hits = _limiter.hits  # Existing test reset/inspection hook; production writes use the lock.


def client_ip(request: Request) -> str:
    # TrustedProxyMiddleware supplies one canonical address before the guard.
    return request.client.host if request.client else "unknown"


def rate_limited(ip: str, now: float | None = None) -> int:
    """Sliding-window limiter. Returns seconds to wait, or 0 if allowed."""
    return _limiter.check(ip, limit=RATE_LIMIT, window=RATE_WINDOW, capacity=RATE_MAX_CLIENTS, now=now)


def secure_response(response: Response, path: str) -> Response:
    for k, v in SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    if path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    elif path.startswith("/static/"):
        # Unversioned module/style dependencies must revalidate after an upgrade.
        response.headers.setdefault("Cache-Control", "no-cache")
    return response


async def guard(request: Request, call_next):
    path = request.url.path
    if protected_api_path(path):
        if any(
            declared_body_too_large(length, MAX_BODY_BYTES)
            for length in request.headers.getlist("content-length")
        ):
            return secure_response(JSONResponse({"error": "Request too large"}, status_code=413), path)
        wait = rate_limited(client_ip(request))
        if wait:
            return secure_response(
                JSONResponse(
                    {"error": "Too many requests. Please slow down."},
                    status_code=429,
                    headers={"Retry-After": str(wait)},
                ),
                path,
            )
    response = await call_next(request)
    return secure_response(response, path)
