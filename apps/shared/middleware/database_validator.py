"""
Database validation middleware using pure functions.
Following Zero-Trust UUID Architecture Phase 2 requirements.
"""
import logging
from typing import Callable, Awaitable
from pathlib import Path
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from apps.shared.config.database import DATABASE_PATH

logger = logging.getLogger(__name__)


# Pure function for database validation logic
async def validate_database_access(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    db_path: Path = DATABASE_PATH
) -> Response:
    """
    Validate database configuration before processing request.

    Args:
        request: The incoming request
        call_next: Function to call the next middleware/route
        db_path: Database path to validate

    Returns:
        Response from the route handler
    """
    # Validate database exists
    if not db_path.exists():
        logger.error(f"Database does not exist at: {db_path}")
        # Don't fail the request, just log - database might be created on first use

    # Log database path for API requests (helps debugging)
    if request.url.path.startswith('/api'):
        logger.debug(f"API Request using database: {db_path}")

    # Continue with request
    response = await call_next(request)
    return response


# Backward compatibility class wrapper (TEMPORARY - to be removed)
class DatabaseValidationMiddleware(BaseHTTPMiddleware):
    """
    DEPRECATED: Backward compatibility wrapper. Use validate_database_access function instead.
    This class will be removed in Phase 2 completion.
    """

    async def dispatch(self, request: Request, call_next):
        """Intercept request and validate database configuration."""
        return await validate_database_access(request, call_next)
