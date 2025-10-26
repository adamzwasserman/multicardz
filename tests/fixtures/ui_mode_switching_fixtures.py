"""
Fixtures for UI mode switching BDD tests.

Provides mock UI components, mode switching services, and subscription verification.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any


@pytest.fixture
def mock_settings_panel():
    """Mock settings panel UI component."""
    panel = Mock()
    panel.display_mode = Mock(return_value="normal")
    panel.display_mode_description = Mock(return_value="Server-based storage")
    panel.display_features = Mock(return_value=["Cloud sync", "Multi-device"])
    panel.show = Mock()
    panel.hide = Mock()
    return panel


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service for premium checks."""
    service = Mock()
    service.check_subscription = Mock(return_value={
        "tier": "standard",
        "features": ["basic_storage", "cloud_sync"]
    })
    service.has_premium = Mock(return_value=False)
    return service


@pytest.fixture
def mock_premium_subscription_service():
    """Mock premium subscription service."""
    service = Mock()
    service.check_subscription = Mock(return_value={
        "tier": "premium",
        "features": ["basic_storage", "cloud_sync", "privacy_mode", "offline_mode"]
    })
    service.has_premium = Mock(return_value=True)
    return service


@pytest.fixture
def mock_mode_switcher():
    """Mock mode switcher service."""
    switcher = AsyncMock()
    switcher.switch_to_privacy = AsyncMock(return_value={
        "success": True,
        "mode": "privacy",
        "migrated_cards": 150,
        "migrated_tags": 45
    })
    switcher.switch_to_normal = AsyncMock(return_value={
        "success": True,
        "mode": "normal",
        "synced_cards": 150,
        "synced_bitmaps": 150
    })
    switcher.get_current_mode = Mock(return_value="normal")
    return switcher


@pytest.fixture
def mock_data_migrator():
    """Mock data migration service."""
    migrator = AsyncMock()
    migrator.migrate_to_browser = AsyncMock(return_value={
        "success": True,
        "cards_migrated": 150,
        "tags_migrated": 45,
        "duration_ms": 234
    })
    migrator.migrate_to_server = AsyncMock(return_value={
        "success": True,
        "cards_synced": 150,
        "bitmaps_synced": 150,
        "duration_ms": 345
    })
    return migrator


@pytest.fixture
def mock_browser_storage():
    """Mock browser storage for mode persistence."""
    storage = Mock()
    storage.get_item = Mock(return_value="privacy")
    storage.set_item = Mock()
    storage.remove_item = Mock()
    return storage


@pytest.fixture
def privacy_mode_context():
    """Context for privacy mode state."""
    return {
        "mode": "privacy",
        "workspace_id": "test-workspace-1",
        "user_id": "test-user-1",
        "subscription_tier": "premium",
        "browser_db_stats": {
            "total_cards": 150,
            "total_tags": 45,
            "storage_used_mb": 2.5,
            "last_sync": "2025-10-10T16:00:00Z"
        }
    }


@pytest.fixture
def normal_mode_context():
    """Context for normal mode state."""
    return {
        "mode": "normal",
        "workspace_id": "test-workspace-1",
        "user_id": "test-user-1",
        "subscription_tier": "standard",
        "server_stats": {
            "total_cards": 150,
            "total_tags": 45,
            "last_sync": "2025-10-10T16:00:00Z"
        }
    }


@pytest.fixture
def mode_switching_config():
    """Configuration for mode switching."""
    return {
        "modes": {
            "dev": {
                "enabled": True,
                "requires_subscription": False,
                "features": ["local_db", "fast_iteration"]
            },
            "normal": {
                "enabled": True,
                "requires_subscription": False,
                "features": ["cloud_sync", "multi_device"]
            },
            "privacy": {
                "enabled": True,
                "requires_subscription": True,
                "subscription_tier": "premium",
                "features": ["browser_storage", "offline_mode", "zero_content_on_server"]
            }
        },
        "migration_batch_size": 100,
        "sync_retry_attempts": 3
    }


@pytest.fixture
def upgrade_prompt_data():
    """Data for subscription upgrade prompt."""
    return {
        "current_tier": "standard",
        "required_tier": "premium",
        "message": "Privacy mode requires a premium subscription",
        "features": [
            "Browser-based storage",
            "Offline mode",
            "Zero content on server",
            "Enhanced privacy"
        ],
        "upgrade_url": "/subscription/upgrade"
    }


@pytest.fixture
def mock_confirmation_dialog():
    """Mock confirmation dialog for mode switching."""
    dialog = Mock()
    dialog.show = Mock()
    dialog.hide = Mock()
    dialog.set_message = Mock()
    dialog.set_title = Mock()
    return dialog
