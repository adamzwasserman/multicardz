"""
MultiCardz™ User Application.
Frontend application for spatial tag manipulation interface.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging

# Import routers
from .routes.cards_api import router as cards_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """Create FastAPI application instance."""
    app = FastAPI(
        title="MultiCardz™ User Application",
        description="Frontend application for spatial tag manipulation interface",
        version="1.0.0"
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="apps/static"), name="static")

    # Setup templates
    templates = Jinja2Templates(directory="apps/static/templates")

    # Include routers
    app.include_router(cards_router)

    # Main interface route
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        # For now, serve a test interface with sample tags
        sample_tags = ["javascript", "python", "react", "fastapi", "testing", "ui", "backend"]
        sample_groups = []

        return templates.TemplateResponse("user_home.html", {
            "request": request,
            "available_tags": sample_tags,
            "groups": sample_groups
        })

    logger.info("MultiCardz™ User Application initialized")
    return app


def main():
    """Run user application."""
    import uvicorn
    app = create_app()

    logger.info("Starting MultiCardz™ User Application")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
