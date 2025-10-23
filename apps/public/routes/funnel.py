"""
Funnel analytics API routes.

Provides comprehensive funnel analytics endpoints for tracking user progression
through conversion stages.

Endpoints:
- GET /api/funnel/metrics - Overall funnel metrics
- GET /api/funnel/user/{user_id} - User-specific funnel progression
- GET /api/funnel/dropoff - Drop-off analysis between stages
- GET /api/funnel/durations - Average time between stages
- GET /api/funnel/cohort/{date} - Cohort analysis by date
- GET /api/funnel/by-page - Performance by landing page
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from core.database import get_db
from services.funnel_service import (
    get_overall_funnel_metrics,
    get_user_funnel_progression,
    get_funnel_dropoff_analysis,
    get_average_stage_durations,
    get_funnel_cohort_analysis,
    get_funnel_by_landing_page
)

router = APIRouter(prefix="/api/funnel", tags=["funnel"])


# Response models
class FunnelMetricsResponse(BaseModel):
    """Overall funnel metrics response."""
    stages: Dict[str, int]
    conversion_rates: Dict[str, float]
    average_durations: Dict[str, float]


class UserProgressionResponse(BaseModel):
    """User funnel progression response."""
    user_id: str
    stages: List[Dict[str, Any]]
    stage_durations: Dict[str, float]
    time_between_stages: Dict[str, float]


class DropoffAnalysisResponse(BaseModel):
    """Funnel drop-off analysis response."""
    landing_to_signup: Dict[str, Any] | None = None
    signup_to_first_card: Dict[str, Any] | None = None
    first_card_to_upgrade: Dict[str, Any] | None = None


class StageDurationsResponse(BaseModel):
    """Average stage durations response."""
    landing_to_signup: Dict[str, float]
    signup_to_first_card: Dict[str, float]
    first_card_to_upgrade: Dict[str, float]


class CohortAnalysisResponse(BaseModel):
    """Cohort analysis response."""
    cohort_date: str
    total_users: int
    signups: int
    first_cards: int
    upgrades: int
    signup_conversion_rate: float
    first_card_conversion_rate: float
    upgrade_conversion_rate: float


class PagePerformanceItem(BaseModel):
    """Landing page performance item."""
    landing_page_id: str
    page_slug: str
    page_name: str
    landings: int
    signups: int
    conversion_rate: float


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/metrics", response_model=FunnelMetricsResponse)
def get_funnel_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get overall funnel metrics.

    Returns aggregated stage counts, conversion rates, and average durations
    across the entire conversion funnel.

    Returns:
        FunnelMetricsResponse with stages, conversion_rates, average_durations
    """
    return get_overall_funnel_metrics(db)


@router.get("/user/{user_id}", response_model=UserProgressionResponse)
def get_user_progression(
    user_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get funnel progression for a specific user.

    Shows all stages the user has completed with timestamps and
    time between each stage.

    Args:
        user_id: User ID to analyze

    Returns:
        UserProgressionResponse with user's funnel journey

    Raises:
        HTTPException: 404 if user has no funnel records
    """
    progression = get_user_funnel_progression(db, user_id)

    if not progression.get('stages'):
        raise HTTPException(
            status_code=404,
            detail=f"No funnel records found for user {user_id}"
        )

    return progression


@router.get("/dropoff", response_model=DropoffAnalysisResponse)
def get_dropoff_analysis(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Analyze drop-off rates between funnel stages.

    Calculates the percentage of users who drop off at each stage
    transition (landing→signup, signup→first_card, first_card→upgrade).

    Returns:
        DropoffAnalysisResponse with drop-off rates for each transition
    """
    return get_funnel_dropoff_analysis(db)


@router.get("/durations", response_model=StageDurationsResponse)
def get_stage_durations(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get average time users spend between funnel stages.

    Returns average seconds for each stage transition.

    Returns:
        StageDurationsResponse with average durations
    """
    return get_average_stage_durations(db)


@router.get("/cohort/{cohort_date}", response_model=CohortAnalysisResponse)
def get_cohort_analysis(
    cohort_date: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze funnel performance for a specific cohort by signup date.

    Args:
        cohort_date: Date string (YYYY-MM-DD) for cohort analysis

    Returns:
        CohortAnalysisResponse with cohort conversion metrics

    Example:
        GET /api/funnel/cohort/2025-10-20
    """
    return get_funnel_cohort_analysis(db, cohort_date)


@router.get("/by-page", response_model=List[PagePerformanceItem])
def get_page_performance(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Analyze funnel performance by landing page.

    Returns conversion rates for each landing page, sorted by
    conversion rate (best performing first).

    Returns:
        List of PagePerformanceItem sorted by conversion_rate DESC
    """
    return get_funnel_by_landing_page(db)
