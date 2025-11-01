"""
FastAPI application entry point.

This module implements the main FastAPI application with proper SOLID principles:
- Single Responsibility: Each function has one clear purpose
- Open/Closed: Easy to extend with new routes without modifying core code
- Dependency Inversion: Uses FastAPI's dependency injection system
"""

from pathlib import Path
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings

# Initialize settings
settings = get_settings()

# Initialize FastAPI application
app = FastAPI(
    title="PyHDHRDVR",
    description="Web-based DVR management interface for HDHomeRun network TV tuners",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
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


# Application Lifecycle Events
@app.on_event("startup")
async def startup_event() -> None:
    """
    Application startup event handler.

    Executes when the FastAPI application starts.
    Future tasks will add:
    - Database connection initialization
    - Background scheduler startup
    - External API client initialization
    """
    print(f"PyHDHRDVR starting on {settings.host}:{settings.port}")
    print(f"HDHomeRun device: {settings.hdhomerun_ip}")
    print(f"Recording path: {settings.recording_path}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Application shutdown event handler.

    Executes when the FastAPI application shuts down.
    Future tasks will add:
    - Database connection cleanup
    - Background scheduler shutdown
    - Graceful recording termination
    """
    print("PyHDHRDVR shutting down...")


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
