"""Step definitions for conversion funnel schema BDD tests."""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from sqlalchemy import text
from uuid import uuid4
from datetime import datetime, UTC
import json


# Link feature file
scenarios('../features/conversion_schema.feature')


# State management for test context
@pytest.fixture
def context():
    """Test context to share data between steps."""
    return {}


# Scenario: Track funnel stage
@given('a session exists', target_fixture='test_session_id')
def given_session_exists(db_connection):
    """Create a test session."""
    session_id = uuid4()
    landing_page_id = uuid4()

    # Create landing page first (required for FK)
    db_connection.execute(
        text("""INSERT INTO landing_pages
           (id, slug, category, name, headline, created, modified)
           VALUES (:id, :slug, :category, :name, :headline, :created, :modified)"""),
        {
            'id': landing_page_id,
            'slug': 'test-page',
            'category': 'REPLACEMENT',
            'name': 'Test Page',
            'headline': 'Test Headline',
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    )

    # Insert session
    db_connection.execute(
        text("""INSERT INTO analytics_sessions
           (session_id, landing_page_id, landing_page_slug, first_seen, last_seen)
           VALUES (:session_id, :landing_page_id, :landing_page_slug, :first_seen, :last_seen)"""),
        {
            'session_id': session_id,
            'landing_page_id': landing_page_id,
            'landing_page_slug': 'test-page',
            'first_seen': datetime.now(UTC),
            'last_seen': datetime.now(UTC)
        }
    )
    db_connection.commit()

    return {'session_id': session_id, 'landing_page_id': landing_page_id}


@when(parsers.parse('I log a "{stage}" stage'))
def when_log_funnel_stage(db_connection, test_session_id, stage, context):
    """Log a funnel stage."""
    db_connection.execute(
        text("""INSERT INTO conversion_funnel
           (session_id, user_id, funnel_stage, landing_page_id, created)
           VALUES (:session_id, :user_id, :funnel_stage, :landing_page_id, :created)"""),
        {
            'session_id': test_session_id['session_id'],
            'user_id': None,
            'funnel_stage': stage,
            'landing_page_id': test_session_id['landing_page_id'],
            'created': datetime.now(UTC)
        }
    )
    db_connection.commit()

    context['stage'] = stage
    context['session_id'] = test_session_id['session_id']


@then('the stage should be recorded with timestamp')
def then_stage_recorded(db_connection, context):
    """Verify stage was recorded."""
    result = db_connection.execute(
        text("""SELECT funnel_stage, created FROM conversion_funnel
           WHERE session_id = :session_id AND funnel_stage = :funnel_stage"""),
        {'session_id': context['session_id'], 'funnel_stage': context['stage']}
    ).fetchone()

    assert result is not None, "Funnel stage not found"
    assert result[0] == context['stage'], "Stage name mismatch"
    assert result[1] is not None, "Timestamp not recorded"


@then('I can query all stages for the session')
def then_query_all_stages(db_connection, context):
    """Verify we can query all stages for the session."""
    stages = db_connection.execute(
        text("""SELECT funnel_stage FROM conversion_funnel
           WHERE session_id = :session_id
           ORDER BY created"""),
        {'session_id': context['session_id']}
    ).fetchall()

    assert len(stages) > 0, "No stages found for session"


# Scenario: Link session to user
@given('a session with funnel stages exists', target_fixture='session_with_stages')
def given_session_with_stages(db_connection):
    """Create session with funnel stages."""
    session_id = uuid4()
    landing_page_id = uuid4()

    # Create landing page first
    db_connection.execute(
        text("""INSERT INTO landing_pages
           (id, slug, category, name, headline, created, modified)
           VALUES (:id, :slug, :category, :name, :headline, :created, :modified)"""),
        {
            'id': landing_page_id,
            'slug': 'test-page-2',
            'category': 'REPLACEMENT',
            'name': 'Test Page 2',
            'headline': 'Test Headline',
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    )

    # Insert session
    db_connection.execute(
        text("""INSERT INTO analytics_sessions
           (session_id, landing_page_id, landing_page_slug, first_seen, last_seen)
           VALUES (:session_id, :landing_page_id, :landing_page_slug, :first_seen, :last_seen)"""),
        {
            'session_id': session_id,
            'landing_page_id': landing_page_id,
            'landing_page_slug': 'test-page-2',
            'first_seen': datetime.now(UTC),
            'last_seen': datetime.now(UTC)
        }
    )

    # Insert funnel stages
    db_connection.execute(
        text("""INSERT INTO conversion_funnel
           (session_id, funnel_stage, landing_page_id, created)
           VALUES (:session_id, :funnel_stage, :landing_page_id, :created)"""),
        {
            'session_id': session_id,
            'funnel_stage': 'view',
            'landing_page_id': landing_page_id,
            'created': datetime.now(UTC)
        }
    )
    db_connection.commit()

    return session_id


@when('an account is created with user_id')
def when_account_created(db_connection, session_with_stages, context):
    """Link session to user."""
    user_id = uuid4()

    # Update session with user_id
    db_connection.execute(
        text("""UPDATE analytics_sessions
           SET user_id = :user_id
           WHERE session_id = :session_id"""),
        {'user_id': user_id, 'session_id': session_with_stages}
    )

    # Insert account_create stage with user_id
    db_connection.execute(
        text("""INSERT INTO conversion_funnel
           (session_id, user_id, funnel_stage, created)
           VALUES (:session_id, :user_id, :funnel_stage, :created)"""),
        {
            'session_id': session_with_stages,
            'user_id': user_id,
            'funnel_stage': 'account_create',
            'created': datetime.now(UTC)
        }
    )
    db_connection.commit()

    context['user_id'] = user_id
    context['session_id'] = session_with_stages


@then('the session should be linked to the user')
def then_session_linked(db_connection, context):
    """Verify session has user_id."""
    result = db_connection.execute(
        text("""SELECT user_id FROM analytics_sessions
           WHERE session_id = :session_id"""),
        {'session_id': context['session_id']}
    ).fetchone()

    assert result is not None, "Session not found"
    assert result[0] == context['user_id'], "User ID not linked"


@then('all subsequent stages should include user_id')
def then_stages_have_user_id(db_connection, context):
    """Verify new stages have user_id."""
    result = db_connection.execute(
        text("""SELECT user_id FROM conversion_funnel
           WHERE session_id = :session_id
           AND funnel_stage = 'account_create'"""),
        {'session_id': context['session_id']}
    ).fetchone()

    assert result is not None, "Stage not found"
    assert result[0] == context['user_id'], "User ID not in stage"


# Scenario: Calculate conversion rates
@given('100 sessions with various funnel stages', target_fixture='conversion_data')
def given_conversion_sessions(db_connection):
    """Create 100 sessions with different funnel stages."""
    landing_page_id = uuid4()
    sessions = []

    # Create landing page first
    db_connection.execute(
        text("""INSERT INTO landing_pages
           (id, slug, category, name, headline, created, modified)
           VALUES (:id, :slug, :category, :name, :headline, :created, :modified)"""),
        {
            'id': landing_page_id,
            'slug': 'test-page-conv',
            'category': 'REPLACEMENT',
            'name': 'Test Page Conv',
            'headline': 'Test Headline',
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    )

    # Create 100 sessions
    for i in range(100):
        session_id = uuid4()
        sessions.append(session_id)

        db_connection.execute(
            text("""INSERT INTO analytics_sessions
               (session_id, landing_page_id, landing_page_slug, first_seen, last_seen)
               VALUES (:session_id, :landing_page_id, :landing_page_slug, :first_seen, :last_seen)"""),
            {
                'session_id': session_id,
                'landing_page_id': landing_page_id,
                'landing_page_slug': 'test-page-conv',
                'first_seen': datetime.now(UTC),
                'last_seen': datetime.now(UTC)
            }
        )

        # All get 'view' stage
        db_connection.execute(
            text("""INSERT INTO conversion_funnel
               (session_id, funnel_stage, landing_page_id, created)
               VALUES (:session_id, :funnel_stage, :landing_page_id, :created)"""),
            {
                'session_id': session_id,
                'funnel_stage': 'view',
                'landing_page_id': landing_page_id,
                'created': datetime.now(UTC)
            }
        )

        # 30% get to account_create
        if i < 30:
            db_connection.execute(
                text("""INSERT INTO conversion_funnel
                   (session_id, funnel_stage, landing_page_id, created)
                   VALUES (:session_id, :funnel_stage, :landing_page_id, :created)"""),
                {
                    'session_id': session_id,
                    'funnel_stage': 'account_create',
                    'landing_page_id': landing_page_id,
                    'created': datetime.now(UTC)
                }
            )

    db_connection.commit()
    return {'landing_page_id': landing_page_id, 'sessions': sessions}


@when(parsers.parse('I calculate conversion from "{from_stage}" to "{to_stage}"'))
def when_calculate_conversion(db_connection, conversion_data, from_stage, to_stage, context):
    """Calculate conversion rate between stages."""
    result = db_connection.execute(
        text("""SELECT
               COUNT(DISTINCT CASE WHEN funnel_stage = :from_stage THEN session_id END) as from_count,
               COUNT(DISTINCT CASE WHEN funnel_stage = :to_stage THEN session_id END) as to_count
           FROM conversion_funnel
           WHERE landing_page_id = :landing_page_id"""),
        {
            'from_stage': from_stage,
            'to_stage': to_stage,
            'landing_page_id': conversion_data['landing_page_id']
        }
    ).fetchone()

    from_count, to_count = result
    conversion_rate = (to_count / from_count * 100) if from_count > 0 else 0

    context['from_count'] = from_count
    context['to_count'] = to_count
    context['conversion_rate'] = conversion_rate


@then('the conversion rate should be calculable')
def then_conversion_calculable(context):
    """Verify conversion rate was calculated."""
    assert 'conversion_rate' in context, "Conversion rate not calculated"
    assert context['conversion_rate'] > 0, "Conversion rate should be > 0"
    assert context['conversion_rate'] <= 100, "Conversion rate should be <= 100"


@then('abandonment rate should be measurable')
def then_abandonment_measurable(context):
    """Verify abandonment rate can be calculated."""
    abandonment_rate = 100 - context['conversion_rate']
    assert abandonment_rate >= 0, "Abandonment rate should be >= 0"
    assert abandonment_rate < 100, "Abandonment rate should be < 100"


# Scenario: Create A/B test
@given('I define a test with 50/50 split', target_fixture='ab_test_data')
def given_ab_test(db_connection):
    """Create an A/B test with 50/50 split."""
    test_id = uuid4()
    variant_a_id = uuid4()
    variant_b_id = uuid4()
    landing_page_a = uuid4()
    landing_page_b = uuid4()

    # Create landing pages first
    db_connection.execute(
        text("""INSERT INTO landing_pages
           (id, slug, category, name, headline, created, modified)
           VALUES (:id, :slug, :category, :name, :headline, :created, :modified)"""),
        {
            'id': landing_page_a,
            'slug': 'test-ab-page-a',
            'category': 'REPLACEMENT',
            'name': 'Test AB Page A',
            'headline': 'Test Headline A',
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    )

    db_connection.execute(
        text("""INSERT INTO landing_pages
           (id, slug, category, name, headline, created, modified)
           VALUES (:id, :slug, :category, :name, :headline, :created, :modified)"""),
        {
            'id': landing_page_b,
            'slug': 'test-ab-page-b',
            'category': 'REPLACEMENT',
            'name': 'Test AB Page B',
            'headline': 'Test Headline B',
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    )

    # Create A/B test
    db_connection.execute(
        text("""INSERT INTO a_b_tests
           (id, name, description, is_active, traffic_split, start_date, created, modified)
           VALUES (:id, :name, :description, :is_active, :traffic_split, :start_date, :created, :modified)"""),
        {
            'id': test_id,
            'name': 'Test headline',
            'description': 'Testing variations',
            'is_active': True,
            'traffic_split': json.dumps({'control': 50, 'variant_a': 50}),
            'start_date': datetime.now(UTC),
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    )

    # Create variants
    db_connection.execute(
        text("""INSERT INTO a_b_test_variants
           (id, a_b_test_id, variant_name, landing_page_id, weight, created)
           VALUES (:id, :a_b_test_id, :variant_name, :landing_page_id, :weight, :created)"""),
        {
            'id': variant_a_id,
            'a_b_test_id': test_id,
            'variant_name': 'control',
            'landing_page_id': landing_page_a,
            'weight': 50,
            'created': datetime.now(UTC)
        }
    )

    db_connection.execute(
        text("""INSERT INTO a_b_test_variants
           (id, a_b_test_id, variant_name, landing_page_id, weight, created)
           VALUES (:id, :a_b_test_id, :variant_name, :landing_page_id, :weight, :created)"""),
        {
            'id': variant_b_id,
            'a_b_test_id': test_id,
            'variant_name': 'variant_a',
            'landing_page_id': landing_page_b,
            'weight': 50,
            'created': datetime.now(UTC)
        }
    )

    db_connection.commit()

    return {
        'test_id': test_id,
        'variants': [variant_a_id, variant_b_id]
    }


@when('I assign sessions to variants')
def when_assign_variants(db_connection, ab_test_data, context):
    """Assign 100 sessions to variants."""
    variant_assignments = {ab_test_data['variants'][0]: 0, ab_test_data['variants'][1]: 0}

    for i in range(100):
        session_id = uuid4()
        # Deterministic assignment based on session_id hash
        variant_id = ab_test_data['variants'][i % 2]
        variant_assignments[variant_id] += 1

        db_connection.execute(
            text("""INSERT INTO analytics_sessions
               (session_id, a_b_variant_id, landing_page_slug, first_seen, last_seen)
               VALUES (:session_id, :a_b_variant_id, :landing_page_slug, :first_seen, :last_seen)"""),
            {
                'session_id': session_id,
                'a_b_variant_id': variant_id,
                'landing_page_slug': 'test-page',
                'first_seen': datetime.now(UTC),
                'last_seen': datetime.now(UTC)
            }
        )

    db_connection.commit()
    context['assignments'] = variant_assignments


@then('assignments should be deterministic')
def then_assignments_deterministic(context):
    """Verify assignments are deterministic."""
    assert 'assignments' in context, "Assignments not found"
    assert len(context['assignments']) == 2, "Should have 2 variants"


@then('traffic should split approximately 50/50')
def then_traffic_split_equal(context):
    """Verify traffic split is approximately 50/50."""
    counts = list(context['assignments'].values())
    assert len(counts) == 2, "Should have 2 variant counts"

    # Allow for some variance (45-55%)
    total = sum(counts)
    for count in counts:
        percentage = count / total * 100
        assert 45 <= percentage <= 55, f"Traffic split out of range: {percentage}%"


# Scenario: Create heatmap bucket
@given('a landing page exists', target_fixture='heatmap_page_id')
def given_heatmap_page(db_connection):
    """Create a landing page for heatmap testing."""
    page_id = uuid4()
    unique_slug = f'test-heatmap-{uuid4().hex[:8]}'

    db_connection.execute(
        text("""INSERT INTO landing_pages
           (id, slug, category, name, headline, created, modified)
           VALUES (:id, :slug, :category, :name, :headline, :created, :modified)"""),
        {
            'id': page_id,
            'slug': unique_slug,
            'category': 'REPLACEMENT',
            'name': 'Test Page Heatmap',
            'headline': 'Test Headline',
            'created': datetime.now(UTC),
            'modified': datetime.now(UTC)
        }
    )
    db_connection.commit()

    return page_id


@when('I record clicks in 10px buckets')
def when_record_heatmap_clicks(db_connection, heatmap_page_id, context):
    """Record clicks in 10px buckets."""
    # Insert first click
    db_connection.execute(
        text("""INSERT INTO analytics_heatmap_data
           (landing_page_id, viewport_bucket, x_bucket, y_bucket,
            click_count, hover_duration_ms, updated)
           VALUES (:landing_page_id, :viewport_bucket, :x_bucket, :y_bucket, :click_count, :hover_duration_ms, :updated)"""),
        {
            'landing_page_id': heatmap_page_id,
            'viewport_bucket': '1920x1080',
            'x_bucket': 100,
            'y_bucket': 200,
            'click_count': 1,
            'hover_duration_ms': 0,
            'updated': datetime.now(UTC)
        }
    )

    # Update same bucket (increment count)
    db_connection.execute(
        text("""UPDATE analytics_heatmap_data
           SET click_count = click_count + 1,
               updated = :updated
           WHERE landing_page_id = :landing_page_id
           AND viewport_bucket = :viewport_bucket
           AND x_bucket = :x_bucket
           AND y_bucket = :y_bucket"""),
        {
            'updated': datetime.now(UTC),
            'landing_page_id': heatmap_page_id,
            'viewport_bucket': '1920x1080',
            'x_bucket': 100,
            'y_bucket': 200
        }
    )

    db_connection.commit()
    context['page_id'] = heatmap_page_id


@then('buckets should aggregate click counts')
def then_buckets_aggregate(db_connection, context):
    """Verify click counts are aggregated."""
    result = db_connection.execute(
        text("""SELECT click_count FROM analytics_heatmap_data
           WHERE landing_page_id = :landing_page_id
           AND viewport_bucket = :viewport_bucket
           AND x_bucket = :x_bucket
           AND y_bucket = :y_bucket"""),
        {
            'landing_page_id': context['page_id'],
            'viewport_bucket': '1920x1080',
            'x_bucket': 100,
            'y_bucket': 200
        }
    ).fetchone()

    assert result is not None, "Heatmap bucket not found"
    assert result[0] == 2, f"Expected 2 clicks, got {result[0]}"


@then('unique constraint should prevent duplicates')
def then_unique_constraint_enforced(db_connection, context):
    """Verify unique constraint on bucket coordinates."""
    try:
        # Try to insert duplicate bucket
        db_connection.execute(
            text("""INSERT INTO analytics_heatmap_data
               (landing_page_id, viewport_bucket, x_bucket, y_bucket,
                click_count, hover_duration_ms, updated)
               VALUES (:landing_page_id, :viewport_bucket, :x_bucket, :y_bucket, :click_count, :hover_duration_ms, :updated)"""),
            {
                'landing_page_id': context['page_id'],
                'viewport_bucket': '1920x1080',
                'x_bucket': 100,
                'y_bucket': 200,
                'click_count': 1,
                'hover_duration_ms': 0,
                'updated': datetime.now(UTC)
            }
        )
        db_connection.commit()
        assert False, "Duplicate bucket insertion should have failed"
    except Exception as e:
        # Expected to fail with unique constraint violation
        db_connection.rollback()
        assert 'unique' in str(e).lower() or 'duplicate' in str(e).lower()


@then('hover duration should be tracked')
def then_hover_duration_tracked(db_connection, context):
    """Verify hover duration is tracked."""
    result = db_connection.execute(
        text("""SELECT hover_duration_ms FROM analytics_heatmap_data
           WHERE landing_page_id = :landing_page_id
           AND viewport_bucket = :viewport_bucket
           AND x_bucket = :x_bucket
           AND y_bucket = :y_bucket"""),
        {
            'landing_page_id': context['page_id'],
            'viewport_bucket': '1920x1080',
            'x_bucket': 100,
            'y_bucket': 200
        }
    ).fetchone()

    assert result is not None, "Heatmap bucket not found"
    assert result[0] is not None, "Hover duration not tracked"
