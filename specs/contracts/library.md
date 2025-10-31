# Recording Library API Contracts

## Endpoints

### 1. Get Recording Library

**Endpoint:** `GET /api/v1/library`

**Description:** Retrieve list of completed recordings (library view).

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string[] | No | completed | Filter by status (completed,failed,partial) |
| `series_id` | string | No | All | Filter by series |
| `start_date` | date | No | All time | Recorded on or after date |
| `end_date` | date | No | Today | Recorded on or before date |
| `sort` | string | No | recorded_date | Sort field (recorded_date, title, file_size) |
| `order` | string | No | desc | Sort order (asc, desc) |
| `group_by` | string | No | series | Grouping (series, date, none) |
| `limit` | integer | No | 100 | Results per page |
| `offset` | integer | No | 0 | Pagination offset |

**Example Request:**
```
GET /api/v1/library?group_by=series&sort=title&order=asc
```

**Success Response (200) - Grouped by Series:**
```json
{
  "success": true,
  "data": {
    "series_groups": [
      {
        "series_id": "SH012345678",
        "series_title": "Survivor",
        "recordings": [
          {
            "recording_id": 100,
            "program": { /* Program Schema */ },
            "station": { /* Station Schema */ },
            "air_datetime": "2025-10-31T20:00:00Z",
            "recorded_datetime": "2025-10-31T20:00:00Z",
            "status": "completed",
            "file_path": "/recordings/Survivor/S45E10 - Episode Title.ts",
            "file_size_bytes": 3456789012,
            "duration_seconds": 3600,
            "quality": "HD 1080i"
          }
        ],
        "total_recordings": 12,
        "total_size_gb": 42.5,
        "total_duration_hours": 12.5
      }
    ],
    "movies": [
      {
        "recording_id": 250,
        "program": { /* Program Schema */ },
        "file_path": "/recordings/Movies/Movie Title (2025-10-31).ts",
        "file_size_bytes": 4567890123
      }
    ],
    "one_time": [
      /* Recordings not part of a series */
    ],
    "pagination": { /* Pagination Schema */ },
    "summary": {
      "total_recordings": 156,
      "total_size_gb": 485.7,
      "total_duration_hours": 243.2
    }
  }
}
```

**Success Response (200) - Ungrouped:**
```json
{
  "success": true,
  "data": {
    "recordings": [
      { /* Recording with full program/station details */ }
    ],
    "pagination": { /* Pagination Schema */ },
    "summary": { /* Summary statistics */ }
  }
}
```

---

### 2. Get Recording File Details

**Endpoint:** `GET /api/v1/library/:recording_id`

**Description:** Get detailed information about a completed recording.

**Path Parameters:**
- `recording_id` - Recording identifier

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "recording": {
      "recording_id": 100,
      "program": { /* Full Program Schema */ },
      "station": { /* Station Schema */ },
      "status": "completed",
      "air_datetime": "2025-10-31T20:00:00Z",
      "recorded_datetime": "2025-10-31T20:00:00Z",
      "file_path": "/recordings/Survivor/S45E10 - Episode Title.ts",
      "file_size_bytes": 3456789012,
      "file_size_formatted": "3.22 GB",
      "duration_seconds": 3600,
      "duration_formatted": "1h 0m",
      "actual_start_time": "2025-10-31T19:59:00Z",
      "actual_end_time": "2025-10-31T21:02:00Z",
      "quality_metrics": {
        "video_codec": "MPEG2",
        "audio_codec": "AC3",
        "resolution": "1920x1080i",
        "bitrate_kbps": 15000,
        "dropped_packets": 0
      }
    },
    "file_info": {
      "exists": true,
      "readable": true,
      "created_at": "2025-10-31T19:59:00Z",
      "modified_at": "2025-10-31T21:02:00Z"
    },
    "series_info": {
      "series_rule_id": 5,
      "episode_number_in_series": 10,
      "total_episodes_recorded": 12
    }
  }
}
```

**Error Responses:**
- `404 Not Found` - Recording not found

---

### 3. Delete Recording

**Endpoint:** `DELETE /api/v1/library/:recording_id`

**Description:** Delete a completed recording and its file.

**Path Parameters:**
- `recording_id` - Recording identifier

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `delete_file` | boolean | No | true | Delete file from disk |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "deleted_file": true,
    "freed_space_bytes": 3456789012,
    "freed_space_gb": 3.22
  },
  "message": "Recording deleted successfully. 3.22 GB freed."
}
```

**Error Responses:**
- `404 Not Found` - Recording not found
- `500 Internal Server Error` - File deletion failed
  ```json
  {
    "success": false,
    "error": {
      "code": "STORAGE_ERROR",
      "message": "Failed to delete recording file",
      "details": {
        "file_path": "/recordings/Show/S01E01.ts",
        "error": "Permission denied"
      }
    }
  }
  ```

---

### 4. Bulk Delete Recordings

**Endpoint:** `POST /api/v1/library/bulk-delete`

**Description:** Delete multiple recordings at once.

**Request Body:**
```json
{
  "recording_ids": [100, 101, 102],
  "delete_files": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "deleted": [100, 101, 102],
    "failed": [],
    "freed_space_gb": 9.66
  },
  "message": "3 recordings deleted successfully. 9.66 GB freed."
}
```

**Partial Success Response (200):**
```json
{
  "success": true,
  "data": {
    "deleted": [100, 101],
    "failed": [
      {
        "recording_id": 102,
        "reason": "File not found"
      }
    ],
    "freed_space_gb": 6.44
  },
  "message": "2 of 3 recordings deleted. 6.44 GB freed."
}
```

---

### 5. Delete Series Recordings

**Endpoint:** `DELETE /api/v1/library/series/:series_id`

**Description:** Delete all recordings for a specific series.

**Path Parameters:**
- `series_id` - Series identifier

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `delete_files` | boolean | No | true | Delete files from disk |
| `keep_count` | integer | No | 0 | Keep N most recent episodes |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "deleted_count": 10,
    "kept_count": 2,
    "freed_space_gb": 32.2
  },
  "message": "10 episodes deleted, 2 kept. 32.2 GB freed."
}
```

---

### 6. Mark as Watched

**Endpoint:** `PATCH /api/v1/library/:recording_id/watched`

**Description:** Mark a recording as watched (for future watch tracking).

**Path Parameters:**
- `recording_id` - Recording identifier

**Request Body:**
```json
{
  "watched": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Recording marked as watched"
}
```

**Note:** Watch tracking is a future enhancement, not in MVP scope

---

### 7. Get Storage Statistics

**Endpoint:** `GET /api/v1/library/storage`

**Description:** Get storage usage statistics for the recording library.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "storage_path": "/mnt/recordings",
    "total_space_gb": 1000.0,
    "used_space_gb": 485.7,
    "free_space_gb": 514.3,
    "used_percentage": 48.6,
    "recordings_size_gb": 485.7,
    "recording_count": 156,
    "average_recording_size_gb": 3.11,
    "by_status": {
      "completed": {
        "count": 142,
        "size_gb": 450.2
      },
      "failed": {
        "count": 5,
        "size_gb": 2.1
      },
      "partial": {
        "count": 9,
        "size_gb": 33.4
      }
    },
    "top_series_by_size": [
      {
        "series_id": "SH012345678",
        "series_title": "Survivor",
        "count": 12,
        "size_gb": 42.5
      }
    ],
    "warning": {
      "low_space": true,
      "message": "Free space below 10 GB threshold",
      "threshold_gb": 10.0
    }
  }
}
```

---

### 8. Search Library

**Endpoint:** `GET /api/v1/library/search`

**Description:** Search completed recordings by title or metadata.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query |
| `series_only` | boolean | No | false | Only search series recordings |
| `limit` | integer | No | 50 | Results limit |
| `offset` | integer | No | 0 | Pagination offset |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "recording": { /* Recording Schema */ },
        "match_field": "title",
        "match_snippet": "...Survivor: Island of the Idols..."
      }
    ],
    "pagination": { /* Pagination Schema */ }
  }
}
```

---

### 9. Export Library Metadata

**Endpoint:** `GET /api/v1/library/export`

**Description:** Export library metadata as JSON or CSV for backup/analysis.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `format` | string | No | json | Export format (json, csv) |
| `include_failed` | boolean | No | false | Include failed recordings |

**Success Response (200) - JSON:**
```json
{
  "success": true,
  "data": {
    "export_date": "2025-10-31T22:00:00Z",
    "recordings": [
      { /* Full recording details */ }
    ]
  }
}
```

**Success Response (200) - CSV:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="library-export-2025-10-31.csv"

recording_id,title,episode,series,air_date,file_size_gb,status
100,"Survivor","S45E10","Survivor","2025-10-31",3.22,"completed"
...
```

---

### 10. Validate Library

**Endpoint:** `POST /api/v1/library/validate`

**Description:** Validate library integrity (check for missing/corrupted files).

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "total_recordings": 156,
    "validated": 156,
    "issues": [
      {
        "recording_id": 105,
        "issue": "file_missing",
        "file_path": "/recordings/Show/S01E05.ts",
        "suggested_action": "Delete database entry"
      },
      {
        "recording_id": 108,
        "issue": "file_size_mismatch",
        "expected_size": 3456789012,
        "actual_size": 1234567,
        "suggested_action": "Mark as partial or delete"
      }
    ]
  }
}
```

---

## Library Organization

### File Structure

```
{storage_path}/
├── {SeriesTitle}/
│   ├── S01E01 - Episode Title.ts
│   ├── S01E02 - Episode Title.ts
│   └── S01E03 - Episode Title.ts
├── Movies/
│   ├── Movie Title (2025-10-31).ts
│   └── Another Movie (2025-11-01).ts
└── OneTime/
    └── Special Program (2025-10-31 20-00).ts
```

### File Naming Conventions

**Series Episodes:**
- Format: `S{season:02d}E{episode:02d} - {episode_title}.ts`
- Example: `S45E10 - Island of the Idols.ts`

**Movies:**
- Format: `{title} ({air_date}).ts`
- Example: `The Matrix (2025-10-31).ts`

**Non-episodic/One-time:**
- Format: `{title} ({air_date} {time}).ts`
- Example: `Super Bowl LVIII (2025-02-11 18-30).ts`

### Metadata Sidecar Files (Optional)

For each recording, optional `.nfo` file:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<episodedetails>
  <title>Episode Title</title>
  <showtitle>Series Title</showtitle>
  <season>45</season>
  <episode>10</episode>
  <aired>2025-10-31</aired>
  <plot>Episode description...</plot>
  <runtime>60</runtime>
  <genre>Reality</genre>
</episodedetails>
```

Compatible with Plex, Kodi, Emby for automatic metadata recognition.

---

## Notes

### File Deletion Safety

- Database entry deleted first
- File deletion attempted second
- If file deletion fails, database entry remains deleted
- Orphaned files can be detected via validation endpoint

### Storage Warnings

- Warning triggered when free space < threshold (default 10 GB)
- Warning shown in UI and API responses
- Automatic cleanup not implemented in MVP (manual deletion only)

### Failed/Partial Recordings

- Failed recordings (0 bytes) can be auto-deleted
- Partial recordings retained for user review
- User can decide to keep or delete partial recordings

### Performance Considerations

- Library list queries optimized with indexes
- Large libraries (1000+ recordings) use pagination
- File size calculations cached in database
- Storage statistics cached for 5 minutes
