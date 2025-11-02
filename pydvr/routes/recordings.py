"""
Recordings page routes and API endpoints.

This module provides routes for viewing and managing scheduled and completed
recordings, including scheduling new recordings from the guide.
"""

import logging
from datetime import UTC

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from pydvr.config import get_settings
from pydvr.database import get_db
from pydvr.models import Recording, RecordingStatus, Schedule

logger = logging.getLogger(__name__)
settings = get_settings()

# Create router instance
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateRecordingRequest(BaseModel):
    """Request model for creating a new recording.

    Attributes:
        schedule_id: The schedule ID to record
        padding_start_seconds: Optional seconds to start early (overrides default)
        padding_end_seconds: Optional seconds to end late (overrides default)
    """

    schedule_id: str = Field(..., description="Schedule ID from the guide to record")
    padding_start_seconds: int | None = Field(
        default=None,
        ge=0,
        le=1800,  # Max 30 minutes
        description="Seconds to start recording before scheduled time",
    )
    padding_end_seconds: int | None = Field(
        default=None,
        ge=0,
        le=3600,  # Max 60 minutes
        description="Seconds to continue recording after scheduled end time",
    )


class RecordingResponse(BaseModel):
    """Response model for a recording.

    Attributes:
        recording_id: Unique recording identifier
        schedule_id: Associated schedule ID
        status: Current recording status
        padding_start_seconds: Seconds to start early
        padding_end_seconds: Seconds to end late
    """

    recording_id: int
    schedule_id: str
    status: str
    padding_start_seconds: int
    padding_end_seconds: int

    class Config:
        from_attributes = True


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/api/recordings",
    response_model=RecordingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Recordings"],
)
async def create_recording(
    request: CreateRecordingRequest, db: Session = Depends(get_db)
) -> RecordingResponse:
    """
    Schedule a new recording.

    Creates a new recording entry in the database with status='scheduled'.
    The recording scheduler will automatically pick it up and execute it
    at the scheduled time.

    Args:
        request: Recording creation request with schedule_id and optional padding
        db: Database session from dependency injection

    Returns:
        RecordingResponse: The created recording details

    Raises:
        HTTPException 404: If schedule_id does not exist
        HTTPException 409: If recording already exists for this schedule
        HTTPException 400: If schedule is in the past or invalid

    Example:
        POST /api/recordings
        {
            "schedule_id": "EP012345670123",
            "padding_start_seconds": 120,
            "padding_end_seconds": 180
        }
    """
    logger.info(f"Creating recording for schedule_id: {request.schedule_id}")

    # Verify schedule exists
    schedule = db.query(Schedule).filter(Schedule.id == request.schedule_id).first()
    if not schedule:
        logger.warning(f"Schedule not found: {request.schedule_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with ID '{request.schedule_id}' not found",
        )

    # Check if recording already exists for this schedule
    existing_recording = (
        db.query(Recording)
        .filter(Recording.schedule_id == request.schedule_id)
        .filter(Recording.status.in_([RecordingStatus.SCHEDULED, RecordingStatus.IN_PROGRESS]))
        .first()
    )

    if existing_recording:
        logger.warning(f"Recording already exists for schedule: {request.schedule_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Recording already scheduled for this program (ID: {existing_recording.id})",
        )

    # Validate schedule is not in the past
    from datetime import datetime

    now = datetime.now(UTC).replace(tzinfo=None)  # Remove timezone for comparison with DB datetime
    if schedule.air_datetime < now:
        logger.warning(f"Schedule is in the past: {request.schedule_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule recording for past program",
        )

    # Create recording with defaults or provided padding values
    recording = Recording(
        schedule_id=request.schedule_id,
        status=RecordingStatus.SCHEDULED,
        padding_start_seconds=request.padding_start_seconds
        if request.padding_start_seconds is not None
        else settings.default_padding_start,
        padding_end_seconds=request.padding_end_seconds
        if request.padding_end_seconds is not None
        else settings.default_padding_end,
    )

    try:
        db.add(recording)
        db.commit()
        db.refresh(recording)

        logger.info(
            f"Recording created successfully: ID={recording.id}, "
            f"schedule={request.schedule_id}, "
            f"padding_start={recording.padding_start_seconds}s, "
            f"padding_end={recording.padding_end_seconds}s"
        )

        return RecordingResponse(
            recording_id=recording.id,
            schedule_id=recording.schedule_id,
            status=recording.status.value,
            padding_start_seconds=recording.padding_start_seconds,
            padding_end_seconds=recording.padding_end_seconds,
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create recording: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create recording. Please try again.",
        )


@router.delete(
    "/api/recordings/{recording_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Recordings"]
)
async def cancel_recording(recording_id: int, db: Session = Depends(get_db)) -> None:
    """
    Cancel a scheduled recording.

    Only recordings with status='scheduled' can be cancelled.
    In-progress or completed recordings cannot be cancelled.

    Args:
        recording_id: The ID of the recording to cancel
        db: Database session from dependency injection

    Raises:
        HTTPException 404: If recording does not exist
        HTTPException 409: If recording cannot be cancelled (wrong status)

    Example:
        DELETE /api/recordings/123
    """
    logger.info(f"Cancelling recording: {recording_id}")

    # Find the recording
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        logger.warning(f"Recording not found: {recording_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID {recording_id} not found",
        )

    # Check if recording can be cancelled
    if not recording.can_cancel():
        logger.warning(f"Cannot cancel recording {recording_id}: status={recording.status.value}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel recording with status '{recording.status.value}'. "
            "Only scheduled recordings can be cancelled.",
        )

    try:
        # Mark as cancelled
        recording.mark_cancelled()
        db.commit()

        logger.info(f"Recording {recording_id} cancelled successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cancel recording {recording_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel recording. Please try again.",
        )


@router.delete(
    "/api/recordings/{recording_id}/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Recordings"],
)
async def delete_recording(recording_id: int, db: Session = Depends(get_db)) -> None:
    """
    Delete a completed recording.

    Deletes both the database entry and the video file from disk.
    Only recordings with status='completed' or 'failed' can be deleted.

    Args:
        recording_id: The ID of the recording to delete
        db: Database session from dependency injection

    Raises:
        HTTPException 404: If recording does not exist
        HTTPException 409: If recording cannot be deleted (wrong status)

    Example:
        DELETE /api/recordings/123/delete
    """
    import os
    from pathlib import Path

    logger.info(f"Deleting recording: {recording_id}")

    # Find the recording
    recording = db.query(Recording).filter(Recording.id == recording_id).first()
    if not recording:
        logger.warning(f"Recording not found: {recording_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recording with ID {recording_id} not found",
        )

    # Check if recording can be deleted (only completed or failed recordings)
    if recording.status not in (
        RecordingStatus.COMPLETED,
        RecordingStatus.FAILED,
        RecordingStatus.CANCELLED,
    ):
        logger.warning(f"Cannot delete recording {recording_id}: status={recording.status.value}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete recording with status '{recording.status.value}'. "
            "Only completed, failed, or cancelled recordings can be deleted.",
        )

    try:
        # Delete the file if it exists
        if recording.file_path:
            file_path = Path(recording.file_path)
            if file_path.exists():
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
                except OSError as e:
                    logger.error(f"Failed to delete file {file_path}: {e}", exc_info=True)
                    # Continue with database deletion even if file deletion fails
            else:
                logger.warning(f"File not found, skipping deletion: {file_path}")

        # Delete the database entry
        db.delete(recording)
        db.commit()

        logger.info(f"Recording {recording_id} deleted successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete recording {recording_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete recording. Please try again.",
        )


# ============================================================================
# Page Routes
# ============================================================================


@router.get("/scheduled", response_class=HTMLResponse, tags=["Navigation"])
async def scheduled_recordings_page(
    request: Request, db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Render the scheduled recordings page.

    Displays all upcoming recordings with status='scheduled' or 'in_progress',
    sorted by air time. Users can view recording details and cancel scheduled
    recordings.

    Args:
        request: FastAPI Request object for template context
        db: Database session from dependency injection

    Returns:
        HTMLResponse: Rendered scheduled.html template with recordings list
    """
    from pydvr.main import templates

    try:
        # Query scheduled and in-progress recordings with joined schedule/program/station data
        recordings = (
            db.query(Recording)
            .options(
                joinedload(Recording.schedule).joinedload(Schedule.program),
                joinedload(Recording.schedule).joinedload(Schedule.station),
            )
            .filter(Recording.status.in_([RecordingStatus.SCHEDULED, RecordingStatus.IN_PROGRESS]))
            .join(Schedule)
            .order_by(Schedule.air_datetime)
            .all()
        )

        logger.info(f"Found {len(recordings)} scheduled/in-progress recordings")

        # Format recordings for template
        recordings_data = []
        for recording in recordings:
            schedule = recording.schedule
            program = schedule.program
            station = schedule.station

            # Format datetime as ISO string with Z suffix for UTC
            air_datetime_str = schedule.air_datetime.isoformat()
            if not air_datetime_str.endswith("Z") and "+" not in air_datetime_str:
                air_datetime_str += "Z"

            # Calculate total duration with padding
            total_duration_seconds = (
                recording.padding_start_seconds
                + schedule.duration_seconds
                + recording.padding_end_seconds
            )
            total_duration_minutes = total_duration_seconds // 60

            recordings_data.append(
                {
                    "recording_id": recording.id,
                    "schedule_id": schedule.id,
                    "program_title": program.title,
                    "channel_number": station.channel_number,
                    "channel_name": station.name,
                    "air_datetime_utc": air_datetime_str,
                    "duration_minutes": schedule.duration_seconds // 60,
                    "total_duration_minutes": total_duration_minutes,
                    "padding_start_seconds": recording.padding_start_seconds,
                    "padding_end_seconds": recording.padding_end_seconds,
                    "status": recording.status.value,
                    "can_cancel": recording.can_cancel(),
                }
            )

        return templates.TemplateResponse(
            "scheduled.html",
            {
                "request": request,
                "recordings": recordings_data,
            },
        )
    except Exception as e:
        logger.error(f"Error loading scheduled recordings page: {e}", exc_info=True)
        return templates.TemplateResponse(
            "scheduled.html",
            {
                "request": request,
                "recordings": [],
                "error": "Failed to load scheduled recordings. Please try again later.",
            },
        )


@router.get("/recordings", response_class=HTMLResponse, tags=["Navigation"])
async def recordings_library_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """
    Render the recordings library page.

    Displays all completed recordings sorted by air date (most recent first).
    Users can view recording details, file paths, file sizes, and delete recordings.

    Args:
        request: FastAPI Request object for template context
        db: Database session from dependency injection

    Returns:
        HTMLResponse: Rendered recordings.html template with completed recordings list
    """
    import shutil
    from pathlib import Path

    from pydvr.main import templates

    try:
        # Query completed recordings with joined schedule/program/station data
        recordings = (
            db.query(Recording)
            .options(
                joinedload(Recording.schedule).joinedload(Schedule.program),
                joinedload(Recording.schedule).joinedload(Schedule.station),
            )
            .filter(Recording.status == RecordingStatus.COMPLETED)
            .join(Schedule)
            .order_by(Schedule.air_datetime.desc())
            .all()
        )

        logger.info(f"Found {len(recordings)} completed recordings")

        # Format file size for display helper function
        def format_file_size(size_bytes: int) -> str:
            """Format bytes to human readable size."""
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

        # Format recordings for template
        recordings_data = []
        total_size_bytes = 0

        for recording in recordings:
            schedule = recording.schedule
            program = schedule.program
            station = schedule.station

            # Format datetime as ISO string with Z suffix for UTC
            air_datetime_str = schedule.air_datetime.isoformat()
            if not air_datetime_str.endswith("Z") and "+" not in air_datetime_str:
                air_datetime_str += "Z"

            # Get file size if file exists
            file_size_bytes = 0
            file_exists = False
            if recording.file_path:
                file_path = Path(recording.file_path)
                if file_path.exists():
                    file_exists = True
                    file_size_bytes = file_path.stat().st_size
                    total_size_bytes += file_size_bytes

            recordings_data.append(
                {
                    "recording_id": recording.id,
                    "schedule_id": schedule.id,
                    "program_title": program.title,
                    "channel_number": station.channel_number,
                    "channel_name": station.name,
                    "air_datetime_utc": air_datetime_str,
                    "duration_minutes": schedule.duration_seconds // 60,
                    "file_path": recording.file_path,
                    "file_exists": file_exists,
                    "file_size_bytes": file_size_bytes,
                    "file_size_formatted": format_file_size(file_size_bytes),
                    "actual_start_time": recording.actual_start_time.isoformat() + "Z"
                    if recording.actual_start_time
                    else None,
                    "actual_end_time": recording.actual_end_time.isoformat() + "Z"
                    if recording.actual_end_time
                    else None,
                }
            )

        # Calculate storage stats
        recording_path = Path(settings.recording_path)
        storage_stats = {
            "total_recordings_size": format_file_size(total_size_bytes)
            if recordings_data
            else "0 B",
            "recordings_count": len(recordings_data),
        }

        # Get disk space info if recording path exists
        if recording_path.exists():
            disk_usage = shutil.disk_usage(recording_path)
            storage_stats["free_space"] = format_file_size(disk_usage.free)
            storage_stats["total_space"] = format_file_size(disk_usage.total)
            storage_stats["used_space"] = format_file_size(disk_usage.used)
            storage_stats["percent_free"] = round((disk_usage.free / disk_usage.total) * 100, 1)
        else:
            storage_stats["free_space"] = "Unknown"
            storage_stats["total_space"] = "Unknown"
            storage_stats["used_space"] = "Unknown"
            storage_stats["percent_free"] = 0

        return templates.TemplateResponse(
            "recordings.html",
            {
                "request": request,
                "recordings": recordings_data,
                "storage_stats": storage_stats,
            },
        )
    except Exception as e:
        logger.error(f"Error loading recordings library page: {e}", exc_info=True)
        return templates.TemplateResponse(
            "recordings.html",
            {
                "request": request,
                "recordings": [],
                "storage_stats": {"total_recordings_size": "0 B", "recordings_count": 0},
                "error": "Failed to load recordings library. Please try again later.",
            },
        )
