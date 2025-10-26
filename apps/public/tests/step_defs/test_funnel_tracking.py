"""
Step definitions for funnel tracking BDD tests.
"""

from pytest_bdd import scenarios, given, when, then, parsers
import pytest

# Load scenarios from feature file
scenarios('../features/funnel_tracking.feature')


# ============================================================================
# GIVEN steps
# ============================================================================

@given('the database is empty')
def empty_database(db_session):
    """Database is cleaned before each test."""
    # Clean up conversion_funnel and analytics_sessions
    from sqlalchemy import text
    db_session.execute(text("TRUNCATE TABLE conversion_funnel CASCADE"))
    db_session.execute(text("TRUNCATE TABLE analytics_sessions CASCADE"))
    db_session.execute(text("TRUNCATE TABLE landing_pages CASCADE"))
    db_session.commit()


@given('I have a test landing page')
def have_landing_page(test_landing_page):
    """Landing page fixture is available."""
    pass


@given('I have analytics sessions with funnel stages')
def have_sessions_with_funnel(analytics_sessions_with_funnel, context):
    """Store sessions in context."""
    context['sessions'] = analytics_sessions_with_funnel


@given(parsers.parse('a user "{user_id}" has progressed through multiple stages'))
def user_completed_funnel(user_with_complete_funnel, context, user_id):
    """User with complete funnel progression."""
    assert user_with_complete_funnel['user_id'] == user_id
    context['complete_user'] = user_with_complete_funnel


@given(parsers.parse('I have {count:d} sessions at landing stage'))
def sessions_at_landing(funnel_sessions_by_count, context, count):
    """Sessions at landing stage."""
    assert funnel_sessions_by_count['landing'] == count
    context['funnel_counts'] = funnel_sessions_by_count


@given(parsers.parse('{count:d} sessions progressed to signup'))
def sessions_at_signup(context, count):
    """Sessions at signup stage."""
    assert context['funnel_counts']['signup'] == count


@given(parsers.parse('{count:d} sessions progressed to first_card'))
def sessions_at_first_card(context, count):
    """Sessions at first card stage."""
    assert context['funnel_counts']['first_card'] == count


@given(parsers.parse('{count:d} sessions progressed to upgrade'))
def sessions_at_upgrade(context, count):
    """Sessions at upgrade stage."""
    assert context['funnel_counts']['upgrade'] == count


@given('users have various completion times between stages')
def users_with_various_times(analytics_sessions_with_funnel, context):
    """Sessions with various completion times."""
    context['sessions'] = analytics_sessions_with_funnel


@given('I have funnel data for the past 30 days')
def funnel_cohort_data_exists(funnel_cohort_data, context):
    """Cohort data fixture."""
    context['cohort_data'] = funnel_cohort_data


@given('I have multiple landing pages')
def multiple_landing_pages(multiple_landing_pages_funnel, context):
    """Multiple landing pages with different conversion rates."""
    context['landing_pages'] = multiple_landing_pages_funnel


@given('each page has different conversion rates')
def pages_have_different_rates(context):
    """Pages have different conversion rates (verified by fixture)."""
    assert len(context['landing_pages']) > 1


# ============================================================================
# WHEN steps
# ============================================================================

@when('I request overall funnel metrics')
def request_overall_metrics(db_session, context):
    """Request overall funnel metrics."""
    from services.funnel_service import get_overall_funnel_metrics
    context['funnel_metrics'] = get_overall_funnel_metrics(db_session)


@when(parsers.parse('I request funnel progression for user "{user_id}"'))
def request_user_progression(db_session, context, user_id):
    """Request funnel progression for specific user."""
    from services.funnel_service import get_user_funnel_progression
    context['user_progression'] = get_user_funnel_progression(db_session, user_id)


@when('I request funnel drop-off analysis')
def request_dropoff_analysis(db_session, context):
    """Request funnel drop-off analysis."""
    from services.funnel_service import get_funnel_dropoff_analysis
    context['dropoff_analysis'] = get_funnel_dropoff_analysis(db_session)


@when('I request average funnel stage durations')
def request_stage_durations(db_session, context):
    """Request average durations between stages."""
    from services.funnel_service import get_average_stage_durations
    context['stage_durations'] = get_average_stage_durations(db_session)


@when(parsers.parse('I request funnel cohort analysis for "{cohort_date}"'))
def request_cohort_analysis(db_session, context, cohort_date):
    """Request cohort analysis for specific date."""
    from services.funnel_service import get_funnel_cohort_analysis
    context['cohort_analysis'] = get_funnel_cohort_analysis(db_session, cohort_date)


@when('I request funnel performance by landing page')
def request_page_performance(db_session, context):
    """Request funnel performance by landing page."""
    from services.funnel_service import get_funnel_by_landing_page
    context['page_performance'] = get_funnel_by_landing_page(db_session)


# ============================================================================
# THEN steps
# ============================================================================

@then('I should see funnel stage counts')
def verify_stage_counts(context):
    """Verify funnel metrics contain stage counts."""
    metrics = context['funnel_metrics']
    assert 'stages' in metrics
    assert 'landing' in metrics['stages']
    assert 'signup' in metrics['stages']
    assert 'first_card' in metrics['stages']
    assert 'upgrade' in metrics['stages']
    assert metrics['stages']['landing'] > 0


@then('I should see conversion rates between stages')
def verify_conversion_rates(context):
    """Verify conversion rates are calculated."""
    metrics = context['funnel_metrics']
    assert 'conversion_rates' in metrics
    assert 'landing_to_signup' in metrics['conversion_rates']
    assert 'signup_to_first_card' in metrics['conversion_rates']
    assert 'first_card_to_upgrade' in metrics['conversion_rates']


@then('I should see total funnel duration statistics')
def verify_duration_stats(context):
    """Verify duration statistics are included."""
    metrics = context['funnel_metrics']
    assert 'average_durations' in metrics or 'duration_stats' in metrics


@then('I should see all stages the user completed')
def verify_user_stages(context):
    """Verify all user stages are returned."""
    progression = context['user_progression']
    assert 'stages' in progression
    assert len(progression['stages']) == 4  # landing, signup, first_card, upgrade
    stage_names = [s['stage'] for s in progression['stages']]
    assert 'landing' in stage_names
    assert 'signup' in stage_names
    assert 'first_card' in stage_names
    assert 'upgrade' in stage_names


@then('I should see timestamps for each stage')
def verify_stage_timestamps(context):
    """Verify each stage has a timestamp."""
    progression = context['user_progression']
    for stage in progression['stages']:
        assert 'timestamp' in stage or 'created' in stage
        assert stage.get('timestamp') or stage.get('created')


@then('I should see time between stages')
def verify_time_between_stages(context):
    """Verify time differences between stages."""
    progression = context['user_progression']
    assert 'stage_durations' in progression or 'time_between_stages' in progression


@then(parsers.re(r'I should see (?P<dropoff>[\d.]+)% drop-off between landing and signup'))
def verify_landing_signup_dropoff(context, dropoff):
    """Verify drop-off percentage between landing and signup."""
    analysis = context['dropoff_analysis']
    assert 'landing_to_signup' in analysis
    # Allow for small floating point differences and rounding
    assert abs(analysis['landing_to_signup']['dropoff_rate'] - float(dropoff)) < 1.5


@then(parsers.re(r'I should see (?P<dropoff>[\d.]+)% drop-off between signup and first_card'))
def verify_signup_firstcard_dropoff(context, dropoff):
    """Verify drop-off percentage between signup and first_card."""
    analysis = context['dropoff_analysis']
    assert 'signup_to_first_card' in analysis
    # Allow for rounding differences (expecting ~33% but may get 34%)
    assert abs(analysis['signup_to_first_card']['dropoff_rate'] - float(dropoff)) < 1.5


@then(parsers.re(r'I should see (?P<dropoff>[\d.]+)% drop-off between first_card and upgrade'))
def verify_firstcard_upgrade_dropoff(context, dropoff):
    """Verify drop-off percentage between first_card and upgrade."""
    analysis = context['dropoff_analysis']
    assert 'first_card_to_upgrade' in analysis
    # Allow for rounding differences
    assert abs(analysis['first_card_to_upgrade']['dropoff_rate'] - float(dropoff)) < 1.5


@then('I should see average time from landing to signup')
def verify_landing_signup_duration(context):
    """Verify average duration from landing to signup."""
    durations = context['stage_durations']
    assert 'landing_to_signup' in durations
    assert durations['landing_to_signup']['avg_seconds'] > 0


@then('I should see average time from signup to first_card')
def verify_signup_firstcard_duration(context):
    """Verify average duration from signup to first_card."""
    durations = context['stage_durations']
    assert 'signup_to_first_card' in durations
    assert durations['signup_to_first_card']['avg_seconds'] > 0


@then('I should see average time from first_card to upgrade')
def verify_firstcard_upgrade_duration(context):
    """Verify average duration from first_card to upgrade."""
    durations = context['stage_durations']
    assert 'first_card_to_upgrade' in durations
    assert durations['first_card_to_upgrade']['avg_seconds'] > 0


@then('I should see signup conversions for that cohort')
def verify_cohort_signups(context):
    """Verify cohort signup conversions."""
    analysis = context['cohort_analysis']
    assert 'signup_conversion_rate' in analysis
    assert analysis['signup_conversion_rate'] > 0


@then('I should see retention to first_card for that cohort')
def verify_cohort_first_card(context):
    """Verify cohort first_card retention."""
    analysis = context['cohort_analysis']
    assert 'first_card_conversion_rate' in analysis
    assert analysis['first_card_conversion_rate'] > 0


@then('I should see upgrade conversions for that cohort')
def verify_cohort_upgrades(context):
    """Verify cohort upgrade conversions."""
    analysis = context['cohort_analysis']
    assert 'upgrade_conversion_rate' in analysis
    assert analysis['upgrade_conversion_rate'] >= 0


@then('I should see conversion rates for each page')
def verify_page_conversion_rates(context):
    """Verify each page has conversion rates."""
    performance = context['page_performance']
    assert len(performance) > 0
    for page in performance:
        assert 'landing_page_id' in page or 'page_slug' in page
        assert 'conversion_rate' in page
        assert page['conversion_rate'] >= 0


@then('pages should be ranked by conversion performance')
def verify_pages_ranked(context):
    """Verify pages are sorted by conversion rate."""
    performance = context['page_performance']
    conversion_rates = [p['conversion_rate'] for p in performance]
    # Check if sorted in descending order
    assert conversion_rates == sorted(conversion_rates, reverse=True)
