"""
MultiCardz™ User Application.
Frontend application for spatial tag manipulation interface.
"""

import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.gzip import GZipMiddleware
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

    # Add GZip compression middleware (79KB savings!)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Configure cache TTLs from environment
    is_dev = os.getenv('ENV', 'development') == 'development'
    static_ttl = int(os.getenv('MULTICARDZ_STATIC_CACHE_TTL', '60' if is_dev else '31536000'))
    html_ttl = int(os.getenv('MULTICARDZ_HTML_CACHE_TTL', '10' if is_dev else '86400'))

    # Mount static files with cache headers
    class CachedStaticFiles(StaticFiles):
        def file_response(self, *args, **kwargs):
            response = super().file_response(*args, **kwargs)
            if not is_dev:
                response.headers["Cache-Control"] = f"public, max-age={static_ttl}, immutable"
            else:
                response.headers["Cache-Control"] = f"public, max-age={static_ttl}"
            return response

    app.mount("/static", CachedStaticFiles(directory="apps/static"), name="static")

    # Setup templates
    templates = Jinja2Templates(directory="apps/static/templates")

    # Include routers
    app.include_router(cards_router)

    # Main interface route with aggressive caching
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        # For now, serve a test interface with sample tags
        sample_tags = ["javascript", "python", "react", "fastapi", "testing", "ui", "backend"]
        sample_groups = []

        response = templates.TemplateResponse("user_home.html", {
            "request": request,
            "available_tags": sample_tags,
            "groups": sample_groups
        })

        # Set aggressive cache headers for HTML
        response.headers["Cache-Control"] = f"public, max-age={html_ttl}, s-maxage={html_ttl}"
        response.headers["Vary"] = "Accept-Encoding"

        return response

    logger.info("MultiCardz™ User Application initialized")
    return app


def main():
    """Run user application."""
    import uvicorn
    app = create_app()

    logger.info("Starting MultiCardz™ User Application")
    uvicorn.run(app, host="0.0.0.0", port=8011, reload=True)


if __name__ == "__main__":
    main()
