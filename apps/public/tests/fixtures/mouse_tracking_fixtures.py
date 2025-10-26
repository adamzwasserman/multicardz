"""
Fixtures for mouse tracking JavaScript testing.
"""

import pytest
from pathlib import Path


@pytest.fixture
def mouse_tracking_js_path():
    """Path to mouse-tracking.js file."""
    return Path(__file__).parent.parent.parent / "static" / "js" / "mouse-tracking.js"


@pytest.fixture
def sample_rate_ms():
    """Default sampling rate for mouse tracking."""
    return 100  # 100ms = 10 samples per second


@pytest.fixture
def batch_size():
    """Batch size for mouse position buffering."""
    return 50  # Send every 50 positions


@pytest.fixture
def test_mouse_positions():
    """Sample mouse positions for testing."""
    return [
        {"x": 100, "y": 150, "timestamp": 1000},
        {"x": 105, "y": 155, "timestamp": 1100},
        {"x": 110, "y": 160, "timestamp": 1200},
        {"x": 115, "y": 165, "timestamp": 1300},
        {"x": 120, "y": 170, "timestamp": 1400},
    ]


@pytest.fixture
def expected_mouse_tracking_keys():
    """Required keys in mouse tracking data."""
    return [
        "session_id",
        "page_view_id",
        "positions",  # Array of {x, y, t}
        "timestamp"
    ]


@pytest.fixture
def privacy_settings():
    """Privacy settings for mouse tracking."""
    return {
        "enable_mouse_tracking": True,
        "enable_session_replay": True,
        "respect_do_not_track": True
    }
