"""Landing page routes."""

from fastapi import APIRouter, Depends, HTTPException
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

# Set up Jinja2 environment
template_dir = Path(__file__).parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))


@router.get("/{slug}", response_class=HTMLResponse)
async def get_landing_page(slug: str, db: Session = Depends(get_db)):
    """
    Retrieve and render landing page by slug.

    Args:
        slug: Landing page slug (e.g., 'trello-performance')
        db: Database session

    Returns:
        Rendered HTML page

    Raises:
        HTTPException: 404 if page not found
    """
    landing_page_data = get_landing_page_by_slug(db, slug)
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
