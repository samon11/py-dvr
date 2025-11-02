# PyDVR

A web-based DVR management interface for HDHomeRun network TV tuner devices. Schedule recordings, browse TV program schedules, and automatically capture live TV streams to disk.

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
- Schedules Direct subscription ($36/year) - [Sign up here](https://www.schedulesdirect.org/)
- Local network access to HDHomeRun device

## Quick Start

### 1. Installation

```bash
# Install from PyPI
pip install py-dvr

# Or for development, clone and install in editable mode
git clone https://github.com/samon11/py-dvr.git
cd py-dvr
pip install -e ".[dev]"
```

### 2. Configuration

```bash
# Run the interactive setup wizard
pydvr setup

# This will prompt you for:
# - HDHomeRun device IP address
# - Schedules Direct credentials
# - Recording directory path
# - Optional settings (server port, logging, etc.)
```

### 3. Sync Guide Data

```bash
# Run initial guide data sync (this will also initialize the database)
pydvr sync-guide

# Or specify more options
pydvr sync-guide --days 14
```

### 4. Run the Application

```bash
# Start the web server
pydvr server

# Or with custom options
pydvr server --port 9000

# For development with auto-reload
pydvr server --reload

# Access the web interface at:
# http://localhost:80
```

### 5. Running as a Background Process or on Startup

#### Linux - Using systemd (Starts on Boot)

Create a systemd service file:

```bash
# Create service file
sudo nano /etc/systemd/system/pydvr.service
```

Add the following content (replace `your-username` and paths):

```ini
[Unit]
Description=PyDVR - HDHomeRun DVR Service
After=network.target

[Service]
Type=simple
User=your-username
ExecStart=/usr/local/bin/pydvr server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable pydvr

# Start the service now
sudo systemctl start pydvr

# Check status
sudo systemctl status pydvr

# View logs
sudo journalctl -u pydvr -f
```

#### macOS - Using launchd (Starts on Boot)

Create a launch agent:

```bash
# Create directory if needed
mkdir -p ~/Library/LaunchAgents

# Create the plist file
nano ~/Library/LaunchAgents/com.pydvr.server.plist
```

Add this content (adjust the path to your pydvr executable):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.pydvr.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/pydvr</string>
        <string>server</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/pydvr.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/pydvr.error.log</string>
</dict>
</plist>
```

Load and start:

```bash
# Load the service (starts on boot)
launchctl load ~/Library/LaunchAgents/com.pydvr.server.plist

# To unload (disable)
launchctl unload ~/Library/LaunchAgents/com.pydvr.server.plist

# View logs
tail -f /tmp/pydvr.log
```

#### Windows - Using NSSM (Starts on Boot)

Install as a Windows service using [NSSM](https://nssm.cc/download):

```powershell
# Download NSSM from https://nssm.cc/download

# Install as a service (GUI method - recommended)
nssm install PyDVR

# Or command line (replace path with your Python Scripts directory)
nssm install PyDVR "C:\Python311\Scripts\pydvr.exe" "server"

# Start the service
nssm start PyDVR

# Check status
nssm status PyDVR

# Remove service if needed
nssm remove PyDVR
```

#### Quick Background Process (No Auto-Start)

If you just want to run in the background for the current session:

**Linux/macOS:**
```bash
# Using screen
screen -dmS pydvr pydvr server

# Reattach later
screen -r pydvr

# Or using nohup
nohup pydvr server &

# View logs
tail -f nohup.out
```

**Windows PowerShell:**
```powershell
# Run in background
Start-Process pydvr -ArgumentList "server" -WindowStyle Hidden
```

## Configuration

Configuration is stored in `~/.config/pydvr/config.yaml` (Linux/macOS) or `%APPDATA%\PyDVR\config.yaml` (Windows).

Run `pydvr paths` to see where configuration files are stored on your system.

To manually edit configuration:
```bash
# See where config is stored
pydvr paths

# Edit with your preferred editor
nano ~/.config/pydvr/config.yaml  # Linux/macOS
```

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
pydvr sync-guide
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
