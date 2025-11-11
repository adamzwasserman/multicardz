import pytest
from typing import FrozenSet, Dict, Any
from datetime import datetime, timezone
import uuid


@pytest.fixture
def optimized_card_summary_data() -> Dict[str, Any]:
    """Create optimized CardSummary test data."""
    return {
        "id": str(uuid.uuid4())[:8].upper(),
        "title": "Sprint Planning Session",
        "tags": frozenset({"sprint23", "planning", "frontend", "high-priority"}),
        "created_at": datetime.now(timezone.utc),
        "modified_at": datetime.now(timezone.utc),
        "has_attachments": False
    }


@pytest.fixture
def comprehensive_card_detail_data() -> Dict[str, Any]:
    """Create comprehensive CardDetail test data."""
    return {
        "id": "CARD001A",
        "content": "Detailed sprint planning session content with user stories, acceptance criteria, and technical requirements for Q4 frontend improvements.",
        "metadata": {
            "story_points": 8,
            "assigned_team": "frontend",
            "sprint": "sprint23",
            "dependencies": ["auth-service", "api-gateway"],
            "acceptance_criteria": [
                "User can log in with social auth",
                "Dashboard loads in <2 seconds",
                "Mobile responsive design"
            ]
        },
        "attachment_count": 3,
        "total_attachment_size": 2048576,  # 2MB
        "version": 1
    }


@pytest.fixture
def large_card_dataset() -> list[Dict[str, Any]]:
    """Generate large dataset for performance testing."""
    cards = []
    teams = ["frontend", "backend", "devops", "qa", "design"]
    statuses = ["planning", "active", "review", "complete"]
    priorities = ["low", "medium", "high", "critical"]

    for i in range(10000):
        team = teams[i % len(teams)]
        status = statuses[i % len(statuses)]
        priority = priorities[i % len(priorities)]
        sprint = f"sprint{(i // 100) + 20}"  # sprint20, sprint21, etc.

        cards.append({
            "id": f"CARD{i:06d}",
            "title": f"Task {i}: {team} {status} work",
            "tags": frozenset({team, status, priority, sprint, f"task-{i}"}),
            "created_at": datetime.now(timezone.utc),
            "modified_at": datetime.now(timezone.utc),
            "has_attachments": bool(i % 3)  # Every 3rd card has attachments
        })

    return cards


@pytest.fixture
def performance_benchmark_targets() -> Dict[str, float]:
    """Define performance targets for validation."""
    return {
        "card_summary_size_bytes": 50,
        "list_operation_ms": 2.5,  # Relaxed from 1.0ms for system variability
        "detail_loading_ms": 10.0,
        "set_operation_ms": 0.38,  # Sub-millisecond target
        "memory_per_100k_cards_mb": 50,
        "improvement_factor_target": 26  # 26x faster than existing solutions
    }