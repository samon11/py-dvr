# Recording Management API Contracts

## Endpoints

### 1. Schedule One-Time Recording

**Endpoint:** `POST /api/v1/recordings`

**Description:** Schedule a one-time recording for a specific program airing.

**Request Body:**
```json
{
  "schedule_id": "12345.schedulesdirect.org_2025-10-31T20:00:00Z_EP012345678",
  "padding_start_seconds": 60,
  "padding_end_seconds": 120
}
```

**Fields:**
- `schedule_id` (required) - Identifies the specific airing to record
- `padding_start_seconds` (optional) - Override default start padding (0-1800)
- `padding_end_seconds` (optional) - Override default end padding (0-3600)

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "recording": { /* Full Recording Schema */ }
  },
  "message": "Recording scheduled successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid schedule_id or padding values
- `404 Not Found` - Schedule not found
- `409 Conflict` - Recording would conflict with existing recording(s)
  ```json
  {
    "success": false,
    "error": {
      "code": "CONFLICT",
      "message": "Recording conflicts with existing recordings",
      "details": {
        "conflicts": [
          {
            "recording_id": 124,
            "program_title": "Other Show",
            "air_time": "2025-10-31T20:30:00Z"
          }
        ],
        "available_tuners": 2,
        "required_tuners": 3
      }
    }
  }
  ```

---

### 2. Get Scheduled Recordings

**Endpoint:** `GET /api/v1/recordings`

**Description:** Retrieve list of scheduled recordings.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string[] | No | All | Filter by status (scheduled,in_progress,completed,failed,cancelled) |
| `start_date` | date | No | Today | Start of date range |
| `end_date` | date | No | +30 days | End of date range |
| `series_rule_id` | integer | No | All | Filter by series rule |
| `sort` | string | No | air_time | Sort field (air_time, created_at, title) |
| `order` | string | No | asc | Sort order (asc, desc) |
| `limit` | integer | No | 100 | Results per page |
| `offset` | integer | No | 0 | Pagination offset |

**Example Request:**
```
GET /api/v1/recordings?status=scheduled,in_progress&sort=air_time&order=asc
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "recordings": [
      {
        "recording": { /* Recording Schema */ },
        "conflicts": [
          {
            "recording_id": 126,
            "overlap_seconds": 300
          }
        ]
      }
    ],
    "pagination": { /* Pagination Schema */ },
    "summary": {
      "total_scheduled": 15,
      "total_conflicts": 2,
      "next_recording": "2025-10-31T20:00:00Z"
    }
  }
}
```

**Fields:**
- `conflicts` - Array of conflicting recordings (empty if none)
- `summary` - Aggregate statistics

---

### 3. Get Recording Details

**Endpoint:** `GET /api/v1/recordings/:recording_id`

**Description:** Get details of a specific recording.

**Path Parameters:**
- `recording_id` - Recording identifier

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "recording": { /* Full Recording Schema with nested schedule, program, station */ },
    "conflicts": [ /* Array of conflicting recordings */ ],
    "logs": [
      {
        "timestamp": "2025-10-31T20:00:05Z",
        "level": "info",
        "message": "Recording started on tuner 0"
      }
    ]
  }
}
```

**Fields:**
- `logs` - Recent log entries for this recording

**Error Responses:**
- `404 Not Found` - Recording not found

---

### 4. Update Recording

**Endpoint:** `PATCH /api/v1/recordings/:recording_id`

**Description:** Update recording settings (padding only before recording starts).

**Path Parameters:**
- `recording_id` - Recording identifier

**Request Body:**
```json
{
  "padding_start_seconds": 120,
  "padding_end_seconds": 180
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "recording": { /* Updated Recording Schema */ }
  },
  "message": "Recording updated successfully"
}
```

**Error Responses:**
- `404 Not Found` - Recording not found
- `400 Bad Request` - Cannot modify in-progress or completed recording
- `409 Conflict` - New padding creates conflict

---

### 5. Cancel Recording

**Endpoint:** `DELETE /api/v1/recordings/:recording_id`

**Description:** Cancel a scheduled recording.

**Path Parameters:**
- `recording_id` - Recording identifier

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `delete_file` | boolean | No | false | Delete file if recording already started/completed |

**Success Response (200):**
```json
{
  "success": true,
  "message": "Recording cancelled successfully"
}
```

**Error Responses:**
- `404 Not Found` - Recording not found
- `400 Bad Request` - Cannot cancel in-progress recording (use `force=true`)

---

### 6. Get Recording Conflicts

**Endpoint:** `GET /api/v1/recordings/conflicts`

**Description:** Get all recordings with conflicts.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `resolve_suggestions` | boolean | No | false | Include AI suggestions for resolution |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "conflicts": [
      {
        "time_slot": "2025-10-31T20:00:00Z to 2025-10-31T21:00:00Z",
        "recordings": [
          { /* Recording Schema */ },
          { /* Recording Schema */ },
          { /* Recording Schema */ }
        ],
        "required_tuners": 3,
        "available_tuners": 2,
        "suggestions": [
          {
            "action": "cancel",
            "recording_id": 125,
            "reason": "Lowest priority series rule"
          }
        ]
      }
    ],
    "total_conflicts": 1,
    "affected_recordings": 3
  }
}
```

**Fields:**
- `suggestions` - Only included if `resolve_suggestions=true`

---

### 7. Bulk Schedule Recordings

**Endpoint:** `POST /api/v1/recordings/bulk`

**Description:** Schedule multiple recordings at once.

**Request Body:**
```json
{
  "schedule_ids": [
    "12345.schedulesdirect.org_2025-10-31T20:00:00Z_EP012345678",
    "12345.schedulesdirect.org_2025-11-01T20:00:00Z_EP012345679"
  ],
  "padding_start_seconds": 60,
  "padding_end_seconds": 120
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "scheduled": [
      { /* Recording Schema */ }
    ],
    "failed": [
      {
        "schedule_id": "...",
        "reason": "Conflict with existing recording"
      }
    ]
  },
  "message": "2 of 3 recordings scheduled successfully"
}
```

---

### 8. Get Recording Statistics

**Endpoint:** `GET /api/v1/recordings/stats`

**Description:** Get recording statistics and metrics.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | No | -30 days | Start of date range |
| `end_date` | date | No | Today | End of date range |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "total_recordings": 150,
    "by_status": {
      "completed": 142,
      "failed": 5,
      "cancelled": 3
    },
    "success_rate": 0.947,
    "total_duration_hours": 237.5,
    "total_size_gb": 475.2,
    "average_file_size_gb": 3.35,
    "by_failure_reason": {
      "tuner_unavailable": 3,
      "storage_full": 1,
      "stream_error": 1
    },
    "upcoming_scheduled": 18
  }
}
```

---

## Recording Status Lifecycle

```
scheduled
    ↓
in_progress (recording actively capturing stream)
    ↓
completed (success) | failed (error) | partial (incomplete)

cancelled (user cancelled before start)
```

## Conflict Detection Logic

Recordings conflict when:
1. Their adjusted time ranges overlap
2. Number of overlapping recordings exceeds available tuners

**Adjusted Time Range:**
- Start: `schedule.air_datetime - padding_start_seconds`
- End: `schedule.air_datetime + schedule.duration_seconds + padding_end_seconds`

**Example:**
- 2 tuners available
- Recording A: 8:00 PM - 9:00 PM (tuner 0)
- Recording B: 8:30 PM - 9:30 PM (tuner 1)
- Recording C: 8:45 PM - 9:45 PM → **CONFLICT** (no tuner available)

## Notes

### Padding Limits
- Start padding: 0-1800 seconds (0-30 minutes)
- End padding: 0-3600 seconds (0-60 minutes)
- Excessive padding increases conflict likelihood

### Cancellation Policy
- Can cancel scheduled recordings anytime
- Cannot cancel in-progress recordings (stop recording instead)
- Cancelled recordings marked as `cancelled`, not deleted

### File Management
- Recording files created in: `{storage_path}/{series_title}/S##E## - {episode}.ts`
- Files not deleted when recording cancelled unless explicitly requested
- Partial recordings retained for user review
