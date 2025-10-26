"""Analytics API routes."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID
from datetime import datetime, UTC
import logging

from ..config.database import get_db
from ..models.analytics import (
    SessionCreateRequest,
    SessionResponse,
    PageViewRequest,
    PageViewResponse,
    EventBatchRequest,
    EventBatchResponse,
    MouseTrackingRequest,
    MouseTrackingResponse,
    AnalyticsSession,
    PageView,
    AnalyticsEvent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def extract_client_ip(request: Request) -> str | None:
    """
    Extract client IP address from request headers.

    Checks for X-Forwarded-For header first (for proxies),
    falls back to direct client IP.

    Args:
        request: FastAPI Request object

    Returns:
        str | None: Client IP address or None for test clients
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()

    # Fallback to direct client IP
    if request.client:
        host = request.client.host
        # Return None for test client (not a valid IP)
        if host == "testclient":
            return None
        return host

    return None


def create_session_in_db(
    session_data: SessionCreateRequest,
    ip_address: str,
    db: Session
) -> tuple[AnalyticsSession, bool]:
    """
    Create or update analytics session in database.
    
    Args:
        session_data: Session data from request
        ip_address: Client IP address
        db: Database session
        
    Returns:
        tuple: (AnalyticsSession, is_new) where is_new indicates if session was created
    """
    # Convert session_id to UUID if it's a string
    session_id = UUID(str(session_data.session_id))
    
    # Check if session already exists
    existing = db.execute(
        text("""
        SELECT session_id, first_seen, last_seen
        FROM analytics_sessions
        WHERE session_id = :session_id
        """),
        {"session_id": session_id}
    ).fetchone()
    
    if existing:
        # Update last_seen timestamp
        db.execute(
            text("""
            UPDATE analytics_sessions
            SET last_seen = :now
            WHERE session_id = :session_id
            """),
            {
                "session_id": session_id,
                "now": datetime.now(UTC)
            }
        )
        db.commit()
        
        # Return existing session
        session = AnalyticsSession(
            session_id=existing[0],
            first_seen=existing[1],
            last_seen=datetime.now(UTC)
        )
        return session, False
    
    # Create AnalyticsSession model instance (triggers domain extraction)
    session = AnalyticsSession(
        session_id=session_id,
        referrer_url=session_data.referrer_url,
        utm_source=session_data.utm_source,
        utm_medium=session_data.utm_medium,
        utm_campaign=session_data.utm_campaign,
        utm_term=session_data.utm_term,
        utm_content=session_data.utm_content,
        user_agent=session_data.user_agent,
        ip_address=ip_address
    )
    
    # Insert into database
    db.execute(
        text("""
        INSERT INTO analytics_sessions (
            session_id,
            user_id,
            referrer_url,
            referrer_domain,
            utm_source,
            utm_medium,
            utm_campaign,
            utm_term,
            utm_content,
            user_agent,
            ip_address,
            first_seen,
            last_seen
        ) VALUES (
            :session_id,
            :user_id,
            :referrer_url,
            :referrer_domain,
            :utm_source,
            :utm_medium,
            :utm_campaign,
            :utm_term,
            :utm_content,
            :user_agent,
            :ip_address,
            :first_seen,
            :last_seen
        )
        """),
        {
            "session_id": session.session_id,
            "user_id": session_data.anonymous_user_id,  # Store anonymous user ID for tracking
            "referrer_url": session.referrer_url,
            "referrer_domain": session.referrer_domain,
            "utm_source": session.utm_source,
            "utm_medium": session.utm_medium,
            "utm_campaign": session.utm_campaign,
            "utm_term": session.utm_term,
            "utm_content": session.utm_content,
            "user_agent": session.user_agent,
            "ip_address": session.ip_address,
            "first_seen": session.first_seen,
            "last_seen": session.last_seen
        }
    )
    db.commit()
    
    return session, True


@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: Request,
    session_data: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create or update an analytics session.
    
    If session_id already exists, updates last_seen timestamp.
    If new session, creates database record with UTM parameters and referrer info.
    
    Args:
        request: FastAPI Request (for IP extraction)
        session_data: Session creation data
        db: Database session
        
    Returns:
        SessionResponse with session_id and status
    """
    try:
        # Extract client IP
        ip_address = extract_client_ip(request)
        
        # Create or update session
        session, is_new = create_session_in_db(session_data, ip_address, db)
        
        # Determine response status code and message
        response_status = "created" if is_new else "updated"
        status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
        
        response = SessionResponse(
            session_id=str(session.session_id),
            status=response_status,
            message=f"Session {response_status} successfully"
        )
        
        return JSONResponse(
            status_code=status_code,
            content=response.model_dump()
        )
        
    except ValueError as e:
        logger.error(f"Invalid session data: {e}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )


@router.post("/page-view", response_model=PageViewResponse, status_code=status.HTTP_201_CREATED)
async def create_page_view(
    page_view_data: PageViewRequest,
    db: Session = Depends(get_db)
):
    """
    Log a page view event.
    
    Records which pages the user visits with timing and engagement metrics.
    
    Args:
        page_view_data: Page view data including URL, duration, scroll depth
        db: Database session
        
    Returns:
        PageViewResponse with page_view_id
    """
    try:
        # Create PageView model instance
        page_view = PageView(
            session_id=UUID(str(page_view_data.session_id)),
            url=page_view_data.url,
            referrer=page_view_data.referrer,
            duration_ms=page_view_data.duration_ms,
            scroll_depth_percent=page_view_data.scroll_depth_percent,
            viewport_width=page_view_data.viewport_width,
            viewport_height=page_view_data.viewport_height
        )
        
        # Insert into database
        db.execute(
            text("""
            INSERT INTO analytics_page_views (
                id, session_id, url, referrer, duration_ms,
                scroll_depth_percent, viewport_width, viewport_height, created
            ) VALUES (
                :id, :session_id, :url, :referrer, :duration_ms,
                :scroll_depth_percent, :viewport_width, :viewport_height, :created
            )
            """),
            {
                "id": page_view.id,
                "session_id": page_view.session_id,
                "url": page_view.url,
                "referrer": page_view.referrer,
                "duration_ms": page_view.duration_ms,
                "scroll_depth_percent": page_view.scroll_depth_percent,
                "viewport_width": page_view.viewport_width,
                "viewport_height": page_view.viewport_height,
                "created": page_view.created
            }
        )
        db.commit()
        
        response = PageViewResponse(
            page_view_id=str(page_view.id),
            status="created",
            message="Page view logged successfully"
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.model_dump()
        )
        
    except ValueError as e:
        logger.error(f"Invalid page view data: {e}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Error logging page view: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )


@router.post("/events/batch", response_model=EventBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_events_batch(
    batch_data: EventBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a batch of analytics events.
    
    Client sends multiple events at once to reduce API calls.
    
    Args:
        batch_data: Batch of events with session and page view IDs
        db: Database session
        
    Returns:
        EventBatchResponse with count of events created
    """
    try:
        session_id = UUID(str(batch_data.session_id))
        page_view_id = UUID(str(batch_data.page_view_id))
        
        events_created = 0
        
        for event_data in batch_data.events:
            # Create event instance
            event = AnalyticsEvent(
                session_id=session_id,
                page_view_id=page_view_id,
                event_type=event_data.get('event_type', 'unknown'),
                element_selector=event_data.get('element_selector'),
                element_text=event_data.get('element_text'),
                element_position_x=event_data.get('element_position_x'),
                element_position_y=event_data.get('element_position_y'),
                timestamp_ms=event_data.get('timestamp_ms', 0)
            )
            
            # Insert into database
            db.execute(
                text("""
                INSERT INTO analytics_events (
                    id, session_id, page_view_id, event_type,
                    element_selector, element_text,
                    element_position_x, element_position_y,
                    timestamp_ms, created
                ) VALUES (
                    :id, :session_id, :page_view_id, :event_type,
                    :element_selector, :element_text,
                    :element_position_x, :element_position_y,
                    :timestamp_ms, :created
                )
                """),
                {
                    "id": event.id,
                    "session_id": event.session_id,
                    "page_view_id": event.page_view_id,
                    "event_type": event.event_type,
                    "element_selector": event.element_selector,
                    "element_text": event.element_text,
                    "element_position_x": event.element_position_x,
                    "element_position_y": event.element_position_y,
                    "timestamp_ms": event.timestamp_ms,
                    "created": event.created
                }
            )
            events_created += 1
        
        db.commit()
        
        response = EventBatchResponse(
            events_created=events_created,
            status="created",
            message=f"{events_created} events logged successfully"
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.model_dump()
        )
        
    except ValueError as e:
        logger.error(f"Invalid event batch data: {e}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Error logging event batch: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )


@router.post("/mouse-tracking", response_model=MouseTrackingResponse, status_code=status.HTTP_201_CREATED)
async def create_mouse_tracking(
    tracking_data: MouseTrackingRequest,
    db: Session = Depends(get_db)
):
    """
    Submit mouse tracking coordinates.
    
    Records mouse movements and clicks for session replay.
    
    Args:
        tracking_data: Mouse coordinates with timestamps
        db: Database session
        
    Returns:
        MouseTrackingResponse with count of points created
    """
    try:
        session_id = UUID(str(tracking_data.session_id))
        page_view_id = UUID(str(tracking_data.page_view_id))
        
        points_created = 0
        
        for coord in tracking_data.coordinates:
            # Insert into database (id is auto-increment)
            db.execute(
                text("""
                INSERT INTO analytics_mouse_tracking (
                    session_id, page_view_id, timestamp_ms,
                    event_type, x, y, scroll_x, scroll_y
                ) VALUES (
                    :session_id, :page_view_id, :timestamp_ms,
                    :event_type, :x, :y, :scroll_x, :scroll_y
                )
                """),
                {
                    "session_id": session_id,
                    "page_view_id": page_view_id,
                    "timestamp_ms": coord.get('timestamp_ms', 0),
                    "event_type": coord.get('event_type', 'move'),
                    "x": coord.get('x'),
                    "y": coord.get('y'),
                    "scroll_x": coord.get('scroll_x'),
                    "scroll_y": coord.get('scroll_y')
                }
            )
            points_created += 1
        
        db.commit()
        
        response = MouseTrackingResponse(
            points_created=points_created,
            status="created",
            message=f"{points_created} mouse tracking points logged successfully"
        )
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response.model_dump()
        )
        
    except ValueError as e:
        logger.error(f"Invalid mouse tracking data: {e}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(e)}
        )
    except Exception as e:
        logger.error(f"Error logging mouse tracking: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )
