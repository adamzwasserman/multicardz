"""Test fixtures for landing page schema tests."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def test_landing_page():
    """Sample landing page data for testing."""
    return {
        'id': uuid4(),
        'slug': 'test-trello',
        'category': 'REPLACEMENT',
        'name': 'Test Trello Alternative',
        'headline': 'Test Headline',
        'subheadline': 'Test Subheadline',
        'competitor_name': 'Trello',
        'is_active': True,
        'created': datetime.now(UTC),
        'modified': datetime.now(UTC),
        'deleted': None
    }


@pytest.fixture
def test_section_data():
    """Sample section data for testing."""
    return {
        'pain_point': {
            'text': 'Your boards freeze with 500 cards',
            'icon': '⚠️'
        },
        'benefit': {
            'title': 'Handle 500,000+ cards',
            'description': 'Patent-pending architecture'
        }
    }


@pytest.fixture
def db_session():
    """
    Database session for tests.

    Uses PostgreSQL for public website system data.
    """
    import sys
    from pathlib import Path

    # Add apps/public to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from config.database import get_database_url

    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Cleanup after tests
    session.rollback()
    session.close()


@pytest.fixture
def clean_landing_pages(db_session):
    """Clean up landing pages before each test."""
    # Delete test data (CASCADE will handle sections)
    db_session.execute(text(
        "DELETE FROM landing_pages WHERE slug LIKE 'test-%'"
    ))
    db_session.commit()

    yield

    # Cleanup after test
    db_session.execute(text(
        "DELETE FROM landing_pages WHERE slug LIKE 'test-%'"
    ))
    db_session.commit()
