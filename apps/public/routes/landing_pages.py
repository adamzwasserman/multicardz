"""Landing page routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from services.landing_page_service import (
    get_landing_page_by_slug,
    get_all_active_landing_pages
)


router = APIRouter(tags=["landing_pages"])


@router.get("/{slug}")
async def get_landing_page(slug: str, db: Session = Depends(get_db)):
    """
    Retrieve landing page by slug.

    Args:
        slug: Landing page slug (e.g., 'trello-performance')
        db: Database session

    Returns:
        Landing page data with all sections

    Raises:
        HTTPException: 404 if page not found
    """
    return get_landing_page_by_slug(db, slug)


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
