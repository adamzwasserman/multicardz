"""Step definitions for content migration tests."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from pathlib import Path
from uuid import uuid4

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.content_migration import (
    parse_html_file,
    transform_to_landing_page,
    transform_to_sections,
    migrate_content_to_database
)

# Load scenarios
scenarios('../features/content_migration.feature')


# Scenario 1: Parse JavaScript data from HTML

@given('the landing-variations-viewer-v3.html file')
def html_file_setup(html_file_path):
    """Fixture providing HTML file path."""
    pytest.html_file = html_file_path


@when('I extract the segmentsData JavaScript object')
def extract_segments_data():
    """Extract segments data from HTML."""
    pytest.shared_data = parse_html_file(pytest.html_file)


@then('I should have 2 replacement segments')
def check_replacement_segments():
    """Verify replacement segment count."""
    data = pytest.shared_data
    replacement = data.get('replacement_segments', [])
    assert len(replacement) == 2, f"Expected 2 replacement segments, got {len(replacement)}"


@then(parsers.parse('I should have {count:d} complementary segments'))
def check_complementary_segments(count):
    """Verify complementary segment count."""
    data = pytest.shared_data
    complementary = data.get('complementary_segments', [])
    assert len(complementary) == count, f"Expected {count} complementary segments, got {len(complementary)}"


@then('each segment should have all required fields')
def check_segment_fields():
    """Verify each segment has required fields."""
    data = pytest.shared_data
    all_segments = (
        data.get('replacement_segments', []) +
        data.get('complementary_segments', [])
    )

    required_fields = ['id', 'name', 'category', 'headline']

    for segment in all_segments:
        for field in required_fields:
            assert field in segment, f"Segment missing required field: {field}"


# Scenario 2: Transform pain points to sections

@given('a landing page with 4 pain points')
def landing_page_with_pain_points_fixture(landing_page_with_pain_points):
    """Fixture providing landing page with pain points."""
    pytest.test_segment = landing_page_with_pain_points


@when('I transform to landing_page_sections format')
def transform_pain_points():
    """Transform pain points to sections."""
    landing_page_id = uuid4()
    pytest.test_sections = transform_to_sections(landing_page_id, pytest.test_segment)


@then(parsers.parse('I should have {count:d} sections of type "{section_type}"'))
def check_section_count_by_type(count, section_type):
    """Verify section count by type."""
    sections = pytest.test_sections
    matching_sections = [s for s in sections if s['section_type'] == section_type]
    assert len(matching_sections) == count, \
        f"Expected {count} sections of type {section_type}, got {len(matching_sections)}"


@then('each section should have data in JSONB format')
def check_jsonb_format():
    """Verify sections have data field."""
    sections = pytest.test_sections
    for section in sections:
        assert 'data' in section, "Section missing 'data' field"
        assert isinstance(section['data'], dict), "Section data must be a dict"


@then('sections should be ordered by index')
def check_section_ordering():
    """Verify sections are ordered."""
    sections = pytest.test_sections
    for i, section in enumerate(sections):
        assert section['order_index'] == i, \
            f"Section at position {i} has order_index {section['order_index']}"


# Scenario 3: Transform benefits to sections

@given('a landing page with 4 benefits')
def landing_page_with_benefits_fixture(landing_page_with_benefits):
    """Fixture providing landing page with benefits."""
    pytest.test_segment = landing_page_with_benefits


@when('I transform to sections format')
def transform_benefits():
    """Transform benefits to sections."""
    landing_page_id = uuid4()
    pytest.test_sections = transform_to_sections(landing_page_id, pytest.test_segment)


@then('each benefit should have title and description')
def check_benefit_fields():
    """Verify benefits have required fields."""
    sections = pytest.test_sections
    benefit_sections = [s for s in sections if s['section_type'] == 'benefit']

    for section in benefit_sections:
        assert 'title' in section['data'], "Benefit missing 'title'"
        assert 'description' in section['data'], "Benefit missing 'description'"


@then('sections should be ordered sequentially')
def check_sequential_ordering():
    """Verify sections are ordered sequentially."""
    sections = pytest.test_sections
    for i, section in enumerate(sections):
        assert section['order_index'] == i, \
            f"Section at position {i} has order_index {section['order_index']}"


# Scenario 4: Insert complete landing page

@given(parsers.parse('parsed content for "{slug}"'))
def parsed_content(sample_segment_data, db_connection):
    """Fixture providing parsed segment data."""
    from sqlalchemy import text

    # Clean up any existing test data
    db_connection.execute(
        text("DELETE FROM landing_pages WHERE slug = :slug"),
        {'slug': sample_segment_data['id']}
    )
    db_connection.commit()

    pytest.test_segment = sample_segment_data


@when('I insert into database')
def insert_into_database(db_connection):
    """Insert landing page into database."""
    # Create a test segment
    segment = pytest.test_segment

    # Transform to landing page
    landing_page = transform_to_landing_page(segment)
    pytest.test_landing_page_id = landing_page['id']
    pytest.test_slug = landing_page['slug']

    # Insert landing page
    from sqlalchemy import text
    import json

    db_connection.execute(
        text("""INSERT INTO landing_pages
           (id, slug, category, name, headline, subheadline,
            competitor_name, is_active, created, modified)
           VALUES (:id, :slug, :category, :name, :headline,
                   :subheadline, :competitor_name, :is_active,
                   :created, :modified)"""),
        landing_page
    )

    # Transform and insert sections
    sections = transform_to_sections(pytest.test_landing_page_id, segment)
    pytest.test_section_count = len(sections)

    for section in sections:
        db_connection.execute(
            text("""INSERT INTO landing_page_sections
               (id, landing_page_id, section_type, order_index,
                data, created, modified)
               VALUES (:id, :landing_page_id, :section_type,
                       :order_index, CAST(:data AS jsonb), :created, :modified)"""),
            {**section, 'data': json.dumps(section['data'])}
        )

    db_connection.commit()


@then('the landing page should exist with slug')
def check_landing_page_exists(db_connection):
    """Verify landing page exists in database."""
    from sqlalchemy import text

    result = db_connection.execute(
        text("SELECT * FROM landing_pages WHERE slug = :slug"),
        {'slug': pytest.test_slug}
    ).fetchone()

    assert result is not None, f"Landing page with slug '{pytest.test_slug}' not found"


@then('all sections should be linked')
def check_sections_linked(db_connection):
    """Verify sections are linked to landing page."""
    from sqlalchemy import text

    result = db_connection.execute(
        text("""SELECT COUNT(*) FROM landing_page_sections
                WHERE landing_page_id = :id"""),
        {'id': pytest.test_landing_page_id}
    ).fetchone()

    count = result[0]
    assert count > 0, "No sections found linked to landing page"


@then('section count should match source data')
def check_section_count(db_connection):
    """Verify section count matches source."""
    from sqlalchemy import text

    result = db_connection.execute(
        text("""SELECT COUNT(*) FROM landing_page_sections
                WHERE landing_page_id = :id"""),
        {'id': pytest.test_landing_page_id}
    ).fetchone()

    count = result[0]
    assert count == pytest.test_section_count, \
        f"Expected {pytest.test_section_count} sections, got {count}"
