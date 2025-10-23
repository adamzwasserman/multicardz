"""
Fixtures for conversion tracking JavaScript testing.
"""
import pytest
from pathlib import Path


@pytest.fixture
def conversion_tracking_js():
    """Load conversion-tracking.js file."""
    js_file = Path(__file__).parent.parent.parent / "static" / "js" / "conversion-tracking.js"
    if js_file.exists():
        return js_file.read_text()
    return None


@pytest.fixture
def conversion_tracking_config():
    """Configuration for conversion tracking tests."""
    return {
        "batch_size": 5,
        "batch_interval": 5000,  # 5 seconds
        "api_endpoint": "/api/analytics/conversion",
        "funnel_stages": ["view", "cta_click", "account_create", "activate", "upgrade"],
        "cta_selector": "[data-cta]"
    }


@pytest.fixture
def mock_session_id():
    """Mock session ID for testing."""
    return "test-session-123"


@pytest.fixture
def mock_landing_page_id():
    """Mock landing page ID for testing."""
    return "page-abc-456"


@pytest.fixture
def mock_cta_buttons():
    """Mock CTA button configurations."""
    return [
        {
            "id": "hero-cta",
            "text": "Start Free Trial",
            "selector": '[data-cta="hero-cta"]',
            "position": {"x": 100, "y": 200}
        },
        {
            "id": "footer-cta",
            "text": "Get Started Now",
            "selector": '[data-cta="footer-cta"]',
            "position": {"x": 150, "y": 800}
        },
        {
            "id": "signup",
            "text": "Sign Up",
            "selector": '[data-cta="signup"]',
            "position": {"x": 200, "y": 300}
        }
    ]
