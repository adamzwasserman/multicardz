"""
Request interceptor middleware using pure functions.
Following Zero-Trust UUID Architecture Phase 2 requirements.
"""
import logging
import time
from typing import Callable, Awaitable
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Pure function for request interception logic
async def intercept_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    start_time: float = None
) -> Response:
    """
    Intercept request before it reaches route handler.

    Args:
        request: The incoming request
        call_next: Function to call the next middleware/route
        start_time: Optional start time (uses current time if not provided)

    Returns:
        Response from the route handler
    """
    if start_time is None:
        start_time = time.time()

    # Log all incoming requests
    logger.info(f"REQUEST: {request.method} {request.url.path}")

    # Add request metadata
    request.state.intercepted_at = start_time

    # Execute the actual route
    response = await call_next(request)

    # Log response
    duration = (time.time() - start_time) * 1000
    logger.info(f"RESPONSE: {request.method} {request.url.path} - {response.status_code} ({duration:.2f}ms)")

    return response


# Backward compatibility class wrapper (TEMPORARY - to be removed)
class RequestInterceptorMiddleware(BaseHTTPMiddleware):
    """
    DEPRECATED: Backward compatibility wrapper. Use intercept_request function instead.
    This class will be removed in Phase 2 completion.
    """

    async def dispatch(self, request: Request, call_next):
        """Intercept every request before it reaches the route handler."""
        return await intercept_request(request, call_next)
