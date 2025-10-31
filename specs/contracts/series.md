# Series Recording API Contracts

## Endpoints

### 1. Create Series Rule

**Endpoint:** `POST /api/v1/series-rules`

**Description:** Create a new series recording rule.

**Request Body:**
```json
{
  "series_id": "SH012345678",
  "title": "Survivor",
  "record_new_only": true,
  "channel_filter": null,
  "time_filter_start": null,
  "time_filter_end": null,
  "day_of_week_filter": null,
  "keep_limit": 10,
  "keep_policy": "latest",
  "padding_start_seconds": null,
  "padding_end_seconds": null,
  "priority": 5
}
```

**Fields:**
- `series_id` (required) - Schedules Direct series ID
- `title` (required) - Series title for display
- `record_new_only` (optional, default: true) - Only record new episodes
- `channel_filter` (optional) - Restrict to specific station_id
- `time_filter_start` (optional) - Start of time window (HH:MM format, e.g., "19:00")
- `time_filter_end` (optional) - End of time window (HH:MM format, e.g., "23:00")
- `day_of_week_filter` (optional) - Array of integers 0-6 (Monday=0, Sunday=6)
- `keep_limit` (optional) - Maximum episodes to retain (null = unlimited)
- `keep_policy` (optional, default: "all") - "all", "latest", "unwatched", "space"
- `padding_start_seconds` (optional) - Override default start padding
- `padding_end_seconds` (optional) - Override default end padding
- `priority` (optional, default: 5) - Priority 1-10 for conflict resolution

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "rule": { /* Full SeriesRule Schema */ },
    "matched_episodes": [
      { /* Schedule Schema */ }
    ],
    "scheduled_count": 5
  },
  "message": "Series rule created successfully. 5 episodes scheduled."
}
```

**Fields:**
- `matched_episodes` - Upcoming episodes matching this rule
- `scheduled_count` - Number of recordings automatically scheduled

**Error Responses:**
- `400 Bad Request` - Invalid parameters or validation error
- `404 Not Found` - Series ID not found in guide data
- `409 Conflict` - Series rule already exists for this series

**Validation Rules:**
- If `time_filter_start` is set, `time_filter_end` must also be set
- `time_filter_start` must be before `time_filter_end`
- `priority` must be 1-10
- `keep_limit` must be > 0 if set
- `day_of_week_filter` elements must be 0-6

---

### 2. Get Series Rules

**Endpoint:** `GET /api/v1/series-rules`

**Description:** Retrieve list of all series recording rules.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled_only` | boolean | No | false | Only active rules |
| `sort` | string | No | title | Sort field (title, created_at, priority) |
| `order` | string | No | asc | Sort order (asc, desc) |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "rules": [
      {
        "rule": { /* SeriesRule Schema */ },
        "scheduled_count": 5,
        "recorded_count": 12,
        "next_recording": {
          "air_datetime": "2025-11-01T20:00:00Z",
          "episode_title": "Next Episode"
        }
      }
    ]
  }
}
```

**Fields:**
- `scheduled_count` - Number of future scheduled recordings
- `recorded_count` - Number of completed recordings
- `next_recording` - Next episode that will be recorded (null if none)

---

### 3. Get Series Rule Details

**Endpoint:** `GET /api/v1/series-rules/:rule_id`

**Description:** Get detailed information about a specific series rule.

**Path Parameters:**
- `rule_id` - Rule identifier

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "rule": { /* Full SeriesRule Schema */ },
    "scheduled_recordings": [
      { /* Recording Schema with nested schedule */ }
    ],
    "completed_recordings": [
      { /* Recording Schema */ }
    ],
    "matched_but_not_scheduled": [
      {
        "schedule": { /* Schedule Schema */ },
        "reason": "Conflict with higher priority recording"
      }
    ],
    "statistics": {
      "total_scheduled": 5,
      "total_recorded": 12,
      "success_rate": 0.917,
      "total_size_gb": 48.5,
      "disk_space_used_gb": 48.5
    }
  }
}
```

**Fields:**
- `matched_but_not_scheduled` - Episodes matching rule but not scheduled (due to conflicts or other issues)
- `statistics` - Aggregate stats for this series

**Error Responses:**
- `404 Not Found` - Rule not found

---

### 4. Update Series Rule

**Endpoint:** `PATCH /api/v1/series-rules/:rule_id`

**Description:** Update an existing series rule.

**Path Parameters:**
- `rule_id` - Rule identifier

**Request Body:**
```json
{
  "record_new_only": false,
  "keep_limit": 15,
  "priority": 7
}
```

**Note:** Can update any field except `series_id` and `title`

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "rule": { /* Updated SeriesRule Schema */ },
    "changes": {
      "new_matches": 3,
      "removed_matches": 1
    }
  },
  "message": "Series rule updated. 3 new episodes scheduled, 1 unscheduled."
}
```

**Fields:**
- `changes.new_matches` - Episodes newly matching after update
- `changes.removed_matches` - Episodes no longer matching after update

**Error Responses:**
- `404 Not Found` - Rule not found
- `400 Bad Request` - Invalid parameters

---

### 5. Delete Series Rule

**Endpoint:** `DELETE /api/v1/series-rules/:rule_id`

**Description:** Delete a series recording rule.

**Path Parameters:**
- `rule_id` - Rule identifier

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `cancel_scheduled` | boolean | No | false | Cancel scheduled recordings |
| `delete_recorded` | boolean | No | false | Delete completed recording files |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "cancelled_recordings": 5,
    "deleted_files": 0
  },
  "message": "Series rule deleted. 5 scheduled recordings cancelled."
}
```

**Error Responses:**
- `404 Not Found` - Rule not found

---

### 6. Skip Episode

**Endpoint:** `POST /api/v1/series-rules/:rule_id/skip`

**Description:** Skip a specific episode for this series rule.

**Path Parameters:**
- `rule_id` - Rule identifier

**Request Body:**
```json
{
  "schedule_id": "12345.schedulesdirect.org_2025-11-01T20:00:00Z_EP012345678"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Episode skipped. Recording cancelled."
}
```

**Note:** If recording already scheduled, it will be cancelled

**Error Responses:**
- `404 Not Found` - Rule or schedule not found
- `400 Bad Request` - Episode not matched by this rule

---

### 7. Un-skip Episode

**Endpoint:** `POST /api/v1/series-rules/:rule_id/unskip`

**Description:** Remove skip for a previously skipped episode.

**Path Parameters:**
- `rule_id` - Rule identifier

**Request Body:**
```json
{
  "schedule_id": "12345.schedulesdirect.org_2025-11-01T20:00:00Z_EP012345678"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "recording": { /* Newly created Recording Schema */ }
  },
  "message": "Episode un-skipped. Recording scheduled."
}
```

**Error Responses:**
- `404 Not Found` - Rule or schedule not found
- `409 Conflict` - Scheduling creates conflict

---

### 8. Test Series Rule

**Endpoint:** `POST /api/v1/series-rules/test`

**Description:** Test a series rule without creating it (preview matching episodes).

**Request Body:**
```json
{
  "series_id": "SH012345678",
  "record_new_only": true,
  "channel_filter": null,
  "time_filter_start": "19:00",
  "time_filter_end": "23:00",
  "day_of_week_filter": [0, 1, 2, 3, 4]
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "matched_episodes": [
      { /* Schedule Schema */ }
    ],
    "match_count": 8,
    "conflicts": [
      {
        "schedule": { /* Schedule Schema */ },
        "conflicting_recordings": [ /* Recording IDs */ ]
      }
    ],
    "warnings": [
      "Time filter (19:00-23:00) excludes 2 airings outside this window",
      "Weekday filter excludes 3 weekend airings"
    ]
  }
}
```

**Fields:**
- `matched_episodes` - Episodes that would be scheduled
- `conflicts` - Potential conflicts with existing recordings
- `warnings` - Helpful messages about filter effects

---

### 9. Get Series Suggestions

**Endpoint:** `GET /api/v1/series-rules/suggestions`

**Description:** Get suggestions for popular series to record based on guide data.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | Number of suggestions |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "series_id": "SH012345678",
        "title": "Popular Show",
        "genres": ["Drama", "Thriller"],
        "upcoming_episodes": 5,
        "has_rule": false,
        "reason": "Highly rated drama series with 5 upcoming episodes"
      }
    ]
  }
}
```

**Note:** This is a future enhancement feature for MVP+

---

## Series Matching Logic

### Matching Algorithm

For each upcoming airing in guide data (up to 14 days):

1. **Series ID Match:** `program.series_id = rule.series_id`
2. **New Episodes Only:** If `rule.record_new_only = true`, check `schedule.is_new = true`
3. **Channel Filter:** If `rule.channel_filter` is set, check `schedule.station_id = rule.channel_filter`
4. **Time Window Filter:** If `rule.time_filter_start/end` are set, check time of day within window
5. **Day of Week Filter:** If `rule.day_of_week_filter` is set, check day of week in array
6. **Already Scheduled:** Skip if episode already has a recording scheduled
7. **Already Recorded:** Skip if episode already recorded (check by program_id)

### Keep Limit Enforcement

When `keep_limit` is set and reached:

**Policy: "latest"**
- Delete oldest completed recordings first
- Keep most recent N episodes

**Policy: "unwatched"** (future)
- Delete watched episodes first
- Requires watch tracking

**Policy: "space"** (future)
- Delete oldest only when storage threshold reached

### Priority System

Used for automatic conflict resolution:
- Higher priority (1 = highest, 10 = lowest)
- When conflict detected, lower priority recordings cancelled automatically
- Equal priority: manual resolution required

---

## Notes

### Time Filters

Time filters use local time (converted from UTC):
- Format: "HH:MM" in 24-hour format
- Example: `"19:00"` to `"23:00"` for primetime
- Useful for shows that air multiple times daily

### Day of Week Filter

Integer array representing days:
- 0 = Monday
- 1 = Tuesday
- 2 = Wednesday
- 3 = Thursday
- 4 = Friday
- 5 = Saturday
- 6 = Sunday

Example weekdays only: `[0, 1, 2, 3, 4]`

### Episode Skipping

- Skip list stored separately (not in database schema above)
- Skipped episodes won't be scheduled even if they match rule
- Useful for reruns, specials, or unwanted episodes

### Series Rule Conflicts

When creating/updating rule:
- System checks if new scheduled recordings would create conflicts
- Rule can still be created with conflicts (manual resolution required)
- Warning shown to user about conflicts
