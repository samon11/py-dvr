"""Schedule model representing a specific airing of a program.

A Schedule represents a program broadcast on a specific station at a
specific date/time. It forms the many-to-many relationship between
Programs and Stations.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.program import Program
    from app.models.recording import Recording
    from app.models.station import Station


class Schedule(Base):
    """Represents a specific airing of a program on a station.

    Schedules connect Programs to Stations with timing information,
    forming the TV guide data. Each schedule represents one broadcast
    occurrence.

    Attributes:
        schedule_id: Composite ID from Schedules Direct
        program_id: Foreign key to programs table
        station_id: Foreign key to stations table
        air_datetime: When the program airs (UTC timezone-aware)
        duration_seconds: Duration of this specific airing
        program: Relationship to Program entity
        station: Relationship to Station entity
        recordings: Relationship to Recording entities for this airing

    MVP Simplifications:
        - No is_new, is_live, is_premiere, is_finale flags (post-MVP)
        - No audio_properties, video_properties (post-MVP)
        - No part_number, part_total for multi-part episodes (post-MVP)
        - No md5_hash for change detection (post-MVP)

    Indexes:
        - Primary key on schedule_id
        - program_id for reverse lookup
        - station_id for channel guide queries
        - air_datetime for time-based queries
        - Composite (station_id, air_datetime) for efficient guide display

    Validation:
        - air_datetime must be timezone-aware UTC
        - duration_seconds must be positive
        - program_id and station_id must reference valid entities
    """

    __tablename__ = "schedules"

    # Override id to use string schedule_id from Schedules Direct
    id: Mapped[str] = mapped_column(
        "schedule_id",
        String(64),
        primary_key=True,
        doc="Composite ID: {station_id}_{air_datetime}_{program_id}"
    )

    # Foreign keys
    program_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("programs.program_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to programs table"
    )

    station_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to stations table"
    )

    # Timing information
    air_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When program airs (UTC)"
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Duration of this airing in seconds"
    )

    # Relationships
    program: Mapped["Program"] = relationship(
        "Program",
        back_populates="schedules",
        doc="The program being broadcast"
    )

    station: Mapped["Station"] = relationship(
        "Station",
        back_populates="schedules",
        doc="The station broadcasting the program"
    )

    recordings: Mapped[list["Recording"]] = relationship(
        "Recording",
        back_populates="schedule",
        cascade="all, delete-orphan",
        doc="Recordings scheduled for this airing"
    )

    # Indexes
    __table_args__ = (
        Index("ix_schedule_station_time", "station_id", "air_datetime"),
    )

    def __repr__(self) -> str:
        """Return string representation with schedule details.

        Returns:
            String in format: Schedule(id='...', station='2.1', time='2025-10-31 20:00')
        """
        time_str = self.air_datetime.strftime('%Y-%m-%d %H:%M') if self.air_datetime else 'N/A'
        return f"Schedule(id='{self.id[:20]}...', station='{self.station_id}', time='{time_str}')"

    @property
    def end_datetime(self) -> datetime:
        """Calculate the end time of this airing.

        Returns:
            End datetime (air_datetime + duration_seconds)
        """
        from datetime import timedelta
        return self.air_datetime + timedelta(seconds=self.duration_seconds)
