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

from pydvr.database import get_db, is_database_empty, run_migrations
from pydvr.services.guide_sync import GuideDataSync

@click.group()
def cli():
    """PyDVR CLI - Command-line tools for DVR management."""
    pass


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
