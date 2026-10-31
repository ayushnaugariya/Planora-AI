"""Anonymous ownership and current-revision HTTP dependencies."""

import hashlib
import re
import secrets
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Response

from app.core.errors import RevisionConflict
from app.repositories.workspaces import WorkspaceRepository
from app.schemas.workspaces import EventWorkspace

COOKIE = "eventra_workspace_session"

_TOKEN = re.compile(r"[A-Za-z0-9_-]{43}\Z")


def enforce_same_origin(request: Request) -> None:
    if request.method not in ("GET", "HEAD"):
        origin = request.headers.get("origin")
        expected = f"{request.url.scheme}://{request.url.netloc}"
        if request.headers.get("sec-fetch-site") == "cross-site" or (origin and origin != expected):
            raise HTTPException(status_code=403, detail="Cross-origin workspace changes are not allowed")


def owner_session(request: Request, response: Response) -> str:
    enforce_same_origin(request)
    token = request.cookies.get(COOKIE, "")
    if not _TOKEN.fullmatch(token):
        token = secrets.token_urlsafe(32)
        response.set_cookie(
            COOKIE,
            token,
            max_age=365 * 24 * 60 * 60,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="strict",
        )
    # Only a one-way owner reference reaches SQLite, never the bearer cookie.
    return hashlib.sha256(token.encode()).hexdigest()


Owner = Annotated[str, Depends(owner_session)]


def repository(request: Request) -> WorkspaceRepository:
    return request.app.state.workspace_repository


def current(request: Request, owner: str, event_id: UUID, revision: int) -> EventWorkspace:
    workspace = repository(request).get(owner, str(event_id))
    if workspace.revision != revision:
        raise RevisionConflict
    return workspace
