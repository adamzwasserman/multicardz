"""
Admin Dashboard Routes.

Provides endpoints for:
- Dashboard overview page
- Per-page analytics views
- Heatmap visualization
- Session replay viewer
- Funnel visualization
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

# Import services
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from ..config.database import get_db
from ..services.dashboard_service import (
    get_dashboard_overview,
    get_top_landing_pages,
    get_active_ab_tests_summary,
    get_traffic_source_breakdown
)

router = APIRouter(prefix="/admin", tags=["admin"])

# Set up templates
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


@router.get("/")
async def dashboard_overview(
    request: Request,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Dashboard overview page showing key metrics.

    Query Parameters:
        days: Number of days to look back (default: 30)

    Returns:
        HTML page with dashboard metrics or JSON
    """
    # Get dashboard data
    data = get_dashboard_overview(db, days=days)

    # Return JSON for API clients or if template fails
    if request.headers.get("accept") == "application/json":
        return data

    # Try to render HTML template
    try:
        return templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
                "data": data
            }
        )
    except Exception as e:
        # Fallback to JSON response if template rendering fails
        return data


@router.get("/metrics", response_model=dict)
async def get_metrics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    API endpoint for dashboard metrics (JSON only).

    Query Parameters:
        days: Number of days to look back (default: 30)

    Returns:
        JSON with dashboard metrics
    """
    return get_dashboard_overview(db, days=days)


@router.get("/landing-pages", response_model=list)
async def get_landing_pages_performance(
    days: int = 30,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    API endpoint for top landing pages by conversion rate.

    Query Parameters:
        days: Number of days to look back (default: 30)
        limit: Maximum number of results (default: 10)

    Returns:
        JSON list of landing page performance data
    """
    return get_top_landing_pages(db, days=days, limit=limit)


@router.get("/ab-tests", response_model=list)
async def get_ab_tests(
    db: Session = Depends(get_db)
):
    """
    API endpoint for active A/B tests summary.

    Returns:
        JSON list of A/B test summaries
    """
    return get_active_ab_tests_summary(db)


@router.get("/traffic-sources", response_model=dict)
async def get_traffic_sources(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    API endpoint for traffic source breakdown.

    Query Parameters:
        days: Number of days to look back (default: 30)

    Returns:
        JSON with traffic source percentages
    """
    return get_traffic_source_breakdown(db, days=days)
