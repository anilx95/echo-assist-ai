"""
ECHO-ASSIST AI backend entrypoint.

Run with: uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    ai,
    auth,
    contacts,
    emergency,
    health,
    navigation,
    sensors,
    speech,
    user,
)
from app.core.config import settings
from app.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echo_assist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    init_db()
    logger.info("Database initialized. AI mock mode: %s", settings.AI_MOCK_MODE)
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(contacts.router)
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
