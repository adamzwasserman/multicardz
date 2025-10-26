"""
Fixtures for Turso integration testing.
"""
import pytest
from unittest.mock import Mock, MagicMock
from typing import NamedTuple


class MockCard(NamedTuple):
    """Mock card for testing."""
    card_id: str
    name: str
    workspace_id: str
    user_id: str
    tags: str
    card_bitmap: int
    created: str
    modified: str


@pytest.fixture
def full_integration_environment():
    """Complete integration environment with all services."""
    browser_db = Mock()
    browser_db.execute_query.return_value = {
        'success': True,
        'rows': [],
        'rows_affected': 0
    }

    server_db = Mock()
    server_db.execute.return_value = None
    server_db.commit.return_value = None

    sync_service = Mock()
    sync_service.sync_card_bitmap.return_value = {
        'success': True,
        'card_id': 'test-card-1'
    }

    query_router = Mock()
    query_router.route_card_query.return_value = {
        'success': True,
        'rows': []
    }

    return {
        'browser_db': browser_db,
        'server_db': server_db,
        'sync_service': sync_service,
        'query_router': query_router
    }


@pytest.fixture
def privacy_verification_queries():
    """Queries for verifying privacy guarantees."""
    return {
        'check_server_schema': """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'card_bitmaps'
        """,
        'verify_no_content': """
            SELECT card_id, workspace_id, user_id, card_bitmap, tag_bitmaps
            FROM card_bitmaps
            LIMIT 1
        """,
        'verify_bitmap_only': """
            SELECT COUNT(*) as count
            FROM card_bitmaps
            WHERE card_bitmap IS NOT NULL
        """
    }


@pytest.fixture
def mock_browser_cards():
    """Mock cards stored in browser database."""
    return [
        MockCard(
            card_id='card-1',
            name='Card 1',
            workspace_id='ws-1',
            user_id='user-1',
            tags='tag-1,tag-2',
            card_bitmap=12345,
            created='2025-10-10 15:00:00',
            modified='2025-10-10 15:00:00'
        ),
        MockCard(
            card_id='card-2',
            name='Card 2',
            workspace_id='ws-1',
            user_id='user-1',
            tags='tag-2,tag-3',
            card_bitmap=23456,
            created='2025-10-10 15:01:00',
            modified='2025-10-10 15:01:00'
        ),
        MockCard(
            card_id='card-3',
            name='Card 3',
            workspace_id='ws-1',
            user_id='user-1',
            tags='tag-1,tag-3',
            card_bitmap=34567,
            created='2025-10-10 15:02:00',
            modified='2025-10-10 15:02:00'
        )
    ]


@pytest.fixture
def mock_bitmap_sync_data():
    """Mock data for bitmap sync operations."""
    return {
        'card_id': 'test-card-uuid',
        'workspace_id': 'test-ws',
        'user_id': 'test-user',
        'card_bitmap': 12345,
        'tag_bitmaps': [111, 222, 333]
    }


@pytest.fixture
def mock_server_unavailable():
    """Mock server unavailable scenario."""
    mock = Mock()
    mock.sync_card_bitmap.side_effect = ConnectionError("Server unavailable")
    return mock


@pytest.fixture
def mock_server_available():
    """Mock server available scenario."""
    mock = Mock()
    mock.sync_card_bitmap.return_value = {
        'success': True,
        'card_id': 'test-card-1'
    }
    return mock


@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    return {
        'modes': ['dev', 'normal', 'privacy'],
        'default_mode': 'normal',
        'privacy_mode_requires': 'premium',
        'browser_db_init_timeout_ms': 100,
        'server_sync_timeout_ms': 1000,
        'retry_attempts': 3,
        'retry_delay_ms': 100
    }


@pytest.fixture
def mode_switch_scenarios():
    """Test scenarios for mode switching."""
    return [
        {
            'from_mode': 'normal',
            'to_mode': 'privacy',
            'expected_routing': 'browser',
            'subscription_required': True
        },
        {
            'from_mode': 'privacy',
            'to_mode': 'dev',
            'expected_routing': 'dev',
            'subscription_required': False
        },
        {
            'from_mode': 'dev',
            'to_mode': 'normal',
            'expected_routing': 'server',
            'subscription_required': False
        }
    ]


@pytest.fixture
def privacy_compliance_checks():
    """Privacy compliance verification checks."""
    return {
        'forbidden_fields': ['name', 'description', 'content', 'tags'],
        'required_fields': ['card_id', 'workspace_id', 'user_id', 'card_bitmap'],
        'allowed_operations': ['sync_bitmap', 'query_bitmaps', 'filter_by_bitmap'],
        'forbidden_operations': ['sync_content', 'query_content']
    }
