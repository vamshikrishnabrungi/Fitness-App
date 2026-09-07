from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from backend.app.core.database import SessionFactory, close_database
from backend.app.core.http_client import close_http_client
from backend.app.core.problems import ProblemError, problem_handler
from backend.app.operations.worker_router import router as worker_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_http_client()
    await close_database()


app = FastAPI(
    title="Runlete Worker",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    openapi_url=None,
)
app.add_exception_handler(ProblemError, problem_handler)


@app.get("/healthz", include_in_schema=False)
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
async def readyz() -> dict[str, str]:
    async with SessionFactory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ready"}


app.include_router(worker_router)
