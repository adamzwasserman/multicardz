"""Step definitions for Pydantic models tests."""

from pytest_bdd import scenarios, given, when, then, parsers
from uuid import UUID
from datetime import datetime

# Load scenarios from feature file
scenarios('../features/pydantic_models.feature')

# Import models
from models.landing_page import LandingPage
from models.analytics import AnalyticsSession, AnalyticsEvent


# Shared context
@given('a landing page dict with all fields', target_fixture='landing_page_dict')
def landing_page_dict(valid_landing_page_data):
    """Provide landing page dict."""
    return valid_landing_page_data


@when('I create a LandingPage Pydantic model', target_fixture='landing_page_model')
def create_landing_page_model(landing_page_dict):
    """Create LandingPage model from dict."""
    return LandingPage(**landing_page_dict)


@then('all fields should be validated')
def all_fields_validated(landing_page_model):
    """Verify all fields are present."""
    assert landing_page_model.slug == 'trello-performance'
    assert landing_page_model.category == 'REPLACEMENT'
    assert landing_page_model.name == 'Trello Performance Refugees'
    assert landing_page_model.headline is not None
    assert landing_page_model.is_active is True


@then('UUID fields should be proper UUIDs')
def uuid_fields_valid(landing_page_model):
    """Verify UUID fields are proper UUIDs."""
    assert isinstance(landing_page_model.id, UUID)


@then('timestamps should be datetime objects')
def timestamps_are_datetime(landing_page_model):
    """Verify timestamps are datetime objects."""
    assert isinstance(landing_page_model.created, datetime)
    assert isinstance(landing_page_model.modified, datetime)


# Analytics Event scenarios
@given('an analytics event dict', target_fixture='event_dict')
def event_dict(valid_event_data):
    """Provide event dict."""
    return valid_event_data


@when('I create an AnalyticsEvent model', target_fixture='event_model')
def create_event_model(event_dict):
    """Create AnalyticsEvent model from dict."""
    return AnalyticsEvent(**event_dict)


@then('required fields should be enforced')
def required_fields_enforced(event_dict):
    """Verify required fields are enforced."""
    from pydantic import ValidationError
    import pytest

    # Remove required field
    invalid_data = event_dict.copy()
    del invalid_data['event_type']

    # Should raise validation error
    with pytest.raises(ValidationError):
        AnalyticsEvent(**invalid_data)


@then('optional fields should be nullable')
def optional_fields_nullable():
    """Verify optional fields can be None."""
    from uuid import uuid4

    # Create with minimal required fields
    minimal_event = AnalyticsEvent(
        session_id=uuid4(),
        page_view_id=uuid4(),
        event_type='click',
        timestamp_ms=1000
    )

    assert minimal_event.element_selector is None
    assert minimal_event.element_text is None


@then('timestamp_ms should be a positive integer')
def timestamp_ms_positive(event_dict):
    """Verify timestamp_ms must be positive."""
    from pydantic import ValidationError
    import pytest

    # Try negative timestamp
    invalid_data = event_dict.copy()
    invalid_data['timestamp_ms'] = -100

    with pytest.raises(ValidationError):
        AnalyticsEvent(**invalid_data)


# Session scenarios
@given('session data with referrer and UTM params', target_fixture='session_dict')
def session_dict(valid_session_data):
    """Provide session dict."""
    return valid_session_data


@when('I create an AnalyticsSession model', target_fixture='session_model')
def create_session_model(session_dict):
    """Create AnalyticsSession model from dict."""
    return AnalyticsSession(**session_dict)


@then('UTM parameters should be extracted')
def utm_params_extracted(session_model):
    """Verify UTM parameters are present."""
    assert session_model.utm_source == 'google'
    assert session_model.utm_medium == 'cpc'
    assert session_model.utm_campaign == 'trello-refugees'
    assert session_model.utm_term == 'trello alternative'
    assert session_model.utm_content == 'ad-1'


@then('referrer_domain should be parsed')
def referrer_domain_parsed(session_model):
    """Verify referrer domain is extracted from URL."""
    assert session_model.referrer_domain == 'google.com'


@then('session_id should be generated if not provided')
def session_id_generated():
    """Verify session_id is auto-generated."""
    # Create without session_id
    session = AnalyticsSession()

    assert session.session_id is not None
    assert isinstance(session.session_id, UUID)
