"""Test fixtures for database mode selection tests."""
import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service for testing mode selection."""
    mock = Mock()
    mock.check_subscription.return_value = {"tier": "standard"}
    return mock


@pytest.fixture
def database_mode_config():
    """Database mode configuration for tests."""
    return {
        "dev": {"enabled": True, "url": "http://127.0.0.1:8080"},
        "normal": {"enabled": True, "url": "turso-cloud-url"},
        "privacy": {"enabled": False, "requires": "premium"}
    }
