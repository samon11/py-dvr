"""
FastAPI application entry point.

This module implements the main FastAPI application with proper SOLID principles:
- Single Responsibility: Each function has one clear purpose
- Open/Closed: Easy to extend with new routes without modifying core code
- Dependency Inversion: Uses FastAPI's dependency injection system
"""

from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydvr.config import get_settings
from pydvr.logging_config import get_logger, setup_logging
from pydvr.paths import get_log_file
from pydvr.services.recorder import RecordingScheduler

# Initialize settings
settings = get_settings()

# Setup logging
setup_logging(
    log_level=settings.log_level,
    log_file=get_log_file() if not settings.debug else None,
)

# Get logger for this module
logger = get_logger(__name__)

# Initialize background scheduler for periodic jobs (like guide sync)
scheduler = AsyncIOScheduler()

# Initialize recording scheduler
recording_scheduler = RecordingScheduler()


async def sync_guide_data_job():
    """Background job for daily guide data sync.

    This job runs daily at 4 AM to synchronize guide data from Schedules Direct.
    It fetches lineups, stations, schedules, and program metadata for the next 3 days.
    """
    from pydvr.database import get_db
    from pydvr.services.guide_sync import GuideDataSync

    db = next(get_db())
    try:
        sync = GuideDataSync(db)
        result = await sync.sync_guide_data(days=7)
        logger.info(
            f"Guide sync completed: {result.schedules_updated} schedules, "
            f"{result.programs_updated} programs"
        )
    except Exception as e:
        logger.error(f"Guide sync failed: {e}", exc_info=True)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Manages startup and shutdown events for the FastAPI application.

    Startup:
    - Initializes background scheduler with daily guide sync at 4 AM
    - Starts recording scheduler for monitoring and executing recordings
    - Displays application configuration

    Shutdown:
    - Gracefully shuts down background scheduler
    - Stops recording scheduler
    - Performs cleanup tasks
    """
    from pydvr.database import _get_session_factory

    # Startup
    logger.info(f"PyDVR starting on {settings.host}:{settings.port}")
    logger.info(f"HDHomeRun device: {settings.hdhomerun_ip}")
    logger.info(f"Recording path: {settings.recording_path}")

    # Start background scheduler for periodic jobs
    # Daily sync at 4 AM
    scheduler.add_job(sync_guide_data_job, trigger="cron", hour=4, minute=0, id="daily_guide_sync")
    scheduler.start()
    logger.info("Background scheduler started - daily guide sync at 4 AM")

    # Start recording scheduler
    # This runs continuously, checking for upcoming recordings every 10 seconds
    import asyncio

    asyncio.create_task(recording_scheduler.start(db_session_factory=_get_session_factory()))
    logger.info("Recording scheduler started - monitoring for upcoming recordings")

    yield

    # Shutdown
    logger.info("PyDVR shutting down...")

    # Shutdown recording scheduler
    await recording_scheduler.stop()
    logger.info("Recording scheduler stopped")

    # Shutdown periodic scheduler
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")


# Initialize FastAPI application
app = FastAPI(
    title="PyDVR",
    description="Web-based DVR management interface for HDHomeRun network TV tuners",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Configure paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Configure Jinja2 templates
# Single Responsibility: Templates instance only handles template rendering
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static files for CSS, JavaScript, and images
# Static files are served at /static URL path
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register routers
from pydvr.routes import guide, lineups, recordings

app.include_router(lineups.router)
app.include_router(guide.router)
app.include_router(recordings.router)


# Health Check Endpoint
@app.get("/health", response_model=dict[str, str], tags=["System"])
async def health_check() -> JSONResponse:
    """
    Health check endpoint for monitoring application status.

    Returns:
        JSONResponse: Status indicating the application is healthy

    Example:
        >>> response = await health_check()
        >>> response.body
        {"status": "healthy"}
    """
    return JSONResponse(
        content={"status": "healthy"},
        status_code=200,
    )


# Root endpoint - renders home page
@app.get("/", response_class=HTMLResponse, tags=["Navigation"])
async def root(request: Request) -> HTMLResponse:
    """
    Root endpoint that renders the home page.

    In Phase 4, this may redirect to the guide page.
    For now, displays a welcome page with navigation cards.

    Args:
        request: FastAPI Request object for template context

    Returns:
        HTMLResponse: Rendered home page template
    """
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "hdhomerun_ip": settings.hdhomerun_ip,
            "recording_path": str(settings.recording_path),
        },
    )


if __name__ == "__main__":
    """
    Direct execution entry point.

    For development, use: uvicorn app.main:app --reload
    For production, use: uvicorn app.main:app --host 0.0.0.0 --port 8000
    """
    import uvicorn

    uvicorn.run(
        "pydvr.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
