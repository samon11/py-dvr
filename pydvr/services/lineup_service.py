"""Lineup management service.

This module provides the LineupService for managing user lineups,
including searching for available headends, adding lineups to the account,
and removing lineups with database cleanup.
"""

import logging

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from pydvr.models.lineup import Lineup
from pydvr.models.station import Station
from pydvr.schemas.schedules_direct import (
    AddLineupResponse,
    DeleteLineupResponse,
    Headend,
)
from pydvr.services.schedules_direct import SchedulesDirectClient

logger = logging.getLogger(__name__)


class LineupService:
    """Service for managing Schedules Direct lineups.

    This service handles lineup management operations including searching
    for available lineups, adding them to the user's account, syncing
    lineup data to the database, and removing lineups.

    Attributes:
        db: SQLAlchemy database session
        client: SchedulesDirectClient instance for API calls
    """

    def __init__(self, db: Session):
        """Initialize LineupService with database session.

        Args:
            db: SQLAlchemy Session instance
        """
        self.db = db
        self.client = SchedulesDirectClient()

    async def get_user_lineups(self, include_deleted: bool = False) -> list[Lineup]:
        """Get lineups from the database.

        Args:
            include_deleted: If True, include soft-deleted lineups

        Returns:
            List of Lineup entities from database
        """
        query = self.db.query(Lineup)
        if not include_deleted:
            query = query.filter(Lineup.is_deleted == False)
        return query.all()

    async def search_headends(self, country: str, postal_code: str) -> list[Headend]:
        """Search for available headends/lineups by location.

        Args:
            country: Country code (e.g., "USA")
            postal_code: Postal/ZIP code

        Returns:
            List of available headends with their lineups

        Raises:
            SDError: If Schedules Direct API returns an error
        """
        logger.info(f"Searching headends for {country} {postal_code}")
        headends = await self.client.get_headends(country, postal_code)
        logger.info(f"Found {len(headends)} headends")
        return headends

    async def add_lineup(self, lineup_id: str) -> AddLineupResponse:
        """Add a lineup to user's account and sync stations to database.

        This method:
        1. Adds the lineup to the user's Schedules Direct account
        2. Fetches the lineup's stations from the API
        3. Syncs the lineup and stations to the database

        Args:
            lineup_id: Lineup ID to add (e.g., "USA-CA94105-X")

        Returns:
            AddLineupResponse from Schedules Direct API

        Raises:
            SDError: If Schedules Direct API returns an error
        """
        logger.info(f"Adding lineup {lineup_id}")

        # Add lineup via API
        response = await self.client.add_lineup(lineup_id)
        logger.info(f"Added lineup {lineup_id}: {response.message}")

        # Sync the lineup to database
        await self._sync_single_lineup(lineup_id)

        return response

    async def delete_lineup(self, lineup_id: str) -> DeleteLineupResponse:
        """Delete a lineup from user's account and remove from database.

        This method:
        1. Deletes the lineup from the user's Schedules Direct account
        2. Hard-deletes the lineup from the database (cascade to stations/schedules/recordings)

        Args:
            lineup_id: Lineup ID to delete (e.g., "USA-CA94105-X")

        Returns:
            DeleteLineupResponse from Schedules Direct API

        Raises:
            SDError: If Schedules Direct API returns an error
            ValueError: If lineup not found in database
        """
        logger.info(f"Deleting lineup {lineup_id}")

        # Verify lineup exists in database
        lineup = self.db.query(Lineup).filter(Lineup.id == lineup_id).first()
        if not lineup:
            raise ValueError(f"Lineup {lineup_id} not found in database")

        # Delete lineup via API
        response = await self.client.delete_lineup(lineup_id)
        logger.info(f"Deleted lineup {lineup_id} from SD: {response.message}")

        # Hard delete from database (cascade will handle stations/schedules/recordings)
        self.db.delete(lineup)
        self.db.commit()
        logger.info(f"Deleted lineup {lineup_id} from database")

        return response

    async def _sync_single_lineup(self, lineup_id: str) -> None:
        """Sync a single lineup and its stations to the database.

        Args:
            lineup_id: Lineup ID to sync
        """
        logger.info(f"Syncing lineup {lineup_id}")

        # Get lineup details from API
        lineup_data = await self.client.get_lineup_stations(lineup_id)

        # Upsert lineup
        lineup_values = {
            "lineup_id": lineup_id,
            "name": lineup_data.metadata.lineup,
            "transport": lineup_data.metadata.transport,
            "location": None,  # Not provided in LineupStationsResponse
            "modified": lineup_data.metadata.modified,
            "is_deleted": False,
        }

        stmt = insert(Lineup).values(**lineup_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["lineup_id"],
            set_={
                "name": stmt.excluded.name,
                "transport": stmt.excluded.transport,
                "modified": stmt.excluded.modified,
                "is_deleted": stmt.excluded.is_deleted,
            }
        )
        self.db.execute(stmt)
        self.db.commit()
        logger.info(f"Synced lineup {lineup_id}")

        # Sync stations
        stations_added = 0
        for map_entry in lineup_data.map:
            # Find matching station in stations list
            station = next(
                (s for s in lineup_data.stations if s.stationID == map_entry.stationID),
                None
            )

            if not station:
                logger.warning(f"Station {map_entry.stationID} in map but not in stations list")
                continue

            # Get logo URL (prefer first logo in list)
            logo_url = None
            if station.stationLogo and len(station.stationLogo) > 0:
                logo_url = station.stationLogo[0].URL

            # Upsert station
            station_values = {
                "station_id": station.stationID,
                "lineup_id": lineup_id,
                "callsign": station.callsign,
                "channel_number": map_entry.channel,
                "name": station.name,
                "affiliate": station.affiliate,
                "logo_url": logo_url,
                "enabled": True,
            }

            stmt = insert(Station).values(**station_values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["station_id"],
                set_={
                    "lineup_id": stmt.excluded.lineup_id,
                    "callsign": stmt.excluded.callsign,
                    "channel_number": stmt.excluded.channel_number,
                    "name": stmt.excluded.name,
                    "affiliate": stmt.excluded.affiliate,
                    "logo_url": stmt.excluded.logo_url,
                }
            )
            self.db.execute(stmt)
            stations_added += 1

        self.db.commit()
        logger.info(f"Synced {stations_added} stations for lineup {lineup_id}")
