"""Private publisher and separate anonymous allowlisted public endpoints."""

import re
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.ai.website_copy import generate
from app.api.dependencies import Owner, current, enforce_same_origin, repository
from app.core.config import FRONTEND_DIR
from app.core.errors import RevisionConflict
from app.repositories import websites
from app.schemas.websites import (
    ApprovalRequest,
    ContentRequest,
    DraftRequest,
    PublicResponse,
    PublicWebsite,
    PublishRequest,
    ResponseAcknowledgement,
    WebsiteCopy,
    WebsitePreview,
    WebsiteState,
)
from app.services.websites import preview_hash, project

router = APIRouter()
PREFIX = "/api/events/{event_id}/website"


def valid_slug(slug):
    if not re.fullmatch(r"[A-Za-z0-9_-]{32}", slug):
        raise HTTPException(status_code=404, detail="Invitation not available")
    return slug


@router.get(PREFIX, response_model=WebsiteState, tags=["event website"])
def get_website(event_id: UUID, request: Request, owner: Owner):
    return websites.read(repository(request), owner, event_id)


@router.put(PREFIX, response_model=WebsiteState, tags=["event website"])
def save_website(event_id: UUID, body: DraftRequest, request: Request, owner: Owner):
    return websites.mutate(repository(request), owner, event_id, body, "save")


@router.post(PREFIX + "/preview", response_model=WebsitePreview, tags=["event website"])
def preview_website(event_id: UUID, body: DraftRequest, request: Request, owner: Owner):
    current(request, owner, event_id, body.event_revision)
    saved = websites.read(repository(request), owner, event_id)
    if saved.revision != body.revision:
        raise RevisionConflict
    return WebsitePreview(
        website=project(body.config), preview_hash=preview_hash(body.config), public_path=saved.public_path
    )


@router.post(PREFIX + "/publish", response_model=WebsiteState, tags=["event website"])
def publish_website(event_id: UUID, body: PublishRequest, request: Request, owner: Owner):
    return websites.mutate(repository(request), owner, event_id, body, "publish")


@router.post(PREFIX + "/unpublish", response_model=WebsiteState, tags=["event website"])
def unpublish_website(event_id: UUID, body: ApprovalRequest, request: Request, owner: Owner):
    return websites.mutate(repository(request), owner, event_id, body, "unpublish")


@router.post(PREFIX + "/content", response_model=WebsiteCopy, tags=["event website"])
def generate_copy(event_id: UUID, body: ContentRequest, request: Request, owner: Owner):
    current(request, owner, event_id, body.event_revision)
    saved = websites.read(repository(request), owner, event_id)
    if body.revision != saved.revision:
        raise RevisionConflict
    return generate(body, request.app.state.llm)


@router.get("/api/public/websites/{slug}", response_model=PublicWebsite, tags=["public invitation"])
def public_website(slug: str, request: Request):
    return websites.public_read(repository(request), valid_slug(slug))


@router.post(
    "/api/public/websites/{slug}/rsvp",
    response_model=ResponseAcknowledgement,
    status_code=202,
    tags=["public invitation"],
)
def public_rsvp(slug: str, body: PublicResponse, request: Request):
    enforce_same_origin(request)
    return websites.submit(repository(request), valid_slug(slug), body)


@router.get("/e/{slug}", include_in_schema=False)
def public_page(slug: str, request: Request):
    try:
        websites.public_read(repository(request), valid_slug(slug))
    except HTTPException as exc:
        if exc.status_code != 404:
            raise
        return FileResponse(
            FRONTEND_DIR / "invitation-unavailable.html",
            status_code=404,
            headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, noarchive"},
        )
    return FileResponse(
        FRONTEND_DIR / "invitation.html",
        headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, noarchive"},
    )
