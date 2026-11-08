"""Test-only configuration established before application modules are imported."""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_echo_assist.db"
os.environ["DEBUG"] = "false"
os.environ["MAPS_API_KEY"] = ""
os.environ["TWILIO_ACCOUNT_SID"] = ""
os.environ["TWILIO_AUTH_TOKEN"] = ""
os.environ["TWILIO_PHONE_NUMBER"] = ""
os.environ["RESEND_API_KEY"] = ""
os.environ["RESEND_FROM_EMAIL"] = ""

from app.core.config import get_settings
get_settings.cache_clear()


@pytest.fixture()
def client():
    from app.core.config import settings
    from app.database import engine
    from app.main import app

    db_path = "test_echo_assist.db"
    engine.dispose()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(config, "head")
    with TestClient(app) as test_client:
        yield test_client
    engine.dispose()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
