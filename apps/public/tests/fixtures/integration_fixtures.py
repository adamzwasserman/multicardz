"""
Fixtures for analytics JavaScript integration testing.
"""
import pytest
from pathlib import Path


@pytest.fixture
def all_analytics_modules():
    """Load all analytics JavaScript modules."""
    modules = {}
    base_path = Path(__file__).parent.parent.parent / "static" / "js"

    # Load analytics.js
    analytics_file = base_path / "analytics.js"
    if analytics_file.exists():
        modules['analytics'] = analytics_file.read_text()

    # Load mouse-tracking.js
    mouse_file = base_path / "mouse-tracking.js"
    if mouse_file.exists():
        modules['mouse_tracking'] = mouse_file.read_text()

    # Load conversion-tracking.js
    conversion_file = base_path / "conversion-tracking.js"
    if conversion_file.exists():
        modules['conversion_tracking'] = conversion_file.read_text()

    return modules


@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "session_id": "integration-test-session-123",
        "landing_page_id": "test-page-456",
        "modules_loaded": {
            "analytics": False,
            "mouse_tracking": False,
            "conversion_tracking": False
        },
        "shared_session": None
    }
