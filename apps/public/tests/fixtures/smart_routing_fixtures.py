"""Fixtures for smart routing tests."""

import pytest
from urllib.parse import urlencode


@pytest.fixture
def referrer_from_trello():
    """Referrer from Trello domain."""
    return {
        'referrer_url': 'https://trello.com/b/abc123/my-board',
        'referrer_domain': 'trello.com',
        'utm_source': None,
        'utm_medium': None,
        'utm_campaign': None
    }


@pytest.fixture
def referrer_from_google_notion_search():
    """Referrer from Google search for Notion alternative."""
    query_params = urlencode({'q': 'notion alternative best'})
    return {
        'referrer_url': f'https://www.google.com/search?{query_params}',
        'referrer_domain': 'www.google.com',
        'utm_source': None,
        'utm_medium': None,
        'utm_campaign': None
    }


@pytest.fixture
def referrer_with_trello_utm():
    """Referrer with Trello UTM campaign."""
    return {
        'referrer_url': 'https://reddit.com/r/productivity',
        'referrer_domain': 'reddit.com',
        'utm_source': 'reddit',
        'utm_medium': 'social',
        'utm_campaign': 'trello_refugees'
    }


@pytest.fixture
def generic_referrer():
    """Generic referrer (no specific competitor)."""
    return {
        'referrer_url': 'https://news.ycombinator.com/item?id=123456',
        'referrer_domain': 'news.ycombinator.com',
        'utm_source': None,
        'utm_medium': None,
        'utm_campaign': None
    }


@pytest.fixture
def no_referrer():
    """No referrer (direct traffic)."""
    return {
        'referrer_url': None,
        'referrer_domain': None,
        'utm_source': None,
        'utm_medium': None,
        'utm_campaign': None
    }


@pytest.fixture
def default_landing_page_slug():
    """The default landing page for generic traffic."""
    # For this system, we'll use the first COMPLEMENTARY page as default
    return 'cross-platform-operations'
