# PyHDHRDVR - Project Requirements Documentation

**Document Version:** 1.0
**Date:** 2025-10-31
**Project Phase:** Planning & Requirements Definition

---

## 1. PROJECT OVERVIEW

### 1.1 Project Description
**PyHDHRDVR** is a web-based DVR management interface for HDHomeRun network TV tuner devices. The application enables users to browse TV program schedules, search for content, and schedule recordings (both one-time and series) using a modern web interface.

### 1.2 Primary Goals
- Provide a lightweight, web-based alternative to commercial DVR solutions
- Enable automated recording of over-the-air/cable TV content via HDHomeRun devices
- Integrate with Schedules Direct for accurate, comprehensive TV guide data
- Deliver a simple, intuitive interface for managing TV recordings

### 1.3 Target Users
- **Primary:** Individual/household user with technical aptitude for self-hosting
- **User Profile:** Cord-cutter using HDHomeRun tuner for OTA/cable TV
- **Technical Level:** Comfortable with command-line setup but wants web UI for daily use

### 1.4 Key Constraints

#### Technical Constraints
- **Backend:** FastAPI (Python)
- **Frontend:** Jinja2 server-side templates (no SPA framework)
- **Authentication:** None (single-user, local network deployment)
- **Storage:** Local filesystem on application server
- **Recording Format:** MPEG-TS (original transport stream, no transcoding)
- **Device Communication:** Direct HTTP/UDP protocol with HDHomeRun devices

#### Business/Operational Constraints
- Personal project (no commercial support requirements)
- MVP scope: Focus on scheduling and management, not playback
- Requires Schedules Direct subscription (~$25/year) for EPG data
- Assumes local network deployment (not internet-exposed)

#### Integration Constraints
- Must work with HDHomeRun device HTTP API (device discovery, tuner control, streaming)
- Must integrate with Schedules Direct JSON API for program guide data
- No HDHomeRun RECORD device required (DIY DVR approach)

---

## 2. FUNCTIONAL REQUIREMENTS

### 2.1 System Initialization & Configuration

**FR-1.1: Initial Setup Wizard**
- The system shall provide a first-run setup wizard to configure:
  - Schedules Direct credentials (username/password)
  - HDHomeRun device discovery (automatic network scan)
  - Recording storage path
  - Lineup selection (which channels to use)

**FR-1.2: HDHomeRun Device Discovery**
- The system shall automatically discover HDHomeRun devices on the local network using UDP broadcast
- The system shall support manual device entry via IP address if auto-discovery fails
- The system shall display device model, firmware version, and tuner count
- The system shall validate device connectivity before saving configuration

**FR-1.3: Schedules Direct Integration**
- The system shall authenticate with Schedules Direct API using user credentials
- The system shall retrieve available lineups for the user account
- The system shall allow selection of one or more lineups to track
- The system shall cache lineup and station data locally

**FR-1.4: Channel Management**
- The system shall perform channel scan using HDHomeRun device to discover available channels
- The system shall match scanned channels with Schedules Direct lineup data
- The system shall allow users to enable/disable specific channels from the guide
- The system shall store channel favorites for quick access

### 2.2 Program Guide & Browsing

**FR-2.1: Grid-Based Program Guide**
- The system shall display a grid-style program guide showing:
  - Time slots (configurable increment: 30min or 60min)
  - Channel list (vertically)
  - Program blocks spanning their scheduled duration (horizontally)
- The guide shall display at minimum 4 hours of content
- The guide shall support navigation to future/past time periods (up to 14 days forward)

**FR-2.2: Program Listing View**
- The system shall provide a list view of upcoming programs by channel
- The list view shall display: program title, episode info, air time, duration, description
- The list view shall support filtering by channel, date, and time range

**FR-2.3: Program Detail View**
- The system shall display detailed information for selected programs:
  - Title, episode number (SxxExx format), original air date
  - Full description/synopsis
  - Cast, crew, genre, content rating
  - Air date and time, duration
  - Repeat/new episode indicator
- The detail view shall show all upcoming airings of the same episode
- The detail view shall provide action buttons (Record This, Record Series)

**FR-2.4: Guide Data Refresh**
- The system shall automatically refresh guide data from Schedules Direct daily
- The system shall support manual refresh triggered by user
- The system shall display last update timestamp in the UI
- The system shall continue operating with cached data if Schedules Direct is unavailable

### 2.3 Search Functionality

**FR-3.1: Global Search**
- The system shall provide a global search box accessible from all pages
- The search shall query program titles, episode titles, and descriptions
- The search shall return results showing: program title, episode info, channel, air times

**FR-3.2: Search Filters**
- The search shall support filtering by:
  - Date range (today, this week, next 7 days, next 14 days)
  - Channel(s)
  - Genre/category
  - Content rating
  - New episodes only vs. all airings

**FR-3.3: Search Results Display**
- The system shall display search results grouped by show title
- Each result shall show next airing time and count of upcoming airings
- Results shall include "Record" action buttons
- Results shall link to full program detail pages

### 2.4 Recording Management - One-Time Recordings

**FR-4.1: Schedule Single Recording**
- The system shall allow users to schedule a one-time recording from:
  - Program guide grid (click/tap program)
  - Program detail page
  - Search results
- The system shall confirm recording scheduled with visual feedback

**FR-4.2: Recording Pre/Post Padding**
- The system shall allow configurable padding for recordings:
  - Start early (0-30 minutes before scheduled start)
  - End late (0-60 minutes after scheduled end)
- Padding shall default to system-wide settings (configurable: e.g., 1 min early, 2 min late)
- Padding shall be adjustable per recording when scheduling

**FR-4.3: View Scheduled Recordings**
- The system shall provide a "Scheduled Recordings" page listing all upcoming recordings
- The list shall display: program title, episode, channel, date/time, status
- The list shall sort by scheduled recording time (earliest first)
- The list shall distinguish between one-time and series recordings

**FR-4.4: Cancel/Modify Recording**
- The system shall allow users to cancel scheduled recordings before they begin
- The system shall allow users to modify padding settings for scheduled recordings
- The system shall prompt for confirmation before canceling

### 2.5 Recording Management - Series Recordings

**FR-5.1: Schedule Series Recording**
- The system shall allow users to create series recording rules from:
  - Program detail page
  - Search results (via show grouping)
- The system shall prompt user to configure series options:
  - Record all airings or only new episodes
  - Channel restriction (record from specific channel or any channel)
  - Time restriction (e.g., record only primetime airings 7-11 PM)
  - Keep limit (number of episodes to retain, or unlimited)

**FR-5.2: Series Recording Rule Matching**
- The system shall automatically match upcoming program airings to active series rules
- Matching shall use Schedules Direct series ID for accurate identification
- The system shall handle series with multiple airings per day (e.g., news, talk shows)
- The system shall respect "new episodes only" setting using original air date metadata

**FR-5.3: View Series Recording Rules**
- The system shall provide a "Series Manager" page listing all active series rules
- Each series shall display: show title, rule parameters, count of scheduled recordings
- The page shall show upcoming recordings associated with each series

**FR-5.4: Modify/Delete Series Rules**
- The system shall allow users to edit series recording options
- Changes shall apply to future recordings (not already completed recordings)
- The system shall allow deletion of series rules
- Deleting a series rule shall prompt whether to:
  - Keep scheduled recordings for this series
  - Cancel all scheduled recordings for this series
  - Keep already-completed recordings

**FR-5.5: Series Recording Exceptions**
- The system shall allow users to skip specific episodes within a series rule
- The system shall allow users to uncancel specific episodes previously skipped

### 2.6 Recording Execution

**FR-6.1: Tuner Availability Check**
- The system shall check tuner availability before scheduled recording time
- The system shall detect number of available tuners on HDHomeRun device
- The system shall track which tuners are currently in use by the DVR system

**FR-6.2: Recording Initiation**
- The system shall tune the HDHomeRun device to the correct channel at recording start time (minus padding)
- The system shall begin streaming MPEG-TS data from the device
- The system shall write the stream to the configured storage location
- The system shall create recordings in format: `{ShowTitle}/SxxExx - {EpisodeTitle}.ts`

**FR-6.3: Recording Monitoring**
- The system shall monitor active recordings for stream errors or interruptions
- The system shall log recording start time, end time, and file size
- The system shall update recording status in real-time (Scheduled → In Progress → Completed)

**FR-6.4: Recording Completion**
- The system shall stop recording at scheduled end time (plus padding)
- The system shall release the tuner for other use
- The system shall verify the recorded file exists and has reasonable size (not corrupted)
- The system shall update recording metadata with final status

**FR-6.5: Recording Failure Handling**
- The system shall mark recordings as "Failed" if:
  - No tuner was available at start time
  - Stream connection failed or dropped
  - Disk write errors occurred
  - File size is unexpectedly small (< 1MB for 30min program)
- Failed recordings shall be logged with error reason
- The system shall retain partial recordings for user review

### 2.7 Recording Conflict Resolution

**FR-7.1: Conflict Detection**
- The system shall detect scheduling conflicts when:
  - Scheduled recordings overlap in time
  - Number of concurrent recordings exceeds available tuners
- Conflict detection shall occur when:
  - User schedules a new recording
  - Series rules generate new scheduled recordings
  - Guide data updates change program times

**FR-7.2: Conflict Notification**
- The system shall display conflicts prominently in the UI
- The "Scheduled Recordings" page shall highlight conflicting recordings
- A dedicated "Conflicts" page shall list all unresolved conflicts

**FR-7.3: Conflict Resolution (Manual)**
- The system shall allow users to resolve conflicts by:
  - Canceling one or more conflicting recordings
  - Adjusting recording padding to eliminate overlap
  - Modifying series rules to prevent future conflicts
- The system shall indicate when conflict is resolved

**FR-7.4: Priority System (Optional - Future Enhancement)**
- *(Out of MVP scope but documented for future consideration)*
- The system could allow priority ranking of series rules
- Auto-resolution could cancel lower-priority recordings when conflicts occur

### 2.8 Recording Library Management

**FR-8.1: View Recorded Content**
- The system shall provide a "Recordings" page listing all completed recordings
- Recordings shall be organized by show title (grouped)
- Each recording shall display: episode info, air date, recording date, file size, duration

**FR-8.2: Recording Metadata Display**
- The system shall display metadata for completed recordings:
  - Program information (title, episode, description, cast)
  - Technical information (file path, file size, duration, channel recorded from)
  - Recording status (successful, partial, failed)

**FR-8.3: Delete Recordings**
- The system shall allow users to delete individual recordings
- The system shall prompt for confirmation before deleting
- Deletion shall remove both the file and database record
- The system shall update available disk space after deletion

**FR-8.4: Batch Delete Operations**
- The system shall allow selection of multiple recordings for batch deletion
- The system shall provide "Delete All Episodes" option for a series
- The system shall provide "Delete Watched" option (requires manual marking)

**FR-8.5: Storage Management**
- The system shall display total disk space, used space, and free space on recording volume
- The system shall display total size of all recordings
- The system shall warn when free space falls below configurable threshold (e.g., 10GB)

### 2.9 System Administration

**FR-9.1: Settings Configuration**
- The system shall provide a Settings page with configurable options:
  - Schedules Direct credentials
  - HDHomeRun device IP (if manual configuration)
  - Recording storage path
  - Default recording padding (start/end)
  - Guide refresh schedule
  - Storage warning threshold
  - Lineup management (add/remove lineups)

**FR-9.2: System Status Dashboard**
- The system shall provide a dashboard showing:
  - HDHomeRun device status (online/offline)
  - Tuner status (available, in use)
  - Next scheduled recording
  - Recent recording activity
  - Storage capacity
  - Last guide data update

**FR-9.3: Logging & Diagnostics**
- The system shall log all significant events:
  - Recording start/stop/failure
  - Device communication errors
  - API failures (Schedules Direct)
  - Configuration changes
- Logs shall be viewable in the web interface
- Logs shall be rotatable to prevent unbounded growth

**FR-9.4: Background Task Management**
- The system shall run background tasks for:
  - Guide data refresh (daily)
  - Series rule matching (after guide refresh)
  - Recording scheduler (continuous monitoring)
  - Storage cleanup based on retention rules
- Background tasks shall be visible in system status
- The system shall support manual triggering of tasks

---

## 3. NON-FUNCTIONAL REQUIREMENTS

### 3.1 Performance Requirements

**NFR-P1: Page Load Time**
- Web pages shall load within 2 seconds under normal conditions (local network, guide data cached)
- The program guide grid shall render within 3 seconds for 4-hour window

**NFR-P2: Search Response Time**
- Search queries shall return results within 1 second for typical query
- Search index shall be optimized for title and description text

**NFR-P3: Guide Data Refresh**
- Full guide data refresh shall complete within 5 minutes (14 days of data, typical lineup)
- Guide refresh shall not block user interface operations

**NFR-P4: Recording Reliability**
- The system shall successfully initiate 99%+ of scheduled recordings (assuming tuner availability and device connectivity)
- Stream buffering shall prevent dropouts during active recording

**NFR-P5: Concurrent Operations**
- The system shall support simultaneous operations:
  - Multiple background recordings (limited by tuner count)
  - Web UI access during recording
  - Guide data refresh during recording

**NFR-P6: Database Query Performance**
- Database queries for scheduled recordings shall return in < 500ms
- Guide data queries shall use indexed fields (time, channel, series ID)

### 3.2 Scalability Requirements

**NFR-SC1: Guide Data Volume**
- The system shall efficiently handle guide data for:
  - Up to 100 channels
  - 14 days of forward data
  - Estimated 50,000+ program entries

**NFR-SC2: Recording Library Size**
- The system shall support libraries with 1,000+ recorded episodes without performance degradation
- File system organization shall use hierarchical directories to avoid single-directory limits

**NFR-SC3: Concurrent Recordings**
- The system shall support concurrent recordings up to available tuner count (typically 2-4)
- The system shall scale to HDHomeRun devices with up to 6 tuners (e.g., HDHomeRun PRIME)

### 3.3 Reliability Requirements

**NFR-R1: System Uptime**
- The application shall run continuously as a background service/daemon
- The system shall automatically restart after unhandled errors
- Critical failures shall not corrupt database or configuration

**NFR-R2: Data Integrity**
- Recording metadata shall be persisted transactionally (no partial database writes)
- Configuration changes shall be validated before saving
- Database backups shall be supported (export/import)

**NFR-R3: Graceful Degradation**
- If Schedules Direct is unavailable, the system shall continue operating with cached guide data
- If HDHomeRun device is offline, the system shall display error but allow schedule browsing
- Failed recordings shall not prevent other scheduled recordings

**NFR-R4: Error Recovery**
- The system shall automatically retry failed HTTP requests to devices/APIs (up to 3 attempts)
- The system shall recover from temporary network interruptions during recording
- The system shall handle disk-full conditions gracefully (cancel in-progress recording, alert user)

### 3.4 Usability Requirements

**NFR-U1: User Interface Design**
- The interface shall follow modern web design principles (responsive, intuitive navigation)
- Visual design shall be clean and uncluttered, optimized for desktop browsers
- The guide grid shall be readable on screens ≥ 1280px wide

**NFR-U2: Responsive Design**
- The interface shall be usable on tablet devices (portrait and landscape)
- Core functions (schedule, cancel, search) shall work on mobile phones (≥ 375px width)
- Complex views (program guide grid) may be simplified on small screens

**NFR-U3: Browser Compatibility**
- The system shall support modern browsers:
  - Chrome/Chromium (last 2 versions)
  - Firefox (last 2 versions)
  - Safari (last 2 versions)
  - Edge (Chromium-based)
- JavaScript shall be required (no graceful degradation to non-JS)

**NFR-U4: Accessibility**
- The interface shall use semantic HTML for screen reader compatibility
- Interactive elements shall be keyboard-navigable
- Color contrast shall meet WCAG 2.1 AA standards
- Alt text shall be provided for informational images

**NFR-U5: User Feedback**
- All user actions shall provide immediate visual feedback (loading spinners, success messages)
- Error messages shall be clear and actionable
- Confirmation dialogs shall be used for destructive actions (delete, cancel)

**NFR-U6: Learning Curve**
- New users shall be able to schedule their first recording within 5 minutes
- Navigation structure shall be intuitive without requiring documentation
- Help tooltips shall be provided for advanced features

### 3.5 Security Requirements

**NFR-S1: Network Security**
- The application shall be designed for local network deployment only (not internet-exposed)
- If internet access is required, the application shall use HTTPS with valid certificate
- The system shall not implement authentication (single-user assumption)

**NFR-S2: Data Protection**
- Schedules Direct credentials shall be stored encrypted (not plaintext)
- API keys and passwords shall not be logged
- Configuration files shall have restricted file permissions (owner read/write only)

**NFR-S3: Input Validation**
- All user inputs shall be validated server-side
- File paths shall be sanitized to prevent directory traversal attacks
- SQL injection shall be prevented via parameterized queries (ORM usage)

**NFR-S4: Dependency Security**
- Python dependencies shall be kept up-to-date with security patches
- Known vulnerable packages shall be avoided
- Dependency versions shall be pinned for reproducible builds

**NFR-S5: File System Access**
- The application shall only write to designated recording directory
- Recording deletion shall verify file path is within recording directory (prevent arbitrary file deletion)
- The application shall run with minimal required privileges (not root/administrator)

### 3.6 Maintainability Requirements

**NFR-M1: Code Quality**
- Code shall follow PEP 8 Python style guidelines
- Code shall use type hints for function signatures
- Cyclomatic complexity shall be kept low (functions < 15 complexity)

**NFR-M2: Documentation**
- README shall include installation and setup instructions
- API endpoints shall be documented (OpenAPI/Swagger via FastAPI)
- Complex algorithms (conflict detection, series matching) shall have inline comments

**NFR-M3: Testing**
- Critical functions shall have unit tests (target: 70%+ coverage)
- Integration tests shall verify HDHomeRun communication
- Mock tests shall validate Schedules Direct API integration

**NFR-M4: Logging**
- Logs shall use structured logging (JSON or key-value format)
- Log levels shall be appropriate (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Sensitive data (passwords, API keys) shall not be logged

**NFR-M5: Configuration Management**
- Configuration shall be externalized (not hardcoded)
- Environment variables shall be supported for deployment flexibility
- Configuration schema shall be validated at startup

**NFR-M6: Modularity**
- Code shall be organized into logical modules:
  - API client modules (HDHomeRun, Schedules Direct)
  - Database models and ORM
  - Recording engine
  - Web routes and templates
- Dependencies between modules shall be minimized

### 3.7 Portability Requirements

**NFR-PO1: Operating System Support**
- The system shall run on Linux (Ubuntu 20.04+, Debian 11+)
- The system shall run on Windows 10/11
- The system shall run on macOS (12+)

**NFR-PO2: Python Version**
- The system shall require Python 3.9 or higher
- The system shall use only cross-platform Python libraries

**NFR-PO3: Database Portability**
- The system shall use SQLite for data storage (no separate database server required)
- Database schema shall be managed via migrations (Alembic)
- Alternative databases (PostgreSQL, MySQL) may be supported via ORM abstraction

**NFR-PO4: Deployment Options**
- The system shall support installation via pip/pipx
- The system shall provide systemd service file for Linux
- The system shall support Docker deployment (optional)

---

## 4. USER STORIES

User stories are organized by epic/feature area and prioritized using MoSCoW method:
- **MUST**: Critical for MVP
- **SHOULD**: Important but not blocking
- **COULD**: Nice-to-have for initial release
- **WON'T**: Explicitly out of scope for MVP

### EPIC 1: Setup & Configuration

**US-1.1: Initial Setup** [MUST]
- **As a** new user
- **I want** to complete initial setup via a guided wizard
- **So that** the system is configured and ready to use without manual file editing

**Acceptance Criteria:**
- Wizard presents steps in logical order (SD credentials → device discovery → storage path → lineup)
- Each step validates input before proceeding
- User can go back to previous steps to change settings
- Wizard saves configuration and redirects to dashboard on completion

**US-1.2: Device Discovery** [MUST]
- **As a** user
- **I want** the system to automatically find my HDHomeRun device
- **So that** I don't need to look up IP addresses manually

**Acceptance Criteria:**
- System broadcasts UDP discovery packet on startup
- Discovered devices are listed with model name and IP
- User can select device from list or enter IP manually
- Connection test verifies device is accessible before saving

**US-1.3: Channel Scan** [SHOULD]
- **As a** user
- **I want** to scan for available channels using my HDHomeRun
- **So that** the guide only shows channels I can actually receive

**Acceptance Criteria:**
- Channel scan runs in background with progress indicator
- Scan results show channel number, callsign, and signal strength
- User can select which channels to include in guide
- Scanned channels are mapped to Schedules Direct lineup stations

### EPIC 2: Browsing & Discovery

**US-2.1: View Program Guide** [MUST]
- **As a** user
- **I want** to view a TV guide showing upcoming programs
- **So that** I can see what's on TV now and later

**Acceptance Criteria:**
- Guide displays current time period on page load
- Programs are shown in grid with time on horizontal axis, channels on vertical
- Current time is indicated with vertical line or highlight
- User can navigate forward/backward in time (scroll or buttons)
- Clicking a program opens details

**US-2.2: Search for Shows** [MUST]
- **As a** user
- **I want** to search for programs by name
- **So that** I can quickly find shows I want to record

**Acceptance Criteria:**
- Search box is prominent and accessible from all pages
- Search provides results as I type (autocomplete/live search)
- Results show program title, next airing time, and channel
- Clicking result shows full program details
- Empty results show helpful message ("No programs found matching '...'")

**US-2.3: View Program Details** [MUST]
- **As a** user
- **I want** to see full details about a program
- **So that** I can decide if I want to record it

**Acceptance Criteria:**
- Details page shows description, episode info, cast, genre, rating
- All upcoming airings are listed with date/time/channel
- "Record" buttons are available for single and series recording
- Page indicates if program/series is already scheduled

**US-2.4: Filter by Genre** [COULD]
- **As a** user
- **I want** to browse programs by genre (Movies, Sports, News, Drama)
- **So that** I can discover new content matching my interests

**Acceptance Criteria:**
- Genre filter is available on guide and search pages
- Selecting genre filters results to matching programs
- Multiple genres can be selected simultaneously
- Filter state persists during navigation

### EPIC 3: Recording Management

**US-3.1: Schedule One-Time Recording** [MUST]
- **As a** user
- **I want** to schedule a recording of a specific program airing
- **So that** I can watch it later

**Acceptance Criteria:**
- "Record" button is available in guide, search results, and program details
- Clicking "Record" immediately schedules the recording
- Visual feedback confirms recording is scheduled (button changes state)
- Scheduled recording appears in "Scheduled Recordings" list

**US-3.2: Schedule Series Recording** [MUST]
- **As a** user
- **I want** to create a rule to record all episodes of a show
- **So that** I don't have to manually schedule each episode

**Acceptance Criteria:**
- "Record Series" button available on program detail page
- Dialog prompts for series options (new only, channel, time restrictions)
- Series rule is created and appears in "Series Manager"
- Upcoming episodes matching rule appear in "Scheduled Recordings"

**US-3.3: View Scheduled Recordings** [MUST]
- **As a** user
- **I want** to see a list of all scheduled recordings
- **So that** I can review what will be recorded

**Acceptance Criteria:**
- List shows all upcoming recordings sorted by date/time
- Each item shows program title, episode, channel, date/time
- Icons distinguish one-time vs. series recordings
- Conflicting recordings are highlighted visually

**US-3.4: Cancel Scheduled Recording** [MUST]
- **As a** user
- **I want** to cancel a scheduled recording
- **So that** I can free up tuners or remove unwanted recordings

**Acceptance Criteria:**
- "Cancel" button available for each scheduled recording
- Confirmation dialog prevents accidental cancellation
- Canceled recording is removed from schedule list immediately
- If part of series, option to skip just this episode or delete entire series rule

**US-3.5: Manage Series Rules** [SHOULD]
- **As a** user
- **I want** to view and edit all my series recording rules
- **So that** I can adjust settings or remove series I'm no longer interested in

**Acceptance Criteria:**
- "Series Manager" page lists all active series rules
- Each series shows rule parameters and count of scheduled recordings
- "Edit" opens dialog to modify rule parameters
- "Delete" removes rule and optionally cancels scheduled recordings
- Changes to rules are reflected in scheduled recordings

**US-3.6: Set Recording Padding** [SHOULD]
- **As a** user
- **I want** to start recordings early and end late
- **So that** I don't miss the beginning or end due to schedule inaccuracies

**Acceptance Criteria:**
- Default padding is configurable in settings (e.g., 1 min early, 2 min late)
- Per-recording padding can be adjusted when scheduling
- Padding is shown in scheduled recording details
- Padding is applied when recording starts/stops

**US-3.7: Resolve Recording Conflicts** [MUST]
- **As a** user
- **I want** to see when scheduled recordings conflict
- **So that** I can decide which ones to keep

**Acceptance Criteria:**
- Conflicts are detected when recordings overlap and exceed tuner count
- Conflicting recordings are marked with warning icon
- "Conflicts" page lists all conflicts with explanations
- User can cancel recordings from conflict page to resolve
- Resolved conflicts are removed from warning list

### EPIC 4: Recording Library

**US-4.1: View Completed Recordings** [SHOULD]
- **As a** user
- **I want** to see all my recorded programs
- **So that** I know what's available to watch

**Acceptance Criteria:**
- "Recordings" page lists all completed recordings
- Recordings are grouped by show title
- Each recording shows episode info, date recorded, file size
- Failed/partial recordings are indicated with status icon

**US-4.2: Delete Recordings** [SHOULD]
- **As a** user
- **I want** to delete recordings I've watched or don't want
- **So that** I can free up disk space

**Acceptance Criteria:**
- "Delete" button available for each recording
- Confirmation dialog prevents accidental deletion
- Deleted recording is removed from list and file is deleted from disk
- Error message shown if file deletion fails

**US-4.3: View Storage Usage** [SHOULD]
- **As a** user
- **I want** to see how much disk space my recordings use
- **So that** I know when I need to delete old content

**Acceptance Criteria:**
- Dashboard/Recordings page shows total storage used by recordings
- Disk space graph or indicator shows used vs. available space
- Warning is displayed when free space is low (< configured threshold)
- Storage info updates after recordings complete or are deleted

**US-4.4: Bulk Delete Operations** [COULD]
- **As a** user
- **I want** to delete multiple recordings at once
- **So that** I can quickly clean up old content

**Acceptance Criteria:**
- Checkboxes allow selection of multiple recordings
- "Delete Selected" button appears when recordings are selected
- Confirmation dialog shows count of recordings to delete
- All selected recordings are deleted in single operation

### EPIC 5: System Monitoring

**US-5.1: View System Status** [SHOULD]
- **As a** user
- **I want** to see system status at a glance
- **So that** I know everything is working properly

**Acceptance Criteria:**
- Dashboard shows HDHomeRun device status (online/offline)
- Tuner availability is displayed (e.g., "2 of 3 tuners available")
- Next scheduled recording is prominently displayed
- Recent activity log shows last few recordings
- Last guide update time is shown

**US-5.2: View Recording History** [COULD]
- **As a** user
- **I want** to see history of past recordings including failures
- **So that** I can troubleshoot problems

**Acceptance Criteria:**
- History page lists all recording attempts (success and failure)
- Failed recordings show error reason
- History can be filtered by date range and status
- History includes timestamp, program, channel, outcome

**US-5.3: Receive Failure Notifications** [WON'T - MVP]
- **As a** user
- **I want** to be notified when recordings fail
- **So that** I can take action if needed
- **Note:** Out of scope for MVP; would require email/push notification system

### EPIC 6: Advanced Features (Future Enhancements)

**US-6.1: Automatic Commercial Detection** [WON'T - MVP]
- Out of scope; requires video analysis

**US-6.2: Transcoding Options** [WON'T - MVP]
- Out of scope; MVP uses MPEG-TS format only

**US-6.3: Remote Access (Internet Streaming)** [WON'T - MVP]
- Out of scope; local network only

**US-6.4: Multi-User Accounts** [WON'T - MVP]
- Out of scope; single-user design

**US-6.5: Watch History Tracking** [WON'T - MVP]
- Nice to have but not essential for MVP

---

## 5. SUCCESS CRITERIA

### 5.1 Technical Success Criteria

**TSC-1: Functional Completeness**
- [ ] All MUST-have user stories are implemented and tested
- [ ] User can complete full workflow: setup → browse guide → schedule recording → recording completes successfully
- [ ] Recording success rate is ≥ 95% (given tuner availability)

**TSC-2: Performance Benchmarks**
- [ ] Page load times < 2 seconds on local network
- [ ] Search returns results in < 1 second
- [ ] Program guide grid renders in < 3 seconds
- [ ] System handles 4 concurrent recordings without dropped frames

**TSC-3: Reliability Metrics**
- [ ] Application runs continuously for 7+ days without restart
- [ ] No data corruption or database inconsistencies observed
- [ ] Failed recordings are properly logged and don't crash the system

**TSC-4: Integration Validation**
- [ ] HDHomeRun device communication works reliably (discovery, tuning, streaming)
- [ ] Schedules Direct API integration retrieves accurate guide data
- [ ] Channel mapping correctly matches scanned channels to SD lineup

### 5.2 User Experience Success Criteria

**UXC-1: Usability Testing**
- [ ] New user can complete initial setup in < 10 minutes
- [ ] User can schedule first recording within 5 minutes of setup completion
- [ ] Navigation structure is intuitive (no user confusion observed during testing)
- [ ] Error messages are clear and actionable

**UXC-2: Interface Quality**
- [ ] UI is visually consistent across all pages
- [ ] Responsive design works on desktop, tablet, and mobile
- [ ] No broken layouts or overlapping elements
- [ ] Accessibility audit passes WCAG 2.1 AA criteria

### 5.3 Business/Project Success Criteria

**BSC-1: Project Completion**
- [ ] MVP delivered within target timeframe (define specific date if needed)
- [ ] Code is documented and maintainable
- [ ] Installation instructions enable deployment by technical users

**BSC-2: Personal Goals**
- [ ] Application successfully replaces commercial DVR solution for personal use
- [ ] System operates reliably for day-to-day household TV recording needs
- [ ] Project serves as portfolio piece demonstrating full-stack web development skills

### 5.4 Acceptance Testing Scenarios

**Scenario 1: End-to-End Recording**
1. User completes initial setup wizard
2. User browses program guide and finds a show airing tonight
3. User schedules a one-time recording
4. Recording starts at scheduled time and completes successfully
5. Recorded file appears in library with correct metadata
6. User can play recording in VLC or other media player

**Scenario 2: Series Recording**
1. User searches for a series (e.g., "Survivor")
2. User creates series recording rule (new episodes only)
3. System identifies upcoming episodes matching rule
4. Episodes appear in scheduled recordings list
5. Multiple episodes record successfully over several days
6. Recordings are organized by series in library

**Scenario 3: Conflict Resolution**
1. User schedules 3 recordings overlapping in time (assuming 2-tuner device)
2. System detects and displays conflict warning
3. User views conflicts page to see explanation
4. User cancels one recording to resolve conflict
5. Remaining 2 recordings proceed without issue

**Scenario 4: System Recovery**
1. HDHomeRun device is powered off during scheduled recording
2. System detects device unavailable and marks recording as failed
3. Device is powered back on
4. System automatically reconnects and proceeds with next scheduled recording

---

## 6. EDGE CASES & EXCEPTION SCENARIOS

### 6.1 Input & Data Validation Edge Cases

**EC-1.1: Invalid Configuration Inputs**
- Empty or whitespace-only fields in setup wizard
- Invalid Schedules Direct credentials (wrong username/password)
- Non-existent recording storage path
- Recording path on read-only filesystem
- Invalid HDHomeRun IP address format
- HDHomeRun device IP that doesn't respond

**Handling:**
- Validate all fields before accepting form submission
- Display clear error messages next to invalid fields
- Test SD credentials via API call before saving
- Verify storage path is writable before saving
- Provide example formats for IP addresses

**EC-1.2: Missing or Malformed Guide Data**
- Schedules Direct returns incomplete program data (missing title, time, or channel)
- Program durations are zero or negative
- Episode numbers are malformed (e.g., "S1E0", "S0E0")
- Program times overlap incorrectly
- Series IDs are missing for some programs

**Handling:**
- Implement data validation on guide data import
- Use default values for missing optional fields
- Log data quality issues for investigation
- Display "Information unavailable" in UI for missing data
- Don't crash on malformed data; skip invalid records

**EC-1.3: Search Edge Cases**
- Empty search query
- Search query with only special characters (!@#$%^&*)
- Search query exceeding reasonable length (e.g., > 200 chars)
- Search with no results
- Search returning thousands of results

**Handling:**
- Require minimum 2-character search query
- Sanitize special characters in queries
- Limit search results to reasonable count (e.g., 100 results)
- Show helpful "no results" message with suggestions
- Implement pagination for large result sets

### 6.2 Recording Execution Edge Cases

**EC-2.1: Tuner Availability Issues**
- All tuners in use when recording should start
- Tuner becomes unavailable mid-recording (device reboots)
- Another application (Plex, Kodi, VLC) is using tuners
- User manually tunes channel via HDHomeRun app during recording

**Handling:**
- Queue recording if no tuner available; retry every 30 seconds until padding expires
- Mark recording as failed if no tuner becomes available
- Detect mid-recording tuner loss and mark recording as partial/failed
- Log tuner conflicts for user review
- Consider tuner priority system (DVR vs. live TV) in future

**EC-2.2: Storage Issues**
- Disk full during recording
- Recording directory deleted or permissions changed
- Filesystem errors (I/O errors, bad sectors)
- Network storage becomes unavailable (if using NAS)
- Recording filename conflicts with existing file

**Handling:**
- Check available space before starting recording
- Stop recording gracefully if disk full; mark as failed with error reason
- Verify directory exists and is writable at recording start
- Implement retry logic for transient network storage issues
- Use unique filenames (append timestamp if needed) to avoid conflicts

**EC-2.3: Network & Streaming Issues**
- Network interruption between server and HDHomeRun device
- HDHomeRun device returns error during tuning (channel unavailable, encryption)
- Stream drops frames or packets
- Recording stream ends prematurely (before scheduled end time)
- No video/audio data in stream (blank/corrupted stream)

**Handling:**
- Implement stream buffering to handle brief network hiccups
- Retry tuning if initial attempt fails (up to 3 attempts)
- Log stream quality metrics (dropped packets, bitrate)
- Mark recording as partial if stream ends early
- Validate recorded file size; mark as failed if unexpectedly small

**EC-2.4: Timing Edge Cases**
- Program start time changes after recording is scheduled (guide data update)
- Program is pre-empted or cancelled (sports overtime, breaking news)
- Recording padding causes overlap with next recording on same tuner
- User time zone changes (DST transition)
- System clock is incorrect or drifts

**Handling:**
- Re-check program times before recording starts; adjust if changed
- If program not found at scheduled time, wait for padding duration then fail
- Conflict detection should account for padding when checking overlaps
- Use UTC internally; convert to local time for display only
- Sync system time via NTP for accurate scheduling

### 6.3 Series Recording Edge Cases

**EC-3.1: Series Matching Ambiguity**
- Multiple shows with same title (e.g., "The Office" US vs. UK)
- Show title changes mid-season
- Series ID changes in Schedules Direct data
- Rerun episodes marked as "new" in guide data
- Special episodes with unusual episode numbering (e.g., "S00E01")

**Handling:**
- Use Schedules Direct series ID (not title) for matching
- Require user to select specific series if multiple matches exist
- Log series ID changes and prompt user to verify rule still matches
- Respect original air date for "new episodes only" rules
- Allow user to manually include/exclude special episodes

**EC-3.2: Series Rule Configuration Edge Cases**
- Series rule with time restriction excludes all airings (e.g., "primetime only" but show airs 3 PM)
- Series rule with channel restriction but show moves to different channel
- "New episodes only" but guide data doesn't include original air date
- Series with hundreds of airings (e.g., daily news program)

**Handling:**
- Warn user if rule configuration matches zero upcoming airings
- Allow user to modify rules if show changes channel
- Fall back to recording all episodes if original air date unavailable
- For high-frequency shows, offer additional filters (weekdays only, once per day)

**EC-3.3: Series Rule Conflicts**
- Multiple series rules match same program (overlapping criteria)
- Series rule would schedule conflicting recordings
- User deletes series but recordings already in progress

**Handling:**
- If multiple rules match, use most specific rule or first created
- Conflict detection applies to series-generated recordings same as manual
- Deleting series rule doesn't affect in-progress recordings, only future

### 6.4 UI & Concurrent User Interaction Edge Cases

**EC-4.1: Race Conditions**
- User cancels recording that has already started
- User modifies series rule while matching is in progress
- User deletes recording file manually (outside app) while app tries to access it
- Multiple browser tabs open; action taken in one tab affects data shown in other

**Handling:**
- Check recording status before canceling; don't allow cancel of in-progress recording (or stop recording if allowed)
- Lock series rules during matching operation
- Handle file-not-found errors gracefully; mark recording as deleted
- Implement optimistic UI updates; refresh data periodically

**EC-4.2: Stale Data Display**
- Guide data shown in UI is outdated (overnight refresh not yet run)
- Scheduled recordings list doesn't reflect recent changes
- Conflict warnings persist after conflict is resolved
- Storage space indicator doesn't update after deletion

**Handling:**
- Display last update time prominently
- Implement auto-refresh for dynamic pages (scheduled recordings, status)
- Re-run conflict detection after any schedule change
- Refresh storage stats after recording completion/deletion

### 6.5 External System Failures

**EC-5.1: Schedules Direct API Issues**
- Schedules Direct service is down or unreachable
- API returns HTTP errors (500, 503, rate limiting)
- API response format changes (breaking change)
- User's Schedules Direct subscription expires

**Handling:**
- Continue operating with cached guide data for up to 7 days
- Display warning banner when API is unreachable
- Implement exponential backoff for API retries
- Detect API format changes and log errors for developer review
- Display clear message if subscription expired; link to SD account page

**EC-5.2: HDHomeRun Device Issues**
- Device offline or unreachable (powered off, network issue)
- Device firmware version incompatible with API calls
- Device returns unexpected response format
- Device reboots during recording

**Handling:**
- Periodically ping device to verify connectivity; display status in UI
- Log firmware version; warn if compatibility issues known
- Implement robust error handling for device communication
- Retry recording if device comes back online within padding window

**EC-5.3: System Resource Issues**
- Python process crashes or is killed
- Database file becomes corrupted
- CPU overloaded during multiple concurrent recordings
- Memory exhaustion during guide data refresh

**Handling:**
- Use process supervisor (systemd, supervisord) to auto-restart crashed process
- Implement database backup/restore functionality
- Optimize recording pipeline for low CPU usage (direct stream copy, no transcoding)
- Stream-process guide data rather than loading all into memory
- Implement health check endpoint for monitoring

### 6.6 Boundary Conditions

**BC-6.1: Zero States**
- No HDHomeRun device found on network
- No channels in lineup (or all channels disabled)
- No scheduled recordings
- No recorded content in library
- No search results

**Handling:**
- Display helpful empty states with next-step guidance
- "No device found? Try manual entry or check device power."
- "No recordings scheduled. Browse the guide to find something to record."
- Avoid blank/empty pages; always provide user action

**BC-6.2: Maximum Values**
- Hundreds of scheduled recordings
- Thousands of recordings in library
- Lineup with 100+ channels
- Series rule matching hundreds of airings
- Very long program titles or descriptions (1000+ chars)

**Handling:**
- Implement pagination for large lists
- Use virtualization for long scrollable lists (guide grid)
- Test with maximum realistic data volumes
- Truncate very long text with "read more" expansion
- Set reasonable limits and display warnings when approached

**BC-6.3: Time Boundary Issues**
- Recording scheduled for past time (due to clock skew)
- Recording scheduled beyond guide data availability (> 14 days)
- DST transition during scheduled recording
- Recording spans midnight (start 11:30 PM, end 12:30 AM)

**Handling:**
- Don't allow scheduling recordings in the past; show error
- Warn if scheduling beyond reliable guide data range
- Store times in UTC; convert for display
- Handle date rollover correctly in filename and metadata

---

## 7. API & INTEGRATION REQUIREMENTS

### 7.1 HDHomeRun Device Integration

**INT-1.1: Device Discovery Protocol**
- The system shall implement HDHomeRun device discovery using UDP broadcast
- Discovery packet shall be sent to broadcast address (255.255.255.255) port 65001
- Discovery shall parse response to extract device ID, model, and IP address
- Discovery shall support both automatic broadcast and manual IP entry

**INT-1.2: Device HTTP API**
- The system shall communicate with HDHomeRun device via HTTP API at `http://{device-ip}/`
- Required API endpoints:
  - `/discover.json` - Device information (model, firmware, tuner count, ID)
  - `/lineup.json` - Channel lineup (virtual channels, frequencies, programs)
  - `/tuner{N}/` - Tuner control (status, channel tuning, lock status)
- The system shall parse JSON responses from device API

**INT-1.3: Tuner Control**
- The system shall tune channel via HTTP: `http://{device-ip}/tuner{N}/channel/{channel}`
- The system shall verify tuner lock status before starting stream
- The system shall monitor tuner status during recording (lock, signal strength, signal quality)
- The system shall release tuner after recording: `http://{device-ip}/tuner{N}/channel/none`

**INT-1.4: Stream Capture**
- The system shall retrieve MPEG-TS stream via HTTP: `http://{device-ip}/tuner{N}/`
- Stream shall be read in chunks and written to file continuously
- Stream reading shall be non-blocking to allow monitoring and cancellation
- The system shall handle HTTP stream interruptions and reconnection

**INT-1.5: Device Status Monitoring**
- The system shall periodically check device availability (ping or HTTP GET)
- The system shall track tuner usage (which tuners are in use by this application)
- The system shall detect device offline condition and alert user
- The system shall log device errors for troubleshooting

### 7.2 Schedules Direct Integration

**INT-2.1: Authentication**
- The system shall authenticate with Schedules Direct using username/password
- Authentication endpoint: `https://json.schedulesdirect.org/20141201/token`
- The system shall store and reuse auth token (valid for 24 hours)
- The system shall automatically refresh token when expired

**INT-2.2: Lineup Management**
- The system shall retrieve available lineups for user account
- The system shall retrieve lineup details (stations, channel numbers)
- The system shall support multiple lineups per account (for users with multiple cable/OTA sources)
- API endpoints:
  - `GET /lineups` - Available lineups for account
  - `GET /lineups/{lineup-id}` - Stations in lineup

**INT-2.3: Program Data Retrieval**
- The system shall retrieve program schedules for each station
- Schedule data shall be fetched for 14-day rolling window
- API endpoint: `POST /schedules` (batch request for multiple stations)
- The system shall parse schedule data including:
  - Program ID, air time, duration
  - Station ID

**INT-2.4: Program Metadata Retrieval**
- The system shall retrieve detailed metadata for programs
- API endpoint: `POST /programs` (batch request for multiple program IDs)
- Metadata includes:
  - Title, episode title, description
  - Series ID, episode number (season/episode)
  - Original air date, genres, cast, content rating
  - Show artwork URLs (poster, banner, thumbnail)

**INT-2.5: Efficient Data Synchronization**
- The system shall implement incremental updates (only fetch changed data)
- The system shall use MD5 hashes to detect changed program data
- The system shall respect Schedules Direct rate limits
- The system shall implement exponential backoff on API errors

**INT-2.6: Data Caching Strategy**
- Guide data shall be cached locally in database
- Cache expiration shall be 24 hours (refresh daily)
- Program metadata shall be cached longer (7 days) as it changes infrequently
- The system shall continue operation with stale cache if API unavailable

### 7.3 Database Schema Requirements

**DB-1: Core Entities**

**Stations Table**
- station_id (PRIMARY KEY) - Schedules Direct station ID
- lineup_id - Foreign key to lineup
- callsign - Station callsign (e.g., "WGBH")
- channel_number - Virtual channel number (e.g., "2.1")
- name - Station name
- affiliate - Network affiliation (NBC, CBS, etc.)
- enabled - Boolean flag for user channel selection

**Programs Table**
- program_id (PRIMARY KEY) - Schedules Direct program ID
- series_id - For grouping episodes of same series (nullable for non-series)
- title - Program title
- episode_title - Episode title (nullable)
- description - Long description
- season - Season number (nullable)
- episode - Episode number (nullable)
- original_air_date - Original broadcast date (nullable)
- genres - JSON array of genre tags
- cast_crew - JSON object with cast/crew info
- content_rating - TV-PG, TV-14, etc. (nullable)
- duration_seconds - Program duration
- artwork_url - URL to program artwork (nullable)
- last_updated - Timestamp for cache management

**Schedules Table** (Program Airings)
- schedule_id (PRIMARY KEY)
- program_id (FOREIGN KEY)
- station_id (FOREIGN KEY)
- air_datetime - Start date/time (UTC)
- duration_seconds - Duration of this airing
- is_new - Boolean flag for new episodes vs. reruns
- is_live - Boolean flag for live programming
- audio_properties - JSON (stereo, surround, SAP, etc.)
- video_properties - JSON (HD, SD, 720p, 1080i, etc.)

**Recordings Table** (Scheduled Recordings)
- recording_id (PRIMARY KEY)
- schedule_id (FOREIGN KEY) - Links to specific program airing
- series_rule_id (FOREIGN KEY, nullable) - If created by series rule
- status - ENUM: scheduled, in_progress, completed, failed, cancelled
- padding_start_seconds - Start recording N seconds early
- padding_end_seconds - End recording N seconds late
- tuner_used - Which tuner was used (0-N)
- file_path - Absolute path to recorded file (nullable until recording starts)
- file_size_bytes - Size of recorded file (nullable until complete)
- error_message - Error description if status=failed (nullable)
- created_at - When recording was scheduled
- started_at - When recording actually started (nullable)
- completed_at - When recording finished (nullable)

**SeriesRules Table** (Series Recording Rules)
- rule_id (PRIMARY KEY)
- series_id (FOREIGN KEY)
- title - Series title for display
- record_new_only - Boolean: only record new episodes
- channel_filter - Station ID to restrict to specific channel (nullable)
- time_filter - JSON: time restrictions (e.g., {"start": "19:00", "end": "23:00"})
- keep_limit - Max episodes to keep (nullable = unlimited)
- enabled - Boolean: can be disabled without deleting
- created_at - When rule was created

**Configuration Table** (Key-Value Store)
- key (PRIMARY KEY)
- value - JSON-encoded value
- updated_at

**RecordingLogs Table** (Audit Trail)
- log_id (PRIMARY KEY)
- recording_id (FOREIGN KEY, nullable)
- timestamp
- level - ENUM: info, warning, error
- message - Log message text
- context - JSON object with additional details

### 7.4 File System Organization

**FS-1: Recording File Structure**
```
{recording_storage_path}/
├── {SeriesTitle1}/
│   ├── S01E01 - {EpisodeTitle}.ts
│   ├── S01E02 - {EpisodeTitle}.ts
│   └── S01E03 - {EpisodeTitle}.ts
├── {SeriesTitle2}/
│   └── S02E05 - {EpisodeTitle}.ts
├── Movies/
│   ├── {MovieTitle} (2024-03-15).ts
│   └── {MovieTitle2} (2024-03-20).ts
└── OneTime/
    └── {ProgramTitle} (2024-03-25 20-00).ts
```

**FS-2: Filename Sanitization**
- Remove or replace invalid filesystem characters: `/ \ : * ? " < > |`
- Replace with underscore or remove entirely
- Limit filename length to 255 characters (filesystem limit)
- Handle duplicate filenames by appending counter: `filename (1).ts`

**FS-3: Metadata Sidecar Files (Optional)**
- Create `.nfo` file alongside recording with XML metadata
- NFO format compatible with Plex, Kodi, Emby for media library integration
- Include: title, episode info, description, cast, air date, genre

---

## 8. UI/UX CONSIDERATIONS

### 8.1 Information Architecture

**IA-1: Navigation Structure**
```
Top Navigation Bar:
- Dashboard (Home)
- Program Guide
- Search
- Scheduled Recordings
- Recordings (Library)
- Series Manager
- Settings

Secondary Actions:
- Refresh Guide (icon button)
- System Status (icon with badge for alerts)
```

**IA-2: Page Hierarchy**
- **Dashboard:** Overview, quick access to next recordings, recent activity, system status
- **Program Guide:** Grid or list view of TV schedule
- **Program Detail:** Full information about specific program, all airings, recording actions
- **Search Results:** List of matching programs with quick actions
- **Scheduled Recordings:** List of upcoming recordings, sortable/filterable
- **Conflicts:** Subset of scheduled recordings with conflict warnings
- **Recordings Library:** Completed recordings grouped by series
- **Series Manager:** List of series rules with edit/delete actions
- **Settings:** Configuration pages (tabbed: General, Schedules Direct, Device, Storage)

### 8.2 Key User Flows

**UF-1: Browse and Record Flow**
1. User lands on Dashboard
2. User clicks "Program Guide"
3. User browses grid or searches for show
4. User clicks program to view details
5. User clicks "Record" or "Record Series"
6. Confirmation message appears
7. User navigates to "Scheduled Recordings" to verify

**UF-2: Series Management Flow**
1. User searches for show
2. User clicks "Record Series"
3. Dialog opens with series options (new only, channel, etc.)
4. User configures options and submits
5. User redirected to "Series Manager" showing new rule
6. User can see list of upcoming episodes scheduled by rule

**UF-3: Conflict Resolution Flow**
1. User sees conflict warning badge in navigation
2. User clicks "Scheduled Recordings" or "Conflicts"
3. Conflicting recordings are highlighted with warning icon
4. User clicks into conflict to see details (which recordings overlap, why)
5. User cancels one or more recordings to resolve
6. Warning badge disappears

### 8.3 Visual Design Guidelines

**VD-1: Layout & Spacing**
- Use responsive grid system (CSS Grid or Flexbox)
- Consistent padding/margins: 8px base unit (8, 16, 24, 32px)
- Maximum content width: 1400px for readability
- Sidebar navigation or top horizontal nav (choose based on screen real estate needs)

**VD-2: Typography**
- Use web-safe font stack or Google Fonts (e.g., Inter, Roboto)
- Font sizes: 14px base, 16px body, 20px h3, 24px h2, 32px h1
- Line height: 1.5 for body text, 1.2 for headings
- Font weight: 400 regular, 600 semibold for emphasis, 700 bold for headings

**VD-3: Color Palette**
- Primary color: Used for primary actions (Record button, links)
- Secondary color: Used for secondary actions (Cancel, Edit)
- Success: Green for completed recordings, confirmations
- Warning: Yellow/orange for conflicts, low storage warnings
- Error: Red for failed recordings, errors
- Neutral grays: Background, borders, disabled states
- Ensure color contrast meets WCAG AA (4.5:1 for normal text)

**VD-4: Component Library**
- Buttons: Primary (filled), Secondary (outlined), Tertiary (text-only)
- Form inputs: Text fields, select dropdowns, checkboxes, radio buttons
- Cards: Used for program listings, recording items
- Badges: Used for status indicators (Recording, New, Failed)
- Modals/Dialogs: Used for confirmations, series options
- Toasts/Snackbars: Used for transient feedback messages
- Progress indicators: Spinners for loading, progress bars for storage

### 8.4 Program Guide Design

**PG-1: Grid View**
- **Horizontal axis:** Time (30-min or 1-hour increments)
- **Vertical axis:** Channels (one row per channel)
- **Program blocks:** Span horizontal cells based on duration
- **Visual encoding:**
  - Color coding by genre (optional)
  - Darker background for currently airing programs
  - Icon overlay for scheduled recordings
  - New episode indicator (e.g., "NEW" badge)
- **Interactions:**
  - Click program block to open detail view
  - Right-click or long-press for context menu (Record, Record Series)
  - Scroll horizontally to navigate time
  - Scroll vertically to navigate channels
  - "Jump to now" button to return to current time

**PG-2: List View (Alternative)**
- **Grouping:** By channel or by time
- **Display:** Program title, time, duration, description preview
- **Interactions:** Click to expand full details, Record button inline

**PG-3: Responsive Behavior**
- Desktop: Full grid view with 4-6 hour window, 20+ channels visible
- Tablet: Narrower grid (2-3 hours) or list view
- Mobile: List view only, grouped by time or channel

### 8.5 Accessibility Features

**A11Y-1: Keyboard Navigation**
- All interactive elements focusable via Tab key
- Enter/Space activates buttons and links
- Arrow keys navigate program guide grid
- Esc closes modals/dialogs
- Focus indicators clearly visible (outline, highlight)

**A11Y-2: Screen Reader Support**
- Semantic HTML (nav, main, aside, article, section)
- ARIA labels for icon-only buttons
- ARIA live regions for dynamic content updates (recording started, guide refreshed)
- Alt text for program artwork images
- Table structure for program guide grid (if using <table>)

**A11Y-3: Visual Accessibility**
- Color contrast ratios meet WCAG AA (4.5:1 normal text, 3:1 large text)
- Don't rely solely on color to convey information (use icons, text labels)
- Text resizable up to 200% without breaking layout
- Focus indicators visible for keyboard users

**A11Y-4: Mobile Accessibility**
- Touch targets ≥ 44x44 pixels
- Swipe gestures optional, not required (provide button alternatives)
- Zoom enabled (no viewport user-scalable=no)

### 8.6 Error Handling & Feedback

**EF-1: Form Validation**
- Inline validation messages below invalid fields
- Red border or icon to indicate error
- Disable submit button until form is valid (or allow submit and show errors)
- Show success confirmation after successful form submission

**EF-2: Loading States**
- Show spinner or skeleton UI while loading data
- Disable buttons during API calls to prevent double-submission
- Display progress indicators for long operations (guide refresh, channel scan)

**EF-3: Error Messages**
- User-friendly language (avoid technical jargon unless necessary)
- Actionable: Tell user what went wrong and how to fix it
- Examples:
  - ❌ "API call failed with status 500"
  - ✅ "Unable to connect to Schedules Direct. Please check your internet connection and try again."
- Display errors persistently (not disappearing toasts) for critical issues
- Provide "Try Again" button where appropriate

**EF-4: Success Confirmations**
- Show transient success message (toast/snackbar) for actions: "Recording scheduled", "Series rule created", "Recording deleted"
- Update UI immediately (optimistic updates) before server confirms
- Revert UI change if server returns error

### 8.7 Performance Optimization

**PERF-1: Page Load Optimization**
- Minimize initial page payload (lazy load non-critical JS/CSS)
- Use CDN for static assets (if applicable)
- Compress assets (gzip/brotli)
- Cache static resources with appropriate headers

**PERF-2: Program Guide Optimization**
- Render only visible time window (4-6 hours), load more on scroll
- Use virtual scrolling for long channel lists
- Optimize DOM structure (minimize nested elements)
- Debounce scroll events

**PERF-3: Search Optimization**
- Debounce search input (wait 300ms after typing stops before querying)
- Show loading indicator during search
- Cache recent search results client-side
- Limit results to reasonable count (100-200)

**PERF-4: Image Optimization**
- Use responsive images (srcset) for program artwork
- Lazy load images (loading="lazy")
- Serve images in modern formats (WebP) with fallbacks
- Cache images aggressively (long expiration headers)

---

## 9. DEVELOPMENT ROADMAP & PRIORITIZATION

### Phase 1: Foundation (MVP Core)

**Milestone 1.1: Project Setup & Architecture**
- [ ] Initialize Python project with FastAPI, Jinja2, SQLAlchemy
- [ ] Set up database schema and migrations (Alembic)
- [ ] Configure development environment (venv, dependencies)
- [ ] Implement basic web UI structure (base templates, navigation)
- [ ] Implement configuration management (settings.py, env vars)

**Milestone 1.2: HDHomeRun Integration**
- [ ] Implement device discovery (UDP broadcast)
- [ ] Implement device HTTP API client (discover, lineup, tuner control)
- [ ] Implement MPEG-TS stream capture and file writing
- [ ] Create tuner management service (availability tracking)
- [ ] Test with physical HDHomeRun device

**Milestone 1.3: Schedules Direct Integration**
- [ ] Implement authentication and token management
- [ ] Implement lineup retrieval
- [ ] Implement program schedule retrieval (batch API)
- [ ] Implement program metadata retrieval
- [ ] Implement guide data caching and database storage
- [ ] Create background task for daily guide refresh

**Milestone 1.4: Program Guide UI**
- [ ] Create program guide grid view (HTML/CSS/JS)
- [ ] Implement time navigation (forward/backward)
- [ ] Implement channel filtering
- [ ] Create program detail page
- [ ] Display program metadata from database

**Milestone 1.5: One-Time Recording**
- [ ] Implement "Schedule Recording" action (UI + backend)
- [ ] Create "Scheduled Recordings" list page
- [ ] Implement recording scheduler (background service)
- [ ] Implement recording execution (tune, stream, write file)
- [ ] Implement recording status tracking (scheduled → in progress → completed)
- [ ] Test end-to-end recording flow

### Phase 2: Core Features

**Milestone 2.1: Series Recording**
- [ ] Create series rule creation UI (dialog with options)
- [ ] Implement series rule matching logic (match programs to rules)
- [ ] Create "Series Manager" page
- [ ] Implement rule editing and deletion
- [ ] Implement automatic scheduling of episodes based on rules

**Milestone 2.2: Search Functionality**
- [ ] Implement search API endpoint (query database)
- [ ] Create search UI (search box, results page)
- [ ] Implement search filters (date, channel, genre)
- [ ] Add search result actions (record, record series)
- [ ] Optimize search performance (database indexes)

**Milestone 2.3: Conflict Detection & Resolution**
- [ ] Implement conflict detection algorithm (overlap + tuner count)
- [ ] Create "Conflicts" page showing overlapping recordings
- [ ] Highlight conflicts in "Scheduled Recordings" list
- [ ] Implement manual conflict resolution (cancel recordings)
- [ ] Test conflict scenarios (multiple overlaps, tuner exhaustion)

**Milestone 2.4: Recording Library**
- [ ] Create "Recordings" page listing completed recordings
- [ ] Implement grouping by series
- [ ] Implement recording deletion (file + database)
- [ ] Display storage usage and disk space
- [ ] Implement recording metadata display

### Phase 3: Polish & Enhancement

**Milestone 3.1: System Monitoring**
- [ ] Create Dashboard page with system overview
- [ ] Display HDHomeRun device status and tuner availability
- [ ] Display next scheduled recording
- [ ] Display recent recording activity/history
- [ ] Implement logging viewer in UI

**Milestone 3.2: Settings & Configuration**
- [ ] Create Settings page with tabs (General, Device, SD, Storage)
- [ ] Implement configuration editing UI
- [ ] Implement default recording padding settings
- [ ] Implement channel enable/disable management
- [ ] Implement lineup management (add/remove)

**Milestone 3.3: Error Handling & Resilience**
- [ ] Implement comprehensive error handling (try/catch, logging)
- [ ] Implement retry logic for transient failures
- [ ] Implement graceful degradation (offline mode with cached data)
- [ ] Add health check endpoint
- [ ] Improve error messages throughout UI

**Milestone 3.4: UI/UX Refinement**
- [ ] Responsive design implementation (mobile, tablet support)
- [ ] Accessibility audit and fixes (WCAG AA compliance)
- [ ] Loading states and progress indicators
- [ ] Visual design polish (consistent colors, spacing, typography)
- [ ] User testing and feedback incorporation

**Milestone 3.5: Testing & Documentation**
- [ ] Write unit tests for core logic (recording scheduler, series matching, conflict detection)
- [ ] Write integration tests (API clients, database operations)
- [ ] Write end-to-end test scenarios (recording lifecycle)
- [ ] Document API endpoints (OpenAPI/Swagger)
- [ ] Write user documentation (setup guide, user manual)
- [ ] Create installation scripts and deployment documentation

### Phase 4: Future Enhancements (Post-MVP)

These are explicitly out of scope for MVP but documented for future consideration:

- **Playback Integration:** In-browser video player for watching recordings
- **Transcoding Support:** Convert MPEG-TS to MP4/H.264 for compatibility and space savings
- **Commercial Detection/Skipping:** Analyze recordings to detect and mark commercials
- **Multiple User Profiles:** Support for separate user accounts with individual preferences
- **Remote Access:** Enable secure internet access to DVR (authentication, SSL)
- **Mobile Apps:** Native iOS/Android apps for remote scheduling
- **Smart Recording:** Priority system, auto-delete watched episodes, disk space management
- **Notifications:** Email/push notifications for recording failures or important events
- **Advanced Analytics:** Recording statistics, viewing history, trends
- **Integration with Media Servers:** Better Plex/Kodi/Emby integration with metadata sync

---

## 10. TECHNICAL ARCHITECTURE OVERVIEW

### 10.1 System Components

**Component 1: Web Application (FastAPI)**
- FastAPI application serving HTTP endpoints
- Jinja2 template rendering for HTML pages
- Static file serving (CSS, JavaScript, images)
- RESTful API endpoints for AJAX operations
- WebSocket support for real-time updates (optional)

**Component 2: Database Layer (SQLAlchemy + SQLite)**
- SQLite database file for data persistence
- SQLAlchemy ORM for database access
- Alembic for schema migrations
- Database models: Station, Program, Schedule, Recording, SeriesRule, Config

**Component 3: Recording Scheduler (Background Service)**
- Continuous loop checking for upcoming recordings
- Starts recordings at scheduled time (minus padding)
- Monitors active recordings
- Updates recording status in database
- Handles recording completion and cleanup

**Component 4: HDHomeRun Client**
- Device discovery via UDP broadcast
- HTTP API client for device communication
- Tuner control (tune, status, release)
- MPEG-TS stream capture
- Error handling and retry logic

**Component 5: Schedules Direct Client**
- Authentication and token management
- Lineup and station data retrieval
- Program schedule and metadata retrieval
- Incremental sync with MD5 hash checking
- Rate limiting and error handling

**Component 6: Background Tasks (Celery or APScheduler)**
- Daily guide data refresh task
- Series rule matching task (after guide refresh)
- Storage cleanup task (apply retention rules)
- Device health check task
- Log rotation task

### 10.2 Technology Stack

**Backend:**
- Python 3.9+
- FastAPI (web framework)
- Uvicorn (ASGI server)
- SQLAlchemy (ORM)
- Alembic (database migrations)
- Pydantic (data validation)
- APScheduler (background tasks) or Celery (if more complex)
- Requests or httpx (HTTP client for APIs)

**Frontend:**
- Jinja2 templates (server-side rendering)
- HTML5, CSS3
- JavaScript (vanilla or lightweight library like Alpine.js)
- CSS framework (Bootstrap, Tailwind, or custom)
- Minimal JavaScript for interactivity (AJAX, form handling, dynamic updates)

**Database:**
- SQLite (development and production for single-user)
- Option to support PostgreSQL/MySQL for advanced users

**Deployment:**
- Systemd service (Linux)
- Docker container (optional)
- Windows service (optional, using NSSM or similar)

**Development Tools:**
- Git (version control)
- pytest (testing)
- Black (code formatting)
- pylint/flake8 (linting)
- mypy (type checking)

### 10.3 Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│                 User Browser                    │
│              (Desktop/Mobile)                   │
└───────────────────┬─────────────────────────────┘
                    │ HTTP/HTTPS
                    │
┌───────────────────▼─────────────────────────────┐
│            FastAPI Web Application              │
│  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Web Routes   │  │ Background Scheduler    │ │
│  │ (Jinja2)     │  │ (Recording Engine)      │ │
│  └──────────────┘  └─────────────────────────┘ │
│  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ API Clients  │  │ Background Tasks        │ │
│  │ (HDHR, SD)   │  │ (Guide Refresh)         │ │
│  └──────────────┘  └─────────────────────────┘ │
└─────────────┬───────────────────────┬───────────┘
              │                       │
┌─────────────▼──────────┐  ┌─────────▼──────────┐
│  SQLite Database       │  │ Local Filesystem   │
│  (Config, Guide,       │  │ (Recordings)       │
│   Recordings)          │  │                    │
└────────────────────────┘  └────────────────────┘
              │                       │
┌─────────────▼──────────┐  ┌─────────▼──────────┐
│ Schedules Direct API   │  │ HDHomeRun Device   │
│ (HTTPS)                │  │ (Local Network)    │
└────────────────────────┘  └────────────────────┘
```

### 10.4 Data Flow Examples

**Example 1: User Schedules Recording**
1. User clicks "Record" button in program guide
2. Browser sends POST request to `/api/recordings/schedule`
3. FastAPI route validates input, checks for conflicts
4. If no conflict, creates Recording entry in database with status="scheduled"
5. Returns success response to browser
6. Browser shows success toast and updates UI
7. Background scheduler detects new recording on next iteration
8. At scheduled time, scheduler tunes HDHomeRun and starts stream capture

**Example 2: Daily Guide Refresh**
1. APScheduler triggers guide refresh task at 3 AM
2. Task authenticates with Schedules Direct, gets token
3. Task fetches schedules for all stations (next 14 days)
4. Task compares MD5 hashes to detect changed programs
5. Task fetches metadata for new/changed programs
6. Task updates database (insert/update Program and Schedule records)
7. Task triggers series rule matching
8. Series rule matcher identifies new episodes matching active rules
9. New recordings are automatically scheduled
10. Task logs completion and updates last_refresh timestamp

**Example 3: Recording Execution**
1. Scheduler checks database every 10 seconds for upcoming recordings
2. At recording time (minus start padding), scheduler claims recording
3. Scheduler checks tuner availability via HDHomeRun API
4. If tuner available, tunes to channel: POST /tuner0/channel/{channel}
5. Verifies tuner lock status, waits up to 10 seconds for lock
6. Opens HTTP stream: GET /tuner0/ (returns MPEG-TS)
7. Writes stream chunks to file: `{storage_path}/{series}/{filename}.ts`
8. Updates recording status to "in_progress" in database
9. Monitors stream for errors, logs any dropouts
10. At scheduled end time (plus end padding), closes stream
11. Releases tuner: POST /tuner0/channel/none
12. Verifies file size, marks recording as "completed" or "failed"
13. Updates database with final status, file path, size

---

## 11. RISK ANALYSIS & MITIGATION

### Risk 1: HDHomeRun Device Compatibility
**Description:** HDHomeRun devices have varying models with different capabilities and API versions. Direct HTTP/UDP implementation may not work across all models.

**Probability:** Medium
**Impact:** High (blocks core functionality)
**Mitigation:**
- Test with multiple HDHomeRun models (CONNECT, EXTEND, FLEX, PRIME)
- Document supported models
- Implement version detection and handle API differences
- Provide fallback to manual device configuration if discovery fails
- Monitor HDHomeRun developer forums for API changes

### Risk 2: Schedules Direct API Changes
**Description:** Schedules Direct API may change format, rate limits, or availability, breaking integration.

**Probability:** Low
**Impact:** High (no guide data = unusable)
**Mitigation:**
- Use stable API version (20141201) documented by Schedules Direct
- Implement robust error handling and logging for API calls
- Cache guide data locally for up to 7 days as fallback
- Monitor Schedules Direct announcements for breaking changes
- Join Schedules Direct developer community for advance notice

### Risk 3: Recording Reliability
**Description:** Network interruptions, device reboots, or software bugs may cause failed or corrupted recordings.

**Probability:** Medium
**Impact:** High (user frustration, defeats purpose of DVR)
**Mitigation:**
- Implement comprehensive error handling and retry logic
- Log all recording events (start, stop, errors) for troubleshooting
- Validate recorded files (check size, duration)
- Provide clear failure notifications with error reasons
- Test extensively with long-duration recordings and concurrent recordings
- Implement stream buffering to handle brief network hiccups

### Risk 4: Storage Exhaustion
**Description:** Recordings consume large amounts of disk space; disk full condition crashes recordings.

**Probability:** Medium
**Impact:** Medium (new recordings fail until space freed)
**Mitigation:**
- Display storage usage prominently in UI
- Warn user when free space falls below threshold (e.g., 10GB)
- Fail gracefully on disk-full: stop recording, mark as failed, alert user
- Implement optional automatic cleanup (delete oldest recordings when space low)
- Document storage requirements (typical 1-4 GB per hour of HD content)

### Risk 5: Concurrency & Race Conditions
**Description:** Multiple background threads (scheduler, guide refresh, series matching) may conflict or cause database corruption.

**Probability:** Medium
**Impact:** Medium (data inconsistency, failed recordings)
**Mitigation:**
- Use database transactions for critical operations
- Implement proper locking for shared resources (tuner allocation)
- Test concurrent operations (multiple recordings + guide refresh)
- Use thread-safe data structures
- Implement idempotency for background tasks (safe to run multiple times)

### Risk 6: Series Matching Accuracy
**Description:** Series matching logic may fail to correctly identify episodes, causing missed recordings or duplicates.

**Probability:** Medium
**Impact:** Medium (missed episodes, wasted storage on duplicates)
**Mitigation:**
- Use Schedules Direct series ID (not title matching) for reliability
- Implement logging of series matching decisions for debugging
- Allow user to manually skip/include episodes (override matching)
- Test with various series types (daily shows, specials, multi-part episodes)
- Provide UI to view all episodes matched by a rule

### Risk 7: Configuration Complexity
**Description:** Initial setup may be too complex for non-technical users, leading to misconfiguration.

**Probability:** Low (target user is technical)
**Impact:** Medium (setup abandoned or incorrect)
**Mitigation:**
- Implement guided setup wizard with validation
- Provide clear error messages for invalid configuration
- Include screenshots in documentation
- Test setup process with fresh installations
- Provide sane defaults where possible

### Risk 8: Performance Degradation
**Description:** Large guide data or recording libraries may cause slow page loads or database queries.

**Probability:** Low
**Impact:** Low (usability suffers but not broken)
**Mitigation:**
- Implement database indexes on frequently queried fields
- Use pagination for large lists (recordings, search results)
- Profile database queries and optimize slow ones
- Test with realistic data volumes (100 channels, 1000+ recordings)
- Implement caching for expensive computations

### Risk 9: Time Zone & DST Issues
**Description:** Time zone handling errors may cause recordings to start at wrong time or fail.

**Probability:** Low
**Impact:** High (recordings missed)
**Mitigation:**
- Store all times in UTC internally
- Convert to local time only for display
- Use timezone-aware datetime objects (Python pytz or zoneinfo)
- Test around DST transitions (spring forward, fall back)
- Document time zone assumptions

### Risk 10: Security Vulnerabilities
**Description:** Web interface may be vulnerable to attacks (XSS, CSRF, SQL injection).

**Probability:** Low (local network deployment)
**Impact:** Medium (data loss, configuration tampering)
**Mitigation:**
- Use parameterized queries (SQLAlchemy ORM) to prevent SQL injection
- Implement CSRF protection in forms (FastAPI built-in)
- Sanitize user inputs (filename paths, search queries)
- Escape output in Jinja2 templates (automatic escaping)
- Conduct security review before release
- Document deployment as local-only (not internet-exposed)

---

## 12. OPEN QUESTIONS & DECISIONS NEEDED

### Question 1: Database Choice
**Question:** Should we commit to SQLite or abstract database to support PostgreSQL/MySQL?

**Options:**
- A) SQLite only (simpler, no separate DB server)
- B) Abstract via SQLAlchemy to support multiple databases

**Recommendation:** Start with SQLite (MVP), use SQLAlchemy ORM to allow future DB swapping. Document that SQLite is default but PostgreSQL can be used for advanced deployments.

### Question 2: Recording File Naming Convention
**Question:** What file naming pattern should be used for recordings?

**Current Proposal:** `{SeriesTitle}/S{season:02d}E{episode:02d} - {EpisodeTitle}.ts`

**Considerations:**
- Compatibility with Plex/Kodi naming conventions
- Handling of non-episodic content (movies, news, sports)
- Handling of missing episode numbers

**Recommendation:** Use proposed convention for series; use `{ProgramTitle} ({AirDate}).ts` for non-episodic content. Document naming convention and provide configuration option to customize.

### Question 3: Conflict Resolution Strategy
**Question:** Should the system support automatic conflict resolution (priority-based) or only manual resolution?

**Current Scope:** Manual resolution only (MVP)

**Future Consideration:** Allow users to assign priorities to series rules; system auto-cancels lower-priority recordings when conflict occurs.

**Decision:** Manual resolution for MVP. Document priority system as future enhancement.

### Question 4: Recording Padding Defaults
**Question:** What should default padding values be?

**Options:**
- A) 0 minutes start, 0 minutes end (exact schedule)
- B) 1 minute start, 2 minutes end (conservative)
- C) 2 minutes start, 5 minutes end (generous)

**Recommendation:** Default to 1 minute early, 2 minutes late (option B). Allow user to configure in settings. Document that padding increases conflict likelihood.

### Question 5: Failed Recording Retention
**Question:** Should failed or partial recordings be automatically deleted or kept for user review?

**Options:**
- A) Keep all failed recordings (user manually deletes)
- B) Keep partial recordings, delete if file size is 0 bytes
- C) Automatically delete all failed recordings after 7 days

**Recommendation:** Keep partial recordings (option B) for user review. Display failed recordings prominently in UI. Provide option to delete all failed recordings.

### Question 6: Multiple HDHomeRun Devices
**Question:** Should the system support multiple HDHomeRun devices for increased tuner capacity?

**Current Scope:** Single device (MVP)

**Future Consideration:** Allow multiple devices; pool tuners across devices for recording.

**Decision:** Single device for MVP. Document multi-device support as future enhancement.

### Question 7: Program Guide Time Range
**Question:** How much time should the program guide display by default?

**Options:**
- A) 3 hours (compact, easier to navigate)
- B) 4 hours (balance)
- C) 6 hours (more overview, more scrolling)

**Recommendation:** Default to 4 hours (option B). Allow user to switch between 3h/4h/6h views. Ensure guide is performant even at 6h view.

### Question 8: Logging Verbosity
**Question:** What level of logging detail is appropriate for production use?

**Options:**
- A) Minimal (only errors and critical events)
- B) Moderate (info level: recording start/stop, guide refresh, errors)
- C) Verbose (debug level: all API calls, database queries, decisions)

**Recommendation:** Default to moderate (option B). Provide configuration option to enable debug logging for troubleshooting. Implement log rotation to prevent unbounded growth.

### Question 9: Systemd vs. Standalone Service
**Question:** How should the background recording service run?

**Options:**
- A) Part of web application process (single process)
- B) Separate service process (two processes communicating via database)

**Recommendation:** Part of web application (option A) using FastAPI background tasks or APScheduler. Simpler deployment, fewer moving parts. If scalability issues arise, can split later.

### Question 10: Initial Release Scope
**Question:** Should any SHOULD-priority features be cut to accelerate MVP release?

**Features to Consider:**
- Recording library management (view/delete completed recordings)
- Series rule editing (delete only, not edit)
- System status dashboard (basic status only, not full dashboard)

**Recommendation:** Include all SHOULD features for complete MVP experience. Recording library management is essential for disk space management. Series editing is important for rule correction. Status dashboard aids troubleshooting.

---

## 13. SUMMARY & NEXT STEPS

### 13.1 Key Decisions Recap

**Project Scope:**
- MVP focused on core scheduling and management
- No playback functionality (use external players)
- Single-user, local network deployment
- MPEG-TS recording format (no transcoding)
- Local filesystem storage

**Technology Stack:**
- Backend: FastAPI + Python 3.9+
- Frontend: Jinja2 templates + vanilla JavaScript
- Database: SQLite (with SQLAlchemy ORM)
- Deployment: Systemd service (Linux) or standalone process

**Integration Approach:**
- Direct HTTP/UDP communication with HDHomeRun devices
- Schedules Direct JSON API for guide data
- Daily guide refresh with local caching

### 13.2 Requirements Completeness Checklist

- [x] Functional requirements documented (FR-1 through FR-9)
- [x] Non-functional requirements documented (NFR-P, NFR-SC, NFR-R, NFR-U, NFR-S, NFR-M, NFR-PO)
- [x] User stories organized by epic with MoSCoW prioritization
- [x] Success criteria defined (technical, UX, business/project)
- [x] Edge cases and exception scenarios identified (6 categories, 20+ scenarios)
- [x] API integration requirements documented (HDHomeRun, Schedules Direct)
- [x] Database schema defined (7 tables with relationships)
- [x] UI/UX considerations documented (navigation, flows, design guidelines)
- [x] Development roadmap with phased milestones
- [x] Technical architecture overview
- [x] Risk analysis with mitigation strategies
- [x] Open questions documented for resolution

### 13.3 Recommended Next Steps

**Immediate Actions (Before Development):**

1. **Resolve Open Questions:** Review open questions section and make final decisions on:
   - Recording file naming convention
   - Default padding values
   - Failed recording retention policy
   - Program guide default time range

2. **Validate Technical Feasibility:**
   - Acquire or borrow HDHomeRun device for testing
   - Register Schedules Direct trial account
   - Test HDHomeRun HTTP API with curl/Postman
   - Test Schedules Direct API with sample requests

3. **Set Up Development Environment:**
   - Initialize Git repository
   - Create Python virtual environment
   - Install FastAPI, SQLAlchemy, and dependencies
   - Set up project structure (folders for models, routes, services, templates)

4. **Create Project Documentation:**
   - README.md with project overview and setup instructions
   - CONTRIBUTING.md with development guidelines
   - LICENSE file (choose appropriate license)
   - Architecture diagram (draw system components and data flow)

**Phase 1 Development (Weeks 1-4):**

5. **Build Foundation:**
   - Implement database schema and migrations
   - Create basic FastAPI application structure
   - Implement configuration management
   - Build initial HTML templates and navigation

6. **Implement HDHomeRun Integration:**
   - Build device discovery and HTTP API client
   - Test tuner control and stream capture
   - Verify recording file writing

7. **Implement Schedules Direct Integration:**
   - Build authentication and API client
   - Implement guide data sync
   - Test data caching in database

8. **Build Program Guide UI:**
   - Create guide grid view
   - Implement time navigation
   - Build program detail page

**Phase 2 Development (Weeks 5-8):**

9. **Implement Recording Features:**
   - Build recording scheduler service
   - Implement one-time recording
   - Implement series recording rules and matching
   - Test end-to-end recording workflow

10. **Build Management UIs:**
    - Scheduled recordings list
    - Series manager
    - Recording library (view/delete)
    - Search functionality

11. **Implement Conflict Detection:**
    - Build conflict detection algorithm
    - Create conflict resolution UI
    - Test various conflict scenarios

**Phase 3 Polish (Weeks 9-10):**

12. **Testing & Bug Fixes:**
    - Write unit tests for core logic
    - Perform integration testing
    - Fix bugs discovered during testing
    - Test on target operating systems

13. **UI/UX Refinement:**
    - Responsive design implementation
    - Accessibility improvements
    - Visual design polish
    - User testing (if possible)

14. **Documentation & Release:**
    - Complete user documentation
    - Write deployment guide
    - Create installation scripts
    - Tag v1.0.0 release

### 13.4 Success Metrics to Track During Development

- **Code Coverage:** Target 70%+ test coverage for critical modules
- **Recording Success Rate:** Monitor during testing, target 95%+
- **Performance Benchmarks:** Measure page load times, search response times
- **Bug Count:** Track and resolve bugs discovered during testing
- **Documentation Completeness:** Ensure all user-facing features are documented

### 13.5 Stakeholder Communication Plan

As a personal project, stakeholder communication is simpler, but consider:

- **Development Log:** Keep notes or blog posts documenting progress and decisions
- **Commit Messages:** Write clear, descriptive commit messages for future reference
- **GitHub Issues:** Use issues to track bugs, feature ideas, and questions (even if working solo)
- **Release Notes:** Document changes and new features with each release

---

## APPENDIX A: GLOSSARY

**DVR (Digital Video Recorder):** Electronic device that records video content to digital storage medium.

**EPG (Electronic Program Guide):** Digital TV guide showing current and upcoming programs.

**HDHomeRun:** Network-attached TV tuner device manufactured by SiliconDust.

**MPEG-TS (MPEG Transport Stream):** Container format for digital audio and video, commonly used for broadcast television.

**OTA (Over-The-Air):** Broadcast television signals received via antenna (not cable/satellite).

**Schedules Direct:** Non-profit service providing TV guide data via subscription.

**Series ID:** Unique identifier for a TV series, used to group episodes across seasons.

**Tuner:** Hardware component that receives and decodes TV signals. HDHomeRun devices have 1-4 tuners.

**Padding:** Extra time added before/after scheduled recording to avoid missing content due to schedule inaccuracies.

**Lineup:** Collection of channels available in a specific geographic area or cable system.

**Station:** Broadcast TV station (e.g., "WGBH", "NBC Boston"). Maps to channel numbers in lineup.

**Airing:** Specific broadcast of a program at a particular date/time on a channel.

**Series Rule:** User-defined rule to automatically record all episodes of a TV series.

---

## APPENDIX B: REFERENCE LINKS

**HDHomeRun Resources:**
- HDHomeRun Developer Documentation: https://www.silicondust.com/support/hdhomerun/
- HDHomeRun HTTP API Reference: https://github.com/Silicondust/libhdhomerun
- HDHomeRun Forums: https://forum.silicondust.com/

**Schedules Direct Resources:**
- Schedules Direct Website: https://www.schedulesdirect.org/
- Schedules Direct JSON API Wiki: https://github.com/SchedulesDirect/JSON-Service/wiki
- API Sample Code: https://github.com/SchedulesDirect/

**Technical Standards:**
- MPEG-TS Specification: ISO/IEC 13818-1
- WCAG 2.1 Accessibility Guidelines: https://www.w3.org/WAI/WCAG21/quickref/

**Development Tools:**
- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Jinja2 Documentation: https://jinja.palletsprojects.com/

---

**END OF REQUIREMENTS DOCUMENT**

This requirements document should be treated as a living document and updated as:
- Technical decisions are finalized
- New requirements are discovered during development
- User feedback necessitates changes
- Post-MVP features are promoted to active development

Next update scheduled: After Phase 1 completion or when significant scope changes occur.
