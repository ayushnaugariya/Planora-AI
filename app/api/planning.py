"""Preserved stateless generation, chat, calendar and health routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.ai import gemini as ai
from app.schemas.planning import ChatRequest, ChatResponse, Plan, PlanRequest
from app.services import engine
from app.services.planning import build_plan

router = APIRouter()


def get_llm(request: Request) -> ai.LLM | None:
    return getattr(request.app.state, "llm", None)


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.post("/api/plan", response_model=Plan)
def create_plan(req: PlanRequest, request: Request) -> Plan:
    return build_plan(req, get_llm(request))


@router.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest, request: Request) -> ChatResponse:
    core = engine.compute(body.plan)
    answer, source = ai.answer_question(body.question, body.plan, core, get_llm(request))
    return ChatResponse(answer=answer, source=source)  # type: ignore[arg-type]


@router.post("/api/ics")
def export_ics(req: PlanRequest) -> Response:
    core = engine.compute(req)
    title = req.title or req.event_type.replace("_", " ").title()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    body = engine.to_ics(title, core.timeline, stamp)
    return Response(
        body,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="eventra-timeline.ics"'},
    )
