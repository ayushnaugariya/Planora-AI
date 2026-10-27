"""Read-only natural-language intake; existing creation API remains the save boundary."""

from fastapi import APIRouter, Request

from app.ai.intake import extract_brief
from app.api.dependencies import Owner
from app.schemas.intake import EventBrief, IntakeRequest

router = APIRouter(tags=["planning intelligence"])


@router.post("/api/intake", response_model=EventBrief)
def event_brief(body: IntakeRequest, request: Request, _owner: Owner):
    return extract_brief(body.description, getattr(request.app.state, "llm", None))
