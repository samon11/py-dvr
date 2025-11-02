"""Database session management and initialization.

This module provides database connection and session management following
the Dependency Inversion Principle and providing a clean abstraction layer
for database operations.

Design Principles:
    - Single Responsibility: Handles only database session lifecycle
    - Dependency Inversion: Provides abstract interface for database access
    - Interface Segregation: Separates concerns of session creation and management
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from pydvr.config import get_settings
from pydvr.models import Base


def _enable_sqlite_foreign_keys(dbapi_conn: Any, _: Any) -> None:
    """Enable foreign key constraints for SQLite connections.

    SQLite requires foreign keys to be explicitly enabled for each connection.
    This function is called automatically when creating an engine.

    Args:
        dbapi_conn: Database API connection
        _: Connection record (unused)
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class DatabaseManager:
    """Manages database engine and session creation.

    This class encapsulates all database connection logic and provides
    a clean interface for creating database sessions. It follows the
    Singleton pattern to ensure only one engine exists per application.

    Attributes:
        engine: SQLAlchemy engine instance
        SessionLocal: Session factory for creating new database sessions

    Example:
        >>> db = DatabaseManager()
        >>> with db.get_session() as session:
        ...     stations = session.query(Station).all()
    """

    def __init__(self, database_url: str | None = None) -> None:
        """Initialize database manager with connection.

        Args:
            database_url: Database connection URL. If None, loads from settings.

        Notes:
            - For SQLite, enables foreign key constraints
            - For production, uses connection pooling
            - For SQLite, disables check_same_thread for multi-threaded FastAPI
        """
        # Try to load settings, but don't fail if not available (e.g., in tests)
        debug_mode = False
        if database_url is None:
            try:
                settings = get_settings()
                self.database_url = settings.database_url
                debug_mode = settings.debug
            except Exception:
                # Settings not available (e.g., in tests without .env)
                # Fall back to default SQLite database
                self.database_url = "sqlite:///./pyhdhrdvr.db"
        else:
            self.database_url = database_url

        # Create engine with appropriate settings
        if self.database_url.startswith("sqlite"):
            # SQLite-specific configuration
            self.engine: Engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},  # Required for FastAPI
                echo=debug_mode,  # Log SQL queries in debug mode
            )
            # Enable foreign keys for SQLite
            event.listen(self.engine, "connect", _enable_sqlite_foreign_keys)
        else:
            # PostgreSQL/MySQL configuration
            self.engine = create_engine(
                self.database_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
                echo=debug_mode,
            )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def create_tables(self) -> None:
        """Create all database tables.

        This method creates tables for all models that inherit from Base.
        It's idempotent - calling it multiple times is safe.

        Note:
            In production, use Alembic migrations instead of this method.
            This is primarily for testing and initial development.

        Example:
            >>> db = DatabaseManager()
            >>> db.create_tables()
        """
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all database tables.

        WARNING: This permanently deletes all data!
        Use only in testing environments.

        Example:
            >>> db = DatabaseManager()
            >>> db.drop_tables()
        """
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions.

        Provides automatic session lifecycle management with proper
        error handling and cleanup.

        Yields:
            Session: Active database session

        Example:
            >>> db = DatabaseManager()
            >>> with db.get_session() as session:
            ...     station = session.query(Station).first()
            ...     print(station.name)

        Notes:
            - Automatically commits on success
            - Automatically rolls back on exception
            - Always closes session to release resources
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_new_session(self) -> Session:
        """Create a new database session.

        Use this when you need manual control over session lifecycle.
        Remember to close the session when done.

        Returns:
            Session: New database session

        Example:
            >>> db = DatabaseManager()
            >>> session = db.get_new_session()
            >>> try:
            ...     stations = session.query(Station).all()
            ...     session.commit()
            ... finally:
            ...     session.close()

        Note:
            Prefer using get_session() context manager when possible
            for automatic cleanup.
        """
        return self.SessionLocal()


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Get or create the global database manager instance.

    This function implements lazy loading and provides a single point of access
    to database functionality (Dependency Inversion Principle).

    Returns:
        DatabaseManager: The global database manager instance

    Example:
        >>> from app.db import get_db_manager
        >>> db = get_db_manager()
        >>> with db.get_session() as session:
        ...     stations = session.query(Station).all()
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.

    This function is designed to be used as a FastAPI dependency,
    providing automatic session management for API endpoints.

    Yields:
        Session: Active database session

    Example:
        >>> from fastapi import Depends
        >>> from app.db import get_db
        >>>
        >>> @app.get("/stations")
        >>> def get_stations(db: Session = Depends(get_db)):
        ...     return db.query(Station).all()

    Notes:
        - Automatically commits on success
        - Automatically rolls back on exception
        - Always closes session after request
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session


def init_db() -> None:
    """Initialize the database.

    Creates all tables if they don't exist. This is the main entry point
    for database initialization during application startup.

    For production deployments, use Alembic migrations instead:
        >>> alembic upgrade head

    Example:
        >>> from app.db import init_db
        >>> init_db()
        >>> print("Database initialized successfully")

    Note:
        This function is idempotent - calling it multiple times is safe.
    """
    db_manager = get_db_manager()
    db_manager.create_tables()


def reset_db() -> None:
    """Reset the database by dropping and recreating all tables.

    WARNING: This permanently deletes all data!
    Use only in testing and development environments.

    Example:
        >>> from app.db import reset_db
        >>> reset_db()
        >>> print("Database reset successfully")
    """
    db_manager = get_db_manager()
    db_manager.drop_tables()
    db_manager.create_tables()
