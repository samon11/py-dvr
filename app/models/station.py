"""Station model representing a broadcast television channel.

A Station corresponds to a physical broadcast channel available through
the HDHomeRun device, sourced from Schedules Direct lineup data.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.schedule import Schedule


class Station(Base):
    """Represents a broadcast television station/channel.

    Stations are populated from Schedules Direct lineup data and represent
    the channels available for viewing and recording. Each station has a
    unique callsign and channel number combination.

    Attributes:
        station_id: Schedules Direct station ID (primary key)
        callsign: FCC call sign (e.g., "KBCW", "KTVU")
        channel_number: Physical or virtual channel number (e.g., "2.1", "44")
        name: Human-readable station name (e.g., "CW Bay Area", "FOX 2")
        enabled: Whether station is enabled for guide display
        schedules: Relationship to Schedule entries for programs on this station

    Indexes:
        - Primary key on station_id
        - channel_number for guide display ordering
        - enabled for filtering active stations

    Constraints:
        - (callsign, channel_number) must be unique
    """

    __tablename__ = "stations"

    # Override id to use string station_id from Schedules Direct
    id: Mapped[str] = mapped_column(
        "station_id",
        String(32),
        primary_key=True,
        doc="Schedules Direct station ID"
    )

    # Core station identification
    callsign: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="FCC station call sign"
    )

    channel_number: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        index=True,
        doc="Channel number (supports subchannels like '2.1')"
    )

    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Station display name"
    )

    # MVP: Simplified - only enabled flag, no affiliate or logo
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Whether station is enabled for display"
    )

    # Relationships
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule",
        back_populates="station",
        cascade="all, delete-orphan",
        doc="Program schedules for this station"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("callsign", "channel_number", name="uq_station_callsign_channel"),
    )

    def __repr__(self) -> str:
        """Return string representation with callsign and channel.

        Returns:
            String in format: Station(id='12345', callsign='KTVU', channel='2.1')
        """
        return f"Station(id='{self.id}', callsign='{self.callsign}', channel='{self.channel_number}')"
