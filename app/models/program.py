"""Program model representing a TV program (show, movie, episode metadata).

Programs contain the metadata for television shows and movies, sourced from
Schedules Direct. Each program can have multiple airings (schedules).
"""

from typing import TYPE_CHECKING

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.schedule import Schedule


class Program(Base):
    """Represents a TV program with metadata.

    Programs contain the descriptive information about television shows,
    movies, and episodes. The same program can air multiple times on
    different stations (many-to-many through Schedule).

    Attributes:
        program_id: Schedules Direct program ID (primary key)
        title: Program title (e.g., "NOVA", "The Shawshank Redemption")
        description: Full description/synopsis of the program
        duration_seconds: Standard duration in seconds
        season: Season number for episodic content (nullable)
        episode: Episode number within season (nullable)
        episode_title: Episode-specific title (nullable)
        schedules: Relationship to Schedule entries for airings of this program

    MVP Simplifications:
        - No series_id (post-MVP, for linking episodes to series)
        - No genres, cast_crew, artwork (post-MVP)
        - No original_air_date, content_rating (post-MVP)
        - No is_movie, is_sports flags (post-MVP)

    Indexes:
        - Primary key on program_id
        - title for search queries

    Validation:
        - duration_seconds must be positive
        - title is required
    """

    __tablename__ = "programs"

    # Override id to use string program_id from Schedules Direct
    id: Mapped[str] = mapped_column(
        "program_id",
        String(32),
        primary_key=True,
        doc="Schedules Direct program ID"
    )

    # Core program metadata
    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        index=True,
        doc="Program title"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Full description/synopsis"
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Standard program duration in seconds"
    )

    # Episode metadata (for series episodes)
    season: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Season number for episodic content"
    )

    episode: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Episode number within season"
    )

    episode_title: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        doc="Episode-specific title (e.g., 'Pilot', 'The One with the Jellyfish')"
    )

    # Relationships
    schedules: Mapped[list["Schedule"]] = relationship(
        "Schedule",
        back_populates="program",
        cascade="all, delete-orphan",
        doc="Scheduled airings of this program"
    )

    # Indexes
    __table_args__ = (
        Index("ix_program_title", "title"),
    )

    def __repr__(self) -> str:
        """Return string representation with program id and title.

        Returns:
            String in format: Program(id='EP012345', title='NOVA')
        """
        return f"Program(id='{self.id}', title='{self.title}')"

    def __str__(self) -> str:
        """Return human-readable string with title.

        Returns:
            The program title
        """
        return self.title
