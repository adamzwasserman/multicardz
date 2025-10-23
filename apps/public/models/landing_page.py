"""Pydantic models for landing page content."""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class LandingPageSection(BaseModel):
    """Landing page section with polymorphic data."""
    id: UUID
    landing_page_id: UUID
    section_type: str  # 'pain_point', 'benefit', 'comparison_metric', etc.
    order_index: int
    data: dict  # JSONB content
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class LandingPage(BaseModel):
    """Landing page model."""
    id: UUID
    slug: str
    category: str  # 'REPLACEMENT' or 'COMPLEMENTARY'
    name: str
    headline: str
    subheadline: str | None = None
    competitor_name: str | None = None
    is_active: bool = True
    created: datetime
    modified: datetime
    deleted: datetime | None = None

    # Related sections (loaded separately)
    sections: list[LandingPageSection] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
