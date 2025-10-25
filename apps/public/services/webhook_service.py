"""
Auth0 and Stripe webhook integration service.

Handles user signup webhooks from Auth0 and subscription webhooks from Stripe.
Links analytics sessions to user accounts when they sign up.
"""

from uuid import uuid4, UUID
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)


def process_auth0_signup(
    db: Session,
    user_id: str,
    anonymous_user_id: str,
    browser_fingerprint: Optional[str] = None,
    email: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process Auth0 signup webhook.

    Links ALL analytics sessions with the anonymous_user_id to the real user_id.
    This allows complete tracking from first visit → signup → paid conversion.

    Args:
        db: Database session
        user_id: Auth0 user ID (e.g., "auth0|user123")
        anonymous_user_id: Persistent anonymous user ID from cookie
        browser_fingerprint: Browser fingerprint from session (legacy, optional)
        email: User email address
        metadata: Additional metadata from Auth0

    Returns:
        dict with 'sessions_updated', 'funnel_created', 'user_id'
    """
    sessions_updated = 0
    session_ids = []

    # Find ALL sessions with this anonymous user ID
    # This is the magic that links the entire journey!
    results = db.execute(text("""
        SELECT session_id, first_seen
        FROM analytics_sessions
        WHERE user_id = :anonymous_user_id
        ORDER BY first_seen ASC
    """), {'anonymous_user_id': anonymous_user_id}).fetchall()

    if results:
        # Update ALL sessions from anonymous to real user ID
        db.execute(text("""
            UPDATE analytics_sessions
            SET user_id = :user_id, last_seen = :now
            WHERE user_id = :anonymous_user_id
        """), {
            'user_id': user_id,
            'anonymous_user_id': anonymous_user_id,
            'now': datetime.now(timezone.utc)
        })

        sessions_updated = len(results)
        session_ids = [str(row[0]) for row in results]
        first_session_id = session_ids[0] if session_ids else None

        logger.info(f"Linked {sessions_updated} sessions from anonymous user {anonymous_user_id} to {user_id}")
    else:
        # Fallback to browser fingerprint if provided (legacy)
        if browser_fingerprint:
            result = db.execute(text("""
                SELECT session_id
                FROM analytics_sessions
                WHERE browser_fingerprint = :fingerprint
                LIMIT 1
            """), {'fingerprint': browser_fingerprint}).fetchone()

            if result:
                first_session_id = result[0]
                db.execute(text("""
                    UPDATE analytics_sessions
                    SET user_id = :user_id, last_seen = :now
                    WHERE session_id = :session_id
                """), {
                    'user_id': user_id,
                    'session_id': first_session_id,
                    'now': datetime.now(timezone.utc)
                })
                sessions_updated = 1
                session_ids = [str(first_session_id)]
                logger.info(f"Linked session {first_session_id} to user {user_id} via fingerprint")
            else:
                logger.warning(f"No sessions found for anonymous_user_id {anonymous_user_id} or fingerprint {browser_fingerprint}")
                first_session_id = None
        else:
            logger.warning(f"No sessions found for anonymous_user_id {anonymous_user_id}")
            first_session_id = None

    # Create conversion funnel record
    import json as json_module
    funnel_data = {
        'email': email,
        'auth0_metadata': metadata or {},
        'sessions_linked': sessions_updated,
        'session_ids': session_ids
    }

    db.execute(text("""
        INSERT INTO conversion_funnel
        (id, session_id, user_id, funnel_stage, data, created)
        VALUES (:id, :session_id, :user_id, :stage, CAST(:data AS jsonb), :created)
    """), {
        'id': uuid4(),
        'session_id': first_session_id,  # Use first session for attribution
        'user_id': user_id,
        'stage': 'signup',
        'data': json_module.dumps(funnel_data),
        'created': datetime.now(timezone.utc)
    })

    db.commit()

    logger.info(f"Created signup funnel record for user {user_id} (linked {sessions_updated} sessions)")

    return {
        'sessions_updated': sessions_updated,
        'funnel_created': True,
        'session_ids': session_ids,
        'first_session_id': str(first_session_id) if first_session_id else None,
        'user_id': user_id
    }


def process_auth0_signup_batch(
    db: Session,
    signups: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process batch of Auth0 signup webhooks.

    Args:
        db: Database session
        signups: List of signup dicts with user_id, browser_fingerprint, email

    Returns:
        dict with 'processed', 'sessions_updated', 'funnels_created'
    """
    processed = 0
    sessions_updated = 0
    funnels_created = 0

    for signup in signups:
        result = process_auth0_signup(
            db=db,
            user_id=signup['user_id'],
            browser_fingerprint=signup['browser_fingerprint'],
            email=signup.get('email', ''),
            metadata=signup.get('metadata')
        )

        processed += 1
        if result['session_updated']:
            sessions_updated += 1
        if result['funnel_created']:
            funnels_created += 1

    logger.info(f"Batch processed {processed} signups: {sessions_updated} sessions updated, {funnels_created} funnels created")

    return {
        'processed': processed,
        'sessions_updated': sessions_updated,
        'funnels_created': funnels_created
    }


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """
    Verify HMAC webhook signature.

    Args:
        payload: Raw request body bytes
        signature: Signature from webhook header
        secret: Shared webhook secret

    Returns:
        True if signature is valid, False otherwise
    """
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def process_stripe_subscription(
    db: Session,
    user_id: str,
    subscription_id: str,
    plan: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process Stripe subscription webhook.

    Creates upgrade funnel record when user subscribes.

    Args:
        db: Database session
        user_id: User ID
        subscription_id: Stripe subscription ID
        plan: Subscription plan name
        status: Subscription status (active, canceled, etc.)
        metadata: Additional Stripe metadata

    Returns:
        dict with 'funnel_created', 'user_id', 'subscription_id'
    """
    # Find session by user_id
    result = db.execute(text("""
        SELECT session_id
        FROM analytics_sessions
        WHERE user_id = :user_id
        ORDER BY last_seen DESC
        LIMIT 1
    """), {'user_id': user_id}).fetchone()

    session_id = result[0] if result else None

    # Create conversion funnel record for upgrade
    import json as json_module
    funnel_data = {
        'subscription_id': subscription_id,
        'plan': plan,
        'status': status,
        'stripe_metadata': metadata or {}
    }

    db.execute(text("""
        INSERT INTO conversion_funnel
        (id, session_id, user_id, funnel_stage, data, created)
        VALUES (:id, :session_id, :user_id, :stage, CAST(:data AS jsonb), :created)
    """), {
        'id': uuid4(),
        'session_id': session_id,
        'user_id': user_id,
        'stage': 'upgrade',
        'data': json_module.dumps(funnel_data),
        'created': datetime.now(timezone.utc)
    })

    db.commit()

    logger.info(f"Created upgrade funnel record for user {user_id}, subscription {subscription_id}")

    return {
        'funnel_created': True,
        'user_id': user_id,
        'subscription_id': subscription_id,
        'session_id': str(session_id) if session_id else None
    }


def track_first_card_creation(
    db: Session,
    user_id: str,
    card_id: str,
    card_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Track first card creation event.

    Creates first_card funnel record.

    Args:
        db: Database session
        user_id: User ID
        card_id: Card ID
        card_data: Optional card metadata

    Returns:
        dict with 'funnel_created', 'user_id', 'card_id'
    """
    # Check if this is the first card
    existing = db.execute(text("""
        SELECT COUNT(*) FROM conversion_funnel
        WHERE user_id = :user_id AND funnel_stage = 'first_card'
    """), {'user_id': user_id}).fetchone()

    if existing and existing[0] > 0:
        logger.info(f"User {user_id} already has first_card record")
        return {
            'funnel_created': False,
            'user_id': user_id,
            'card_id': card_id,
            'message': 'First card already tracked'
        }

    # Find session by user_id
    result = db.execute(text("""
        SELECT session_id
        FROM analytics_sessions
        WHERE user_id = :user_id
        ORDER BY last_seen DESC
        LIMIT 1
    """), {'user_id': user_id}).fetchone()

    session_id = result[0] if result else None

    # Create conversion funnel record
    import json as json_module
    funnel_data = {
        'card_id': card_id,
        'card_data': card_data or {}
    }

    db.execute(text("""
        INSERT INTO conversion_funnel
        (id, session_id, user_id, funnel_stage, data, created)
        VALUES (:id, :session_id, :user_id, :stage, CAST(:data AS jsonb), :created)
    """), {
        'id': uuid4(),
        'session_id': session_id,
        'user_id': user_id,
        'stage': 'first_card',
        'data': json_module.dumps(funnel_data),
        'created': datetime.now(timezone.utc)
    })

    db.commit()

    logger.info(f"Tracked first card creation for user {user_id}")

    return {
        'funnel_created': True,
        'user_id': user_id,
        'card_id': card_id,
        'session_id': str(session_id) if session_id else None
    }
