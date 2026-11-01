"""Eventra ASGI entry point and composition root; run app.main:app."""

import logging
import os
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.ai import gemini as ai
from app.api.budget import router as budget_router
from app.api.command_center import router as command_center_router
from app.api.coordination import router as coordination_router
from app.api.demo import router as demo_router
from app.api.errors import register_handlers
from app.api.guests import router as guest_router
from app.api.intake import router as intake_router
from app.api.intelligence import router as intelligence_router
from app.api.negotiations import router as negotiation_router
from app.api.planning import router as planning_router
from app.api.readiness import router as readiness_router
from app.api.rescue import router as rescue_router
from app.api.scenarios import router as scenario_router
from app.api.websites import router as website_router
from app.api.workspaces import router as workspace_router
from app.core import security
from app.core.config import FRONTEND_DIR, MAX_BODY_BYTES, PROJECT_ROOT, PROXY_POLICY, database_path
from app.core.errors import StorageUnavailable, UnsupportedSchema
from app.core.proxy import TrustedProxyMiddleware
from app.core.request_limits import RequestBodyLimitMiddleware
from app.repositories.workspaces import WorkspaceRepository

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("eventra")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.llm = ai.default_client()
    app.state.workspace_repository = WorkspaceRepository(
        database_path(),
        # Existing Cloud Run hosting is ephemeral/multi-instance. Until a shared
        # database is configured, never claim those local-file saves are durable.
        enabled=not bool(os.getenv("K_SERVICE")),
    )
    try:
        app.state.workspace_repository.initialize()
    except (sqlite3.Error, OSError, UnsupportedSchema, StorageUnavailable):
        # The stateless planner remains usable; saved-event operations retry
        # initialization and return an explicit storage error, never success.
        log.warning("Saved-event storage unavailable; stateless planning remains available")
    log.info("Eventra started (AI mode: %s)", "gemini" if app.state.llm else "offline")
    yield


app = FastAPI(
    title="Eventra",
    description="GenAI celebration and event planner",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Self-hosted Swagger UI below works with the existing CSP.
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

# Registration preserves: proxy -> guard -> body cap -> gzip -> router.
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestBodyLimitMiddleware, max_body_bytes=MAX_BODY_BYTES)
app.include_router(workspace_router)
app.include_router(website_router)
app.include_router(budget_router)
app.include_router(scenario_router)
app.include_router(coordination_router)
app.include_router(command_center_router)
app.include_router(guest_router)
app.include_router(negotiation_router)
app.include_router(rescue_router)
app.include_router(demo_router)
app.include_router(intake_router)
app.include_router(intelligence_router)
app.include_router(readiness_router)
app.middleware("http")(security.guard)
app.add_middleware(TrustedProxyMiddleware, policy=PROXY_POLICY)
register_handlers(app)
app.include_router(planning_router)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html", headers={"Cache-Control": "no-cache"})


@app.api_route("/api/docs", methods=["GET", "HEAD"], include_in_schema=False)
def documentation() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "api-docs.html")


# Match the narrow vendor mount before the general application static directory.
app.mount(
    "/static/assets/vendor/swagger-ui-5.34.0",
    StaticFiles(directory=PROJECT_ROOT / "vendor" / "swagger-ui-5.34.0"),
    name="swagger-assets",
)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
