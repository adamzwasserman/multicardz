"""
Fixtures for analytics JavaScript testing.

Uses Playwright to test JavaScript behavior in real browser.
"""

import pytest
from pathlib import Path


@pytest.fixture
def analytics_js_path():
    """Path to analytics.js file."""
    return Path(__file__).parent.parent.parent / "static" / "js" / "analytics.js"


@pytest.fixture
def test_html_page():
    """HTML page with analytics.js loaded for testing."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Page</title>
</head>
<body>
    <h1>Test Landing Page</h1>
    <button class="cta-button" data-event="cta_click">Start Free Trial</button>
    <div style="height: 3000px;">
        <p>Scroll content for testing scroll depth tracking</p>
    </div>
    <script src="/static/js/analytics.js"></script>
    <script>
        // Initialize analytics on page load
        if (window.multicardzAnalytics) {
            window.analytics = new multicardzAnalytics();
        }
    </script>
</body>
</html>
"""


@pytest.fixture
def mock_api_server():
    """Mock analytics API server responses."""
    return {
        "session_create": {"status": "ok", "session_id": "test-session-123"},
        "page_view": {"status": "ok"},
        "events_batch": {"status": "ok", "received": 0}
    }


@pytest.fixture
def expected_session_keys():
    """Required keys in session data."""
    return [
        "session_id",
        "referrer_url",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "user_agent",
        "viewport_width",
        "viewport_height"
    ]


@pytest.fixture
def expected_page_view_keys():
    """Required keys in page view data."""
    return [
        "session_id",
        "url",
        "referrer",
        "viewport_width",
        "viewport_height",
        "timestamp"
    ]


@pytest.fixture
def expected_event_keys():
    """Required keys in event data."""
    return [
        "session_id",
        "event_type",
        "element_selector",
        "element_text",
        "element_position_x",
        "element_position_y",
        "timestamp_ms"
    ]
