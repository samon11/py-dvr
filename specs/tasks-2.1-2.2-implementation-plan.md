# Implementation Plan: Tasks 2.1 & 2.2 - Schedules Direct Integration

## Overview
Implement Schedules Direct API client with authentication, guide data sync service, and scheduled background sync task.

**Design Decisions:**
- **Lineup Storage:** Create full Lineup entity with proper relational model
- **Token Storage:** File-based cache at `~/.pyhdhrdvr/sd_token.json`
- **Sync Trigger:** Scheduled background task using APScheduler (daily at 4 AM)
- **Error Handling:** Database + UI display via SyncStatus table

---

## Phase 1: Database Schema Updates (30 min)

### 1.1 Create Lineup Model
**File:** `app/models/lineup.py`

```python
from sqlalchemy import Column, String, DateTime, Boolean
from app.database import Base

class Lineup(Base):
    __tablename__ = "lineups"

    lineup_id = Column(String, primary_key=True)  # From Schedules Direct
    name = Column(String, nullable=False)
    transport = Column(String)  # Cable, Satellite, Antenna, etc.
    location = Column(String)  # ZIP code or location
    modified = Column(DateTime)  # For change detection
    is_deleted = Column(Boolean, default=False)
```

### 1.2 Update Station Model
**File:** `app/models/station.py`

Add fields:
```python
lineup_id = Column(String, ForeignKey("lineups.lineup_id"), nullable=False)
affiliate = Column(String, nullable=True)  # Network affiliation (NBC, CBS, etc.)
logo_url = Column(String, nullable=True)  # Station logo URL
```

### 1.3 Update Schedule Model
**File:** `app/models/schedule.py`

Add field:
```python
md5_hash = Column(String(32), nullable=True)  # For change detection
```

### 1.4 Create SyncStatus Model
**File:** `app/models/sync_status.py`

```python
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base
from datetime import datetime, timezone

class SyncStatus(Base):
    __tablename__ = "sync_status"

    sync_id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)  # 'running', 'completed', 'failed'

    # Counters
    lineups_updated = Column(Integer, default=0)
    stations_updated = Column(Integer, default=0)
    schedules_updated = Column(Integer, default=0)
    programs_updated = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)
```

### 1.5 Create Alembic Migration
```bash
alembic revision --autogenerate -m "Add Lineup and SyncStatus models, update Station and Schedule"
alembic upgrade head
```

---

## Phase 2: Task 2.1 - Authentication & API Client (2 hours)

### 2.1 Create `app/services/schedules_direct.py`

#### Class Structure

```python
import hashlib
import httpx
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from app.config import get_settings

class SchedulesDirectClient:
    """Client for Schedules Direct JSON API v20141201"""

    BASE_URL = "https://json.schedulesdirect.org/20141201"

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=600.0)  # 10-minute timeout
        self._token: str | None = None
        self._token_expires: int | None = None

    # Token Management
    async def _get_cached_token(self) -> tuple[str, int] | None:
        """Load token from file cache if valid"""
        pass

    async def _save_token(self, token: str, expires: int) -> None:
        """Save token to file cache"""
        pass

    async def authenticate(self) -> str:
        """Authenticate and return token (POST /token)"""
        pass

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token, refresh if needed"""
        pass

    # Base Request Method
    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Base method with token header, error handling, retry logic"""
        pass

    # API Endpoints
    async def get_lineups(self) -> list[dict]:
        """GET /lineups - Get user's lineups"""
        pass

    async def get_lineup_stations(self, lineup_id: str) -> dict:
        """GET /lineups/{lineup_id} - Get stations in lineup"""
        pass

    async def get_schedule_md5s(
        self,
        station_ids: list[str],
        dates: list[str]
    ) -> dict:
        """POST /schedules/md5 - Check for schedule changes"""
        pass

    async def get_schedules(
        self,
        station_ids: list[str],
        dates: list[str] | None = None
    ) -> list[dict]:
        """POST /schedules - Get schedules (batch, max 5000 stations)"""
        pass

    async def get_programs(self, program_ids: list[str]) -> list[dict]:
        """POST /programs - Get program metadata (batch, max 5000)"""
        pass

    # Error Handling
    def _handle_error_response(self, response: dict) -> None:
        """Map SD error codes to exceptions"""
        pass
```

#### Key Implementation Details

**Authentication Flow:**
```python
async def authenticate(self) -> str:
    # Check cache first
    cached = await self._get_cached_token()
    if cached and cached[1] > datetime.now(timezone.utc).timestamp():
        self._token, self._token_expires = cached
        return self._token

    # Hash password with SHA1
    password_hash = hashlib.sha1(
        self.settings.sd_password.encode()
    ).hexdigest()

    # Request token
    response = await self.client.post(
        f"{self.BASE_URL}/token",
        json={
            "username": self.settings.sd_username,
            "password": password_hash
        },
        headers={"Content-Type": "application/json"}
    )
    data = response.json()

    if data.get("code") != 0:
        self._handle_error_response(data)

    # Cache token
    self._token = data["token"]
    self._token_expires = data["tokenExpires"]
    await self._save_token(self._token, self._token_expires)

    return self._token
```

**Error Code Mapping:**
```python
ERROR_CODES = {
    3000: "SERVICE_OFFLINE",
    4001: "ACCOUNT_EXPIRED",
    4005: "ACCOUNT_ACCESS_DISABLED",
    4006: "TOKEN_EXPIRED",
    4009: "TOO_MANY_LOGINS",
    6000: "INVALID_PROGRAM_ID",
    6001: "PROGRAM_QUEUED",
    7020: "SCHEDULE_RANGE_EXCEEDED",
    7100: "SCHEDULE_QUEUED"
}
```

**File Cache Location:**
```python
cache_path = Path.home() / ".pyhdhrdvr" / "sd_token.json"
cache_path.parent.mkdir(parents=True, exist_ok=True)
```

---

## Phase 3: Task 2.2 - Guide Data Sync (3 hours)

### 3.1 Create `GuideDataSync` class

Add to `app/services/schedules_direct.py`:

```python
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from app.models.lineup import Lineup
from app.models.station import Station
from app.models.schedule import Schedule
from app.models.program import Program
from app.models.sync_status import SyncStatus

class GuideDataSync:
    """Service for syncing Schedules Direct data to database"""

    def __init__(self, db: Session):
        self.db = db
        self.client = SchedulesDirectClient()

    async def sync_guide_data(self, days: int = 3) -> SyncStatus:
        """Main sync method - syncs lineups, stations, schedules, programs"""
        pass

    async def _sync_lineups(self) -> int:
        """Sync lineups from SD to database"""
        pass

    async def _sync_stations(self, lineup_id: str) -> int:
        """Sync stations for a lineup"""
        pass

    async def _sync_schedules(
        self,
        station_ids: list[str],
        dates: list[str]
    ) -> tuple[int, set[str]]:
        """Sync schedules, return (count, program_ids)"""
        pass

    async def _sync_programs(self, program_ids: list[str]) -> int:
        """Sync program metadata (batch 5000 at a time)"""
        pass
```

#### Main Sync Flow

```python
async def sync_guide_data(self, days: int = 3) -> SyncStatus:
    # 1. Create sync status record
    sync_status = SyncStatus(status="running")
    self.db.add(sync_status)
    self.db.commit()

    try:
        # 2. Sync lineups
        lineups_count = await self._sync_lineups()
        sync_status.lineups_updated = lineups_count

        # 3. Get all station IDs from active lineups
        stations = self.db.query(Station).filter(Station.enabled == True).all()
        station_ids = [s.station_id for s in stations]

        # 4. Generate date list
        dates = [
            (datetime.now(timezone.utc) + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(days)
        ]

        # 5. Sync schedules (with MD5 change detection)
        schedules_count, program_ids = await self._sync_schedules(
            station_ids,
            dates
        )
        sync_status.schedules_updated = schedules_count

        # 6. Sync programs
        programs_count = await self._sync_programs(list(program_ids))
        sync_status.programs_updated = programs_count

        # 7. Mark complete
        sync_status.status = "completed"
        sync_status.completed_at = datetime.now(timezone.utc)

    except Exception as e:
        sync_status.status = "failed"
        sync_status.error_message = str(e)
        sync_status.completed_at = datetime.now(timezone.utc)
        raise

    finally:
        self.db.commit()

    return sync_status
```

#### MD5-Based Change Detection

```python
async def _sync_schedules(
    self,
    station_ids: list[str],
    dates: list[str]
) -> tuple[int, set[str]]:
    # Get MD5 hashes from SD
    md5_data = await self.client.get_schedule_md5s(station_ids, dates)

    # Get existing MD5s from DB
    existing_schedules = self.db.query(Schedule).filter(
        Schedule.station_id.in_(station_ids),
        Schedule.air_datetime >= datetime.now(timezone.utc),
        Schedule.air_datetime < datetime.now(timezone.utc) + timedelta(days=len(dates))
    ).all()

    existing_md5s = {
        (s.station_id, s.air_datetime.date()): s.md5_hash
        for s in existing_schedules
    }

    # Determine which schedules need updating
    stations_to_fetch = []
    for station_id in station_ids:
        for date in dates:
            sd_md5 = md5_data.get(station_id, {}).get(date, {}).get("md5")
            db_md5 = existing_md5s.get((station_id, date))

            if sd_md5 != db_md5:
                stations_to_fetch.append({"stationID": station_id, "date": [date]})

    # Fetch only changed schedules
    if not stations_to_fetch:
        return 0, set()

    schedules = await self.client.get_schedules(stations_to_fetch)

    # Upsert to database
    program_ids = set()
    count = 0

    for schedule_data in schedules:
        for program in schedule_data["programs"]:
            stmt = insert(Schedule).values(
                schedule_id=f"{schedule_data['stationID']}_{program['airDateTime']}",
                station_id=schedule_data["stationID"],
                program_id=program["programID"],
                air_datetime=datetime.fromisoformat(program["airDateTime"]),
                duration_seconds=program["duration"],
                md5_hash=program.get("md5")
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["schedule_id"],
                set_={
                    "program_id": program["programID"],
                    "duration_seconds": program["duration"],
                    "md5_hash": program.get("md5")
                }
            )
            self.db.execute(stmt)
            program_ids.add(program["programID"])
            count += 1

    self.db.commit()
    return count, program_ids
```

---

## Phase 4: Background Scheduler Integration (1 hour)

### 4.1 Update `app/main.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.schedules_direct import GuideDataSync
from app.database import get_db

# Global scheduler
scheduler = AsyncIOScheduler()

async def sync_guide_data_job():
    """Background job for daily guide data sync"""
    db = next(get_db())
    try:
        sync = GuideDataSync(db)
        result = await sync.sync_guide_data(days=3)
        print(f"Guide sync completed: {result.schedules_updated} schedules, "
              f"{result.programs_updated} programs")
    except Exception as e:
        print(f"Guide sync failed: {e}")
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Start background scheduler on app startup"""
    # Daily sync at 4 AM
    scheduler.add_job(
        sync_guide_data_job,
        trigger="cron",
        hour=4,
        minute=0,
        id="daily_guide_sync"
    )
    scheduler.start()
    print("Background scheduler started - daily guide sync at 4 AM")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of scheduler"""
    scheduler.shutdown()
```

### 4.2 Add CLI Command for Manual Trigger

**File:** `app/cli.py`

```python
import click
import asyncio
from app.database import get_db
from app.services.schedules_direct import GuideDataSync

@click.group()
def cli():
    """PyHDHRDVR CLI"""
    pass

@cli.command()
@click.option("--days", default=3, help="Number of days to sync (default: 3)")
def sync_guide(days: int):
    """Manually trigger guide data sync"""
    click.echo(f"Starting guide data sync for {days} days...")

    db = next(get_db())
    try:
        sync = GuideDataSync(db)
        result = asyncio.run(sync.sync_guide_data(days=days))

        click.echo(f"Sync completed successfully!")
        click.echo(f"  Lineups: {result.lineups_updated}")
        click.echo(f"  Stations: {result.stations_updated}")
        click.echo(f"  Schedules: {result.schedules_updated}")
        click.echo(f"  Programs: {result.programs_updated}")

    except Exception as e:
        click.echo(f"Sync failed: {e}", err=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cli()
```

**Usage:**
```bash
python -m app.cli sync-guide
python -m app.cli sync-guide --days 7
```

---

## Phase 5: Configuration & Dependencies (15 min)

### 5.1 Update `app/config.py`

Add field:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    token_cache_path: str = str(Path.home() / ".pyhdhrdvr" / "sd_token.json")
```

### 5.2 Update `pyproject.toml`

Add dependencies if not present:
```toml
dependencies = [
    # ... existing ...
    "apscheduler>=3.10.4",
    "click>=8.1.7"
]
```

Install:
```bash
pip install -e .
```

---

## Phase 6: Testing (1 hour)

### 6.1 Unit Tests

**File:** `tests/test_schedules_direct.py`

```python
import pytest
import hashlib
from app.services.schedules_direct import SchedulesDirectClient

def test_password_hashing():
    """Test SHA1 password hashing"""
    password = "test123"
    expected = hashlib.sha1(password.encode()).hexdigest()
    assert len(expected) == 40
    assert expected.islower()

@pytest.mark.asyncio
async def test_token_caching(tmp_path):
    """Test token save/load"""
    # Mock token cache
    pass

def test_error_code_mapping():
    """Test SD error code handling"""
    pass

def test_batch_splitting():
    """Test splitting program_ids into batches of 5000"""
    program_ids = [f"PR{i:08d}" for i in range(12000)]
    batches = [
        program_ids[i:i+5000]
        for i in range(0, len(program_ids), 5000)
    ]
    assert len(batches) == 3
    assert len(batches[0]) == 5000
    assert len(batches[2]) == 2000
```

### 6.2 Integration Tests

**File:** `tests/test_sync_integration.py`

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_sync_flow(db_session):
    """Test complete sync with real SD API"""
    sync = GuideDataSync(db_session)

    # Sync 1 day only for testing
    result = await sync.sync_guide_data(days=1)

    assert result.status == "completed"
    assert result.lineups_updated > 0
    assert result.stations_updated > 0
    assert result.schedules_updated > 0
    assert result.programs_updated > 0
```

### 6.3 Manual Validation Checklist

- [ ] Run `python -m app.cli sync-guide`
- [ ] Check logs for errors
- [ ] Verify `lineups` table populated
- [ ] Verify `stations` table populated with lineup_id foreign keys
- [ ] Verify `schedules` table has md5_hash values
- [ ] Verify `programs` table populated
- [ ] Check `sync_status` table for successful record
- [ ] Verify timestamps are in UTC
- [ ] Test second sync (should use MD5 change detection)
- [ ] Verify token cached in `~/.pyhdhrdvr/sd_token.json`
- [ ] Test with expired token (manually edit cache)
- [ ] Verify background scheduler starts with app

---

## Implementation Checklist

### Phase 1: Database Schema
- [ ] Create `app/models/lineup.py`
- [ ] Update `app/models/station.py`
- [ ] Update `app/models/schedule.py`
- [ ] Create `app/models/sync_status.py`
- [ ] Create and run Alembic migration

### Phase 2: API Client
- [ ] Create `app/services/schedules_direct.py`
- [ ] Implement `SchedulesDirectClient.__init__`
- [ ] Implement token caching (load/save)
- [ ] Implement `authenticate()` with SHA1 hashing
- [ ] Implement `_ensure_token()` with auto-refresh
- [ ] Implement `_request()` base method
- [ ] Implement `get_lineups()`
- [ ] Implement `get_lineup_stations()`
- [ ] Implement `get_schedule_md5s()`
- [ ] Implement `get_schedules()`
- [ ] Implement `get_programs()`
- [ ] Implement error handling for all SD error codes
- [ ] Implement retry logic with exponential backoff

### Phase 3: Sync Service
- [ ] Create `GuideDataSync` class
- [ ] Implement `sync_guide_data()` main method
- [ ] Implement `_sync_lineups()`
- [ ] Implement `_sync_stations()`
- [ ] Implement `_sync_schedules()` with MD5 change detection
- [ ] Implement `_sync_programs()` with batch splitting
- [ ] Add SyncStatus tracking throughout
- [ ] Add error handling and rollback

### Phase 4: Background Scheduler
- [ ] Update `app/main.py` with APScheduler
- [ ] Create `sync_guide_data_job()` function
- [ ] Add startup/shutdown event handlers
- [ ] Create `app/cli.py` with click command
- [ ] Test manual CLI trigger

### Phase 5: Configuration
- [ ] Update `app/config.py` with token_cache_path
- [ ] Update `pyproject.toml` dependencies
- [ ] Run `pip install -e .`

### Phase 6: Testing
- [ ] Write unit tests for authentication
- [ ] Write unit tests for error handling
- [ ] Write integration test for full sync
- [ ] Run manual validation checklist
- [ ] Test background scheduler

---

## Expected Deliverables

1. **Database Models:**
   - `Lineup` entity
   - Updated `Station` with lineup_id FK
   - Updated `Schedule` with md5_hash
   - `SyncStatus` for tracking

2. **API Client:**
   - Full `SchedulesDirectClient` with all endpoints
   - Token caching to file system
   - Comprehensive error handling

3. **Sync Service:**
   - `GuideDataSync` with 3-day default
   - MD5-based change detection
   - Batch processing (5000 limit)
   - Transaction safety

4. **Background Scheduler:**
   - Daily sync at 4 AM
   - CLI command for manual trigger
   - Proper startup/shutdown handling

5. **Testing:**
   - Unit tests for authentication
   - Integration test for sync
   - Manual validation checklist

---

## Estimated Total Time: 7-8 hours

**Breakdown:**
- Phase 1 (Database): 30 min
- Phase 2 (API Client): 2 hours
- Phase 3 (Sync Service): 3 hours
- Phase 4 (Scheduler): 1 hour
- Phase 5 (Config): 15 min
- Phase 6 (Testing): 1 hour

**Note:** This exceeds original 5-hour estimate due to additional features:
- Full Lineup entity (+30 min)
- SyncStatus model (+30 min)
- Background scheduler (+1 hour)
- File-based token cache (+30 min)

---

## Next Steps After Implementation

1. **Create API endpoint for sync status:**
   - `GET /api/system/sync-status` - List recent syncs
   - `POST /api/system/sync` - Trigger manual sync (returns sync_id)
   - `GET /api/system/sync/{sync_id}` - Get sync details

2. **Add UI dashboard:**
   - Display last sync time
   - Show sync status (running/completed/failed)
   - Button to trigger manual sync
   - Display error messages if sync failed

3. **Monitoring:**
   - Log sync duration
   - Alert if sync fails multiple times
   - Track data growth over time

4. **Optimization (post-MVP):**
   - Parallel API requests
   - Database indexing tuning
   - Connection pooling for httpx
   - Incremental sync (only changed data)
