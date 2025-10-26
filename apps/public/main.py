"""
multicardz™ Public Website Application.

Serves landing pages, analytics tracking, and admin dashboard.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

# Import routes (using relative imports)
from .routes import landing_pages
from .routes import analytics  # Phase 6: Analytics API
from .routes import admin  # Phase 9: Admin Dashboard
from .routes import webhooks  # Phase 10: Conversion Integration
from .routes import funnel  # Phase 10: Funnel Analytics
from .routes import ab_testing  # A/B Testing API

# Import shared routes from user app (monorepo code reuse)
from ..user.routes.cards_api import router as cards_router

# Import middleware
from .middleware.ab_test_middleware import ABTestMiddleware


def create_app() -> FastAPI:
    """
    Create FastAPI application instance.

    Returns FastAPI app with middleware and routes configured.
    """
    app = FastAPI(
        title="multicardz Public Website",
        description="Public landing pages and analytics system",
        version="1.0.0",
        docs_url="/admin/docs",  # Protect API docs
        redoc_url="/admin/redoc"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://multicardz.com",
            "https://www.multicardz.com",
            "https://app.multicardz.com"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"]
    )

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "multicardz.com",
            "www.multicardz.com",
            "localhost",
            "127.0.0.1",
            "testserver"  # For test client
        ]
    )

    # A/B Test middleware (needs session to be available - added before SessionMiddleware)
    app.add_middleware(ABTestMiddleware)

    # Session middleware (for analytics session_id - added last so it wraps ABTestMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key="CHANGE-ME-IN-PRODUCTION",  # TODO: Use env var
        max_age=86400 * 90  # 90 days
    )

    # Security headers and cache control middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Add efficient cache headers for static assets
        if request.url.path.startswith("/static/") or request.url.path.startswith("/public/static/"):
            # Cache static assets for 1 year (immutable)
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

        return response

    # Mount static files
    app.mount("/static", StaticFiles(directory="apps/static"), name="static")
    app.mount("/public/static", StaticFiles(directory="apps/public/static"), name="public-static")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "public-website"}

    # Include routers
    app.include_router(landing_pages.router)
    app.include_router(analytics.router)  # Phase 6: Analytics API
    app.include_router(admin.router)  # Phase 9: Admin Dashboard
    app.include_router(webhooks.router)  # Phase 10: Conversion Integration
    app.include_router(funnel.router)  # Phase 10: Funnel Analytics
    app.include_router(ab_testing.router)  # A/B Testing API
    app.include_router(cards_router)  # Cards API (shared from user app)

    return app


def main():
    """Run public website application."""
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    main()
