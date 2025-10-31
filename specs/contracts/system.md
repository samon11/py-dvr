# System Management API Contracts

## Endpoints

### 1. Get System Status

**Endpoint:** `GET /api/v1/system/status`

**Description:** Get overall system health and status.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "system": {
      "status": "healthy",
      "uptime_seconds": 345600,
      "version": "1.0.0",
      "python_version": "3.11.5"
    },
    "device": {
      "status": "online",
      "device_id": "12345ABC",
      "model": "HDHR5-4K",
      "firmware": "20231201",
      "ip_address": "192.168.1.100",
      "tuner_count": 4,
      "tuners_available": 3,
      "last_seen": "2025-10-31T21:55:00Z"
    },
    "guide": {
      "last_refresh": "2025-10-31T03:00:00Z",
      "next_refresh": "2025-11-01T03:00:00Z",
      "status": "current",
      "schedule_count": 52340,
      "program_count": 23456,
      "date_range": {
        "start": "2025-10-31",
        "end": "2025-11-14"
      }
    },
    "recordings": {
      "scheduled_count": 18,
      "in_progress_count": 1,
      "next_recording": {
        "title": "Next Show",
        "air_datetime": "2025-10-31T22:00:00Z",
        "channel": "2.1"
      },
      "active_recording": {
        "title": "Current Show",
        "start_time": "2025-10-31T21:30:00Z",
        "tuner": 0,
        "progress_percentage": 65
      }
    },
    "storage": {
      "path": "/mnt/recordings",
      "total_gb": 1000.0,
      "used_gb": 485.7,
      "free_gb": 514.3,
      "used_percentage": 48.6,
      "warning": false
    },
    "conflicts": {
      "count": 2,
      "next_conflict": "2025-11-02T20:00:00Z"
    }
  }
}
```

**Status Values:**
- `healthy` - All systems operational
- `degraded` - Some issues but functional
- `offline` - Critical systems unavailable

---

### 2. Get Device Status

**Endpoint:** `GET /api/v1/system/device`

**Description:** Get detailed HDHomeRun device information.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "device": {
      "device_id": "12345ABC",
      "device_name": "HDHomeRun Living Room",
      "model": "HDHR5-4K",
      "firmware_version": "20231201",
      "ip_address": "192.168.1.100",
      "tuner_count": 4,
      "is_active": true,
      "last_seen": "2025-10-31T21:55:00Z"
    },
    "tuners": [
      {
        "tuner_id": 0,
        "status": "in_use",
        "channel": "2.1",
        "signal_strength": 100,
        "signal_quality": 100,
        "symbol_quality": 100,
        "used_by": "dvr_recording_125",
        "locked": true
      },
      {
        "tuner_id": 1,
        "status": "available",
        "channel": null,
        "used_by": null
      }
    ],
    "capabilities": {
      "supports_4k": true,
      "supports_atsc3": true,
      "supports_cable_card": false
    }
  }
}
```

**Tuner Status Values:**
- `available` - Tuner free for use
- `in_use` - Tuner in use by DVR
- `external` - Tuner in use by another application

---

### 3. Refresh Guide Data

**Endpoint:** `POST /api/v1/system/guide/refresh`

**Description:** Manually trigger guide data refresh from Schedules Direct.

**Request Body:**
```json
{
  "force_full_refresh": false
}
```

**Success Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Guide refresh started",
  "data": {
    "task_id": "refresh_12345",
    "estimated_duration_minutes": 5
  }
}
```

**Error Responses:**
- `409 Conflict` - Refresh already in progress
- `503 Service Unavailable` - Schedules Direct unavailable

---

### 4. Get Guide Refresh Status

**Endpoint:** `GET /api/v1/system/guide/refresh-status`

**Description:** Check status of ongoing guide refresh.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "in_progress",
    "started_at": "2025-10-31T22:00:00Z",
    "progress_percentage": 45,
    "current_step": "Fetching program metadata",
    "steps_completed": 2,
    "steps_total": 4,
    "estimated_completion": "2025-10-31T22:05:00Z"
  }
}
```

**Status Values:**
- `idle` - No refresh in progress
- `in_progress` - Refresh running
- `completed` - Last refresh completed successfully
- `failed` - Last refresh failed

---

### 5. Get Configuration

**Endpoint:** `GET /api/v1/system/config`

**Description:** Retrieve system configuration settings.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "schedules_direct": {
      "username": "user@example.com",
      "status": "active",
      "subscription_expires": "2026-03-15"
    },
    "recording": {
      "storage_path": "/mnt/recordings",
      "default_padding_start": 60,
      "default_padding_end": 120
    },
    "guide": {
      "refresh_hour": 3,
      "days_forward": 14,
      "last_refresh": "2025-10-31T03:00:00Z"
    },
    "storage": {
      "warning_threshold_gb": 10
    },
    "system": {
      "timezone": "America/New_York",
      "setup_completed": true
    }
  }
}
```

**Note:** Passwords are never returned in API responses

---

### 6. Update Configuration

**Endpoint:** `PATCH /api/v1/system/config`

**Description:** Update system configuration settings.

**Request Body:**
```json
{
  "recording": {
    "default_padding_start": 120,
    "default_padding_end": 180
  },
  "storage": {
    "warning_threshold_gb": 20
  }
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "updated_fields": ["recording.default_padding_start", "recording.default_padding_end", "storage.warning_threshold_gb"]
  },
  "message": "Configuration updated successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid configuration values
- `403 Forbidden` - Cannot modify read-only settings

---

### 7. Test Schedules Direct Connection

**Endpoint:** `POST /api/v1/system/test-sd`

**Description:** Test Schedules Direct API connectivity and credentials.

**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "connection": "success",
    "account_status": "active",
    "subscription_expires": "2026-03-15",
    "lineups": [
      {
        "lineup_id": "USA-OTA-12345",
        "name": "Boston OTA",
        "location": "Boston, MA"
      }
    ],
    "response_time_ms": 245
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `503 Service Unavailable` - Cannot reach Schedules Direct

---

### 8. Test HDHomeRun Connection

**Endpoint:** `POST /api/v1/system/test-device`

**Description:** Test HDHomeRun device connectivity.

**Request Body:**
```json
{
  "ip_address": "192.168.1.100"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "connection": "success",
    "device_id": "12345ABC",
    "model": "HDHR5-4K",
    "firmware": "20231201",
    "tuner_count": 4,
    "tuners_available": 4,
    "response_time_ms": 45
  }
}
```

**Error Responses:**
- `503 Service Unavailable` - Device unreachable

---

### 9. Get System Logs

**Endpoint:** `GET /api/v1/system/logs`

**Description:** Retrieve system logs for troubleshooting.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `level` | string[] | No | All | Filter by level (debug,info,warning,error,critical) |
| `start_time` | datetime | No | -24 hours | Start of time range |
| `end_time` | datetime | No | Now | End of time range |
| `recording_id` | integer | No | All | Filter by recording |
| `limit` | integer | No | 100 | Results limit (max 1000) |
| `offset` | integer | No | 0 | Pagination offset |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "log_id": 12345,
        "timestamp": "2025-10-31T21:30:00Z",
        "level": "info",
        "message": "Recording started successfully",
        "recording_id": 125,
        "context": {
          "tuner": 0,
          "channel": "2.1",
          "program_title": "Show Name"
        }
      }
    ],
    "pagination": { /* Pagination Schema */ }
  }
}
```

---

### 10. Get Health Check

**Endpoint:** `GET /api/v1/health`

**Description:** Simple health check endpoint for monitoring/uptime checks.

**Success Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-31T22:00:00Z"
}
```

**Unhealthy Response (503):**
```json
{
  "status": "unhealthy",
  "timestamp": "2025-10-31T22:00:00Z",
  "issues": [
    "HDHomeRun device unreachable",
    "Database connection failed"
  ]
}
```

---

### 11. Discover HDHomeRun Devices

**Endpoint:** `POST /api/v1/system/discover-devices`

**Description:** Scan network for HDHomeRun devices.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "device_id": "12345ABC",
        "model": "HDHR5-4K",
        "ip_address": "192.168.1.100",
        "firmware": "20231201",
        "tuner_count": 4
      }
    ],
    "scan_duration_ms": 3000
  }
}
```

---

### 12. Run Channel Scan

**Endpoint:** `POST /api/v1/system/channel-scan`

**Description:** Scan for available channels using HDHomeRun device.

**Success Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Channel scan started",
  "data": {
    "task_id": "scan_12345",
    "estimated_duration_minutes": 10
  }
}
```

---

### 13. Get Channel Scan Status

**Endpoint:** `GET /api/v1/system/channel-scan-status`

**Description:** Check status of ongoing channel scan.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "in_progress",
    "started_at": "2025-10-31T22:00:00Z",
    "progress_percentage": 35,
    "channels_found": 42,
    "current_frequency": "573000000",
    "estimated_completion": "2025-10-31T22:10:00Z"
  }
}
```

---

### 14. Get Background Tasks

**Endpoint:** `GET /api/v1/system/tasks`

**Description:** View status of background tasks.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_name": "guide_refresh",
        "status": "scheduled",
        "next_run": "2025-11-01T03:00:00Z",
        "last_run": "2025-10-31T03:00:00Z",
        "last_result": "success",
        "last_duration_seconds": 287
      },
      {
        "task_name": "recording_scheduler",
        "status": "running",
        "started_at": "2025-10-31T21:30:00Z"
      }
    ]
  }
}
```

---

### 15. Trigger Background Task

**Endpoint:** `POST /api/v1/system/tasks/:task_name/trigger`

**Description:** Manually trigger a background task.

**Path Parameters:**
- `task_name` - Name of task (guide_refresh, series_matching, storage_cleanup)

**Success Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Task triggered successfully",
  "data": {
    "task_id": "task_12345",
    "estimated_duration_minutes": 5
  }
}
```

---

### 16. Get System Statistics

**Endpoint:** `GET /api/v1/system/stats`

**Description:** Get aggregated system statistics.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `period` | string | No | all_time | Period (today, week, month, all_time) |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "period": "all_time",
    "recordings": {
      "total": 156,
      "completed": 142,
      "failed": 5,
      "cancelled": 9,
      "success_rate": 0.947
    },
    "storage": {
      "total_size_gb": 485.7,
      "average_recording_size_gb": 3.11
    },
    "series_rules": {
      "active": 8,
      "total_scheduled": 45
    },
    "uptime": {
      "system_uptime_hours": 720,
      "recording_uptime_percentage": 99.2
    },
    "api": {
      "total_requests": 12456,
      "average_response_time_ms": 125
    }
  }
}
```

---

## System Configuration Keys

### Required Configuration

Must be set during initial setup:
- `sd_username` - Schedules Direct username
- `sd_password_encrypted` - Encrypted SD password
- `recording_storage_path` - Root directory for recordings
- `active_device_id` - HDHomeRun device ID

### Optional Configuration

Can use defaults:
- `default_padding_start` - Default: 60 seconds
- `default_padding_end` - Default: 120 seconds
- `guide_refresh_hour` - Default: 3 (3 AM)
- `storage_warning_threshold_gb` - Default: 10
- `guide_days_forward` - Default: 14
- `timezone` - Default: System timezone

---

## Background Tasks

### guide_refresh
- **Schedule:** Daily at configured hour (default 3 AM)
- **Duration:** ~5 minutes
- **Function:** Fetch updated guide data from Schedules Direct

### series_matching
- **Schedule:** After guide refresh completes
- **Duration:** ~30 seconds
- **Function:** Match new airings to series rules, schedule recordings

### recording_scheduler
- **Schedule:** Continuous (checks every 10 seconds)
- **Function:** Monitor scheduled recordings, start at appropriate time

### storage_cleanup (future)
- **Schedule:** Weekly
- **Function:** Apply keep limits, delete old recordings

---

## Notes

### Status Monitoring

- `/health` endpoint designed for uptime monitoring tools
- Returns 200 when healthy, 503 when unhealthy
- Fast response time (< 100ms)

### Log Management

- Logs automatically rotated after 90 days
- Debug logs not enabled by default (performance impact)
- Logs stored in database and optionally written to file

### Task Scheduling

- Background tasks use APScheduler
- Tasks can be manually triggered via API
- Task status visible in system status

### Configuration Security

- Passwords encrypted before storage
- API never returns password values
- Configuration changes logged for audit
