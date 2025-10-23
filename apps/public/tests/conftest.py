"""Pytest configuration for public website tests."""

# Import all fixtures to make them available to tests
pytest_plugins = [
    'tests.fixtures.landing_page_fixtures',
    'tests.fixtures.analytics_fixtures',
    'tests.fixtures.conversion_fixtures',
    'tests.fixtures.migration_fixtures',
    'tests.fixtures.fastapi_fixtures',
    'tests.fixtures.model_fixtures',
    'tests.fixtures.route_fixtures',
    'tests.fixtures.ab_test_fixtures',
    'tests.fixtures.smart_routing_fixtures',
    'tests.fixtures.template_fixtures',
]
