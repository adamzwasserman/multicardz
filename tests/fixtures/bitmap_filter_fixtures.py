"""Test fixtures for bitmap filter endpoint tests."""

import pytest
from unittest.mock import Mock
from typing import List, Dict, Any


@pytest.fixture
def sample_card_bitmaps():
    """Sample card bitmaps for testing."""
    return [
        {
            "card_id": "card-001",
            "workspace_id": "ws-1",
            "user_id": "user-1",
            "card_bitmap": 12345,
            "tag_bitmaps": "111,222"
        },
        {
            "card_id": "card-002",
            "workspace_id": "ws-1",
            "user_id": "user-1",
            "card_bitmap": 12346,
            "tag_bitmaps": "111,333"
        },
        {
            "card_id": "card-003",
            "workspace_id": "ws-1",
            "user_id": "user-1",
            "card_bitmap": 12347,
            "tag_bitmaps": "222,333"
        },
        {
            "card_id": "card-004",
            "workspace_id": "ws-1",
            "user_id": "user-1",
            "card_bitmap": 12348,
            "tag_bitmaps": "111,222,444"
        },
        {
            "card_id": "card-005",
            "workspace_id": "ws-2",
            "user_id": "user-2",
            "card_bitmap": 22345,
            "tag_bitmaps": "111,222"
        }
    ]


@pytest.fixture
def bitmap_filter_request_single():
    """Request for single tag bitmap filter."""
    return {
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "filter": {
            "operation": "MATCH",
            "tag_bitmap": 111
        }
    }


@pytest.fixture
def bitmap_filter_request_intersection():
    """Request for intersection (AND) of tag bitmaps."""
    return {
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "filter": {
            "operation": "AND",
            "tag_bitmaps": [111, 222]
        }
    }


@pytest.fixture
def bitmap_filter_request_union():
    """Request for union (OR) of tag bitmaps."""
    return {
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "filter": {
            "operation": "OR",
            "tag_bitmaps": [111, 222]
        }
    }


@pytest.fixture
def bitmap_filter_request_exclusion():
    """Request for exclusion (NOT) operation."""
    return {
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "filter": {
            "operation": "NOT",
            "include_bitmap": 111,
            "exclude_bitmap": 222
        }
    }


@pytest.fixture
def bitmap_filter_request_complex():
    """Request for complex nested operations."""
    return {
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "filter": {
            "operation": "OR",
            "filters": [
                {
                    "operation": "AND",
                    "tag_bitmaps": [111, 222]
                },
                {
                    "operation": "NOT",
                    "include_bitmap": 333,
                    "exclude_bitmap": 444
                }
            ]
        }
    }


@pytest.fixture
def multi_workspace_bitmaps_for_filter():
    """Card bitmaps across multiple workspaces for zero-trust testing (filter operations)."""
    return [
        {"card_id": "card-ws1-001", "workspace_id": "ws-1", "user_id": "user-1", "tag_bitmaps": "111"},
        {"card_id": "card-ws1-002", "workspace_id": "ws-1", "user_id": "user-1", "tag_bitmaps": "111"},
        {"card_id": "card-ws2-001", "workspace_id": "ws-2", "user_id": "user-2", "tag_bitmaps": "111"},
        {"card_id": "card-ws2-002", "workspace_id": "ws-2", "user_id": "user-2", "tag_bitmaps": "111"}
    ]


@pytest.fixture
def empty_match_request():
    """Request that should return no matches."""
    return {
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "filter": {
            "operation": "MATCH",
            "tag_bitmap": 999  # No cards have this bitmap
        }
    }


@pytest.fixture
def mock_bitmap_database():
    """Mock database for bitmap operations."""
    db = Mock()
    db.execute = Mock()
    db.fetchall = Mock()
    db.commit = Mock()
    return db


@pytest.fixture
def bitmap_operation_results():
    """Expected results for various bitmap operations."""
    return {
        "single_match": ["card-001", "card-002", "card-004"],  # Cards with tag 111
        "intersection": ["card-001", "card-004"],  # Cards with both 111 AND 222
        "union": ["card-001", "card-002", "card-003", "card-004"],  # Cards with 111 OR 222
        "exclusion": ["card-002"],  # Cards with 111 but NOT 222
        "complex": ["card-001", "card-003", "card-004"],  # (111 AND 222) OR (333 NOT 444)
        "zero_trust": ["card-ws1-001", "card-ws1-002"],  # Only ws-1 cards
        "empty": []  # No matches
    }


@pytest.fixture
def performance_validation_config():
    """Configuration for performance validation."""
    return {
        "max_response_time_ms": 100,
        "max_query_time_ms": 50,
        "max_bitmap_op_time_ms": 10
    }
