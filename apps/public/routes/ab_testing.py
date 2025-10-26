"""
A/B Testing API Routes.

Provides endpoints for:
- Retrieving assigned variant for a session
- Tracking conversion events (CTA clicks)
- Getting test results (admin)
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..config.database import get_db
from ..services.ab_test_service import (
    get_active_disclaimer_tests,
    get_disclaimer_test_variants,
    assign_disclaimer_variant,
    track_disclaimer_cta_click,
    calculate_disclaimer_test_results
)

router = APIRouter(prefix="/api/ab-test", tags=["ab_testing"])


class VariantResponse(BaseModel):
    """Response model for variant assignment."""
    variant_id: str
    variant_name: str
    content: dict
    is_control: bool


class ConversionRequest(BaseModel):
    """Request model for conversion tracking."""
    session_id: str
    variant_id: str


class ConversionResponse(BaseModel):
    """Response model for conversion tracking."""
    success: bool
    message: str


@router.get("/active-tests")
async def get_active_tests(db: Session = Depends(get_db)):
    """
    Get all active A/B tests.

    Returns:
        List of active test dicts
    """
    tests = get_active_disclaimer_tests(db)
    return {"tests": tests}


@router.get("/test/{test_id}/variant")
async def get_variant_for_session(
    test_id: str,
    session_id: str,
    db: Session = Depends(get_db)
) -> VariantResponse:
    """
    Get or assign a variant for a session.

    Args:
        test_id: A/B test UUID
        session_id: Session UUID (from analytics)
        db: Database session

    Returns:
        Variant data with content to render

    Raises:
        HTTPException: 404 if test not found
    """
    variant = assign_disclaimer_variant(db, session_id, test_id)

    if not variant:
        raise HTTPException(
            status_code=404,
            detail=f"No active test found with ID: {test_id}"
        )

    return VariantResponse(
        variant_id=variant['id'],
        variant_name=variant['name'],
        content=variant['content'],
        is_control=variant['is_control']
    )


@router.post("/conversion", response_model=ConversionResponse)
async def track_conversion(
    request: ConversionRequest,
    db: Session = Depends(get_db)
):
    """
    Track a conversion event (CTA click).

    Args:
        request: Conversion data (session_id, variant_id)
        db: Database session

    Returns:
        Success status
    """
    success = track_disclaimer_cta_click(
        db,
        request.session_id,
        request.variant_id
    )

    if success:
        return ConversionResponse(
            success=True,
            message="Conversion tracked successfully"
        )
    else:
        return ConversionResponse(
            success=False,
            message="Failed to track conversion"
        )


@router.get("/test/{test_id}/results")
async def get_test_results(
    test_id: str,
    db: Session = Depends(get_db)
):
    """
    Get A/B test results including conversion rates and statistical significance.

    Admin endpoint for viewing test performance.

    Args:
        test_id: A/B test UUID
        db: Database session

    Returns:
        Test results with variant performance data
    """
    results = calculate_disclaimer_test_results(db, test_id)
    return results
