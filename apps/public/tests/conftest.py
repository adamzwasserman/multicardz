"""Pytest configuration for public website tests."""

# Import all fixtures to make them available to tests
pytest_plugins = [
    'tests.fixtures.landing_page_fixtures',
    'tests.fixtures.analytics_fixtures',
    'tests.fixtures.conversion_fixtures',
]
