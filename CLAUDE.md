# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PyHDHRDVR** is a web-based DVR management interface for HDHomeRun network TV tuner devices. It enables users to browse TV program schedules from Schedules Direct, schedule recordings (one-time and series), and automatically capture live TV streams to disk.

**Technology Stack:**
- Backend: FastAPI (Python 3.13+) with Jinja2 server-side templates
- Database: SQLite with SQLAlchemy ORM and Alembic migrations
- Recording Format: MPEG-TS (original transport stream, no transcoding)
- Storage: Local filesystem
- External APIs: HDHomeRun HTTP API, Schedules Direct JSON API

**Target Deployment:** Single-user, local network only (no authentication required)

---

## Project Structure

```
pyhdhrdvr/
├── app/                      # Main application code
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic settings (loads from .env)
│   ├── models/              # SQLAlchemy database models
│   ├── services/            # Business logic and external API clients
│   │   ├── schedules_direct.py  # Schedules Direct API client
│   │   ├── hdhomerun.py         # HDHomeRun device control
│   │   └── recorder.py          # Recording scheduler and execution
│   └── routes/              # FastAPI routes (web pages and API endpoints)
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JavaScript, images
├── tests/                   # Test files
├── specs/                   # Design documentation
│   ├── plan.md             # Full requirements document
│   ├── tasks.md            # MVP implementation tasks
│   ├── data-model.md       # Database schema specification
│   └── contracts/          # API contract specifications
└── alembic/                # Database migrations (created on setup)
```

---

## Development Workflow

### Initial Setup

```bash
# Install dependencies
pip install -e .

# Create .env file from example
cp .env.example .env
# Edit .env with your HDHomeRun IP, Schedules Direct credentials, etc.

# Initialize database
alembic upgrade head

# Run guide data sync (first time)
python -m app.cli sync-guide
```

### Running the Application

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access web interface at: `http://localhost:8000`

### Database Migrations

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_recorder.py

# Run with coverage
pytest --cov=app --cov-report=html
```

---

## Architecture

### Core System Components

**1. Recording Scheduler (Background Service)**
- Runs as APScheduler background task in FastAPI lifecycle
- Polls database every 10 seconds for recordings with status='scheduled'
- Starts recordings at `air_datetime - padding_start_seconds`
- Updates recording status: scheduled → in_progress → completed/failed
- Handles tuner allocation and cleanup

**2. HDHomeRun Client (`app/services/hdhomerun.py`)**
- Device discovery via UDP broadcast to 255.255.255.255:65001
- HTTP API communication: `/discover.json`, `/lineup.json`, `/tuner{N}/`
- Tuner control: tune channel, verify lock status, release tuner
- MPEG-TS stream capture via HTTP streaming to file

**3. Schedules Direct Client (`app/services/schedules_direct.py`)**
- Authentication: POST to `https://json.schedulesdirect.org/20141201/token`
- Token management: 24-hour validity, auto-refresh
- Batch API calls for efficiency:
  - POST `/schedules` - Get program schedule for multiple stations
  - POST `/programs` - Get metadata for multiple programs
- Incremental sync using MD5 hashes to detect changes
- Cache strategy: Guide data refreshed daily, metadata cached 7 days

**4. Database Models (`app/models/`)**
Core entities with simplified MVP schema:
- **Station:** Broadcast channel (callsign, channel_number, name)
- **Program:** Show metadata (title, description, duration, series_id)
- **Schedule:** Specific airing (program + station + air_datetime)
- **Recording:** Scheduled/completed recording (links to schedule, tracks status and file_path)

See `specs/data-model.md` for complete schema with all fields and relationships.

### Key Data Flows

**Recording Execution Flow:**
1. User clicks "Record" → Creates Recording entry (status='scheduled')
2. Scheduler detects upcoming recording → Claims recording
3. Finds available tuner → Tunes to channel via HDHomeRun API
4. Opens HTTP stream → Writes MPEG-TS chunks to file
5. Monitors until end time + padding → Stops stream, releases tuner
6. Validates file → Updates status to 'completed' or 'failed'

**Guide Data Sync Flow:**
1. Authenticate with Schedules Direct → Get token
2. Fetch user's lineups → Get stations
3. Batch request schedules → Get upcoming airings (14 days)
4. Compare MD5 hashes → Identify changed/new programs
5. Batch request program metadata → Get titles, descriptions, etc.
6. Update database → Insert/update Program and Schedule records
7. Trigger series matching (post-MVP) → Auto-schedule new episodes

---

## Configuration

All configuration via `.env` file (loaded by Pydantic Settings in `app/config.py`):

**Required:**
- `HDHOMERUN_IP` - IP address of HDHomeRun device (e.g., "192.168.1.100")
- `SD_USERNAME` - Schedules Direct username (email)
- `SD_PASSWORD` - Schedules Direct password
- `RECORDING_PATH` - Directory for recordings (e.g., "/mnt/recordings")

**Optional (with defaults):**
- `DATABASE_URL` - SQLite path (default: "sqlite:///./pyhdhrdvr.db")
- `DEFAULT_PADDING_START` - Seconds to start early (default: 60)
- `DEFAULT_PADDING_END` - Seconds to end late (default: 120)

---

## MVP Scope vs. Full Vision

**MVP includes:**
- One-time recording scheduling only
- Simple list-based guide view
- Manual configuration (no setup wizard)
- Manual guide data sync
- Basic error handling

**Post-MVP features** (documented in `specs/plan.md`):
- Series recording rules with auto-scheduling
- Grid-based program guide
- Search functionality
- Conflict detection and resolution
- Setup wizard with device auto-discovery
- Channel scanning
- System monitoring dashboard

Refer to `specs/tasks.md` for MVP implementation plan (~40 hours, 20 tasks).

---

## External API Integration Notes

### HDHomeRun HTTP API

**Device Discovery:**
- UDP broadcast to 255.255.255.255:65001
- Response contains: device_id, model, IP address

**Key Endpoints:**
- `GET http://{ip}/discover.json` - Device info (model, firmware, tuner count)
- `GET http://{ip}/lineup.json` - Available channels
- `GET http://{ip}/tuner{N}/` - Tuner status or MPEG-TS stream
- `POST http://{ip}/tuner{N}/channel/{channel}` - Tune to channel
- `POST http://{ip}/tuner{N}/channel/none` - Release tuner

**Tuning Process:**
1. POST to tune channel
2. GET status to verify lock (retry up to 10 seconds)
3. GET stream to capture MPEG-TS data
4. POST "none" to release when done

### Schedules Direct JSON API

**Base URL:** `https://json.schedulesdirect.org/20141201/`

**Authentication:**
- POST `/token` with username/password → Returns token (24h validity)
- Include token in header: `token: {token_value}`

**Key Endpoints:**
- `GET /lineups` - User's available lineups
- `GET /lineups/{lineup-id}` - Stations in lineup
- `POST /schedules` - Batch: Get schedules for multiple stations
- `POST /programs` - Batch: Get metadata for multiple program IDs

**Best Practices:**
- Use batch APIs (send arrays of IDs) for efficiency
- Respect rate limits (implement exponential backoff)
- Cache aggressively (guide data changes infrequently)
- Store MD5 hashes to detect changed programs

---

## File Naming Convention

**Recordings organized by type:**
```
{RECORDING_PATH}/
├── {SeriesTitle}/           # Series episodes
│   └── S{season:02d}E{episode:02d} - {EpisodeTitle}.ts
├── Movies/                  # Movie recordings
│   └── {MovieTitle} ({air_date}).ts
└── OneTime/                 # Non-episodic recordings
    └── {ProgramTitle} ({air_date} {time}).ts
```

**Filename sanitization:**
- Replace invalid characters (`/ \ : * ? " < > |`) with underscore
- Limit length to 255 characters (filesystem limit)
- Append counter for duplicates: `filename (1).ts`

---

## Important Constraints

**Time Handling:**
- All datetimes stored in UTC (SQLite or database)
- Convert to local timezone only for display in UI
- Use timezone-aware datetime objects to avoid DST issues

**Tuner Management:**
- Track which tuners are in use by this application
- Check availability before starting recording
- Handle external tuner usage (Plex, VLC, etc.) gracefully
- MVP: No conflict detection, user manages manually

**Storage:**
- Check free space before starting recording
- Warn when free space < configurable threshold (default: 10GB)
- Fail gracefully on disk full (stop recording, mark as failed)
- Recording size estimate: 2-4 GB per hour for HD content

**Error Recovery:**
- Retry transient failures (API calls, device communication) up to 3 times
- Log all recording events for troubleshooting
- Keep partial recordings for user review (don't auto-delete)
- Continue operation with cached guide data if Schedules Direct unavailable

---

## Testing Strategy

**Integration Tests (Priority):**
- Test with real HDHomeRun device and Schedules Direct account
- Start with short test recordings (5 minutes)
- Verify recorded files play in VLC
- Test concurrent recordings (up to tuner count)

**Unit Tests:**
- Configuration validation
- Filename sanitization
- Time calculations with padding
- Recording state transitions

**Manual Testing Workflow:**
1. Configure app with credentials
2. Run guide data sync
3. Browse guide, schedule recording airing soon
4. Monitor recording execution
5. Verify file created and playable
6. Test cancellation, deletion, error scenarios

---

## Common Issues

**"No tuner available" errors:**
- Check if other apps are using HDHomeRun (Plex, Kodi)
- Verify tuner count vs. concurrent recordings
- Check device is online: `curl http://{device_ip}/discover.json`

**Guide data not loading:**
- Verify Schedules Direct credentials
- Check subscription status (expires annually)
- Test API manually: `curl -u username:password https://json.schedulesdirect.org/20141201/token`
- Check network connectivity

**Recordings fail immediately:**
- Verify RECORDING_PATH exists and is writable
- Check available disk space
- Verify channel number matches lineup
- Check HDHomeRun can tune channel (test with official app)

**Stream drops or corruption:**
- Check network stability between server and HDHomeRun
- Verify HDHomeRun device firmware is up-to-date
- Test with shorter recording duration
- Check for firewall/network issues

---

## Design Documentation

Comprehensive specifications in `specs/` directory:

- **`plan.md`** - Full requirements document (90+ pages)
  - Functional & non-functional requirements
  - User stories with MoSCoW prioritization
  - Edge cases and exception scenarios
  - Risk analysis and mitigation strategies

- **`data-model.md`** - Complete database schema
  - 9 entities with full field definitions
  - Relationships and foreign keys
  - Indexes for query optimization
  - Sample SQL queries

- **`contracts/`** - API specifications (7 files)
  - Request/response schemas for all endpoints
  - Error response formats
  - Pagination and validation rules
  - Organized by domain (guide, recordings, series, library, system, setup)

- **`tasks.md`** - MVP implementation plan
  - 20 prioritized tasks (~40 hours total)
  - Organized into 5 phases
  - Deliverables and estimates for each task

Refer to these when implementing features to ensure consistency with the design.