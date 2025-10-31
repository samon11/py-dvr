# Common API Schemas

## Base Response Types

### Success Response

All successful API responses follow this structure:

```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Optional success message"
}
```

### Error Response

All error responses follow this structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { /* optional additional context */ }
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST creating resource |
| 400 | Bad Request | Invalid input, validation failure |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., recording conflict) |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | External service (SD, HDHomeRun) unavailable |

## Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Resource conflict |
| `EXTERNAL_SERVICE_ERROR` | HDHomeRun or Schedules Direct unavailable |
| `STORAGE_ERROR` | Filesystem or storage issue |
| `TUNER_UNAVAILABLE` | No tuners available for recording |
| `INTERNAL_ERROR` | Unexpected server error |

---

## Common Data Types

### DateTime

ISO 8601 format in UTC:
```
"2025-10-31T20:00:00Z"
```

### Duration

Integer seconds:
```
3600  // 1 hour
```

### Channel Number

String format allowing decimals:
```
"2.1"
"702"
```

---

## Shared Schemas

### Station Schema

```json
{
  "station_id": "12345.schedulesdirect.org",
  "callsign": "WGBH",
  "channel_number": "2.1",
  "name": "WGBH Boston",
  "affiliate": "PBS",
  "logo_url": "https://example.com/logo.png",
  "enabled": true
}
```

### Program Schema

```json
{
  "program_id": "EP012345678",
  "series_id": "SH012345678",
  "title": "Nova",
  "episode_title": "Black Holes",
  "description": "Full description of the episode...",
  "short_description": "Brief description...",
  "season": 50,
  "episode": 12,
  "original_air_date": "2024-03-15",
  "genres": ["Documentary", "Science"],
  "cast_crew": {
    "cast": ["Narrator Name"],
    "director": ["Director Name"]
  },
  "content_rating": "TV-G",
  "duration_seconds": 3600,
  "artwork_url": "https://example.com/artwork.jpg",
  "is_movie": false,
  "is_sports": false
}
```

### Schedule (Airing) Schema

```json
{
  "schedule_id": "12345.schedulesdirect.org_2025-10-31T20:00:00Z_EP012345678",
  "program": { /* Program Schema */ },
  "station": { /* Station Schema */ },
  "air_datetime": "2025-10-31T20:00:00Z",
  "duration_seconds": 3600,
  "is_new": true,
  "is_live": false,
  "is_premiere": false,
  "is_finale": false,
  "audio_properties": ["stereo", "surround"],
  "video_properties": ["HD", "1080i"]
}
```

### Recording Schema

```json
{
  "recording_id": 123,
  "schedule": { /* Schedule Schema */ },
  "series_rule_id": 5,
  "status": "scheduled",
  "padding_start_seconds": 60,
  "padding_end_seconds": 120,
  "tuner_used": null,
  "file_path": null,
  "file_size_bytes": null,
  "actual_start_time": null,
  "actual_end_time": null,
  "error_message": null,
  "created_at": "2025-10-31T15:30:00Z",
  "updated_at": "2025-10-31T15:30:00Z"
}
```

### Series Rule Schema

```json
{
  "rule_id": 5,
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
  "priority": 5,
  "enabled": true,
  "created_at": "2025-10-31T15:00:00Z",
  "updated_at": "2025-10-31T15:00:00Z"
}
```

---

## Pagination

For endpoints returning lists, pagination parameters:

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Number of results per page (max 200) |
| `offset` | integer | 0 | Number of results to skip |

### Paginated Response

```json
{
  "success": true,
  "data": {
    "items": [ /* array of resources */ ],
    "pagination": {
      "limit": 50,
      "offset": 0,
      "total": 250,
      "has_more": true
    }
  }
}
```

---

## Validation Error Response

When input validation fails (400 Bad Request):

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": {
      "fields": {
        "padding_start_seconds": ["Must be between 0 and 1800"],
        "station_id": ["Station not found"]
      }
    }
  }
}
```

---

## Timestamps

All datetime fields:
- Stored and transmitted in UTC
- ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- Client responsible for local timezone conversion for display
