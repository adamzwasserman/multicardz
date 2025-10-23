"""
A/B Test Service.

Provides functions for:
- Assigning sessions to A/B test variants
- Deterministic variant selection based on session ID
- Respecting traffic split weights
"""

import hashlib
from uuid import UUID
from typing import Optional, Any
from sqlalchemy import text


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
            LEFT JOIN landing_pages lp ON v.landing_page_id = lp.id
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
            SELECT v.id, v.variant_name, v.landing_page_id, v.weight
            FROM a_b_test_variants v
            WHERE v.a_b_test_id = :test_id
            ORDER BY v.variant_name
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
    landing_page_id = selected_variant[2]

    # Create or update session with variant assignment
    db.execute(
        text("""
            INSERT INTO analytics_sessions (session_id, a_b_variant_id, landing_page_id, first_seen, last_seen)
            VALUES (:sid, :variant_id, :page_id, now(), now())
            ON CONFLICT (session_id) DO UPDATE
            SET a_b_variant_id = :variant_id,
                landing_page_id = :page_id,
                last_seen = now()
        """),
        {
            'sid': session_id,
            'variant_id': variant_id,
            'page_id': landing_page_id
        }
    )

    db.commit()

    return {
        'variant_id': variant_id,
        'landing_page_id': landing_page_id
    }


def _select_variant_by_hash(session_id: UUID, variants: list) -> Optional[tuple]:
    """
    Select variant using deterministic hash-based distribution.

    Uses MD5 hash of session_id to generate a number 0-99, then
    assigns to variant based on cumulative weight ranges.

    Args:
        session_id: The session UUID
        variants: List of (id, name, landing_page_id, weight) tuples

    Returns:
        Selected variant tuple, or None if no variants
    """
    if not variants:
        return None

    # Generate deterministic hash: 0-99
    hash_bytes = hashlib.md5(str(session_id).encode()).digest()
    hash_value = int.from_bytes(hash_bytes[:4], byteorder='big') % 100

    # Calculate cumulative weights
    total_weight = sum(v[3] for v in variants)
    cumulative = 0

    for variant in variants:
        weight = variant[3]
        # Convert weight to percentage of total
        percentage = (weight / total_weight) * 100
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
        dict with variant performance metrics
    """
    # This function will be implemented in Phase 7
    pass
