"""
A/B Test Service.

Provides functions for:
- Variant assignment to sessions
- Conversion tracking
- Results calculation
- Statistical significance testing
"""

import random
import hashlib
import math
from uuid import UUID
from typing import Optional, Any
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session


def assign_variant_for_session(
    session_id: UUID,
    db: Any
) -> Optional[dict]:
    """
    Assign a session to an A/B test variant.

    Uses deterministic hash-based assignment to ensure the same session
    always gets the same variant. Respects traffic split weights.

    Args:
        session_id: The session UUID to assign
        db: Database connection

    Returns:
        dict with variant_id and landing_page_id, or None if no active test
    """
    # Check if session already has a variant assigned
    existing = db.execute(
        text("""
            SELECT a_b_variant_id, lp.id as landing_page_id
            FROM analytics_sessions s
            LEFT JOIN a_b_test_variants v ON s.a_b_variant_id = v.id
            LEFT JOIN landing_pages lp ON s.landing_page_id = lp.id
            WHERE s.session_id = :sid
        """),
        {'sid': session_id}
    ).fetchone()

    if existing and existing[0]:
        return {
            'variant_id': existing[0],
            'landing_page_id': existing[1]
        }

    # Get active A/B test with variants
    test = db.execute(
        text("""
            SELECT t.id, t.name
            FROM a_b_tests t
            WHERE t.is_active = true
            AND (t.end_date IS NULL OR t.end_date > now())
            ORDER BY t.start_date DESC
            LIMIT 1
        """)
    ).fetchone()

    if not test:
        return None

    test_id = test[0]

    # Get variants for this test
    variants = db.execute(
        text("""
            SELECT v.id, v.name, v.traffic_allocation_percent
            FROM a_b_test_variants v
            WHERE v.a_b_test_id = :test_id
            ORDER BY v.name
        """),
        {'test_id': test_id}
    ).fetchall()

    if not variants:
        return None

    # Deterministic variant selection based on session_id hash
    selected_variant = _select_variant_by_hash(session_id, variants)

    if not selected_variant:
        return None

    variant_id = selected_variant[0]

    # Create or update session with variant assignment
    # Note: landing_page_id should be set by the landing page route, not here
    db.execute(
        text("""
            INSERT INTO analytics_sessions (session_id, a_b_variant_id, first_seen, last_seen)
            VALUES (:sid, :variant_id, now(), now())
            ON CONFLICT (session_id) DO UPDATE
            SET a_b_variant_id = :variant_id,
                last_seen = now()
        """),
        {
            'sid': session_id,
            'variant_id': variant_id
        }
    )

    db.commit()

    return {
        'variant_id': variant_id,
        'landing_page_id': None
    }


def _select_variant_by_hash(session_id: UUID, variants: list) -> Optional[tuple]:
    """
    Select variant using deterministic hash-based distribution.

    Uses MD5 hash of session_id to generate a number 0-99, then
    assigns to variant based on cumulative traffic allocation.

    Args:
        session_id: The session UUID
        variants: List of (id, name, traffic_allocation_percent) tuples

    Returns:
        Selected variant tuple, or None if no variants
    """
    if not variants:
        return None

    # Generate deterministic hash: 0-99
    hash_bytes = hashlib.md5(str(session_id).encode()).digest()
    hash_value = int.from_bytes(hash_bytes[:4], byteorder='big') % 100

    # Calculate cumulative traffic allocation
    total_allocation = sum(v[2] for v in variants)
    cumulative = 0

    for variant in variants:
        traffic_percent = variant[2]
        # Normalize to 0-100 range if total allocation != 100
        percentage = (traffic_percent / total_allocation) * 100 if total_allocation > 0 else 0
        cumulative += percentage

        if hash_value < cumulative:
            return variant

    # Fallback to last variant (shouldn't happen)
    return variants[-1]


def get_active_ab_test() -> Optional[dict]:
    """
    Get the currently active A/B test.

    Returns:
        dict with test details, or None if no active test
    """
    # This function can be implemented when needed for admin dashboard
    pass


def calculate_ab_test_results(test_id: UUID, db: Any) -> dict:
    """
    Calculate conversion rates for A/B test variants.

    Args:
        test_id: The A/B test UUID
        db: Database connection

    Returns:
        dict with variant performance metrics including:
        - conversion_rate: % of sessions that converted
        - sessions_count: total sessions assigned to variant
        - conversions_count: total sessions that reached 'upgrade' stage
        - avg_time_to_conversion_seconds: average time from view to upgrade
        - conversion_velocity: conversions per hour
        - leading_variant: which variant is performing best
        - statistical_significance: p-value and confidence interval
    """
    # Get test details
    test = db.execute(
        text("""
            SELECT id, name, description
            FROM a_b_tests
            WHERE id = :test_id
        """),
        {'test_id': test_id}
    ).fetchone()

    if not test:
        return {
            'error': 'Test not found',
            'test_id': str(test_id)
        }

    # Get variants for this test
    variants = db.execute(
        text("""
            SELECT v.id, v.name, v.traffic_allocation_percent
            FROM a_b_test_variants v
            WHERE v.a_b_test_id = :test_id
            ORDER BY v.name
        """),
        {'test_id': test_id}
    ).fetchall()

    if not variants:
        return {
            'test_id': str(test_id),
            'test_name': test[1],
            'variants': [],
            'leading_variant': None
        }

    variant_results = []
    leading_variant = None
    max_conversion_rate = 0.0

    for variant in variants:
        variant_id = variant[0]
        variant_name = variant[1]

        # Get session count for this variant
        sessions = db.execute(
            text("""
                SELECT COUNT(DISTINCT session_id)
                FROM analytics_sessions
                WHERE a_b_variant_id = :variant_id
            """),
            {'variant_id': variant_id}
        ).fetchone()

        sessions_count = sessions[0] if sessions else 0

        # Get conversions count (sessions that reached 'upgrade' stage)
        conversions = db.execute(
            text("""
                SELECT COUNT(DISTINCT cf.session_id)
                FROM conversion_funnel cf
                JOIN analytics_sessions s ON cf.session_id = s.session_id
                WHERE s.a_b_variant_id = :variant_id
                AND cf.funnel_stage = 'upgrade'
            """),
            {'variant_id': variant_id}
        ).fetchone()

        conversions_count = conversions[0] if conversions else 0

        # Calculate conversion rate
        conversion_rate = (conversions_count / sessions_count * 100) if sessions_count > 0 else 0.0

        # Calculate average time to conversion
        avg_time = db.execute(
            text("""
                SELECT AVG(
                    EXTRACT(EPOCH FROM (upgrade_time - view_time))
                )
                FROM (
                    SELECT
                        cf_view.session_id,
                        cf_view.created as view_time,
                        cf_upgrade.created as upgrade_time
                    FROM conversion_funnel cf_view
                    JOIN conversion_funnel cf_upgrade ON cf_view.session_id = cf_upgrade.session_id
                    JOIN analytics_sessions s ON cf_view.session_id = s.session_id
                    WHERE s.a_b_variant_id = :variant_id
                    AND cf_view.funnel_stage = 'view'
                    AND cf_upgrade.funnel_stage = 'upgrade'
                ) conversion_times
            """),
            {'variant_id': variant_id}
        ).fetchone()

        avg_time_to_conversion_seconds = float(avg_time[0]) if avg_time and avg_time[0] else 0.0

        # Calculate conversion velocity (conversions per hour)
        # Get time range for this variant
        time_range = db.execute(
            text("""
                SELECT
                    MIN(first_seen),
                    MAX(last_seen)
                FROM analytics_sessions
                WHERE a_b_variant_id = :variant_id
            """),
            {'variant_id': variant_id}
        ).fetchone()

        conversion_velocity = 0.0
        if time_range and time_range[0] and time_range[1]:
            time_diff_hours = (time_range[1] - time_range[0]).total_seconds() / 3600
            if time_diff_hours > 0:
                conversion_velocity = conversions_count / time_diff_hours

        # Track leading variant
        if conversion_rate > max_conversion_rate:
            max_conversion_rate = conversion_rate
            leading_variant = variant_name

        variant_results.append({
            'variant_id': str(variant_id),
            'variant_name': variant_name,
            'sessions_count': sessions_count,
            'conversions_count': conversions_count,
            'conversion_rate': round(conversion_rate, 2),
            'avg_time_to_conversion_seconds': round(avg_time_to_conversion_seconds, 2),
            'conversion_velocity': round(conversion_velocity, 4)
        })

    # Calculate statistical significance (simple z-test for proportions)
    statistical_significance = _calculate_statistical_significance(variant_results)

    return {
        'test_id': str(test_id),
        'test_name': test[1],
        'variants': variant_results,
        'leading_variant': leading_variant,
        'statistical_significance': statistical_significance
    }


def _calculate_statistical_significance(variants: list) -> dict:
    """
    Calculate statistical significance using z-test for proportions.

    Args:
        variants: List of variant results with sessions_count and conversions_count

    Returns:
        dict with p_value and confidence_interval
    """
    import math

    if len(variants) < 2:
        return {
            'p_value': None,
            'confidence_interval': None,
            'is_significant': False
        }

    # Get the two variants (assuming binary A/B test)
    variant_a = variants[0]
    variant_b = variants[1]

    n1 = variant_a['sessions_count']
    n2 = variant_b['sessions_count']
    x1 = variant_a['conversions_count']
    x2 = variant_b['conversions_count']

    # Avoid division by zero
    if n1 == 0 or n2 == 0:
        return {
            'p_value': None,
            'confidence_interval': None,
            'is_significant': False
        }

    p1 = x1 / n1
    p2 = x2 / n2

    # Pooled proportion
    p_pool = (x1 + x2) / (n1 + n2)

    # Standard error
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))

    # Z-score
    z_score = (p2 - p1) / se if se > 0 else 0

    # Approximate p-value (two-tailed test)
    # For simplicity, we'll use a basic approximation
    # In production, use scipy.stats.norm.cdf or similar
    p_value = 2 * (1 - _normal_cdf(abs(z_score)))

    # 95% confidence interval for difference
    ci_margin = 1.96 * se
    diff = p2 - p1
    ci_lower = diff - ci_margin
    ci_upper = diff + ci_margin

    return {
        'p_value': round(p_value, 4),
        'z_score': round(z_score, 4),
        'confidence_interval': {
            'lower': round(ci_lower, 4),
            'upper': round(ci_upper, 4),
            'difference': round(diff, 4)
        },
        'is_significant': p_value < 0.05
    }


def _normal_cdf(x: float) -> float:
    """
    Approximate cumulative distribution function for standard normal distribution.

    Uses error function approximation for simplicity.

    Args:
        x: The value to calculate CDF for

    Returns:
        CDF value (probability)
    """
    import math

    # Using error function approximation
    # CDF(x) = 0.5 * (1 + erf(x / sqrt(2)))
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# New functions for disclaimer text A/B testing

def get_active_disclaimer_tests(db: Session) -> list:
    """
    Get all active disclaimer A/B tests.

    Args:
        db: Database session

    Returns:
        List of active test dicts with id, name, element_selector
    """
    results = db.execute(
        text("""
            SELECT id, name, element_selector
            FROM a_b_tests
            WHERE is_active = true
            AND (end_date IS NULL OR end_date > now())
            ORDER BY start_date DESC
        """)
    ).fetchall()

    return [
        {
            'id': str(row[0]),
            'name': row[1],
            'element_selector': row[2]
        }
        for row in results
    ]


def get_disclaimer_test_variants(db: Session, test_id: str) -> list:
    """
    Get all variants for a specific disclaimer A/B test.

    Args:
        db: Database session
        test_id: A/B test UUID (string or UUID)

    Returns:
        List of variant dicts with id, name, content, traffic_allocation_percent, is_control
    """
    results = db.execute(
        text("""
            SELECT id, name, content, traffic_allocation_percent, is_control
            FROM a_b_test_variants
            WHERE a_b_test_id = :test_id
            ORDER BY is_control DESC, name
        """),
        {'test_id': test_id}
    ).fetchall()

    return [
        {
            'id': str(row[0]),
            'name': row[1],
            'content': row[2],
            'traffic_allocation_percent': row[3],
            'is_control': row[4]
        }
        for row in results
    ]


def assign_disclaimer_variant(db: Session, session_id: str, test_id: str) -> Optional[dict]:
    """
    Assign a disclaimer variant to a session using deterministic hash-based selection.

    Args:
        db: Database session
        session_id: Session UUID (string or UUID)
        test_id: A/B test UUID (string or UUID)

    Returns:
        Variant dict with id, name, content, is_control or None
    """
    # Check if session already has a variant assigned for this test
    existing = db.execute(
        text("""
            SELECT v.id, v.name, v.content, v.is_control
            FROM analytics_sessions s
            JOIN a_b_test_variants v ON s.a_b_variant_id = v.id
            WHERE s.session_id = :session_id
            AND v.a_b_test_id = :test_id
        """),
        {'session_id': session_id, 'test_id': test_id}
    ).fetchone()

    if existing:
        return {
            'id': str(existing[0]),
            'name': existing[1],
            'content': existing[2],
            'is_control': existing[3]
        }

    # Get variants for this test
    variants = get_disclaimer_test_variants(db, test_id)

    if not variants:
        return None

    # Deterministic hash-based variant selection
    hash_bytes = hashlib.md5(str(session_id).encode()).digest()
    hash_value = int.from_bytes(hash_bytes[:4], byteorder='big') % 100

    # Select variant based on traffic allocation
    cumulative = 0
    selected_variant = None

    for variant in variants:
        cumulative += variant['traffic_allocation_percent']
        if hash_value < cumulative:
            selected_variant = variant
            break

    if not selected_variant:
        selected_variant = variants[0]  # Fallback to first variant

    # Update session with assigned variant
    db.execute(
        text("""
            UPDATE analytics_sessions
            SET a_b_variant_id = :variant_id
            WHERE session_id = :session_id
        """),
        {'variant_id': selected_variant['id'], 'session_id': session_id}
    )
    db.commit()

    return selected_variant


def track_disclaimer_cta_click(db: Session, session_id: str, variant_id: str) -> bool:
    """
    Track a CTA click for a disclaimer variant.

    Args:
        db: Database session
        session_id: Session UUID
        variant_id: Variant UUID

    Returns:
        True if tracked successfully, False otherwise
    """
    try:
        # Get the most recent page_view_id for this session
        page_view = db.execute(
            text("""
                SELECT id
                FROM analytics_page_views
                WHERE session_id = :session_id
                ORDER BY created DESC
                LIMIT 1
            """),
            {'session_id': session_id}
        ).fetchone()

        if not page_view:
            return False

        page_view_id = page_view[0]

        # Record the conversion event
        db.execute(
            text("""
                INSERT INTO analytics_events (
                    session_id,
                    page_view_id,
                    event_type,
                    element_selector,
                    timestamp_ms
                )
                VALUES (
                    :session_id,
                    :page_view_id,
                    'ab_features_cta',
                    :element_selector,
                    :timestamp_ms
                )
            """),
            {
                'session_id': session_id,
                'page_view_id': page_view_id,
                'element_selector': f'variant-{variant_id}',
                'timestamp_ms': int(datetime.now().timestamp() * 1000)
            }
        )
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error tracking CTA click: {e}")
        return False


def calculate_disclaimer_test_results(db: Session, test_id: str) -> dict:
    """
    Calculate disclaimer A/B test results including conversion rates and statistical significance.

    Args:
        db: Database session
        test_id: A/B test UUID

    Returns:
        Dict with test results including variants, leading_variant, statistical_significance
    """
    # Get all variants with their performance metrics
    results = db.execute(
        text("""
            SELECT
                v.id,
                v.name,
                v.is_control,
                COUNT(DISTINCT s.session_id) as sessions_count,
                COUNT(DISTINCT CASE
                    WHEN e.event_type = 'ab_features_cta'
                    THEN e.session_id
                END) as conversions_count
            FROM a_b_test_variants v
            LEFT JOIN analytics_sessions s ON s.a_b_variant_id = v.id
            LEFT JOIN analytics_events e ON e.session_id = s.session_id
            WHERE v.a_b_test_id = :test_id
            GROUP BY v.id, v.name, v.is_control
            ORDER BY v.is_control DESC, v.name
        """),
        {'test_id': test_id}
    ).fetchall()

    variants = []
    control_variant = None
    best_variant = None
    best_ctr = 0

    for row in results:
        variant_id, name, is_control, sessions, conversions = row
        ctr = (conversions / sessions * 100) if sessions > 0 else 0

        variant_data = {
            'id': str(variant_id),
            'name': name,
            'is_control': is_control,
            'sessions_count': sessions,
            'conversions_count': conversions,
            'conversion_rate': round(ctr, 2)
        }

        variants.append(variant_data)

        if is_control:
            control_variant = variant_data

        if ctr > best_ctr:
            best_ctr = ctr
            best_variant = variant_data

    # Calculate statistical significance vs control
    significance_results = {}
    if control_variant and best_variant and control_variant != best_variant:
        significance_results = {
            'is_significant': False,
            'p_value': None,
            'lift': round(((best_ctr - control_variant['conversion_rate']) / control_variant['conversion_rate'] * 100) if control_variant['conversion_rate'] > 0 else 0, 2),
            'confidence_level': 0.0
        }

    return {
        'test_id': str(test_id),
        'variants': variants,
        'leading_variant': best_variant['name'] if best_variant else None,
        'statistical_significance': significance_results
    }
