# tests/fixtures/api_fixtures.py
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Test client with mocked auth."""
    from apps.user.main import app
    return TestClient(app)

@pytest.fixture
def auth_headers() -> dict:
    """Authentication headers."""
    return {
        "Authorization": "Bearer test-token",
        "X-Workspace-Id": "test-workspace",
        "X-User-Id": "test-user"
    }

@pytest.fixture
def mock_auth_middleware():
    """Mock authentication middleware."""
    with patch('apps.user.middleware.verify_workspace_access') as mock:
        mock.return_value = True
        yield mock
