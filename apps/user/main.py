"""
MultiCardz™ User Application.
Frontend application for spatial tag manipulation interface.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time

# Import routers
from .routes.cards_api import router as cards_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServerTimingMiddleware(BaseHTTPMiddleware):
    """Add Server-Timing headers to track backend response time."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        process_time_ms = process_time * 1000

        # Add detailed Server-Timing headers
        timing_entries = [
            f"backend;dur={process_time_ms:.2f};desc=\"Backend processing\"",
        ]

        # Add route-specific timing info
        if hasattr(request, 'url') and request.url.path.startswith('/api/'):
            timing_entries.append(f"api;dur={process_time_ms:.2f};desc=\"API endpoint\"")
        elif hasattr(request, 'url') and request.url.path == '/':
            timing_entries.append(f"page;dur={process_time_ms:.2f};desc=\"Page render\"")

        response.headers["Server-Timing"] = ", ".join(timing_entries)

        return response


def create_app():
    """Create FastAPI application instance."""
    app = FastAPI(
        title="MultiCardz™ User Application",
        description="Frontend application for spatial tag manipulation interface",
        version="1.0.0"
    )

    # Add performance monitoring middleware
    app.add_middleware(ServerTimingMiddleware)

    # Mount static files
    app.mount("/static", StaticFiles(directory="apps/static"), name="static")

    # Setup templates
    templates = Jinja2Templates(directory="apps/static/templates")

    # Include routers
    app.include_router(cards_router)

    # RUM data collection endpoint
    @app.post("/api/analytics/rum")
    async def collect_rum_data(request: Request):
        """Collect Real User Monitoring (RUM) data for performance analysis."""
        try:
            rum_data = await request.json()

            # Log RUM data (in production, send to analytics service)
            logger.info(f"RUM Data collected: URL={rum_data.get('url', 'unknown')}")

            # Extract key metrics for logging
            metrics = rum_data.get('metrics', {})
            if 'navigation' in metrics:
                nav = metrics['navigation']
                logger.info(f"Navigation Timing: TTFB={nav.get('ttfb', 0):.1f}ms, "
                           f"DOM={nav.get('domInteractive', 0):.1f}ms, "
                           f"Load={nav.get('totalPageLoad', 0):.1f}ms")

            if 'lcp' in metrics:
                lcp = metrics['lcp']
                logger.info(f"LCP: {lcp.get('value', 0):.1f}ms on {lcp.get('element', 'unknown')}")

            if 'cls' in metrics:
                logger.info(f"CLS: {metrics['cls']:.4f}")

            # Count events by type
            events = rum_data.get('events', [])
            event_counts = {}
            for event in events:
                event_type = event.get('type', 'unknown')
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

            if event_counts:
                logger.info(f"RUM Events: {event_counts}")

            # In production, you would send this to your analytics service:
            # await send_to_analytics_service(rum_data)

            return {"status": "success", "message": "RUM data collected"}

        except Exception as e:
            logger.error(f"Error collecting RUM data: {e}")
            return {"status": "error", "message": "Failed to collect RUM data"}

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
    uvicorn.run(app, host="0.0.0.0", port=8011, reload=True)


if __name__ == "__main__":
    main()
