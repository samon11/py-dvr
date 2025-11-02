# PyDVR

A web-based DVR management interface for HDHomeRun network TV tuner devices. Schedule recordings, browse TV program schedules, and automatically capture live TV streams to disk.

> **Status:** MVP Development - Alpha stage

## Features

- Browse TV program schedules from Schedules Direct
- Invokes [Schedules Direct API](https://github.com/SchedulesDirect/JSON-Service/wiki/API-20141201) for guide data
- Schedule one-time recordings
- Automatic recording execution with configurable padding
- Simple web interface for recording management
- Original quality MPEG-TS recordings (no transcoding)
- SQLite database for guide data and recording history

## Requirements

- Python 3.11 or higher
- HDHomeRun network TV tuner device
- Schedules Direct subscription ($25/year) - [Sign up here](https://www.schedulesdirect.org/)
- Local network access to HDHomeRun device

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pyhdhrdvr.git
cd pyhdhrdvr

# Install dependencies
pip install -e .

# For development (includes testing tools)
pip install -e ".[dev]"
```

### 2. Configuration

```bash
# Copy the example configuration file
cp .env.example .env

# Edit .env with your settings
# - Set HDHOMERUN_IP to your device's IP address
# - Set SD_USERNAME and SD_PASSWORD with your Schedules Direct credentials
# - Set RECORDING_PATH to where you want recordings saved
```

### 3. Database Setup

```bash
# Initialize the database
alembic upgrade head
```

### 4. Sync Guide Data

```bash
# Run initial guide data sync (this may take a few minutes)
python -m app.cli sync-guide
```

### 5. Run the Application

```bash
# Start the web server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access the web interface at:
# http://localhost:8000
```

## Configuration

All configuration is done via the `.env` file. See `.env.example` for all available options.

### Required Settings

- `HDHOMERUN_IP` - IP address of your HDHomeRun device
- `SD_USERNAME` - Your Schedules Direct username (email)
- `SD_PASSWORD` - Your Schedules Direct password
- `RECORDING_PATH` - Directory where recordings will be saved

### Optional Settings

- `DATABASE_URL` - Database connection string (default: SQLite)
- `DEFAULT_PADDING_START` - Seconds to start recording early (default: 60)
- `DEFAULT_PADDING_END` - Seconds to continue after scheduled end (default: 120)

## Usage

### Browsing the Guide

Navigate to the Guide page to see upcoming TV programs. Programs are organized by channel and show the next 12 hours.

### Scheduling Recordings

Click the "Record" button next to any program to schedule a one-time recording. The recording will start automatically at the scheduled time (minus padding).

### Managing Recordings

- **Scheduled** - View upcoming recordings and cancel if needed
- **Recordings** - View completed recordings, file paths, and manage storage

### Syncing Guide Data

Guide data should be refreshed periodically:

```bash
python -m app.cli sync-guide
```

> **Note:** Automatic daily sync is planned for post-MVP.

## Architecture

- **Backend:** FastAPI (Python 3.13+)
- **Database:** SQLite with SQLAlchemy ORM and Alembic migrations
- **Templates:** Jinja2 server-side rendering
- **Recording Format:** MPEG-TS (original transport stream)
- **Scheduler:** APScheduler for background recording tasks

### Directory Structure

```
pyhdhrdvr/
├── app/                    # Main application code
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Configuration management
│   ├── models/            # Database models
│   ├── services/          # Business logic & API clients
│   └── routes/            # HTTP route handlers
├── templates/             # Jinja2 HTML templates
├── static/                # CSS, JavaScript, images
├── tests/                 # Test files
└── specs/                 # Design documentation
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Database Migrations

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Code Quality

This project uses Ruff for linting and formatting:

```bash
# Check code
ruff check .

# Format code
ruff format .
```

## Troubleshooting

### "No tuner available" errors

- Check if other applications are using the HDHomeRun (Plex, Kodi, VLC, etc.)
- Verify the device is online: `curl http://{HDHOMERUN_IP}/discover.json`
- Check tuner count vs. concurrent recordings scheduled

### Guide data not loading

- Verify your Schedules Direct credentials are correct
- Check your subscription is active (renews annually)
- Test manually: `curl -u username:password https://json.schedulesdirect.org/20141201/token`

### Recordings fail immediately

- Verify `RECORDING_PATH` exists and is writable
- Check available disk space (need ~2-4 GB per hour for HD)
- Verify channel number matches your lineup
- Test channel with official HDHomeRun app

## MVP Scope

This is the MVP (Minimum Viable Product) version. Current features:

✅ One-time recording scheduling
✅ Basic web interface
✅ Manual guide data sync
✅ Simple list-based guide view

### Coming in Future Versions

- Series recording rules with auto-scheduling
- Grid-based program guide
- Search functionality
- Conflict detection and resolution
- Setup wizard with device auto-discovery
- System monitoring dashboard
- Automatic guide data refresh

## License

MIT License. See `LICENSE` file for details.

## Contributing

This project is in early development. Contributions welcome!

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the detailed specs in the `specs/` directory
- Open an issue on GitHub

## Acknowledgments

- [HDHomeRun](https://www.silicondust.com/) for their excellent network TV tuners
- [Schedules Direct](https://www.schedulesdirect.org/) for providing TV guide data
