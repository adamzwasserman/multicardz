"""Test fixtures for connection logic update tests."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any


@pytest.fixture
def mock_browser_connection():
    """Mock browser database connection."""
    connection = Mock()
    connection.type = "browser"
    connection.execute = Mock(return_value={"success": True, "rows": []})
    connection.close = Mock()
    connection.is_closed = False
    return connection


@pytest.fixture
def mock_server_connection():
    """Mock server database connection."""
    connection = Mock()
    connection.type = "server"
    connection.url = "libsql://turso-cloud-url"
    connection.execute = Mock(return_value={"success": True, "rows": []})
    connection.close = Mock()
    connection.is_closed = False
    return connection


@pytest.fixture
def mock_local_connection():
    """Mock local development database connection."""
    connection = Mock()
    connection.type = "local"
    connection.url = "http://127.0.0.1:8080"
    connection.execute = Mock(return_value={"success": True, "rows": []})
    connection.close = Mock()
    connection.is_closed = False
    return connection


@pytest.fixture
def connection_routing_config():
    """Configuration for connection routing."""
    return {
        "dev": {
            "enabled": True,
            "url": "http://127.0.0.1:8080",
            "connection_type": "local"
        },
        "normal": {
            "enabled": True,
            "url": "libsql://turso-cloud-url",
            "connection_type": "server"
        },
        "privacy": {
            "enabled": True,
            "connection_type": "browser"
        }
    }


@pytest.fixture
def mock_connection_factory():
    """Mock factory for creating database connections."""
    factory = Mock()
    factory.create_browser_connection = Mock()
    factory.create_server_connection = Mock()
    factory.create_local_connection = Mock()
    return factory


@pytest.fixture
def connection_pool():
    """Mock connection pool for managing connections."""
    pool = Mock()
    pool.active_connections = {}
    pool.get_connection = Mock()
    pool.release_connection = Mock()
    pool.close_all = Mock()
    return pool


@pytest.fixture
def mode_switch_context():
    """Context for testing mode switching."""
    return {
        "original_mode": "normal",
        "target_mode": "privacy",
        "has_active_connection": True,
        "requires_migration": True
    }


@pytest.fixture
def connection_parameters():
    """Various connection parameters for testing."""
    return {
        "server_params": {
            "url": "libsql://turso-cloud-url",
            "auth_token": "test-token",
            "sync_interval": 1000
        },
        "browser_params": {
            "storage": "opfs",
            "db_name": "multicardz.db"
        },
        "local_params": {
            "url": "http://127.0.0.1:8080",
            "timeout": 5000
        }
    }


@pytest.fixture
def connection_validation_rules():
    """Rules for validating connection parameters by mode."""
    return {
        "privacy": {
            "allowed_params": ["storage", "db_name"],
            "forbidden_params": ["url", "auth_token", "sync_interval"]
        },
        "normal": {
            "allowed_params": ["url", "auth_token", "sync_interval"],
            "forbidden_params": ["storage"]
        },
        "dev": {
            "allowed_params": ["url", "timeout"],
            "forbidden_params": ["auth_token", "storage"]
        }
    }
