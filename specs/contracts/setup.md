# Setup Wizard API Contracts

## Overview

The setup wizard guides new users through initial system configuration. It consists of multiple steps that must be completed in order.

## Setup Flow

```
1. Welcome & Prerequisites Check
2. Schedules Direct Configuration
3. HDHomeRun Device Discovery
4. Storage Configuration
5. Lineup Selection & Channel Mapping
6. Completion & Initial Data Load
```

---

## Endpoints

### 1. Get Setup Status

**Endpoint:** `GET /api/v1/setup/status`

**Description:** Check if setup has been completed and current step.

**Success Response (200) - Setup Incomplete:**
```json
{
  "success": true,
  "data": {
    "setup_completed": false,
    "current_step": 2,
    "total_steps": 6,
    "completed_steps": [1],
    "next_step": {
      "step_number": 2,
      "step_name": "schedules_direct",
      "title": "Configure Schedules Direct"
    }
  }
}
```

**Success Response (200) - Setup Complete:**
```json
{
  "success": true,
  "data": {
    "setup_completed": true,
    "completed_at": "2025-10-31T15:00:00Z"
  }
}
```

---

### 2. Step 1: Welcome & Prerequisites

**Endpoint:** `GET /api/v1/setup/step1`

**Description:** Get welcome information and check prerequisites.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "step": 1,
    "title": "Welcome to PyDVR",
    "description": "Let's get your DVR system configured.",
    "prerequisites": {
      "python_version": {
        "required": "3.9+",
        "current": "3.11.5",
        "satisfied": true
      },
      "disk_space": {
        "required_gb": 50,
        "available_gb": 500,
        "satisfied": true
      },
      "network": {
        "has_internet": true,
        "has_local_network": true,
        "satisfied": true
      }
    },
    "requirements": [
      "HDHomeRun network tuner device",
      "Schedules Direct subscription ($25/year)",
      "Local storage for recordings"
    ],
    "can_proceed": true
  }
}
```

**Endpoint:** `POST /api/v1/setup/step1/complete`

**Request Body:**
```json
{
  "acknowledged": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Step 1 completed",
  "data": {
    "next_step": 2
  }
}
```

---

### 3. Step 2: Schedules Direct Configuration

**Endpoint:** `GET /api/v1/setup/step2`

**Description:** Get Schedules Direct configuration form.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "step": 2,
    "title": "Configure Schedules Direct",
    "description": "Enter your Schedules Direct credentials. Don't have an account? Sign up at schedulesdirect.org",
    "fields": [
      {
        "name": "username",
        "type": "email",
        "label": "Schedules Direct Username",
        "required": true
      },
      {
        "name": "password",
        "type": "password",
        "label": "Password",
        "required": true
      }
    ],
    "help_url": "https://www.schedulesdirect.org/signup"
  }
}
```

**Endpoint:** `POST /api/v1/setup/step2/validate`

**Description:** Validate Schedules Direct credentials without saving.

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
    "valid": true,
    "account_status": "active",
    "subscription_expires": "2026-03-15",
    "available_lineups": 3
  }
}
```

**Error Response (401):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```

**Endpoint:** `POST /api/v1/setup/step2/complete`

**Description:** Save Schedules Direct configuration.

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
  "message": "Schedules Direct configured successfully",
  "data": {
    "next_step": 3
  }
}
```

---

### 4. Step 3: HDHomeRun Device Discovery

**Endpoint:** `GET /api/v1/setup/step3`

**Description:** Get device discovery interface.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "step": 3,
    "title": "Find HDHomeRun Device",
    "description": "We'll scan your local network for HDHomeRun devices.",
    "options": [
      "automatic_discovery",
      "manual_entry"
    ]
  }
}
```

**Endpoint:** `POST /api/v1/setup/step3/discover`

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
        "tuner_count": 4,
        "selectable": true
      }
    ],
    "scan_duration_ms": 3000
  }
}
```

**No Devices Found:**
```json
{
  "success": true,
  "data": {
    "devices": [],
    "message": "No HDHomeRun devices found. Make sure your device is powered on and connected to the network.",
    "can_retry": true,
    "can_manual_entry": true
  }
}
```

**Endpoint:** `POST /api/v1/setup/step3/test-device`

**Description:** Test connection to specific device (for manual entry).

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
    "device_id": "12345ABC",
    "model": "HDHR5-4K",
    "firmware": "20231201",
    "tuner_count": 4,
    "connection_valid": true
  }
}
```

**Endpoint:** `POST /api/v1/setup/step3/complete`

**Description:** Select and save device configuration.

**Request Body:**
```json
{
  "device_id": "12345ABC",
  "ip_address": "192.168.1.100"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "HDHomeRun device configured successfully",
  "data": {
    "next_step": 4
  }
}
```

---

### 5. Step 4: Storage Configuration

**Endpoint:** `GET /api/v1/setup/step4`

**Description:** Get storage configuration form.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "step": 4,
    "title": "Configure Recording Storage",
    "description": "Choose where to store your recordings. Ensure the location has sufficient space.",
    "fields": [
      {
        "name": "storage_path",
        "type": "path",
        "label": "Recording Storage Path",
        "required": true,
        "help": "Absolute path to directory for recordings"
      },
      {
        "name": "warning_threshold_gb",
        "type": "number",
        "label": "Low Space Warning Threshold (GB)",
        "required": false,
        "default": 10
      }
    ],
    "recommendations": {
      "minimum_space_gb": 50,
      "recommended_space_gb": 500,
      "typical_recording_size_gb": 3
    }
  }
}
```

**Endpoint:** `POST /api/v1/setup/step4/validate`

**Description:** Validate storage path without saving.

**Request Body:**
```json
{
  "storage_path": "/mnt/recordings"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "path_valid": true,
    "path_exists": true,
    "writable": true,
    "total_space_gb": 1000,
    "free_space_gb": 900,
    "sufficient_space": true
  }
}
```

**Error Response (400):**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Storage path validation failed",
    "details": {
      "path_exists": false,
      "writable": false,
      "error": "Directory does not exist"
    }
  }
}
```

**Endpoint:** `POST /api/v1/setup/step4/complete`

**Description:** Save storage configuration.

**Request Body:**
```json
{
  "storage_path": "/mnt/recordings",
  "warning_threshold_gb": 10,
  "create_directory": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Storage configured successfully",
  "data": {
    "next_step": 5
  }
}
```

---

### 6. Step 5: Lineup Selection & Channel Mapping

**Endpoint:** `GET /api/v1/setup/step5`

**Description:** Get available lineups and channel mapping interface.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "step": 5,
    "title": "Select TV Lineup",
    "description": "Choose your TV lineup and configure channels.",
    "available_lineups": [
      {
        "lineup_id": "USA-OTA-02134",
        "name": "Boston OTA",
        "location": "Boston, MA",
        "type": "Antenna",
        "station_count": 45
      },
      {
        "lineup_id": "USA-XFINITY-Boston",
        "name": "Xfinity Boston",
        "location": "Boston, MA",
        "type": "Cable",
        "station_count": 250
      }
    ]
  }
}
```

**Endpoint:** `POST /api/v1/setup/step5/select-lineup`

**Description:** Select a lineup and retrieve its stations.

**Request Body:**
```json
{
  "lineup_id": "USA-OTA-02134"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "lineup": {
      "lineup_id": "USA-OTA-02134",
      "name": "Boston OTA",
      "type": "Antenna",
      "station_count": 45
    },
    "stations": [
      {
        "station_id": "12345",
        "callsign": "WGBH",
        "channel_number": "2.1",
        "name": "WGBH Boston",
        "affiliate": "PBS",
        "enabled": true
      }
    ]
  }
}
```

**Endpoint:** `POST /api/v1/setup/step5/channel-scan`

**Description:** Optionally scan for available channels using HDHomeRun.

**Success Response (202):**
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

**Endpoint:** `POST /api/v1/setup/step5/complete`

**Description:** Save lineup and channel selections.

**Request Body:**
```json
{
  "lineup_id": "USA-OTA-02134",
  "enabled_stations": ["12345", "12346", "12347"]
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Lineup configured successfully",
  "data": {
    "next_step": 6,
    "enabled_station_count": 42
  }
}
```

---

### 7. Step 6: Completion & Initial Data Load

**Endpoint:** `GET /api/v1/setup/step6`

**Description:** Get completion status and initial data load progress.

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "step": 6,
    "title": "Setup Complete",
    "description": "Your DVR is now configured. We're loading guide data...",
    "initial_load": {
      "status": "in_progress",
      "started_at": "2025-10-31T15:00:00Z",
      "progress_percentage": 65,
      "current_task": "Fetching program metadata",
      "estimated_completion": "2025-10-31T15:05:00Z"
    }
  }
}
```

**Success Response (200) - Load Complete:**
```json
{
  "success": true,
  "data": {
    "step": 6,
    "title": "Setup Complete",
    "description": "Your DVR is ready to use!",
    "initial_load": {
      "status": "completed",
      "completed_at": "2025-10-31T15:05:00Z",
      "stations_loaded": 42,
      "schedules_loaded": 52340,
      "programs_loaded": 23456
    },
    "next_actions": [
      "Browse the program guide",
      "Search for shows to record",
      "Create series recording rules"
    ]
  }
}
```

**Endpoint:** `POST /api/v1/setup/step6/complete`

**Description:** Mark setup as complete and redirect to main application.

**Success Response (200):**
```json
{
  "success": true,
  "message": "Setup completed successfully",
  "data": {
    "redirect_url": "/dashboard"
  }
}
```

---

### 8. Reset Setup

**Endpoint:** `POST /api/v1/setup/reset`

**Description:** Reset setup wizard (for troubleshooting or reconfiguration).

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `confirm` | boolean | Yes | - | Must be true to confirm |

**Success Response (200):**
```json
{
  "success": true,
  "message": "Setup reset successfully. All configuration cleared.",
  "data": {
    "redirect_url": "/setup/step1"
  }
}
```

**Warning:** This clears all configuration but does not delete recorded files or database data.

---

## Setup State Management

### State Persistence

Setup progress stored in configuration:
```json
{
  "setup_completed": false,
  "setup_current_step": 3,
  "setup_completed_steps": [1, 2],
  "setup_started_at": "2025-10-31T14:00:00Z"
}
```

### Step Dependencies

Steps must be completed in order:
1. Step 1 → Step 2 (always allowed)
2. Step 2 → Step 3 (requires valid SD credentials)
3. Step 3 → Step 4 (requires device selected)
4. Step 4 → Step 5 (requires storage configured)
5. Step 5 → Step 6 (requires lineup selected)
6. Step 6 → Complete (requires initial data load)

### Skipping Steps

Cannot skip steps, but can go back to previous steps to modify:
- `POST /api/v1/setup/goto/:step_number`
- Only allowed if step was previously completed

---

## Setup Validation Summary

### Step 2 Validation
- ✅ Schedules Direct credentials valid
- ✅ Account is active
- ✅ Subscription not expired

### Step 3 Validation
- ✅ Device reachable on network
- ✅ Device responds to API calls
- ✅ Tuner count > 0

### Step 4 Validation
- ✅ Storage path exists or can be created
- ✅ Path is writable
- ✅ Sufficient free space (>50 GB recommended)

### Step 5 Validation
- ✅ At least one lineup selected
- ✅ At least one station enabled
- ✅ Stations mapped to Schedules Direct data

### Step 6 Validation
- ✅ Initial guide data loaded
- ✅ No critical errors during setup

---

## Error Handling

### Common Setup Errors

**Schedules Direct Connection Failed:**
```json
{
  "success": false,
  "error": {
    "code": "EXTERNAL_SERVICE_ERROR",
    "message": "Unable to connect to Schedules Direct",
    "details": {
      "service": "schedules_direct",
      "suggestion": "Check your internet connection and try again"
    }
  }
}
```

**HDHomeRun Not Found:**
```json
{
  "success": false,
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "No HDHomeRun devices found on network",
    "details": {
      "suggestion": "Ensure device is powered on and connected to network. Try manual IP entry."
    }
  }
}
```

**Storage Path Invalid:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Storage path is not writable",
    "details": {
      "path": "/mnt/recordings",
      "issue": "Permission denied",
      "suggestion": "Check directory permissions or choose different path"
    }
  }
}
```

---

## Notes

### Setup Time Estimate

- Step 1: < 1 minute
- Step 2: 1-2 minutes (credential entry + validation)
- Step 3: 2-3 minutes (device discovery + testing)
- Step 4: 1-2 minutes (path entry + validation)
- Step 5: 3-5 minutes (lineup selection + channel configuration)
- Step 6: 5-10 minutes (initial guide data load)

**Total: 15-25 minutes**

### First-Time Experience

- Setup wizard shown on first application launch
- Cannot access main application until setup complete
- Progress saved, can resume if interrupted
- Can restart setup from beginning if needed

### Reconfiguration

After initial setup, settings can be changed via:
- Settings page (not setup wizard)
- Individual configuration endpoints
- Reset setup only for complete reconfiguration
