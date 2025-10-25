"""Pydantic models for analytics data."""

from pydantic import BaseModel, Field, model_validator, ConfigDict
from uuid import UUID, uuid4
from datetime import datetime, UTC


class AnalyticsSession(BaseModel):
    """Analytics session model."""
    session_id: UUID = Field(default_factory=uuid4)
    landing_page_id: UUID | None = None
    landing_page_slug: str | None = None
    a_b_variant_id: UUID | None = None
    referrer_url: str | None = None
    referrer_domain: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None
    browser_fingerprint: str | None = None
    first_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    user_id: UUID | None = None

    @model_validator(mode='after')
    def extract_domain(self):
        """Extract domain from referrer_url if referrer_domain not provided."""
        if not self.referrer_domain and self.referrer_url:
            from urllib.parse import urlparse
            parsed = urlparse(self.referrer_url)
            self.referrer_domain = parsed.netloc.lower()
        return self

    model_config = ConfigDict(from_attributes=True)


class PageView(BaseModel):
    """Page view model."""
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    landing_page_id: UUID | None = None
    url: str
    referrer: str | None = None
    duration_ms: int | None = None
    scroll_depth_percent: int | None = Field(None, ge=0, le=100)
    viewport_width: int | None = None
    viewport_height: int | None = None
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class AnalyticsEvent(BaseModel):
    """Analytics event model."""
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    page_view_id: UUID
    event_type: str  # 'click', 'cta_click', 'scroll', 'section_view'
    element_selector: str | None = None
    element_text: str | None = None
    element_position_x: int | None = None
    element_position_y: int | None = None
    timestamp_ms: int = Field(..., gt=0)  # Must be positive
    created: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class BatchEvents(BaseModel):
    """Batch event submission."""
    session_id: UUID
    page_view_id: UUID
    events: list[dict]  # Array of event data


class MouseTrackingPoint(BaseModel):
    """Mouse tracking coordinate."""
    session_id: UUID
    page_view_id: UUID
    timestamp_ms: int
    event_type: str  # 'move', 'click', 'scroll'
    x: int | None = None
    y: int | None = None
    scroll_x: int | None = None
    scroll_y: int | None = None


# API Request/Response Models

class SessionCreateRequest(BaseModel):
    """Request model for session creation."""
    session_id: str | UUID  # Allow string to be converted
    anonymous_user_id: str | None = None  # Persistent cookie-based anonymous user ID
    referrer_url: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_term: str | None = None
    utm_content: str | None = None
    user_agent: str | None = None
    viewport_width: int | None = None
    viewport_height: int | None = None
    timestamp: int | None = None  # Milliseconds since epoch


class SessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str
    status: str  # 'created' or 'updated'
    message: str | None = None


class PageViewRequest(BaseModel):
    """Request model for page view logging."""
    session_id: str | UUID
    url: str
    referrer: str | None = None
    duration_ms: int | None = None
    scroll_depth_percent: int | None = Field(None, ge=0, le=100)
    viewport_width: int | None = None
    viewport_height: int | None = None


class PageViewResponse(BaseModel):
    """Response model for page view logging."""
    page_view_id: str
    status: str
    message: str | None = None


class EventBatchRequest(BaseModel):
    """Request model for batch event submission."""
    session_id: str | UUID
    page_view_id: str | UUID
    events: list[dict]  # Array of event data


class EventBatchResponse(BaseModel):
    """Response model for batch event submission."""
    events_created: int
    status: str
    message: str | None = None


class MouseTrackingRequest(BaseModel):
    """Request model for mouse tracking data."""
    session_id: str | UUID
    page_view_id: str | UUID
    coordinates: list[dict]  # Array of {x, y, timestamp_ms, event_type}


class MouseTrackingResponse(BaseModel):
    """Response model for mouse tracking data."""
    points_created: int
    status: str
    message: str | None = None
