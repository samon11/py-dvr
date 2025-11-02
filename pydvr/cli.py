"""Command-line interface for PyDVR.

This module provides CLI commands for managing the DVR system,
including manual guide data synchronization and other administrative tasks.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import asyncio

import click
import yaml

from pydvr.database import get_db, is_database_empty, run_migrations
from pydvr.paths import (
    get_app_data_dir,
    get_cache_dir,
    get_config_dir,
    get_config_file,
    get_log_dir,
    print_paths,
)
from pydvr.services.guide_sync import GuideDataSync


@click.group()
def cli():
    """PyDVR CLI - Command-line tools for DVR management."""
    pass


@cli.command()
def setup():
    """Interactive setup wizard for first-time configuration.

    Guides you through configuring PyDVR by prompting for required settings
    and creating a config.yaml file in your user config directory.

    This is the recommended way to configure PyDVR for the first time.

    Examples:
        pydvr setup
    """
    click.echo(click.style("=" * 70, fg="cyan"))
    click.echo(click.style("  PyDVR Setup Wizard", fg="cyan", bold=True))
    click.echo(click.style("=" * 70, fg="cyan"))
    click.echo()

    # Show where config will be saved
    config_file = get_config_file()
    click.echo(f"Configuration will be saved to: {click.style(str(config_file), fg='green')}")
    click.echo()

    # Check if config already exists
    if config_file.exists():
        click.echo(click.style("⚠️  Warning: Configuration file already exists!", fg="yellow"))
        if not click.confirm("Do you want to overwrite it?", default=False):
            click.echo("Setup cancelled.")
            return
        click.echo()

    config = {}

    # HDHomeRun Configuration
    click.echo(click.style("📺 HDHomeRun Configuration", fg="blue", bold=True))
    click.echo("Enter the IP address of your HDHomeRun device on your local network.")
    click.echo("You can find this in the HDHomeRun app or your router's DHCP list.")
    hdhomerun_ip = click.prompt("HDHomeRun IP address", type=str, default="192.168.1.100")
    config["hdhomerun"] = {"ip": hdhomerun_ip}
    click.echo()

    # Schedules Direct Configuration
    click.echo(click.style("📅 Schedules Direct Configuration", fg="blue", bold=True))
    click.echo("Schedules Direct provides TV guide data ($25/year subscription).")
    click.echo("Sign up at: https://www.schedulesdirect.org/")
    sd_username = click.prompt("Schedules Direct username", type=str)
    sd_password = click.prompt("Schedules Direct password", type=str, hide_input=True)
    config["schedules_direct"] = {"username": sd_username, "password": sd_password}
    click.echo()

    # Recording Path Configuration
    click.echo(click.style("💾 Recording Storage", fg="blue", bold=True))
    click.echo("Specify where recordings should be saved.")
    click.echo("The directory will be created if it doesn't exist.")
    default_recording_path = str(Path.home() / "PyDVR-Recordings")
    recording_path = click.prompt("Recording directory path", type=str, default=default_recording_path)

    # Try to create the recording directory
    try:
        Path(recording_path).mkdir(parents=True, exist_ok=True)
        click.echo(click.style(f"✓ Recording directory created: {recording_path}", fg="green"))
    except Exception as e:
        click.echo(click.style(f"⚠️  Warning: Could not create directory: {e}", fg="yellow"))

    config["recording"] = {"path": recording_path}
    click.echo()

    # Optional Settings
    if click.confirm("Do you want to configure optional settings?", default=False):
        click.echo()
        click.echo(click.style("⚙️  Optional Settings", fg="blue", bold=True))

        # Database URL
        database_url = click.prompt(
            "Database URL (leave default for SQLite)",
            type=str,
            default="default"
        )
        if database_url != "default":
            config["database"] = {"url": database_url}

        # Padding settings
        padding_start = click.prompt(
            "Seconds to start recording early",
            type=int,
            default=60
        )
        padding_end = click.prompt(
            "Seconds to continue recording late",
            type=int,
            default=120
        )
        config["recording"]["padding_start"] = padding_start
        config["recording"]["padding_end"] = padding_end

        # Server settings
        host = click.prompt("Server host", type=str, default="0.0.0.0")
        port = click.prompt("Server port", type=int, default=80)
        debug = click.confirm("Enable debug mode?", default=False)
        log_level = click.prompt(
            "Log level",
            type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
            default="INFO"
        )

        config["server"] = {
            "host": host,
            "port": port,
            "debug": debug,
            "log_level": log_level
        }
        click.echo()

    # Write config.yaml file
    click.echo(click.style("💾 Saving configuration...", fg="blue"))

    try:
        # Ensure config directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, "w") as f:
            f.write("# PyDVR Configuration\n")
            f.write("# Generated by PyDVR setup wizard\n")
            f.write("# Edit this file to customize your settings\n\n")
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        click.echo(click.style(f"✓ Configuration saved to {config_file}", fg="green"))
        click.echo()

        # Show all directories
        click.echo(click.style("📁 PyDVR Directory Locations:", fg="blue", bold=True))
        click.echo(f"  Config:  {get_config_dir()}")
        click.echo(f"  Data:    {get_app_data_dir()}")
        click.echo(f"  Logs:    {get_log_dir()}")
        click.echo(f"  Cache:   {get_cache_dir()}")
        click.echo()

        # Offer to initialize database
        if click.confirm("Do you want to initialize the database now?", default=True):
            click.echo(click.style("🗄️  Initializing database...", fg="blue"))
            try:
                run_migrations()
                click.echo(click.style("✓ Database initialized successfully!", fg="green"))
            except Exception as e:
                click.echo(click.style(f"⚠️  Database initialization failed: {e}", fg="red"))
                click.echo("You can initialize it later with: pydvr sync-guide")

        click.echo()
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo(click.style("✨ Setup Complete!", fg="green", bold=True))
        click.echo(click.style("=" * 70, fg="cyan"))
        click.echo()
        click.echo("Next steps:")
        click.echo("  1. Run 'pydvr sync-guide' to download TV guide data")
        click.echo("  2. Run 'pydvr server' to start the web interface")
        port_num = config.get("server", {}).get("port", 80)
        click.echo(f"  3. Open http://localhost:{port_num} in your browser")
        click.echo()

    except Exception as e:
        click.echo(click.style(f"✗ Failed to save configuration: {e}", fg="red"), err=True)
        raise


@cli.command()
def paths():
    """Show PyDVR directory and file locations.

    Displays where PyDVR stores configuration, data, logs, and cache files.
    Useful for troubleshooting and understanding where files are stored.

    Examples:
        pydvr paths
    """
    print_paths()



@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
@click.option("--port", default=80, help="Port to bind to (default: 80)")
@click.option("--reload", is_flag=True, help="Enable auto-reload (for development)")
def server(host: str, port: int, reload: bool):
    """Start the PyDVR web server.

    Starts the FastAPI web application for managing recordings and browsing
    the TV guide. The web interface will be available at http://HOST:PORT

    Examples:
        pydvr server
        pydvr server --port 9000
        pydvr server --reload  # Development mode with auto-reload
    """
    import uvicorn

    click.echo(f"Starting PyDVR server on http://{host}:{port}")
    if reload:
        click.echo(click.style("Auto-reload enabled (development mode)", fg="yellow"))

    uvicorn.run(
        "pydvr.main:app",
        host=host,
        port=port,
        reload=reload
    )


@cli.command()
@click.option("--days", default=7, help="Number of days to sync (default: 7)")
@click.option("--no-cleanup", is_flag=True, help="Skip cleanup of old data")
@click.option("--keep-days", default=7, help="Days of past data to keep during cleanup (default: 7)")
def sync_guide(days: int, no_cleanup: bool, keep_days: int):
    """Manually trigger guide data sync.

    Synchronizes TV guide data from Schedules Direct for the specified
    number of days. This fetches lineups, stations, schedules, and
    program metadata.

    By default, old schedules and orphaned programs are cleaned up to save
    disk space. Use --no-cleanup to skip cleanup, or --keep-days to control
    how much past data is retained.

    Examples:
        pydvr sync-guide
        pydvr sync-guide --days 7
        pydvr sync-guide --no-cleanup
        pydvr sync-guide --keep-days 14
    """
    # Check if database needs initialization
    if is_database_empty():
        click.echo(click.style("Database is empty. Running migrations...", fg="yellow"))
        try:
            run_migrations()
            click.echo(click.style("Migrations completed successfully!", fg="green"))
        except Exception as e:
            click.echo(click.style(f"Migration failed: {e}", fg="red"), err=True)
            raise

    click.echo(f"Starting guide data sync for {days} days...")
    if no_cleanup:
        click.echo("Cleanup disabled - old data will not be removed")
    else:
        click.echo(f"Cleanup enabled - will keep {keep_days} days of past data")

    db = next(get_db())
    try:
        sync = GuideDataSync(db)
        result = asyncio.run(sync.sync_guide_data(days=days, cleanup=not no_cleanup, keep_days=keep_days))

        if result.status == "completed":
            click.echo(click.style("Sync completed successfully!", fg="green"))
            click.echo(f"  Lineups: {result.lineups_updated}")
            click.echo(f"  Stations: {result.stations_updated}")
            click.echo(f"  Schedules: {result.schedules_updated}")
            click.echo(f"  Programs: {result.programs_updated}")
            if result.duration_seconds:
                click.echo(f"  Duration: {result.duration_seconds:.2f} seconds")
        else:
            click.echo(click.style(f"Sync failed: {result.error_message}", fg="red"), err=True)

    except Exception as e:
        click.echo(click.style(f"Sync failed: {e}", fg="red"), err=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    cli()
