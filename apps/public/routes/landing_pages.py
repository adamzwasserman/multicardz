"""Landing page routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ..config.database import get_db
from ..services.landing_page_service import (
    get_landing_page_by_slug,
    get_all_active_landing_pages
)
from ..services.template_service import render_landing_page


router = APIRouter(tags=["landing_pages"])

# Set up Jinja2 environment with multiple template directories
template_dirs = [
    str(Path(__file__).parent.parent / "templates"),  # Public templates
    str(Path(__file__).parent.parent.parent / "static" / "templates")  # Shared templates
]
jinja_env = Environment(loader=FileSystemLoader(template_dirs))


@router.get("/{slug}", response_class=HTMLResponse)
async def get_landing_page(slug: str, request: Request, db: Session = Depends(get_db)):
    """
    Retrieve and render landing page by slug.

    Session management and A/B test variant assignment handled by middleware.

    Args:
        slug: Landing page slug (e.g., 'trello-performance')
        request: FastAPI request (has ab_test_variant from middleware)
        db: Database session

    Returns:
        Rendered HTML page with A/B test variant

    Raises:
        HTTPException: 404 if page not found
    """
    # Get landing page data
    landing_page_data = get_landing_page_by_slug(db, slug)

    # Get A/B test variant from request state (set by middleware)
    variant_content = getattr(request.state, 'ab_test_variant', None)

    # Add variant content to landing page data for template
    landing_page_data['ab_test_variant'] = variant_content

    return render_landing_page(landing_page_data, jinja_env)


@router.get("/")
async def list_landing_pages(db: Session = Depends(get_db)):
    """
    List all active landing pages.

    Args:
        db: Database session

    Returns:
        List of landing pages (without sections)
    """
    return get_all_active_landing_pages(db)
