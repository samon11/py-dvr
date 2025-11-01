"""
Database session management and utilities.

Provides database connection and session management using SQLAlchemy 2.0+
with proper dependency injection patterns for FastAPI.
"""

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from alembic.config import Config
from alembic import command

from app.config import get_settings

# Get settings
settings = get_settings()

# Create database engine
# For SQLite: Check same thread is False to allow multiple threads
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Yields a database session and ensures it's properly closed after use.
    Use this with FastAPI's dependency injection system.

    Yields:
        Session: SQLAlchemy database session

    Example:
        >>> from fastapi import Depends
        >>> @app.get("/items")
        >>> def get_items(db: Session = Depends(get_db)):
        >>>     return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_database_empty() -> bool:
    """
    Check if the database has any tables.

    Returns:
        bool: True if the database is empty (no tables), False otherwise
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return len(tables) == 0


def run_migrations():
    """
    Run Alembic migrations to upgrade database to latest version.

    This function runs all pending Alembic migrations, bringing the database
    schema up to date with the current application models.

    Raises:
        Exception: If migrations fail for any reason
    """
    # Find alembic.ini relative to this file's parent directory (project root)
    project_root = Path(__file__).parent.parent
    alembic_ini_path = project_root / "alembic.ini"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {alembic_ini_path}")

    alembic_cfg = Config(str(alembic_ini_path))
    command.upgrade(alembic_cfg, "head")
