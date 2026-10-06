from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _engine_kwargs(url: str) -> dict[str, object]:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    # PostgreSQL (deploy prompt): a small pool per worker; 2 workers x (5 + 5) stay well under
    # max_connections = 40 of deploy/postgres/postgresql.conf
    return {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 5, "pool_recycle": 1800}


settings = get_settings()
engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def bind_url(db) -> str:
    """The database URL of a session, bound to an engine or to a connection."""
    bind = db.get_bind()
    return str(getattr(bind, "url", None) or bind.engine.url)
