"""Content migration from HTML to database."""

import json
import re
from pathlib import Path
from uuid import uuid4
from datetime import datetime, UTC
from typing import List, Dict, Any


def parse_html_file(file_path: Path) -> dict:
    """
    Extract JavaScript segmentsData from HTML file.

    Args:
        file_path: Path to HTML file containing segmentsData

    Returns:
        dict with 'replacement_segments' and 'complementary_segments' arrays

    Raises:
        ValueError: If segmentsData not found in HTML
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"HTML file not found: {file_path}")

    content = file_path.read_text()

    # Find segmentsData = {...}; in JavaScript
    pattern = r'const segmentsData\s*=\s*(\{[\s\S]*?\n\s*\});'
    match = re.search(pattern, content)

    if not match:
        raise ValueError("Could not find segmentsData in HTML")

    # Extract JSON
    js_object = match.group(1)

    # Parse JSON
    try:
        data = json.loads(js_object)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse segmentsData JSON: {e}")

    return data


def transform_to_landing_page(segment: dict) -> dict:
    """
    Transform segment data to landing_page format.

    Args:
        segment: Segment data from HTML

    Returns:
        dict ready for database insertion
    """
    return {
        'id': uuid4(),
        'slug': segment['id'],
        'category': segment['category'],
        'name': segment['name'],
        'headline': segment['headline'],
        'subheadline': segment.get('subheadline'),
        'competitor_name': segment.get('comparison', {}).get('competitor'),
        'is_active': True,
        'created': datetime.now(UTC),
        'modified': datetime.now(UTC),
        'deleted': None
    }


def transform_to_sections(
    landing_page_id: Any,
    segment: dict
) -> List[dict]:
    """
    Transform segment data to landing_page_sections format.

    Args:
        landing_page_id: UUID of the landing page
        segment: Segment data from HTML

    Returns:
        list of section dicts with order_index
    """
    sections = []
    index = 0

    # Pain points
    for pain in segment.get('pain_points', []):
        sections.append({
            'id': uuid4(),
            'landing_page_id': landing_page_id,
            'section_type': 'pain_point',
            'order_index': index,
            'data': {'text': pain},
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        })
        index += 1

    # Benefits
    for benefit in segment.get('benefits', []):
        sections.append({
            'id': uuid4(),
            'landing_page_id': landing_page_id,
            'section_type': 'benefit',
            'order_index': index,
            'data': {
                'title': benefit['title'],
                'description': benefit['description']
            },
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        })
        index += 1

    # Comparison metrics
    comparison = segment.get('comparison', {})
    for metric in comparison.get('metrics', []):
        sections.append({
            'id': uuid4(),
            'landing_page_id': landing_page_id,
            'section_type': 'comparison_metric',
            'order_index': index,
            'data': {
                'label': metric['label'],
                'them': metric['them'],
                'us': metric['us']
            },
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        })
        index += 1

    # Testimonial
    testimonial = segment.get('testimonial', {})
    if testimonial:
        sections.append({
            'id': uuid4(),
            'landing_page_id': landing_page_id,
            'section_type': 'testimonial',
            'order_index': index,
            'data': {
                'quote': testimonial['quote'],
                'author': testimonial['author'],
                'role': testimonial['role']
            },
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        })
        index += 1

    # Differentiator
    diff = segment.get('differentiator', {})
    if diff:
        sections.append({
            'id': uuid4(),
            'landing_page_id': landing_page_id,
            'section_type': 'differentiator',
            'order_index': index,
            'data': {
                'title': diff['title'],
                'stat': diff['stat'],
                'description': diff['description']
            },
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        })
        index += 1

    # Pricing
    pricing = segment.get('pricing', {})
    if pricing:
        sections.append({
            'id': uuid4(),
            'landing_page_id': landing_page_id,
            'section_type': 'pricing',
            'order_index': index,
            'data': pricing,
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        })

    return sections


def migrate_content_to_database(
    file_path: Path,
    db_session: Any
) -> int:
    """
    Parse HTML file and migrate all content to database.

    Args:
        file_path: Path to HTML file
        db_session: SQLAlchemy session

    Returns:
        count of landing pages inserted

    Raises:
        ValueError: If parsing fails
        Exception: If database insertion fails
    """
    # Parse HTML
    data = parse_html_file(file_path)

    # Combine all segments
    all_segments = (
        data.get('replacement_segments', []) +
        data.get('complementary_segments', [])
    )

    inserted_count = 0

    for segment in all_segments:
        # Transform to landing page
        landing_page = transform_to_landing_page(segment)
        landing_page_id = landing_page['id']

        # Insert landing page
        from sqlalchemy import text
        db_session.execute(
            text("""INSERT INTO landing_pages
               (id, slug, category, name, headline, subheadline,
                competitor_name, is_active, created, modified)
               VALUES (:id, :slug, :category, :name, :headline,
                       :subheadline, :competitor_name, :is_active,
                       :created, :modified)"""),
            landing_page
        )

        # Transform and insert sections
        sections = transform_to_sections(landing_page_id, segment)
        for section in sections:
            db_session.execute(
                text("""INSERT INTO landing_page_sections
                   (id, landing_page_id, section_type, order_index,
                    data, created, modified)
                   VALUES (:id, :landing_page_id, :section_type,
                           :order_index, CAST(:data AS jsonb), :created, :modified)"""),
                {**section, 'data': json.dumps(section['data'])}
            )

        inserted_count += 1

    db_session.commit()
    return inserted_count
