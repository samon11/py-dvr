"""Lineup model representing a Schedules Direct lineup.

A Lineup represents a collection of stations available in a specific location
and transport method (e.g., Cable in ZIP 94105, Antenna in 10001).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.station import Station


class Lineup(Base):
    """Represents a Schedules Direct lineup.

    Lineups define the available stations for a specific location and
    transport method. Users typically have one or more lineups associated
    with their Schedules Direct account.

    Attributes:
        lineup_id: Schedules Direct lineup ID (primary key, e.g., "USA-CA94105-X")
        name: Human-readable lineup name (e.g., "Comcast Cable - San Francisco")
        transport: Transport method (Cable, Satellite, Antenna, etc.)
        location: ZIP code or location identifier
        modified: Last modified timestamp from Schedules Direct
        is_deleted: Soft delete flag for removed lineups
        stations: Relationship to Station entities in this lineup

    Indexes:
        - Primary key on lineup_id
    """

    __tablename__ = "lineups"

    # Override id to use string lineup_id from Schedules Direct
    id: Mapped[str] = mapped_column(
        "lineup_id",
        String(64),
        primary_key=True,
        doc="Schedules Direct lineup ID"
    )

    # Core lineup metadata
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        doc="Human-readable lineup name"
    )

    transport: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        doc="Transport method (Cable, Satellite, Antenna, etc.)"
    )

    location: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        doc="ZIP code or location identifier"
    )

    modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last modified timestamp from Schedules Direct"
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Soft delete flag for removed lineups"
    )

    # Relationships
    stations: Mapped[list["Station"]] = relationship(
        "Station",
        back_populates="lineup",
        cascade="all, delete-orphan",
        doc="Stations in this lineup"
    )

    def __repr__(self) -> str:
        """Return string representation with lineup id and name.

        Returns:
            String in format: Lineup(id='USA-CA94105-X', name='Comcast Cable...')
        """
        return f"Lineup(id='{self.id}', name='{self.name}')"
