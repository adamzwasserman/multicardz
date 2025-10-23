"""Step definitions for landing page route tests."""

from pytest_bdd import scenarios, given, when, then, parsers
import json
from sqlalchemy import text


scenarios('../features/landing_page_routes.feature')


@given("the database has landing pages", target_fixture="db_with_pages")
def setup_database_with_pages(db_connection, sample_landing_page_db):
    """Insert sample landing pages into database."""
    # Clean up first
    db_connection.execute(text("DELETE FROM landing_page_sections"))
    db_connection.execute(text("DELETE FROM landing_pages"))
    db_connection.commit()

    # Insert landing page
    page = sample_landing_page_db['page']
    db_connection.execute(
        text("""
            INSERT INTO landing_pages
            (id, slug, category, name, headline, subheadline, competitor_name, is_active, created, modified)
            VALUES (:id, :slug, :category, :name, :headline, :subheadline, :competitor_name, :is_active, :created, :modified)
        """),
        page
    )

    # Insert sections
    for section in sample_landing_page_db['sections']:
        db_connection.execute(
            text("""
                INSERT INTO landing_page_sections
                (id, landing_page_id, section_type, order_index, data, created, modified)
                VALUES (:id, :landing_page_id, :section_type, :order_index, CAST(:data AS jsonb), :created, :modified)
            """),
            section
        )

    db_connection.commit()
    return db_connection


@given("a landing page exists with pain_points and benefits", target_fixture="db_with_sections")
def setup_page_with_sections(db_connection, sample_landing_page_db):
    """Insert landing page with various section types."""
    # Reuse the setup from db_with_pages
    return setup_database_with_pages(db_connection, sample_landing_page_db)


@given("a landing page exists but is_active is false", target_fixture="db_with_inactive")
def setup_inactive_page(db_connection, inactive_landing_page_db):
    """Insert inactive landing page."""
    # Clean up first
    db_connection.execute(text("DELETE FROM landing_page_sections"))
    db_connection.execute(text("DELETE FROM landing_pages"))
    db_connection.commit()

    # Insert inactive page
    page = inactive_landing_page_db['page']
    db_connection.execute(
        text("""
            INSERT INTO landing_pages
            (id, slug, category, name, headline, subheadline, competitor_name, is_active, created, modified)
            VALUES (:id, :slug, :category, :name, :headline, :subheadline, :competitor_name, :is_active, :created, :modified)
        """),
        page
    )
    db_connection.commit()
    return db_connection


@given("a landing page with complex JSONB data", target_fixture="db_with_complex")
def setup_complex_jsonb_page(db_connection, complex_jsonb_page_db):
    """Insert landing page with complex JSONB data."""
    # Clean up first
    db_connection.execute(text("DELETE FROM landing_page_sections"))
    db_connection.execute(text("DELETE FROM landing_pages"))
    db_connection.commit()

    # Insert page
    page = complex_jsonb_page_db['page']
    db_connection.execute(
        text("""
            INSERT INTO landing_pages
            (id, slug, category, name, headline, subheadline, competitor_name, is_active, created, modified)
            VALUES (:id, :slug, :category, :name, :headline, :subheadline, :competitor_name, :is_active, :created, :modified)
        """),
        page
    )

    # Insert sections
    for section in complex_jsonb_page_db['sections']:
        db_connection.execute(
            text("""
                INSERT INTO landing_page_sections
                (id, landing_page_id, section_type, order_index, data, created, modified)
                VALUES (:id, :landing_page_id, :section_type, :order_index, CAST(:data AS jsonb), :created, :modified)
            """),
            section
        )

    db_connection.commit()
    return db_connection


@when(parsers.parse('I request GET "{path}"'), target_fixture="api_response")
def request_landing_page(test_client, path):
    """Make GET request to landing page endpoint."""
    response = test_client.get(path)
    return response


@when(parsers.parse('I request GET "/{slug}"'), target_fixture="api_response")
def request_landing_page_by_slug(test_client, request):
    """Make GET request using slug from appropriate fixture."""
    # Force the db setup fixtures to run
    if 'db_with_sections' in request.fixturenames:
        request.getfixturevalue('db_with_sections')
        fixture_data = request.getfixturevalue('sample_landing_page_db')
    elif 'db_with_complex' in request.fixturenames:
        request.getfixturevalue('db_with_complex')
        fixture_data = request.getfixturevalue('complex_jsonb_page_db')
    elif 'db_with_inactive' in request.fixturenames:
        request.getfixturevalue('db_with_inactive')
        fixture_data = request.getfixturevalue('inactive_landing_page_db')
    else:
        # Fallback - use sample
        fixture_data = request.getfixturevalue('sample_landing_page_db')

    slug = fixture_data['page']['slug']
    response = test_client.get(f"/{slug}")
    return response


@then(parsers.parse("the response status should be {status_code:d}"))
def check_response_status(api_response, status_code):
    """Verify HTTP status code."""
    assert api_response.status_code == status_code, \
        f"Expected {status_code}, got {api_response.status_code}: {api_response.text}"


@then("the response should contain the landing page data")
def check_landing_page_data(api_response, sample_landing_page_db):
    """Verify response contains landing page data."""
    assert api_response.status_code == 200
    data = api_response.json()

    # Check main page fields
    assert data['slug'] == sample_landing_page_db['page']['slug']
    assert data['name'] == sample_landing_page_db['page']['name']
    assert data['headline'] == sample_landing_page_db['page']['headline']
    assert data['category'] == sample_landing_page_db['page']['category']


@then("the response should include all sections in order")
def check_sections_in_order(api_response, sample_landing_page_db):
    """Verify sections are included and ordered."""
    data = api_response.json()

    assert 'sections' in data
    sections = data['sections']

    # Should have 4 sections from fixture
    assert len(sections) == 4

    # Check order_index is sequential
    for i, section in enumerate(sections):
        assert section['order_index'] == i


@then("the response should include pain_point sections")
def check_pain_point_sections(api_response):
    """Verify pain_point sections exist."""
    data = api_response.json()
    sections = data['sections']

    pain_points = [s for s in sections if s['section_type'] == 'pain_point']
    assert len(pain_points) >= 1, "Should have at least one pain_point section"


@then("the response should include benefit sections")
def check_benefit_sections(api_response):
    """Verify benefit sections exist."""
    data = api_response.json()
    sections = data['sections']

    benefits = [s for s in sections if s['section_type'] == 'benefit']
    assert len(benefits) >= 1, "Should have at least one benefit section"


@then("the response should include comparison_metric sections")
def check_comparison_sections(api_response):
    """Verify comparison_metric sections exist."""
    data = api_response.json()
    sections = data['sections']

    comparisons = [s for s in sections if s['section_type'] == 'comparison_metric']
    assert len(comparisons) >= 1, "Should have at least one comparison_metric section"


@then("sections should be ordered by order_index")
def check_sections_ordered(api_response):
    """Verify sections are properly ordered."""
    data = api_response.json()
    sections = data['sections']

    # Extract order_index values
    indices = [s['order_index'] for s in sections]

    # Should be sorted
    assert indices == sorted(indices), "Sections should be ordered by order_index"


@then("the response should contain an error message")
def check_error_message(api_response):
    """Verify error response contains message."""
    assert api_response.status_code == 404
    data = api_response.json()
    assert 'detail' in data or 'error' in data


@then("the response should indicate page not found")
def check_page_not_found(api_response):
    """Verify 404 response for inactive page."""
    assert api_response.status_code == 404
    data = api_response.json()
    assert 'detail' in data or 'error' in data


@then("the response should contain parsed JSONB data")
def check_jsonb_parsed(api_response):
    """Verify JSONB data is properly parsed."""
    data = api_response.json()
    sections = data['sections']

    # Check that sections have data field with parsed JSON
    for section in sections:
        assert 'data' in section
        assert isinstance(section['data'], dict), "data should be parsed as dict, not string"


@then("the data should be properly structured")
def check_data_structure(api_response):
    """Verify JSONB data has proper structure."""
    data = api_response.json()
    sections = data['sections']

    # Find testimonial section
    testimonials = [s for s in sections if s['section_type'] == 'testimonial']
    if testimonials:
        testimonial = testimonials[0]
        assert 'quote' in testimonial['data']
        assert 'author' in testimonial['data']
        assert 'role' in testimonial['data']


@then("all section fields should be accessible")
def check_section_fields(api_response):
    """Verify all section fields are accessible."""
    data = api_response.json()
    sections = data['sections']

    for section in sections:
        # All sections should have these fields
        assert 'section_type' in section
        assert 'order_index' in section
        assert 'data' in section

        # data should be a dict
        assert isinstance(section['data'], dict)
