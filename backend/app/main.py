import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from sqlalchemy import text

from backend.app.activities.router import router as activities_router
from backend.app.activities.import_router import router as imports_router
from backend.app.athletes.router import router as athletes_router
from backend.app.competition.router import router as clubs_router
from backend.app.core.config import get_settings
from backend.app.core.database import SessionFactory, close_database
from backend.app.core.http_client import close_http_client
from backend.app.core.ids import uuid7
from backend.app.core.security import LOCAL_ADMIN_USER_ID
from backend.app.identity.models import User
from backend.app.core.problems import ProblemError, problem_handler
from backend.app.health.router import router as health_router
from backend.app.identity.router import privacy_router, router as identity_router
from backend.app.nutrition.router import router as nutrition_router
from backend.app.training.router import router as training_router
from backend.app.admin.router import router as admin_router
from backend.app.maps.router import router as maps_router
from backend.app.notifications.router import router as notifications_router
from backend.app.competition.public_router import router as competition_router
from backend.app.competition.leaderboards_router import router as leaderboards_router
from backend.app.athletes.goals_router import router as goals_router
from backend.app.competition.territory_router import router as territory_router
from backend.app.athletes.analytics_router import router as analytics_router
from backend.app.operations.safety_router import router as safety_router
from backend.app.moderation.router import router as moderation_router
from backend.app.operations.outbox import request_outbox_events
from backend.app.operations.publisher import publish_outbox_ids
from backend.app.competition.invitation_router import router as invitation_router
from backend.app.operations.idempotency import idempotency_middleware


logger = logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.admin_studio_open_access:
        async with SessionFactory() as session:
            if await session.get(User, LOCAL_ADMIN_USER_ID) is None:
                session.add(User(id=LOCAL_ADMIN_USER_ID, display_name="Local Admin Studio"))
                await session.commit()
    yield
    await close_http_client()
    await close_database()


settings = get_settings()
app = FastAPI(title="Runlete API", version="1.0.0", lifespan=lifespan, docs_url="/api/docs" if not settings.is_production else None, openapi_url="/api/openapi.json")
app.add_exception_handler(ProblemError, problem_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_origin_regex=None if settings.is_production else r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "If-Match", "X-Refresh-Token"],
)
app.middleware("http")(idempotency_middleware)


@app.middleware("http")
async def publish_committed_outbox(request: Request, call_next):
    token = request_outbox_events.set(())
    try:
        response = await call_next(request)
        event_ids = request_outbox_events.get()
        if event_ids and response.status_code < 500:
            expected = len(set(event_ids))
            published = await publish_outbox_ids(tuple(dict.fromkeys(event_ids)))
            if published != expected:
                logger.error("outbox publication deferred published=%s expected=%s", published, expected)
        return response
    finally:
        request_outbox_events.reset(token)


@app.middleware("http")
async def request_diagnostics(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid7())
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.1f}"
    response.headers["X-Request-ID"] = request_id
    if elapsed_ms >= 1_000:
        logger.warning("slow_request method=%s path=%s status=%s duration_ms=%.1f", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]: return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
async def readyz() -> dict[str, str]:
    async with SessionFactory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ready"}


for router in (identity_router, privacy_router, athletes_router, analytics_router, goals_router, training_router, imports_router, activities_router, clubs_router, invitation_router, competition_router, leaderboards_router, territory_router, nutrition_router, health_router, maps_router, safety_router, notifications_router, moderation_router, admin_router):
    app.include_router(router, prefix="/api/v1")


def canonical_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    for path_item in schema.get("paths", {}).values():
        for method in ("post", "put", "patch", "delete"):
            operation = path_item.get(method)
            if not operation or not operation.get("security"):
                continue
            parameters = operation.setdefault("parameters", [])
            if any(parameter.get("in") == "header" and parameter.get("name") == "Idempotency-Key" for parameter in parameters):
                continue
            parameters.append(
                {
                    "name": "Idempotency-Key",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string", "maxLength": 180},
                    "description": "Unique key used to replay an authenticated mutation safely for 24 hours.",
                }
            )
    app.openapi_schema = schema
    return schema


app.openapi = canonical_openapi
