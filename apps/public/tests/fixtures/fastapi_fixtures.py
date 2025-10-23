"""Fixtures for FastAPI application testing."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    import sys
    from pathlib import Path

    # Add apps/public to path for imports
    public_path = Path(__file__).parent.parent.parent
    if str(public_path) not in sys.path:
        sys.path.insert(0, str(public_path))

    from main import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture
def expected_security_headers():
    """Expected security headers in all responses."""
    return {
        'x-frame-options': 'DENY',
        'x-content-type-options': 'nosniff',
        'x-xss-protection': '1; mode=block',
        'strict-transport-security': 'max-age=31536000; includeSubDomains'
    }


@pytest.fixture
def allowed_origins():
    """List of allowed CORS origins."""
    return [
        "https://multicardz.com",
        "https://www.multicardz.com",
        "https://app.multicardz.com"
    ]
