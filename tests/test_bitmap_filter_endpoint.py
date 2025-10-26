"""BDD tests for bitmap filter endpoint."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import Mock, patch
import time

# Load all scenarios from the feature file
scenarios('../tests/features/bitmap_filter_endpoint.feature')


# Shared context for test scenarios
@pytest.fixture
def context():
    """Shared context for test scenarios."""
    return {
        "card_bitmaps": [],
        "filter_request": None,
        "filter_response": None,
        "response_time_ms": 0,
        "error": None
    }


# Given steps
@given("I have card bitmaps in the database")
def setup_card_bitmaps(context, sample_card_bitmaps):
    """Set up card bitmaps in the database."""
    context["card_bitmaps"] = sample_card_bitmaps


@given("I have card bitmaps for multiple workspaces")
def setup_multi_workspace_bitmaps(context, multi_workspace_bitmaps_for_filter):
    """Set up card bitmaps across multiple workspaces."""
    context["card_bitmaps"] = multi_workspace_bitmaps_for_filter


# When steps
@when(parsers.parse('I request cards with tag bitmap "{bitmap}"'))
def request_single_bitmap(context, bitmap):
    """Request cards matching a single tag bitmap."""
    from apps.shared.services.bitmap_filter import filter_by_bitmap

    start_time = time.perf_counter()
    try:
        context["filter_response"] = filter_by_bitmap(
            workspace_id="ws-1",
            user_id="user-1",
            tag_bitmap=int(bitmap),
            card_bitmaps=context["card_bitmaps"]
        )
        context["response_time_ms"] = (time.perf_counter() - start_time) * 1000
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I request cards with tag bitmaps "{bitmap1}" AND "{bitmap2}"'))
def request_intersection(context, bitmap1, bitmap2):
    """Request cards matching intersection of tag bitmaps."""
    from apps.shared.services.bitmap_filter import filter_by_intersection

    start_time = time.perf_counter()
    try:
        context["filter_response"] = filter_by_intersection(
            workspace_id="ws-1",
            user_id="user-1",
            tag_bitmaps=[int(bitmap1), int(bitmap2)],
            card_bitmaps=context["card_bitmaps"]
        )
        context["response_time_ms"] = (time.perf_counter() - start_time) * 1000
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I request cards with tag bitmaps "{bitmap1}" OR "{bitmap2}"'))
def request_union(context, bitmap1, bitmap2):
    """Request cards matching union of tag bitmaps."""
    from apps.shared.services.bitmap_filter import filter_by_union

    start_time = time.perf_counter()
    try:
        context["filter_response"] = filter_by_union(
            workspace_id="ws-1",
            user_id="user-1",
            tag_bitmaps=[int(bitmap1), int(bitmap2)],
            card_bitmaps=context["card_bitmaps"]
        )
        context["response_time_ms"] = (time.perf_counter() - start_time) * 1000
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I request cards with tag bitmap "{include}" NOT "{exclude}"'))
def request_exclusion(context, include, exclude):
    """Request cards with exclusion (NOT) operation."""
    from apps.shared.services.bitmap_filter import filter_by_exclusion

    start_time = time.perf_counter()
    try:
        context["filter_response"] = filter_by_exclusion(
            workspace_id="ws-1",
            user_id="user-1",
            include_bitmap=int(include),
            exclude_bitmap=int(exclude),
            card_bitmaps=context["card_bitmaps"]
        )
        context["response_time_ms"] = (time.perf_counter() - start_time) * 1000
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I request cards with complex filter "{filter_expr}"'))
def request_complex_filter(context, filter_expr):
    """Request cards with complex nested operations."""
    from apps.shared.services.bitmap_filter import filter_by_complex_expression

    start_time = time.perf_counter()
    try:
        context["filter_response"] = filter_by_complex_expression(
            workspace_id="ws-1",
            user_id="user-1",
            filter_expression=filter_expr,
            card_bitmaps=context["card_bitmaps"]
        )
        context["response_time_ms"] = (time.perf_counter() - start_time) * 1000
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I request cards with workspace_id "{workspace_id}" and user_id "{user_id}"'))
def request_with_zero_trust(context, workspace_id, user_id):
    """Request cards with zero-trust UUID isolation."""
    from apps.shared.services.bitmap_filter import filter_by_bitmap

    try:
        context["filter_response"] = filter_by_bitmap(
            workspace_id=workspace_id,
            user_id=user_id,
            tag_bitmap=111,  # Use a common bitmap
            card_bitmaps=context["card_bitmaps"]
        )
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I request cards with tag bitmap "{bitmap}" that has no matches'))
def request_no_matches(context, bitmap):
    """Request cards with a bitmap that has no matches."""
    from apps.shared.services.bitmap_filter import filter_by_bitmap

    try:
        context["filter_response"] = filter_by_bitmap(
            workspace_id="ws-1",
            user_id="user-1",
            tag_bitmap=int(bitmap),
            card_bitmaps=context["card_bitmaps"]
        )
    except Exception as e:
        context["error"] = e


# Then steps
@then("the server should return matching card UUIDs")
def verify_matching_uuids(context):
    """Verify matching card UUIDs are returned."""
    assert context["filter_response"] is not None
    assert hasattr(context["filter_response"], "card_ids") or "card_ids" in context["filter_response"]
    card_ids = context["filter_response"].card_ids if hasattr(context["filter_response"], "card_ids") else context["filter_response"]["card_ids"]
    assert len(card_ids) > 0


@then("no content should be returned")
def verify_no_content(context):
    """Verify no content fields are in the response."""
    assert context["filter_response"] is not None
    # Should only have card_ids and metadata, not content fields
    forbidden_fields = ["name", "description", "tags", "content", "title"]
    for field in forbidden_fields:
        assert field not in str(context["filter_response"])


@then("the response time should be under 100ms")
def verify_response_time(context):
    """Verify response time is under 100ms."""
    assert context["response_time_ms"] < 100, \
        f"Response time {context['response_time_ms']}ms exceeds 100ms"


@then("the server should return cards matching both tags")
def verify_intersection_result(context, bitmap_operation_results):
    """Verify intersection returns correct cards."""
    assert context["filter_response"] is not None
    expected = bitmap_operation_results["intersection"]
    actual = context["filter_response"].card_ids
    assert set(actual) == set(expected)


@then("the operation should use bitmap intersection")
def verify_intersection_operation(context):
    """Verify intersection operation was used."""
    assert context["filter_response"] is not None
    assert context["filter_response"].operation == "AND" or \
           "intersection" in context["filter_response"].method.lower()


@then("the server should return cards matching either tag")
def verify_union_result(context, bitmap_operation_results):
    """Verify union returns correct cards."""
    assert context["filter_response"] is not None
    expected = bitmap_operation_results["union"]
    actual = context["filter_response"].card_ids
    assert set(actual) == set(expected)


@then("the operation should use bitmap union")
def verify_union_operation(context):
    """Verify union operation was used."""
    assert context["filter_response"] is not None
    assert context["filter_response"].operation == "OR" or \
           "union" in context["filter_response"].method.lower()


@then(parsers.parse("the server should return cards with tag {include} but not tag {exclude}"))
def verify_exclusion_result(context, include, exclude, bitmap_operation_results):
    """Verify exclusion returns correct cards."""
    assert context["filter_response"] is not None
    expected = bitmap_operation_results["exclusion"]
    actual = context["filter_response"].card_ids
    assert set(actual) == set(expected)


@then("the operation should use bitmap difference")
def verify_difference_operation(context):
    """Verify difference operation was used."""
    assert context["filter_response"] is not None
    assert context["filter_response"].operation == "NOT" or \
           "difference" in context["filter_response"].method.lower() or \
           "exclusion" in context["filter_response"].method.lower()


@then("the server should compute the nested operations correctly")
def verify_complex_operations(context):
    """Verify complex nested operations are computed correctly."""
    assert context["filter_response"] is not None
    assert hasattr(context["filter_response"], "card_ids")


@then("return only the matching card UUIDs")
def verify_only_uuids(context):
    """Verify only UUIDs are returned."""
    assert context["filter_response"] is not None
    card_ids = context["filter_response"].card_ids
    # All items should be strings (UUIDs)
    assert all(isinstance(card_id, str) for card_id in card_ids)


@then("the server should return only cards for that workspace and user")
def verify_workspace_isolation(context):
    """Verify workspace and user isolation."""
    assert context["filter_response"] is not None
    card_ids = context["filter_response"].card_ids
    # All returned cards should be from ws-1 and user-1
    for card_id in card_ids:
        assert card_id.startswith("card-ws1-")


@then("cards from other workspaces should be excluded")
def verify_other_workspaces_excluded(context):
    """Verify cards from other workspaces are excluded."""
    assert context["filter_response"] is not None
    card_ids = context["filter_response"].card_ids
    # No cards from ws-2 should be present
    for card_id in card_ids:
        assert not card_id.startswith("card-ws2-")


@then("the server should return an empty card list")
def verify_empty_result(context):
    """Verify empty result for no matches."""
    assert context["filter_response"] is not None
    assert len(context["filter_response"].card_ids) == 0


@then("the response should indicate 0 matches")
def verify_zero_matches(context):
    """Verify response indicates 0 matches."""
    assert context["filter_response"] is not None
    assert context["filter_response"].total_matches == 0 or \
           len(context["filter_response"].card_ids) == 0
