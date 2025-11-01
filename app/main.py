"""
FastAPI application entry point.

This module implements the main FastAPI application with proper SOLID principles:
- Single Responsibility: Each function has one clear purpose
- Open/Closed: Easy to extend with new routes without modifying core code
- Dependency Inversion: Uses FastAPI's dependency injection system
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings

# Initialize settings
settings = get_settings()

# Initialize background scheduler
scheduler = AsyncIOScheduler()


async def sync_guide_data_job():
    """Background job for daily guide data sync.

    This job runs daily at 4 AM to synchronize guide data from Schedules Direct.
    It fetches lineups, stations, schedules, and program metadata for the next 3 days.
    """
    from app.database import get_db
    from app.services.guide_sync import GuideDataSync

    db = next(get_db())
    try:
        sync = GuideDataSync(db)
        result = await sync.sync_guide_data(days=3)
        print(f"Guide sync completed: {result.schedules_updated} schedules, "
              f"{result.programs_updated} programs")
    except Exception as e:
        print(f"Guide sync failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Manages startup and shutdown events for the FastAPI application.

    Startup:
    - Initializes background scheduler with daily guide sync at 4 AM
    - Displays application configuration

    Shutdown:
    - Gracefully shuts down background scheduler
    - Performs cleanup tasks
    """
    # Startup
    print(f"PyHDHRDVR starting on {settings.host}:{settings.port}")
    print(f"HDHomeRun device: {settings.hdhomerun_ip}")
    print(f"Recording path: {settings.recording_path}")

    # Start background scheduler
    # Daily sync at 4 AM
    scheduler.add_job(
        sync_guide_data_job,
        trigger="cron",
        hour=4,
        minute=0,
        id="daily_guide_sync"
    )
    scheduler.start()
    print("Background scheduler started - daily guide sync at 4 AM")

    yield

    # Shutdown
    print("PyHDHRDVR shutting down...")

    # Shutdown scheduler
    if scheduler.running:
        scheduler.shutdown()
        print("Background scheduler stopped")


# Initialize FastAPI application
app = FastAPI(
    title="PyHDHRDVR",
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
from app.routes import lineups
app.include_router(lineups.router)


# Health Check Endpoint
@app.get("/health", response_model=Dict[str, str], tags=["System"])
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
        }
    )


if __name__ == "__main__":
    """
    Direct execution entry point.

    For development, use: uvicorn app.main:app --reload
    For production, use: uvicorn app.main:app --host 0.0.0.0 --port 8000
    """
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
