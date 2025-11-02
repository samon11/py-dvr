# PyDVR - MVP Task List

**Version:** 1.0 - MVP Only
**Date:** 2025-10-31
**Goal:** Build a minimal working DVR that can schedule and execute recordings

---

## MVP Scope

**What we're building:**
A user can configure the app, browse TV listings, schedule one-time recordings, and have them successfully record to disk.

**What we're NOT building yet:**
- Setup wizard (use config file)
- Auto-discovery (manual IP entry)
- Grid-based guide (simple list view)
- Series recordings (one-time only)
- Conflict detection (manual management)
- Search functionality
- Advanced error handling
- System monitoring dashboard

---

## Phase 1: Foundation (Days 1-2)

### [P0] Task 1.1: Project Setup ✅
**Estimate:** 1 hour
**Status:** COMPLETED

- [x] Initialize git repository
- [x] Create Python project structure:
  ```
  pyhdhrdvr/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── models/
  │   ├── services/
  │   └── routes/
  ├── templates/
  ├── static/
  ├── tests/
  ├── pyproject.toml
  ├── .env.example
  └── README.md
  ```
- [x] Create pyproject.toml with dependencies:
  - fastapi
  - uvicorn
  - sqlalchemy
  - alembic
  - pydantic
  - httpx
  - jinja2
- [x] Create basic README.md

**Deliverable:** Project structure with installable package ✅

---

### [P0] Task 1.2: Configuration Management ✅
**Estimate:** 1 hour
**Status:** COMPLETED

- [x] Create `app/config.py` with Pydantic settings:
  - `HDHOMERUN_IP`: str
  - `SD_USERNAME`: str
  - `SD_PASSWORD`: str
  - `RECORDING_PATH`: Path
  - `DATABASE_URL`: str
  - `DEFAULT_PADDING_START`: int (default: 60)
  - `DEFAULT_PADDING_END`: int (default: 120)
- [x] Support loading from `.env` file
- [x] Add validation for required fields
- [x] Create `.env.example` template

**Deliverable:** Working configuration system ✅

---

### [P0] Task 1.3: Database Setup ✅
**Estimate:** 2 hours
**Status:** COMPLETED

- [x] Create SQLAlchemy models in `app/models/`:
  - Station (simplified: id, callsign, channel_number, name)
  - Program (simplified: id, title, description, duration_seconds)
  - Schedule (id, program_id, station_id, air_datetime, duration_seconds)
  - Recording (id, schedule_id, status, file_path, padding_start, padding_end)
- [x] Keep it minimal - only essential fields
- [x] Create Alembic migration for initial schema
- [x] Create database initialization function

**Deliverable:** Working database with basic schema ✅

---

### [P0] Task 1.4: Basic FastAPI Application
**Estimate:** 2 hours

- [x] Create `app/main.py` with FastAPI app instance
- [x] Add static file serving for CSS/JS
- [x] Configure Jinja2 templates
- [x] Create base template (`templates/base.html`) with:
  - Simple navigation (Guide, Scheduled, Recordings)
  - Basic CSS for readable layout
- [x] Add health check endpoint: `GET /health`
- [x] Test app starts successfully: `uvicorn app.main:app`

**Deliverable:** Running FastAPI app with basic templating

---

## Phase 2: External Integrations (Days 3-4)

### [P0] Task 2.1: Schedules Direct Client - Authentication
**Estimate:** 2 hours

- [x] Create `app/services/schedules_direct.py`
- [x] Implement authentication:
  - POST to `https://json.schedulesdirect.org/20141201/token`
  - Store token with expiration
  - Auto-refresh when expired
- [x] Add error handling for invalid credentials
- [x] Test with real SD account

**Deliverable:** Working SD authentication

---

### [P0] Task 2.2: Schedules Direct Client - Guide Data
**Estimate:** 3 hours

- [x] Implement lineup retrieval:
  - GET user's lineups
  - GET stations for a lineup
- [x] Implement schedule retrieval:
  - POST /schedules (batch request)
  - Parse schedule data
- [x] Implement program metadata retrieval:
  - POST /programs (batch request)
  - Parse program details
- [x] Create function to sync guide data to database
- [x] For MVP: Sync only 3 days of data (not 14)

**Deliverable:** Function that populates database with guide data

---

### [P0] Task 2.3: HDHomeRun Client - Basic Communication
**Estimate:** 2 hours

- [x] Create `app/services/hdhomerun.py`
- [x] Implement device info retrieval:
  - GET `http://{device_ip}/discover.json`
  - Parse device model, tuner count
- [x] Implement tuner status check:
  - GET `http://{device_ip}/tuner{N}/`
  - Parse tuner availability
- [x] Test connection to real HDHomeRun device

**Deliverable:** Working device communication

---

### [P0] Task 2.4: HDHomeRun Client - Recording
**Estimate:** 3 hours

- [x] Implement channel tuning:
  - POST `http://{device_ip}/tuner{N}/channel/{channel}`
  - Verify tuner lock
- [x] Implement stream capture:
  - GET `http://{device_ip}/tuner{N}/` (MPEG-TS stream)
  - Write chunks to file
  - Handle stream interruptions
- [x] Implement tuner release:
  - POST `http://{device_ip}/tuner{N}/channel/none`
- [x] Create test recording function (record 30 seconds)

**Deliverable:** Function that can record a channel to file

---

## Phase 3: Recording Engine (Days 5-6)

### [P0] Task 3.1: Recording Scheduler Service ✅
**Estimate:** 4 hours
**Status:** COMPLETED

- [x] Create `app/services/recorder.py`
- [x] Implement scheduler loop:
  - Check database every 10 seconds for upcoming recordings
  - Start recording at scheduled time minus padding
- [x] Implement recording state machine:
  - scheduled → in_progress → completed/failed
- [x] Update recording status in database
- [x] Calculate actual recording time with padding
- [x] Handle basic errors (no tuner available, stream error)

**Deliverable:** Background service that executes recordings ✅

---

### [P0] Task 3.2: Recording Execution Logic ✅
**Estimate:** 3 hours
**Status:** COMPLETED

- [x] Create filename from program data:
  - Format: `{title} ({date}).ts`
  - Sanitize invalid characters
- [x] Create recording directory if needed
- [x] Implement recording workflow:
  1. Find available tuner
  3. Capture stream to file
  4. Monitor for errors
  5. Stop at end time + padding
  6. Release tuner
  7. Update recording status
- [x] Validate file exists and has reasonable size

**Deliverable:** Complete recording execution pipeline ✅

---

### [P0] Task 3.3: Background Task Integration ✅
**Estimate:** 2 hours
**Status:** COMPLETED

- [x] Add APScheduler to FastAPI app
- [x] Create background task for recording scheduler
- [x] Start scheduler on app startup
- [x] Ensure scheduler runs continuously
- [x] Add graceful shutdown handling

**Deliverable:** Recording scheduler runs as background task ✅

---

## Phase 4: Web Interface (Days 7-8)

### [P0] Task 4.1: Guide Page - List View
**Estimate:** 3 hours

- [x] Create route: `GET /guide` in `app/routes/guide.py`
- [x] Create template: `templates/guide.html`
- [x] Display programs as simple list:
  - Group by channel
  - Show: time, title, description
  - Show only next 12 hours (keep it simple)
- [x] Add "Record" button for each program
- [x] Make it readable with basic CSS

**Deliverable:** Working guide page showing programs

---

### [P0] Task 4.2: Schedule Recording Action
**Estimate:** 2 hours

- [ ] Create API endpoint: `POST /api/recordings`
- [ ] Accept schedule_id and optional padding values
- [ ] Create Recording entry in database with status="scheduled"
- [ ] Return success/error response
- [ ] Add JavaScript to handle "Record" button click
- [ ] Show success message on page

**Deliverable:** User can schedule recordings from guide

---

### [P0] Task 4.3: Scheduled Recordings Page
**Estimate:** 2 hours

- [x] Create route: `GET /scheduled` in `app/routes/recordings.py`
- [x] Create template: `templates/scheduled.html`
- [x] Display upcoming recordings as list:
  - Show: program title, channel, date/time, status
  - Sort by air time
- [x] Add "Cancel" button for each recording
- [x] Implement cancel action: `DELETE /api/recordings/{id}`

**Deliverable:** User can view and cancel scheduled recordings

---

### [P0] Task 4.4: Recordings Library Page
**Estimate:** 2 hours

- [x] Create route: `GET /recordings` in `app/routes/recordings.py`
- [x] Create template: `templates/recordings.html`
- [x] Display completed recordings as list:
  - Show: program title, air date, file size
  - Filter: status='completed'
- [x] Show file path for each recording
- [x] Add "Delete" button (deletes DB entry + file)
- [x] Show storage stats (total used, free space)

**Deliverable:** User can view and delete recordings

---

## Phase 5: Integration & Testing (Days 9-10)

### [P0] Task 5.1: End-to-End Testing
**Estimate:** 3 hours

- [ ] Manual test workflow:
  1. Configure app with real credentials
  2. Start app: `uvicorn app.main:app`
  3. Load guide data (run sync manually first time)
  4. Browse guide page
  5. Schedule a recording (test program airing soon)
  6. Verify recording appears in scheduled list
  7. Wait for recording to execute
  8. Verify file created in recording directory
  9. Verify recording appears in library
  10. Play recording in VLC to confirm it works
- [ ] Document any bugs found
- [ ] Fix critical bugs

**Deliverable:** Verified end-to-end workflow

---

### [P1] Task 5.2: Guide Data Sync Command
**Estimate:** 2 hours

- [ ] Create CLI command or API endpoint to sync guide data
- [ ] For MVP: Run manually when needed
- [ ] Add progress logging
- [ ] Handle errors gracefully
- [ ] Document how to run sync

**Deliverable:** Manual guide data sync

---

### [P1] Task 5.3: Basic Error Handling
**Estimate:** 2 hours

- [ ] Add try/catch blocks to critical paths
- [ ] Log errors with context
- [ ] Return user-friendly error messages
- [ ] Handle common failures:
  - SD API unreachable
  - HDHomeRun device offline
  - Disk full
  - No tuner available

**Deliverable:** App doesn't crash on common errors

---

### [P1] Task 5.4: Documentation
**Estimate:** 2 hours

- [ ] Update README.md with:
  - Installation instructions
  - Configuration guide
  - How to run the app
  - How to sync guide data
  - Troubleshooting tips
- [ ] Add comments to complex code sections
- [ ] Document API endpoints (basic list)

**Deliverable:** Users can install and run the app

---

## MVP Complete! 🎉

**Total Estimated Time:** ~40 hours (5 days of focused work or 2 weeks part-time)

### What You Built:
✅ Database with guide data and recordings
✅ Integration with Schedules Direct
✅ Integration with HDHomeRun
✅ Background recording scheduler
✅ Web UI to browse programs
✅ Ability to schedule one-time recordings
✅ Automatic recording execution
✅ Library to view completed recordings

### What's Missing (Post-MVP):
- Setup wizard
- Auto-discovery
- Grid-based guide
- Series recordings
- Conflict detection
- Search
- Advanced UI/UX
- Comprehensive error handling
- System monitoring

---

## Post-MVP Priorities

Once MVP is working, prioritize in this order:

1. **Series Recording** - Most requested feature
2. **Grid Guide** - Better UX for browsing
3. **Search** - Find shows quickly
4. **Conflict Detection** - Prevent recording failures
5. **Setup Wizard** - Easier onboarding
6. **Auto-discovery** - Convenience feature

---

## Notes

### Simplifications for MVP:
- Manual configuration (no wizard)
- Manual guide sync (no automatic daily refresh)
- Simple list guide (no grid)
- One-time recordings only
- No conflict checking (user manages manually)
- Basic error handling only
- Minimal UI styling

### Why These Simplifications:
- Gets you to a working DVR faster
- Proves core functionality works
- Provides foundation to build on
- Reduces complexity and risk
- Allows for user feedback early

### Development Tips:
- Test with a real HDHomeRun and SD account from day 1
- Start with short test recordings (5 minutes)
- Use a dedicated test recording directory
- Keep backups of your database during development
- Commit code frequently
