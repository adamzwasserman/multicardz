"""Test fixtures for conversion funnel and A/B testing."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC


@pytest.fixture
def test_funnel_stages():
    """Sample funnel stage data for testing conversion rates."""
    return [
        {'stage': 'view', 'session_count': 1000},
        {'stage': 'cta_click', 'session_count': 300},
        {'stage': 'account_create', 'session_count': 150},
        {'stage': 'activate', 'session_count': 120},
        {'stage': 'upgrade', 'session_count': 30}
    ]


@pytest.fixture
def test_ab_test():
    """Sample A/B test configuration."""
    return {
        'id': uuid4(),
        'name': 'Hero headline test',
        'description': 'Testing headline variations',
        'is_active': True,
        'traffic_split': {'variant_a': 50, 'variant_b': 50},
        'start_date': datetime.now(UTC)
    }


@pytest.fixture
def test_variants(test_ab_test):
    """Sample A/B test variants."""
    return [
        {
            'a_b_test_id': test_ab_test['id'],
            'variant_name': 'control',
            'landing_page_id': uuid4(),
            'weight': 50
        },
        {
            'a_b_test_id': test_ab_test['id'],
            'variant_name': 'variant_a',
            'landing_page_id': uuid4(),
            'weight': 50
        }
    ]


@pytest.fixture
def test_heatmap_data():
    """Sample heatmap bucket data."""
    return {
        'landing_page_id': uuid4(),
        'viewport_bucket': '1920x1080',
        'x_bucket': 100,  # 100px bucket
        'y_bucket': 200,  # 200px bucket
        'click_count': 15,
        'hover_duration_ms': 3500
    }


@pytest.fixture
def test_session_with_funnel(test_landing_page):
    """Session with funnel stages for testing."""
    session_id = uuid4()
    return {
        'session_id': session_id,
        'landing_page_id': test_landing_page['id'],
        'funnel_stages': [
            {
                'session_id': session_id,
                'funnel_stage': 'view',
                'landing_page_id': test_landing_page['id'],
                'data': None
            },
            {
                'session_id': session_id,
                'funnel_stage': 'cta_click',
                'landing_page_id': test_landing_page['id'],
                'data': {'button': 'Start free trial'}
            }
        ]
    }
