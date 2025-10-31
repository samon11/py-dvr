"""SQLAlchemy models for PyHDHRDVR.

This package contains all database models following the Single Responsibility
Principle, with each model in its own module for better maintainability.

Models:
    - Base: Abstract base class with common functionality
    - Station: Broadcast television channel
    - Program: TV show/movie metadata
    - Schedule: Specific airing of a program on a station
    - Recording: Scheduled or completed recording
    - RecordingStatus: Enum for recording states

The models follow these principles:
    - SOLID design principles for clean, maintainable code
    - Strong typing with Python 3.13+ type hints
    - Timezone-aware UTC datetimes for consistency
    - Proper foreign key relationships with cascade deletes
    - Indexes for query performance
    - Comprehensive docstrings
"""

from app.models.base import Base
from app.models.program import Program
from app.models.recording import Recording, RecordingStatus
from app.models.schedule import Schedule
from app.models.station import Station

__all__ = [
    "Base",
    "Station",
    "Program",
    "Schedule",
    "Recording",
    "RecordingStatus",
]
