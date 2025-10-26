"""
Simple smoke tests for admin dashboard.

These tests verify basic functionality without full BDD coverage.
Full BDD implementation can be added later.
"""

import pytest
from fastapi.testclient import TestClient
from main import create_app


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    app = create_app()
    return TestClient(app)


def test_admin_metrics_endpoint_returns_200(test_client):
    """Test that admin metrics endpoint is accessible."""
    response = test_client.get("/admin/metrics")
    assert response.status_code == 200
    data = response.json()
    assert 'total_sessions' in data
    assert 'total_page_views' in data
    assert 'total_conversions' in data
    assert 'overall_conversion_rate' in data


def test_admin_landing_pages_endpoint(test_client):
    """Test landing pages performance endpoint."""
    response = test_client.get("/admin/landing-pages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_admin_ab_tests_endpoint(test_client):
    """Test A/B tests summary endpoint."""
    response = test_client.get("/admin/ab-tests")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_admin_traffic_sources_endpoint(test_client):
    """Test traffic sources breakdown endpoint."""
    response = test_client.get("/admin/traffic-sources")
    assert response.status_code == 200
    data = response.json()
    assert 'direct' in data
    assert 'organic_search' in data
    assert 'social' in data
    assert 'referral' in data


def test_dashboard_overview_accessible(test_client):
    """Test that dashboard overview page renders."""
    response = test_client.get("/admin/", headers={"accept": "application/json"})
    # Should return JSON if template rendering fails
    assert response.status_code == 200
    data = response.json()
    assert 'total_sessions' in data
