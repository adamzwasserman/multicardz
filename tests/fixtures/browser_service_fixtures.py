"""
Test fixtures for browser database service testing.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List


@pytest.fixture
def mock_browser_db_connection():
    """Mock browser database connection for testing."""
    mock = Mock()
    mock.execute = AsyncMock(return_value={
        "success": True,
        "rows": [{"id": 1, "name": "Test Card"}],
        "rowsAffected": 1
    })
    mock.batch = AsyncMock(return_value={"success": True})
    mock.close = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def test_queries() -> List[str]:
    """Standard test queries for database operations."""
    return [
        "SELECT * FROM cards WHERE workspace_id = ? AND user_id = ?",
        "INSERT INTO cards (card_id, name, workspace_id, user_id) VALUES (?, ?, ?, ?)",
        "UPDATE cards SET name = ? WHERE card_id = ? AND workspace_id = ? AND user_id = ?",
        "DELETE FROM cards WHERE card_id = ? AND workspace_id = ? AND user_id = ?"
    ]


@pytest.fixture
def test_transaction_statements() -> List[Dict[str, Any]]:
    """Test transaction with multiple statements."""
    return [
        {
            "sql": "INSERT INTO cards (card_id, name, workspace_id, user_id) VALUES (?, ?, ?, ?)",
            "params": ["card-1", "Card 1", "ws-1", "user-1"]
        },
        {
            "sql": "INSERT INTO tags (tag_id, name, workspace_id, user_id) VALUES (?, ?, ?, ?)",
            "params": ["tag-1", "Tag 1", "ws-1", "user-1"]
        },
        {
            "sql": "INSERT INTO card_tags (card_id, tag_id, workspace_id, user_id) VALUES (?, ?, ?, ?)",
            "params": ["card-1", "tag-1", "ws-1", "user-1"]
        }
    ]


@pytest.fixture
def mock_opfs_storage():
    """Mock OPFS storage for browser database."""
    mock = Mock()
    mock.get_directory = AsyncMock(return_value=Mock())
    mock.get_file = AsyncMock(return_value=Mock())
    mock.write_file = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def browser_db_config() -> Dict[str, Any]:
    """Configuration for browser database."""
    return {
        "storage": "opfs",
        "database_name": "multicardz_browser.db",
        "max_connections": 1,
        "enable_wal": True,
        "cache_size": 2000,
        "page_size": 4096
    }
