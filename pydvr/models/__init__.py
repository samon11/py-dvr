"""SQLAlchemy models for PyDVR.

This package contains all database models following the Single Responsibility
Principle, with each model in its own module for better maintainability.

Models:
    - Base: Abstract base class with common functionality
    - Lineup: Schedules Direct lineup (collection of stations)
    - Station: Broadcast television channel
    - Program: TV show/movie metadata
    - Schedule: Specific airing of a program on a station
    - Recording: Scheduled or completed recording
    - RecordingStatus: Enum for recording states
    - SyncStatus: Guide data synchronization tracking

The models follow these principles:
    - SOLID design principles for clean, maintainable code
    - Strong typing with Python 3.13+ type hints
    - Timezone-aware UTC datetimes for consistency
    - Proper foreign key relationships with cascade deletes
    - Indexes for query performance
    - Comprehensive docstrings
"""

from pydvr.models.base import Base
from pydvr.models.lineup import Lineup
from pydvr.models.program import Program
from pydvr.models.recording import Recording, RecordingStatus
from pydvr.models.schedule import Schedule
from pydvr.models.station import Station
from pydvr.models.sync_status import SyncStatus

__all__ = [
    "Base",
    "Lineup",
    "Station",
    "Program",
    "Schedule",
    "Recording",
    "RecordingStatus",
    "SyncStatus",
]
