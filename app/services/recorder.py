"""
Recording scheduler service for executing scheduled TV recordings.

This module provides a background scheduler service that monitors the database
for upcoming recordings and executes them at the appropriate time using the
HDHomeRun client.

Design Principles:
- Single Responsibility: Handles only recording scheduling and execution
- Open/Closed: Can be extended with additional recording strategies
- Dependency Inversion: Depends on abstractions (config, models) not implementations
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.recording import Recording, RecordingStatus
from app.models.schedule import Schedule
from app.services.hdhomerun import HDHomeRunClient, HDHomeRunError, TunerNotAvailableError

logger = logging.getLogger(__name__)


class RecordingScheduler:
    """
    Background service that monitors and executes scheduled recordings.

    The scheduler runs continuously in the background, checking the database
    every 10 seconds for recordings that need to be started. When a recording's
    start time approaches, the scheduler claims it and begins the recording process.

    Attributes:
        settings: Application configuration
        check_interval: Seconds between database checks (default: 10)
        lookahead_minutes: How far ahead to look for recordings (default: 5)
        is_running: Whether the scheduler is currently active
    """

    def __init__(
        self,
        check_interval: int = 10,
        lookahead_minutes: int = 5,
    ):
        """
        Initialize the recording scheduler.

        Args:
            check_interval: Seconds between database checks
            lookahead_minutes: Minutes ahead to look for upcoming recordings
        """
        self.settings = get_settings()
        self.check_interval = check_interval
        self.lookahead_minutes = lookahead_minutes
        self.is_running = False
        self._active_recordings: dict[int, asyncio.Task] = {}

        logger.info(
            f"Recording scheduler initialized: "
            f"check_interval={check_interval}s, lookahead={lookahead_minutes}m"
        )

    async def start(self, db_session_factory):
        """
        Start the recording scheduler loop.

        This method runs continuously, checking for upcoming recordings
        and starting them at the appropriate time.

        Args:
            db_session_factory: Callable that returns a database session
        """
        if self.is_running:
            logger.warning("Scheduler already running, ignoring start request")
            return

        self.is_running = True
        logger.info("Recording scheduler started")

        try:
            while self.is_running:
                try:
                    # Create a new database session for this check
                    db = db_session_factory()
                    try:
                        await self._check_and_start_recordings(db)
                    finally:
                        db.close()

                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}", exc_info=True)

                # Wait before next check
                await asyncio.sleep(self.check_interval)

        finally:
            self.is_running = False
            logger.info("Recording scheduler stopped")

    async def stop(self):
        """
        Stop the recording scheduler.

        Waits for any active recordings to complete before stopping.
        """
        logger.info("Stopping recording scheduler...")
        self.is_running = False

        # Wait for active recordings to complete
        if self._active_recordings:
            logger.info(f"Waiting for {len(self._active_recordings)} active recordings to complete")
            await asyncio.gather(*self._active_recordings.values(), return_exceptions=True)

        logger.info("Recording scheduler stopped successfully")

    async def _check_and_start_recordings(self, db: Session):
        """
        Check for upcoming recordings and start them if needed.

        Args:
            db: Database session
        """
        now = datetime.now(timezone.utc)
        lookahead = now + timedelta(minutes=self.lookahead_minutes)

        # Query for scheduled recordings that should start soon
        # Note: We can't subtract timedelta from datetime in SQL, so we fetch all
        # scheduled recordings and filter in Python
        stmt = (
            select(Recording)
            .join(Schedule)
            .where(Recording.status == RecordingStatus.SCHEDULED)
            .where(Schedule.air_datetime <= lookahead)
            .order_by(Schedule.air_datetime)
        )

        recordings = db.execute(stmt).scalars().all()

        if not recordings:
            logger.debug("No upcoming recordings found")
            return

        logger.info(f"Found {len(recordings)} scheduled recording(s)")

        for recording in recordings:
            # Calculate actual start time (air_datetime - padding)
            schedule = recording.schedule
            start_time = schedule.air_datetime - timedelta(seconds=recording.padding_start_seconds)

            # Check if it's time to start this recording
            if start_time <= now:
                # Check if we're already recording this
                if recording.id not in self._active_recordings:
                    logger.info(
                        f"Starting recording {recording.id}: "
                        f"{schedule.program.title} on {schedule.station.channel_number}"
                    )

                    # Start recording in background task
                    task = asyncio.create_task(
                        self._execute_recording(recording.id, db_session_factory=lambda: db)
                    )
                    self._active_recordings[recording.id] = task

                    # Cleanup completed tasks
                    task.add_done_callback(lambda t, rid=recording.id: self._active_recordings.pop(rid, None))
            else:
                time_until = (start_time - now).total_seconds()
                logger.debug(
                    f"Recording {recording.id} starts in {time_until:.0f}s: "
                    f"{schedule.program.title}"
                )

    async def _execute_recording(self, recording_id: int, db_session_factory):
        """
        Execute a recording from start to finish.

        This method handles the complete recording workflow:
        1. Mark recording as in_progress
        2. Calculate recording duration with padding
        3. Generate output filename
        4. Stream from HDHomeRun to file
        5. Mark recording as completed or failed

        Args:
            recording_id: ID of the recording to execute
            db_session_factory: Factory function to create database sessions
        """
        db = db_session_factory()
        start_time = datetime.now(timezone.utc)

        try:
            # Load recording with relationships
            recording = db.get(Recording, recording_id)
            if not recording:
                logger.error(f"Recording {recording_id} not found")
                return

            schedule = recording.schedule
            program = schedule.program
            station = schedule.station

            logger.info(
                f"Executing recording {recording_id}: "
                f"{program.title} on channel {station.channel_number}"
            )

            # Mark recording as in progress
            recording.mark_in_progress(start_time)
            db.commit()

            # Calculate total recording duration (program duration + end padding)
            total_duration = schedule.duration_seconds + recording.padding_end_seconds

            # Generate output file path
            output_path = self._generate_output_path(program, schedule, station)
            logger.info(f"Recording to: {output_path}")

            # Execute the recording
            try:
                result = await self._capture_stream(
                    channel=station.channel_number,
                    output_path=output_path,
                    duration=total_duration,
                )

                # Verify file was created and has content
                if not output_path.exists():
                    raise HDHomeRunError(f"Recording file was not created: {output_path}")

                file_size = output_path.stat().st_size
                if file_size == 0:
                    raise HDHomeRunError("Recording file is empty")

                # Calculate minimum expected size (very conservative: 500 KB/s)
                min_expected_size = total_duration * 500 * 1024  # ~500 KB/s
                if file_size < min_expected_size:
                    logger.warning(
                        f"Recording file size ({file_size:,} bytes) is smaller than "
                        f"expected ({min_expected_size:,} bytes)"
                    )

                # Mark recording as completed
                end_time = datetime.now(timezone.utc)
                recording.mark_completed(end_time, output_path)
                db.commit()

                logger.info(
                    f"Recording {recording_id} completed successfully: "
                    f"{file_size:,} bytes, {result.get('duration', 0):.1f}s"
                )

            except TunerNotAvailableError as e:
                # No tuner available - mark as failed
                error_msg = f"No tuner available: {e}"
                logger.error(f"Recording {recording_id} failed: {error_msg}")

                end_time = datetime.now(timezone.utc)
                recording.mark_failed(error_msg, end_time)
                db.commit()

            except HDHomeRunError as e:
                # Stream error - mark as failed
                error_msg = f"Stream error: {e}"
                logger.error(f"Recording {recording_id} failed: {error_msg}")

                end_time = datetime.now(timezone.utc)
                recording.mark_failed(error_msg, end_time)
                db.commit()

            except Exception as e:
                # Unexpected error - mark as failed
                error_msg = f"Unexpected error: {e}"
                logger.error(
                    f"Recording {recording_id} failed with unexpected error: {error_msg}",
                    exc_info=True
                )

                end_time = datetime.now(timezone.utc)
                recording.mark_failed(error_msg, end_time)
                db.commit()

        except Exception as e:
            logger.error(
                f"Fatal error executing recording {recording_id}: {e}",
                exc_info=True
            )

        finally:
            db.close()

    async def _capture_stream(
        self,
        channel: str,
        output_path: Path,
        duration: int,
    ) -> dict[str, Any]:
        """
        Capture a stream from HDHomeRun to file.

        This is an async wrapper around the synchronous HDHomeRun client.

        Args:
            channel: Channel number (e.g., "2.1")
            output_path: Path to save the recording
            duration: Duration in seconds

        Returns:
            dict with recording metadata

        Raises:
            TunerNotAvailableError: If no tuner is available
            HDHomeRunError: If stream capture fails
        """
        # Run the synchronous stream capture in a thread pool
        loop = asyncio.get_event_loop()

        def sync_capture():
            with HDHomeRunClient(self.settings.hdhomerun_ip) as client:
                return client.stream_channel(
                    channel=channel,
                    output_path=output_path,
                    duration=duration,
                    tuner_id="auto",
                )

        return await loop.run_in_executor(None, sync_capture)

    def _generate_output_path(
        self,
        program,
        schedule: Schedule,
        station,
    ) -> Path:
        """
        Generate output file path for a recording.

        For MVP, we use a simple format:
        {title} ({date}).ts

        Future enhancements could organize by series, season/episode, etc.

        Args:
            program: Program being recorded
            schedule: Schedule information
            station: Station information

        Returns:
            Path to the output file
        """
        # Format date/time for filename
        air_date = schedule.air_datetime.strftime("%Y-%m-%d")
        air_time = schedule.air_datetime.strftime("%H%M")

        # Build filename: Title (YYYY-MM-DD HHMM).ts
        title = self._sanitize_filename(program.title)
        filename = f"{title} ({air_date} {air_time}).ts"

        # Use recording path from settings
        output_dir = self.settings.recording_path
        output_path = output_dir / filename

        # Handle duplicate filenames by appending a counter
        if output_path.exists():
            counter = 1
            while output_path.exists():
                filename = f"{title} ({air_date} {air_time}) ({counter}).ts"
                output_path = output_dir / filename
                counter += 1

        return output_path

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string for use as a filename.

        Removes or replaces characters that are invalid in filenames
        across different operating systems.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for all platforms
        """
        # Replace invalid characters with underscore
        # Invalid chars: / \ : * ? " < > |
        sanitized = re.sub(r'[/\\:*?"<>|]', '_', filename)

        # Remove leading/trailing spaces and periods
        sanitized = sanitized.strip('. ')

        # Limit length to 200 characters (leaving room for date/extension)
        if len(sanitized) > 200:
            sanitized = sanitized[:200].strip()

        # Ensure it's not empty
        if not sanitized:
            sanitized = "recording"

        return sanitized
