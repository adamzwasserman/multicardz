"""Fixtures for FastAPI application testing."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(db_connection):
    """Create FastAPI test client with shared database session."""
    import sys
    from pathlib import Path

    # Add apps/public to path for imports
    public_path = Path(__file__).parent.parent.parent
    if str(public_path) not in sys.path:
        sys.path.insert(0, str(public_path))

    from main import create_app
    from config.database import get_db

    app = create_app()

    # Override get_db dependency to use test database session
    def override_get_db():
        try:
            yield db_connection
        finally:
            pass  # Don't close - managed by db_connection fixture

    app.dependency_overrides[get_db] = override_get_db

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
