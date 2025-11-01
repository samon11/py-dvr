"""Guide data synchronization service.

This module provides the GuideDataSync service for syncing TV guide data
from Schedules Direct to the local database. It handles lineups, stations,
schedules, and program metadata with MD5-based change detection.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

from sqlalchemy.dialects.sqlite import insert

from app.services.schedules_direct import SchedulesDirectClient
from app.models.lineup import Lineup
from app.models.station import Station
from app.models.schedule import Schedule
from app.models.program import Program
from app.models.sync_status import SyncStatus

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GuideDataSync:
    """Service for syncing Schedules Direct data to database.

    This service orchestrates the complete guide data synchronization process,
    including lineups, stations, schedules, and program metadata. It uses
    MD5-based change detection to minimize API calls and database writes.

    Attributes:
        db: SQLAlchemy database session
        client: SchedulesDirectClient instance for API calls
    """

    def __init__(self, db: "Session"):
        """Initialize GuideDataSync with database session.

        Args:
            db: SQLAlchemy Session instance
        """
        self.db = db
        self.client = SchedulesDirectClient()

    async def sync_guide_data(self, days: int = 3) -> SyncStatus:
        """Main sync method - syncs lineups, stations, schedules, programs.

        This is the primary entry point for guide data synchronization. It:
        1. Creates a SyncStatus record to track progress
        2. Syncs lineups from Schedules Direct
        3. Syncs stations for all lineups
        4. Syncs schedules for the next N days (with MD5 change detection)
        5. Syncs program metadata for all new/changed programs
        6. Updates SyncStatus with results

        Args:
            days: Number of days of guide data to sync (default: 3)

        Returns:
            SyncStatus record with sync results and statistics

        Raises:
            Exception: Any error during sync (captured in SyncStatus.error_message)
        """
        # 1. Create sync status record
        sync_status = SyncStatus(status="running")
        self.db.add(sync_status)
        self.db.commit()

        try:
            logger.info(f"Starting guide data sync for {days} days (sync_id={sync_status.id})")

            # 2. Sync lineups
            logger.info("Syncing lineups...")
            lineups_count = await self._sync_lineups()
            sync_status.lineups_updated = lineups_count
            self.db.commit()
            logger.info(f"Synced {lineups_count} lineups")

            # 3. Get all station IDs from active lineups
            stations = self.db.query(Station).filter(Station.enabled == True).all()
            station_ids = [s.id for s in stations]
            logger.info(f"Found {len(station_ids)} enabled stations")

            if not station_ids:
                logger.warning("No enabled stations found, skipping schedule/program sync")
                sync_status.status = "completed"
                sync_status.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                return sync_status

            # 4. Generate date list (YYYY-MM-DD format)
            dates = [
                (datetime.now(timezone.utc) + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(days)
            ]
            logger.info(f"Syncing schedules for dates: {dates}")

            # 5. Sync schedules (with MD5 change detection)
            logger.info("Syncing schedules...")
            schedules_count, program_ids = await self._sync_schedules(
                station_ids,
                dates
            )
            sync_status.schedules_updated = schedules_count
            self.db.commit()
            logger.info(f"Synced {schedules_count} schedules, found {len(program_ids)} unique programs")

            # 6. Sync programs
            if program_ids:
                logger.info("Syncing program metadata...")
                programs_count = await self._sync_programs(list(program_ids))
                sync_status.programs_updated = programs_count
                self.db.commit()
                logger.info(f"Synced {programs_count} programs")
            else:
                logger.info("No programs to sync")

            # 7. Mark complete
            sync_status.status = "completed"
            sync_status.completed_at = datetime.now(timezone.utc)
            logger.info(f"Guide data sync completed successfully (sync_id={sync_status.id})")

        except Exception as e:
            logger.error(f"Guide data sync failed: {e}", exc_info=True)
            sync_status.status = "failed"
            sync_status.error_message = str(e)
            sync_status.completed_at = datetime.now(timezone.utc)
            raise

        finally:
            self.db.commit()

        return sync_status

    async def _sync_lineups(self) -> int:
        """Sync lineups from Schedules Direct to database.

        Fetches the user's lineups from Schedules Direct and upserts them
        to the database. Also syncs stations for each lineup.

        Returns:
            Number of lineups synced
        """
        # Fetch lineups from Schedules Direct
        lineups = await self.client.get_lineups()

        count = 0
        for lineup_data in lineups:
            # Upsert lineup
            # Note: UserLineup doesn't have 'modified' field, use current time
            stmt = insert(Lineup).values(
                id=lineup_data.lineup,
                name=lineup_data.name,
                transport=lineup_data.transport,
                location=lineup_data.location,
                modified=datetime.now(timezone.utc)
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["lineup_id"],
                set_={
                    "name": lineup_data.name,
                    "transport": lineup_data.transport,
                    "location": lineup_data.location,
                    "modified": datetime.now(timezone.utc),
                    "is_deleted": False
                }
            )
            self.db.execute(stmt)
            count += 1

            # Sync stations for this lineup
            stations_count = await self._sync_stations(lineup_data.lineup)
            logger.debug(f"Synced {stations_count} stations for lineup {lineup_data.lineup}")

        self.db.commit()
        return count

    async def _sync_stations(self, lineup_id: str) -> int:
        """Sync stations for a lineup.

        Fetches stations from Schedules Direct for the given lineup
        and upserts them to the database.

        Args:
            lineup_id: Schedules Direct lineup ID

        Returns:
            Number of stations synced
        """
        # Fetch stations from Schedules Direct
        lineup_response = await self.client.get_lineup_stations(lineup_id)

        # Build a mapping of stationID -> channel from the map array
        station_channel_map = {
            entry.stationID: entry.channel
            for entry in lineup_response.map
        }

        count = 0
        for station_data in lineup_response.stations:
            # Get channel number from the map
            channel_number = station_channel_map.get(station_data.stationID, "0")

            # Upsert station
            stmt = insert(Station).values(
                id=station_data.stationID,
                lineup_id=lineup_id,
                callsign=station_data.callsign,
                channel_number=channel_number,
                name=station_data.name,
                affiliate=station_data.affiliate,
                logo_url=station_data.logo.URL if station_data.logo else None
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["station_id"],
                set_={
                    "lineup_id": lineup_id,
                    "callsign": station_data.callsign,
                    "channel_number": channel_number,
                    "name": station_data.name,
                    "affiliate": station_data.affiliate,
                    "logo_url": station_data.logo.URL if station_data.logo else None
                }
            )
            self.db.execute(stmt)
            count += 1

        self.db.commit()
        return count

    async def _sync_schedules(
        self,
        station_ids: list[str],
        dates: list[str]
    ) -> tuple[int, set[str]]:
        """Sync schedules, return (count, program_ids).

        Uses MD5-based change detection to only fetch schedules that have
        changed since the last sync. This significantly reduces API calls
        and database writes.

        Args:
            station_ids: List of Schedules Direct station IDs
            dates: List of dates in YYYY-MM-DD format

        Returns:
            Tuple of (schedules_count, program_ids_set)
        """
        # Get MD5 hashes from Schedules Direct
        logger.debug(f"Fetching MD5 hashes for {len(station_ids)} stations")
        md5_response = await self.client.get_schedule_md5s(station_ids)

        # Get existing schedules from database
        date_start = datetime.strptime(dates[0], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        date_end = datetime.strptime(dates[-1], "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)

        existing_schedules = self.db.query(Schedule).filter(
            Schedule.station_id.in_(station_ids),
            Schedule.air_datetime >= date_start,
            Schedule.air_datetime < date_end
        ).all()

        # Build map of existing MD5 hashes
        existing_md5s = {
            (s.station_id, s.air_datetime.strftime("%Y-%m-%d")): s.md5_hash
            for s in existing_schedules
        }

        # Determine which stations need updating
        # MD5 response is a dict: {stationID: {date: ScheduleMD5Entry}}
        stations_to_fetch = []
        for station_id in station_ids:
            for date in dates:
                # Get MD5 from Schedules Direct response
                if station_id not in md5_response.root:
                    continue

                date_md5_data = md5_response.root[station_id].get(date)
                if not date_md5_data:
                    continue

                sd_md5 = date_md5_data.md5
                db_md5 = existing_md5s.get((station_id, date))

                # Fetch if MD5 doesn't match or schedule doesn't exist
                if sd_md5 != db_md5:
                    stations_to_fetch.append({"stationID": station_id, "date": date})

        logger.info(f"MD5 change detection: {len(stations_to_fetch)} station-dates need updating")

        # Fetch only changed schedules
        if not stations_to_fetch:
            return 0, set()

        # Fetch schedules from Schedules Direct (in batches if needed)
        # The API supports up to 5000 station-date combinations
        program_ids = set()
        count = 0

        # Process in batches of 5000
        batch_size = 5000
        for i in range(0, len(stations_to_fetch), batch_size):
            batch = stations_to_fetch[i:i + batch_size]
            logger.debug(f"Fetching schedules batch {i//batch_size + 1} ({len(batch)} station-dates)")

            # Build request format: [{"stationID": "12345", "date": ["2025-01-01"]}]
            # Group by station ID
            station_date_map = {}
            for item in batch:
                station_id = item["stationID"]
                date = item["date"]
                if station_id not in station_date_map:
                    station_date_map[station_id] = []
                station_date_map[station_id].append(date)

            request_data = [
                {"stationID": sid, "date": dates_list}
                for sid, dates_list in station_date_map.items()
            ]

            schedules_response = await self.client.get_schedules(request_data)

            # Upsert schedules to database
            for schedule_data in schedules_response.root:
                for program in schedule_data.programs:
                    # airDateTime is already a datetime object from Pydantic parsing
                    air_dt = program.airDateTime

                    # Create schedule ID using ISO format string
                    schedule_id = f"{schedule_data.stationID}_{program.airDateTime.isoformat()}"

                    stmt = insert(Schedule).values(
                        id=schedule_id,
                        station_id=schedule_data.stationID,
                        program_id=program.programID,
                        air_datetime=air_dt,
                        duration_seconds=program.duration,
                        md5_hash=program.md5
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["schedule_id"],
                        set_={
                            "program_id": program.programID,
                            "duration_seconds": program.duration,
                            "md5_hash": program.md5
                        }
                    )
                    self.db.execute(stmt)
                    program_ids.add(program.programID)
                    count += 1

        self.db.commit()
        return count, program_ids

    async def _sync_programs(self, program_ids: list[str]) -> int:
        """Sync program metadata (batch 5000 at a time).

        Fetches program metadata from Schedules Direct and upserts to
        the database. Processes in batches of 5000 (API limit).

        Args:
            program_ids: List of Schedules Direct program IDs

        Returns:
            Number of programs synced
        """
        count = 0
        batch_size = 5000

        # Process in batches of 5000
        for i in range(0, len(program_ids), batch_size):
            batch = program_ids[i:i + batch_size]
            logger.debug(f"Fetching programs batch {i//batch_size + 1} ({len(batch)} programs)")

            programs_response = await self.client.get_programs(batch)

            # Upsert programs to database
            for program_data in programs_response.root:
                # Build description from ProgramDescriptions object
                description = None
                if program_data.descriptions:
                    # Use the longest description (typically description1000)
                    descriptions = program_data.descriptions.description1000
                    if not descriptions:
                        descriptions = program_data.descriptions.description100
                    if descriptions and len(descriptions) > 0:
                        description = descriptions[0].description

                # Extract episode metadata from Gracenote or TVmaze metadata
                season = None
                episode = None
                episode_title = program_data.episodeTitle150

                if program_data.metadata:
                    # metadata is a list of dicts, each dict has provider-specific keys
                    # Try Gracenote first, fall back to TVmaze
                    for metadata_dict in program_data.metadata:
                        # The dict has keys like "Gracenote" or "TVmaze"
                        if "Gracenote" in metadata_dict and metadata_dict["Gracenote"]:
                            gracenote_data = metadata_dict["Gracenote"]
                            if hasattr(gracenote_data, "season") and gracenote_data.season:
                                season = gracenote_data.season
                            if hasattr(gracenote_data, "episode") and gracenote_data.episode:
                                episode = gracenote_data.episode
                            break
                        elif "TVmaze" in metadata_dict and metadata_dict["TVmaze"]:
                            tvmaze_data = metadata_dict["TVmaze"]
                            if hasattr(tvmaze_data, "season") and tvmaze_data.season:
                                season = tvmaze_data.season
                            if hasattr(tvmaze_data, "episode") and tvmaze_data.episode:
                                episode = tvmaze_data.episode
                            break

                stmt = insert(Program).values(
                    id=program_data.programID,
                    title=program_data.titles[0].title120 if program_data.titles else "Unknown",
                    description=description,
                    duration_seconds=program_data.duration or 3600,  # Default 1 hour if not provided
                    season=season,
                    episode=episode,
                    episode_title=episode_title
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["program_id"],
                    set_={
                        "title": program_data.titles[0].title120 if program_data.titles else "Unknown",
                        "description": description,
                        "duration_seconds": program_data.duration or 3600,
                        "season": season,
                        "episode": episode,
                        "episode_title": episode_title
                    }
                )
                self.db.execute(stmt)
                count += 1

        self.db.commit()
        return count
