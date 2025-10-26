"""Test fixtures for analytics schema tests."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC
from sqlalchemy import create_engine, text


@pytest.fixture
def db_connection():
    """
    Database connection for analytics tests.

    Returns dict with connection and metadata storage.
    """
    import sys
    from pathlib import Path

    # Add apps/public to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from config.database import get_database_url

    engine = create_engine(get_database_url())
    connection = engine.connect()

    # Create wrapper object with metadata storage
    class ConnectionWrapper:
        def __init__(self, conn):
            self._conn = conn
            self.info = {}

        def execute(self, *args, **kwargs):
            return self._conn.execute(*args, **kwargs)

        def commit(self):
            return self._conn.commit()

        def rollback(self):
            return self._conn.rollback()

        def close(self):
            return self._conn.close()

    wrapper = ConnectionWrapper(connection)

    yield wrapper

    # Cleanup
    wrapper.rollback()
    wrapper.close()


@pytest.fixture
def test_session():
    """Sample analytics session data (without landing_page_id to avoid FK constraint)."""
    return {
        'session_id': uuid4(),
        'landing_page_id': None,  # Null to avoid FK constraint in tests
        'referrer_url': 'https://google.com/search?q=trello+alternative',
        'referrer_domain': 'google.com',
        'utm_source': 'google',
        'utm_medium': 'cpc',
        'utm_campaign': 'trello-refugees',
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'ip_address': '192.168.1.1',
        'browser_fingerprint': 'abc123',
        'first_seen': datetime.now(UTC),
        'last_seen': datetime.now(UTC)
    }


@pytest.fixture
def test_page_view(test_session):
    """Sample page view data."""
    return {
        'session_id': test_session['session_id'],
        'landing_page_id': None,  # Null to avoid FK constraint
        'url': 'https://multicardz.com/trello-performance',
        'duration_ms': 45000,
        'scroll_depth_percent': 75,
        'viewport_width': 1920,
        'viewport_height': 1080
    }


@pytest.fixture
def test_event(test_page_view):
    """Sample analytics event data."""
    return {
        'session_id': test_page_view['session_id'],
        'page_view_id': uuid4(),
        'event_type': 'cta_click',
        'element_selector': '.cta-button',
        'element_text': 'Start free trial',
        'element_position_x': 640,
        'element_position_y': 300,
        'timestamp_ms': 15000
    }


@pytest.fixture
def test_mouse_coordinates(test_page_view):
    """Generate 100 mouse tracking coordinates."""
    base_timestamp = 0
    coordinates = []

    for i in range(100):
        coordinates.append({
            'session_id': test_page_view['session_id'],
            'page_view_id': uuid4(),
            'timestamp_ms': base_timestamp + (i * 100),  # 100ms intervals
            'event_type': 'move',
            'x': 500 + (i % 50),
            'y': 300 + (i // 10),
            'scroll_x': 0,
            'scroll_y': i * 10
        })

    return coordinates
