"""SyncStatus model for tracking guide data synchronization progress.

Tracks the status of guide data sync operations, including counters for
updated entities and error messages if sync fails.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from pydvr.models.base import Base


class SyncStatus(Base):
    """Represents a guide data synchronization operation.

    Each sync operation creates a record tracking progress, success/failure,
    and statistics about what data was updated.

    Attributes:
        sync_id: Primary key (auto-increment)
        started_at: When sync operation started (UTC)
        completed_at: When sync operation completed (UTC, null if still running)
        status: Current status ('running', 'completed', 'failed')
        lineups_updated: Count of lineups added or updated
        stations_updated: Count of stations added or updated
        schedules_updated: Count of schedules added or updated
        programs_updated: Count of programs added or updated
        error_message: Error details if sync failed

    Indexes:
        - Primary key on sync_id
        - started_at for chronological queries

    Validation:
        - status must be one of: 'running', 'completed', 'failed'
        - Counter fields must be non-negative
    """

    __tablename__ = "sync_status"

    # Override the default id field from Base
    id: Mapped[int] = mapped_column(
        "sync_id", Integer, primary_key=True, autoincrement=True, doc="Sync operation ID"
    )

    # Timing information
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
        doc="When sync started (UTC)",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="When sync completed (UTC)"
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, doc="Sync status: 'running', 'completed', 'failed'"
    )

    # Update counters
    lineups_updated: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Number of lineups added or updated"
    )

    stations_updated: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Number of stations added or updated"
    )

    schedules_updated: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Number of schedules added or updated"
    )

    programs_updated: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Number of programs added or updated"
    )

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Error message if sync failed"
    )

    def __repr__(self) -> str:
        """Return string representation with sync id and status.

        Returns:
            String in format: SyncStatus(id=1, status='completed')
        """
        return f"SyncStatus(id={self.id}, status='{self.status}')"

    @property
    def duration_seconds(self) -> float | None:
        """Calculate sync duration in seconds.

        Returns:
            Duration in seconds, or None if sync hasn't completed
        """
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()
