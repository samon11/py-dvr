"""
Lineup management routes.

This module provides both API endpoints and web page routes for managing
Schedules Direct lineups, including searching for available lineups,
adding them to the account, and deleting them.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.lineup_service import LineupService
from app.schemas.schedules_direct import (
    Headend,
    AddLineupResponse,
    DeleteLineupResponse,
)

logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter()


# ============================================================================
# Page Routes
# ============================================================================

@router.get("/lineups", response_class=HTMLResponse, tags=["Navigation"])
async def lineups_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """
    Render the lineups management page.

    This page allows users to:
    - Search for available headends by postal code
    - View their current lineups
    - Add new lineups to their account
    - Delete lineups from their account

    Args:
        request: FastAPI Request object for template context
        db: Database session from dependency injection

    Returns:
        HTMLResponse: Rendered lineups.html template
    """
    from app.main import templates

    service = LineupService(db)
    try:
        # Get current lineups for display
        lineups = await service.get_user_lineups(include_deleted=False)

        return templates.TemplateResponse(
            "lineups.html",
            {
                "request": request,
                "lineups": lineups,
            }
        )
    except Exception as e:
        logger.error(f"Error loading lineups page: {e}", exc_info=True)
        return templates.TemplateResponse(
            "lineups.html",
            {
                "request": request,
                "lineups": [],
                "error": str(e),
            }
        )


# ============================================================================
# API Routes
# ============================================================================

@router.get("/api/lineups", tags=["Lineups"])
async def get_lineups(db: Session = Depends(get_db)) -> JSONResponse:
    """
    Get the user's current lineups.

    Returns a JSON list of all lineups currently in the database
    (excluding soft-deleted lineups).

    Args:
        db: Database session from dependency injection

    Returns:
        JSONResponse: List of lineup objects

    Example Response:
        [
            {
                "id": "USA-CA94105-X",
                "name": "Comcast Cable - San Francisco",
                "transport": "Cable",
                "location": "94105",
                "modified": "2025-10-31T12:00:00Z",
                "is_deleted": false
            }
        ]
    """
    service = LineupService(db)
    try:
        lineups = await service.get_user_lineups(include_deleted=False)

        # Convert to dict for JSON response
        lineups_data = [
            {
                "id": lineup.id,
                "name": lineup.name,
                "transport": lineup.transport,
                "location": lineup.location,
                "modified": lineup.modified.isoformat() if lineup.modified else None,
                "is_deleted": lineup.is_deleted,
            }
            for lineup in lineups
        ]

        return JSONResponse(content={"lineups": lineups_data}, status_code=200)
    except Exception as e:
        logger.error(f"Error fetching lineups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/headends", tags=["Lineups"])
async def search_headends(
    country: str = Query(..., description="Country code (e.g., 'USA')"),
    postal_code: str = Query(..., description="Postal/ZIP code"),
    db: Session = Depends(get_db)
) -> JSONResponse:
    """
    Search for available headends by location.

    Queries Schedules Direct API for available TV providers (headends)
    and their lineups in a specific location.

    Args:
        country: Country code (e.g., "USA")
        postal_code: Postal/ZIP code (e.g., "94105")
        db: Database session from dependency injection

    Returns:
        JSONResponse: List of headends with their available lineups

    Raises:
        HTTPException: If API call fails or invalid parameters

    Example Response:
        {
            "headends": [
                {
                    "headend": "CA00053",
                    "transport": "Cable",
                    "location": "San Francisco, CA",
                    "lineups": [
                        {
                            "name": "Comcast Cable",
                            "lineup": "USA-CA94105-X",
                            "uri": "/20141201/lineups/USA-CA94105-X"
                        }
                    ]
                }
            ]
        }
    """
    service = LineupService(db)
    try:
        headends = await service.search_headends(country, postal_code)

        # Convert Pydantic models to dict for JSON response
        headends_data = [headend.model_dump() for headend in headends]

        return JSONResponse(content={"headends": headends_data}, status_code=200)
    except Exception as e:
        logger.error(f"Error searching headends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/lineups/{lineup_id}", tags=["Lineups"])
async def add_lineup(
    lineup_id: str,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """
    Add a lineup to the user's Schedules Direct account.

    This endpoint:
    1. Adds the lineup to the user's Schedules Direct account via API
    2. Syncs the lineup's stations to the local database

    Args:
        lineup_id: Lineup ID to add (e.g., "USA-CA94105-X")
        db: Database session from dependency injection

    Returns:
        JSONResponse: Success response with message and changes remaining

    Raises:
        HTTPException: If API call fails or lineup already exists

    Example Response:
        {
            "code": 0,
            "response": "OK",
            "message": "Added lineup.",
            "serverID": "AWS-SD-web.1",
            "datetime": "2025-10-31T20:00:00Z",
            "changesRemaining": 254
        }
    """
    service = LineupService(db)
    try:
        response = await service.add_lineup(lineup_id)
        return response
    except Exception as e:
        logger.error(f"Error adding lineup {lineup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/lineups/{lineup_id}", tags=["Lineups"])
async def delete_lineup(
    lineup_id: str,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """
    Delete a lineup from the user's Schedules Direct account.

    This endpoint:
    1. Deletes the lineup from the user's Schedules Direct account via API
    2. Hard-deletes the lineup from the local database
    3. Cascade-deletes all associated stations, schedules, and recordings

    Args:
        lineup_id: Lineup ID to delete (e.g., "USA-CA94105-X")
        db: Database session from dependency injection

    Returns:
        JSONResponse: Success response with message and changes remaining

    Raises:
        HTTPException: If API call fails or lineup not found

    Example Response:
        {
            "code": 0,
            "response": "OK",
            "message": "Deleted lineup.",
            "serverID": "AWS-SD-web.1",
            "datetime": "2025-10-31T20:00:00Z",
            "changesRemaining": 253
        }
    """
    service = LineupService(db)
    try:
        response = await service.delete_lineup(lineup_id)
        return response
    except ValueError as e:
        # Lineup not found in database
        logger.warning(f"Lineup {lineup_id} not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting lineup {lineup_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
