"""Bound API request buffering before validation or endpoint execution."""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def protected_api_path(path: str) -> bool:
    return path.startswith("/api/") and not path.startswith("/api/docs") and path != "/api/openapi.json"


def declared_body_too_large(length: str, maximum: int) -> bool:
    """Compare decimal lengths without converting arbitrarily large integers.

    Malformed metadata is not authoritative; the actual byte count still applies.
    """
    length = length.strip()
    if not length.isascii() or not length.isdecimal():
        return False
    digits = length.lstrip("0")
    limit = str(maximum)
    return len(digits) > len(limit) or (len(digits) == len(limit) and digits > limit)


class RequestBodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not protected_api_path(scope["path"]):
            await self.app(scope, receive, send)
            return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                # Match FastAPI's existing incomplete-body parsing error, without
                # ever passing a partial request to validation or an endpoint.
                response = JSONResponse({"detail": "There was an error parsing the body"}, status_code=400)
                await response(scope, receive, send)
                return
            chunk = message.get("body", b"")
            if len(chunk) > self.max_body_bytes - len(body):
                response = JSONResponse({"error": "Request too large"}, status_code=413)
                await response(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        replayed = False

        async def replay_receive() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay_receive, send)
