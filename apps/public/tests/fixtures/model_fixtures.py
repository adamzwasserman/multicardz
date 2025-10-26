"""Test fixtures for Pydantic model tests."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC


@pytest.fixture
def valid_landing_page_data():
    """Valid landing page data for testing."""
    return {
        'id': uuid4(),
        'slug': 'trello-performance',
        'category': 'REPLACEMENT',
        'name': 'Trello Performance Refugees',
        'headline': 'Love Trello?<br>Hate slowdowns?',
        'subheadline': 'Get 1000× capacity',
        'competitor_name': 'Trello',
        'is_active': True,
        'created': datetime.now(UTC),
        'modified': datetime.now(UTC),
        'deleted': None
    }


@pytest.fixture
def valid_event_data():
    """Valid analytics event data for testing."""
    return {
        'session_id': uuid4(),
        'page_view_id': uuid4(),
        'event_type': 'cta_click',
        'element_selector': '.cta-button',
        'element_text': 'Start free trial',
        'element_position_x': 640,
        'element_position_y': 300,
        'timestamp_ms': 15000
    }


@pytest.fixture
def valid_session_data():
    """Valid analytics session data for testing."""
    return {
        'landing_page_id': uuid4(),
        'landing_page_slug': 'trello-performance',
        'referrer_url': 'https://google.com/search?q=trello+alternative',
        'utm_source': 'google',
        'utm_medium': 'cpc',
        'utm_campaign': 'trello-refugees',
        'utm_term': 'trello alternative',
        'utm_content': 'ad-1',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'ip_address': '192.168.1.1',
        'browser_fingerprint': 'abc123def456'
    }
