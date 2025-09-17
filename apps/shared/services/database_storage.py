"""
Database Storage Layer for MultiCardz Two-Tier Architecture.

This module implements the storage layer with CardSummary/CardDetail separation,
tag count tuple generation for 80/20 optimization, and user preferences persistence.

Target file size: ~500 lines (following architectural guidelines)
"""

import json
import logging
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, NamedTuple

from apps.shared.models.card import CardDetail, CardSummary
from apps.shared.models.user_preferences import UserPreferences

# Type aliases for clarity
TagWithCount = tuple[str, int]
DatabaseConnection = sqlite3.Connection

# Config as tuple for zero allocations: (db_path, enable_foreign_keys, timeout, check_same_thread, max_attachment_size_mb)
DatabaseConfig = tuple[Path, bool, float, bool, int]


# Named tuple for structured card summaries (alternative to Pydantic for performance)
class CardSummaryTuple(NamedTuple):
    id: str
    title: str
    tags: frozenset
    created_at: datetime
    modified_at: datetime
    has_attachments: bool


# Performance tracking
logger = logging.getLogger(__name__)


class DatabaseStorageError(Exception):
    """Base exception for database storage operations."""

    pass


class CardNotFoundError(DatabaseStorageError):
    """Raised when a card is not found in the database."""

    pass


class UserPreferencesNotFoundError(DatabaseStorageError):
    """Raised when user preferences are not found."""

    pass


def create_database_connection(config: DatabaseConfig) -> DatabaseConnection:
    """
    Create SQLite database connection with optimized settings.

    Args:
        config: Database configuration tuple (db_path, enable_foreign_keys, timeout, check_same_thread, max_attachment_size_mb)

    Returns:
        Configured SQLite connection

    Raises:
        DatabaseStorageError: If connection fails
    """
    try:
        (
            db_path,
            enable_foreign_keys,
            timeout,
            check_same_thread,
            max_attachment_size_mb,
        ) = config

        conn = sqlite3.connect(
            str(db_path), timeout=timeout, check_same_thread=check_same_thread
        )

        if enable_foreign_keys:
            conn.execute("PRAGMA foreign_keys = ON")

        # Log max attachment size for bulk operations
        logger.debug(
            f"Database connection created with max_attachment_size: {max_attachment_size_mb}MB"
        )

        # Performance optimizations
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA mmap_size = 268435456")  # 256MB

        return conn

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to create database connection: {e}")


def initialize_database_schema(conn: DatabaseConnection) -> None:
    """
    Initialize database schema for two-tier architecture.

    Args:
        conn: Database connection

    Raises:
        DatabaseStorageError: If schema creation fails
    """
    schema_sql = """
    -- Card Summaries: Minimal data for fast list rendering (~50 bytes)
    CREATE TABLE IF NOT EXISTS card_summaries (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        tags_json TEXT NOT NULL,  -- Keep for backward compatibility during migration
        created_at TEXT NOT NULL,
        modified_at TEXT NOT NULL,
        has_attachments BOOLEAN DEFAULT FALSE
    );

    -- Normalized Tags: Separate table for scale (10M+ tags performance)
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    -- Card-Tag Relations: Many-to-many for efficient queries
    CREATE TABLE IF NOT EXISTS card_tags (
        card_id TEXT NOT NULL,
        tag_id INTEGER NOT NULL,
        FOREIGN KEY (card_id) REFERENCES card_summaries(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id),
        PRIMARY KEY (card_id, tag_id)
    );

    -- Card Details: Full data loaded on-demand
    CREATE TABLE IF NOT EXISTS card_details (
        id TEXT PRIMARY KEY REFERENCES card_summaries(id) ON DELETE CASCADE,
        content TEXT DEFAULT '',
        metadata_json TEXT DEFAULT '{}',
        attachment_count INTEGER DEFAULT 0,
        total_attachment_size INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1
    );

    -- User Preferences: Server-side preference application
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id TEXT PRIMARY KEY,
        preferences_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        version INTEGER DEFAULT 1
    );

    -- Attachments: BLOB storage for self-contained deployment
    CREATE TABLE IF NOT EXISTS attachments (
        id TEXT PRIMARY KEY,
        card_id TEXT REFERENCES card_summaries(id) ON DELETE CASCADE,
        filename TEXT NOT NULL,
        content_type TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        data BLOB NOT NULL,
        uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    -- Indexes for performance optimization
    CREATE INDEX IF NOT EXISTS idx_card_summaries_tags ON card_summaries(tags_json);
    CREATE INDEX IF NOT EXISTS idx_card_summaries_modified ON card_summaries(modified_at);
    CREATE INDEX IF NOT EXISTS idx_attachments_card_id ON attachments(card_id);

    -- Indexes for normalized tag schema (Turso-optimized)
    CREATE INDEX IF NOT EXISTS idx_card_tags_card ON card_tags(card_id);
    CREATE INDEX IF NOT EXISTS idx_card_tags_tag ON card_tags(tag_id);
    CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
    """

    try:
        conn.executescript(schema_sql)
        conn.commit()
        logger.info("Database schema initialized successfully")

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to initialize database schema: {e}")


def save_card_summary(conn: DatabaseConnection, card: CardSummary) -> str:
    """
    Save CardSummary to database for fast list operations.

    Args:
        conn: Database connection
        card: CardSummary to save

    Returns:
        Card ID

    Raises:
        DatabaseStorageError: If save operation fails
    """
    try:
        # Convert datetime to ISO string for SQLite compatibility
        created_at = (
            card.created_at.isoformat()
            if isinstance(card.created_at, datetime)
            else card.created_at
        )
        modified_at = (
            card.modified_at.isoformat()
            if isinstance(card.modified_at, datetime)
            else card.modified_at
        )

        conn.execute(
            """INSERT OR REPLACE INTO card_summaries
               (id, title, tags_json, created_at, modified_at, has_attachments)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                card.id,
                card.title,
                json.dumps(sorted(list(card.tags))),  # Sort for consistent storage
                created_at,
                modified_at,
                card.has_attachments,
            ),
        )
        conn.commit()

        logger.debug(f"Saved CardSummary {card.id}: {card.title}")
        return card.id

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to save CardSummary {card.id}: {e}")


def load_card_summary(conn: DatabaseConnection, card_id: str) -> CardSummary:
    """
    Load CardSummary by ID for fast display.

    Args:
        conn: Database connection
        card_id: Card identifier

    Returns:
        CardSummary object

    Raises:
        CardNotFoundError: If card not found
        DatabaseStorageError: If load operation fails
    """
    try:
        cursor = conn.execute(
            """SELECT id, title, tags_json, created_at, modified_at, has_attachments
               FROM card_summaries WHERE id = ?""",
            (card_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise CardNotFoundError(f"CardSummary {card_id} not found")

        # Parse stored datetime strings back to datetime objects
        created_at = (
            datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3]
        )
        modified_at = (
            datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4]
        )

        return CardSummary(
            id=row[0],
            title=row[1],
            tags=frozenset(json.loads(row[2])),
            created_at=created_at,
            modified_at=modified_at,
            has_attachments=bool(row[5]),
        )

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to load CardSummary {card_id}: {e}")


def load_all_card_summaries(
    conn: DatabaseConnection, limit: int | None = None
) -> frozenset[CardSummary]:
    """
    Load all CardSummary objects for set operations.

    Args:
        conn: Database connection
        limit: Maximum number of cards to load (None for unlimited)

    Returns:
        Immutable set of CardSummary objects

    Raises:
        DatabaseStorageError: If load operation fails
    """
    try:
        start_time = time.perf_counter()

        query = """SELECT id, title, tags_json, created_at, modified_at, has_attachments
                   FROM card_summaries ORDER BY modified_at DESC"""
        if limit:
            query += f" LIMIT {limit}"

        cursor = conn.execute(query)
        cards = []

        for row in cursor.fetchall():
            # Parse stored datetime strings
            created_at = (
                datetime.fromisoformat(row[3]) if isinstance(row[3], str) else row[3]
            )
            modified_at = (
                datetime.fromisoformat(row[4]) if isinstance(row[4], str) else row[4]
            )

            card = CardSummary(
                id=row[0],
                title=row[1],
                tags=frozenset(json.loads(row[2])),
                created_at=created_at,
                modified_at=modified_at,
                has_attachments=bool(row[5]),
            )
            cards.append(card)

        end_time = time.perf_counter()
        load_time_ms = (end_time - start_time) * 1000

        logger.info(f"Loaded {len(cards)} CardSummary objects in {load_time_ms:.2f}ms")
        return frozenset(cards)

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to load CardSummary objects: {e}")


def save_card_detail(conn: DatabaseConnection, card_detail: CardDetail) -> str:
    """
    Save CardDetail for on-demand loading.

    Args:
        conn: Database connection
        card_detail: CardDetail to save

    Returns:
        Card ID

    Raises:
        DatabaseStorageError: If save operation fails
    """
    try:
        conn.execute(
            """INSERT OR REPLACE INTO card_details
               (id, content, metadata_json, attachment_count, total_attachment_size, version)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                card_detail.id,
                card_detail.content,
                json.dumps(card_detail.metadata),
                card_detail.attachment_count,
                card_detail.total_attachment_size,
                card_detail.version,
            ),
        )
        conn.commit()

        logger.debug(f"Saved CardDetail {card_detail.id}")
        return card_detail.id

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to save CardDetail {card_detail.id}: {e}")


def load_card_detail(conn: DatabaseConnection, card_id: str) -> CardDetail:
    """
    Load CardDetail on-demand by ID.

    Args:
        conn: Database connection
        card_id: Card identifier

    Returns:
        CardDetail object

    Raises:
        CardNotFoundError: If card detail not found
        DatabaseStorageError: If load operation fails
    """
    try:
        cursor = conn.execute(
            """SELECT id, content, metadata_json, attachment_count, total_attachment_size, version
               FROM card_details WHERE id = ?""",
            (card_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise CardNotFoundError(f"CardDetail {card_id} not found")

        return CardDetail(
            id=row[0],
            content=row[1],
            metadata=json.loads(row[2]),
            attachment_count=row[3],
            total_attachment_size=row[4],
            version=row[5],
        )

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to load CardDetail {card_id}: {e}")


def create_tag_count_tuples_from_database(
    conn: DatabaseConnection, use_normalized_schema: bool = True
) -> list[TagWithCount]:
    """
    Create TagWithCount tuples from database for 80/20 optimization.

    CRITICAL: This function generates the (tag, count) tuples required by
    set operations for selectivity ordering and performance optimization.

    Uses SQL-only approach for optimal performance at scale (10M+ cards).

    Args:
        conn: Database connection
        use_normalized_schema: Whether to use normalized tags table (faster for large datasets)

    Returns:
        List of (tag, count) tuples sorted by count ascending (most selective first)

    Raises:
        DatabaseStorageError: If tag analysis fails
    """
    try:
        start_time = time.perf_counter()

        if use_normalized_schema:
            # SQL-only approach using normalized schema (optimal for 10M+ scale)
            cursor = conn.execute("""
                SELECT t.name, COUNT(ct.card_id) as tag_count
                FROM tags t
                LEFT JOIN card_tags ct ON t.id = ct.tag_id
                GROUP BY t.id, t.name
                ORDER BY tag_count ASC
            """)
            tuples = [(name, count) for name, count in cursor.fetchall()]

        else:
            # Fallback to JSON parsing for backward compatibility
            cursor = conn.execute("SELECT tags_json FROM card_summaries")
            tag_counts = {}

            for (tags_json,) in cursor.fetchall():
                tags = json.loads(tags_json)
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Convert to tuples sorted by count ascending (most selective first)
            tuples = [(tag, count) for tag, count in tag_counts.items()]
            tuples.sort(key=lambda x: x[1])  # Sort by count ascending for selectivity

        end_time = time.perf_counter()
        analysis_time_ms = (end_time - start_time) * 1000

        schema_type = "normalized" if use_normalized_schema else "JSON"
        logger.info(
            f"Generated {len(tuples)} tag count tuples ({schema_type}) in {analysis_time_ms:.2f}ms"
        )
        return tuples

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to create tag count tuples: {e}")


def save_user_preferences(
    conn: DatabaseConnection, preferences: UserPreferences
) -> str:
    """
    Save user preferences for server-side application.

    Args:
        conn: Database connection
        preferences: UserPreferences to save

    Returns:
        User ID

    Raises:
        DatabaseStorageError: If save operation fails
    """
    try:
        # Convert preferences to JSON for storage
        preferences_json = preferences.model_dump_json()

        conn.execute(
            """INSERT OR REPLACE INTO user_preferences
               (user_id, preferences_json, updated_at)
               VALUES (?, ?, ?)""",
            (preferences.user_id, preferences_json, datetime.now(UTC).isoformat()),
        )
        conn.commit()

        logger.debug(f"Saved preferences for user {preferences.user_id}")
        return preferences.user_id

    except sqlite3.Error as e:
        raise DatabaseStorageError(
            f"Failed to save preferences for user {preferences.user_id}: {e}"
        )


def load_user_preferences(conn: DatabaseConnection, user_id: str) -> UserPreferences:
    """
    Load user preferences for server-side HTML generation.

    Args:
        conn: Database connection
        user_id: User identifier

    Returns:
        UserPreferences object

    Raises:
        UserPreferencesNotFoundError: If preferences not found
        DatabaseStorageError: If load operation fails
    """
    try:
        cursor = conn.execute(
            "SELECT preferences_json FROM user_preferences WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()

        if not row:
            # Return default preferences if none exist
            logger.info(f"No preferences found for user {user_id}, returning defaults")
            return UserPreferences(user_id=user_id)

        # Parse JSON back to UserPreferences object
        preferences_data = json.loads(row[0])
        return UserPreferences(**preferences_data)

    except sqlite3.Error as e:
        raise DatabaseStorageError(
            f"Failed to load preferences for user {user_id}: {e}"
        )


def delete_card(conn: DatabaseConnection, card_id: str) -> bool:
    """
    Delete card and all associated data (CASCADE).

    Args:
        conn: Database connection
        card_id: Card identifier

    Returns:
        True if card was deleted, False if not found

    Raises:
        DatabaseStorageError: If delete operation fails
    """
    try:
        # Delete CardSummary (CASCADE will handle CardDetail and attachments)
        cursor = conn.execute("DELETE FROM card_summaries WHERE id = ?", (card_id,))
        deleted = cursor.rowcount > 0
        conn.commit()

        if deleted:
            logger.info(f"Deleted card {card_id} and associated data")
        else:
            logger.warning(f"Card {card_id} not found for deletion")

        return deleted

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to delete card {card_id}: {e}")


def get_database_statistics(conn: DatabaseConnection) -> dict[str, Any]:
    """
    Get database statistics for monitoring and debugging.

    Args:
        conn: Database connection

    Returns:
        Dictionary with database statistics

    Raises:
        DatabaseStorageError: If statistics query fails
    """
    try:
        stats = {}

        # Count records in each table
        tables = ["card_summaries", "card_details", "user_preferences", "attachments"]
        for table in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            stats[f"{table}_count"] = cursor.fetchone()[0]

        # Database file size (if not in-memory)
        cursor = conn.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor = conn.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        stats["database_size_bytes"] = page_count * page_size

        # Get unique tag count
        cursor = conn.execute("SELECT tags_json FROM card_summaries")
        all_tags = set()
        for (tags_json,) in cursor.fetchall():
            tags = json.loads(tags_json)
            all_tags.update(tags)
        stats["unique_tags_count"] = len(all_tags)

        return stats

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to get database statistics: {e}")


# Turso-Optimized Bulk Loading Functions


def bulk_load_card_summaries(
    conn: DatabaseConnection, cards: list[CardSummary], batch_size: int = 10000
) -> int:
    """
    Bulk load CardSummary objects with Turso-optimized settings.

    Uses executemany for optimal performance on large datasets (10k+ cards).
    Automatically applies Turso-specific optimizations for universe-scale data.

    Args:
        conn: Database connection
        cards: List of CardSummary objects to insert
        batch_size: Number of cards per batch for memory management

    Returns:
        Number of cards successfully inserted

    Raises:
        DatabaseStorageError: If bulk insert fails
    """
    try:
        start_time = time.perf_counter()
        total_inserted = 0

        # Turso optimizations for bulk insert
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = OFF")  # Fastest for bulk loads
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")

        # Process in batches to manage memory
        for i in range(0, len(cards), batch_size):
            batch = cards[i : i + batch_size]

            # Prepare batch data
            batch_data = []
            for card in batch:
                created_at = (
                    card.created_at.isoformat()
                    if isinstance(card.created_at, datetime)
                    else card.created_at
                )
                modified_at = (
                    card.modified_at.isoformat()
                    if isinstance(card.modified_at, datetime)
                    else card.modified_at
                )

                batch_data.append(
                    (
                        card.id,
                        card.title,
                        json.dumps(sorted(list(card.tags))),
                        created_at,
                        modified_at,
                        card.has_attachments,
                    )
                )

            # Bulk insert batch
            conn.executemany(
                """INSERT OR REPLACE INTO card_summaries
                   (id, title, tags_json, created_at, modified_at, has_attachments)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                batch_data,
            )

            total_inserted += len(batch)

            # Log progress for large batches
            if len(cards) > batch_size:
                logger.debug(
                    f"Bulk loaded batch {i//batch_size + 1}: {len(batch)} cards"
                )

        # Commit all batches
        conn.commit()

        # Restore normal synchronous mode
        conn.execute("PRAGMA synchronous = NORMAL")

        end_time = time.perf_counter()
        load_time_ms = (end_time - start_time) * 1000

        logger.info(
            f"Bulk loaded {total_inserted} CardSummary objects in {load_time_ms:.2f}ms"
        )
        return total_inserted

    except sqlite3.Error as e:
        # Rollback on error
        conn.rollback()
        conn.execute("PRAGMA synchronous = NORMAL")  # Restore normal mode
        raise DatabaseStorageError(f"Failed to bulk load CardSummary objects: {e}")


def bulk_load_tags(
    conn: DatabaseConnection, tags: list[str], batch_size: int = 10000
) -> dict[str, int]:
    """
    Bulk load tags into normalized tags table with Turso optimizations.

    Efficiently handles large tag vocabularies (10M+ unique tags).
    Returns mapping of tag names to their database IDs.

    Args:
        conn: Database connection
        tags: List of unique tag names to insert
        batch_size: Number of tags per batch

    Returns:
        Dictionary mapping tag names to tag IDs

    Raises:
        DatabaseStorageError: If bulk insert fails
    """
    try:
        start_time = time.perf_counter()

        # Turso optimizations
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute("PRAGMA cache_size = -32000")  # 32MB cache for tags

        # Get existing tags to avoid duplicates
        cursor = conn.execute("SELECT name, id FROM tags")
        tag_id_map = {name: tag_id for name, tag_id in cursor.fetchall()}

        # Find new tags to insert
        new_tags = [tag for tag in tags if tag not in tag_id_map]

        if new_tags:
            # Process in batches
            for i in range(0, len(new_tags), batch_size):
                batch = new_tags[i : i + batch_size]
                batch_data = [(tag,) for tag in batch]

                # Bulk insert new tags
                conn.executemany(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)", batch_data
                )

            conn.commit()

            # Get IDs for newly inserted tags
            placeholders = ",".join(["?" for _ in new_tags])
            cursor = conn.execute(
                f"SELECT name, id FROM tags WHERE name IN ({placeholders})", new_tags
            )

            # Update mapping with new tags
            for name, tag_id in cursor.fetchall():
                tag_id_map[name] = tag_id

        # Restore normal mode
        conn.execute("PRAGMA synchronous = NORMAL")

        end_time = time.perf_counter()
        load_time_ms = (end_time - start_time) * 1000

        logger.info(
            f"Bulk loaded {len(new_tags)} new tags in {load_time_ms:.2f}ms (total: {len(tag_id_map)})"
        )
        return tag_id_map

    except sqlite3.Error as e:
        conn.rollback()
        conn.execute("PRAGMA synchronous = NORMAL")
        raise DatabaseStorageError(f"Failed to bulk load tags: {e}")


def bulk_load_card_tags(
    conn: DatabaseConnection,
    card_tag_relations: list[tuple[str, int]],
    batch_size: int = 50000,
) -> int:
    """
    Bulk load card-tag relationships into normalized card_tags table.

    Optimized for massive relationship tables (100M+ relations).

    Args:
        conn: Database connection
        card_tag_relations: List of (card_id, tag_id) tuples
        batch_size: Number of relations per batch

    Returns:
        Number of relationships successfully inserted

    Raises:
        DatabaseStorageError: If bulk insert fails
    """
    try:
        start_time = time.perf_counter()
        total_inserted = 0

        # Turbo mode for relations
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute("PRAGMA cache_size = -128000")  # 128MB cache for relations
        conn.execute("PRAGMA temp_store = MEMORY")

        # Process in batches
        for i in range(0, len(card_tag_relations), batch_size):
            batch = card_tag_relations[i : i + batch_size]

            conn.executemany(
                "INSERT OR IGNORE INTO card_tags (card_id, tag_id) VALUES (?, ?)", batch
            )

            total_inserted += len(batch)

            # Log progress for large datasets
            if len(card_tag_relations) > batch_size:
                logger.debug(
                    f"Bulk loaded card-tag batch {i//batch_size + 1}: {len(batch)} relations"
                )

        conn.commit()
        conn.execute("PRAGMA synchronous = NORMAL")

        end_time = time.perf_counter()
        load_time_ms = (end_time - start_time) * 1000

        logger.info(
            f"Bulk loaded {total_inserted} card-tag relations in {load_time_ms:.2f}ms"
        )
        return total_inserted

    except sqlite3.Error as e:
        conn.rollback()
        conn.execute("PRAGMA synchronous = NORMAL")
        raise DatabaseStorageError(f"Failed to bulk load card-tag relations: {e}")


# Streaming Functions for Universe-Scale Datasets


def stream_card_summaries(
    conn: DatabaseConnection, batch_size: int = 10000, limit: int | None = None
) -> list[CardSummary]:
    """
    Stream CardSummary objects in batches for memory-efficient processing.

    Yields batches of CardSummary objects to prevent memory exhaustion
    when processing universe-scale datasets (10M+ cards).

    Args:
        conn: Database connection
        batch_size: Number of cards per batch
        limit: Maximum total cards to stream (None for unlimited)

    Yields:
        Batches of CardSummary objects

    Raises:
        DatabaseStorageError: If streaming fails
    """
    try:
        # Build query with optional limit
        base_query = """
            SELECT id, title, tags_json, created_at, modified_at, has_attachments
            FROM card_summaries ORDER BY modified_at DESC
        """

        if limit:
            query = f"{base_query} LIMIT {limit}"
        else:
            query = base_query

        # Get total count for progress tracking
        cursor = conn.execute("SELECT COUNT(*) FROM card_summaries")
        total_cards = cursor.fetchone()[0]

        if limit and limit < total_cards:
            total_cards = limit

        logger.info(
            f"Starting stream of {total_cards} cards in batches of {batch_size}"
        )

        # Stream in batches using OFFSET
        offset = 0
        processed = 0

        while processed < total_cards:
            # Calculate current batch size
            current_batch_size = min(batch_size, total_cards - processed)

            # Query current batch
            batch_query = f"{query} LIMIT {current_batch_size} OFFSET {offset}"
            cursor = conn.execute(batch_query)

            batch = []
            for row in cursor.fetchall():
                # Parse datetime strings
                created_at = (
                    datetime.fromisoformat(row[3])
                    if isinstance(row[3], str)
                    else row[3]
                )
                modified_at = (
                    datetime.fromisoformat(row[4])
                    if isinstance(row[4], str)
                    else row[4]
                )

                card = CardSummary(
                    id=row[0],
                    title=row[1],
                    tags=frozenset(json.loads(row[2])),
                    created_at=created_at,
                    modified_at=modified_at,
                    has_attachments=bool(row[5]),
                )
                batch.append(card)

            if not batch:
                break

            # Yield current batch
            yield batch

            # Update counters
            processed += len(batch)
            offset += current_batch_size

            # Log progress for large streams
            if total_cards > batch_size:
                progress_pct = (processed / total_cards) * 100
                logger.debug(
                    f"Streamed {processed}/{total_cards} cards ({progress_pct:.1f}%)"
                )

        logger.info(f"Completed streaming {processed} cards")

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to stream CardSummary objects: {e}")


def stream_card_summaries_by_tags(
    conn: DatabaseConnection,
    target_tags: list[str],
    batch_size: int = 10000,
    use_normalized_schema: bool = True,
) -> list[CardSummary]:
    """
    Stream CardSummary objects filtered by tags for efficient set operations.

    Memory-efficient streaming of cards matching specific tags,
    optimized for universe-scale tag filtering operations.

    Args:
        conn: Database connection
        target_tags: List of tags to filter by
        batch_size: Number of cards per batch
        use_normalized_schema: Whether to use normalized tags table

    Yields:
        Batches of filtered CardSummary objects

    Raises:
        DatabaseStorageError: If streaming fails
    """
    try:
        start_time = time.perf_counter()

        if use_normalized_schema and target_tags:
            # SQL-optimized filtering using normalized schema
            placeholders = ",".join(["?" for _ in target_tags])

            # Query cards that have any of the target tags
            query = f"""
                SELECT DISTINCT cs.id, cs.title, cs.tags_json, cs.created_at, cs.modified_at, cs.has_attachments
                FROM card_summaries cs
                JOIN card_tags ct ON cs.id = ct.card_id
                JOIN tags t ON ct.tag_id = t.id
                WHERE t.name IN ({placeholders})
                ORDER BY cs.modified_at DESC
            """

            # Get total count for progress tracking
            count_query = f"""
                SELECT COUNT(DISTINCT cs.id)
                FROM card_summaries cs
                JOIN card_tags ct ON cs.id = ct.card_id
                JOIN tags t ON ct.tag_id = t.id
                WHERE t.name IN ({placeholders})
            """

            cursor = conn.execute(count_query, target_tags)
            total_cards = cursor.fetchone()[0]

            logger.info(
                f"Streaming {total_cards} cards matching {len(target_tags)} tags"
            )

            # Stream in batches
            offset = 0
            processed = 0

            while processed < total_cards:
                batch_query = f"{query} LIMIT {batch_size} OFFSET {offset}"
                cursor = conn.execute(batch_query, target_tags)

                batch = []
                for row in cursor.fetchall():
                    # Parse datetime strings
                    created_at = (
                        datetime.fromisoformat(row[3])
                        if isinstance(row[3], str)
                        else row[3]
                    )
                    modified_at = (
                        datetime.fromisoformat(row[4])
                        if isinstance(row[4], str)
                        else row[4]
                    )

                    card = CardSummary(
                        id=row[0],
                        title=row[1],
                        tags=frozenset(json.loads(row[2])),
                        created_at=created_at,
                        modified_at=modified_at,
                        has_attachments=bool(row[5]),
                    )
                    batch.append(card)

                if not batch:
                    break

                yield batch

                processed += len(batch)
                offset += batch_size

        else:
            # Fallback to streaming all cards with client-side filtering
            target_tags_set = set(target_tags)

            for batch in stream_card_summaries(conn, batch_size):
                # Filter batch by tags
                filtered_batch = [
                    card for card in batch if target_tags_set.intersection(card.tags)
                ]

                if filtered_batch:
                    yield filtered_batch

        end_time = time.perf_counter()
        stream_time_ms = (end_time - start_time) * 1000

        schema_type = "normalized" if use_normalized_schema else "fallback"
        logger.info(
            f"Completed tag-filtered streaming ({schema_type}) in {stream_time_ms:.2f}ms"
        )

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to stream cards by tags: {e}")


def stream_bulk_export(
    conn: DatabaseConnection, export_format: str = "json", batch_size: int = 5000
) -> dict[str, Any]:
    """
    Stream database export in batches for universe-scale backup operations.

    Memory-efficient export of entire database contents,
    suitable for multi-terabyte universe datasets.

    Args:
        conn: Database connection
        export_format: Export format ("json", "csv", or "sql")
        batch_size: Number of records per batch

    Yields:
        Export data batches in specified format

    Raises:
        DatabaseStorageError: If export streaming fails
    """
    try:
        start_time = time.perf_counter()

        logger.info(
            f"Starting bulk export in {export_format} format (batch size: {batch_size})"
        )

        # Export card summaries
        for batch in stream_card_summaries(conn, batch_size):
            if export_format == "json":
                batch_data = {
                    "type": "card_summaries",
                    "data": [
                        {
                            "id": card.id,
                            "title": card.title,
                            "tags": list(card.tags),
                            "created_at": card.created_at.isoformat(),
                            "modified_at": card.modified_at.isoformat(),
                            "has_attachments": card.has_attachments,
                        }
                        for card in batch
                    ],
                }
                yield batch_data

            elif export_format == "csv":
                # CSV header for first batch
                yield {
                    "type": "card_summaries_csv",
                    "headers": [
                        "id",
                        "title",
                        "tags",
                        "created_at",
                        "modified_at",
                        "has_attachments",
                    ],
                    "data": [
                        [
                            card.id,
                            card.title,
                            ";".join(sorted(card.tags)),
                            card.created_at.isoformat(),
                            card.modified_at.isoformat(),
                            card.has_attachments,
                        ]
                        for card in batch
                    ],
                }

        # Export normalized tags if available
        try:
            cursor = conn.execute("SELECT name, id FROM tags ORDER BY id")
            tags_data = cursor.fetchall()

            if tags_data:
                yield {
                    "type": "tags",
                    "data": [
                        {"id": tag_id, "name": name} for name, tag_id in tags_data
                    ],
                }
        except sqlite3.OperationalError:
            # Tags table doesn't exist, skip
            pass

        end_time = time.perf_counter()
        export_time_ms = (end_time - start_time) * 1000

        logger.info(f"Completed bulk export in {export_time_ms:.2f}ms")

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to stream bulk export: {e}")


# Utility functions for database management


def backup_database(source_conn: DatabaseConnection, backup_path: Path) -> None:
    """
    Create database backup using SQLite backup API.

    Args:
        source_conn: Source database connection
        backup_path: Path for backup file

    Raises:
        DatabaseStorageError: If backup fails
    """
    try:
        backup_conn = sqlite3.connect(str(backup_path))
        source_conn.backup(backup_conn)
        backup_conn.close()

        logger.info(f"Database backed up to {backup_path}")

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to backup database: {e}")


def backup_database_turso(
    source_conn: DatabaseConnection,
    backup_path: Path,
    batch_size: int = 10000,
    compress: bool = True,
) -> None:
    """
    Create Turso-optimized database backup for universe-scale datasets.

    Uses streaming approach to handle multi-terabyte databases efficiently.

    Args:
        source_conn: Source database connection
        backup_path: Path for backup file
        batch_size: Number of records per batch
        compress: Whether to enable compression

    Raises:
        DatabaseStorageError: If backup fails
    """
    try:
        import gzip

        start_time = time.perf_counter()

        # Open backup file with optional compression
        if compress:
            backup_file = gzip.open(f"{backup_path}.gz", "wt", encoding="utf-8")
        else:
            backup_file = open(backup_path, "w", encoding="utf-8")

        try:
            # Write backup header
            backup_file.write("-- MultiCardz Turso Database Backup\n")
            backup_file.write(f"-- Generated: {datetime.now(UTC).isoformat()}\n")
            backup_file.write("-- Format: Streaming SQL with Turso optimizations\n\n")

            # Disable foreign keys during restore
            backup_file.write("PRAGMA foreign_keys = OFF;\n")
            backup_file.write("BEGIN TRANSACTION;\n\n")

            # Stream card summaries
            backup_file.write("-- Card Summaries\n")
            total_cards = 0

            for batch in stream_card_summaries(source_conn, batch_size):
                for card in batch:
                    backup_file.write(
                        f"INSERT OR REPLACE INTO card_summaries "
                        f"(id, title, tags_json, created_at, modified_at, has_attachments) "
                        f"VALUES ('{card.id}', '{card.title.replace("'", "''")}', "
                        f"'{json.dumps(sorted(list(card.tags))).replace("'", "''")}', "
                        f"'{card.created_at.isoformat()}', '{card.modified_at.isoformat()}', "
                        f"{1 if card.has_attachments else 0});\n"
                    )
                    total_cards += 1

                # Flush batch to disk
                backup_file.flush()

            # Stream normalized tags if available
            try:
                cursor = source_conn.execute("SELECT id, name FROM tags ORDER BY id")
                backup_file.write("\n-- Normalized Tags\n")

                for tag_id, name in cursor.fetchall():
                    backup_file.write(
                        f"INSERT OR REPLACE INTO tags (id, name) "
                        f"VALUES ({tag_id}, '{name.replace("'", "''")}');\n"
                    )

            except sqlite3.OperationalError:
                # Tags table doesn't exist
                pass

            # Stream card-tag relations if available
            try:
                cursor = source_conn.execute("SELECT card_id, tag_id FROM card_tags")
                backup_file.write("\n-- Card-Tag Relations\n")

                batch_relations = []
                for card_id, tag_id in cursor.fetchall():
                    batch_relations.append((card_id, tag_id))

                    if len(batch_relations) >= batch_size:
                        for rel_card_id, rel_tag_id in batch_relations:
                            backup_file.write(
                                f"INSERT OR IGNORE INTO card_tags (card_id, tag_id) "
                                f"VALUES ('{rel_card_id}', {rel_tag_id});\n"
                            )
                        batch_relations = []
                        backup_file.flush()

                # Write remaining relations
                for rel_card_id, rel_tag_id in batch_relations:
                    backup_file.write(
                        f"INSERT OR IGNORE INTO card_tags (card_id, tag_id) "
                        f"VALUES ('{rel_card_id}', {rel_tag_id});\n"
                    )

            except sqlite3.OperationalError:
                # card_tags table doesn't exist
                pass

            # Finalize backup
            backup_file.write("\nCOMMIT;\n")
            backup_file.write("PRAGMA foreign_keys = ON;\n")
            backup_file.write("VACUUM;\n")
            backup_file.write("ANALYZE;\n")

        finally:
            backup_file.close()

        end_time = time.perf_counter()
        backup_time_ms = (end_time - start_time) * 1000

        # Get backup file size
        file_size_mb = (
            backup_path.stat().st_size / (1024 * 1024) if backup_path.exists() else 0
        )
        compression_note = " (compressed)" if compress else ""

        logger.info(
            f"Turso backup completed: {total_cards} cards in {backup_time_ms:.2f}ms, "
            f"{file_size_mb:.1f}MB{compression_note}"
        )

    except Exception as e:
        raise DatabaseStorageError(f"Failed to create Turso backup: {e}")


def optimize_database(conn: DatabaseConnection) -> None:
    """
    Optimize database performance through VACUUM and ANALYZE.

    Args:
        conn: Database connection

    Raises:
        DatabaseStorageError: If optimization fails
    """
    try:
        start_time = time.perf_counter()

        conn.execute("VACUUM")
        conn.execute("ANALYZE")

        end_time = time.perf_counter()
        optimization_time_ms = (end_time - start_time) * 1000

        logger.info(f"Database optimized in {optimization_time_ms:.2f}ms")

    except sqlite3.Error as e:
        raise DatabaseStorageError(f"Failed to optimize database: {e}")
