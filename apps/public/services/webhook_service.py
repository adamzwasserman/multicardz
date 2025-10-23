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
    browser_fingerprint: str,
    email: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process Auth0 signup webhook.

    Links analytics session to user account and creates signup funnel record.

    Args:
        db: Database session
        user_id: Auth0 user ID (e.g., "auth0|user123")
        browser_fingerprint: Browser fingerprint from session
        email: User email address
        metadata: Additional metadata from Auth0

    Returns:
        dict with 'session_updated', 'funnel_created', 'session_id', 'user_id'
    """
    session_updated = False
    session_id = None

    # Find session by browser fingerprint
    result = db.execute(text("""
        SELECT session_id, user_id
        FROM analytics_sessions
        WHERE browser_fingerprint = :fingerprint
        LIMIT 1
    """), {'fingerprint': browser_fingerprint}).fetchone()

    if result:
        existing_session_id, existing_user_id = result

        # Only update if not already linked
        if existing_user_id is None:
            db.execute(text("""
                UPDATE analytics_sessions
                SET user_id = :user_id, last_seen = :now
                WHERE session_id = :session_id
            """), {
                'user_id': user_id,
                'session_id': existing_session_id,
                'now': datetime.now(timezone.utc)
            })
            session_updated = True
            session_id = existing_session_id
            logger.info(f"Linked session {existing_session_id} to user {user_id}")
        else:
            # Already linked - don't create duplicate funnel record
            logger.info(f"Session {existing_session_id} already linked to {existing_user_id}")
            return {
                'session_updated': False,
                'funnel_created': False,
                'session_id': str(existing_session_id),
                'user_id': user_id,
                'message': 'Session already linked'
            }
    else:
        logger.info(f"No session found for fingerprint {browser_fingerprint}")

    # Create conversion funnel record
    import json as json_module
    funnel_data = {
        'email': email,
        'auth0_metadata': metadata or {}
    }

    db.execute(text("""
        INSERT INTO conversion_funnel
        (id, session_id, user_id, funnel_stage, data, created)
        VALUES (:id, :session_id, :user_id, :stage, CAST(:data AS jsonb), :created)
    """), {
        'id': uuid4(),
        'session_id': session_id,
        'user_id': user_id,
        'stage': 'signup',
        'data': json_module.dumps(funnel_data),
        'created': datetime.now(timezone.utc)
    })

    db.commit()

    logger.info(f"Created signup funnel record for user {user_id}")

    return {
        'session_updated': session_updated,
        'funnel_created': True,
        'session_id': str(session_id) if session_id else None,
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
