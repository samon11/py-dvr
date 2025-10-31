"""Recording model representing a scheduled or completed recording.

Recordings track the lifecycle of capturing a TV program to disk, from
scheduling through execution to completion or failure.
"""

import enum
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.schedule import Schedule


class RecordingStatus(enum.Enum):
    """Valid states for a recording.

    State Transitions:
        scheduled → in_progress → completed
                                → failed
        scheduled → cancelled

    Attributes:
        SCHEDULED: Recording is scheduled, not yet started
        IN_PROGRESS: Recording is currently active
        COMPLETED: Recording finished successfully
        FAILED: Recording failed due to error
        CANCELLED: User cancelled before start
    """

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value


class Recording(Base):
    """Represents a scheduled or completed recording.

    Recordings link to Schedule entries and track the entire recording
    lifecycle including status, file location, timing, and error information.

    Attributes:
        recording_id: Auto-incrementing integer primary key
        schedule_id: Foreign key to schedules table
        status: Current recording state (see RecordingStatus enum)
        padding_start_seconds: Seconds to start early
        padding_end_seconds: Seconds to end late
        file_path: Absolute path to recorded .ts file
        actual_start_time: When recording actually started (UTC)
        actual_end_time: When recording actually ended (UTC)
        error_message: Error description if failed
        schedule: Relationship to Schedule entity

    MVP Simplifications:
        - No series_rule_id (series recording post-MVP)
        - No tuner_used tracking (simplified MVP)
        - No file_size_bytes (can be computed from filesystem)
        - No quality_metrics (post-MVP)

    Indexes:
        - Primary key on recording_id (auto-increment)
        - schedule_id for reverse lookup
        - status for filtering by state
        - Composite (status, schedule_id) for upcoming recordings query

    Validation:
        - status must be valid RecordingStatus enum value
        - padding_start_seconds >= 0 and <= 1800 (30 minutes)
        - padding_end_seconds >= 0 and <= 3600 (60 minutes)
        - file_path must be within recording storage directory when set
        - actual_start_time and actual_end_time must be UTC
    """

    __tablename__ = "recordings"

    # Primary key - auto-incrementing integer
    id: Mapped[int] = mapped_column(
        "recording_id",
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique recording identifier"
    )

    # Foreign key
    schedule_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("schedules.schedule_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to schedules table"
    )

    # Recording state
    status: Mapped[RecordingStatus] = mapped_column(
        Enum(RecordingStatus),
        nullable=False,
        index=True,
        default=RecordingStatus.SCHEDULED,
        doc="Current recording status"
    )

    # Padding configuration
    padding_start_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        doc="Seconds to start recording early"
    )

    padding_end_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=120,
        doc="Seconds to continue recording late"
    )

    # File information
    file_path: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
        doc="Absolute path to recorded .ts file"
    )

    # Execution timing
    actual_start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When recording actually started (UTC)"
    )

    actual_end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When recording actually ended (UTC)"
    )

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error description if recording failed"
    )

    # Relationships
    schedule: Mapped["Schedule"] = relationship(
        "Schedule",
        back_populates="recordings",
        doc="The scheduled airing being recorded"
    )

    # Indexes
    __table_args__ = (
        Index("ix_recording_status_schedule", "status", "schedule_id"),
    )

    def __repr__(self) -> str:
        """Return string representation with recording details.

        Returns:
            String in format: Recording(id=123, status='scheduled', schedule='...')
        """
        return f"Recording(id={self.id}, status='{self.status.value}', schedule='{self.schedule_id[:20]}...')"

    @property
    def file_path_obj(self) -> Path | None:
        """Get file_path as pathlib.Path object.

        Returns:
            Path object if file_path is set, None otherwise
        """
        return Path(self.file_path) if self.file_path else None

    @file_path_obj.setter
    def file_path_obj(self, path: Path | None) -> None:
        """Set file_path from pathlib.Path object.

        Args:
            path: Path object to set, or None to clear
        """
        self.file_path = str(path.absolute()) if path else None

    @property
    def is_scheduled(self) -> bool:
        """Check if recording is in scheduled state."""
        return self.status == RecordingStatus.SCHEDULED

    @property
    def is_in_progress(self) -> bool:
        """Check if recording is currently in progress."""
        return self.status == RecordingStatus.IN_PROGRESS

    @property
    def is_completed(self) -> bool:
        """Check if recording completed successfully."""
        return self.status == RecordingStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if recording failed."""
        return self.status == RecordingStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        """Check if recording was cancelled."""
        return self.status == RecordingStatus.CANCELLED

    def can_cancel(self) -> bool:
        """Check if recording can be cancelled.

        Returns:
            True if recording is in scheduled state, False otherwise
        """
        return self.status == RecordingStatus.SCHEDULED

    def mark_in_progress(self, start_time: datetime) -> None:
        """Mark recording as in progress.

        Args:
            start_time: UTC datetime when recording started

        Raises:
            ValueError: If recording is not in scheduled state
        """
        if not self.is_scheduled:
            raise ValueError(f"Cannot start recording in {self.status.value} state")

        self.status = RecordingStatus.IN_PROGRESS
        self.actual_start_time = start_time

    def mark_completed(self, end_time: datetime, file_path: Path) -> None:
        """Mark recording as completed.

        Args:
            end_time: UTC datetime when recording ended
            file_path: Path to the recorded file

        Raises:
            ValueError: If recording is not in progress
        """
        if not self.is_in_progress:
            raise ValueError(f"Cannot complete recording in {self.status.value} state")

        self.status = RecordingStatus.COMPLETED
        self.actual_end_time = end_time
        self.file_path_obj = file_path

    def mark_failed(self, error: str, end_time: datetime | None = None) -> None:
        """Mark recording as failed.

        Args:
            error: Error message describing the failure
            end_time: Optional UTC datetime when failure occurred

        Raises:
            ValueError: If recording is not in scheduled or in_progress state
        """
        if self.status not in (RecordingStatus.SCHEDULED, RecordingStatus.IN_PROGRESS):
            raise ValueError(f"Cannot fail recording in {self.status.value} state")

        self.status = RecordingStatus.FAILED
        self.error_message = error
        if end_time:
            self.actual_end_time = end_time

    def mark_cancelled(self) -> None:
        """Mark recording as cancelled.

        Raises:
            ValueError: If recording is not in scheduled state
        """
        if not self.is_scheduled:
            raise ValueError(f"Cannot cancel recording in {self.status.value} state")

        self.status = RecordingStatus.CANCELLED
