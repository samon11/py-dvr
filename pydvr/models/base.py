"""Base model class providing common patterns for all database models.

This module defines the base class that all SQLAlchemy models inherit from,
following the Single Responsibility Principle by centralizing common
database patterns and timestamp management.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Abstract base class for all database models.

    Provides common functionality:
    - Primary key convention
    - Automatic timestamp tracking
    - Timezone-aware datetime handling
    - String representation

    All timestamps are stored in UTC to ensure consistency across timezones.
    """

    # Type annotation for mapped classes
    __abstract__ = True

    # Primary key - all models have an integer id
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Audit timestamps - automatically managed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="Record creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        doc="Record last update timestamp (UTC)",
    )

    def __repr__(self) -> str:
        """Return string representation showing class name and id.

        Returns:
            String in format: ClassName(id=123)
        """
        return f"{self.__class__.__name__}(id={self.id})"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary.

        Useful for serialization and API responses.
        Excludes SQLAlchemy internal attributes.

        Returns:
            Dictionary of column names to values
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
