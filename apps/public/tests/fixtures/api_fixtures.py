"""Fixtures for analytics API testing."""

import pytest
from uuid import uuid4


@pytest.fixture
def test_app(test_client):
    """Alias for test_client to match step definition naming."""
    return test_client.app


@pytest.fixture
def sample_session_data():
    """Sample session data for API tests."""
    return {
        'session_id': str(uuid4()),
        'referrer_url': 'https://google.com/search?q=trello+alternative',
        'utm_source': 'google',
        'utm_medium': 'cpc',
        'utm_campaign': 'trello-refugees',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'viewport_width': 1920,
        'viewport_height': 1080
    }


@pytest.fixture
def sample_page_view_data():
    """Sample page view data for API tests."""
    return {
        'session_id': str(uuid4()),
        'url': 'https://multicardz.com/trello-performance',
        'referrer': 'https://google.com',
        'duration_ms': 45000,
        'scroll_depth_percent': 75,
        'viewport_width': 1920,
        'viewport_height': 1080
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for API tests."""
    return {
        'session_id': str(uuid4()),
        'page_view_id': str(uuid4()),
        'event_type': 'cta_click',
        'element_selector': '.cta-button',
        'element_text': 'Start free trial',
        'element_position_x': 640,
        'element_position_y': 300,
        'timestamp_ms': 15000
    }


@pytest.fixture
def sample_mouse_tracking_data():
    """Sample mouse tracking data for API tests."""
    return {
        'session_id': str(uuid4()),
        'page_view_id': str(uuid4()),
        'coordinates': [
            {'x': 100, 'y': 200, 'timestamp_ms': 1000},
            {'x': 150, 'y': 250, 'timestamp_ms': 1100},
            {'x': 200, 'y': 300, 'timestamp_ms': 1200}
        ]
    }
