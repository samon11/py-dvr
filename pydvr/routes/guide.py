"""
Guide page routes.

This module provides the TV program guide interface for browsing
upcoming programs and scheduling recordings.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from pydvr.database import get_db
from pydvr.models import Recording, Schedule, Station
from pydvr.models.recording import RecordingStatus

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
    station_id: str = Query(default=None, description="Station ID to display"),
    date: str = Query(default=None, description="Date to display (YYYY-MM-DD)"),
    tz_offset: int = Query(default=0, description="Timezone offset in minutes from UTC")
) -> HTMLResponse:
    """
    Render the TV program guide page.

    This page displays upcoming programs for a specific channel and date.
    Users can select a channel from a dropdown and pick a date to view programs.

    The page shows:
    - Channel selector dropdown (with affiliate name and channel number)
    - Date picker for selecting which day to view
    - Programs for the selected channel and date
    - Air time, title, and description for each program
    - Duration and status badges (NEW, LIVE)
    - "Record" button for each program

    Args:
        request: FastAPI Request object for template context
        db: Database session from dependency injection
        station_id: Station ID to display programs for
        date: Date to display programs for (YYYY-MM-DD format)

    Returns:
        HTMLResponse: Rendered guide.html template with programs and stations list
    """
    from pydvr.main import templates

    try:
        # Get today's date for the date picker
        today = datetime.utcnow().date().isoformat()

        # Get all enabled stations for the dropdown
        stations = (
            db.query(Station)
            .filter(Station.enabled == True)
            .order_by(Station.channel_number)
            .all()
        )

        # Format stations for dropdown
        stations_list = _format_stations_for_dropdown(stations)

        # If no station or date selected, show empty state with selection UI
        if not station_id or not date:
            return templates.TemplateResponse(
                "guide.html",
                {
                    "request": request,
                    "stations": stations_list,
                    "selected_station_id": station_id,
                    "selected_date": date,
                    "today_date": today,
                    "programs": [],
                }
            )

        # Parse the date
        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid date format: {date}")
            return templates.TemplateResponse(
                "guide.html",
                {
                    "request": request,
                    "stations": stations_list,
                    "selected_station_id": station_id,
                    "selected_date": None,
                    "today_date": today,
                    "programs": [],
                    "error": "Invalid date format. Please use YYYY-MM-DD.",
                }
            )

        # Calculate start and end times for the selected date in UTC
        # The date comes from the user's browser as a local date (e.g., "2025-11-06")
        # tz_offset is in minutes from UTC
        # JavaScript's getTimezoneOffset() returns:
        #   - Positive values for west of UTC (e.g., 480 for PST/UTC-8, 300 for EST/UTC-5)
        #   - Negative values for east of UTC (e.g., -60 for CET/UTC+1, -540 for JST/UTC+9)

        # We want to show programs that START during the selected calendar day in the user's local timezone
        # Formula: UTC time = Local time + offset (because offset represents how far behind UTC we are)

        # Example: User in PST (UTC-8) selects Nov 6
        # - tz_offset = 480 minutes (8 hours)
        # - Local: Nov 6 00:00 to Nov 7 00:00
        # - UTC: Nov 6 08:00 to Nov 7 08:00

        # Create the local date range (midnight to midnight)
        local_start = selected_date.replace(hour=0, minute=0, second=0, microsecond=0)
        local_end = local_start + timedelta(days=1)

        # Convert to UTC
        start_time_utc = local_start + timedelta(minutes=tz_offset)
        end_time_utc = local_end + timedelta(minutes=tz_offset)

        logger.info(f"Fetching guide data for station {station_id} on {date}")

        # Get current time in UTC to filter out past programs
        current_time_utc = datetime.utcnow()

        # Query schedules for the selected station and date
        # Only show programs that haven't ended yet
        # We'll filter in Python after the query since SQLite doesn't support datetime arithmetic easily
        all_schedules = (
            db.query(Schedule)
            .options(
                joinedload(Schedule.program),
                joinedload(Schedule.station)
            )
            .filter(
                and_(
                    Schedule.station_id == station_id,
                    Schedule.air_datetime >= start_time_utc,
                    Schedule.air_datetime < end_time_utc
                )
            )
            .order_by(Schedule.air_datetime)
            .all()
        )

        # Filter out programs that have already ended
        # A program has ended if: air_datetime + duration_seconds < current_time
        schedules = [
            schedule for schedule in all_schedules
            if schedule.air_datetime + timedelta(seconds=schedule.duration_seconds) >= current_time_utc
        ]

        logger.info(f"Found {len(schedules)} programs for station {station_id} on {date}")

        # Get all scheduled/in-progress recordings for these schedules to check status
        schedule_ids = [s.id for s in schedules]
        active_recordings = (
            db.query(Recording.schedule_id)
            .filter(
                and_(
                    Recording.schedule_id.in_(schedule_ids),
                    Recording.status.in_([RecordingStatus.SCHEDULED, RecordingStatus.IN_PROGRESS])
                )
            )
            .all()
        )
        scheduled_schedule_ids = {r.schedule_id for r in active_recordings}

        # Format programs for display
        programs = _format_programs_for_display(schedules, scheduled_schedule_ids)

        return templates.TemplateResponse(
            "guide.html",
            {
                "request": request,
                "stations": stations_list,
                "selected_station_id": station_id,
                "selected_date": date,
                "today_date": today,
                "programs": programs,
            }
        )
    except Exception as e:
        logger.error(f"Error loading guide page: {e}", exc_info=True)
        return templates.TemplateResponse(
            "guide.html",
            {
                "request": request,
                "stations": stations_list if 'stations_list' in locals() else [],
                "selected_station_id": station_id,
                "selected_date": date,
                "today_date": today if 'today' in locals() else datetime.utcnow().date().isoformat(),
                "programs": [],
                "error": "Failed to load guide data. Please try again later.",
            }
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _format_stations_for_dropdown(stations: list[Station]) -> list[dict[str, Any]]:
    """
    Format stations for dropdown display.

    Args:
        stations: List of Station objects

    Returns:
        List of station dictionaries with formatted display text
    """
    stations_list = []

    for station in stations:
        # Format display text: "Channel 2.1 - NBC (KNTV)"
        display_parts = [f"Channel {station.channel_number}"]

        if station.affiliate:
            display_parts.append(station.affiliate)

        if station.callsign:
            display_parts.append(f"({station.callsign})")

        display_text = " - ".join(display_parts)

        stations_list.append({
            "id": station.id,
            "channel_number": station.channel_number,
            "name": station.name,
            "callsign": station.callsign,
            "affiliate": station.affiliate,
            "display_text": display_text
        })

    return stations_list


def _format_programs_for_display(schedules: list[Schedule], scheduled_schedule_ids: set = None) -> list[dict[str, Any]]:
    """
    Format schedules for template display.

    Args:
        schedules: List of Schedule objects with joined program and station data
        scheduled_schedule_ids: Set of schedule IDs that already have active recordings

    Returns:
        List of program dictionaries for display
    """
    programs = []
    if scheduled_schedule_ids is None:
        scheduled_schedule_ids = set()

    for schedule in schedules:
        program = schedule.program

        # Calculate duration in minutes
        duration_minutes = schedule.duration_seconds // 60

        # Format datetime as ISO string with Z suffix for UTC
        # Ensure proper UTC timezone indicator for JavaScript Date parsing
        air_datetime_str = schedule.air_datetime.isoformat()
        if not air_datetime_str.endswith('Z') and '+' not in air_datetime_str:
            air_datetime_str += 'Z'

        # Check if this program is already scheduled for recording
        is_scheduled = schedule.id in scheduled_schedule_ids

        # Add program to list
        programs.append({
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
            "is_scheduled": is_scheduled,
        })

    return programs
