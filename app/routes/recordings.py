"""
Recordings page routes and API endpoints.

This module provides routes for viewing and managing scheduled and completed
recordings, including scheduling new recordings from the guide.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Recording, RecordingStatus, Schedule

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
    schedule_id: str = Field(
        ...,
        description="Schedule ID from the guide to record"
    )
    padding_start_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        le=1800,  # Max 30 minutes
        description="Seconds to start recording before scheduled time"
    )
    padding_end_seconds: Optional[int] = Field(
        default=None,
        ge=0,
        le=3600,  # Max 60 minutes
        description="Seconds to continue recording after scheduled end time"
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
    tags=["Recordings"]
)
async def create_recording(
    request: CreateRecordingRequest,
    db: Session = Depends(get_db)
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
            detail=f"Schedule with ID '{request.schedule_id}' not found"
        )

    # Check if recording already exists for this schedule
    existing_recording = (
        db.query(Recording)
        .filter(Recording.schedule_id == request.schedule_id)
        .filter(Recording.status.in_([
            RecordingStatus.SCHEDULED,
            RecordingStatus.IN_PROGRESS
        ]))
        .first()
    )

    if existing_recording:
        logger.warning(f"Recording already exists for schedule: {request.schedule_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Recording already scheduled for this program (ID: {existing_recording.id})"
        )

    # Validate schedule is not in the past
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # Remove timezone for comparison with DB datetime
    if schedule.air_datetime < now:
        logger.warning(f"Schedule is in the past: {request.schedule_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot schedule recording for past program"
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
            else settings.default_padding_end
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
            padding_end_seconds=recording.padding_end_seconds
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create recording: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create recording. Please try again."
        )
