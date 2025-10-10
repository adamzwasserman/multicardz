"""
pytest configuration for MultiCardz™ shared package tests.
"""

import pytest
from jinja2 import DictLoader, Environment

# Commented out to avoid import errors when testing templates
# from fastapi.testclient import TestClient
from apps.shared.models import Attachment, CardDetail, CardSummary, UserTier, Workspace

# Import fixture modules to make them discoverable
pytest_plugins = [
    "tests.fixtures.model_fixtures",
    "tests.fixtures.api_fixtures",
    "tests.fixtures.bitmap_fixtures",
    "tests.fixtures.connection_fixtures",
    "tests.fixtures.tag_count_fixtures",
    "tests.fixtures.template_fixtures",
    "tests.fixtures.performance_fixtures",
    "tests.fixtures.database_mode_fixtures",
    "tests.fixtures.browser_service_fixtures",
    "tests.fixtures.bitmap_sync_fixtures",
    "tests.fixtures.query_routing_fixtures",
    "tests.fixtures.integration_fixtures",
    "tests.fixtures.connection_logic_fixtures",
    "tests.fixtures.bitmap_filter_fixtures",
    "tests.fixtures.card_creation_fixtures",
]


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


# Performance testing fixtures
from typing import FrozenSet
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class TestCard:
    card_id: str
    tag_bitmaps: tuple


@pytest.fixture
def large_card_set() -> FrozenSet[TestCard]:
    """Generate 100K test cards."""
    cards = []
    for i in range(100000):
        card = TestCard(
            card_id=f"card-{i:06d}",
            tag_bitmaps=tuple(random.sample(range(1, 100), k=random.randint(1, 10)))
        )
        cards.append(card)
    return frozenset(cards)


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics."""
    import psutil
    import time

    class Monitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.start_cpu = None

        def start(self):
            self.start_time = time.perf_counter()
            self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            self.start_cpu = psutil.cpu_percent()

        def stop(self):
            elapsed = time.perf_counter() - self.start_time
            memory = psutil.Process().memory_info().rss / 1024 / 1024 - self.start_memory
            cpu = psutil.cpu_percent() - self.start_cpu
            return {
                "elapsed": elapsed,
                "memory_mb": memory,
                "cpu_percent": cpu
            }

    return Monitor()


@pytest.fixture
def performance_test_datasets():
    """Generate performance test datasets of various sizes."""
    from packages.shared.src.backend.models.card_models import CardSummary

    datasets = {}

    # Generate datasets of different sizes
    for size in [100, 1000, 10000, 100000]:
        cards = frozenset([
            CardSummary(
                title=f"Card {i}",
                tags=frozenset({
                    f"team-{i % 5}",
                    f"priority-{i % 3}",
                    f"category-{i % 10}"
                })
            )
            for i in range(size)
        ])
        datasets[f"cards_{size}"] = cards

    return datasets


@pytest.fixture
def mathematical_validation_cases():
    """Test cases for mathematical property validation."""
    from packages.shared.src.backend.models.card_models import CardSummary

    # Create simple sets for property testing
    set_a = frozenset([
        CardSummary(title=f"A{i}", tags=frozenset({f"tag-{i}"}))
        for i in range(10)
    ])

    set_b = frozenset([
        CardSummary(title=f"B{i}", tags=frozenset({f"tag-{i}"}))
        for i in range(5, 15)
    ])

    return [
        {
            "property": "commutative_intersection",
            "sets": (set_a, set_b)
        }
    ]


@pytest.fixture
def complex_set_operation_scenarios():
    """Scenarios for testing complex set operations."""
    from packages.shared.src.backend.models.card_models import CardSummary

    set_a = frozenset([
        CardSummary(title=f"A{i}", tags=frozenset({f"tag-{i}"}))
        for i in range(10)
    ])

    set_b = frozenset([
        CardSummary(title=f"B{i}", tags=frozenset({f"tag-{i}"}))
        for i in range(5, 15)
    ])

    return [
        {
            "set_a": set_a,
            "set_b": set_b,
            "expected_properties": ["commutative_intersection", "associative_union"]
        }
    ]


@pytest.fixture
def cache_performance_context():
    """Context for cache performance testing."""
    from packages.shared.src.backend.domain.set_operations import clear_operation_cache

    # Clear cache before test
    clear_operation_cache()

    return {
        "cache_enabled": True,
        "expected_improvement": 0.7  # 70% improvement target
    }
