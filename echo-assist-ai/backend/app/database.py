"""
Database engine, session factory, and declarative base.

Uses SQLite for the MVP. DATABASE_URL is PostgreSQL-ready: swapping the
value in .env to a postgresql:// URL requires no code changes here.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. For MVP use; production should use Alembic migrations."""
    import app.models  # noqa: F401  (registers all models on Base.metadata)

    Base.metadata.create_all(bind=engine)
