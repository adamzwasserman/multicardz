"""Step definitions for A/B test assignment feature."""

from pytest_bdd import scenarios, given, when, then, parsers
from uuid import uuid4
from sqlalchemy import text

# Load scenarios
scenarios('../features/ab_test_assignment.feature')


# Shared state
class Context:
    def __init__(self):
        self.ab_test = None
        self.session_id = None
        self.assigned_variant = None
        self.assigned_variants = []
        self.variant_counts = {}


@given("an active A/B test exists with 50/50 traffic split", target_fixture="context")
def active_ab_test_50_50(sample_ab_test, cleanup_ab_tests):
    """Set up active A/B test with 50/50 split."""
    ctx = Context()
    ctx.ab_test = sample_ab_test
    return ctx


@given("two variants exist for the test")
def two_variants_exist(context):
    """Verify two variants exist (already created in fixture)."""
    assert context.ab_test['variant_a_id'] is not None
    assert context.ab_test['variant_b_id'] is not None


@when("I request variant assignment for a new session")
def request_variant_assignment(context, db_connection):
    """Request variant assignment for new session."""
    from services.ab_test_service import assign_variant_for_session

    context.session_id = uuid4()
    context.assigned_variant = assign_variant_for_session(
        session_id=context.session_id,
        db=db_connection
    )


@then("a variant should be assigned deterministically")
def variant_assigned_deterministically(context):
    """Verify variant was assigned."""
    assert context.assigned_variant is not None
    assert 'variant_id' in context.assigned_variant
    assert 'landing_page_id' in context.assigned_variant


@then("the session should be linked to the variant")
def session_linked_to_variant(context, db_connection):
    """Verify session stored with variant link."""
    result = db_connection.execute(
        text("SELECT a_b_variant_id FROM analytics_sessions WHERE session_id = :sid"),
        {'sid': context.session_id}
    ).fetchone()

    assert result is not None
    assert result[0] == context.assigned_variant['variant_id']


# Scenario 2: Deterministic assignment
@given("an active A/B test with variants", target_fixture="context")
def ab_test_with_variants(sample_ab_test, cleanup_ab_tests):
    """Set up A/B test with variants."""
    ctx = Context()
    ctx.ab_test = sample_ab_test
    ctx.session_id = uuid4()
    return ctx


@when("I request assignment for the same session twice")
def request_assignment_twice(context, db_connection):
    """Request assignment twice with same session ID."""
    from services.ab_test_service import assign_variant_for_session

    # First assignment
    variant1 = assign_variant_for_session(
        session_id=context.session_id,
        db=db_connection
    )

    # Second assignment (should be same)
    variant2 = assign_variant_for_session(
        session_id=context.session_id,
        db=db_connection
    )

    context.assigned_variants = [variant1, variant2]


@then("the same variant should be returned both times")
def same_variant_both_times(context):
    """Verify deterministic assignment."""
    assert len(context.assigned_variants) == 2
    assert context.assigned_variants[0]['variant_id'] == context.assigned_variants[1]['variant_id']


# Scenario 3: Traffic split weights
@given("an A/B test with 70/30 split", target_fixture="context")
def ab_test_70_30_split(ab_test_70_30, cleanup_ab_tests):
    """Set up A/B test with 70/30 split."""
    ctx = Context()
    ctx.ab_test = ab_test_70_30
    return ctx


@when("I assign 1000 sessions to variants")
def assign_1000_sessions(context, db_connection):
    """Assign 1000 unique sessions to variants."""
    from services.ab_test_service import assign_variant_for_session

    context.variant_counts = {}

    for _ in range(1000):
        session_id = uuid4()
        variant = assign_variant_for_session(
            session_id=session_id,
            db=db_connection
        )

        if variant:
            variant_id = str(variant['variant_id'])
            context.variant_counts[variant_id] = context.variant_counts.get(variant_id, 0) + 1


@then("approximately 700 sessions should get variant A")
def approximately_700_variant_a(context):
    """Verify ~70% got variant A."""
    variant_a_id = str(context.ab_test['variant_a_id'])
    count = context.variant_counts.get(variant_a_id, 0)

    # Allow 5% margin: 650-750
    assert 650 <= count <= 750, f"Expected 650-750 for variant A, got {count}"


@then("approximately 300 sessions should get variant B")
def approximately_300_variant_b(context):
    """Verify ~30% got variant B."""
    variant_b_id = str(context.ab_test['variant_b_id'])
    count = context.variant_counts.get(variant_b_id, 0)

    # Allow 5% margin: 250-350
    assert 250 <= count <= 350, f"Expected 250-350 for variant B, got {count}"


@then("the distribution should be within 5% margin")
def distribution_within_margin(context):
    """Verify overall distribution is reasonable."""
    total = sum(context.variant_counts.values())
    assert total == 1000, f"Expected 1000 assignments, got {total}"


# Scenario 4: No active test
@given("no active A/B tests exist", target_fixture="context")
def no_active_tests(db_connection, cleanup_ab_tests):
    """Ensure no active A/B tests."""
    # cleanup_ab_tests fixture already cleared tests
    ctx = Context()
    ctx.session_id = uuid4()
    return ctx


@when("I request variant assignment")
def request_assignment_no_test(context, db_connection):
    """Request assignment when no test exists."""
    from services.ab_test_service import assign_variant_for_session

    context.assigned_variant = assign_variant_for_session(
        session_id=context.session_id,
        db=db_connection
    )


@then("no variant should be assigned")
def no_variant_assigned(context):
    """Verify None returned when no test."""
    assert context.assigned_variant is None


@then("the session should proceed without A/B test tracking")
def session_proceeds_without_tracking(context, db_connection):
    """Verify session can be created without variant."""
    # Session should not exist yet (or if it does, a_b_variant_id should be None)
    result = db_connection.execute(
        text("SELECT a_b_variant_id FROM analytics_sessions WHERE session_id = :sid"),
        {'sid': context.session_id}
    ).fetchone()

    # Either no session yet, or a_b_variant_id is NULL
    if result:
        assert result[0] is None
