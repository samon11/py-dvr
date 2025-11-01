"""Command-line interface for PyHDHRDVR.

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

from app.database import get_db, is_database_empty, run_migrations
from app.services.guide_sync import GuideDataSync


@click.group()
def cli():
    """PyHDHRDVR CLI - Command-line tools for DVR management."""
    pass


@cli.command()
@click.option("--days", default=3, help="Number of days to sync (default: 3)")
def sync_guide(days: int):
    """Manually trigger guide data sync.

    Synchronizes TV guide data from Schedules Direct for the specified
    number of days. This fetches lineups, stations, schedules, and
    program metadata.

    Examples:
        python -m app.cli sync-guide
        python -m app.cli sync-guide --days 7
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

    db = next(get_db())
    try:
        sync = GuideDataSync(db)
        result = asyncio.run(sync.sync_guide_data(days=days))

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
