from typing import Any

import pytest


@pytest.fixture
def valid_card_data() -> dict[str, Any]:
    """Valid card creation data."""
    return {
        "name": "Test Card",
        "description": "Test description",
        "user_id": "test-user-id",
        "workspace_id": "test-workspace-id"
    }

@pytest.fixture
def valid_tag_data() -> dict[str, Any]:
    """Valid tag creation data."""
    return {
        "name": "Test Tag",
        "user_id": "test-user-id",
        "workspace_id": "test-workspace-id",
        "tag_bitmap": 1
    }

@pytest.fixture
def invalid_isolation_data() -> dict[str, Any]:
    """Data missing workspace isolation."""
    return {
        "name": "Test Card",
        "user_id": "test-user-id"
        # Missing workspace_id
    }
