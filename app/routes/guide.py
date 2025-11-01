"""
Guide page routes.

This module provides the TV program guide interface for browsing
upcoming programs and scheduling recordings.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Schedule, Program, Station

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()


# ============================================================================
# Page Routes
# ============================================================================

@router.get("/guide", response_class=HTMLResponse, tags=["Navigation"])
async def guide_page(
    request: Request,
    db: Session = Depends(get_db),
    hours: int = Query(default=12, ge=1, le=168, description="Number of hours to display")
) -> HTMLResponse:
    """
    Render the TV program guide page.

    This page displays upcoming programs for the specified time range, grouped by
    channel. Users can browse the guide and schedule recordings.

    The page shows:
    - Programs organized by channel (sorted by channel number)
    - Air time, title, and description for each program
    - Duration and status badges (NEW, LIVE)
    - "Record" button for each program
    - Time range selector (3, 6, 12, 24, 48 hours)
    - Search bar to filter programs by title

    Args:
        request: FastAPI Request object for template context
        db: Database session from dependency injection
        hours: Number of hours to display (default: 12, min: 1, max: 168/1 week)

    Returns:
        HTMLResponse: Rendered guide.html template with programs_by_channel data
    """
    from app.main import templates

    try:
        # Get current time and time window based on hours parameter
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours)

        logger.info(f"Fetching guide data from {now} to {end_time} ({hours} hours)")

        # Query schedules with joined program and station data
        schedules = (
            db.query(Schedule)
            .options(
                joinedload(Schedule.program),
                joinedload(Schedule.station)
            )
            .filter(
                and_(
                    Schedule.air_datetime >= now,
                    Schedule.air_datetime < end_time,
                    Schedule.station.has(Station.enabled == True)
                )
            )
            .order_by(Schedule.station_id, Schedule.air_datetime)
            .all()
        )

        logger.info(f"Found {len(schedules)} programs in the next {hours} hours")

        # Group programs by channel
        programs_by_channel = _group_programs_by_channel(schedules)

        return templates.TemplateResponse(
            "guide.html",
            {
                "request": request,
                "programs_by_channel": programs_by_channel,
                "hours": hours,
            }
        )
    except Exception as e:
        logger.error(f"Error loading guide page: {e}", exc_info=True)
        return templates.TemplateResponse(
            "guide.html",
            {
                "request": request,
                "programs_by_channel": [],
                "error": "Failed to load guide data. Please try again later.",
            }
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _group_programs_by_channel(schedules: List[Schedule]) -> List[Dict[str, Any]]:
    """
    Group schedules by channel and format for template display.

    Args:
        schedules: List of Schedule objects with joined program and station data

    Returns:
        List of channel dictionaries, each containing:
        - channel_number: Channel number (e.g., "2.1")
        - channel_name: Station name
        - callsign: Station callsign
        - programs: List of program dictionaries
    """
    channels_dict: Dict[str, Dict[str, Any]] = {}

    for schedule in schedules:
        station = schedule.station
        program = schedule.program

        # Get or create channel entry
        if station.id not in channels_dict:
            channels_dict[station.id] = {
                "channel_number": station.channel_number,
                "channel_name": station.name,
                "callsign": station.callsign,
                "programs": []
            }

        # Calculate duration in minutes
        duration_minutes = schedule.duration_seconds // 60

        # Format datetime as ISO string with Z suffix for UTC
        # Ensure proper UTC timezone indicator for JavaScript Date parsing
        air_datetime_str = schedule.air_datetime.isoformat()
        if not air_datetime_str.endswith('Z') and '+' not in air_datetime_str:
            air_datetime_str += 'Z'

        # Add program to channel
        channels_dict[station.id]["programs"].append({
            "schedule_id": schedule.id,
            "air_datetime_utc": air_datetime_str,  # ISO format with Z for JavaScript
            "duration_minutes": duration_minutes,
            "title": program.title,
            "description": program.description or "No description available.",
            "episode_title": None,  # MVP: No episode data yet
            "season_number": None,
            "episode_number": None,
            "is_new": False,  # MVP: No flags yet
            "is_live": False,
            "original_air_date": None,
            "genres": [],  # MVP: No genre data yet
        })

    # Convert to list and sort by channel number
    channels_list = list(channels_dict.values())

    # Sort channels by channel number (handle subchannels like "2.1")
    def _channel_sort_key(channel: Dict[str, Any]) -> tuple:
        """Extract major and minor channel numbers for sorting."""
        try:
            parts = channel["channel_number"].split(".")
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            return (major, minor)
        except (ValueError, IndexError):
            # If parsing fails, sort to end
            return (999999, 999999)

    channels_list.sort(key=_channel_sort_key)

    return channels_list
