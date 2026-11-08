"""
ECHO-ASSIST AI backend entrypoint.

Run with: uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
import logging
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    ai,
    auth,
    contacts,
    dashboard,
    devices,
    emergency,
    health,
    navigation,
    notifications,
    sensors,
    speech,
    user,
)
from app.core.config import settings
from app.database import check_database_health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echo_assist")
_rate_limit_buckets: dict[str, tuple[float, int]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    database_ready, database_error = check_database_health()
    if database_ready:
        logger.info("Database connection is ready. AI mock mode: %s", settings.AI_MOCK_MODE)
    else:
        logger.warning("Database connection is unavailable at startup: %s", database_error)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI for Inclusive Mobility - backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """Small safe default for single-instance deployments.

    Put an edge proxy or Redis-backed limiter in front of multi-worker
    production deployments; this guard intentionally does not treat itself as
    a distributed security control.
    """
    if request.url.path in {"/health", "/docs", "/openapi.json", "/redoc"}:
        return await call_next(request)
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    start, count = _rate_limit_buckets.get(client, (now, 0))
    if now - start >= settings.RATE_LIMIT_WINDOW_SECONDS:
        start, count = now, 0
    if count >= settings.RATE_LIMIT_REQUESTS:
        return JSONResponse(status_code=429, content={"detail": "Too many requests. Please try again shortly."})
    _rate_limit_buckets[client] = (start, count + 1)
    return await call_next(request)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(contacts.router)
app.include_router(devices.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(ai.router)
app.include_router(sensors.router)
app.include_router(emergency.router)
app.include_router(navigation.router)
app.include_router(speech.router)


# Mount static files (web dashboard)
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/")
def root():
    """Serve the web dashboard if it exists, otherwise return JSON info."""
    index = _static_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {
        "app": settings.APP_NAME,
        "tagline": "AI for Inclusive Mobility",
        "docs": "/docs",
    }
