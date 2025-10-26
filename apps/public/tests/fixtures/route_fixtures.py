"""Test fixtures for route testing."""

import pytest
from uuid import uuid4
from datetime import datetime, UTC
import json


@pytest.fixture
def sample_landing_page_db():
    """Sample landing page data for database insertion."""
    page_id = uuid4()
    return {
        'page': {
            'id': page_id,
            'slug': 'trello-performance',
            'category': 'REPLACEMENT',
            'name': 'Trello Performance Refugees',
            'headline': 'Love Trello\'s simplicity?<br>Hate the slowdowns?',
            'subheadline': 'Get everything you love about Trello, with 1000× the capacity and 80× the speed.',
            'competitor_name': 'Trello',
            'is_active': True,
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC),
            'deleted': None
        },
        'sections': [
            {
                'id': uuid4(),
                'landing_page_id': page_id,
                'section_type': 'pain_point',
                'order_index': 0,
                'data': json.dumps({'text': 'Your boards freeze when you hit 500–1000 cards'}),
                'created': datetime.now(UTC),
                'modified': datetime.now(UTC)
            },
            {
                'id': uuid4(),
                'landing_page_id': page_id,
                'section_type': 'pain_point',
                'order_index': 1,
                'data': json.dumps({'text': '7–8 second load times with complete browser lock-up'}),
                'created': datetime.now(UTC),
                'modified': datetime.now(UTC)
            },
            {
                'id': uuid4(),
                'landing_page_id': page_id,
                'section_type': 'benefit',
                'order_index': 2,
                'data': json.dumps({
                    'title': 'Handle 500,000+ cards',
                    'description': 'Not a typo. Our patent-pending architecture handles 1000× more cards.'
                }),
                'created': datetime.now(UTC),
                'modified': datetime.now(UTC)
            },
            {
                'id': uuid4(),
                'landing_page_id': page_id,
                'section_type': 'comparison_metric',
                'order_index': 3,
                'data': json.dumps({
                    'label': 'Load time (500 cards)',
                    'them': '7.2s',
                    'us': '0.09s'
                }),
                'created': datetime.now(UTC),
                'modified': datetime.now(UTC)
            }
        ]
    }


@pytest.fixture
def inactive_landing_page_db():
    """Inactive landing page for testing 404 behavior."""
    page_id = uuid4()
    return {
        'page': {
            'id': page_id,
            'slug': 'inactive-page',
            'category': 'REPLACEMENT',
            'name': 'Inactive Page',
            'headline': 'This page is inactive',
            'subheadline': None,
            'competitor_name': None,
            'is_active': False,
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC),
            'deleted': None
        },
        'sections': []
    }


@pytest.fixture
def complex_jsonb_page_db():
    """Landing page with complex JSONB data."""
    page_id = uuid4()
    return {
        'page': {
            'id': page_id,
            'slug': 'complex-data',
            'category': 'COMPLEMENTARY',
            'name': 'Complex Data Test',
            'headline': 'Complex JSONB test',
            'subheadline': None,
            'competitor_name': None,
            'is_active': True,
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC),
            'deleted': None
        },
        'sections': [
            {
                'id': uuid4(),
                'landing_page_id': page_id,
                'section_type': 'testimonial',
                'order_index': 0,
                'data': json.dumps({
                    'quote': 'This product changed everything for us.',
                    'author': 'Jane Doe',
                    'role': 'Product Manager',
                    'company': 'Tech Corp'
                }),
                'created': datetime.now(UTC),
                'modified': datetime.now(UTC)
            },
            {
                'id': uuid4(),
                'landing_page_id': page_id,
                'section_type': 'pricing',
                'order_index': 1,
                'data': json.dumps({
                    'free_tier': {
                        'cards': 1000,
                        'users': 'Unlimited',
                        'price': 0
                    },
                    'pro_tier': {
                        'cards': 'Unlimited',
                        'users': 'Unlimited',
                        'price': 12
                    }
                }),
                'created': datetime.now(UTC),
                'modified': datetime.now(UTC)
            }
        ]
    }
