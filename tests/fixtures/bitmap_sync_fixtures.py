"""
Test fixtures for bitmap sync API testing.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List
import random


@pytest.fixture
def bitmap_sync_request() -> Dict[str, Any]:
    """Standard bitmap sync request data."""
    return {
        "card_id": "card-test-uuid-001",
        "workspace_id": "ws-test-uuid-001",
        "user_id": "user-test-uuid-001",
        "card_bitmap": 12345,
        "tag_bitmaps": [111, 222, 333]
    }


@pytest.fixture
def tag_bitmap_sync_request() -> Dict[str, Any]:
    """Tag bitmap sync request data."""
    return {
        "tag_id": "tag-test-uuid-001",
        "workspace_id": "ws-test-uuid-001",
        "user_id": "user-test-uuid-001",
        "tag_bitmap": 456,
        "card_count": 15
    }


@pytest.fixture
def multi_workspace_bitmaps() -> List[Dict[str, Any]]:
    """Bitmaps from multiple workspaces for isolation testing."""
    return [
        {
            "card_id": "card-ws1-001",
            "workspace_id": "ws-001",
            "user_id": "user-001",
            "card_bitmap": 100,
            "tag_bitmaps": [10, 20]
        },
        {
            "card_id": "card-ws2-001",
            "workspace_id": "ws-002",
            "user_id": "user-001",
            "card_bitmap": 200,
            "tag_bitmaps": [30, 40]
        },
        {
            "card_id": "card-ws1-002",
            "workspace_id": "ws-001",
            "user_id": "user-002",
            "card_bitmap": 300,
            "tag_bitmaps": [50, 60]
        }
    ]


@pytest.fixture
def mock_bitmap_database():
    """Mock database connection for bitmap storage."""
    mock = Mock()
    mock.execute = Mock(return_value=None)
    mock.commit = Mock(return_value=None)
    mock.fetchone = Mock(return_value=(1,))  # Affected rows
    return mock


@pytest.fixture
def mock_unavailable_server():
    """Mock server that is unavailable."""
    mock = Mock()
    mock.execute = Mock(side_effect=ConnectionError("Server unavailable"))
    return mock


@pytest.fixture
def sample_card_with_bitmap() -> Dict[str, Any]:
    """Sample card with bitmap data."""
    return {
        "card_id": "card-sample-001",
        "name": "Sample Card",
        "workspace_id": "ws-sample",
        "user_id": "user-sample",
        "card_bitmap": random.randint(1000, 9999),
        "tag_bitmaps": [random.randint(100, 999) for _ in range(3)],
        "created": "2025-10-10T15:00:00Z",
        "modified": "2025-10-10T15:00:00Z"
    }


@pytest.fixture
def sample_tag_with_bitmap() -> Dict[str, Any]:
    """Sample tag with bitmap data."""
    return {
        "tag_id": "tag-sample-001",
        "workspace_id": "ws-sample",
        "user_id": "user-sample",
        "tag_bitmap": random.randint(1000, 9999),
        "card_count": random.randint(1, 100)
    }


@pytest.fixture
def zero_trust_validation_data() -> Dict[str, Any]:
    """Data for validating zero-trust UUID isolation."""
    return {
        "valid": {
            "workspace_id": "ws-valid",
            "user_id": "user-valid",
            "card_id": "card-valid"
        },
        "invalid": {
            "workspace_id": "ws-invalid",
            "user_id": "user-invalid",
            "card_id": "card-invalid"
        }
    }
