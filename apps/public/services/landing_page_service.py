"""Landing page service functions."""

from typing import Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException
import json


def get_landing_page_by_slug(db: Session, slug: str) -> dict:
    """
    Retrieve landing page by slug with all sections.

    Args:
        db: Database session
        slug: Landing page slug (e.g., 'trello-performance')

    Returns:
        Dict with landing page data and sections

    Raises:
        HTTPException: 404 if page not found or inactive
    """
    # Query landing page
    result = db.execute(
        text("""
            SELECT id, slug, category, name, headline, subheadline,
                   competitor_name, is_active, created, modified
            FROM landing_pages
            WHERE slug = :slug
              AND is_active = true
              AND deleted IS NULL
        """),
        {'slug': slug}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail=f"Landing page '{slug}' not found")

    # Build landing page dict
    landing_page = {
        'id': str(result[0]),
        'slug': result[1],
        'category': result[2],
        'name': result[3],
        'headline': result[4],
        'subheadline': result[5],
        'competitor_name': result[6],
        'is_active': result[7],
        'created': result[8].isoformat(),
        'modified': result[9].isoformat()
    }

    # Query sections
    sections_result = db.execute(
        text("""
            SELECT id, section_type, order_index, data
            FROM landing_page_sections
            WHERE landing_page_id = :landing_page_id
            ORDER BY order_index ASC
        """),
        {'landing_page_id': result[0]}
    ).fetchall()

    # Build sections list
    sections = []
    for section_row in sections_result:
        sections.append({
            'id': str(section_row[0]),
            'section_type': section_row[1],
            'order_index': section_row[2],
            'data': section_row[3]  # Already parsed as dict by PostgreSQL JSONB
        })

    landing_page['sections'] = sections

    return landing_page


def get_all_active_landing_pages(db: Session) -> list[dict]:
    """
    Retrieve all active landing pages (without sections).

    Args:
        db: Database session

    Returns:
        List of landing page dicts
    """
    result = db.execute(
        text("""
            SELECT id, slug, category, name, headline, subheadline,
                   competitor_name, created, modified
            FROM landing_pages
            WHERE is_active = true
              AND deleted IS NULL
            ORDER BY created DESC
        """)
    ).fetchall()

    pages = []
    for row in result:
        pages.append({
            'id': str(row[0]),
            'slug': row[1],
            'category': row[2],
            'name': row[3],
            'headline': row[4],
            'subheadline': row[5],
            'competitor_name': row[6],
            'created': row[7].isoformat(),
            'modified': row[8].isoformat()
        })

    return pages


def get_landing_page_by_id(db: Session, page_id: UUID) -> Optional[dict]:
    """
    Retrieve landing page by ID with all sections.

    Args:
        db: Database session
        page_id: Landing page UUID

    Returns:
        Dict with landing page data or None if not found
    """
    result = db.execute(
        text("""
            SELECT id, slug, category, name, headline, subheadline,
                   competitor_name, is_active, created, modified
            FROM landing_pages
            WHERE id = :page_id
              AND is_active = true
              AND deleted IS NULL
        """),
        {'page_id': page_id}
    ).fetchone()

    if not result:
        return None

    # Build landing page dict
    landing_page = {
        'id': str(result[0]),
        'slug': result[1],
        'category': result[2],
        'name': result[3],
        'headline': result[4],
        'subheadline': result[5],
        'competitor_name': result[6],
        'is_active': result[7],
        'created': result[8].isoformat(),
        'modified': result[9].isoformat()
    }

    # Query sections
    sections_result = db.execute(
        text("""
            SELECT id, section_type, order_index, data
            FROM landing_page_sections
            WHERE landing_page_id = :landing_page_id
            ORDER BY order_index ASC
        """),
        {'landing_page_id': result[0]}
    ).fetchall()

    # Build sections list
    sections = []
    for section_row in sections_result:
        sections.append({
            'id': str(section_row[0]),
            'section_type': section_row[1],
            'order_index': section_row[2],
            'data': section_row[3]
        })

    landing_page['sections'] = sections

    return landing_page
