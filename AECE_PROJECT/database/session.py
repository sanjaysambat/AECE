import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def _build_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    # Local dev fallback: SQLite file in workspace.
    return "sqlite:///./aece_local.db"


def create_engine_from_env() -> Engine:
    url = _build_database_url()
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


engine = create_engine_from_env()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

