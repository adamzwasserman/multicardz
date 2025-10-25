"""
A/B Test Middleware.

Handles session management and A/B test variant assignment through middleware
following event sourcing architecture.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4, UUID
from sqlalchemy import text
from ..config.database import get_db
from ..services.ab_test_service import assign_variant_for_session


class ABTestMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle A/B test variant assignment.

    Responsibilities:
    - Extract or create session ID
    - Assign A/B test variant for session
    - Attach variant content to request.state
    """

    async def dispatch(self, request: Request, call_next):
        # Get or create session ID
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid4())
            request.session['session_id'] = session_id

        # Get database session
        db = next(get_db())
        try:
            # Assign A/B test variant (if any active tests)
            variant_assignment = assign_variant_for_session(UUID(session_id), db)

            # Get variant content if assigned
            variant_content = None
            if variant_assignment:
                variant_result = db.execute(
                    text("""
                        SELECT v.name, v.content
                        FROM a_b_test_variants v
                        WHERE v.id = :variant_id
                    """),
                    {'variant_id': variant_assignment['variant_id']}
                ).fetchone()

                if variant_result:
                    variant_content = {
                        'name': variant_result[0],
                        'content': variant_result[1]
                    }

            # Attach to request state for route handlers
            request.state.ab_test_variant = variant_content
            request.state.session_id = session_id

        finally:
            db.close()

        # Process request
        response = await call_next(request)
        return response
