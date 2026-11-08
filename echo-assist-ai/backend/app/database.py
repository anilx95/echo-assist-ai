"""
Database engine, session factory, and declarative base.

PostgreSQL is the application database. SQLite remains supported only for
isolated tests and local migration development; runtime schema changes are
managed exclusively by Alembic.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = (
    {"check_same_thread": False}
    if is_sqlite
    else {"connect_timeout": settings.DATABASE_CONNECT_TIMEOUT_SECONDS}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=not is_sqlite,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Yield a transaction-safe session for a request."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_health() -> tuple[bool, str | None]:
    """Perform a lightweight connectivity check without exposing credentials."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError as exc:
        return False, str(exc.__class__.__name__)
