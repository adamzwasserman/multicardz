"""
Turso Privacy Mode Manager for multicardz.
Handles three-way sync between browser WASM SQLite, server SQLite, and Turso cloud.
"""

import os
import json
import hashlib
from typing import Dict, Optional, Any, List
from enum import Enum
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import libsql_experimental as libsql

from apps.shared.models.orm_models import Base, Cards, Tags, CardContents


class SyncDirection(Enum):
    """Sync direction for replication."""
    BROWSER_TO_SERVER = "browser_to_server"
    SERVER_TO_TURSO = "server_to_turso"
    TURSO_TO_SERVER = "turso_to_server"
    SERVER_TO_BROWSER = "server_to_browser"


class TursoPrivacyManager:
    """
    Manages Privacy Mode databases with Turso replication.

    Architecture:
    1. Browser WASM SQLite (client-side, full content)
    2. Server SQLite (obfuscated, bitmaps only)
    3. Turso Cloud (backup/replication, obfuscated)
    """

    def __init__(self):
        self.turso_url = os.getenv('TURSO_DATABASE_URL')
        self.turso_token = os.getenv('TURSO_AUTH_TOKEN')
        self.sync_interval = int(os.getenv('TURSO_SYNC_INTERVAL', '60'))  # seconds

        # Cache for embedded replicas
        self.embedded_replicas: Dict[str, libsql.Database] = {}
        self.obfuscation_keys: Dict[str, bytes] = {}

    def _get_obfuscation_key(self, user_id: str, workspace_id: str) -> bytes:
        """Generate deterministic obfuscation key for user/workspace."""
        key_id = f"{user_id}_{workspace_id}"

        if key_id not in self.obfuscation_keys:
            # Use environment secret + user/workspace for key derivation
            secret = os.getenv('OBFUSCATION_SECRET', 'default-secret')
            key_material = f"{secret}:{user_id}:{workspace_id}".encode()
            self.obfuscation_keys[key_id] = hashlib.sha256(key_material).digest()

        return self.obfuscation_keys[key_id]

    def create_embedded_replica(self, user_id: str, workspace_id: str) -> libsql.Database:
        """
        Create or get an embedded replica for user/workspace.
        This creates a local SQLite database that syncs with Turso.
        """
        replica_id = f"{user_id}_{workspace_id}"

        if replica_id not in self.embedded_replicas:
            # Local path for embedded replica
            local_path = f"data/privacy/{user_id}_{workspace_id}_replica.db"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Turso database name for this user/workspace
            turso_db_name = f"{user_id}-{workspace_id}-privacy"
            turso_url = f"libsql://{turso_db_name}.{self.turso_url}"

            # Create embedded replica with Turso sync
            db = libsql.Database(
                path=local_path,
                sync_url=turso_url,
                auth_token=self.turso_token,
                sync_interval=self.sync_interval,
                encryption_key=self._get_obfuscation_key(user_id, workspace_id)
            )

            # Initialize schema for obfuscated data
            conn = db.connect()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS obfuscated_cards (
                    card_bitmap INTEGER PRIMARY KEY,
                    tag_bitmaps TEXT,  -- JSON array of tag bitmaps
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

            self.embedded_replicas[replica_id] = db

        return self.embedded_replicas[replica_id]

    def obfuscate_card(self, card: Cards) -> Dict[str, Any]:
        """
        Obfuscate card data for Privacy Mode storage.
        Only stores bitmaps and checksums, no actual content.
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

    def obfuscate_tag(self, tag: Tags) -> Dict[str, Any]:
        """
        Obfuscate tag data for Privacy Mode storage.
        Only stores bitmap and checksum.
        """
        # Create checksum of tag name for verification
        checksum = hashlib.sha256(tag.name.encode()).hexdigest()[:16]

        return {
            'tag_bitmap': tag.tag_bitmap,
            'checksum': checksum
        }

    def sync_browser_to_server(self, user_id: str, workspace_id: str,
                              browser_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync data from browser WASM SQLite to server embedded replica.
        Browser sends full data, server stores obfuscated version.
        """
        replica = self.create_embedded_replica(user_id, workspace_id)
        conn = replica.connect()

        try:
            # Begin transaction for atomic updates
            conn.execute("BEGIN TRANSACTION")

            # Process cards
            for card_data in browser_data.get('cards', []):
                obfuscated = self.obfuscate_card(card_data)
                conn.execute("""
                    INSERT OR REPLACE INTO obfuscated_cards
                    (card_bitmap, tag_bitmaps, checksum, sync_version)
                    VALUES (?, ?, ?, ?)
                """, (
                    obfuscated['card_bitmap'],
                    json.dumps(obfuscated['tag_bitmaps']),
                    obfuscated['checksum'],
                    browser_data.get('sync_version', 0)
                ))

            # Process tags
            for tag_data in browser_data.get('tags', []):
                obfuscated = self.obfuscate_tag(tag_data)
                conn.execute("""
                    INSERT OR REPLACE INTO obfuscated_tags
                    (tag_bitmap, checksum, sync_version)
                    VALUES (?, ?, ?)
                """, (
                    obfuscated['tag_bitmap'],
                    obfuscated['checksum'],
                    browser_data.get('sync_version', 0)
                ))

            # Update sync metadata
            conn.execute("""
                INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
                VALUES ('last_browser_sync', ?, strftime('%s', 'now'))
            """, (json.dumps({'user_id': user_id, 'workspace_id': workspace_id}),))

            conn.execute("COMMIT")

            # Trigger sync to Turso
            replica.sync()

            return {
                'status': 'success',
                'synced_cards': len(browser_data.get('cards', [])),
                'synced_tags': len(browser_data.get('tags', []))
            }

        except Exception as e:
            conn.execute("ROLLBACK")
            return {
                'status': 'error',
                'message': str(e)
            }
        finally:
            conn.close()

    def get_obfuscated_data(self, user_id: str, workspace_id: str) -> Dict[str, Any]:
        """
        Get obfuscated data from server embedded replica.
        Used for RoaringBitmap operations without exposing content.
        """
        replica = self.create_embedded_replica(user_id, workspace_id)
        conn = replica.connect()

        try:
            # Get all obfuscated cards
            cursor = conn.execute("""
                SELECT card_bitmap, tag_bitmaps FROM obfuscated_cards
            """)
            cards = []
            for row in cursor:
                cards.append({
                    'card_bitmap': row[0],
                    'tag_bitmaps': json.loads(row[1])
                })

            # Get all obfuscated tags
            cursor = conn.execute("""
                SELECT tag_bitmap FROM obfuscated_tags
            """)
            tags = [{'tag_bitmap': row[0]} for row in cursor]

            return {
                'cards': cards,
                'tags': tags
            }

        finally:
            conn.close()

    def perform_set_operation(self, user_id: str, workspace_id: str,
                            operation: str, tag_bitmaps: List[int]) -> List[int]:
        """
        Perform set operations on obfuscated data.
        Returns card bitmaps matching the operation.
        """
        data = self.get_obfuscated_data(user_id, workspace_id)

        # Convert to sets for operations
        if operation == 'union':
            result = set()
            for card in data['cards']:
                card_tags = set(card['tag_bitmaps'])
                if card_tags & set(tag_bitmaps):  # Any tag matches
                    result.add(card['card_bitmap'])

        elif operation == 'intersection':
            result = None
            for tag_bitmap in tag_bitmaps:
                tag_cards = {card['card_bitmap'] for card in data['cards']
                           if tag_bitmap in card['tag_bitmaps']}
                if result is None:
                    result = tag_cards
                else:
                    result &= tag_cards
            result = result or set()

        elif operation == 'difference':
            # Cards with first tag but not others
            if not tag_bitmaps:
                return []

            result = {card['card_bitmap'] for card in data['cards']
                     if tag_bitmaps[0] in card['tag_bitmaps']}

            for tag_bitmap in tag_bitmaps[1:]:
                exclude = {card['card_bitmap'] for card in data['cards']
                          if tag_bitmap in card['tag_bitmaps']}
                result -= exclude

        else:
            raise ValueError(f"Unknown operation: {operation}")

        return list(result)

    def force_sync(self, user_id: str, workspace_id: str) -> bool:
        """Force immediate sync with Turso cloud."""
        replica_id = f"{user_id}_{workspace_id}"

        if replica_id in self.embedded_replicas:
            try:
                self.embedded_replicas[replica_id].sync()
                return True
            except Exception as e:
                print(f"Sync failed: {e}")
                return False

        return False

    def restore_from_turso(self, user_id: str, workspace_id: str) -> bool:
        """
        Restore local embedded replica from Turso cloud backup.
        Used for disaster recovery or new device setup.
        """
        try:
            # Remove existing local replica
            local_path = f"data/privacy/{user_id}_{workspace_id}_replica.db"
            if os.path.exists(local_path):
                os.remove(local_path)

            # Remove from cache
            replica_id = f"{user_id}_{workspace_id}"
            if replica_id in self.embedded_replicas:
                del self.embedded_replicas[replica_id]

            # Create new replica (will pull from Turso)
            replica = self.create_embedded_replica(user_id, workspace_id)
            replica.sync()

            return True

        except Exception as e:
            print(f"Restore failed: {e}")
            return False

    def get_sync_status(self, user_id: str, workspace_id: str) -> Dict[str, Any]:
        """Get current sync status and metadata."""
        replica = self.create_embedded_replica(user_id, workspace_id)
        conn = replica.connect()

        try:
            cursor = conn.execute("""
                SELECT key, value, updated_at FROM sync_metadata
            """)

            metadata = {}
            for row in cursor:
                metadata[row[0]] = {
                    'value': json.loads(row[1]) if row[1] else None,
                    'updated_at': row[2]
                }

            # Get counts
            card_count = conn.execute("SELECT COUNT(*) FROM obfuscated_cards").fetchone()[0]
            tag_count = conn.execute("SELECT COUNT(*) FROM obfuscated_tags").fetchone()[0]

            return {
                'status': 'connected',
                'card_count': card_count,
                'tag_count': tag_count,
                'metadata': metadata,
                'replica_path': f"data/privacy/{user_id}_{workspace_id}_replica.db"
            }

        finally:
            conn.close()


# Global instance
turso_manager = TursoPrivacyManager()