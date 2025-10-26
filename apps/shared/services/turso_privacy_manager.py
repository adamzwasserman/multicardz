"""
Turso Privacy Mode Manager using pure functions.
Handles three-way sync between browser WASM SQLite, server SQLite, and Turso cloud.
Following Zero-Trust UUID Architecture Phase 2 requirements.
"""

import hashlib
import json
import os
from enum import Enum
from typing import Any, Optional

import libsql_experimental as libsql
from apps.shared.models.orm_models import Cards, Tags


class SyncDirection(Enum):
    """Sync direction for replication."""
    BROWSER_TO_SERVER = "browser_to_server"
    SERVER_TO_TURSO = "server_to_turso"
    TURSO_TO_SERVER = "turso_to_server"
    SERVER_TO_BROWSER = "server_to_browser"


# Pure functions for obfuscation
def get_obfuscation_key(
    user_id: str,
    workspace_id: str,
    secret: Optional[str] = None,
    cache: Optional[dict[str, bytes]] = None
) -> bytes:
    """
    Generate deterministic obfuscation key for user/workspace.

    Args:
        user_id: User identifier
        workspace_id: Workspace identifier
        secret: Obfuscation secret (uses env var if not provided)
        cache: Optional cache dict for keys

    Returns:
        32-byte obfuscation key
    """
    key_id = f"{user_id}_{workspace_id}"

    # Check cache if provided
    if cache is not None and key_id in cache:
        return cache[key_id]

    # Use environment secret if not provided
    if secret is None:
        secret = os.getenv('OBFUSCATION_SECRET', 'default-secret')

    # Generate key
    key_material = f"{secret}:{user_id}:{workspace_id}".encode()
    key = hashlib.sha256(key_material).digest()

    # Store in cache if provided
    if cache is not None:
        cache[key_id] = key

    return key


def create_embedded_replica(
    user_id: str,
    workspace_id: str,
    turso_url: Optional[str] = None,
    turso_token: Optional[str] = None,
    sync_interval: int = 60,
    replica_cache: Optional[dict[str, libsql.Database]] = None,
    obfuscation_key_cache: Optional[dict[str, bytes]] = None
) -> libsql.Database:
    """
    Create or get an embedded replica for user/workspace.

    Args:
        user_id: User identifier
        workspace_id: Workspace identifier
        turso_url: Turso database URL (uses env var if not provided)
        turso_token: Turso auth token (uses env var if not provided)
        sync_interval: Sync interval in seconds
        replica_cache: Optional cache for replicas
        obfuscation_key_cache: Optional cache for obfuscation keys

    Returns:
        libsql Database instance
    """
    replica_id = f"{user_id}_{workspace_id}"

    # Check cache if provided
    if replica_cache is not None and replica_id in replica_cache:
        return replica_cache[replica_id]

    # Use environment variables if not provided
    if turso_url is None:
        turso_url = os.getenv('TURSO_DATABASE_URL')
    if turso_token is None:
        turso_token = os.getenv('TURSO_AUTH_TOKEN')

    # Local path for embedded replica
    local_path = f"data/privacy/{user_id}_{workspace_id}_replica.db"
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # Turso database name for this user/workspace
    turso_db_name = f"{user_id}-{workspace_id}-privacy"
    full_turso_url = f"libsql://{turso_db_name}.{turso_url}"

    # Get obfuscation key
    encryption_key = get_obfuscation_key(user_id, workspace_id, cache=obfuscation_key_cache)

    # Create embedded replica with Turso sync
    db = libsql.Database(
        path=local_path,
        sync_url=full_turso_url,
        auth_token=turso_token,
        sync_interval=sync_interval,
        encryption_key=encryption_key
    )

    # Initialize schema for obfuscated data
    conn = db.connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS obfuscated_cards (
            card_bitmap INTEGER PRIMARY KEY,
            tag_bitmaps TEXT,
            checksum TEXT,
            sync_version INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS obfuscated_tags (
            tag_bitmap INTEGER PRIMARY KEY,
            checksum TEXT,
            sync_version INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sync_metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at INTEGER
        )
    """)
    conn.commit()
    conn.close()

    # Store in cache if provided
    if replica_cache is not None:
        replica_cache[replica_id] = db

    return db


def obfuscate_card(card: Cards) -> dict[str, Any]:
    """
    Obfuscate card data for Privacy Mode storage.

    Args:
        card: Card model instance

    Returns:
        Dict with obfuscated card data (bitmap, checksums only)
    """
    # Generate card bitmap from UUID
    card_bitmap = int(hashlib.md5(card.card_id.encode()).hexdigest()[:8], 16)

    # Create checksum of actual content for verification
    content_str = json.dumps({
        'name': card.name,
        'description': card.description,
        'tag_ids': card.tag_ids
    }, sort_keys=True)
    checksum = hashlib.sha256(content_str.encode()).hexdigest()[:16]

    return {
        'card_bitmap': card_bitmap,
        'tag_bitmaps': card.tag_bitmaps or [],
        'checksum': checksum
    }


def obfuscate_tag(tag: Tags) -> dict[str, Any]:
    """
    Obfuscate tag data for Privacy Mode storage.

    Args:
        tag: Tag model instance

    Returns:
        Dict with obfuscated tag data (bitmap, checksum only)
    """
    # Create checksum of tag name for verification
    checksum = hashlib.sha256(tag.name.encode()).hexdigest()[:16]

    return {
        'tag_bitmap': tag.tag_bitmap,
        'checksum': checksum
    }


def sync_browser_to_server(
    user_id: str,
    workspace_id: str,
    browser_data: dict[str, Any],
    replica_cache: Optional[dict[str, libsql.Database]] = None,
    obfuscation_key_cache: Optional[dict[str, bytes]] = None
) -> dict[str, Any]:
    """
    Sync data from browser WASM SQLite to server embedded replica.

    Args:
        user_id: User identifier
        workspace_id: Workspace identifier
        browser_data: Full data from browser
        replica_cache: Optional replica cache
        obfuscation_key_cache: Optional obfuscation key cache

    Returns:
        Sync result status
    """
    # Get or create embedded replica
    db = create_embedded_replica(
        user_id, workspace_id,
        replica_cache=replica_cache,
        obfuscation_key_cache=obfuscation_key_cache
    )

    # TODO: Implement actual sync logic (Phase 5)
    return {'status': 'success', 'synced': 0}


# Backward compatibility class wrapper (TEMPORARY - to be removed)
class TursoPrivacyManager:
    """
    DEPRECATED: Backward compatibility wrapper. Use pure functions instead.
    This class will be removed in Phase 2 completion.
    """

    def __init__(self):
        self.turso_url = os.getenv('TURSO_DATABASE_URL')
        self.turso_token = os.getenv('TURSO_AUTH_TOKEN')
        self.sync_interval = int(os.getenv('TURSO_SYNC_INTERVAL', '60'))
        self.embedded_replicas: dict[str, libsql.Database] = {}
        self.obfuscation_keys: dict[str, bytes] = {}

    def _get_obfuscation_key(self, user_id: str, workspace_id: str) -> bytes:
        return get_obfuscation_key(user_id, workspace_id, cache=self.obfuscation_keys)

    def create_embedded_replica(self, user_id: str, workspace_id: str) -> libsql.Database:
        return create_embedded_replica(
            user_id, workspace_id,
            self.turso_url, self.turso_token, self.sync_interval,
            self.embedded_replicas, self.obfuscation_keys
        )

    def obfuscate_card(self, card: Cards) -> dict[str, Any]:
        return obfuscate_card(card)

    def obfuscate_tag(self, tag: Tags) -> dict[str, Any]:
        return obfuscate_tag(tag)

    def sync_browser_to_server(self, user_id: str, workspace_id: str,
                              browser_data: dict[str, Any]) -> dict[str, Any]:
        return sync_browser_to_server(
            user_id, workspace_id, browser_data,
            self.embedded_replicas, self.obfuscation_keys
        )
