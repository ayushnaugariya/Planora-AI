"""Existing safe HTTP error formats; wired by app.main."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from app.core.errors import RevisionConflict, StorageUnavailable, UnsupportedSchema, WorkspaceNotFound
from app.core.security import secure_response

log = logging.getLogger("eventra")


async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Do not echo user input back; report only field and message.
    details = [
        {"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "message": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse({"error": "Invalid input", "details": details}, status_code=422)


async def missing_workspace(_: Request, exc: WorkspaceNotFound) -> JSONResponse:
    return JSONResponse({"error": "Saved event not found"}, status_code=404)


async def stale_workspace(_: Request, exc: RevisionConflict) -> JSONResponse:
    return JSONResponse({"error": "This event changed. Reopen it before saving again."}, status_code=409)


async def unavailable_workspace(_: Request, exc: Exception) -> JSONResponse:
    log.warning("Saved-event operation failed (%s)", type(exc).__name__)
    return JSONResponse({"error": "Saved-event storage is unavailable. Please try again."}, status_code=503)


async def unhandled(request: Request, exc: Exception) -> Response:
    log.exception("Unhandled error")
    # ServerErrorMiddleware emits this response outside the normal HTTP guard.
    return secure_response(
        JSONResponse({"error": "Something went wrong. Please try again."}, status_code=500),
        request.url.path,
        https=request.url.scheme == "https",
    )


def register_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_handler)
    app.add_exception_handler(WorkspaceNotFound, missing_workspace)
    app.add_exception_handler(RevisionConflict, stale_workspace)
    app.add_exception_handler(StorageUnavailable, unavailable_workspace)
    app.add_exception_handler(UnsupportedSchema, unavailable_workspace)
    app.add_exception_handler(Exception, unhandled)
