import pytest
from unittest.mock import Mock, patch
from contextlib import contextmanager

@pytest.fixture
def mock_turso_available():
    """Mock Turso being available."""
    with patch('apps.shared.services.database_connection.check_turso') as mock:
        mock.return_value = True
        yield mock

@pytest.fixture
def mock_turso_unavailable():
    """Mock Turso being unavailable."""
    with patch('apps.shared.services.database_connection.check_turso') as mock:
        mock.return_value = False
        yield mock

@pytest.fixture
def mock_connection_pool():
    """Mock connection pool."""
    pool = Mock()
    pool.get_connection.return_value = Mock()
    return pool
