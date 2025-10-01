from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def mock_db_connection():
    """Mock async database connection."""
    mock = AsyncMock()
    mock.execute.return_value = None
    mock.fetchone.return_value = {"count": 5}
    return mock

@pytest.fixture
def sample_tag_counts() -> dict[str, int]:
    """Sample tag counts."""
    return {
        "tag_a": 10,
        "tag_b": 5,
        "tag_c": 0,
        "tag_d": 15
    }

@pytest.fixture
def tag_update_scenarios() -> list[dict]:
    """Tag update test scenarios."""
    return [
        {
            "old_tags": ["tag_a", "tag_b"],
            "new_tags": ["tag_b", "tag_c"],
            "expected_changes": {
                "tag_a": -1,
                "tag_b": 0,
                "tag_c": +1
            }
        }
    ]
