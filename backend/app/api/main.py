from contextlib import asynccontextmanager

import time

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db, init_db
from app.logging_config import configure_logging
from app.metrics import metrics
from app.api.routers import (
    eligibility,
    rankings,
    explain,
    ingest as ingest_router,
    monitoring as monitoring_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    yield


app = FastAPI(
    title="ForgeOne AI — Manufacturing Decision Copilot",
    description="Decision support only. No supplier is contacted, approved, "
                 "or ordered from through this API.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS is intentionally restrictive by default; allow origins can be configured
# via ALLOWED_ORIGINS in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed = time.perf_counter() - start_time
        metrics.record_request(500, elapsed)
        raise
    elapsed = time.perf_counter() - start_time
    metrics.record_request(response.status_code, elapsed)
    return response


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database connection unavailable") from exc
    return {"status": "ok"}


app.include_router(eligibility.router)
app.include_router(rankings.router)
app.include_router(explain.router)
app.include_router(ingest_router.router)
app.include_router(monitoring_router.router)
