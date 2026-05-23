from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import configure_database, init_database
from app.routes import adapters, ai, approvals, audit, dashboard, demo, intake, jobs, web

configure_database()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_database()
    yield

app = FastAPI(
    title="Campus ERP Integration Bridge",
    description="Synthetic Workday-adjacent ERP-style adapter and audit trail prototype.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(intake.router)
app.include_router(approvals.router)
app.include_router(jobs.router)
app.include_router(audit.router)
app.include_router(dashboard.router)
app.include_router(ai.router)
app.include_router(demo.router)
app.include_router(adapters.router)
app.include_router(web.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
