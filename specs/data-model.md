# PyHDHRDVR Data Model Specification

**Version:** 1.0
**Date:** 2025-10-31
**Status:** Draft

---

## Table of Contents
1. [Overview](#overview)
2. [Entity Relationship Diagram](#entity-relationship-diagram)
3. [Core Entities](#core-entities)
4. [Enumerations](#enumerations)
5. [Indexes and Performance](#indexes-and-performance)
6. [Validation Rules](#validation-rules)
7. [Data Relationships](#data-relationships)

---

## Overview

This document defines the complete data model for the PyHDHRDVR application. The model supports:
- TV guide data from Schedules Direct
- HDHomeRun device configuration
- Recording schedules (one-time and series)
- Recording execution tracking
- System configuration

**Database Technology:** SQLite (primary), with SQLAlchemy ORM for portability to PostgreSQL/MySQL

---

## Entity Relationship Diagram

```
┌─────────────────┐
│   Configuration │
│   (Key-Value)   │
└─────────────────┘

┌─────────────────┐        ┌──────────────────┐        ┌─────────────────┐
│     Lineup      │───<───>│     Station      │───<────│   Schedule      │
│                 │        │                  │        │   (Airing)      │
└─────────────────┘        └─────┬────────────┘        └────┬────────────┘
                                 │                          │
                                 │                          │
                           ┌─────▼────────────┐            │
                           │     Program      │◄───────────┘
                           │                  │
                           └─────┬────────────┘
                                 │
                                 │ series_id
                                 │
┌─────────────────┐        ┌─────▼────────────┐        ┌─────────────────┐
│   SeriesRule    │────────│    Recording     │◄───────│   Schedule      │
│                 │ 1:N    │                  │  N:1   │   (Airing)      │
└─────────────────┘        └──────────────────┘        └─────────────────┘
                                 │
                                 │
                           ┌─────▼────────────┐
                           │  RecordingLog    │
                           │                  │
                           └──────────────────┘

┌─────────────────┐
│     Device      │
│  (HDHomeRun)    │
└─────────────────┘
```

---

## Core Entities

### 1. Station

Represents a broadcast TV station/channel.

**Table Name:** `stations`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| station_id | VARCHAR(32) | PRIMARY KEY | Schedules Direct station ID |
| lineup_id | VARCHAR(32) | NOT NULL | Foreign key to lineup |
| callsign | VARCHAR(16) | NOT NULL | Station callsign (e.g., "WGBH") |
| channel_number | VARCHAR(16) | NOT NULL | Virtual channel (e.g., "2.1") |
| name | VARCHAR(128) | NOT NULL | Station full name |
| affiliate | VARCHAR(32) | NULL | Network affiliation (NBC, CBS, etc.) |
| enabled | BOOLEAN | NOT NULL DEFAULT TRUE | User can disable channels |
| logo_url | VARCHAR(512) | NULL | URL to station logo |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Record creation time |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Last update time |

**Indexes:**
- PRIMARY KEY on `station_id`
- INDEX on `lineup_id`
- INDEX on `channel_number`
- INDEX on `enabled`

**Business Rules:**
- `channel_number` must be unique within a lineup
- `callsign` should be uppercase
- Disabled stations are hidden from guide but historical data retained

---

### 2. Program

Represents a TV program (show, movie, episode metadata).

**Table Name:** `programs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| program_id | VARCHAR(32) | PRIMARY KEY | Schedules Direct program ID |
| series_id | VARCHAR(32) | NULL | Groups episodes of same series |
| title | VARCHAR(256) | NOT NULL | Program title |
| episode_title | VARCHAR(256) | NULL | Episode title (for series) |
| description | TEXT | NULL | Full description/synopsis |
| short_description | VARCHAR(512) | NULL | Brief description for lists |
| season | INTEGER | NULL | Season number |
| episode | INTEGER | NULL | Episode number within season |
| original_air_date | DATE | NULL | Original broadcast date |
| genres | JSON | NOT NULL DEFAULT '[]' | Array of genre strings |
| cast_crew | JSON | NULL | Object with cast/crew arrays |
| content_rating | VARCHAR(16) | NULL | TV-PG, TV-14, R, etc. |
| duration_seconds | INTEGER | NOT NULL | Program duration in seconds |
| artwork_url | VARCHAR(512) | NULL | URL to program poster/image |
| is_movie | BOOLEAN | NOT NULL DEFAULT FALSE | True if movie, false if series |
| is_sports | BOOLEAN | NOT NULL DEFAULT FALSE | True if sports program |
| md5_hash | VARCHAR(32) | NULL | For detecting metadata changes |
| last_updated | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Cache management |

**Indexes:**
- PRIMARY KEY on `program_id`
- INDEX on `series_id`
- INDEX on `title`
- INDEX on `original_air_date`
- FULLTEXT INDEX on `title, episode_title, description` (for search)

**Business Rules:**
- Series programs must have `series_id`
- Movies typically have `season` and `episode` as NULL
- `genres` is JSON array: `["Drama", "Comedy"]`
- `cast_crew` is JSON object: `{"cast": ["Actor 1", "Actor 2"], "director": ["Director Name"]}`
- `duration_seconds` must be positive

---

### 3. Schedule (Airing)

Represents a specific airing of a program on a station at a particular time.

**Table Name:** `schedules`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| schedule_id | VARCHAR(64) | PRIMARY KEY | Composite: {station_id}_{air_datetime}_{program_id} |
| program_id | VARCHAR(32) | NOT NULL, FOREIGN KEY | Links to programs table |
| station_id | VARCHAR(32) | NOT NULL, FOREIGN KEY | Links to stations table |
| air_datetime | DATETIME | NOT NULL | Start time (UTC) |
| duration_seconds | INTEGER | NOT NULL | Duration of this specific airing |
| is_new | BOOLEAN | NOT NULL DEFAULT FALSE | New episode vs rerun |
| is_live | BOOLEAN | NOT NULL DEFAULT FALSE | Live programming flag |
| is_premiere | BOOLEAN | NOT NULL DEFAULT FALSE | Season/series premiere |
| is_finale | BOOLEAN | NOT NULL DEFAULT FALSE | Season/series finale |
| audio_properties | JSON | NULL | ["stereo", "surround", "SAP"] |
| video_properties | JSON | NULL | ["HD", "1080i", "720p"] |
| part_number | INTEGER | NULL | For multi-part episodes (part 1 of 2) |
| part_total | INTEGER | NULL | Total parts |
| md5_hash | VARCHAR(32) | NULL | For detecting schedule changes |

**Indexes:**
- PRIMARY KEY on `schedule_id`
- INDEX on `program_id`
- INDEX on `station_id`
- INDEX on `air_datetime`
- COMPOSITE INDEX on `(station_id, air_datetime)` for guide queries
- INDEX on `is_new`

**Business Rules:**
- `air_datetime` stored in UTC, converted to local for display
- `duration_seconds` can differ from program.duration_seconds
- Schedule must have valid `program_id` and `station_id`
- End time calculated as `air_datetime + duration_seconds`

---

### 4. Recording

Represents a scheduled or completed recording.

**Table Name:** `recordings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| recording_id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique recording identifier |
| schedule_id | VARCHAR(64) | NOT NULL, FOREIGN KEY | Links to schedules table |
| series_rule_id | INTEGER | NULL, FOREIGN KEY | If created by series rule |
| status | VARCHAR(16) | NOT NULL | See RecordingStatus enum |
| padding_start_seconds | INTEGER | NOT NULL DEFAULT 60 | Start N seconds early |
| padding_end_seconds | INTEGER | NOT NULL DEFAULT 120 | End N seconds late |
| tuner_used | INTEGER | NULL | Which tuner (0-N) |
| file_path | VARCHAR(1024) | NULL | Absolute path to .ts file |
| file_size_bytes | BIGINT | NULL | Size of recorded file |
| actual_start_time | DATETIME | NULL | When recording actually started |
| actual_end_time | DATETIME | NULL | When recording actually ended |
| error_message | TEXT | NULL | Error description if failed |
| quality_metrics | JSON | NULL | Stream stats (dropped packets, etc.) |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When scheduled |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Last status update |

**Indexes:**
- PRIMARY KEY on `recording_id`
- INDEX on `schedule_id`
- INDEX on `series_rule_id`
- INDEX on `status`
- COMPOSITE INDEX on `(status, schedule.air_datetime)` for upcoming recordings
- INDEX on `created_at`

**Business Rules:**
- Status transitions: scheduled → in_progress → completed/failed/cancelled
- `tuner_used` NULL until recording starts
- `file_path` NULL until recording starts
- `file_size_bytes` NULL until recording completes
- `actual_start_time` may differ from scheduled time due to conflicts
- `padding_start_seconds` and `padding_end_seconds` must be >= 0

---

### 5. SeriesRule

Represents an automatic recording rule for a TV series.

**Table Name:** `series_rules`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| rule_id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique rule identifier |
| series_id | VARCHAR(32) | NOT NULL | Schedules Direct series ID |
| title | VARCHAR(256) | NOT NULL | Series title for display |
| record_new_only | BOOLEAN | NOT NULL DEFAULT TRUE | Only new episodes |
| channel_filter | VARCHAR(32) | NULL, FOREIGN KEY | Restrict to specific station |
| time_filter_start | TIME | NULL | Start of time window (e.g., 19:00) |
| time_filter_end | TIME | NULL | End of time window (e.g., 23:00) |
| day_of_week_filter | JSON | NULL | Array of integers 0-6 (Mon-Sun) |
| keep_limit | INTEGER | NULL | Max episodes to retain |
| keep_policy | VARCHAR(16) | NOT NULL DEFAULT 'all' | See KeepPolicy enum |
| padding_start_seconds | INTEGER | NULL | Override default padding |
| padding_end_seconds | INTEGER | NULL | Override default padding |
| priority | INTEGER | NOT NULL DEFAULT 5 | Priority 1-10 for conflict resolution |
| enabled | BOOLEAN | NOT NULL DEFAULT TRUE | Can disable without deleting |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Rule creation time |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Last modification |

**Indexes:**
- PRIMARY KEY on `rule_id`
- INDEX on `series_id`
- INDEX on `enabled`
- INDEX on `priority`

**Business Rules:**
- `series_id` must match a valid program.series_id
- `channel_filter` if set must be valid station_id
- `time_filter_start` and `time_filter_end` must both be set or both NULL
- `keep_limit` NULL means unlimited
- `day_of_week_filter` example: `[0, 1, 2, 3, 4]` for weekdays only
- `priority` used for automatic conflict resolution (higher = more important)
- `keep_policy` determines deletion strategy when limit reached

---

### 6. Lineup

Represents a Schedules Direct lineup (set of channels).

**Table Name:** `lineups`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| lineup_id | VARCHAR(32) | PRIMARY KEY | Schedules Direct lineup ID |
| name | VARCHAR(128) | NOT NULL | Lineup display name |
| location | VARCHAR(128) | NULL | Geographic location |
| lineup_type | VARCHAR(32) | NOT NULL | "Cable", "Antenna", "Satellite" |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | Currently in use |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When added to system |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Last sync time |

**Indexes:**
- PRIMARY KEY on `lineup_id`
- INDEX on `is_active`

**Business Rules:**
- At least one lineup must be active
- Lineup data synced from Schedules Direct
- Inactive lineups retained for historical data

---

### 7. Device

Represents an HDHomeRun device.

**Table Name:** `devices`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| device_id | VARCHAR(32) | PRIMARY KEY | HDHomeRun device ID |
| device_name | VARCHAR(128) | NOT NULL | User-friendly name |
| model | VARCHAR(64) | NOT NULL | Device model (CONNECT, FLEX, etc.) |
| firmware_version | VARCHAR(32) | NULL | Current firmware version |
| ip_address | VARCHAR(45) | NOT NULL | IPv4 or IPv6 address |
| tuner_count | INTEGER | NOT NULL | Number of tuners |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | Currently in use |
| last_seen | DATETIME | NULL | Last successful communication |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When discovered/added |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Last update |

**Indexes:**
- PRIMARY KEY on `device_id`
- INDEX on `is_active`
- INDEX on `last_seen`

**Business Rules:**
- Only one device can be active (MVP limitation)
- `tuner_count` typically 2-4
- `last_seen` updated on each successful API call
- Device marked inactive if unreachable for extended period

---

### 8. Configuration

Key-value store for system settings.

**Table Name:** `configuration`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| config_key | VARCHAR(128) | PRIMARY KEY | Configuration key |
| config_value | JSON | NOT NULL | Configuration value (any type) |
| description | TEXT | NULL | Human-readable description |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | Last modification |

**Indexes:**
- PRIMARY KEY on `config_key`

**Standard Configuration Keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `sd_username` | string | NULL | Schedules Direct username |
| `sd_password_encrypted` | string | NULL | Encrypted SD password |
| `recording_storage_path` | string | NULL | Root directory for recordings |
| `default_padding_start` | integer | 60 | Default start padding (seconds) |
| `default_padding_end` | integer | 120 | Default end padding (seconds) |
| `guide_refresh_hour` | integer | 3 | Hour to refresh guide (0-23) |
| `storage_warning_threshold_gb` | integer | 10 | Warn when free space below this |
| `guide_days_forward` | integer | 14 | Days of guide data to fetch |
| `timezone` | string | "UTC" | System timezone |
| `last_guide_refresh` | datetime | NULL | Last successful guide update |
| `setup_completed` | boolean | false | Has setup wizard been completed |

---

### 9. RecordingLog

Audit trail for recording events.

**Table Name:** `recording_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| log_id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique log entry ID |
| recording_id | INTEGER | NULL, FOREIGN KEY | Related recording (NULL for system logs) |
| timestamp | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | When event occurred |
| level | VARCHAR(16) | NOT NULL | See LogLevel enum |
| message | TEXT | NOT NULL | Log message |
| context | JSON | NULL | Additional structured data |

**Indexes:**
- PRIMARY KEY on `log_id`
- INDEX on `recording_id`
- INDEX on `timestamp`
- INDEX on `level`

**Business Rules:**
- `recording_id` NULL for system-level logs
- `context` contains structured data (e.g., tuner number, error codes)
- Logs rotated/archived after 90 days to prevent unbounded growth

---

## Enumerations

### RecordingStatus

Valid values for `recordings.status`:

| Value | Description |
|-------|-------------|
| `scheduled` | Recording is scheduled, not yet started |
| `in_progress` | Recording is currently active |
| `completed` | Recording finished successfully |
| `failed` | Recording failed due to error |
| `cancelled` | User cancelled before start |
| `partial` | Recording started but didn't complete |

**State Transitions:**
```
scheduled → in_progress → completed
                       → failed
                       → partial
scheduled → cancelled
```

### KeepPolicy

Valid values for `series_rules.keep_policy`:

| Value | Description |
|-------|-------------|
| `all` | Keep all episodes (ignore keep_limit) |
| `latest` | Keep N most recent episodes |
| `unwatched` | Keep N unwatched episodes (requires watch tracking) |
| `space` | Delete oldest when space needed |

### LogLevel

Valid values for `recording_logs.level`:

| Value | Description |
|-------|-------------|
| `debug` | Detailed debug information |
| `info` | General informational messages |
| `warning` | Warning messages (non-critical) |
| `error` | Error messages (recoverable) |
| `critical` | Critical errors (system failure) |

---

## Indexes and Performance

### Composite Indexes

For optimal query performance:

```sql
-- Guide queries (get programs on channel in time range)
CREATE INDEX idx_schedules_station_time
ON schedules(station_id, air_datetime);

-- Upcoming recordings query
CREATE INDEX idx_recordings_status_time
ON recordings(status, schedule_id);

-- Series matching (find airings for series)
CREATE INDEX idx_programs_series
ON programs(series_id, original_air_date);

-- Search performance
CREATE INDEX idx_programs_title
ON programs(title, episode_title);
```

### Query Optimization Guidelines

1. **Guide Queries:** Always filter by `station_id` and time range
2. **Search:** Use FULLTEXT index for title/description search
3. **Recording Scheduler:** Query only `status='scheduled'` with time filter
4. **Conflict Detection:** Join recordings with schedules on overlapping times
5. **Series Matching:** Query by `series_id` with date range

---

## Validation Rules

### Data Integrity Constraints

#### Station
- `channel_number` format: `^\d+(\.\d+)?$` (e.g., "2", "2.1", "702")
- `callsign` max 16 characters, alphanumeric + hyphen

#### Program
- `title` required, max 256 characters
- `duration_seconds` must be > 0 and < 86400 (24 hours)
- `season` and `episode` must be >= 0 if provided
- `genres` must be valid JSON array

#### Schedule
- `air_datetime` must be valid UTC datetime
- `duration_seconds` must be > 0
- End time (`air_datetime + duration`) must not exceed 24 hours from start

#### Recording
- `padding_start_seconds` must be >= 0 and <= 1800 (30 min)
- `padding_end_seconds` must be >= 0 and <= 3600 (60 min)
- `tuner_used` must be >= 0 and < device.tuner_count
- `file_path` must be absolute path within recording storage directory

#### SeriesRule
- `priority` must be 1-10
- `keep_limit` must be > 0 if set
- `time_filter_start` < `time_filter_end` if both set
- `day_of_week_filter` array elements must be 0-6

### Business Logic Validation

1. **Recording Conflicts:**
   - Two recordings overlap if their adjusted times intersect
   - Adjusted start: `schedule.air_datetime - padding_start_seconds`
   - Adjusted end: `schedule.air_datetime + schedule.duration_seconds + padding_end_seconds`
   - Conflict exists if overlapping recordings > available tuners

2. **Series Matching:**
   - Match by `program.series_id = rule.series_id`
   - If `record_new_only`: filter `schedule.is_new = TRUE`
   - If `channel_filter`: filter `schedule.station_id = rule.channel_filter`
   - If `time_filter`: check `TIME(schedule.air_datetime)` within window
   - If `day_of_week_filter`: check `WEEKDAY(schedule.air_datetime)` in array

3. **Storage Management:**
   - Before recording: check free space > expected size (estimate 2 GB/hour HD)
   - After recording: validate file exists and size > 1 MB
   - When `keep_limit` exceeded: delete oldest recordings for series

---

## Data Relationships

### One-to-Many Relationships

1. **Lineup → Station** (1:N)
   - One lineup contains many stations
   - `stations.lineup_id` → `lineups.lineup_id`

2. **Station → Schedule** (1:N)
   - One station has many scheduled airings
   - `schedules.station_id` → `stations.station_id`

3. **Program → Schedule** (1:N)
   - One program has many airings
   - `schedules.program_id` → `programs.program_id`

4. **Schedule → Recording** (1:N)
   - One airing can be recorded multiple times (rare, but possible)
   - `recordings.schedule_id` → `schedules.schedule_id`

5. **SeriesRule → Recording** (1:N)
   - One rule creates many recordings
   - `recordings.series_rule_id` → `series_rules.rule_id`

6. **Recording → RecordingLog** (1:N)
   - One recording generates many log entries
   - `recording_logs.recording_id` → `recordings.recording_id`

### Many-to-One Relationships

1. **Program → Series** (N:1 via series_id)
   - Many episodes belong to one series
   - Relationship via `programs.series_id` (not a foreign key, just grouping)

### Optional Relationships

1. **Recording → SeriesRule** (N:0..1)
   - Recording may or may not be created by a rule
   - `recordings.series_rule_id` is nullable

2. **SeriesRule → Station** (N:0..1)
   - Rule may optionally filter by channel
   - `series_rules.channel_filter` is nullable foreign key

---

## Database Schema Migration Strategy

### Version Control

Use Alembic for schema migrations:

```
migrations/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_priority_to_series_rules.py
│   └── 003_add_quality_metrics_to_recordings.py
└── env.py
```

### Initial Schema Creation

The initial migration creates all tables with:
- Primary keys
- Foreign keys with ON DELETE CASCADE where appropriate
- Indexes for query performance
- Default values
- Check constraints

### Backward Compatibility

- Never delete columns (mark as deprecated, NULL-able)
- Add new columns as nullable or with defaults
- Use database views for complex queries
- Keep migrations reversible (implement `downgrade()`)

---

## Sample Data Queries

### Get Program Guide for Channel and Time Range

```sql
SELECT
    s.schedule_id,
    s.air_datetime,
    s.duration_seconds,
    s.is_new,
    p.title,
    p.episode_title,
    p.season,
    p.episode,
    p.description,
    st.channel_number,
    st.callsign
FROM schedules s
JOIN programs p ON s.program_id = p.program_id
JOIN stations st ON s.station_id = st.station_id
WHERE st.station_id = ?
  AND s.air_datetime >= ?
  AND s.air_datetime < ?
ORDER BY s.air_datetime;
```

### Get Upcoming Recordings

```sql
SELECT
    r.recording_id,
    r.status,
    s.air_datetime,
    s.duration_seconds,
    p.title,
    p.episode_title,
    p.season,
    p.episode,
    st.channel_number,
    st.callsign
FROM recordings r
JOIN schedules s ON r.schedule_id = s.schedule_id
JOIN programs p ON s.program_id = p.program_id
JOIN stations st ON s.station_id = st.station_id
WHERE r.status IN ('scheduled', 'in_progress')
ORDER BY s.air_datetime;
```

### Detect Recording Conflicts

```sql
SELECT
    r1.recording_id AS recording1_id,
    r2.recording_id AS recording2_id,
    s1.air_datetime AS start1,
    s2.air_datetime AS start2
FROM recordings r1
JOIN schedules s1 ON r1.schedule_id = s1.schedule_id
JOIN recordings r2 ON r2.recording_id > r1.recording_id
JOIN schedules s2 ON r2.schedule_id = s2.schedule_id
WHERE r1.status = 'scheduled'
  AND r2.status = 'scheduled'
  AND (
    -- r1 starts during r2 (with padding)
    (s1.air_datetime - r1.padding_start_seconds) BETWEEN
        (s2.air_datetime - r2.padding_start_seconds) AND
        (s2.air_datetime + s2.duration_seconds + r2.padding_end_seconds)
    OR
    -- r2 starts during r1 (with padding)
    (s2.air_datetime - r2.padding_start_seconds) BETWEEN
        (s1.air_datetime - r1.padding_start_seconds) AND
        (s1.air_datetime + s1.duration_seconds + r1.padding_end_seconds)
  );
```

### Find Episodes Matching Series Rule

```sql
SELECT
    s.schedule_id,
    s.air_datetime,
    p.title,
    p.episode_title,
    p.season,
    p.episode,
    st.channel_number
FROM schedules s
JOIN programs p ON s.program_id = p.program_id
JOIN stations st ON s.station_id = st.station_id
WHERE p.series_id = :series_id
  AND s.air_datetime >= CURRENT_TIMESTAMP
  AND s.air_datetime < DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 14 DAY)
  AND (:record_new_only = 0 OR s.is_new = 1)
  AND (:channel_filter IS NULL OR st.station_id = :channel_filter)
  AND (:time_start IS NULL OR TIME(s.air_datetime) >= :time_start)
  AND (:time_end IS NULL OR TIME(s.air_datetime) <= :time_end)
ORDER BY s.air_datetime;
```

---

## Notes and Considerations

### UTC Time Storage

All datetime fields store UTC timestamps:
- `schedules.air_datetime` is UTC
- `recordings.actual_start_time` is UTC
- Display conversion to local timezone happens in application layer

### JSON Field Usage

JSON fields provide flexibility without schema changes:
- `programs.genres`: `["Drama", "Thriller", "Crime"]`
- `programs.cast_crew`: `{"cast": ["Actor 1"], "director": ["Dir"]}`
- `schedules.audio_properties`: `["stereo", "surround"]`
- `recording.quality_metrics`: `{"dropped_packets": 12, "avg_bitrate": 15000000}`

### Soft Deletes vs Hard Deletes

- **Hard Delete:** Recordings, SeriesRules (user explicitly deletes)
- **Soft Delete:** Stations (set `enabled=false`), Devices (set `is_active=false`)
- **Cascade Delete:** RecordingLogs when Recording deleted

### Database Size Estimates

For 100 channels, 14 days of guide data:
- ~50,000 schedule entries
- ~25,000 unique programs
- ~100 recordings per month
- Database size: ~100-200 MB

Recording files (not in database) consume much more space:
- 1 hour HD recording: ~2-4 GB

---

**End of Data Model Specification**
