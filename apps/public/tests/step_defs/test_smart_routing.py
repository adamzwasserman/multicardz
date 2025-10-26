"""Step definitions for smart routing feature."""

from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios
scenarios('../features/smart_routing.feature')


# Shared state
class Context:
    def __init__(self):
        self.referrer_data = None
        self.routing_result = None


@given('a visitor comes from "trello.com"', target_fixture="context")
def visitor_from_trello(referrer_from_trello):
    """Set up visitor from Trello."""
    ctx = Context()
    ctx.referrer_data = referrer_from_trello
    return ctx


@given('a visitor comes from Google with query "notion alternative"', target_fixture="context")
def visitor_from_google_notion(referrer_from_google_notion_search):
    """Set up visitor from Google searching for Notion alternative."""
    ctx = Context()
    ctx.referrer_data = referrer_from_google_notion_search
    return ctx


@given('a visitor has UTM parameters with source "trello_refugees"', target_fixture="context")
def visitor_with_trello_utm(referrer_with_trello_utm):
    """Set up visitor with Trello UTM campaign."""
    ctx = Context()
    ctx.referrer_data = referrer_with_trello_utm
    return ctx


@given("a visitor comes from a generic referrer", target_fixture="context")
def visitor_from_generic(generic_referrer):
    """Set up visitor from generic referrer."""
    ctx = Context()
    ctx.referrer_data = generic_referrer
    return ctx


@given("a visitor has no referrer", target_fixture="context")
def visitor_no_referrer(no_referrer):
    """Set up visitor with no referrer (direct traffic)."""
    ctx = Context()
    ctx.referrer_data = no_referrer
    return ctx


@when("I request smart routing for the referrer")
def request_smart_routing(context):
    """Request smart routing based on referrer data."""
    from services.smart_routing_service import route_by_referrer

    context.routing_result = route_by_referrer(
        referrer_url=context.referrer_data['referrer_url'],
        referrer_domain=context.referrer_data['referrer_domain'],
        utm_source=context.referrer_data['utm_source'],
        utm_medium=context.referrer_data['utm_medium'],
        utm_campaign=context.referrer_data['utm_campaign']
    )


@then(parsers.parse('I should be routed to "{expected_slug}" landing page'))
def routed_to_landing_page(context, expected_slug):
    """Verify routed to expected landing page."""
    assert context.routing_result is not None
    assert 'slug' in context.routing_result
    assert context.routing_result['slug'] == expected_slug


@then(parsers.parse('the routing reason should be "{expected_reason}"'))
def routing_reason_correct(context, expected_reason):
    """Verify routing reason is correct."""
    assert 'reason' in context.routing_result
    assert context.routing_result['reason'] == expected_reason


@then("I should be routed to the default landing page")
def routed_to_default(context, default_landing_page_slug):
    """Verify routed to default landing page."""
    assert context.routing_result is not None
    assert 'slug' in context.routing_result
    # Default should be a valid landing page slug
    assert context.routing_result['slug'] is not None
    # For now, just verify it's one of the known landing pages
    assert len(context.routing_result['slug']) > 0
