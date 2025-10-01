"""
pytest configuration for MultiCardz™ shared package tests.
"""

import pytest
# Commented out to avoid import errors when testing templates
# from fastapi.testclient import TestClient

from apps.shared.models import Attachment, CardDetail, CardSummary, UserTier, Workspace
from jinja2 import Environment, DictLoader


@pytest.fixture
def sample_card_summary():
    """Create a sample card summary for testing."""
    return CardSummary(
        id="TEST0001", title="Sample Card", tags=frozenset(["test", "sample"])
    )


@pytest.fixture
def sample_card_detail():
    """Create a sample card detail for testing."""
    return CardDetail(
        id="TEST0001",
        content="This is a test card with detailed content",
        metadata={"priority": "high", "category": "test"},
    )


@pytest.fixture
def sample_workspace():
    """Create a sample workspace for testing."""
    return Workspace(
        id="ws-TEST001",
        name="Test Workspace",
        description="A workspace for testing",
        card_ids=frozenset(["TEST0001", "TEST0002"]),
        owner_id="user-123",
    )


@pytest.fixture
def sample_card_summaries():
    """Create multiple sample card summaries for testing."""
    return [
        CardSummary(
            id="CARD0001",
            title="Video Project",
            tags=frozenset(["video", "urgent", "marketing"]),
        ),
        CardSummary(
            id="CARD0002", title="Bug Fix", tags=frozenset(["bug", "urgent", "backend"])
        ),
        CardSummary(
            id="CARD0003",
            title="Feature Request",
            tags=frozenset(["feature", "enhancement", "frontend"]),
        ),
    ]


@pytest.fixture
def sample_attachment():
    """Create a sample attachment for testing."""
    return Attachment(
        card_id="TEST0001",
        filename="test_document.pdf",
        content_type="application/pdf",
        size_bytes=2048,
        data=b"fake pdf content for testing",
    )


@pytest.fixture
def sample_user_tier():
    """Create a sample user tier for testing."""
    return UserTier(
        user_id="USER123",
        tier="pro",
        max_attachment_size_mb=25,
        total_storage_quota_gb=10,
        current_storage_bytes=1024 * 1024 * 1024,  # 1GB
    )


@pytest.fixture
def test_client():
    """Test client with mocked auth for API route testing."""
    from fastapi.testclient import TestClient
    from apps.user.main import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture
def jinja_env():
    """Jinja2 environment for testing."""
    templates = {
        "card_grid.html": """
        <div class="card-grid" data-workspace="{{ workspace_id }}">
            {% for card in cards %}
            <div class="card" data-card-id="{{ card.card_id }}">
                {{ card.name }}
            </div>
            {% endfor %}
        </div>
        """,
        "tag_filter.html": """
        <div class="tag-filter" data-workspace="{{ workspace_id }}">
            <div id="tagsInPlay"></div>
        </div>
        """
    }
    return Environment(loader=DictLoader(templates))


@pytest.fixture
def workspace_context():
    """Workspace context for templates."""
    return {
        "workspace_id": "test-workspace",
        "workspace_name": "Test Workspace",
        "user_id": "test-user"
    }
