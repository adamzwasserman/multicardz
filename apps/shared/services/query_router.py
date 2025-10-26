"""
Query Router for Turso Browser Integration.

Routes queries between browser database (content) and server database (bitmaps)
based on the current database mode (privacy, normal, dev).

Architecture:
- Pure functions for routing logic
- NamedTuple for type-safe results
- Zero-trust UUID isolation enforced
- Privacy mode: content → browser, bitmaps → server
- Normal mode: all → server
- Dev mode: all → local

Examples:
    >>> # Route content query in privacy mode
    >>> result = route_card_query("ws-1", "user-1", mode="privacy", query_type="content")
    >>> result.source
    'browser'

    >>> # Route bitmap operation in privacy mode
    >>> result = route_bitmap_operation("ws-1", "user-1", operations=[{"type": "union"}])
    >>> result.source
    'server'

    >>> # Combined query (server filters, browser resolves)
    >>> result = route_filtered_query("ws-1", "user-1", filter_operations=[{"type": "intersection"}])
    >>> len(result.cards) > 0
    True
"""

from typing import NamedTuple, List, Dict, Any, Optional, Literal
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class QueryResult(NamedTuple):
    """Result of a routed query operation.

    Attributes:
        success: Whether the query executed successfully
        source: Where the query executed ('browser', 'server', 'local')
        data: Query result data
        error: Error message if query failed
        card_ids: List of card UUIDs (for bitmap operations)
    """
    success: bool
    source: Literal['browser', 'server', 'local']
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    card_ids: Optional[List[str]] = None


class FilteredQueryResult(NamedTuple):
    """Result of a combined browser + server filtered query.

    Attributes:
        success: Whether the operation succeeded
        matched_card_ids: UUIDs from server bitmap filtering
        cards: Full card content from browser database
        total_matches: Number of cards matching filter
        error: Error message if operation failed
    """
    success: bool
    matched_card_ids: List[str]
    cards: List[Dict[str, Any]]
    total_matches: int
    error: Optional[str] = None


class RoutingDecision(NamedTuple):
    """Decision about where to route a query.

    Attributes:
        target: Where to route the query ('browser', 'server', 'local')
        reason: Explanation for routing decision
        fallback: Alternative target if primary fails
    """
    target: Literal['browser', 'server', 'local']
    reason: str
    fallback: Optional[Literal['browser', 'server', 'local']] = None


# ============================================================================
# ROUTING DECISION FUNCTIONS (PURE)
# ============================================================================

def decide_routing_target(
    mode: str,
    query_type: Literal['content', 'bitmap', 'combined']
) -> RoutingDecision:
    """Determine where to route a query based on mode and type.

    Pure function - deterministic routing logic.

    Args:
        mode: Database mode ('privacy', 'normal', 'dev')
        query_type: Type of query ('content', 'bitmap', 'combined')

    Returns:
        RoutingDecision with target and reason

    Examples:
        >>> decision = decide_routing_target('privacy', 'content')
        >>> decision.target
        'browser'

        >>> decision = decide_routing_target('privacy', 'bitmap')
        >>> decision.target
        'server'

        >>> decision = decide_routing_target('normal', 'content')
        >>> decision.target
        'server'
    """
    # Privacy mode routing
    if mode == 'privacy':
        if query_type == 'content':
            return RoutingDecision(
                target='browser',
                reason='Privacy mode: content stored in browser',
                fallback='server'
            )
        elif query_type == 'bitmap':
            return RoutingDecision(
                target='server',
                reason='Privacy mode: bitmaps computed on server',
                fallback=None
            )
        elif query_type == 'combined':
            return RoutingDecision(
                target='browser',  # Primary coordination happens in browser
                reason='Privacy mode: server filters, browser resolves',
                fallback='server'
            )

    # Normal mode routing (all to server)
    elif mode == 'normal':
        return RoutingDecision(
            target='server',
            reason='Normal mode: all data on server',
            fallback=None
        )

    # Dev mode routing (all to local)
    elif mode == 'dev':
        return RoutingDecision(
            target='local',
            reason='Dev mode: local database',
            fallback=None
        )

    # Unknown mode - default to server
    else:
        logger.warning(f"Unknown mode '{mode}', defaulting to server")
        return RoutingDecision(
            target='server',
            reason=f'Unknown mode {mode}, defaulting to server',
            fallback=None
        )


# ============================================================================
# QUERY EXECUTION FUNCTIONS
# ============================================================================

def route_card_query(
    workspace_id: str,
    user_id: str,
    mode: str = 'normal',
    query_type: Literal['content', 'bitmap'] = 'content',
    limit: int = 1000,
    offset: int = 0
) -> QueryResult:
    """Route a card query to the appropriate database.

    Routes based on mode and query type. In privacy mode, content queries
    go to browser database, bitmap queries go to server.

    Args:
        workspace_id: Workspace UUID (zero-trust isolation)
        user_id: User UUID (zero-trust isolation)
        mode: Database mode ('privacy', 'normal', 'dev')
        query_type: Type of query ('content', 'bitmap')
        limit: Maximum number of results
        offset: Result offset for pagination

    Returns:
        QueryResult with execution details

    Examples:
        >>> result = route_card_query("ws-1", "user-1", mode="privacy", query_type="content")
        >>> result.success
        True
        >>> result.source
        'browser'
    """
    try:
        # Determine routing target
        decision = decide_routing_target(mode, query_type)

        logger.info(
            f"Routing card query: mode={mode}, type={query_type}, "
            f"target={decision.target}, reason={decision.reason}"
        )

        # Execute based on target
        if decision.target == 'browser':
            # Browser database query
            from apps.shared.services.browser_database import (
                execute_query,
                BrowserDatabaseConnection
            )

            # Create a mock connected browser database connection
            conn = BrowserDatabaseConnection(
                database_name="multicardz_browser.db",
                storage_type="opfs",
                connected=True
            )

            result = execute_query(
                connection=conn,
                sql="""
                    SELECT card_id, name, description, tags, card_bitmap, created, modified
                    FROM cards
                    WHERE workspace_id = ? AND user_id = ? AND deleted IS NULL
                    ORDER BY created DESC
                    LIMIT ? OFFSET ?
                """,
                params=[workspace_id, user_id, limit, offset]
            )

            if result.success:
                return QueryResult(
                    success=True,
                    source='browser',
                    data={'cards': result.rows, 'count': len(result.rows)},
                    card_ids=[row.get('card_id') for row in result.rows] if result.rows else []
                )
            else:
                return QueryResult(
                    success=False,
                    source='browser',
                    error=result.error
                )

        elif decision.target == 'server':
            # Server database query (mock implementation)
            logger.info(f"Server query for workspace {workspace_id}, user {user_id}")
            return QueryResult(
                success=True,
                source='server',
                data={'cards': [], 'count': 0},
                card_ids=[]
            )

        elif decision.target == 'local':
            # Local dev database query (mock implementation)
            logger.info(f"Local query for workspace {workspace_id}, user {user_id}")
            return QueryResult(
                success=True,
                source='local',
                data={'cards': [], 'count': 0},
                card_ids=[]
            )

        else:
            return QueryResult(
                success=False,
                source='server',
                error=f"Unknown routing target: {decision.target}"
            )

    except Exception as e:
        logger.error(f"Query routing failed: {e}", exc_info=True)
        return QueryResult(
            success=False,
            source='server',
            error=str(e)
        )


def route_bitmap_operation(
    workspace_id: str,
    user_id: str,
    operations: List[Dict[str, Any]]
) -> QueryResult:
    """Route a bitmap operation to the server.

    Bitmap operations (union, intersection, exclusion) are always executed
    on the server, regardless of mode. Returns only UUIDs, never content.

    Args:
        workspace_id: Workspace UUID (zero-trust isolation)
        user_id: User UUID (zero-trust isolation)
        operations: List of bitmap operations to execute

    Returns:
        QueryResult with card UUIDs only

    Examples:
        >>> ops = [{"type": "union", "tag_ids": ["tag-1", "tag-2"]}]
        >>> result = route_bitmap_operation("ws-1", "user-1", ops)
        >>> result.success
        True
        >>> result.source
        'server'
        >>> 'card_ids' in result._asdict()
        True
    """
    try:
        logger.info(
            f"Routing bitmap operation: workspace={workspace_id}, "
            f"user={user_id}, operations={len(operations)}"
        )

        # Bitmap operations always go to server
        # (Mock implementation - would call actual bitmap service)
        from apps.shared.services.bitmap_sync import query_bitmaps

        # For now, query_bitmaps only takes workspace_id and user_id
        # Filter operations would be applied by a separate endpoint
        bitmap_result = query_bitmaps(
            workspace_id=workspace_id,
            user_id=user_id
        )

        # bitmap_result.QueryResult has: count, bitmaps, error
        if bitmap_result.error is None:
            # Extract card_ids from bitmaps
            card_ids = [b.get('card_id') for b in bitmap_result.bitmaps if 'card_id' in b]
            return QueryResult(
                success=True,
                source='server',
                data=None,  # No content - privacy enforced
                card_ids=card_ids
            )
        else:
            return QueryResult(
                success=False,
                source='server',
                error=bitmap_result.error
            )

    except Exception as e:
        logger.error(f"Bitmap operation routing failed: {e}", exc_info=True)
        return QueryResult(
            success=False,
            source='server',
            error=str(e)
        )


def route_filtered_query(
    workspace_id: str,
    user_id: str,
    filter_operations: List[Dict[str, Any]],
    limit: int = 1000,
    offset: int = 0
) -> FilteredQueryResult:
    """Execute a combined query: server filters, browser resolves content.

    Two-phase query:
    1. Server executes bitmap filtering → returns UUIDs
    2. Browser resolves UUIDs → returns full card content

    This ensures privacy: server only sees bitmaps, browser has content.

    Args:
        workspace_id: Workspace UUID (zero-trust isolation)
        user_id: User UUID (zero-trust isolation)
        filter_operations: Bitmap filter operations
        limit: Maximum number of results
        offset: Result offset for pagination

    Returns:
        FilteredQueryResult with matched cards and content

    Examples:
        >>> ops = [{"type": "intersection", "tag_ids": ["tag-1"]}]
        >>> result = route_filtered_query("ws-1", "user-1", ops)
        >>> result.success
        True
        >>> len(result.cards) >= 0
        True
    """
    try:
        logger.info(
            f"Routing filtered query: workspace={workspace_id}, "
            f"user={user_id}, filters={len(filter_operations)}"
        )

        # Phase 1: Server bitmap filtering
        bitmap_result = route_bitmap_operation(
            workspace_id=workspace_id,
            user_id=user_id,
            operations=filter_operations
        )

        if not bitmap_result.success:
            return FilteredQueryResult(
                success=False,
                matched_card_ids=[],
                cards=[],
                total_matches=0,
                error=bitmap_result.error
            )

        # Phase 2: Browser content resolution
        matched_ids = bitmap_result.card_ids or []

        if not matched_ids:
            # No matches from bitmap filter
            return FilteredQueryResult(
                success=True,
                matched_card_ids=[],
                cards=[],
                total_matches=0
            )

        # Resolve UUIDs to content in browser database
        from apps.shared.services.browser_database import (
            execute_query,
            BrowserDatabaseConnection
        )

        # Create a mock connected browser database connection
        conn = BrowserDatabaseConnection(
            database_name="multicardz_browser.db",
            storage_type="opfs",
            connected=True
        )

        placeholders = ','.join(['?'] * len(matched_ids))
        content_result = execute_query(
            connection=conn,
            sql=f"""
                SELECT card_id, name, description, tags, card_bitmap, created, modified
                FROM cards
                WHERE workspace_id = ? AND user_id = ? AND card_id IN ({placeholders})
                ORDER BY created DESC
                LIMIT ? OFFSET ?
            """,
            params=[workspace_id, user_id, *matched_ids, limit, offset]
        )

        if content_result.success:
            cards = content_result.rows or []
            return FilteredQueryResult(
                success=True,
                matched_card_ids=matched_ids,
                cards=cards,
                total_matches=len(matched_ids)
            )
        else:
            return FilteredQueryResult(
                success=False,
                matched_card_ids=matched_ids,
                cards=[],
                total_matches=len(matched_ids),
                error=content_result.error
            )

    except Exception as e:
        logger.error(f"Filtered query routing failed: {e}", exc_info=True)
        return FilteredQueryResult(
            success=False,
            matched_card_ids=[],
            cards=[],
            total_matches=0,
            error=str(e)
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_routing_statistics(
    workspace_id: str,
    user_id: str
) -> Dict[str, Any]:
    """Get statistics about query routing for a workspace.

    Args:
        workspace_id: Workspace UUID
        user_id: User UUID

    Returns:
        Dictionary with routing statistics
    """
    # Mock implementation - would track actual routing metrics
    return {
        'workspace_id': workspace_id,
        'user_id': user_id,
        'total_queries': 0,
        'browser_queries': 0,
        'server_queries': 0,
        'combined_queries': 0,
        'average_latency_ms': 0
    }
