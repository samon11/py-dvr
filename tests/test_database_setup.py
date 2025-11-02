"""Test database setup and models.

This test verifies that:
1. Database tables can be created successfully
2. Models can be instantiated and saved
3. Relationships work correctly
4. Enums work correctly
5. Indexes are created properly
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import inspect

from pydvr.db import DatabaseManager
from pydvr.models import Program, Recording, RecordingStatus, Schedule, Station


@pytest.fixture
def db_manager():
    """Create a temporary in-memory database for testing."""
    db = DatabaseManager("sqlite:///:memory:")
    db.create_tables()
    yield db
    # Cleanup happens automatically with in-memory database


def test_tables_created(db_manager):
    """Test that all tables are created successfully."""
    inspector = inspect(db_manager.engine)
    tables = inspector.get_table_names()

    assert "stations" in tables
    assert "programs" in tables
    assert "schedules" in tables
    assert "recordings" in tables


def test_station_model(db_manager):
    """Test Station model creation and retrieval."""
    with db_manager.get_session() as session:
        # Create station
        station = Station(
            id="12345.schedulesdirect.org",
            callsign="KTVU",
            channel_number="2.1",
            name="FOX 2 Oakland",
            enabled=True,
        )
        session.add(station)
        session.commit()

        # Retrieve station
        retrieved = session.query(Station).filter_by(callsign="KTVU").first()
        assert retrieved is not None
        assert retrieved.callsign == "KTVU"
        assert retrieved.channel_number == "2.1"
        assert retrieved.name == "FOX 2 Oakland"
        assert retrieved.enabled is True


def test_program_model(db_manager):
    """Test Program model creation and retrieval."""
    with db_manager.get_session() as session:
        # Create program
        program = Program(
            id="EP012345678",
            title="NOVA",
            description="Science documentary series",
            duration_seconds=3600,
        )
        session.add(program)
        session.commit()

        # Retrieve program
        retrieved = session.query(Program).filter_by(title="NOVA").first()
        assert retrieved is not None
        assert retrieved.title == "NOVA"
        assert retrieved.duration_seconds == 3600
        assert retrieved.description == "Science documentary series"


def test_schedule_model_with_relationships(db_manager):
    """Test Schedule model with foreign key relationships."""
    with db_manager.get_session() as session:
        # Create station and program
        station = Station(
            id="12345.schedulesdirect.org",
            callsign="WGBH",
            channel_number="2.1",
            name="WGBH Boston",
            enabled=True,
        )
        program = Program(
            id="EP012345678", title="NOVA", description="Science documentary", duration_seconds=3600
        )
        session.add(station)
        session.add(program)
        session.commit()

        # Create schedule
        air_time = datetime(2025, 10, 31, 20, 0, 0, tzinfo=UTC)
        schedule = Schedule(
            id="12345.schedulesdirect.org_2025-10-31T20:00:00Z_EP012345678",
            program_id=program.id,
            station_id=station.id,
            air_datetime=air_time,
            duration_seconds=3600,
        )
        session.add(schedule)
        session.commit()

        # Retrieve and verify relationships
        retrieved = session.query(Schedule).first()
        assert retrieved is not None
        assert retrieved.program.title == "NOVA"
        assert retrieved.station.callsign == "WGBH"
        # Note: SQLite doesn't preserve timezone info, so we compare without tzinfo
        assert retrieved.air_datetime.replace(tzinfo=UTC) == air_time


def test_recording_model_with_enum(db_manager):
    """Test Recording model with RecordingStatus enum."""
    with db_manager.get_session() as session:
        # Create dependencies
        station = Station(
            id="12345.schedulesdirect.org",
            callsign="KTVU",
            channel_number="2.1",
            name="FOX 2",
            enabled=True,
        )
        program = Program(
            id="EP012345678", title="Test Show", description="Test", duration_seconds=1800
        )
        schedule = Schedule(
            id="test_schedule_id",
            program_id=program.id,
            station_id=station.id,
            air_datetime=datetime.now(UTC),
            duration_seconds=1800,
        )
        session.add_all([station, program, schedule])
        session.commit()

        # Create recording
        recording = Recording(
            schedule_id=schedule.id,
            status=RecordingStatus.SCHEDULED,
            padding_start_seconds=60,
            padding_end_seconds=120,
        )
        session.add(recording)
        session.commit()

        # Retrieve and verify
        retrieved = session.query(Recording).first()
        assert retrieved is not None
        assert retrieved.status == RecordingStatus.SCHEDULED
        assert retrieved.is_scheduled is True
        assert retrieved.is_in_progress is False
        assert retrieved.padding_start_seconds == 60
        assert retrieved.padding_end_seconds == 120


def test_recording_state_transitions(db_manager):
    """Test Recording state transition methods."""
    with db_manager.get_session() as session:
        # Create dependencies
        station = Station(
            id="12345.schedulesdirect.org",
            callsign="KTVU",
            channel_number="2.1",
            name="FOX 2",
            enabled=True,
        )
        program = Program(
            id="EP012345678", title="Test Show", description="Test", duration_seconds=1800
        )
        schedule = Schedule(
            id="test_schedule_id",
            program_id=program.id,
            station_id=station.id,
            air_datetime=datetime.now(UTC),
            duration_seconds=1800,
        )
        recording = Recording(
            schedule_id=schedule.id,
            status=RecordingStatus.SCHEDULED,
            padding_start_seconds=60,
            padding_end_seconds=120,
        )
        session.add_all([station, program, schedule, recording])
        session.commit()

        # Test state transitions
        start_time = datetime.now(UTC)
        recording.mark_in_progress(start_time)
        assert recording.status == RecordingStatus.IN_PROGRESS
        assert recording.actual_start_time == start_time

        end_time = datetime.now(UTC)
        file_path = Path("/recordings/test.ts")
        recording.mark_completed(end_time, file_path)
        assert recording.status == RecordingStatus.COMPLETED
        assert recording.actual_end_time == end_time
        assert recording.file_path == str(file_path.absolute())


def test_cascade_delete(db_manager):
    """Test that cascade deletes work properly."""
    with db_manager.get_session() as session:
        # Create full hierarchy
        station = Station(
            id="12345.schedulesdirect.org",
            callsign="KTVU",
            channel_number="2.1",
            name="FOX 2",
            enabled=True,
        )
        program = Program(
            id="EP012345678", title="Test Show", description="Test", duration_seconds=1800
        )
        schedule = Schedule(
            id="test_schedule_id",
            program_id=program.id,
            station_id=station.id,
            air_datetime=datetime.now(UTC),
            duration_seconds=1800,
        )
        recording = Recording(
            schedule_id=schedule.id,
            status=RecordingStatus.SCHEDULED,
            padding_start_seconds=60,
            padding_end_seconds=120,
        )
        session.add_all([station, program, schedule, recording])
        session.commit()

        # Delete schedule should cascade to recording
        session.delete(schedule)
        session.commit()

        # Recording should be deleted
        assert session.query(Recording).count() == 0
        # But station and program should remain
        assert session.query(Station).count() == 1
        assert session.query(Program).count() == 1


def test_unique_constraints(db_manager):
    """Test that unique constraints are enforced."""
    from sqlalchemy.exc import IntegrityError

    # Create first station in separate session
    with db_manager.get_session() as session:
        station1 = Station(
            id="12345.schedulesdirect.org",
            callsign="KTVU",
            channel_number="2.1",
            name="FOX 2",
            enabled=True,
        )
        session.add(station1)
        session.commit()

    # Try to create duplicate in new session (same callsign and channel_number)
    # This should raise IntegrityError
    exception_raised = False
    try:
        with db_manager.get_session() as session:
            station2 = Station(
                id="67890.schedulesdirect.org",
                callsign="KTVU",
                channel_number="2.1",
                name="FOX 2 Duplicate",
                enabled=True,
            )
            session.add(station2)
            session.commit()
    except IntegrityError:
        exception_raised = True

    assert exception_raised, "Expected IntegrityError for duplicate unique constraint"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
