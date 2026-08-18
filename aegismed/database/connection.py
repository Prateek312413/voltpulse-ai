"""
AegisMed Database Connection & Engine Manager
Supports CockroachDB Distributed SQL and automatic local fallback.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from aegismed.config import settings
from aegismed.database.models import Base

logger = logging.getLogger("aegismed.database")
logging.basicConfig(level=logging.INFO)

# Determine Engine
def create_app_engine():
    """Attempts to connect to CockroachDB, falls back to SQLite if unreachable."""
    try:
        db_url = settings.COCKROACH_DB_URL
        if db_url.startswith("cockroachdb://"):
            pg_url = db_url.replace("cockroachdb://", "postgresql+psycopg2://")
        else:
            pg_url = db_url
            
        test_engine = create_engine(
            pg_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 2}
        )
        with test_engine.connect() as conn:
            logger.info("Successfully connected to CockroachDB distributed cluster!")
        return test_engine, "COCKROACHDB"
    except Exception:
        if settings.USE_FALLBACK_DB_IF_UNAVAILABLE:
            sqlite_url = f"sqlite:///{settings.SQLITE_FALLBACK_PATH}"
            fallback_engine = create_engine(
                sqlite_url,
                connect_args={"check_same_thread": False}
            )
            return fallback_engine, "LOCAL_FALLBACK"
        else:
            raise



engine, active_backend = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes all database tables and indexes."""
    Base.metadata.create_all(bind=engine)
    logger.info(f"Initialized AegisMed Database schema using [{active_backend}] backend.")


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic rollback on failure."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_db():
    """FastAPI dependency yielding a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
