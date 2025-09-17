"""
Card Service Layer for MultiCardz™.

Flattened functional service layer with pure functions and explicit connection passing.
No classes, no mutable state, no OOP overhead - optimized for universe-scale operations.

Target file size: ~500 lines (following architectural guidelines)
"""

import json
import logging
import uuid
from collections import namedtuple
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from apps.shared.services.database_storage import (
    CardNotFoundError,
    DatabaseConfig,
    DatabaseConnection,
    DatabaseStorageError,
    TagWithCount,
    UserPreferencesNotFoundError,
    create_database_connection,
    create_tag_count_tuples_from_database,
    delete_card,
    get_database_statistics,
    initialize_database_schema,
    load_all_card_summaries,
    load_card_detail,
    load_card_summary,
    load_user_preferences,
    save_card_detail,
    save_card_summary,
    save_user_preferences,
    stream_card_summaries,
)
from apps.shared.services.set_operations_unified import (
    OperationResult,
    OperationSequence,
    apply_unified_operations,
    clear_unified_cache,
    get_unified_metrics,
)

# Performance tracking
logger = logging.getLogger(__name__)

# Immutable Data Structures (replacing Pydantic models)
CardSummaryTuple = namedtuple(
    "CardSummaryTuple",
    ["id", "title", "tags", "created_at", "modified_at", "has_attachments"],
)

CardDetailTuple = namedtuple(
    "CardDetailTuple",
    [
        "id",
        "content",
        "metadata",
        "attachment_count",
        "total_attachment_size",
        "version",
    ],
)

UserPreferencesTuple = namedtuple(
    "UserPreferencesTuple",
    [
        "user_id",
        "theme",
        "cards_per_page",
        "sort_order",
        "show_tags",
        "created_at",
        "updated_at",
    ],
)

# Context Manager for Database Sessions


@contextmanager
def with_db_session(
    config: DatabaseConfig,
) -> Generator[DatabaseConnection, None, None]:
    """
    Pure context manager for database sessions with automatic initialization.

    Yields connection with WAL mode enabled and schema initialized.
    Auto-closes connection on exit.

    Args:
        config: Database configuration tuple

    Yields:
        Configured database connection

    Raises:
        DatabaseStorageError: If connection or initialization fails
    """
    conn = create_database_connection(config)
    try:
        # Enable WAL mode for concurrent access
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")

        # Initialize schema
        initialize_database_schema(conn)
        yield conn
    finally:
        conn.close()


# Pure Functions for Card Operations


def create_card(
    conn: DatabaseConnection, title: str, content: str = "", tags: frozenset[str] = None
) -> str:
    """
    Create new card with two-tier architecture using immutable tuples.

    Args:
        conn: Database connection
        title: Card title
        content: Card content (stored as CardDetail)
        tags: Card tags (stored with CardSummary)

    Returns:
        Card ID

    Raises:
        DatabaseStorageError: If creation fails
    """
    if tags is None:
        tags = frozenset()

    # Generate unique ID
    card_id = str(uuid.uuid4())
    now = datetime.now(UTC)

    # Create immutable card tuples
    card_summary = CardSummaryTuple(
        id=card_id,
        title=title,
        tags=tags,
        created_at=now,
        modified_at=now,
        has_attachments=False,
    )

    card_detail = CardDetailTuple(
        id=card_id,
        content=content,
        metadata={},
        attachment_count=0,
        total_attachment_size=0,
        version=1,
    )

    # Save both tiers (adapters handle tuple conversion)
    save_card_summary(conn, card_summary)
    save_card_detail(conn, card_detail)

    logger.info(f"Created card {card_id}: {title}")
    return card_id


def get_card_summary(conn: DatabaseConnection, card_id: str) -> CardSummaryTuple:
    """
    Get CardSummary for fast display.

    Args:
        conn: Database connection
        card_id: Card identifier

    Returns:
        CardSummaryTuple object

    Raises:
        CardNotFoundError: If card not found
    """
    return load_card_summary(conn, card_id)


def get_card_detail(conn: DatabaseConnection, card_id: str) -> CardDetailTuple:
    """
    Get CardDetail on-demand for editing/viewing.

    Args:
        conn: Database connection
        card_id: Card identifier

    Returns:
        CardDetailTuple object

    Raises:
        CardNotFoundError: If card not found
    """
    return load_card_detail(conn, card_id)


def get_all_card_summaries(
    conn: DatabaseConnection, limit: int | None = None
) -> frozenset[CardSummaryTuple]:
    """
    Get all CardSummary objects for set operations.

    Args:
        conn: Database connection
        limit: Maximum number of cards to load

    Returns:
        Immutable set of CardSummaryTuple objects
    """
    return load_all_card_summaries(conn, limit)


def update_card_summary(
    conn: DatabaseConnection,
    card_id: str,
    title: str | None = None,
    tags: frozenset[str] | None = None,
) -> CardSummaryTuple:
    """
    Update CardSummary fields immutably.

    Args:
        conn: Database connection
        card_id: Card identifier
        title: New title (optional)
        tags: New tags (optional)

    Returns:
        Updated CardSummaryTuple

    Raises:
        CardNotFoundError: If card not found
    """
    # Load existing card
    existing = load_card_summary(conn, card_id)

    # Create updated version using _replace
    updated = existing._replace(
        title=title if title is not None else existing.title,
        tags=tags if tags is not None else existing.tags,
        modified_at=datetime.now(UTC),
    )

    # Save updated card
    save_card_summary(conn, updated)

    logger.info(f"Updated CardSummary {card_id}")
    return updated


def update_card_detail(
    conn: DatabaseConnection,
    card_id: str,
    content: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CardDetailTuple:
    """
    Update CardDetail fields immutably.

    Args:
        conn: Database connection
        card_id: Card identifier
        content: New content (optional)
        metadata: New metadata (optional)

    Returns:
        Updated CardDetailTuple

    Raises:
        CardNotFoundError: If card not found
    """
    # Load existing card detail
    existing = load_card_detail(conn, card_id)

    # Create updated version using _replace
    updated = existing._replace(
        content=content if content is not None else existing.content,
        metadata=metadata if metadata is not None else existing.metadata,
        version=existing.version + 1,  # Increment version
    )

    # Save updated card detail
    save_card_detail(conn, updated)

    logger.info(f"Updated CardDetail {card_id}")
    return updated


def remove_card(conn: DatabaseConnection, card_id: str) -> bool:
    """
    Delete card and all associated data.

    Args:
        conn: Database connection
        card_id: Card identifier

    Returns:
        True if deleted, False if not found
    """
    return delete_card(conn, card_id)


def filter_cards_with_operations_streamed(
    conn: DatabaseConnection,
    operations: OperationSequence,
    *,
    user_preferences: dict[str, Any] | None = None,
    use_cache: bool = True,
    optimize_order: bool = True,
    batch_size: int = 10000,
) -> OperationResult:
    """
    Filter cards using set operations with streaming for universe-scale datasets.

    Uses database-generated tag counts and streaming to handle millions of cards
    without memory exhaustion.

    Args:
        conn: Database connection
        operations: Set operations to apply
        user_preferences: User preferences dict for result ordering
        use_cache: Enable operation caching
        optimize_order: Enable tag selectivity optimization
        batch_size: Number of cards per batch for streaming

    Returns:
        OperationResult with filtered cards and performance metrics
    """
    # Generate tag count tuples from database for optimization
    tag_count_tuples = create_tag_count_tuples_from_database(
        conn, use_normalized_schema=True
    )
    tag_count_map = {tag: count for tag, count in tag_count_tuples}

    # Optimize operation order by selectivity (most selective first)
    if optimize_order:
        sorted_operations = []
        for op_type, op_tags in operations:
            # Calculate average selectivity for this operation
            total_selectivity = sum(
                tag_count_map.get(tag if isinstance(tag, str) else tag[0], 1)
                for tag in op_tags
            )
            avg_selectivity = (
                total_selectivity / len(op_tags) if op_tags else float("inf")
            )
            sorted_operations.append((avg_selectivity, op_type, op_tags))

        sorted_operations.sort(key=lambda x: x[0])  # Sort by selectivity ascending
        operations = [(op_type, op_tags) for _, op_type, op_tags in sorted_operations]

    # Convert operations to use database-generated tag counts
    optimized_operations = []
    for operation_type, operation_tags in operations:
        updated_tags = []
        for tag_item in operation_tags:
            if isinstance(tag_item, tuple):
                tag_name, _ = tag_item  # Ignore provided count
            else:
                tag_name = tag_item

            # Use database count or default to 1 if tag not found
            count = tag_count_map.get(tag_name, 1)
            updated_tags.append((tag_name, count))

        optimized_operations.append((operation_type, updated_tags))

    # For large datasets, use streaming approach
    total_cards = get_database_statistics(conn).get("card_summaries_count", 0)

    if total_cards > batch_size:
        # Stream cards in batches to avoid memory exhaustion
        all_cards = []
        for batch in stream_card_summaries(conn, batch_size):
            all_cards.extend(batch)
        all_cards = frozenset(all_cards)
    else:
        # Small dataset, load all at once
        all_cards = get_all_card_summaries(conn)

    # Apply set operations with optimized tag counts
    result = apply_unified_operations(
        cards=all_cards,
        operations=optimized_operations,
        use_cache=use_cache,
        optimize_order=False,  # Already optimized above
        user_preferences=user_preferences,
    )

    logger.info(
        f"Streamed & filtered {len(all_cards)} cards to {len(result.cards)} results "
        f"in {result.execution_time_ms:.2f}ms with {len(operations)} operations (batch_size: {batch_size})"
    )

    return result


def get_tag_statistics(conn: DatabaseConnection) -> list[TagWithCount]:
    """
    Get tag usage statistics for analysis and optimization.

    Args:
        conn: Database connection

    Returns:
        List of (tag, count) tuples sorted by frequency
    """
    return create_tag_count_tuples_from_database(conn, use_normalized_schema=True)


def store_user_preferences(
    conn: DatabaseConnection, preferences: dict[str, Any]
) -> str:
    """
    Save user preferences for server-side application.

    Args:
        conn: Database connection
        preferences: User preferences dictionary

    Returns:
        User ID
    """
    return save_user_preferences(conn, preferences)


def load_user_preferences(conn: DatabaseConnection, user_id: str) -> dict[str, Any]:
    """
    Get user preferences for server-side HTML generation.

    Args:
        conn: Database connection
        user_id: User identifier

    Returns:
        User preferences dictionary (defaults if none exist)
    """
    try:
        # Import the function from database_storage to avoid naming conflict
        from apps.shared.services.database_storage import (
            load_user_preferences as db_load_user_preferences,
        )

        return db_load_user_preferences(conn, user_id)
    except UserPreferencesNotFoundError:
        # Return default preferences if none exist
        return {"sort_by": "modified_at", "sort_order": "desc", "items_per_page": 50}


def get_full_statistics(conn: DatabaseConnection) -> dict[str, Any]:
    """
    Get comprehensive service statistics.

    Args:
        conn: Database connection

    Returns:
        Dictionary with database and operation statistics
    """
    db_stats = get_database_statistics(conn)
    unified_stats = get_unified_metrics()

    return {
        "database": db_stats,
        "operations": {
            "cache_hit_rate": unified_stats.cache_hit_rate,
            "total_time_ms": unified_stats.total_time_ms,
            "processing_mode": unified_stats.processing_mode,
            "parallel_workers": unified_stats.parallel_workers,
            "operations_count": unified_stats.operations_count,
        },
        "tag_statistics": len(get_tag_statistics(conn)),
    }


def clear_all_caches() -> None:
    """Clear all caches for fresh performance measurements."""
    clear_unified_cache()
    logger.info("Cleared all service caches")


def bulk_import_cards_optimized(
    conn: DatabaseConnection, cards_data: list[dict[str, Any]], batch_size: int = 10000
) -> list[str]:
    """
    Import multiple cards efficiently with Turso optimizations.

    Args:
        conn: Database connection
        cards_data: List of card data dictionaries with 'title', 'content', 'tags'
        batch_size: Number of cards per batch for memory management

    Returns:
        List of created card IDs

    Raises:
        DatabaseStorageError: If import fails
    """
    # Validate all cards before starting transaction
    validated_summaries = []
    validated_details = []

    try:
        for card_data in cards_data:
            title = card_data["title"]
            content = card_data.get("content", "")
            tags = frozenset(card_data.get("tags", []))

            # Validate before creating to catch errors early
            if not title or not title.strip():
                raise ValueError("Card title cannot be empty")

            # Create immutable tuples
            card_id = str(uuid.uuid4())
            now = datetime.now(UTC)

            card_summary = CardSummaryTuple(
                id=card_id,
                title=title,
                tags=tags,
                created_at=now,
                modified_at=now,
                has_attachments=False,
            )

            card_detail = CardDetailTuple(
                id=card_id,
                content=content,
                metadata={},
                attachment_count=0,
                total_attachment_size=0,
                version=1,
            )

            validated_summaries.append(card_summary)
            validated_details.append(card_detail)

    except Exception as e:
        logger.error(f"Validation failed before transaction: {e}")
        raise DatabaseStorageError(f"Bulk import validation failed: {e}")

    # Use individual create functions for now (until we implement bulk_load_card_details)
    try:
        created_ids = []

        for card_data in cards_data:
            title = card_data["title"]
            content = card_data.get("content", "")
            tags = frozenset(card_data.get("tags", []))

            card_id = create_card(conn, title, content, tags)
            created_ids.append(card_id)

        logger.info(f"Bulk imported {len(created_ids)} cards")
        return created_ids

    except Exception as e:
        logger.error(f"Bulk import failed: {e}")
        raise DatabaseStorageError(f"Bulk import failed: {e}")


def export_cards_data_streamed(
    conn: DatabaseConnection, card_ids: list[str] | None = None, batch_size: int = 1000
) -> Generator[dict[str, Any], None, None]:
    """
    Export card data for backup or migration using streaming.

    Args:
        conn: Database connection
        card_ids: Specific card IDs to export (None for all)
        batch_size: Number of cards per batch

    Yields:
        Card data dictionaries
    """
    if card_ids is None:
        # Stream all cards
        for batch in stream_card_summaries(conn, batch_size):
            card_ids_batch = [card.id for card in batch]
            yield from _export_cards_batch(conn, card_ids_batch)
    else:
        # Export specific cards in batches
        for i in range(0, len(card_ids), batch_size):
            batch_ids = card_ids[i : i + batch_size]
            yield from _export_cards_batch(conn, batch_ids)


def _export_cards_batch(
    conn: DatabaseConnection, card_ids: list[str]
) -> Generator[dict[str, Any], None, None]:
    """Helper function to export a batch of cards."""
    for card_id in card_ids:
        try:
            summary = get_card_summary(conn, card_id)
            detail = get_card_detail(conn, card_id)

            card_data = {
                "id": summary.id,
                "title": summary.title,
                "tags": list(summary.tags),
                "content": detail.content,
                "metadata": detail.metadata,
                "created_at": summary.created_at.isoformat()
                if summary.created_at
                else None,
                "modified_at": summary.modified_at.isoformat()
                if summary.modified_at
                else None,
                "has_attachments": summary.has_attachments,
                "attachment_count": detail.attachment_count,
                "version": detail.version,
            }

            yield card_data

        except CardNotFoundError:
            logger.warning(f"Card {card_id} not found during export, skipping")
            continue


# Utility Functions for Common Operations


def quick_card_filter(
    config: DatabaseConfig,
    filter_tags: list[str],
    union_tags: list[str] = None,
    user_id: str = None,
) -> list[CardSummaryTuple]:
    """
    Quick utility function for simple card filtering using pure functions.

    Args:
        config: Database configuration tuple
        filter_tags: Tags for intersection filtering
        union_tags: Tags for union filtering
        user_id: User ID for preferences

    Returns:
        List of filtered cards
    """
    if union_tags is None:
        union_tags = []

    # Create operations sequence (mock counts will be replaced with DB counts)
    operations = []
    if filter_tags:
        filter_tuples = [(tag, 100) for tag in filter_tags]
        operations.append(("intersection", filter_tuples))

    if union_tags:
        union_tuples = [(tag, 100) for tag in union_tags]
        operations.append(("union", union_tuples))

    # Get user preferences if provided
    user_preferences = None
    if user_id:
        with with_db_session(config) as conn:
            try:
                user_preferences = load_user_preferences(conn, user_id)
            except UserPreferencesNotFoundError:
                pass

    # Execute filtering using streaming operations
    with with_db_session(config) as conn:
        result = filter_cards_with_operations_streamed(
            conn=conn, operations=operations, user_preferences=user_preferences
        )

    return list(result.cards)


def create_database_config(
    db_path: Path,
    enable_foreign_keys: bool = True,
    timeout: float = 30.0,
    check_same_thread: bool = False,
    max_attachment_size_mb: int = 100,
) -> DatabaseConfig:
    """
    Create database configuration tuple for pure function usage.

    Args:
        db_path: Path to SQLite database file
        enable_foreign_keys: Enable foreign key constraints
        timeout: Connection timeout in seconds
        check_same_thread: Check same thread for connection
        max_attachment_size_mb: Maximum attachment size in MB

    Returns:
        Database configuration tuple
    """
    return (
        db_path,
        enable_foreign_keys,
        timeout,
        check_same_thread,
        max_attachment_size_mb,
    )


# High-Level Convenience Functions


def create_card_simple(
    config: DatabaseConfig, title: str, content: str = "", tags: list[str] = None
) -> str:
    """
    Convenience function to create a card with automatic session management.

    Args:
        config: Database configuration tuple
        title: Card title
        content: Card content
        tags: List of tag strings

    Returns:
        Created card ID
    """
    with with_db_session(config) as conn:
        return create_card(conn, title, content, frozenset(tags or []))


def get_cards_by_tags(
    config: DatabaseConfig, tags: list[str], batch_size: int = 10000
) -> list[CardSummaryTuple]:
    """
    Convenience function to get cards filtered by tags.

    Args:
        config: Database configuration tuple
        tags: List of tags to filter by
        batch_size: Batch size for streaming

    Returns:
        List of matching cards
    """
    operations = [("intersection", [(tag, 1) for tag in tags])]

    with with_db_session(config) as conn:
        result = filter_cards_with_operations_streamed(
            conn=conn, operations=operations, batch_size=batch_size
        )

    return list(result.cards)


def export_all_cards(
    config: DatabaseConfig, output_path: Path, batch_size: int = 1000
) -> int:
    """
    Convenience function to export all cards to JSON file.

    Args:
        config: Database configuration tuple
        output_path: Output file path
        batch_size: Batch size for streaming export

    Returns:
        Number of cards exported
    """

    exported_count = 0

    with with_db_session(config) as conn:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("[\n")
            first_card = True

            for card_data in export_cards_data_streamed(conn, batch_size=batch_size):
                if not first_card:
                    f.write(",\n")
                else:
                    first_card = False

                json.dump(card_data, f, indent=2, ensure_ascii=False)
                exported_count += 1

            f.write("\n]")

    logger.info(f"Exported {exported_count} cards to {output_path}")
    return exported_count


def import_cards_from_json(
    config: DatabaseConfig, input_path: Path, batch_size: int = 10000
) -> list[str]:
    """
    Convenience function to import cards from JSON file.

    Args:
        config: Database configuration tuple
        input_path: Input JSON file path
        batch_size: Batch size for bulk import

    Returns:
        List of created card IDs
    """

    with open(input_path, encoding="utf-8") as f:
        cards_data = json.load(f)

    with with_db_session(config) as conn:
        return bulk_import_cards_optimized(conn, cards_data, batch_size)


def get_system_stats(config: DatabaseConfig) -> dict[str, Any]:
    """
    Convenience function to get comprehensive system statistics.

    Args:
        config: Database configuration tuple

    Returns:
        Complete system statistics
    """
    with with_db_session(config) as conn:
        return get_full_statistics(conn)


# Backward Compatibility Functions for Tests


class CardServiceCompat:
    """Backward compatibility class that wraps functional card service."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connection = None

    def __enter__(self):
        self.connection = create_database_connection(self.config)
        self.connection.execute("PRAGMA journal_mode = WAL")
        initialize_database_schema(self.connection)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()

    def bulk_import_cards(self, cards_data):
        """Backward compatibility method for bulk_import_cards."""
        return bulk_import_cards_optimized(self.connection, cards_data)

    def get_all_cards(self):
        """Backward compatibility method for get_all_cards."""
        return get_all_card_summaries(self.connection)

    def get_all_card_summaries(self):
        """Backward compatibility method for get_all_card_summaries."""
        return get_all_card_summaries(self.connection)

    def get_card_summary(self, card_id):
        """Backward compatibility method for get_card_summary."""
        return get_card_summary(self.connection, card_id)

    def get_card_detail(self, card_id):
        """Backward compatibility method for get_card_detail."""
        return get_card_detail(self.connection, card_id)

    def get_tag_statistics(self):
        """Backward compatibility method for get_tag_statistics."""
        return create_tag_count_tuples_from_database(
            self.connection, use_normalized_schema=False
        )

    def filter_cards(self, operations, user_preferences=None):
        """Backward compatibility method for filter_cards."""
        return filter_cards_with_operations_streamed(
            self.connection, operations, user_preferences=user_preferences
        )

    def filter_cards_with_operations(
        self, operations, user_preferences=None, optimize_order=True
    ):
        """Backward compatibility method for filter_cards_with_operations."""
        return filter_cards_with_operations_streamed(
            self.connection,
            operations,
            user_preferences=user_preferences,
            optimize_order=optimize_order,
        )

    def create_card(self, title, content="", tags=None):
        """Backward compatibility method for create_card."""
        if tags is None:
            tags = frozenset()
        elif isinstance(tags, list):
            tags = frozenset(tags)
        return create_card(self.connection, title, content, tags)

    def save_user_preferences(self, preferences):
        """Backward compatibility method for save_user_preferences."""
        return save_user_preferences(self.connection, preferences)

    def load_user_preferences(self, user_id):
        """Backward compatibility method for load_user_preferences."""
        return load_user_preferences(self.connection, user_id)

    def get_user_preferences(self, user_id):
        """Backward compatibility method for get_user_preferences (alias for load_user_preferences)."""
        return load_user_preferences(self.connection, user_id)

    def delete_card(self, card_id):
        """Backward compatibility method for delete_card."""
        return remove_card(self.connection, card_id)

    def get_service_statistics(self):
        """Backward compatibility method for get_service_statistics."""
        return get_full_statistics(self.connection)

    def export_cards_data(self, card_ids=None, batch_size=1000):
        """Backward compatibility method for export_cards_data."""
        return list(export_cards_data_streamed(self.connection, card_ids, batch_size))

    def clear_all_caches(self):
        """Backward compatibility method for clear_all_caches."""
        clear_unified_cache()
        logger.info("Cleared all service caches")


def create_card_service(db_path: Path, **db_options):
    """
    Backward compatibility function that returns a context manager.

    Note: This is a compatibility layer for tests. The actual implementation
    is now purely functional and doesn't use classes.

    Args:
        db_path: Path to SQLite database file
        **db_options: Additional database configuration options

    Returns:
        Context manager that yields a service-like object
    """
    # Convert old-style options to new tuple format
    enable_foreign_keys = db_options.get("enable_foreign_keys", True)
    timeout = db_options.get("timeout", 30.0)
    check_same_thread = db_options.get("check_same_thread", False)
    max_attachment_size_mb = db_options.get("max_attachment_size_mb", 100)

    config = create_database_config(
        db_path=db_path,
        enable_foreign_keys=enable_foreign_keys,
        timeout=timeout,
        check_same_thread=check_same_thread,
        max_attachment_size_mb=max_attachment_size_mb,
    )

    return CardServiceCompat(config)
