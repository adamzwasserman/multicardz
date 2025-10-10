"""
Fixtures for card creation integration testing.
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime


@pytest.fixture
def mock_browser_database_initialized():
    """Mock initialized browser database."""
    mock = Mock()
    mock.execute = AsyncMock(return_value={
        "success": True,
        "rows": [],
        "rowsAffected": 1
    })
    mock.batch = AsyncMock(return_value={"success": True})
    mock.close = AsyncMock(return_value={"success": True})
    return mock


@pytest.fixture
def privacy_mode_context():
    """Context for privacy mode operations."""
    return {
        "mode": "privacy",
        "user_id": "test-user-uuid",
        "workspace_id": "test-workspace-uuid",
        "database_mode": "privacy",
        "sync_enabled": True
    }


@pytest.fixture
def normal_mode_context():
    """Context for normal mode operations."""
    return {
        "mode": "normal",
        "user_id": "test-user-uuid",
        "workspace_id": "test-workspace-uuid",
        "database_mode": "normal",
        "server_url": "https://turso.example.com"
    }


@pytest.fixture
def sample_card_creation_request():
    """Sample card creation request."""
    return {
        "name": "Test Card",
        "description": "",
        "tag_ids": ["tag-1-uuid", "tag-2-uuid"],
        "tags": ["tag1", "tag2"],
        "user_id": "test-user-uuid",
        "workspace_id": "test-workspace-uuid"
    }


@pytest.fixture
def sample_dimensional_card_request():
    """Sample card creation from grid cell with dimensional tags."""
    return {
        "name": "Untitled",
        "description": "",
        "row_tag": "Priority",
        "column_tag": "Work",
        "tag_ids": ["priority-uuid", "work-uuid"],
        "tags": ["Priority", "Work"],
        "user_id": "test-user-uuid",
        "workspace_id": "test-workspace-uuid"
    }


@pytest.fixture
def mock_tag_bitmaps():
    """Mock tag bitmaps for bitmap calculation."""
    return {
        "javascript": 0b1010,  # Binary: cards 1, 3
        "react": 0b0110,       # Binary: cards 2, 3
        "tutorial": 0b1100     # Binary: cards 3, 4
    }


@pytest.fixture
def mock_bitmap_sync_service():
    """Mock bitmap sync service."""
    mock = AsyncMock()
    mock.sync_card_bitmap = AsyncMock(return_value={
        "success": True,
        "synced": True,
        "card_id": "test-card-uuid"
    })
    return mock


@pytest.fixture
def mock_server_api_unavailable():
    """Mock server API that's unavailable."""
    mock = AsyncMock()
    mock.post = AsyncMock(side_effect=ConnectionError("Server unavailable"))
    return mock


@pytest.fixture
def mock_card_repository():
    """Mock card repository for normal mode."""
    mock = Mock()
    mock.create = Mock(return_value={
        "card_id": "test-card-uuid",
        "name": "Test Card",
        "description": "",
        "tag_ids": ["tag-1-uuid", "tag-2-uuid"],
        "user_id": "test-user-uuid",
        "workspace_id": "test-workspace-uuid",
        "created": datetime.utcnow().isoformat(),
        "modified": datetime.utcnow().isoformat()
    })
    return mock


@pytest.fixture
def sample_created_card():
    """Sample created card response."""
    return {
        "card_id": "test-card-uuid",
        "name": "Test Card",
        "description": "",
        "tags": ["tag1", "tag2"],
        "tag_ids": ["tag-1-uuid", "tag-2-uuid"],
        "card_bitmap": 0b111,  # Calculated from tag bitmaps
        "user_id": "test-user-uuid",
        "workspace_id": "test-workspace-uuid",
        "created": "2025-10-10T15:00:00.000Z",
        "modified": "2025-10-10T15:00:00.000Z"
    }


@pytest.fixture
def card_creation_config():
    """Configuration for card creation."""
    return {
        "privacy_mode": {
            "local_storage": True,
            "sync_bitmaps": True,
            "sync_content": False,
            "auto_calculate_bitmap": True
        },
        "normal_mode": {
            "local_storage": False,
            "server_storage": True,
            "auto_calculate_bitmap": True
        },
        "ui_behavior": {
            "auto_focus_title": True,
            "show_in_grid": True,
            "render_delay_ms": 100
        }
    }


@pytest.fixture
def mock_grid_render_system():
    """Mock grid rendering system."""
    mock = Mock()
    mock.updateStateAndRender = AsyncMock(return_value={"success": True})
    mock.focusCard = Mock()
    return mock
