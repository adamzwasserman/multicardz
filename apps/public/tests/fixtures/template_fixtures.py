"""Fixtures for template rendering tests."""

import pytest
from uuid import uuid4
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


@pytest.fixture
def jinja_env():
    """Create Jinja2 environment for testing."""
    template_dir = Path(__file__).parent.parent.parent / 'templates'
    template_dir.mkdir(exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True
    )
    return env


@pytest.fixture
def sample_landing_page_data():
    """Sample landing page data for template rendering."""
    return {
        'id': uuid4(),
        'slug': 'test-page',
        'category': 'REPLACEMENT',
        'name': 'Test Landing Page',
        'headline': 'Love Test?<br>Hate Problems?',
        'subheadline': 'Get everything you love, with 1000× the capacity',
        'competitor_name': 'TestApp',
        'sections': []
    }


@pytest.fixture
def landing_page_with_pain_points(sample_landing_page_data):
    """Landing page with pain points."""
    sample_landing_page_data['sections'] = [
        {
            'section_type': 'pain_point',
            'order_index': 0,
            'data': {'text': 'Your boards freeze with 500 cards'}
        },
        {
            'section_type': 'pain_point',
            'order_index': 1,
            'data': {'text': '7-8 second load times'}
        },
        {
            'section_type': 'pain_point',
            'order_index': 2,
            'data': {'text': 'Complete browser lock-up'}
        },
        {
            'section_type': 'pain_point',
            'order_index': 3,
            'data': {'text': 'Forced upgrades to expensive plans'}
        }
    ]
    return sample_landing_page_data


@pytest.fixture
def landing_page_with_benefits(sample_landing_page_data):
    """Landing page with benefits."""
    sample_landing_page_data['sections'] = [
        {
            'section_type': 'benefit',
            'order_index': 0,
            'data': {
                'title': 'Handle 500,000+ cards',
                'description': 'Patent-pending architecture handles massive scale'
            }
        },
        {
            'section_type': 'benefit',
            'order_index': 1,
            'data': {
                'title': 'Load in 0.09 seconds',
                'description': 'Lightning-fast performance at any scale'
            }
        },
        {
            'section_type': 'benefit',
            'order_index': 2,
            'data': {
                'title': 'Zero performance degradation',
                'description': 'Stays fast no matter how much data you have'
            }
        },
        {
            'section_type': 'benefit',
            'order_index': 3,
            'data': {
                'title': 'Same familiar interface',
                'description': 'Keep what you love, upgrade what you need'
            }
        }
    ]
    return sample_landing_page_data


@pytest.fixture
def landing_page_with_comparison(sample_landing_page_data):
    """Landing page with comparison metrics."""
    sample_landing_page_data['sections'] = [
        {
            'section_type': 'comparison_metric',
            'order_index': 0,
            'data': {
                'label': 'Maximum Cards',
                'them': '10,000',
                'us': '500,000+'
            }
        },
        {
            'section_type': 'comparison_metric',
            'order_index': 1,
            'data': {
                'label': 'Load Time',
                'them': '7-8 seconds',
                'us': '0.09 seconds'
            }
        },
        {
            'section_type': 'comparison_metric',
            'order_index': 2,
            'data': {
                'label': 'Performance at Scale',
                'them': 'Degrades significantly',
                'us': 'Stays consistent'
            }
        }
    ]
    sample_landing_page_data['competitor_name'] = 'Trello'
    return sample_landing_page_data
