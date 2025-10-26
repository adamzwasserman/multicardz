"""Fixtures for query routing tests."""
import pytest
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_cards() -> List[Dict[str, Any]]:
    """Sample cards for testing query routing."""
    return [
        {
            "card_id": "card-1",
            "name": "Card 1",
            "description": "First card",
            "tags": "tag-1,tag-2",
            "workspace_id": "ws-1",
            "user_id": "user-1",
            "card_bitmap": 12,
            "created": "2025-10-10 10:00:00",
            "modified": "2025-10-10 10:00:00"
        },
        {
            "card_id": "card-2",
            "name": "Card 2",
            "description": "Second card",
            "tags": "tag-2,tag-3",
            "workspace_id": "ws-1",
            "user_id": "user-1",
            "card_bitmap": 13,
            "created": "2025-10-10 10:01:00",
            "modified": "2025-10-10 10:01:00"
        },
        {
            "card_id": "card-3",
            "name": "Card 3",
            "description": "Third card",
            "tags": "tag-1,tag-3",
            "workspace_id": "ws-1",
            "user_id": "user-1",
            "card_bitmap": 14,
            "created": "2025-10-10 10:02:00",
            "modified": "2025-10-10 10:02:00"
        }
    ]


@pytest.fixture
def mock_bitmap_filter_response() -> Dict[str, Any]:
    """Mock server bitmap filter response."""
    return {
        "card_ids": ["card-1", "card-3"],
        "total_cards": 3,
        "matched_cards": 2,
        "filter_operations": ["union", "intersection"]
    }


@pytest.fixture
def mock_browser_database() -> Mock:
    """Mock browser database for local queries."""
    mock_db = Mock()
    mock_db.execute_query = Mock(return_value={
        "success": True,
        "rows": [],
        "rows_affected": 0
    })
    return mock_db


@pytest.fixture
def mock_server_api() -> Mock:
    """Mock server API for bitmap operations."""
    mock_api = Mock()
    mock_api.filter_bitmaps = AsyncMock(return_value={
        "success": True,
        "card_ids": ["card-1", "card-2"],
        "matched_cards": 2
    })
    return mock_api


@pytest.fixture
def query_routing_config() -> Dict[str, Any]:
    """Configuration for query routing tests."""
    return {
        "privacy_mode": {
            "route_content_to": "browser",
            "route_bitmaps_to": "server",
            "fallback_mode": "server"
        },
        "normal_mode": {
            "route_content_to": "server",
            "route_bitmaps_to": "server",
            "fallback_mode": "server"
        },
        "dev_mode": {
            "route_content_to": "local",
            "route_bitmaps_to": "local",
            "fallback_mode": "local"
        }
    }


@pytest.fixture
def mock_set_operations() -> List[Dict[str, Any]]:
    """Sample set operations for bitmap filtering."""
    return [
        {
            "operation": "union",
            "tag_bitmaps": [1, 2, 4],
            "expected_result": 7
        },
        {
            "operation": "intersection",
            "tag_bitmaps": [3, 5],
            "expected_result": 1
        },
        {
            "operation": "exclusion",
            "include_bitmaps": [15],
            "exclude_bitmaps": [8],
            "expected_result": 7
        }
    ]


@pytest.fixture
def privacy_mode_context() -> Dict[str, Any]:
    """Context for privacy mode testing."""
    return {
        "mode": "privacy",
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "browser_db_initialized": True,
        "server_connected": True
    }


@pytest.fixture
def normal_mode_context() -> Dict[str, Any]:
    """Context for normal mode testing."""
    return {
        "mode": "normal",
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "browser_db_initialized": False,
        "server_connected": True
    }
