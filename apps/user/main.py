"""
MultiCardz™ User Application.
Frontend application for spatial tag manipulation interface.
"""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import routers
from .routes.cards_api import router as cards_router
from .routes.tags_api import router as tags_router

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
    app.include_router(tags_router)

    # Main interface route (no authentication)
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        try:
            # Load lesson tags for the current lesson
            from apps.shared.data.onboarding_lessons import get_lesson_tags
            from apps.shared.services.lesson_service import get_default_lesson_state

            lesson_state = get_default_lesson_state()

            # Check for lesson parameter from URL (for lesson switching)
            lesson_param = request.query_params.get('lesson')
            if lesson_param:
                try:
                    current_lesson = int(lesson_param)
                    lesson_state['current_lesson'] = current_lesson
                except (ValueError, TypeError):
                    current_lesson = lesson_state.get('current_lesson', 1)
            else:
                current_lesson = lesson_state.get('current_lesson', 1)

            # Get tags from tutorial database
            import sqlite3

            db_path = "/var/data/tutorial_customer.db"
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    # Use new zero-trust schema with UUID and card_count field
                    cursor.execute("""
                        SELECT tag_id, tag, card_count
                        FROM tags
                        WHERE user_id = ? AND workspace_id = ? AND deleted IS NULL
                        ORDER BY tag
                    """, ("default-user", "default-workspace"))
                    available_tags = [{"id": row[0], "name": row[1], "count": row[2]} for row in cursor.fetchall()]

                    # Debug: what tags are we loading?
                    logger.info(f"Tutorial database tags: {available_tags}")
                    print(f"DEBUG: Loading {len(available_tags)} tags from tutorial database: {available_tags}")
            except Exception as db_e:
                logger.warning(f"Could not load tags from tutorial database: {db_e}")
                # Fallback to lesson definitions
                lesson_tags = get_lesson_tags(current_lesson)
                available_tags = [{"name": tag.name, "count": 0} for tag in lesson_tags]
                logger.info(f"Fallback to lesson {current_lesson} tags: {available_tags}")

            logger.info(f"Loading {len(available_tags)} tags")

        except Exception as e:
            logger.warning(f"Could not load lesson tags: {e}. Using fallback.")
            # Fallback to basic tags if lesson system fails
            available_tags = [{"name": "drag me to first box", "count": 0}]

        response = templates.TemplateResponse("user_home.html", {
            "request": request,
            "available_tags": available_tags,
            "groups": []
        })

        # Set cache headers for authenticated content
        response.headers["Cache-Control"] = "private, max-age=60"
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
