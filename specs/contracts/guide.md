# Program Guide API Contracts

## Endpoints

### 1. Get Program Guide (Grid View)

**Endpoint:** `GET /api/v1/guide`

**Description:** Retrieve program schedule for multiple channels in a time range.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_time` | datetime | No | Now | Start of time range (ISO 8601 UTC) |
| `end_time` | datetime | No | +4 hours | End of time range (ISO 8601 UTC) |
| `station_ids` | string[] | No | All enabled | Comma-separated station IDs |
| `enabled_only` | boolean | No | true | Only include enabled stations |

**Example Request:**
```
GET /api/v1/guide?start_time=2025-10-31T20:00:00Z&end_time=2025-11-01T00:00:00Z&station_ids=12345,12346
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "start_time": "2025-10-31T20:00:00Z",
    "end_time": "2025-11-01T00:00:00Z",
    "stations": [
      {
        "station": { /* Station Schema */ },
        "schedules": [
          { /* Schedule Schema */ },
          { /* Schedule Schema */ }
        ]
      }
    ]
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid time range
- `500 Internal Server Error` - Database error

---

### 2. Get Program Details

**Endpoint:** `GET /api/v1/programs/:program_id`

**Description:** Retrieve detailed information about a specific program.

**Path Parameters:**
- `program_id` - Schedules Direct program ID

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "program": { /* Full Program Schema */ },
    "upcoming_airings": [
      { /* Schedule Schema */ },
      { /* Schedule Schema */ }
    ],
    "is_recorded": false,
    "is_scheduled": true,
    "has_series_rule": false
  }
}
```

**Fields:**
- `upcoming_airings` - All future airings within guide data range (14 days)
- `is_recorded` - True if any airing has been recorded
- `is_scheduled` - True if any airing is scheduled for recording
- `has_series_rule` - True if active series rule exists

**Error Responses:**
- `404 Not Found` - Program not found

---

### 3. Get Schedule Details

**Endpoint:** `GET /api/v1/schedules/:schedule_id`

**Description:** Retrieve details about a specific program airing.

**Path Parameters:**
- `schedule_id` - Unique schedule identifier

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "schedule": { /* Full Schedule Schema with nested program and station */ },
    "recording": { /* Recording Schema if scheduled */ },
    "conflicts": [
      {
        "recording_id": 125,
        "program_title": "Conflicting Show",
        "start_time": "2025-10-31T20:30:00Z"
      }
    ]
  }
}
```

**Fields:**
- `recording` - Null if not scheduled for recording
- `conflicts` - Empty array if no conflicts

**Error Responses:**
- `404 Not Found` - Schedule not found

---

### 4. Search Programs

**Endpoint:** `GET /api/v1/search`

**Description:** Search for programs by title, description, or metadata.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (min 2 chars) |
| `start_date` | date | No | Today | Start of date range |
| `end_date` | date | No | +14 days | End of date range |
| `station_ids` | string[] | No | All | Filter by station IDs |
| `genres` | string[] | No | All | Filter by genres |
| `new_only` | boolean | No | false | Only new episodes |
| `limit` | integer | No | 50 | Results per page (max 200) |
| `offset` | integer | No | 0 | Pagination offset |

**Example Request:**
```
GET /api/v1/search?query=survivor&new_only=true&genres=Reality
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "query": "survivor",
    "results": [
      {
        "program": { /* Program Schema */ },
        "next_airing": { /* Schedule Schema */ },
        "total_airings": 5,
        "is_scheduled": false,
        "has_series_rule": false
      }
    ],
    "pagination": {
      "limit": 50,
      "offset": 0,
      "total": 3,
      "has_more": false
    }
  }
}
```

**Fields:**
- `results` - Array of matching programs
- `next_airing` - Earliest upcoming airing
- `total_airings` - Count of airings in date range

**Error Responses:**
- `400 Bad Request` - Query too short or invalid parameters

---

### 5. Get Channel List

**Endpoint:** `GET /api/v1/stations`

**Description:** Retrieve list of all stations/channels.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `enabled_only` | boolean | No | false | Only enabled stations |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "stations": [
      { /* Station Schema */ }
    ]
  }
}
```

---

### 6. Update Station Settings

**Endpoint:** `PATCH /api/v1/stations/:station_id`

**Description:** Update station settings (enable/disable).

**Path Parameters:**
- `station_id` - Station identifier

**Request Body:**
```json
{
  "enabled": false
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "station": { /* Updated Station Schema */ }
  },
  "message": "Station updated successfully"
}
```

**Error Responses:**
- `404 Not Found` - Station not found
- `400 Bad Request` - Invalid input

---

### 7. Browse by Genre

**Endpoint:** `GET /api/v1/guide/genres/:genre`

**Description:** Get programs in specific genre within time range.

**Path Parameters:**
- `genre` - Genre name (e.g., "Sports", "Movies", "Drama")

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_time` | datetime | No | Now | Start of time range |
| `end_time` | datetime | No | +7 days | End of time range |
| `limit` | integer | No | 50 | Results limit |
| `offset` | integer | No | 0 | Pagination offset |

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "genre": "Movies",
    "schedules": [
      { /* Schedule Schema with nested program */ }
    ],
    "pagination": { /* Pagination Schema */ }
  }
}
```

---

### 8. Get Available Genres

**Endpoint:** `GET /api/v1/genres`

**Description:** Get list of all genres in guide data.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "genres": [
      {
        "name": "Drama",
        "count": 150
      },
      {
        "name": "Comedy",
        "count": 89
      }
    ]
  }
}
```

**Fields:**
- `count` - Number of programs in genre

---

## Notes

### Time Ranges

- Default guide view: 4 hours
- Maximum time range per request: 24 hours
- Guide data available: 14 days forward

### Search Performance

- Minimum query length: 2 characters
- Search indexes: title, episode_title, description
- Results grouped by series when applicable

### Caching

- Guide data cached for 1 hour (client-side caching recommended)
- Stale data served if Schedules Direct unavailable
- Cache header: `Cache-Control: public, max-age=3600`
