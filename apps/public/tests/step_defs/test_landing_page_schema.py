"""BDD step definitions for landing page schema tests."""

import pytest
import json
from pytest_bdd import scenarios, given, when, then, parsers
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy import text


# Load scenarios from feature file
scenarios('../features/landing_page_schema.feature')


# Shared context for test data
@pytest.fixture
def context():
    """Shared context between test steps."""
    return {}


@given('the database is connected')
def database_connected(db_session):
    """Verify database connection."""
    result = db_session.execute(text("SELECT 1")).scalar()
    assert result == 1


@given(parsers.parse('a landing page exists with id "{page_id}"'))
def landing_page_exists(db_session, test_landing_page, context, page_id):
    """Insert a test landing page."""
    # Create landing page
    page_data = test_landing_page.copy()
    page_data['slug'] = f'test-{page_id}'
    context['landing_page_id'] = page_data['id']

    db_session.execute(text("""
        INSERT INTO landing_pages
            (id, slug, category, name, headline, subheadline,
             competitor_name, is_active, created, modified)
        VALUES (:id, :slug, :category, :name, :headline, :subheadline,
                :competitor_name, :is_active, :created, :modified)
    """), page_data)
    db_session.commit()


@given(parsers.parse('landing pages exist with categories "{cat1}" and "{cat2}"'))
def multiple_landing_pages(db_session, clean_landing_pages):
    """Create landing pages with different categories."""
    pages = [
        {
            'id': uuid4(),
            'slug': 'test-replacement-1',
            'category': 'REPLACEMENT',
            'name': 'Test Replacement Page',
            'headline': 'Test',
            'is_active': True,
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        },
        {
            'id': uuid4(),
            'slug': 'test-complementary-1',
            'category': 'COMPLEMENTARY',
            'name': 'Test Complementary Page',
            'headline': 'Test',
            'is_active': True,
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    ]

    for page in pages:
        db_session.execute(text("""
            INSERT INTO landing_pages
                (id, slug, category, name, headline, is_active, created, modified)
            VALUES (:id, :slug, :category, :name, :headline, :is_active, :created, :modified)
        """), page)

    db_session.commit()


@when(parsers.parse('I insert a landing page with slug "{slug}"'))
def insert_landing_page(db_session, test_landing_page, context, clean_landing_pages, slug):
    """Insert a landing page."""
    page_data = test_landing_page.copy()
    page_data['slug'] = slug
    context['landing_page_id'] = page_data['id']
    context['slug'] = slug

    db_session.execute(text("""
        INSERT INTO landing_pages
            (id, slug, category, name, headline, subheadline,
             competitor_name, is_active, created, modified)
        VALUES (:id, :slug, :category, :name, :headline, :subheadline,
                :competitor_name, :is_active, :created, :modified)
    """), page_data)
    db_session.commit()


@when(parsers.parse('I insert sections of type "{type1}" and "{type2}"'))
def insert_sections(db_session, test_section_data, context, type1, type2):
    """Insert sections with different types."""
    sections = [
        {
            'id': uuid4(),
            'landing_page_id': context['landing_page_id'],
            'section_type': type1,
            'order_index': 0,
            'data': json.dumps(test_section_data[type1]),
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        },
        {
            'id': uuid4(),
            'landing_page_id': context['landing_page_id'],
            'section_type': type2,
            'order_index': 1,
            'data': json.dumps(test_section_data[type2]),
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    ]

    for section in sections:
        db_session.execute(text("""
            INSERT INTO landing_page_sections
                (id, landing_page_id, section_type, order_index, data, created, modified)
            VALUES (:id, :landing_page_id, :section_type, :order_index, :data, :created, :modified)
        """), section)

    db_session.commit()


@when(parsers.parse('I query for "{category}" pages'))
def query_by_category(db_session, context, category):
    """Query landing pages by category."""
    result = db_session.execute(text("""
        SELECT * FROM landing_pages
        WHERE category = :category
          AND deleted IS NULL
        ORDER BY created DESC
    """), {'category': category})

    context['query_results'] = result.fetchall()


@then('the landing page should be retrievable by slug')
def landing_page_retrievable(db_session, context):
    """Verify landing page can be retrieved."""
    result = db_session.execute(text("""
        SELECT * FROM landing_pages
        WHERE slug = :slug
          AND deleted IS NULL
    """), {'slug': context['slug']})

    page = result.fetchone()
    assert page is not None
    assert str(page.id) == str(context['landing_page_id'])


@then('the page should have all required fields')
def page_has_required_fields(db_session, context):
    """Verify all required fields are present."""
    result = db_session.execute(text("""
        SELECT slug, category, name, headline, is_active
        FROM landing_pages
        WHERE slug = :slug
    """), {'slug': context['slug']})

    page = result.fetchone()
    assert page.slug == context['slug']
    assert page.category == 'REPLACEMENT'
    assert page.name == 'Test Trello Alternative'
    assert page.headline == 'Test Headline'
    assert page.is_active is True


@then('the sections should be ordered correctly')
def sections_ordered(db_session, context):
    """Verify sections are in correct order."""
    result = db_session.execute(text("""
        SELECT section_type, order_index
        FROM landing_page_sections
        WHERE landing_page_id = :page_id
        ORDER BY order_index
    """), {'page_id': context['landing_page_id']})

    sections = result.fetchall()
    assert len(sections) == 2
    assert sections[0].order_index == 0
    assert sections[1].order_index == 1


@then('the sections should contain JSONB data')
def sections_have_jsonb(db_session, context):
    """Verify sections contain valid JSONB data."""
    result = db_session.execute(text("""
        SELECT section_type, data
        FROM landing_page_sections
        WHERE landing_page_id = :page_id
        ORDER BY order_index
    """), {'page_id': context['landing_page_id']})

    sections = result.fetchall()

    # First section (pain_point)
    pain_data = sections[0].data
    assert 'text' in pain_data
    assert pain_data['text'] == 'Your boards freeze with 500 cards'

    # Second section (benefit)
    benefit_data = sections[1].data
    assert 'title' in benefit_data
    assert benefit_data['title'] == 'Handle 500,000+ cards'


@then(parsers.parse('I should only get {category} pages'))
def only_category_pages(context, category):
    """Verify only pages from specified category are returned."""
    results = context['query_results']
    assert len(results) > 0

    for row in results:
        assert row.category == category


@then('the pages should be ordered by created date')
def pages_ordered_by_date(context):
    """Verify pages are ordered by creation date (DESC)."""
    results = context['query_results']

    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i].created >= results[i + 1].created
