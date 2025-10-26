"""Test fixtures for content migration."""

import pytest
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime, UTC


@pytest.fixture
def html_file_path():
    """Path to the HTML source file."""
    return Path("/Users/adam/Downloads/landing-variations-viewer-v3.html")


@pytest.fixture
def sample_segment_data():
    """Sample segment data structure."""
    return {
        "id": "trello-performance",
        "name": "Trello Performance Refugees",
        "category": "REPLACEMENT",
        "headline": "Love Trello's simplicity?<br>Hate the slowdowns?",
        "subheadline": "Get everything you love about Trello, with 1000× the capacity and 80× the speed.",
        "pain_points": [
            "Your boards freeze when you hit 500–1000 cards",
            "7–8 second load times with complete browser lock-up",
            "Search doesn't work across boards",
            "You're forced to archive boards to regain performance"
        ],
        "benefits": [
            {
                "title": "Handle 500,000+ cards",
                "description": "Not a typo. Our patent-pending architecture..."
            },
            {
                "title": "Search in 0.38 milliseconds",
                "description": "Drag tags to search across all your boards instantly."
            },
            {
                "title": "Same drag-and-drop flow",
                "description": "If you know Trello, you already know multicardz."
            },
            {
                "title": "50% cheaper pricing",
                "description": "Better performance at half the cost."
            }
        ],
        "comparison": {
            "competitor": "Trello",
            "metrics": [
                {
                    "label": "Optimal card count",
                    "them": "500",
                    "us": "500,000+"
                },
                {
                    "label": "Load time (1000 cards)",
                    "them": "7–8 seconds",
                    "us": "0.1 seconds"
                }
            ]
        },
        "differentiator": {
            "title": "Built for scale from day one",
            "stat": "1000× more capacity<br>80× faster",
            "description": [
                "While Trello slows down as you add cards, multicardz stays fast.",
                "Our patent-pending architecture means the 500,000th card is as fast as the 1st."
            ]
        },
        "testimonial": {
            "quote": "We had 12 Trello boards that were becoming unusable...",
            "author": "Sarah Chen",
            "role": "Product Manager, TechCorp"
        },
        "pricing": {
            "competitor_name": "Trello Premium",
            "competitor_price": "$10",
            "our_name": "multicardz Premium",
            "our_price": "$5",
            "savings": "Save 50% + better performance"
        }
    }


@pytest.fixture
def transformed_section():
    """Sample transformed section."""
    return {
        'section_type': 'pain_point',
        'order_index': 0,
        'data': {
            'text': 'Your boards freeze when you hit 500–1000 cards'
        }
    }


@pytest.fixture
def landing_page_with_pain_points():
    """Landing page with 4 pain points."""
    return {
        "id": "test-page",
        "name": "Test Page",
        "category": "REPLACEMENT",
        "headline": "Test Headline",
        "subheadline": "Test Subheadline",
        "pain_points": [
            "Pain point 1",
            "Pain point 2",
            "Pain point 3",
            "Pain point 4"
        ],
        "benefits": []
    }


@pytest.fixture
def landing_page_with_benefits():
    """Landing page with 4 benefits."""
    return {
        "id": "test-page",
        "name": "Test Page",
        "category": "REPLACEMENT",
        "headline": "Test Headline",
        "subheadline": "Test Subheadline",
        "pain_points": [],
        "benefits": [
            {"title": "Benefit 1", "description": "Description 1"},
            {"title": "Benefit 2", "description": "Description 2"},
            {"title": "Benefit 3", "description": "Description 3"},
            {"title": "Benefit 4", "description": "Description 4"}
        ]
    }
