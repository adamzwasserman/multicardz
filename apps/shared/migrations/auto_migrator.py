"""
Fast migration executor with minimal overhead.

Streamlined migration application focusing on:
- Fast SQL file execution (bulk executescript)
- Minimal result objects (only essential data)
- Clean transaction handling
- Integration with in-memory cache

Performance target: 5-10ms per migration (one-time cost).
"""
import sqlite3
import time
from pathlib import Path
from typing import Tuple, Optional
import logging

from .types import Migration, MigrationResult
from .fast_detector import mark_migration_applied

logger = logging.getLogger(__name__)


# ============================================================================
# MIGRATION DEFINITIONS (immutable registry)
# ============================================================================

# All available migrations in application order
MIGRATIONS: Tuple[Migration, ...] = (
    Migration(
        version=1,
        sql_file="001_zero_trust_schema.sql"
    ),
    Migration(
        version=2,
        sql_file="002_add_bitmap_sequences.sql"
    ),
)


def get_migration_by_version(version: int) -> Optional[Migration]:
    """
    Get migration by version number (simple iteration - only 2-10 migrations).

    Performance: O(n) but n is tiny (2-10), so <100ns.

    Args:
        version: Migration version number

    Returns:
        Migration object or None if not found
    """
    for migration in MIGRATIONS:
        if migration.version == version:
            return migration
    return None


# ============================================================================
# FAST MIGRATION EXECUTION
# ============================================================================

def apply_migration_fast(
    connection: sqlite3.Connection,
    version: int,
    sql_base_dir: Path
) -> Tuple[bool, float, Optional[str]]:
    """
    Fast migration application with minimal overhead.

    Returns tuple instead of complex object: (success, duration_ms, error_msg).

    Performance: 5-10ms for typical migration (one-time cost).

    Optimizations:
    - Direct file read (no abstraction layers)
    - Bulk executescript (fastest SQLite execution)
    - Simple tuple return (no object allocation)
    - Single commit at end

    Args:
        connection: SQLite database connection
        version: Migration version to apply
        sql_base_dir: Base directory containing SQL files

    Returns:
        Tuple of (success: bool, duration_ms: float, error: Optional[str])

    Examples:
        >>> success, duration, error = apply_migration_fast(conn, 2, Path("migrations"))
        >>> if success:
        ...     print(f"Migration applied in {duration}ms")
    """
    start = time.perf_counter()

    try:
        # Get migration metadata
        migration = get_migration_by_version(version)
        if migration is None:
            duration = (time.perf_counter() - start) * 1000
            return (False, duration, f"Migration {version} not found")

        # Direct file read - no helper functions
        sql_path = sql_base_dir / migration.sql_file
        if not sql_path.exists():
            duration = (time.perf_counter() - start) * 1000
            return (False, duration, f"Migration file not found: {sql_path}")

        sql = sql_path.read_text(encoding="utf-8")

        # Fast bulk execution (executescript is fastest for multiple statements)
        connection.executescript(sql)

        # Record in schema_version table (create if needed)
        _ensure_schema_version_table(connection)
        connection.execute(
            "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
            (version,)
        )

        # Single commit at end
        connection.commit()

        # Update in-memory cache
        mark_migration_applied(version)

        duration = (time.perf_counter() - start) * 1000
        logger.info(f"Migration {version} applied in {duration:.2f}ms")

        return (True, duration, None)

    except Exception as e:
        # Rollback on any error
        connection.rollback()
        duration = (time.perf_counter() - start) * 1000

        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Migration {version} failed: {error_msg}")

        return (False, duration, error_msg)


def apply_migration_with_result(
    connection: sqlite3.Connection,
    version: int,
    sql_base_dir: Path
) -> MigrationResult:
    """
    Apply migration and return MigrationResult object.

    Wrapper around apply_migration_fast for callers that prefer typed results.

    Args:
        connection: SQLite database connection
        version: Migration version to apply
        sql_base_dir: Base directory containing SQL files

    Returns:
        MigrationResult with success status and metrics
    """
    success, duration_ms, error = apply_migration_fast(connection, version, sql_base_dir)

    return MigrationResult(
        success=success,
        version=version,
        duration_ms=duration_ms,
        error=error
    )


def _ensure_schema_version_table(connection: sqlite3.Connection) -> None:
    """
    Ensure schema_version table exists (internal helper).

    Creates table if missing. Idempotent - safe to call multiple times.

    Performance: <1ms (CREATE IF NOT EXISTS is fast).

    Args:
        connection: SQLite database connection
    """
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


# ============================================================================
# DEPENDENCY RESOLUTION (simple topological sort for small DAGs)
# ============================================================================

def get_migration_dependencies(version: int) -> Tuple[int, ...]:
    """
    Get migration dependencies in application order.

    For our current schema:
    - Migration 1 has no dependencies
    - Migration 2 depends on migration 1

    Simple linear dependency chain for now. If we need complex DAG resolution
    later, we can implement proper topological sort.

    Performance: O(1) for current simple dependencies.

    Args:
        version: Migration version to get dependencies for

    Returns:
        Tuple of version numbers that must be applied first (in order)

    Examples:
        >>> get_migration_dependencies(1)
        ()
        >>> get_migration_dependencies(2)
        (1,)
    """
    if version <= 1:
        return ()

    # Simple linear dependency: all earlier versions
    # For version 2, depends on version 1
    # For version 3, would depend on versions 1 and 2
    return tuple(range(1, version))


def apply_migration_with_dependencies(
    connection: sqlite3.Connection,
    version: int,
    sql_base_dir: Path,
    *,
    skip_applied: bool = True
) -> Tuple[bool, list[MigrationResult]]:
    """
    Apply migration and all dependencies in correct order.

    Returns (overall_success, list_of_results).

    Args:
        connection: SQLite database connection
        version: Target migration version to apply
        sql_base_dir: Base directory containing SQL files
        skip_applied: Skip migrations that are already applied (default True)

    Returns:
        Tuple of (success: bool, results: list[MigrationResult])
        success is True only if all migrations succeeded

    Examples:
        >>> success, results = apply_migration_with_dependencies(conn, 2, Path("migrations"))
        >>> if success:
        ...     print(f"Applied {len(results)} migrations")
    """
    results = []

    # Get dependencies + target migration
    deps = get_migration_dependencies(version)
    all_versions = (*deps, version)

    # Apply each migration in order
    for v in all_versions:
        # Skip if already applied (unless explicitly requested)
        if skip_applied:
            from .fast_detector import is_migration_applied
            if is_migration_applied(v):
                logger.debug(f"Migration {v} already applied, skipping")
                continue

        # Apply migration
        result = apply_migration_with_result(connection, v, sql_base_dir)
        results.append(result)

        # Stop on first failure
        if not result.success:
            return (False, results)

    # All succeeded
    return (True, results)


# ============================================================================
# EVENT LOGGING (pure function for event construction)
# ============================================================================

def create_migration_event(
    result: MigrationResult,
    *,
    user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    request_path: Optional[str] = None
) -> dict:
    """
    Create migration event dictionary for audit trail.

    Pure function - no side effects, just data transformation.

    Args:
        result: Migration execution result
        user_id: Optional user ID for audit trail
        workspace_id: Optional workspace ID for audit trail
        request_path: Optional request path that triggered migration

    Returns:
        Event dictionary ready for logging/event store

    Examples:
        >>> event = create_migration_event(result, user_id="user-123")
        >>> logger.info("Migration event", extra=event)
    """
    from datetime import datetime

    return {
        "event_type": "database_migration",
        "timestamp": datetime.utcnow().isoformat(),
        "migration_version": result.version,
        "success": result.success,
        "duration_ms": result.duration_ms,
        "error": result.error,
        "user_id": user_id,
        "workspace_id": workspace_id,
        "request_path": request_path,
    }


def log_migration_event(
    result: MigrationResult,
    *,
    user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    request_path: Optional[str] = None
) -> None:
    """
    Log migration event (side effect - logging output).

    Creates event dict and logs it. In future, could also send to event store.

    Args:
        result: Migration execution result
        user_id: Optional user ID for audit trail
        workspace_id: Optional workspace ID for audit trail
        request_path: Optional request path that triggered migration
    """
    event = create_migration_event(
        result,
        user_id=user_id,
        workspace_id=workspace_id,
        request_path=request_path
    )

    if result.success:
        logger.info(
            f"Migration {result.version} applied in {result.duration_ms:.2f}ms",
            extra=event
        )
    else:
        logger.error(
            f"Migration {result.version} failed: {result.error}",
            extra=event
        )

    # TODO: Send to event store (RedPanda/Kafka)
    # await send_to_event_store(event)
