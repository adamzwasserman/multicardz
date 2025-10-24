"""
Webhook routes for Auth0 and Stripe integrations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import logging
import os

from ..config.database import get_db
from ..services.webhook_service import (
    process_auth0_signup,
    process_auth0_signup_batch,
    verify_webhook_signature,
    process_stripe_subscription,
    track_first_card_creation
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/webhooks', tags=['webhooks'])


# Pydantic models for request validation

class Auth0SignupWebhook(BaseModel):
    """Auth0 user signup webhook payload."""
    user_id: str = Field(..., description="Auth0 user ID")
    browser_fingerprint: str = Field(..., description="Browser fingerprint from analytics")
    email: str = Field(..., description="User email address")
    created_at: str = Field(..., description="ISO timestamp of signup")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional Auth0 metadata")


class Auth0SignupBatchWebhook(BaseModel):
    """Batch of Auth0 signup webhooks."""
    signups: List[Auth0SignupWebhook] = Field(..., description="List of signup events")


class StripeSubscriptionWebhook(BaseModel):
    """Stripe subscription webhook payload."""
    user_id: str = Field(..., description="User ID (from Stripe metadata)")
    subscription_id: str = Field(..., description="Stripe subscription ID")
    plan: str = Field(..., description="Subscription plan name")
    status: str = Field(..., description="Subscription status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional Stripe metadata")


class FirstCardWebhook(BaseModel):
    """First card creation webhook payload."""
    user_id: str = Field(..., description="User ID")
    card_id: str = Field(..., description="Card ID")
    card_data: Optional[Dict[str, Any]] = Field(None, description="Card metadata")


# Webhook endpoints

@router.post('/auth0/signup')
async def auth0_signup_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_auth0_webhook_signature: Optional[str] = Header(None)
):
    """
    Handle Auth0 user signup webhook.

    Links analytics session to user account and creates signup funnel record.
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature if configured
    webhook_secret = os.getenv('AUTH0_WEBHOOK_SECRET')
    if webhook_secret and x_auth0_webhook_signature:
        if not verify_webhook_signature(body, x_auth0_webhook_signature, webhook_secret):
            logger.warning(f"Invalid Auth0 webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    import json
    payload_dict = json.loads(body.decode())
    payload = Auth0SignupWebhook(**payload_dict)

    try:
        result = process_auth0_signup(
            db=db,
            user_id=payload.user_id,
            browser_fingerprint=payload.browser_fingerprint,
            email=payload.email,
            metadata=payload.metadata
        )

        logger.info(f"Processed Auth0 signup for user {payload.user_id}: {result}")

        return {
            'success': True,
            'result': result
        }

    except Exception as e:
        logger.error(f"Error processing Auth0 signup webhook: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post('/auth0/signup/batch')
async def auth0_signup_batch_webhook(
    payload: Auth0SignupBatchWebhook,
    db: Session = Depends(get_db)
):
    """
    Handle batch of Auth0 signup webhooks.

    Processes multiple signups in a single request.
    """
    try:
        # Convert Pydantic models to dicts
        signups = [signup.model_dump() for signup in payload.signups]

        result = process_auth0_signup_batch(
            db=db,
            signups=signups
        )

        logger.info(f"Processed Auth0 batch signup: {result}")

        return {
            'success': True,
            'result': result
        }

    except Exception as e:
        logger.error(f"Error processing Auth0 batch signup webhook: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing batch webhook: {str(e)}")


@router.post('/stripe/subscription')
async def stripe_subscription_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: Optional[str] = Header(None)
):
    """
    Handle Stripe subscription webhook.

    Creates upgrade funnel record when user subscribes.
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature if configured
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if webhook_secret and stripe_signature:
        if not verify_webhook_signature(body, stripe_signature, webhook_secret):
            logger.warning(f"Invalid Stripe webhook signature")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    import json
    payload_dict = json.loads(body.decode())
    payload = StripeSubscriptionWebhook(**payload_dict)

    try:
        result = process_stripe_subscription(
            db=db,
            user_id=payload.user_id,
            subscription_id=payload.subscription_id,
            plan=payload.plan,
            status=payload.status,
            metadata=payload.metadata
        )

        logger.info(f"Processed Stripe subscription for user {payload.user_id}: {result}")

        return {
            'success': True,
            'result': result
        }

    except Exception as e:
        logger.error(f"Error processing Stripe subscription webhook: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post('/first-card')
async def first_card_webhook(
    payload: FirstCardWebhook,
    db: Session = Depends(get_db)
):
    """
    Handle first card creation webhook.

    Tracks when a user creates their first card.
    """
    try:
        result = track_first_card_creation(
            db=db,
            user_id=payload.user_id,
            card_id=payload.card_id,
            card_data=payload.card_data
        )

        logger.info(f"Tracked first card for user {payload.user_id}: {result}")

        return {
            'success': True,
            'result': result
        }

    except Exception as e:
        logger.error(f"Error tracking first card: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error tracking first card: {str(e)}")
