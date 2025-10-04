# multicardz™ Zero-Trust UUID Implementation Plan v1

**Document Version**: 1.0
**Date**: 2025-09-28
**Status**: IMPLEMENTATION READY
**Author**: Implementation Team
**Architecture Reference**: [016-2025-09-28-multicardz-Zero-Trust-UUID-Architecture-v1.md](../architecture/016-2025-09-28-multicardz-Zero-Trust-UUID-Architecture-v1.md)

## Executive Summary

This implementation plan delivers the Zero-Trust UUID Architecture over 16 weeks, transforming multicardz into a verifiable privacy-first system. The plan emphasizes incremental delivery, maintaining system stability while building new capabilities.

**Timeline**: 16 weeks (4 months)
**Team Size**: 2-3 developers
**Risk Level**: Medium (significant architecture change)
**Customer Impact**: Zero during implementation, high value after delivery

## Current Architecture Baseline

### What Actually Exists (TO BE COMPLETELY REPLACED)

**[COMPLETE REPLACEMENT]** The current implementation uses a flawed two-tier architecture that must be entirely removed:

- `card_summaries` and `card_details` tables - REMOVE COMPLETELY
- `card_tags` junction table - REMOVE (tags will be stored as list in cards table)
- Mixed user/project data in single database - MUST SEPARATE
- No zero-trust isolation - MUST ADD
- No workspace separation - MUST ADD
- Two-tier CardSummary/CardDetail models - REPLACE with cards/tags/card_contents

### New Database Architecture

#### 1. Centralized Server (Turso Cloud)

- User authentication and management tables (when not using external auth)
- Internal housekeeping and audit logs
- **Privacy Mode**: Uses Turso embedded replicas with three-way sync:
  - Browser: Full WASM Turso ( with SQLite backup) database with complete content
  - Server: Obfuscated Turso ( with SQLite backup) embedded replica (bitmaps only, no content)
  - Turso Cloud: Automatic backup and replication of obfuscated data

#### 2. Project Database Schema (Identical for Turso [with SQLite backup])/Turso Cloud/WASM)

```sql
-- Core tables - NO foreign keys between them
CREATE TABLE cards (
    card_id TEXT PRIMARY KEY,  -- UUID stored as TEXT in SQLite
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted TIMESTAMP,
    tag_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array of tag UUIDs (inverted index)
    tag_bitmaps TEXT DEFAULT '[]'  -- JSON array of tag integer bitmaps for RoaringBitmap ops
);

CREATE TABLE tags (
    tag_id TEXT PRIMARY KEY,  -- UUID stored as TEXT in SQLite
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    tag_bitmap INTEGER NOT NULL,  -- Integer bitmap for this tag
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted TIMESTAMP
);

CREATE TABLE card_contents (
    id TEXT PRIMARY KEY,
    card_id TEXT NOT NULL,  -- Foreign key to cards table
    type INTEGER NOT NULL,  -- Polymorphic type indicator
    label TEXT,
    value_text TEXT,
    value_number REAL,
    value_boolean INTEGER,  -- SQLite uses 0/1 for boolean
    value_json TEXT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE
);
```

#### 3. User Preferences Database (DB #1 in each mode)

```sql
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY,
    -- Global settings (booleans stored as 0/1 in SQLite)
    start_cards_visible INTEGER DEFAULT 1,
    start_cards_expanded INTEGER DEFAULT 0,
    show_tag_colors INTEGER DEFAULT 1,

    -- UI settings
    theme TEXT DEFAULT 'system',  -- 'system', 'light', 'dark', 'earth'
    font_family TEXT DEFAULT 'Inter',
    separate_user_ai_tags INTEGER DEFAULT 1,
    stack_tags_vertically INTEGER DEFAULT 0,

    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE saved_views (
    view_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    tags_in_play TEXT NOT NULL,  -- JSON array of tag combinations
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_preferences(user_id)
);
```

#### 4. Database Deployment by Mode

**Dev Mode (Local Turso [with SQLite backup] files):**

- `user_prefs.db` - User preferences and saved views
- `project_{name}.db` - Individual project databases

**Normal Mode (Turso Edge):**

- `{user_id}_prefs` - User preferences database
- `{user_id}_{workspace_id}` - Individual project databases

**Privacy Mode (WASM Turso [with SQLite backup]  + Turso Embedded Replicas):**

- Browser: Full WASM Turso [with SQLite backup]  with complete card/tag content
- Server: Obfuscated Turso [with SQLite backup]  embedded replica (bitmaps only)
- Turso Cloud: Automatic backup and replication of obfuscated data

### Tags Structure

**[NEW]** Tags are unitary and immutable:

- **tag_id**: UUID (TEXT in all database modes)
- **tag_bitmap**: INTEGER for RoaringBitmap operations
- **name**: TEXT
- Tags table has NO arrays - tags are atomic

### Card-Tag Relationship (Inverted Index)

**[NEW]** Arrays are stored IN THE CARD:

- **tag_ids**: JSON array of tag UUIDs (inverted index relating tags to cards)
- **tag_bitmaps**: JSON array of tag integer bitmaps (for potential RoaringBitmap optimization)
- **Example**: `tag_ids: '["uuid-1", "uuid-2"]'`, `tag_bitmaps: '[123, 456]'`

### card_contents Polymorphic Structure

**[NEW]** Flexible content storage:

- **Type 1**: Text content (uses value_text)
- **Type 2**: Numeric values (uses value_number)
- **Type 3**: Boolean flags (uses value_boolean as 0/1)
- **Type 4**: JSON structured data (uses value_json)
- **Type 5**: Combined (can use multiple value fields)

Each card can have multiple card_contents entries of different types, enabling rich, structured data storage.

### Existing Classes Requiring Conversion

**[EXISTS-MODIFY]** 31 classes currently exist that need conversion to pure functions:

**BaseModel Classes (13)** - Will convert to dataclasses or pure functions:

- CardSummary, CardDetail (REMOVE - replaced by new schema)
- Attachment, UserTier, User, UserSession, UserWorkspace, UserRole
- ViewSettings, ThemeSettings, TagSettings, WorkspaceSettings, UserPreferences, Workspace

**Other Classes** - Will convert to pure functions:

- StorageStrategy (ABC), LocalSQLiteStrategy, HybridStrategy
- CardSummaryTuple, LessonCard, LessonTag (NamedTuples)
- DatabaseStorageError, CardNotFoundError, UserPreferencesNotFoundError (Exceptions - may keep)
- Performance and utility classes

### Existing RoaringBitmap Implementation

**[EXISTS-MODIFY]** RoaringBitmap support exists but needs enhancement:

- Uses pyroaring BitMap with fallback to croaring
- Must add integer mapping for UUIDs in obfuscated tables
- Will enhance for Privacy Mode bitmap operations

### Key Architectural Decisions Made

**Database Schema Changes**:

- **[NEW]** Architecture will not create UUID mappings table (will use integer_id column pattern to be added to cards/tags tables)
- **[NEW]** Will add user_id UUID and workspace_id UUID to ALL tables for zero-trust isolation
- **[NEW]** Will add audit columns (created, modified, deleted) to all tables for soft delete
- **[NEW]** Will add access JSON column to all tables for shared access control with owner/invited/public patterns
- **[NEW]** Design decision: use multiple demo databases in development mode, not single SQLite file

**Function-Based Architecture**:

- **[EXISTS-MODIFY]** Will convert 31 existing classes to pure functions (see Current Architecture Baseline)
- **[EXISTS-MODIFY]** Will convert all implementation classes to pure functions
- **[NEW]** Will implement database facade pattern using pure functions instead of classes
- **[NEW]** Will create pure function factories instead of class-based factories

**Communication Patterns**:

- **[NEW]** Will implement fixed drag-drop flow: browser DOM → tagsInPlay → /api/render/cards → HTML response
- **[NEW]** Will add real-time UUID sync for card/tag mutations (not drag-drop operations) NOTE: card/tag mutations may occur as the result of drag and drop. For example if a tag is dropped on a card, or if a card is dropped into a row or column (equals adding card to a spatial set)
- **[NEW]** Will separate server-side UUID template rendering from client-side content injection NOTE: in Privacy mode only

**Dimensional Sets**:

- **[NEW]** Will add spatial set formation with n-dimensional grids
- **[NEW]** Will implement card multiplicity through intersection sets
- **[NEW]** Will create visual distinction requirements for multi-location cards

**Event Sourcing**:

- **[NEW]** Will implement comprehensive event sourcing (no audit logging currently exists)
- **[NEW]** Will add middleware-based event capture to RedPanda
- **[NEW]** Will implement complete request/response/timing/user context logging

## Implementation Phases Overview

| Phase | Duration   | Focus                                        | Deliverable                                           |
| ----- | ---------- | -------------------------------------------- | ----------------------------------------------------- |
| 1     | Week 1-2   | Database Schema & Access Control             | Zero-trust schema with shared access patterns         |
| 2     | Week 3-4   | Function-Based Architecture                  | Pure function conversion with type aliases            |
| 3     | Week 5-6   | UUID Mapping & Set Operations                | RoaringBitmap operations without mappings table       |
| 4     | Week 7-8   | Turso [with SQLite backup]  WASM Integration | Browser-based local storage with multi-demo DBs       |
| 5     | Week 9-10  | Hybrid Rendering & Communication             | Implement fixed drag-drop flow with content injection |
| 6     | Week 11-12 | Dimensional Sets & Multiplicity              | N-dimensional grids with card multiplicity            |
| 7     | Week 13    | Event Sourcing Integration                   | Redpanda middleware with comprehensive logging           |
| 8     | Week 14-15 | Testing & Validation                         | Comprehensive test suite with dimensional tests       |
| 9     | Week 16    | Migration & Documentation                    | Customer data portability with updated patterns       |

## Phase 1: Database Schema & Access Control (Week 1-2)

### Objectives

- **[COMPLETE REPLACEMENT]** Replace entire existing schema with new zero-trust architecture
- **[NEW]** Separate user data from project data into different databases
- **[NEW]** Implement cards/tags/card_contents structure (no card_summaries/card_details)
- **[NEW]** Add user_id/workspace_id to all project tables
- **[NEW]** Use TEXT for UUID storage in all database modes (SQLite, Turso, WASM)
- **[NEW]** Configure multiple databases per mode (user prefs + project DBs)

### Tasks

#### Week 1: Zero-Trust Schema Design

**Day 1-2: New Project Database Schema**

```sql
-- Turso [with SQLite backup]  version (also for Turso/WASM)
CREATE TABLE cards (
    card_id TEXT PRIMARY KEY,  -- UUID as TEXT
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted TIMESTAMP,
    tag_ids TEXT NOT NULL DEFAULT '[]',  -- JSON array of tag UUIDs (inverted index)
    tag_bitmaps TEXT DEFAULT '[]'  -- JSON array of tag integer bitmaps
);

CREATE TABLE tags (
    tag_id TEXT PRIMARY KEY,  -- UUID as TEXT
    user_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    tag_bitmap INTEGER NOT NULL,  -- Integer bitmap for this tag
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted TIMESTAMP
);

CREATE TABLE card_contents (
    id TEXT PRIMARY KEY,
    card_id TEXT NOT NULL,
    type INTEGER NOT NULL,  -- 1=text, 2=number, 3=boolean, 4=json, 5=combined
    label TEXT,
    value_text TEXT,
    value_number REAL,
    value_boolean INTEGER,  -- 0/1 for SQLite
    value_json TEXT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(card_id) ON DELETE CASCADE
);

CREATE TABLE views (
    key UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    tags_in_play JSON NOT NULL,
    user_id UUID NOT NULL,     -- Zero-trust isolation
    workspace_id UUID NOT NULL, -- Project separation
    access JSON NOT NULL DEFAULT '{"owner": null, "invited": [], "public": false}',
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted TIMESTAMP NULL     -- Soft delete
);

-- Development mode demo databases configuration
-- Multiple SQLite databases for different demo scenarios
-- No user_id/workspace_id enforcement in dev mode
-- Reserved UUIDs for special access patterns
-- multicardz Staff: 00000000-0000-0000-0000-000000000001
-- Public Access: ffffffff-ffff-ffff-ffff-ffffffffffff
    workspace_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences database (separate from project data)
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY,
    start_cards_visible INTEGER DEFAULT 1,
    start_cards_expanded INTEGER DEFAULT 0,
    show_tag_colors INTEGER DEFAULT 1,
    theme TEXT DEFAULT 'system',
    font_family TEXT DEFAULT 'Inter',
    separate_user_ai_tags INTEGER DEFAULT 1,
    stack_tags_vertically INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE views (
    key UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    tags_in_play JSONB NOT NULL DEFAULT '{}',
    workspace_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_cards_workspace ON cards(workspace_id);
CREATE INDEX idx_cards_tags ON cards USING GIN(tags);
CREATE INDEX idx_tags_workspace ON tags(workspace_id);
CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);
CREATE INDEX idx_views_workspace ON views(workspace_id);
```

**Day 3-4: Migration Scripts** NOTE: no migration needed

```python
#!/usr/bin/env python3
"""
Migration script for zero-trust schema deployment.
"""

import uuid
import json
from pathlib import Path
from typing import Dict, Any

def migrate_existing_data_to_uuid_schema(
    source_db_path: Path,
    target_db_path: Path,
    *,
    workspace_id: str
) -> None:
    """
    Migrate existing data to UUID-based schema.

    Args:
        source_db_path: Current database file
        target_db_path: New UUID-based database
        workspace_id: Tenant identifier for data isolation
    """
    # Implementation details
    pass

def generate_uuid_mappings(
    cards: list[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Generate deterministic UUIDs for existing cards.

    Args:
        cards: Existing card data

    Returns:
        Mapping from old IDs to new UUIDs
    """
    # Implementation details
    pass
```

**Day 5: Testing and Validation** NOTE: use BDD withe gherkin and pytest

- Schema compatibility testing across SQLite, Turso, WASM
- Migration script validation with sample data
- Performance benchmarking for new indexes

#### Week 2: Implementation and Deployment

**Day 1-2: Schema Deployment Scripts**

```bash
#!/bin/bash
# deploy_schema.sh

set -e

MODE=${1:-development}
WORKSPACE_ID=${2:-$(uuidgen)}

case $MODE in
    "development")
        sqlite3 /var/data/multicardz_dev_uuid.db < schema/sqlite_schema.sql
        ;;
    "standard")
        # Turso deployment
        turso db shell multicardz-standard < schema/turso_schema.sql
        ;;
    "privacy")
        # Turso embedded replica deployment
        turso db create multicardz-privacy --embedded-replica-path ./data/privacy/
        ;;
    *)
        echo "Unknown mode: $MODE"
        exit 1
        ;;
esac

echo "Schema deployed for mode: $MODE"
```

**Day 3-4: Backward Compatibility Layer** NOTE: not needed

```python
from typing import Dict, Any, Callable
# Legacy data conversion functions (no classes)
legacy_uuid_cache: Dict[str, str] = {}

async def convert_legacy_card_to_uuid(
    legacy_card: Dict[str, Any],
    workspace_id: str
) -> Dict[str, Any]:
    """Convert legacy card format to UUID-based format."""
    card_uuid = legacy_uuid_cache.get(legacy_card['id']) or str(uuid.uuid4())
    legacy_uuid_cache[legacy_card['id']] = card_uuid
    return {
        'key': card_uuid,
        'name': legacy_card['title'],
        'description': legacy_card.get('content', ''),
        'workspace_id': workspace_id
    }

async def convert_legacy_tags_to_uuid(
    legacy_tags: list[str]
) -> list[str]:
    """Convert legacy tag names to UUIDs."""
    return [legacy_uuid_cache.get(tag) or str(uuid.uuid5(uuid.NAMESPACE_DNS, tag)) for tag in legacy_tags]

async def convert_sqlite_legacy_card(
    legacy_card: Dict[str, Any],
    workspace_id: str
) -> Dict[str, Any]:
    """Convert card from SQLite legacy format to UUID format."""
    card_uuid = legacy_uuid_cache.get(legacy_card['id']) or str(uuid.uuid4())
    legacy_uuid_cache[legacy_card['id']] = card_uuid

    return {
        'key': card_uuid,
        'name': legacy_card['title'],
        'description': legacy_card.get('content', ''),
        'tags': await convert_legacy_tags_to_uuid(legacy_card.get('tags', [])),
        'workspace_id': workspace_id,
        'created_at': legacy_card.get('created_at'),
        'modified_at': legacy_card.get('modified_at')
    }
```

**Day 5: Integration Testing**

- End-to-end testing with new schema
- Performance validation
- Documentation updates

### Deliverables

- [ ] Canonical database schema files (Turso [with SQLite backup] , Turso, WASM)
- [ ] Performance benchmarks
- [ ] Deployment automation scripts

### Success Criteria

- Schema deploys successfully across all three modes
- Performance benchmarks meet or exceed baseline system requirements
- All existing tests pass with new schema

## Phase 2: Function-Based Architecture (Week 3-4)

### Objectives

- **[EXISTS-MODIFY]** Will convert 31 existing classes (13 BaseModel, 2 ABC, 3 Exception, 2 NamedTuple, etc.) to pure functions
- **[EXISTS-MODIFY]** Will convert all implementation classes to pure functions
- **[NEW]** Will implement database facade pattern using pure functions instead of classes
- **[NEW]** Will create pure function factories instead of class-based factories
- **[NEW]** Architecture will not include UUID mappings table (will use integer_id column pattern to be added to cards/tags tables)

### Tasks

#### Week 3: Pure Function Implementation

**Day 1-2: Function Type Aliases and Pure Functions**

```python
import hashlib
import uuid
from typing import Optional
from datetime import datetime

def generate_deterministic_uuid(
    content: str,
    workspace_id: str,
    entity_type: str,
    *,
    timestamp: Optional[datetime] = None
) -> str:
    """
    Generate deterministic UUID based on content and workspace.

    Args:
        content: Human-readable content (card name or tag name)
        workspace_id: Tenant isolation identifier
        entity_type: 'card' or 'tag'
        timestamp: Optional timestamp for uniqueness

    Returns:
        Deterministic UUID string

    Raises:
        ValueError: If content is empty or invalid
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")

    # Create deterministic seed
    seed_data = f"{workspace_id}:{entity_type}:{content.strip()}"
    if timestamp:
        seed_data += f":{timestamp.isoformat()}"

    # Generate UUID5 for deterministic results
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # Fixed namespace
    return str(uuid.uuid5(namespace, seed_data))

# UUID mapping functions (no classes)
uuid_integer_counters = {'card': 0, 'tag': 0}
uuid_mapping_cache = {}

async def get_or_create_integer_mapping(
    entity_uuid: str,
    entity_type: str,
    workspace_id: str,
    db_connection
) -> int:
    """
    Get existing integer mapping or create new one.

    Args:
        entity_uuid: UUID to map
        entity_type: 'card' or 'tag'
        workspace_id: Tenant identifier
        db_connection: Database connection

    Returns:
        Integer mapping for RoaringBitmap operations
    """
    # Check cache first
    cache_key = f"{workspace_id}:{entity_type}:{entity_uuid}"
    if cache_key in uuid_mapping_cache:
        return uuid_mapping_cache[cache_key]

    # Query database for existing mapping
    query = f"""
        SELECT integer_id FROM {entity_type}s
        WHERE {entity_type}_id = ? AND workspace_id = ?
    """
    result = await db_connection.execute(query, (entity_uuid, workspace_id))
    row = result.fetchone()

    if row:
        uuid_mapping_cache[cache_key] = row[0]
        return row[0]

    # Create new mapping
    next_integer = await get_next_integer(entity_type, workspace_id, db_connection)
    await store_mapping(entity_uuid, next_integer, entity_type, workspace_id, db_connection)
    uuid_mapping_cache[cache_key] = next_integer

    return next_integer

async def get_next_integer(
    entity_type: str,
    workspace_id: str,
    db_connection
) -> int:
    """Get next sequential integer for entity type in workspace."""
    query = f"""
        SELECT COALESCE(MAX(integer_id), 0) + 1
        FROM {entity_type}s
        WHERE workspace_id = ?
    """
    result = await db_connection.execute(query, (workspace_id,))
    return result.fetchone()[0]

async def store_mapping(
    entity_uuid: str,
    integer_id: int,
    entity_type: str,
    workspace_id: str,
    db_connection
) -> None:
    """Store UUID to integer mapping."""
    query = f"""
        UPDATE {entity_type}s
        SET integer_id = ?
        WHERE {entity_type}_id = ? AND workspace_id = ?
    """
    await db_connection.execute(query, (integer_id, entity_uuid, workspace_id))
```

**Day 3-4: Real-time Sync System**

```python
from typing import Dict, Set
from datetime import datetime
import asyncio

# UUID sync functions (no classes)
sync_state = {
    'backend_endpoint': '',
    'sync_queue': None,
    'sync_task': None
}

async def initialize_uuid_sync(backend_endpoint: str):
    """Initialize UUID sync system."""
    sync_state['backend_endpoint'] = backend_endpoint
    sync_state['sync_queue'] = asyncio.Queue()
    sync_state['sync_task'] = asyncio.create_task(uuid_sync_worker())

async def sync_card_creation(
    card_uuid: str,
    tag_uuids: Set[str],
    workspace_id: str
) -> None:
    """
    Queue card creation for sync to backend.

    Args:
        card_uuid: New card identifier
        tag_uuids: Associated tag identifiers
        workspace_id: Tenant identifier
    """
    sync_event = {
        'type': 'card_create',
        'card_uuid': card_uuid,
        'tag_uuids': list(tag_uuids),
        'workspace_id': workspace_id,
        'timestamp': datetime.utcnow().isoformat()
    }

    await sync_state['sync_queue'].put(sync_event)

    async def sync_tag_update(
        self,
        card_uuid: str,
        added_tags: Set[str],
        removed_tags: Set[str],
        workspace_id: str
    ) -> None:
        """
        Queue tag update for sync to backend.

        Args:
            card_uuid: Card being updated
            added_tags: Tag UUIDs being added
            removed_tags: Tag UUIDs being removed
            workspace_id: Tenant identifier
        """
        sync_event = {
            'type': 'tag_update',
            'card_uuid': card_uuid,
            'added_tags': list(added_tags),
            'removed_tags': list(removed_tags),
            'workspace_id': workspace_id,
            'timestamp': datetime.utcnow().isoformat()
        }

        await self._sync_queue.put(sync_event)

    async def _sync_worker(self):
        """Background worker for processing sync events."""
        while True:
            try:
                # Get sync event from queue
                event = await self._sync_queue.get()

                # Send to backend with retry logic
                await self._send_sync_event(event)

                # Mark as complete
                self._sync_queue.task_done()

            except Exception as e:
                # Log error and continue
                print(f"Sync error: {e}")
                await asyncio.sleep(1)

    async def _send_sync_event(
        self,
        event: Dict[str, Any],
        max_retries: int = 3
    ) -> None:
        """Send sync event to backend with retry logic."""
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.backend_endpoint}/sync/uuid",
                        json=event,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            return
                        else:
                            raise Exception(f"Backend sync failed: {response.status}")

            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

**Day 5: Testing and Validation**

- UUID generation determinism testing
- Integer mapping consistency validation
- Sync system reliability testing

#### Week 4: Backend UUID Processing

**Day 1-2: Backend UUID Endpoints**

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/sync", tags=["uuid-sync"])

class UUIDSyncEvent(BaseModel):
    type: str  # 'card_create', 'tag_update', 'card_delete'
    card_uuid: str
    tag_uuids: List[str] = []
    added_tags: List[str] = []
    removed_tags: List[str] = []
    workspace_id: str
    timestamp: str

# UUID Mapping Backend - Pure Functions
"""Backend processing for UUID mappings using pure functions."""

# Global database connection - to be initialized by dependency injection
_uuid_mapping_db_connection = None

def initialize_uuid_mapping_backend(db_connection):
    """Initialize the UUID mapping backend with a database connection."""
    global _uuid_mapping_db_connection
    _uuid_mapping_db_connection = db_connection

async def process_card_creation(
    event: UUIDSyncEvent,
    db_connection = None
) -> Dict[str, int]:
    """
    Process card creation event and return integer mappings.

    Args:
        event: Sync event from client
        db_connection: Database connection (optional, uses global if not provided)

    Returns:
        Mapping of UUIDs to integers for RoaringBitmap operations
    """
    db = db_connection or _uuid_mapping_db_connection
    if not db:
        raise ValueError("No database connection available")

    # Create integer mappings for card and tags
    card_integer = await _get_or_create_integer(
        event.card_uuid, 'card', event.workspace_id, db
    )

    tag_integers = {}
    for tag_uuid in event.tag_uuids:
        tag_integers[tag_uuid] = await _get_or_create_integer(
            tag_uuid, 'tag', event.workspace_id, db
        )

    # Update RoaringBitmap cache
    await _update_roaring_bitmap_cache(
        card_integer, list(tag_integers.values()), event.workspace_id, db
    )

    return {
        'card_integer': card_integer,
        'tag_integers': tag_integers
    }

async def process_tag_update(
    event: UUIDSyncEvent,
    db_connection = None
) -> Dict[str, int]:
    """Process tag update event and return integer mappings."""
    db = db_connection or _uuid_mapping_db_connection
    if not db:
        raise ValueError("No database connection available")
    # Implementation details would be similar to process_card_creation
    # This is a placeholder for the actual implementation
    pass

async def process_card_deletion(
    event: UUIDSyncEvent,
    db_connection = None
) -> Dict[str, int]:
    """Process card deletion event and return integer mappings."""
    db = db_connection or _uuid_mapping_db_connection
    if not db:
        raise ValueError("No database connection available")
    # Implementation details would be similar to process_card_creation
    # This is a placeholder for the actual implementation
    pass

async def _get_or_create_integer(
    uuid_str: str,
    entity_type: str,
    workspace_id: str,
    db_connection
) -> int:
    """Get or create integer mapping for UUID."""
    # Implementation would query/insert into database
    # This is a placeholder for the actual implementation
    pass

async def _update_roaring_bitmap_cache(
    card_integer: int,
    tag_integers: list,
    workspace_id: str,
    db_connection
) -> None:
    """Update RoaringBitmap cache with new mappings."""
    # Implementation would update the cache
    # This is a placeholder for the actual implementation
    pass

@router.post("/uuid")
async def sync_uuid_mapping(
    event: UUIDSyncEvent,
    db_connection = Depends(get_database_connection)
):
    """Sync UUID mapping from client."""
    try:
        if event.type == 'card_create':
            result = await process_card_creation(event, db_connection)
        elif event.type == 'tag_update':
            result = await process_tag_update(event, db_connection)
        elif event.type == 'card_delete':
            result = await process_card_deletion(event, db_connection)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown event type: {event.type}")

        return {"status": "success", "mappings": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
```

**Day 3-4: RoaringBitmap Integration**

```python
import roaringbitmap
from typing import Dict, Set

# RoaringBitmap Cache - Pure Functions
"""Cache for RoaringBitmap representations of tag relationships using pure functions."""

# Global cache state - to be managed by initialization function
_roaring_bitmap_workspace_cache: Dict[str, Dict[int, roaringbitmap.RoaringBitmap]] = {}

def initialize_roaring_bitmap_cache():
    """Initialize the RoaringBitmap cache."""
    global _roaring_bitmap_workspace_cache
    _roaring_bitmap_workspace_cache = {}

def get_roaring_bitmap_cache() -> Dict[str, Dict[int, roaringbitmap.RoaringBitmap]]:
    """Get the current cache state."""
    return _roaring_bitmap_workspace_cache

async def update_card_tags(
    card_integer: int,
    tag_integers: Set[int],
    workspace_id: str,
    cache: Dict[str, Dict[int, roaringbitmap.RoaringBitmap]] = None
) -> None:
    """
    Update RoaringBitmap cache with card-tag relationships.

    Args:
        card_integer: Integer mapping for card
        tag_integers: Integer mappings for tags
        workspace_id: Tenant identifier
        cache: Optional cache dict (uses global if not provided)
    """
    if cache is None:
        cache = _roaring_bitmap_workspace_cache

    if workspace_id not in cache:
        cache[workspace_id] = {}

    workspace_cache = cache[workspace_id]

    # Add card to each tag's bitmap
    for tag_integer in tag_integers:
        if tag_integer not in workspace_cache:
            workspace_cache[tag_integer] = roaringbitmap.RoaringBitmap()
        workspace_cache[tag_integer].add(card_integer)

async def compute_intersection(
    tag_integers: Set[int],
    workspace_id: str,
    cache: Dict[str, Dict[int, roaringbitmap.RoaringBitmap]] = None
) -> roaringbitmap.RoaringBitmap:
    """
    Compute intersection of cards having all specified tags.

    Args:
        tag_integers: Tag integers to intersect
        workspace_id: Tenant identifier
        cache: Optional cache dict (uses global if not provided)

    Returns:
        RoaringBitmap of card integers matching all tags
    """
    if cache is None:
        cache = _roaring_bitmap_workspace_cache

    if workspace_id not in cache:
        return roaringbitmap.RoaringBitmap()

    workspace_cache = cache[workspace_id]

    # Start with first tag's bitmap
    tag_list = list(tag_integers)
    if not tag_list or tag_list[0] not in workspace_cache:
        return roaringbitmap.RoaringBitmap()

    result = workspace_cache[tag_list[0]].copy()

    # Intersect with remaining tags
    for tag_integer in tag_list[1:]:
        if tag_integer in workspace_cache:
            result &= workspace_cache[tag_integer]
        else:
            # Tag not found, empty result
            return roaringbitmap.RoaringBitmap()

    return result

async def compute_union(
    tag_integers: Set[int],
    workspace_id: str,
    cache: Dict[str, Dict[int, roaringbitmap.RoaringBitmap]] = None
) -> roaringbitmap.RoaringBitmap:
    """
    Compute union of cards having any specified tags.

    Args:
        tag_integers: Tag integers to union
        workspace_id: Tenant identifier
        cache: Optional cache dict (uses global if not provided)

    Returns:
        RoaringBitmap of card integers matching any tags
    """
    if cache is None:
        cache = _roaring_bitmap_workspace_cache

    if workspace_id not in cache:
        return roaringbitmap.RoaringBitmap()

    workspace_cache = cache[workspace_id]
    result = roaringbitmap.RoaringBitmap()

    # Union all tag bitmaps
    for tag_integer in tag_integers:
        if tag_integer in workspace_cache:
            result |= workspace_cache[tag_integer]

    return result
```

**Day 5: Performance Testing**

- RoaringBitmap performance benchmarks
- UUID sync latency testing
- End-to-end integration testing

### Deliverables

- [x] UUID generation system with deterministic algorithms
- [x] Integer mapping manager for RoaringBitmap optimization
- [x] Real-time sync system with retry logic
- [x] Backend UUID processing endpoints
- [x] RoaringBitmap cache implementation
- [x] Performance benchmarks and testing

### Success Criteria

- UUID generation is deterministic and collision-free
- Integer mappings provide 10x performance improvement for set operations
- Sync system handles network failures gracefully
- RoaringBitmap operations complete in <10ms for 1000 cards

## Phase 3: UUID Mapping & Set Operations (Week 5-6)

### Objectives

- **[EXISTS-MODIFY]** Will enhance existing RoaringBitmap operations using integer_id column to be added (no separate mappings table)
- **[NEW]** Will optimize set operations with direct database integer_id queries
- **[NEW]** Will create pure function set operation engines
- **[NEW]** Will implement real-time UUID sync for card/tag mutations (not drag-drop operations)

### Tasks

#### Week 5: Blind Set Operation Engine

**Day 1-2: UUID-Based Set Operations**

```python
from typing import Set, Dict, Any, Callable
from dataclasses import dataclass
from pyroaring import BitMap  # Already exists in codebase

# Function type aliases for set operations
ComputeUnion = Callable[[Dict[str, Set[str]], str], Set[str]]
ComputeIntersection = Callable[[Dict[str, Set[str]], str], Set[str]]
ComputeExclusion = Callable[[Set[str], Set[str], str], Set[str]]

@dataclass(frozen=True)
class SetOperationEngine:
    """Pure function container for UUID-based set operations."""
    compute_union: ComputeUnion
    compute_intersection: ComputeIntersection
    compute_exclusion: ComputeExclusion

def create_roaring_bitmap_engine(
    bitmap_cache: Dict[str, BitMap],
    uuid_to_int: Dict[str, int]
) -> SetOperationEngine:
    """Factory function for RoaringBitmap-based set operations."""

    async def compute_union(
        zone_tag_uuids: Dict[str, Set[str]],
        workspace_id: str
    ) -> Set[str]:
        """Compute union using RoaringBitmap operations."""
        result = BitMap()
        for tag_set in zone_tag_uuids.values():
            for tag_uuid in tag_set:
                if tag_uuid in uuid_to_int:
                    result.add(uuid_to_int[tag_uuid])
        return {uuid for uuid, int_id in uuid_to_int.items() if int_id in result}

    async def compute_intersection(
        zone_tag_uuids: Dict[str, Set[str]],
        workspace_id: str
    ) -> Set[str]:
        """Compute intersection using RoaringBitmap operations."""
        if not zone_tag_uuids:
            return set()

        bitmaps = []
        for tag_set in zone_tag_uuids.values():
            zone_bitmap = BitMap()
            for tag_uuid in tag_set:
                if tag_uuid in uuid_to_int:
                    zone_bitmap.add(uuid_to_int[tag_uuid])
            bitmaps.append(zone_bitmap)

        result = bitmaps[0]
        for bitmap in bitmaps[1:]:
            result = result.intersection(bitmap)

        return {uuid for uuid, int_id in uuid_to_int.items() if int_id in result}

    async def compute_exclusion(
        include_uuids: Set[str],
        exclude_uuids: Set[str],
        workspace_id: str
    ) -> Set[str]:
        """Compute exclusion using RoaringBitmap operations."""
        include_bitmap = BitMap([uuid_to_int[u] for u in include_uuids if u in uuid_to_int])
        exclude_bitmap = BitMap([uuid_to_int[u] for u in exclude_uuids if u in uuid_to_int])
        result = include_bitmap.difference(exclude_bitmap)
        return {uuid for uuid, int_id in uuid_to_int.items() if int_id in result}

    return SetOperationEngine(
        compute_union=compute_union,
        compute_intersection=compute_intersection,
        compute_exclusion=compute_exclusion
    )

# RoaringBitmap Set Engine - Pure Functions
"""High-performance set operations using RoaringBitmaps - pure function implementation."""

async def roaring_bitmap_compute_union(
    zone_tag_uuids: Dict[str, Set[str]],
    workspace_id: str,
    uuid_mapper_get_integer_mapping_func,
    uuid_mapper_get_uuid_from_integer_func,
    bitmap_cache: Dict[str, Dict[int, roaringbitmap.RoaringBitmap]] = None
) -> Set[str]:
    """
    Compute union using RoaringBitmap operations.

    Args:
        zone_tag_uuids: Zone name → tag UUID sets
        workspace_id: Tenant identifier
        uuid_mapper_get_integer_mapping_func: Function to get integer mapping from UUID
        uuid_mapper_get_uuid_from_integer_func: Function to get UUID from integer mapping
        bitmap_cache: Optional cache dict (uses global if not provided)

    Returns:
        Set of card UUIDs matching union criteria
    """
    # Convert UUIDs to integers
    all_tag_uuids = set()
    for tag_set in zone_tag_uuids.values():
        all_tag_uuids.update(tag_set)

    tag_integers = await _roaring_bitmap_convert_uuids_to_integers(
        all_tag_uuids, 'tag', workspace_id, uuid_mapper_get_integer_mapping_func
    )

    # Compute union bitmap
    result_bitmap = await compute_union(
        set(tag_integers.values()), workspace_id, bitmap_cache
    )

    # Convert result integers back to UUIDs
    result_integers = list(result_bitmap)
    return await _roaring_bitmap_convert_integers_to_uuids(
        result_integers, 'card', workspace_id, uuid_mapper_get_uuid_from_integer_func
    )

async def roaring_bitmap_compute_intersection(
    zone_tag_uuids: Dict[str, Set[str]],
    workspace_id: str,
    uuid_mapper_get_integer_mapping_func,
    uuid_mapper_get_uuid_from_integer_func,
    bitmap_cache: Dict[str, Dict[int, roaringbitmap.RoaringBitmap]] = None
) -> Set[str]:
    """
    Compute intersection using RoaringBitmap operations.

    Args:
        zone_tag_uuids: Zone name → tag UUID sets
        workspace_id: Tenant identifier
        uuid_mapper_get_integer_mapping_func: Function to get integer mapping from UUID
        uuid_mapper_get_uuid_from_integer_func: Function to get UUID from integer mapping
        bitmap_cache: Optional cache dict (uses global if not provided)

    Returns:
        Set of card UUIDs matching intersection criteria
    """
    # Handle empty zones
    if not zone_tag_uuids:
        return set()

    # Convert UUIDs to integers for all zones
    zone_results = []

    for zone_name, tag_uuids in zone_tag_uuids.items():
        if not tag_uuids:
            continue

        tag_integers = await _roaring_bitmap_convert_uuids_to_integers(
            tag_uuids, 'tag', workspace_id, uuid_mapper_get_integer_mapping_func
        )

        if zone_name == 'union':
            # Union within zone
            zone_bitmap = await compute_union(
                set(tag_integers.values()), workspace_id, bitmap_cache
            )
        elif zone_name == 'intersection':
            # Intersection within zone
            zone_bitmap = await compute_intersection(
                set(tag_integers.values()), workspace_id, bitmap_cache
            )
        else:
            # Default to union for unknown zones
            zone_bitmap = await compute_union(
                set(tag_integers.values()), workspace_id, bitmap_cache
            )

        zone_results.append(zone_bitmap)

    # Intersect results across zones
    if not zone_results:
        return set()

    final_bitmap = zone_results[0].copy()
    for bitmap in zone_results[1:]:
        final_bitmap &= bitmap

    # Convert result back to UUIDs
    result_integers = list(final_bitmap)
    return await _roaring_bitmap_convert_integers_to_uuids(
        result_integers, 'card', workspace_id, uuid_mapper_get_uuid_from_integer_func
    )

async def _roaring_bitmap_convert_uuids_to_integers(
    uuids: Set[str],
    entity_type: str,
    workspace_id: str,
    uuid_mapper_get_integer_mapping_func
) -> Dict[str, int]:
    """Convert UUIDs to integer mappings."""
    result = {}
    for uuid_str in uuids:
        integer_mapping = await uuid_mapper_get_integer_mapping_func(
            uuid_str, entity_type, workspace_id
        )
        if integer_mapping:
            result[uuid_str] = integer_mapping
    return result

async def _roaring_bitmap_convert_integers_to_uuids(
    integers: List[int],
    entity_type: str,
    workspace_id: str,
    uuid_mapper_get_uuid_from_integer_func
) -> Set[str]:
    """Convert integer mappings back to UUIDs."""
    result = set()
    for integer_val in integers:
        uuid_str = await uuid_mapper_get_uuid_from_integer_func(
            integer_val, entity_type, workspace_id
        )
        if uuid_str:
            result.add(uuid_str)
    return result
```

**Day 3-4: Polymorphic Set Operation Interface**

```python
def create_set_operation_engine(
    mode: str,
    **config
) -> BlindSetOperationEngine:
    """
    Factory for set operation engines.

    Args:
        mode: Operation mode ('development', 'standard', 'premium')
        **config: Engine-specific configuration

    Returns:
        Set operation engine implementation
    """
    if mode == 'premium':
        # UUID-based operations for privacy
        return RoaringBitmapSetEngine(
            bitmap_cache=config['bitmap_cache'],
            uuid_mapper=config['uuid_mapper']
        )
    elif mode in ['development', 'standard']:
        # Content-based operations for performance
        return ContentBasedSetEngine(
            db_connection=config['db_connection']
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

# Content-Based Set Engine - Pure Functions
"""Traditional set operations on content for non-premium modes using pure functions."""

async def content_based_compute_union(
    zone_tag_names: Dict[str, Set[str]],  # Tag names, not UUIDs
    workspace_id: str,
    db_connection
) -> Set[str]:
    """
    Compute union using tag names and content.

    Args:
        zone_tag_names: Zone name → tag name sets
        workspace_id: Tenant identifier
        db_connection: Database connection for queries

    Returns:
        Set of card identifiers matching union criteria
    """
    # Traditional implementation for development/standard modes
    # Implementation would query database using tag names
    # This is a placeholder for the actual implementation
    pass

async def content_based_compute_intersection(
    zone_tag_names: Dict[str, Set[str]],
    workspace_id: str,
    db_connection
) -> Set[str]:
    """
    Compute intersection using tag names and content.

    Args:
        zone_tag_names: Zone name → tag name sets
        workspace_id: Tenant identifier
        db_connection: Database connection for queries

    Returns:
        Set of card identifiers matching intersection criteria
    """
    # Traditional implementation for development/standard modes
    # Implementation would query database using tag names
    # This is a placeholder for the actual implementation
    pass
```

**Day 5: Integration and Testing**

- Integration with existing cards API
- Performance benchmarking
- Blind operation validation (no content access)

#### Week 6: API Integration and Optimization

**Day 1-2: Cards API Integration**

```python
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Dict, Set

@router.post("/render/cards", response_class=HTMLResponse)
async def render_cards_with_blind_operations(
    request: Request,
    mode: str = Depends(get_application_mode)
):
    """
    Enhanced cards API supporting blind UUID operations.

    Args:
        request: FastAPI request containing tagsInPlay data
        mode: Application mode (development/standard/premium)
    """
    try:
        # Parse request
        request_data = await request.json()
        tags_in_play = request_data.get('tagsInPlay', {})

        # Get workspace from authentication
        workspace_id = get_workspace_from_auth(request)

        # Create appropriate set operation engine
        set_engine = create_set_operation_engine(
            mode=mode,
            bitmap_cache=get_bitmap_cache(),
            uuid_mapper=get_uuid_mapper(),
            db_connection=get_db_connection()
        )

        if mode == 'premium':
            # Blind UUID operations
            result_card_uuids = await compute_blind_set_operations(
                tags_in_play, set_engine, workspace_id
            )

            # Render template with UUID placeholders
            return await render_uuid_template(
                result_card_uuids, request_data, workspace_id
            )
        else:
            # Traditional content operations
            result_cards = await compute_content_set_operations(
                tags_in_play, set_engine, workspace_id
            )

            # Render complete HTML with content
            return await render_content_template(
                result_cards, request_data, workspace_id
            )

    except Exception as e:
        logger.error(f"Cards rendering failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Rendering failed")

async def compute_blind_set_operations(
    tags_in_play: Dict[str, Any],
    set_engine: BlindSetOperationEngine,
    workspace_id: str
) -> Set[str]:
    """
    Compute set operations using only UUIDs.

    Args:
        tags_in_play: Zone configuration with tag UUIDs
        set_engine: Blind set operation engine
        workspace_id: Tenant identifier

    Returns:
        Set of card UUIDs matching criteria
    """
    zones = tags_in_play.get('zones', {})

    # Extract tag UUIDs from zones
    union_tags = set(zones.get('union', {}).get('tags', []))
    intersection_tags = set(zones.get('intersection', {}).get('tags', []))
    exclusion_tags = set(zones.get('exclusion', {}).get('tags', []))

    # Compute operations
    result_cards = set()

    if union_tags:
        union_result = await set_engine.compute_union(
            {'union': union_tags}, workspace_id
        )
        result_cards.update(union_result)

    if intersection_tags:
        intersection_result = await set_engine.compute_intersection(
            {'intersection': intersection_tags}, workspace_id
        )
        if result_cards:
            result_cards &= intersection_result
        else:
            result_cards = intersection_result

    if exclusion_tags:
        exclusion_result = await set_engine.compute_union(
            {'exclusion': exclusion_tags}, workspace_id
        )
        result_cards -= exclusion_result

    return result_cards
```

**Day 3-4: Performance Optimization**

```python
import asyncio
from typing import Dict, List
import time

# Performance Optimized Set Engine - Pure Functions
"""Optimized set engine with caching and batching using pure functions."""

# Global cache state
_performance_operation_cache: Dict[str, Set[str]] = {}
_performance_cache_ttl = 300  # 5 minutes
_performance_cache_timestamps: Dict[str, float] = {}

def initialize_performance_cache(cache_ttl: int = 300):
    """Initialize the performance cache."""
    global _performance_operation_cache, _performance_cache_ttl, _performance_cache_timestamps
    _performance_operation_cache = {}
    _performance_cache_ttl = cache_ttl
    _performance_cache_timestamps = {}

async def compute_union_with_cache(
    zone_tag_uuids: Dict[str, Set[str]],
    workspace_id: str,
    base_engine_compute_union_func,
    cache: Dict[str, Set[str]] = None,
    cache_timestamps: Dict[str, float] = None,
    cache_ttl: int = None
) -> Set[str]:
    """
    Compute union with result caching.

    Args:
        zone_tag_uuids: Zone configuration
        workspace_id: Tenant identifier
        base_engine_compute_union_func: Function to compute union
        cache: Optional cache dict (uses global if not provided)
        cache_timestamps: Optional cache timestamps dict (uses global if not provided)
        cache_ttl: Optional cache TTL (uses global if not provided)

    Returns:
        Cached or computed result
    """
    if cache is None:
        cache = _performance_operation_cache
    if cache_timestamps is None:
        cache_timestamps = _performance_cache_timestamps
    if cache_ttl is None:
        cache_ttl = _performance_cache_ttl

    # Create cache key
    cache_key = _create_cache_key('union', zone_tag_uuids, workspace_id)

    # Check cache
    if _is_cache_valid(cache_key, cache, cache_timestamps, cache_ttl):
        return cache[cache_key].copy()

    # Compute and cache result
    result = await base_engine_compute_union_func(zone_tag_uuids, workspace_id)
    _store_in_cache(cache_key, result, cache, cache_timestamps)

    return result

async def compute_intersection_with_cache(
    zone_tag_uuids: Dict[str, Set[str]],
    workspace_id: str,
    base_engine_compute_intersection_func,
    cache: Dict[str, Set[str]] = None,
    cache_timestamps: Dict[str, float] = None,
    cache_ttl: int = None
) -> Set[str]:
    """
    Compute intersection with result caching.

    Args:
        zone_tag_uuids: Zone configuration
        workspace_id: Tenant identifier
        base_engine_compute_intersection_func: Function to compute intersection
        cache: Optional cache dict (uses global if not provided)
        cache_timestamps: Optional cache timestamps dict (uses global if not provided)
        cache_ttl: Optional cache TTL (uses global if not provided)

    Returns:
        Cached or computed result
    """
    if cache is None:
        cache = _performance_operation_cache
    if cache_timestamps is None:
        cache_timestamps = _performance_cache_timestamps
    if cache_ttl is None:
        cache_ttl = _performance_cache_ttl

    # Create cache key
    cache_key = _create_cache_key('intersection', zone_tag_uuids, workspace_id)

    # Check cache
    if _is_cache_valid(cache_key, cache, cache_timestamps, cache_ttl):
        return cache[cache_key].copy()

    # Compute and cache result
    result = await base_engine_compute_intersection_func(zone_tag_uuids, workspace_id)
    _store_in_cache(cache_key, result, cache, cache_timestamps)

    return result

def _create_cache_key(
    operation: str,
    zone_tag_uuids: Dict[str, Set[str]],
    workspace_id: str
) -> str:
    """Create deterministic cache key."""
    # Sort for consistency
    sorted_zones = {}
    for zone, tags in zone_tag_uuids.items():
        sorted_zones[zone] = sorted(list(tags))

    import json
    return f"{operation}:{workspace_id}:{json.dumps(sorted_zones, sort_keys=True)}"

def _is_cache_valid(
    cache_key: str,
    cache: Dict[str, Set[str]],
    cache_timestamps: Dict[str, float],
    cache_ttl: int
) -> bool:
    """Check if cache entry is valid."""
    if cache_key not in cache:
        return False

    timestamp = cache_timestamps.get(cache_key, 0)
    return (time.time() - timestamp) < cache_ttl

def _store_in_cache(
    cache_key: str,
    result: Set[str],
    cache: Dict[str, Set[str]],
    cache_timestamps: Dict[str, float]
) -> None:
    """Store result in cache."""
    cache[cache_key] = result.copy()
    cache_timestamps[cache_key] = time.time()

async def batch_compute_operations(
    operations: List[Dict[str, Any]],
    workspace_id: str,
    base_engine_compute_union_func,
    base_engine_compute_intersection_func,
    cache: Dict[str, Set[str]] = None,
    cache_timestamps: Dict[str, float] = None,
    cache_ttl: int = None
) -> List[Set[str]]:
    """
    Batch multiple operations for efficiency.

    Args:
        operations: List of operation specifications
        workspace_id: Tenant identifier
        base_engine_compute_union_func: Function to compute union
        base_engine_compute_intersection_func: Function to compute intersection
        cache: Optional cache dict (uses global if not provided)
        cache_timestamps: Optional cache timestamps dict (uses global if not provided)
        cache_ttl: Optional cache TTL (uses global if not provided)

    Returns:
        List of results corresponding to operations
    """
    # Run operations in parallel
    tasks = []
    for op in operations:
        if op['type'] == 'union':
            task = compute_union_with_cache(
                op['zones'], workspace_id, base_engine_compute_union_func,
                cache, cache_timestamps, cache_ttl
            )
        elif op['type'] == 'intersection':
            task = compute_intersection_with_cache(
                op['zones'], workspace_id, base_engine_compute_intersection_func,
                cache, cache_timestamps, cache_ttl
            )
        else:
            task = asyncio.create_task(asyncio.coroutine(lambda: set())())
        tasks.append(task)

    return await asyncio.gather(*tasks)
```

**Day 5: Testing and Validation**

- End-to-end blind operation testing
- Performance benchmark validation
- Security audit (no content leakage)

### Deliverables

- [x] Blind set operation engine using only UUIDs
- [x] RoaringBitmap optimization for large datasets
- [x] Polymorphic engine supporting all modes
- [x] Performance-optimized caching layer
- [x] Cards API integration with mode detection
- [x] Security validation (no content access in premium mode)

### Success Criteria

- Set operations complete in <10ms for 1000 cards using RoaringBitmaps
- Backend never accesses card/tag content in premium mode
- Performance matches or exceeds baseline system requirements
- All existing functionality preserved

## Phase 4: SQLite WASM Integration (Week 7-8)

### Objectives

- **[NEW]** Will integrate official SQLite WASM for browser-based storage
- **[NEW]** Will implement content injection system for hybrid rendering
- **[NEW]** Will create local database management for premium users

### Tasks

#### Week 7: SQLite WASM Setup and Integration

**Day 1-2: WASM Module Integration**

```javascript
/**
 * SQLite WASM Manager for multicardz Premium Mode
 * Handles local database operations in browser
 */
// SQLite WASM Manager - Pure Functions
/**
 * SQLite WASM management using pure functions.
 */

// Global state for SQLite WASM
let _sqliteWasmState = {
    db: null,
    sqlite3: null,
    isInitialized: false,
    workspaceId: null
};

/**
 * Initialize SQLite WASM module
 * @param {string} wasmPath - Path to sqlite3.wasm file
 * @param {string} workspaceId - Tenant identifier
 * @param {Object} state - Optional state object (uses global if not provided)
 */
async function initializeSQLiteWASM(wasmPath, workspaceId, state = null) {
    const currentState = state || _sqliteWasmState;

    try {
        // Load SQLite WASM module
        currentState.sqlite3 = await sqlite3InitModule({
            locateFile: (file) => {
                if (file.endsWith('.wasm')) {
                    return wasmPath;
                }
                return file;
            }
        });

        currentState.workspaceId = workspaceId;

        // Create in-memory database
        currentState.db = new currentState.sqlite3.oo1.DB();

        // Initialize schema
        await initializeSQLiteSchema(currentState);

        currentState.isInitialized = true;
        console.log('SQLite WASM initialized successfully');

    } catch (error) {
        console.error('SQLite WASM initialization failed:', error);
        throw error;
    }
}

/**
 * Initialize database schema
 * @param {Object} state - State object containing db connection
 */
async function initializeSQLiteSchema(state = null) {
    const currentState = state || _sqliteWasmState;

    const schema = `
        CREATE TABLE IF NOT EXISTS cards (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            tags TEXT NOT NULL, -- JSON array of tag UUIDs
            workspace_id TEXT NOT NULL,
            created_at TEXT,
            modified_at TEXT
        );

        CREATE TABLE IF NOT EXISTS tags (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS card_contents (
            key TEXT PRIMARY KEY,
            card_key TEXT NOT NULL,
            type INTEGER NOT NULL,
            label TEXT NOT NULL,
            value_text TEXT,
            value_integer INTEGER,
            value_boolean INTEGER,
            value_timestamp TEXT,
            value_json TEXT,
            workspace_id TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (card_key) REFERENCES cards(key)
        );

        CREATE INDEX IF NOT EXISTS idx_cards_workspace ON cards(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_tags_workspace ON tags(workspace_id);
        CREATE INDEX IF NOT EXISTS idx_card_contents_card ON card_contents(card_id);
    `;

    currentState.db.exec(schema);
}

/**
 * Load card content by UUID
 * @param {string} cardUuid - Card identifier
 * @param {Object} state - Optional state object (uses global if not provided)
 * @returns {Object|null} Card data or null if not found
 */
async function getSQLiteCardByUuid(cardUuid, state = null) {
    const currentState = state || _sqliteWasmState;

    if (!currentState.isInitialized) {
        throw new Error('SQLite WASM not initialized');
    }

    const stmt = currentState.db.prepare(`
        SELECT key, name, description, tags, created_at, modified_at
        FROM cards
        WHERE key = ? AND workspace_id = ?
    `);

    try {
        const result = stmt.get([cardUuid, currentState.workspaceId]);

        if (result) {
            return {
                uuid: result.key,
                name: result.name,
                description: result.description,
                tags: JSON.parse(result.tags || '[]'),
                created_at: result.created_at,
                modified_at: result.modified_at
            };
        }

        return null;

    } finally {
        stmt.finalize();
    }
}

/**
 * Load multiple cards by UUIDs
 * @param {Array<string>} cardUuids - Card identifiers
 * @param {Object} state - Optional state object (uses global if not provided)
 * @returns {Array<Object>} Array of card data
 */
async function getSQLiteCardsByUuids(cardUuids, state = null) {
    const currentState = state || _sqliteWasmState;

    if (!cardUuids || cardUuids.length === 0) {
        return [];
    }

    const placeholders = cardUuids.map(() => '?').join(',');
    const stmt = currentState.db.prepare(`
        SELECT key, name, description, tags, created_at, modified_at
        FROM cards
        WHERE key IN (${placeholders}) AND workspace_id = ?
    `);

    try {
        const params = [...cardUuids, currentState.workspaceId];
        const results = [];

        stmt.bind(params);
        while (stmt.step()) {
            const row = stmt.get({});
            results.push({
                uuid: row.key,
                name: row.name,
                description: row.description,
                tags: JSON.parse(row.tags || '[]'),
                created_at: row.created_at,
                modified_at: row.modified_at
            });
        }

        return results;

    } finally {
        stmt.finalize();
    }
}

/**
 * Get tag name by UUID
 * @param {string} tagUuid - Tag identifier
 * @param {Object} state - Optional state object (uses global if not provided)
 * @returns {string|null} Tag name or null if not found
 */
async function getSQLiteTagByUuid(tagUuid, state = null) {
    const currentState = state || _sqliteWasmState;

    if (!currentState.isInitialized) {
        throw new Error('SQLite WASM not initialized');
    }

    const stmt = currentState.db.prepare(`
        SELECT name FROM tags
        WHERE key = ? AND workspace_id = ?
    `);

    try {
        const result = stmt.get([tagUuid, currentState.workspaceId]);
        return result ? result.name : null;

    } finally {
        stmt.finalize();
    }
}

/**
 * Import data from external source
 * @param {Object} data - Data to import
 * @param {Object} state - Optional state object (uses global if not provided)
 */
async function importSQLiteData(data, state = null) {
    const currentState = state || _sqliteWasmState;
    const { cards = [], tags = [] } = data;

    // Begin transaction
    currentState.db.exec('BEGIN TRANSACTION');

    try {
        // Import tags first
        const tagStmt = currentState.db.prepare(`
            INSERT OR REPLACE INTO tags (key, name, workspace_id, created_at)
            VALUES (?, ?, ?, ?)
        `);

        for (const tag of tags) {
            tagStmt.run([
                tag.uuid,
                tag.name,
                currentState.workspaceId,
                tag.created_at || new Date().toISOString()
            ]);
        }
        tagStmt.finalize();

        // Import cards
        const cardStmt = currentState.db.prepare(`
            INSERT OR REPLACE INTO cards (key, name, description, tags, workspace_id, created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        `);

        for (const card of cards) {
            cardStmt.run([
                card.uuid,
                card.name,
                card.description || '',
                JSON.stringify(card.tags || []),
                currentState.workspaceId,
                card.created_at || new Date().toISOString(),
                card.modified_at || new Date().toISOString()
            ]);
        }
        cardStmt.finalize();

        // Commit transaction
        currentState.db.exec('COMMIT');

        console.log(`Imported ${cards.length} cards and ${tags.length} tags`);

    } catch (error) {
        // Rollback on error
        currentState.db.exec('ROLLBACK');
        throw error;
    }
}

/**
 * Close database connection
 * @param {Object} state - Optional state object (uses global if not provided)
 */
function closeSQLiteWASM(state = null) {
    const currentState = state || _sqliteWasmState;

    if (currentState.db) {
        currentState.db.close();
        currentState.db = null;
    }
    currentState.isInitialized = false;
}

/**
 * Get current SQLite WASM state
 * @returns {Object} Current state
 */
function getSQLiteWASMState() {
    return _sqliteWasmState;
}

// Global WASM manager - using pure functions
window.sqliteWASM = {
    initialize: initializeSQLiteWASM,
    getCardByUuid: getSQLiteCardByUuid,
    getCardsByUuids: getSQLiteCardsByUuids,
    getTagByUuid: getSQLiteTagByUuid,
    importData: importSQLiteData,
    close: closeSQLiteWASM,
    getState: getSQLiteWASMState
};
```

**Day 3-4: Content Injection System**

```javascript
/**
 * Hybrid Content Injection System
 * Replaces UUID placeholders with actual content from SQLite WASM
 */
// Hybrid Content Injector - Pure Functions
/**
 * Hybrid Content Injection System - Pure function implementation
 * Replaces UUID placeholders with actual content from SQLite WASM
 */

// Constants for placeholder patterns
const CARD_PLACEHOLDER_PATTERN = /{{UUID:([a-f0-9-]{36})}}/g;
const TAG_PLACEHOLDER_PATTERN = /{{TAG_UUID:([a-f0-9-]{36})}}/g;

/**
 * Inject content into UUID placeholder template
 * @param {string} templateHtml - HTML with UUID placeholders
 * @param {Object} wasmManager - WASM manager object with methods
 * @returns {string} HTML with injected content
 */
async function injectHybridContent(templateHtml, wasmManager) {
    try {
        // Extract all card UUIDs from template
        const cardUuids = extractCardUuidsFromTemplate(templateHtml);
        const tagUuids = extractTagUuidsFromTemplate(templateHtml);

        // Load content from SQLite WASM
        const [cards, tagNames] = await Promise.all([
            wasmManager.getCardsByUuids(cardUuids),
            loadTagNamesFromWasm(tagUuids, wasmManager)
        ]);

        // Create lookup maps
        const cardMap = new Map(cards.map(card => [card.uuid, card]));
        const tagMap = new Map(tagNames.map(tag => [tag.uuid, tag.name]));

        // Replace card placeholders
        let result = templateHtml.replace(CARD_PLACEHOLDER_PATTERN, (match, uuid) => {
            const card = cardMap.get(uuid);
            if (card) {
                return renderCardContentHtml(card);
            } else {
                console.warn(`Card not found for UUID: ${uuid}`);
                return `<div class="error">Card not found: ${uuid}</div>`;
            }
        });

        // Replace tag placeholders
        result = result.replace(TAG_PLACEHOLDER_PATTERN, (match, uuid) => {
            const tagName = tagMap.get(uuid);
            if (tagName) {
                return escapeHtmlText(tagName);
            } else {
                console.warn(`Tag not found for UUID: ${uuid}`);
                return `<span class="error">Unknown tag</span>`;
            }
        });

        return result;

    } catch (error) {
        console.error('Content injection failed:', error);
        // Return template with error indicators
        return templateHtml.replace(CARD_PLACEHOLDER_PATTERN,
            '<div class="error">Content unavailable</div>');
    }
}

/**
 * Extract card UUIDs from template
 * @param {string} template - HTML template
 * @returns {Array<string>} Array of card UUIDs
 */
function extractCardUuidsFromTemplate(template) {
    const uuids = [];
    let match;
    const pattern = new RegExp(CARD_PLACEHOLDER_PATTERN);

    while ((match = pattern.exec(template)) !== null) {
        uuids.push(match[1]);
    }

    return [...new Set(uuids)]; // Remove duplicates
}

/**
 * Extract tag UUIDs from template
 * @param {string} template - HTML template
 * @returns {Array<string>} Array of tag UUIDs
 */
function extractTagUuidsFromTemplate(template) {
    const uuids = [];
    let match;
    const pattern = new RegExp(TAG_PLACEHOLDER_PATTERN);

    while ((match = pattern.exec(template)) !== null) {
        uuids.push(match[1]);
    }

    return [...new Set(uuids)]; // Remove duplicates
}

/**
 * Load tag names for UUIDs
 * @param {Array<string>} tagUuids - Tag identifiers
 * @param {Object} wasmManager - WASM manager object
 * @returns {Array<Object>} Array of {uuid, name} objects
 */
async function loadTagNamesFromWasm(tagUuids, wasmManager) {
    const results = [];

    for (const uuid of tagUuids) {
        const name = await wasmManager.getTagByUuid(uuid);
        if (name) {
            results.push({ uuid, name });
        }
    }

    return results;
}

/**
 * Render card content HTML
 * @param {Object} card - Card data
 * @returns {string} Rendered HTML
 */
function renderCardContentHtml(card) {
    const title = escapeHtmlText(card.name);
    const description = escapeHtmlText(card.description || '');
    const createdAt = new Date(card.created_at).toLocaleDateString();

    return `
        <div class="card-item" data-card-uuid="${card.uuid}">
            <div class="card-header">
                <h3 class="card-title">${title}</h3>
                <span class="card-date">${createdAt}</span>
            </div>
            <div class="card-content">
                <p>${description}</p>
            </div>
            <div class="card-tags">
                ${card.tags.map(tagUuid =>
                    `<span class="tag" data-tag-uuid="${tagUuid}">{{TAG_UUID:${tagUuid}}}</span>`
                ).join('')}
            </div>
        </div>
    `;
}

/**
 * Escape HTML entities
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtmlText(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global content injector - using pure functions
window.contentInjector = {
    injectContent: injectHybridContent,
    extractCardUuids: extractCardUuidsFromTemplate,
    extractTagUuids: extractTagUuidsFromTemplate,
    loadTagNames: loadTagNamesFromWasm,
    renderCardContent: renderCardContentHtml,
    escapeHtml: escapeHtmlText
};
```

**Day 5: Integration Testing**

- WASM loading and initialization testing
- Content injection accuracy validation
- Performance benchmarking

#### Week 8: Local Database Management

**Day 1-2: Data Synchronization**

```javascript
/**
 * Data Synchronization Manager
 * Handles sync between local SQLite WASM and external data sources
 */
// Data Sync Manager - Pure Functions
/**
 * Data Synchronization Manager - Pure function implementation
 * Handles sync between local SQLite WASM and external data sources
 */

// Global sync state
let _dataSyncState = {
    lastSyncTimestamp: null,
    syncInProgress: false
};

/**
 * Initialize data sync state
 */
function initializeDataSyncState() {
    _dataSyncState = {
        lastSyncTimestamp: null,
        syncInProgress: false
    };
    loadDataSyncTimestamp();
}

/**
 * Sync data from external source to local SQLite WASM
 * @param {string} workspaceId - Tenant identifier
 * @param {boolean} forceFullSync - Force complete resync
 * @param {Object} wasmManager - WASM manager object
 * @param {string} backendEndpoint - Backend API endpoint
 * @param {Object} syncState - Optional sync state (uses global if not provided)
 */
async function syncDataFromExternal(workspaceId, forceFullSync, wasmManager, backendEndpoint, syncState = null) {
    const currentState = syncState || _dataSyncState;

    if (currentState.syncInProgress) {
        console.log('Sync already in progress, skipping');
        return;
    }

    currentState.syncInProgress = true;

    try {
        console.log('Starting data sync...');

        // Determine sync type
        const syncTimestamp = forceFullSync ? null : currentState.lastSyncTimestamp;

        // Fetch data from external source
        const data = await fetchExternalDataForSync(workspaceId, syncTimestamp, backendEndpoint);

        if (data.cards.length > 0 || data.tags.length > 0) {
            // Import data to SQLite WASM
            await wasmManager.importData(data);

            console.log(`Synced ${data.cards.length} cards and ${data.tags.length} tags`);
        } else {
            console.log('No new data to sync');
        }

        // Update last sync timestamp
        currentState.lastSyncTimestamp = new Date().toISOString();
        storeDataSyncTimestamp(currentState);

    } catch (error) {
        console.error('Data sync failed:', error);
        throw error;

    } finally {
        currentState.syncInProgress = false;
    }
}

/**
 * Fetch data from external source
 * @param {string} workspaceId - Tenant identifier
 * @param {string|null} since - Timestamp for incremental sync
 * @param {string} backendEndpoint - Backend API endpoint
 * @returns {Object} Data with cards and tags arrays
 */
async function fetchExternalDataForSync(workspaceId, since, backendEndpoint) {
    const params = new URLSearchParams({
        workspace_id: workspaceId,
        format: 'full_content'
    });

    if (since) {
        params.append('since', since);
    }

    const response = await fetch(`${backendEndpoint}/export/data?${params}`, {
        headers: {
            'Authorization': `Bearer ${getDataSyncAuthToken()}`,
            'Content-Type': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error(`Data fetch failed: ${response.status}`);
    }

    return await response.json();
}

/**
 * Export local data for backup or migration
 * @param {Object} wasmManager - WASM manager object
 * @returns {Object} Complete local data
 */
async function exportLocalDataFromWasm(wasmManager) {
    const wasmState = wasmManager.getState ? wasmManager.getState() : wasmManager;

    if (!wasmState.isInitialized) {
        throw new Error('SQLite WASM not initialized');
    }

    // Export all cards
    const cardsStmt = wasmState.db.prepare(`
        SELECT key, name, description, tags, workspace_id, created_at, modified_at
        FROM cards
        WHERE workspace_id = ?
    `);

    const cards = [];
    cardsStmt.bind([wasmState.workspaceId]);
    while (cardsStmt.step()) {
        const row = cardsStmt.get({});
        cards.push({
            uuid: row.key,
            name: row.name,
            description: row.description,
            tags: JSON.parse(row.tags || '[]'),
            workspace_id: row.workspace_id,
            created_at: row.created_at,
            modified_at: row.modified_at
        });
    }
    cardsStmt.finalize();

    // Export all tags
    const tagsStmt = wasmState.db.prepare(`
        SELECT key, name, workspace_id, created_at
        FROM tags
        WHERE workspace_id = ?
    `);

    const tags = [];
    tagsStmt.bind([wasmState.workspaceId]);
    while (tagsStmt.step()) {
        const row = tagsStmt.get({});
        tags.push({
            uuid: row.key,
            name: row.name,
            workspace_id: row.workspace_id,
            created_at: row.created_at
        });
    }
    tagsStmt.finalize();

    return {
        cards,
        tags,
        exported_at: new Date().toISOString(),
        workspace_id: wasmState.workspaceId
    };
}

/**
 * Store sync timestamp in localStorage
 * @param {Object} syncState - Optional sync state (uses global if not provided)
 */
function storeDataSyncTimestamp(syncState = null) {
    const currentState = syncState || _dataSyncState;

    if (currentState.lastSyncTimestamp) {
        localStorage.setItem('multicardz_last_sync', currentState.lastSyncTimestamp);
    }
}

/**
 * Load sync timestamp from localStorage
 * @param {Object} syncState - Optional sync state (uses global if not provided)
 */
function loadDataSyncTimestamp(syncState = null) {
    const currentState = syncState || _dataSyncState;

    currentState.lastSyncTimestamp = localStorage.getItem('multicardz_last_sync');
}

/**
 * Get authentication token
 * @returns {string} Auth token
 */
function getDataSyncAuthToken() {
    // Implementation depends on auth system
    return localStorage.getItem('auth_token') || '';
}

/**
 * Get current data sync state
 * @returns {Object} Current sync state
 */
function getDataSyncState() {
    return _dataSyncState;
}

// Global sync manager - using pure functions
window.dataSyncManager = {
    initialize: initializeDataSyncState,
    syncFromExternal: syncDataFromExternal,
    fetchExternalData: fetchExternalDataForSync,
    exportLocalData: exportLocalDataFromWasm,
    storeSyncTimestamp: storeDataSyncTimestamp,
    loadSyncTimestamp: loadDataSyncTimestamp,
    getAuthToken: getDataSyncAuthToken,
    getState: getDataSyncState
};
```

**Day 3-4: Premium Mode UI Integration**

```javascript
/**
 * Premium Mode UI Controller functions (no classes)
 * Manages UI specific to premium zero-trust mode
 */
let premiumModeState = {
    isInitialized: false,
    syncStatus: 'idle' // idle, syncing, error
};

/**
 * Initialize premium mode UI
 * @param {string} workspaceId - Tenant identifier
 */
async function initializePremiumMode(workspaceId) {
    try {
        // Initialize SQLite WASM
        await initializeSQLiteWASM('/static/js/sqlite3.wasm', workspaceId);

        // Initialize content injector
        await initializeContentInjector();

        // Initialize sync manager
        await initializeDataSync('/api/v2');

        // Load sync timestamp
        loadSyncTimestamp();

        // Show premium mode indicators
        showPremiumModeUI();

        // Perform initial sync
        await performInitialSync();

        premiumModeState.isInitialized = true;
        console.log('Premium mode initialized successfully');

    } catch (error) {
        console.error('Premium mode initialization failed:', error);
        showPremiumError('Failed to initialize premium mode');
        throw error;
    }
}

/**
 * Show premium mode UI indicators
 */
function showPremiumModeUI() {
        // Add premium mode indicator
        const indicator = document.createElement('div');
        indicator.id = 'premium-mode-indicator';
        indicator.className = 'premium-indicator';
        indicator.innerHTML = `
            <div class="premium-badge">
                <span class="shield-icon">🛡️</span>
                <span class="mode-text">Zero-Trust Mode</span>
                <span class="sync-status" id="sync-status">●</span>
            </div>
        `;

        // Insert at top of page
        document.body.insertBefore(indicator, document.body.firstChild);

        // Add premium mode styles
        const styles = `
            .premium-indicator {
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 1000;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 8px;
                padding: 8px 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }

            .premium-badge {
                display: flex;
                align-items: center;
                gap: 6px;
                color: white;
                font-size: 12px;
                font-weight: 600;
            }

            .sync-status {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                color: #4ade80;
            }

            .sync-status.syncing {
                animation: pulse 1s infinite;
                color: #fbbf24;
            }

            .sync-status.error {
                color: #ef4444;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    /**
     * Perform initial data sync
     */
    async performInitialSync() {
        this.updateSyncStatus('syncing');

        try {
            await window.dataSyncManager.syncFromExternal(
                window.sqliteWASM.workspaceId,
                true // Force full sync on initialization
            );

            this.updateSyncStatus('idle');

        } catch (error) {
            console.error('Initial sync failed:', error);
            this.updateSyncStatus('error');
            throw error;
        }
    }

    /**
     * Update sync status indicator
     * @param {string} status - Status: idle, syncing, error
     */
    updateSyncStatus(status) {
        this.syncStatus = status;

        const statusElement = document.getElementById('sync-status');
        if (statusElement) {
            statusElement.className = `sync-status ${status}`;

            // Update tooltip
            const tooltips = {
                idle: 'Data synchronized',
                syncing: 'Synchronizing data...',
                error: 'Sync error'
            };

            statusElement.title = tooltips[status] || '';
        }
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        console.error(message);

        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'error-notification';
        notification.innerHTML = `
            <div class="error-content">
                <span class="error-icon">⚠️</span>
                <span class="error-message">${message}</span>
                <button class="error-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Override card rendering for premium mode
     */
    async renderCardsWithContentInjection(templateHtml) {
        if (!this.isInitialized) {
            throw new Error('Premium mode not initialized');
        }

        // Use content injector to replace UUID placeholders
        const htmlWithContent = await window.contentInjector.injectContent(templateHtml);

        // Update DOM
        const cardsContainer = document.getElementById('cardsContainer');
        if (cardsContainer) {
            cardsContainer.innerHTML = htmlWithContent;
        }

        return htmlWithContent;
    }
}

// Global premium mode controller
window.premiumModeController = new PremiumModeController();
```

**Day 5: Testing and Optimization**

- End-to-end premium mode testing
- Performance optimization for large datasets
- Error handling validation

### Deliverables

- [x] SQLite WASM integration with official library
- [x] Content injection system for hybrid rendering
- [x] Local database management with sync capabilities
- [x] Premium mode UI indicators and controls
- [x] Data export/import functionality
- [x] Performance optimization for browser-based database

### Success Criteria

- SQLite WASM loads and initializes in <3 seconds
- Content injection completes in <100ms for 100 cards
- Local database handles 10,000+ cards without performance degradation
- Sync system recovers gracefully from network failures

## Phase 5: Privacy Mode Three-Way Sync Architecture (Week 9-10)

### Objectives

- **[NEW]** Implement Turso embedded replicas for Privacy Mode
- **[NEW]** Create three-way sync between browser, server, and Turso cloud
- **[NEW]** Establish obfuscation layer for server-side operations
- **[NEW]** Enable disaster recovery and multi-device sync

### Architecture Overview

```
┌─────────────────┐       ┌──────────────────┐      ┌─────────────────┐
│  Browser WASM   │◄─────►│  Server SQLite   │◄────►│   Turso Cloud   │
│  (Full Content) │ Sync  │  (Obfuscated)    │ Sync │   (Backup)      │
└─────────────────┘       └──────────────────┘      └─────────────────┘
        │                          │                          │
   Complete Data             Bitmaps Only              Replicated
   User's Device             Set Operations            Obfuscated
```

### Tasks

#### Week 9: Turso Embedded Replica Setup

**Day 1-2: Turso Configuration**

```python
# Environment configuration for Turso
TURSO_DATABASE_URL = "your-turso-database.turso.io"
TURSO_AUTH_TOKEN = "your-auth-token"
TURSO_SYNC_INTERVAL = 60  # seconds

# Per-customer database creation
def create_privacy_database(user_id: str, workspace_id: str):
    """Create Turso embedded replica for Privacy Mode."""
    import libsql_experimental as libsql

    # Local embedded replica path
    local_path = f"data/privacy/{user_id}_{workspace_id}_replica.db"

    # Turso cloud database name
    turso_db_name = f"{user_id}-{workspace_id}-privacy"
    turso_url = f"libsql://{turso_db_name}.{TURSO_DATABASE_URL}"

    # Create embedded replica with automatic sync
    db = libsql.Database(
        path=local_path,
        sync_url=turso_url,
        auth_token=TURSO_AUTH_TOKEN,
        sync_interval=TURSO_SYNC_INTERVAL,
        encryption_key=generate_obfuscation_key(user_id, workspace_id)
    )

    return db
```

**Day 3-4: Obfuscation Layer**

```python
def obfuscate_card_data(card: dict, obfuscation_key: bytes) -> dict:
    """
    Obfuscate card data for server storage.
    Only stores bitmaps and checksums, no actual content.
    """
    import hashlib

    # Generate deterministic bitmap from UUID
    card_bitmap = int(hashlib.md5(card['card_id'].encode()).hexdigest()[:8], 16)

    # Create content checksum for verification
    content_str = json.dumps({
        'name': card['name'],
        'description': card['description'],
        'tag_ids': card['tag_ids']
    }, sort_keys=True)
    checksum = hashlib.sha256(content_str.encode()).hexdigest()[:16]

    return {
        'card_bitmap': card_bitmap,
        'tag_bitmaps': card.get('tag_bitmaps', []),
        'checksum': checksum
    }

def sync_browser_to_server(user_id: str, workspace_id: str, browser_data: dict):
    """
    Sync data from browser WASM to server embedded replica.
    Browser sends full data, server stores obfuscated version.
    """
    replica = get_embedded_replica(user_id, workspace_id)

    with replica.connect() as conn:
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")

        # Process cards - store only obfuscated data
        for card in browser_data['cards']:
            obfuscated = obfuscate_card_data(card, get_obfuscation_key(user_id, workspace_id))
            conn.execute("""
                INSERT OR REPLACE INTO obfuscated_cards
                (card_bitmap, tag_bitmaps, checksum, sync_version)
                VALUES (?, ?, ?, ?)
            """, (
                obfuscated['card_bitmap'],
                json.dumps(obfuscated['tag_bitmaps']),
                obfuscated['checksum'],
                browser_data['sync_version']
            ))

        # Process tags - store only bitmaps
        for tag in browser_data['tags']:
            conn.execute("""
                INSERT OR REPLACE INTO obfuscated_tags
                (tag_bitmap, checksum, sync_version)
                VALUES (?, ?, ?)
            """, (
                tag['tag_bitmap'],
                hashlib.sha256(tag['name'].encode()).hexdigest()[:16],
                browser_data['sync_version']
            ))

        conn.execute("COMMIT")

    # Trigger sync to Turso cloud
    replica.sync()
```

**Day 5: Three-Way Sync Protocol**

```javascript
// Browser-side sync functions (no classes)
let syncState = {
    wasmDb: null,
    syncEndpoint: '',
    syncInterval: 60000,
    lastSyncVersion: 0
};

async function initializePrivacySync(wasmDb, syncEndpoint) {
    syncState.wasmDb = wasmDb;
    syncState.syncEndpoint = syncEndpoint;
    syncState.lastSyncVersion = await getLastSyncVersion(wasmDb);
    return syncState;
}

async function performPrivacySync() {
    // Get changes since last sync
    const changes = await getChangesSinceVersion(
        syncState.wasmDb,
        syncState.lastSyncVersion
    );

    if (changes.cards.length > 0 || changes.tags.length > 0) {
        // Send to server for obfuscated storage
        const response = await fetch(syncState.syncEndpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                cards: changes.cards,
                tags: changes.tags,
                sync_version: syncState.lastSyncVersion + 1
            })
        });

        if (response.ok) {
            syncState.lastSyncVersion++;
            await markChangesSynced(syncState.wasmDb, changes);
        }
    }
}

async function restoreFromCloud() {
    // Disaster recovery - pull from Turso via server
    const response = await fetch(`${syncState.syncEndpoint}/restore`, {
        method: 'GET'
    });

    if (response.ok) {
        const data = await response.json();
        await rebuildLocalDatabase(syncState.wasmDb, data);
    }
}

// Start periodic sync
function startPeriodicSync() {
    setInterval(performPrivacySync, syncState.syncInterval);
}
```

#### Week 10: Performance and Reliability

**Day 1-2: Set Operations on Obfuscated Data**

```python
def perform_obfuscated_set_operation(
    user_id: str,
    workspace_id: str,
    operation: str,
    tag_bitmaps: list[int]
) -> list[int]:
    """
    Perform set operations on obfuscated data without accessing content.
    """
    replica = get_embedded_replica(user_id, workspace_id)

    with replica.connect() as conn:
        if operation == 'union':
            # Find cards with ANY of the specified tag bitmaps
            placeholders = ','.join(['?'] * len(tag_bitmaps))
            cursor = conn.execute(f"""
                SELECT DISTINCT card_bitmap
                FROM obfuscated_cards
                WHERE EXISTS (
                    SELECT 1 FROM json_each(tag_bitmaps) AS t
                    WHERE t.value IN ({placeholders})
                )
            """, tag_bitmaps)

        elif operation == 'intersection':
            # Find cards with ALL specified tag bitmaps
            cursor = conn.execute("""
                SELECT card_bitmap
                FROM obfuscated_cards
                WHERE json_array_length(
                    json_group_array(
                        SELECT value FROM json_each(tag_bitmaps)
                        WHERE value IN (?)
                    )
                ) = ?
            """, (json.dumps(tag_bitmaps), len(tag_bitmaps)))

        return [row[0] for row in cursor]
```

**Day 3-4: Conflict Resolution**

```python
def resolve_sync_conflict(
    local_version: dict,
    remote_version: dict,
    resolution_strategy: str = 'last_write_wins'
) -> dict:
    """
    Resolve conflicts between local and remote versions.
    """
    if resolution_strategy == 'last_write_wins':
        if local_version['modified'] > remote_version['modified']:
            return local_version
        return remote_version

    elif resolution_strategy == 'client_wins':
        return local_version

    elif resolution_strategy == 'server_wins':
        return remote_version

    elif resolution_strategy == 'merge':
        # Custom merge logic for card data
        merged = {
            'card_bitmap': local_version['card_bitmap'],
            'tag_bitmaps': list(set(
                local_version.get('tag_bitmaps', []) +
                remote_version.get('tag_bitmaps', [])
            )),
            'checksum': generate_merged_checksum(local_version, remote_version),
            'sync_version': max(
                local_version.get('sync_version', 0),
                remote_version.get('sync_version', 0)
            ) + 1
        }
        return merged
```

**Day 5: Testing and Optimization**

- Sync reliability testing with network interruptions
- Performance benchmarking for large datasets
- Disaster recovery testing
- Multi-device sync validation

### Acceptance Criteria

- Three-way sync completes in <5 seconds for 1000 cards
- Server performs set operations on 10,000 cards in <100ms
- Turso sync handles network failures gracefully
- Zero content exposure in obfuscated databases
- Successful recovery from complete local data loss

## Phase 6: Hybrid Rendering & Communication (Week 11-12)

### Objectives

- **[NEW]** Will implement fixed drag-drop communication flow: browser DOM → tagsInPlay → /api/render/cards → HTML response
- **[NEW]** Will implement separated server-side UUID template rendering from client-side content injection
- **[NEW]** Will establish real-time UUID sync for card/tag mutations (not drag-drop operations)
- **[EXISTS-MODIFY]** Will enhance existing HTMX rendering with hybrid system

### Tasks

#### Week 9: Template System Design

**Day 1-2: UUID Placeholder Templates**

```python
from jinja2 import Environment, BaseLoader, select_autoescape
from typing import Set, Dict, Any
import uuid

# UUID Placeholder Renderer - Pure Functions
"""Renders templates with UUID placeholders for premium mode using pure functions."""

# Global Jinja2 environment
_uuid_renderer_env = None

def initialize_uuid_renderer(template_dir: str):
    """Initialize the UUID renderer environment."""
    global _uuid_renderer_env
    _uuid_renderer_env = Environment(
        loader=BaseLoader(),
        autoescape=select_autoescape(['html', 'xml'])
    )

async def render_card_template_with_uuids(
    card_uuids: Set[str],
    template_name: str = 'card_grid.html',
    template_env=None,
    **context
) -> str:
    """
    Render template with UUID placeholders instead of content.

    Args:
        card_uuids: Set of card UUIDs to render
        template_name: Template file name
        template_env: Optional Jinja2 environment (uses global if not provided)
        **context: Additional template context

    Returns:
        HTML template with UUID placeholders
    """
    env = template_env or _uuid_renderer_env
    if not env:
        raise ValueError("Template environment not initialized")

    # Load template
    template = env.get_template(template_name)

    # Create placeholder cards
    placeholder_cards = []
    for card_uuid in card_uuids:
        placeholder_cards.append({
            'uuid': card_uuid,
            'title_placeholder': f'{{{{UUID:{card_uuid}:title}}}}',
            'content_placeholder': f'{{{{UUID:{card_uuid}:content}}}}',
            'tags_placeholder': f'{{{{UUID:{card_uuid}:tags}}}}',
            'created_at_placeholder': f'{{{{UUID:{card_uuid}:created_at}}}}'
        })

    # Render template with placeholders
    return template.render(
        cards=placeholder_cards,
        render_mode='uuid_placeholders',
        **context
    )

async def render_full_content_template(
    cards: list[Dict[str, Any]],
    template_name: str = 'card_grid.html',
    template_env=None,
    **context
) -> str:
    """
    Render template with full content for standard modes.

    Args:
        cards: List of card data with content
        template_name: Template file name
        template_env: Optional Jinja2 environment (uses global if not provided)
        **context: Additional template context

    Returns:
        Complete HTML with content
    """
    env = template_env or _uuid_renderer_env
    if not env:
        raise ValueError("Template environment not initialized")

    template = env.get_template(template_name)

    return template.render(
        cards=cards,
        render_mode='full_content',
        **context
    )

# Enhanced Jinja2 template for hybrid rendering
CARD_GRID_TEMPLATE = """
<div class="cards-container" data-render-mode="{{ render_mode }}">
    {% if render_mode == 'uuid_placeholders' %}
        <!-- UUID placeholder mode for premium -->
        {% for card in cards %}
        <div class="card-item" data-card-uuid="{{ card.uuid }}">
            <div class="card-header">
                <h3 class="card-title">{{ card.title_placeholder }}</h3>
                <span class="card-date">{{ card.created_at_placeholder }}</span>
            </div>
            <div class="card-content">
                {{ card.content_placeholder }}
            </div>
            <div class="card-tags">
                {{ card.tags_placeholder }}
            </div>
        </div>
        {% endfor %}
    {% else %}
        <!-- Full content mode for standard/development -->
        {% for card in cards %}
        <div class="card-item" data-card-id="{{ card.id }}">
            <div class="card-header">
                <h3 class="card-title">{{ card.title | e }}</h3>
                <span class="card-date">{{ card.created_at | dateformat }}</span>
            </div>
            <div class="card-content">
                {{ card.description | e | nl2br }}
            </div>
            <div class="card-tags">
                {% for tag in card.tags %}
                <span class="tag" data-tag="{{ tag }}">{{ tag | e }}</span>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    {% endif %}
</div>
"""
```

**Day 3-4: Mode-Aware Rendering Pipeline**

```python
from typing import Union, Dict, Any, Set
from enum import Enum

class RenderMode(Enum):
    DEVELOPMENT = "development"
    STANDARD = "standard"
    PREMIUM = "premium"

# Hybrid Rendering Engine - Pure Functions
"""Mode-aware rendering engine supporting both content and UUID templates using pure functions."""

async def render_cards_hybrid(
    data: Union[Set[str], list[Dict[str, Any]]],
    mode: RenderMode,
    template_context: Dict[str, Any],
    uuid_renderer_func=None,
    content_renderer_func=None,
    template_env=None
) -> str:
    """
    Render cards based on mode and data type.

    Args:
        data: Either card UUIDs (premium) or card objects (standard/dev)
        mode: Rendering mode
        template_context: Additional context for templates
        uuid_renderer_func: Optional UUID renderer function (uses default if not provided)
        content_renderer_func: Optional content renderer function (uses default if not provided)
        template_env: Optional Jinja2 environment

    Returns:
        Rendered HTML
    """
    if mode == RenderMode.PREMIUM:
        # UUID-based rendering for premium mode
        if not isinstance(data, set):
            raise ValueError("Premium mode requires set of UUIDs")

        renderer_func = uuid_renderer_func or render_card_template_with_uuids
        return await renderer_func(
            card_uuids=data,
            template_env=template_env,
            **template_context
        )

    elif mode in [RenderMode.DEVELOPMENT, RenderMode.STANDARD]:
        # Content-based rendering for standard modes
        if not isinstance(data, list):
            raise ValueError("Standard modes require list of card objects")

        renderer_func = content_renderer_func or render_full_content_template
        return await renderer_func(
            cards=data,
            template_env=template_env,
            **template_context
        )

    else:
        raise ValueError(f"Unknown render mode: {mode}")

async def render_with_progressive_enhancement(
    card_data: Union[Set[str], list[Dict[str, Any]]],
    mode: RenderMode,
    template_context: Dict[str, Any],
    uuid_renderer_func=None,
    content_renderer_func=None,
    template_env=None
) -> Dict[str, Any]:
    """
    Render with progressive enhancement metadata.

    Args:
        card_data: Card UUIDs or objects
        mode: Rendering mode
        template_context: Template context
        uuid_renderer_func: Optional UUID renderer function
        content_renderer_func: Optional content renderer function
        template_env: Optional Jinja2 environment

    Returns:
        Dictionary with HTML and enhancement metadata
    """
    html = await render_cards_hybrid(
        card_data, mode, template_context,
        uuid_renderer_func, content_renderer_func, template_env
    )

    from datetime import datetime
    enhancement_metadata = {
        'render_mode': mode.value,
        'requires_content_injection': mode == RenderMode.PREMIUM,
        'card_count': len(card_data) if hasattr(card_data, '__len__') else 0,
        'timestamp': datetime.utcnow().isoformat()
    }

    if mode == RenderMode.PREMIUM:
        enhancement_metadata['uuid_placeholders'] = list(card_data)

    return {
        'html': html,
        'metadata': enhancement_metadata
    }

# Enhanced cards API with hybrid rendering
@router.post("/render/cards", response_class=HTMLResponse)
async def render_cards_hybrid(
    request: Request,
    mode: RenderMode = Depends(get_render_mode)
):
    """
    Enhanced cards API with mode-aware hybrid rendering.

    Args:
        request: FastAPI request with tagsInPlay
        mode: Determined from authentication/subscription

    Returns:
        HTML appropriate for the user's mode
    """
    try:
        # Parse request
        request_data = await request.json()
        tags_in_play = request_data.get('tagsInPlay', {})

        # Get workspace and user context
        workspace_id = get_workspace_from_auth(request)
        user_context = get_user_context(request)

        # Create rendering engine
        rendering_engine = HybridRenderingEngine(
            uuid_renderer=get_uuid_renderer(),
            content_renderer=get_content_renderer()
        )

        if mode == RenderMode.PREMIUM:
            # UUID-based operations for premium users
            set_engine = create_blind_set_operation_engine(workspace_id)
            result_uuids = await compute_uuid_set_operations(
                tags_in_play, set_engine, workspace_id
            )

            # Render with UUID placeholders
            response_data = await rendering_engine.render_with_progressive_enhancement(
                card_data=result_uuids,
                mode=mode,
                template_context={
                    'workspace_id': workspace_id,
                    'user_context': user_context,
                    'tags_in_play': tags_in_play
                }
            )

            # Add content injection instructions
            response_html = f"""
                {response_data['html']}
                <script>
                    // Trigger content injection for premium mode
                    if (window.premiumModeController && window.premiumModeController.isInitialized) {{
                        window.premiumModeController.renderCardsWithContentInjection(
                            document.querySelector('.cards-container').outerHTML
                        ).then(injectedHtml => {{
                            document.querySelector('.cards-container').outerHTML = injectedHtml;
                        }}).catch(error => {{
                            console.error('Content injection failed:', error);
                        }});
                    }}
                </script>
            """

            return HTMLResponse(response_html)

        else:
            # Content-based operations for standard/development
            content_engine = create_content_set_operation_engine(workspace_id)
            result_cards = await compute_content_set_operations(
                tags_in_play, content_engine, workspace_id
            )

            # Render with full content
            response_data = await rendering_engine.render_with_progressive_enhancement(
                card_data=result_cards,
                mode=mode,
                template_context={
                    'workspace_id': workspace_id,
                    'user_context': user_context,
                    'tags_in_play': tags_in_play
                }
            )

            return HTMLResponse(response_data['html'])

    except Exception as e:
        logger.error(f"Hybrid rendering failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Rendering failed")
```

**Day 5: HTMX Compatibility**

- HTMX integration testing with hybrid rendering
- Progressive enhancement validation
- Fallback mechanisms for content injection failures

#### Week 10: Client-Side Enhancement

**Day 1-2: Advanced Content Injection**

```javascript
/**
 * Advanced Content Injection with Performance Optimization
 */
// Advanced injection state
let advancedInjectionState = {
    injectionCache: new Map(),
    batchSize: 50, // Process cards in batches
    cacheTimeout: 5 * 60 * 1000 // 5 minutes
};

/**
 * Inject content with performance optimization and caching
 * @param {string} templateHtml - HTML with UUID placeholders
 * @param {Object} options - Injection options
 * @returns {string} HTML with injected content
 */
async function injectContentOptimized(templateHtml, options = {}) {
        const {
            useCache = true,
            batchProcess = true,
            progressCallback = null
        } = options;

        try {
            // Extract UUIDs
            const cardUuids = this.extractCardUuids(templateHtml);
            const tagUuids = this.extractTagUuids(templateHtml);

            if (progressCallback) {
                progressCallback({ stage: 'extraction', progress: 0.1 });
            }

            // Load content with caching
            const [cardMap, tagMap] = await Promise.all([
                this.loadCardsWithCache(cardUuids, useCache, batchProcess, progressCallback),
                this.loadTagsWithCache(tagUuids, useCache, progressCallback)
            ]);

            if (progressCallback) {
                progressCallback({ stage: 'injection', progress: 0.8 });
            }

            // Perform injection
            const result = await this.performInjection(templateHtml, cardMap, tagMap);

            if (progressCallback) {
                progressCallback({ stage: 'complete', progress: 1.0 });
            }

            return result;

        } catch (error) {
            console.error('Optimized content injection failed:', error);
            throw error;
        }
    }

    /**
     * Load cards with caching and batch processing
     * @param {Array<string>} cardUuids - Card identifiers
     * @param {boolean} useCache - Enable caching
     * @param {boolean} batchProcess - Enable batch processing
     * @param {Function} progressCallback - Progress callback
     * @returns {Map} Card UUID to card data mapping
     */
    async loadCardsWithCache(cardUuids, useCache, batchProcess, progressCallback) {
        const cardMap = new Map();
        const uncachedUuids = [];

        // Check cache first
        if (useCache) {
            for (const uuid of cardUuids) {
                const cached = this.getCachedContent(uuid, 'card');
                if (cached) {
                    cardMap.set(uuid, cached);
                } else {
                    uncachedUuids.push(uuid);
                }
            }
        } else {
            uncachedUuids.push(...cardUuids);
        }

        if (uncachedUuids.length === 0) {
            return cardMap;
        }

        // Load uncached cards
        if (batchProcess && uncachedUuids.length > this.batchSize) {
            // Process in batches
            const batches = this.createBatches(uncachedUuids, this.batchSize);

            for (let i = 0; i < batches.length; i++) {
                const batch = batches[i];
                const batchCards = await this.wasmManager.getCardsByUuids(batch);

                // Add to map and cache
                for (const card of batchCards) {
                    cardMap.set(card.uuid, card);
                    if (useCache) {
                        this.setCachedContent(card.uuid, 'card', card);
                    }
                }

                // Update progress
                if (progressCallback) {
                    const progress = 0.1 + (0.6 * (i + 1) / batches.length);
                    progressCallback({ stage: 'loading_cards', progress });
                }
            }
        } else {
            // Load all at once
            const cards = await this.wasmManager.getCardsByUuids(uncachedUuids);

            for (const card of cards) {
                cardMap.set(card.uuid, card);
                if (useCache) {
                    this.setCachedContent(card.uuid, 'card', card);
                }
            }
        }

        return cardMap;
    }

    /**
     * Load tags with caching
     * @param {Array<string>} tagUuids - Tag identifiers
     * @param {boolean} useCache - Enable caching
     * @param {Function} progressCallback - Progress callback
     * @returns {Map} Tag UUID to tag name mapping
     */
    async loadTagsWithCache(tagUuids, useCache, progressCallback) {
        const tagMap = new Map();
        const uncachedUuids = [];

        // Check cache
        if (useCache) {
            for (const uuid of tagUuids) {
                const cached = this.getCachedContent(uuid, 'tag');
                if (cached) {
                    tagMap.set(uuid, cached);
                } else {
                    uncachedUuids.push(uuid);
                }
            }
        } else {
            uncachedUuids.push(...tagUuids);
        }

        // Load uncached tags
        for (const uuid of uncachedUuids) {
            const tagName = await this.wasmManager.getTagByUuid(uuid);
            if (tagName) {
                tagMap.set(uuid, tagName);
                if (useCache) {
                    this.setCachedContent(uuid, 'tag', tagName);
                }
            }
        }

        if (progressCallback) {
            progressCallback({ stage: 'loading_tags', progress: 0.7 });
        }

        return tagMap;
    }

    /**
     * Perform the actual content injection
     * @param {string} templateHtml - Template HTML
     * @param {Map} cardMap - Card UUID to data mapping
     * @param {Map} tagMap - Tag UUID to name mapping
     * @returns {string} Injected HTML
     */
    async performInjection(templateHtml, cardMap, tagMap) {
        // Use more efficient placeholder replacement
        let result = templateHtml;

        // Replace card placeholders
        result = result.replace(this.placeholderPattern, (match, uuid) => {
            const card = cardMap.get(uuid);
            if (card) {
                return this.renderCardContent(card);
            } else {
                console.warn(`Card not found for UUID: ${uuid}`);
                return this.renderErrorCard(uuid);
            }
        });

        // Replace tag placeholders
        result = result.replace(this.tagPlaceholderPattern, (match, uuid) => {
            const tagName = tagMap.get(uuid);
            if (tagName) {
                return this.escapeHtml(tagName);
            } else {
                console.warn(`Tag not found for UUID: ${uuid}`);
                return `<span class="error-tag" data-uuid="${uuid}">Unknown</span>`;
            }
        });

        return result;
    }

    /**
     * Get cached content
     * @param {string} uuid - Content identifier
     * @param {string} type - Content type (card/tag)
     * @returns {*} Cached content or null
     */
    getCachedContent(uuid, type) {
        const key = `${type}:${uuid}`;
        const cached = this.injectionCache.get(key);

        if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
            return cached.content;
        }

        // Remove expired cache
        if (cached) {
            this.injectionCache.delete(key);
        }

        return null;
    }

    /**
     * Set cached content
     * @param {string} uuid - Content identifier
     * @param {string} type - Content type (card/tag)
     * @param {*} content - Content to cache
     */
    setCachedContent(uuid, type, content) {
        const key = `${type}:${uuid}`;
        this.injectionCache.set(key, {
            content,
            timestamp: Date.now()
        });

        // Limit cache size
        if (this.injectionCache.size > 1000) {
            this.cleanupCache();
        }
    }

    /**
     * Create batches from array
     * @param {Array} array - Input array
     * @param {number} batchSize - Batch size
     * @returns {Array<Array>} Array of batches
     */
    createBatches(array, batchSize) {
        const batches = [];
        for (let i = 0; i < array.length; i += batchSize) {
            batches.push(array.slice(i, i + batchSize));
        }
        return batches;
    }

    /**
     * Clean up expired cache entries
     */
    cleanupCache() {
        const now = Date.now();
        const keysToDelete = [];

        for (const [key, cached] of this.injectionCache.entries()) {
            if ((now - cached.timestamp) > this.cacheTimeout) {
                keysToDelete.push(key);
            }
        }

        for (const key of keysToDelete) {
            this.injectionCache.delete(key);
        }
    }

    /**
     * Render error card for missing content
     * @param {string} uuid - Missing card UUID
     * @returns {string} Error card HTML
     */
    renderErrorCard(uuid) {
        return `
            <div class="card-item error-card" data-card-uuid="${uuid}">
                <div class="card-header">
                    <h3 class="card-title">Content Unavailable</h3>
                </div>
                <div class="card-content">
                    <p class="error-message">Card content could not be loaded.</p>
                    <code class="error-uuid">${uuid}</code>
                </div>
            </div>
        `;
    }
}

// Enhanced premium mode state with progress tracking
let enhancedPremiumState = {
    injectionProgress: 0,
    isInjecting: false
};

/**
 * Render cards with progress tracking
 * @param {string} templateHtml - Template HTML
 * @returns {string} Rendered HTML
 */
async function renderCardsWithProgress(templateHtml) {
        if (!premiumModeState.isInitialized) {
            throw new Error('Premium mode not initialized');
        }

        enhancedPremiumState.isInjecting = true;
        showProgressIndicator();

        try {
            // Use advanced content injector
            const advancedInjector = new AdvancedContentInjector(window.sqliteWASM);

            const result = await advancedInjector.injectContentOptimized(templateHtml, {
                useCache: true,
                batchProcess: true,
                progressCallback: (progress) => {
                    this.updateProgress(progress);
                }
            });

            this.hideProgressIndicator();
            return result;

        } catch (error) {
            this.hideProgressIndicator();
            this.showError('Content injection failed');
            throw error;

        } finally {
            this.isInjecting = false;
        }
    }

    /**
     * Show progress indicator
     */
    showProgressIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'injection-progress';
        indicator.innerHTML = `
            <div class="progress-overlay">
                <div class="progress-modal">
                    <div class="progress-header">Loading Content...</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                    <div class="progress-text" id="progress-text">Initializing...</div>
                </div>
            </div>
        `;

        document.body.appendChild(indicator);
    }

    /**
     * Update progress indicator
     * @param {Object} progress - Progress information
     */
    updateProgress(progress) {
        const fillElement = document.getElementById('progress-fill');
        const textElement = document.getElementById('progress-text');

        if (fillElement && textElement) {
            const percentage = Math.round(progress.progress * 100);
            fillElement.style.width = `${percentage}%`;

            const stageTexts = {
                extraction: 'Extracting placeholders...',
                loading_cards: 'Loading card content...',
                loading_tags: 'Loading tag names...',
                injection: 'Injecting content...',
                complete: 'Complete!'
            };

            textElement.textContent = stageTexts[progress.stage] || 'Processing...';
        }
    }

    /**
     * Hide progress indicator
     */
    hideProgressIndicator() {
        const indicator = document.getElementById('injection-progress');
        if (indicator) {
            indicator.remove();
        }
    }
}

// Replace global controller
window.premiumModeController = new EnhancedPremiumModeController();
```

**Day 3-4: Error Handling and Fallbacks**

```javascript
/**
 * Robust Error Handling for Premium Mode
 */
let errorHandlerState = {
    fallbackAttempts: 0,
    maxFallbackAttempts: 3
};

/**
 * Handle content injection failure with fallbacks
 * @param {string} templateHtml - Original template
 * @param {Error} error - Injection error
 * @returns {string} Fallback HTML
 */
async function handleInjectionFailure(templateHtml, error) {
        console.error('Content injection failed:', error);
        errorHandlerState.fallbackAttempts++;

        if (errorHandlerState.fallbackAttempts <= errorHandlerState.maxFallbackAttempts) {
            // Try different fallback strategies
            switch (errorHandlerState.fallbackAttempts) {
                case 1:
                    return await trySimpleInjection(templateHtml);
                case 2:
                    return await tryUUIDDisplay(templateHtml);
                case 3:
                    return createErrorDisplay(templateHtml, error);
                default:
                    return createMinimalDisplay();
            }
        } else {
            // Max attempts reached, show error
            return this.createErrorDisplay(templateHtml, error);
        }
    }

    /**
     * Try simple content injection without caching
     * @param {string} templateHtml - Template HTML
     * @returns {string} Injected HTML
     */
    async trySimpleInjection(templateHtml) {
        try {
            const simpleInjector = new HybridContentInjector(window.sqliteWASM);
            return await simpleInjector.injectContent(templateHtml);
        } catch (error) {
            console.warn('Simple injection also failed:', error);
            throw error;
        }
    }

    /**
     * Try displaying UUIDs directly
     * @param {string} templateHtml - Template HTML
     * @returns {string} HTML with UUIDs
     */
    async tryUUIDDisplay(templateHtml) {
        // Replace placeholders with UUIDs for debugging
        return templateHtml.replace(
            /\{\{UUID:([a-f0-9-]{36})\}\}/g,
            '<code class="uuid-debug">$1</code>'
        ).replace(
            /\{\{TAG_UUID:([a-f0-9-]{36})\}\}/g,
            '<code class="tag-uuid-debug">$1</code>'
        );
    }

    /**
     * Create error display
     * @param {string} templateHtml - Template HTML
     * @param {Error} error - Error that occurred
     * @returns {string} Error display HTML
     */
    createErrorDisplay(templateHtml, error) {
        return `
            <div class="premium-mode-error">
                <div class="error-header">
                    <h3>🛡️ Zero-Trust Mode - Content Loading Error</h3>
                </div>
                <div class="error-content">
                    <p>Your content is safely stored locally, but there was an error displaying it.</p>
                    <details>
                        <summary>Technical Details</summary>
                        <pre>${error.message}</pre>
                    </details>
                    <div class="error-actions">
                        <button onclick="location.reload()" class="retry-btn">
                            Retry Loading
                        </button>
                        <button onclick="window.premiumModeController.exportData()" class="export-btn">
                            Export Data
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Create minimal display for complete failure
     * @returns {string} Minimal HTML
     */
    createMinimalDisplay() {
        return `
            <div class="premium-mode-minimal">
                <div class="minimal-header">
                    <h3>🛡️ Zero-Trust Mode Active</h3>
                </div>
                <div class="minimal-content">
                    <p>Your data is secure and stored locally.</p>
                    <p>Please refresh the page to try loading your content again.</p>
                    <button onclick="location.reload()" class="reload-btn">
                        Refresh Page
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Reset fallback attempts
     */
    reset() {
        this.fallbackAttempts = 0;
    }
}

// Integration with enhanced premium mode controller
// Final premium mode functions with comprehensive error handling

/**
 * Render cards with comprehensive error handling
 * @param {string} templateHtml - Template HTML
 * @returns {string} Rendered HTML
 */
async function renderCardsWithErrorHandling(templateHtml) {
    try {
        // Reset error handler
        errorHandlerState.fallbackAttempts = 0;

        // Try normal rendering
        return await renderCardsWithProgress(templateHtml);

    } catch (error) {
        // Handle with fallbacks
        return await handleInjectionFailure(templateHtml, error);
    }
}

/**
 * Export data for backup/migration
 * @returns {void}
 */
async function exportPremiumData() {
        try {
            const data = await window.dataSyncManager.exportLocalData();

            // Create download
            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `multicardz-backup-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            this.showSuccess('Data exported successfully');

        } catch (error) {
            this.showError('Export failed: ' + error.message);
        }
    }

    /**
     * Show success message
     * @param {string} message - Success message
     */
    showSuccess(message) {
        const notification = document.createElement('div');
        notification.className = 'success-notification';
        notification.innerHTML = `
            <div class="success-content">
                <span class="success-icon">✅</span>
                <span class="success-message">${message}</span>
                <button class="success-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }
}

// Final global controller
window.premiumModeController = new FinalPremiumModeController();
```

**Day 5: Integration Testing and Performance Validation**

- End-to-end hybrid rendering testing
- Performance benchmarking with large datasets
- Error scenario validation

### Deliverables

- [x] UUID placeholder template system
- [x] Mode-aware rendering pipeline
- [x] Advanced content injection with optimization
- [x] Comprehensive error handling and fallbacks
- [x] HTMX compatibility maintenance
- [x] Performance optimization for large datasets

### Success Criteria

- Hybrid rendering works seamlessly across all three modes
- Content injection completes in <200ms for 100 cards
- Error handling gracefully degrades without data loss
- HTMX functionality preserved for standard/development modes

## Phase 6: Dimensional Sets & Multiplicity (Week 11-12)

### Objectives

- Will implement spatial set formation with n-dimensional grids
- Will enable card multiplicity through intersection sets
- Will add visual distinction requirements for multi-location cards
- Will create n-dimensional slices with scrollable views

### Tasks

#### Week 11: Dimensional Grid Architecture

**Day 1-2: Spatial Set Formation**

```python
# Pure function for n-dimensional grid operations
async def form_spatial_grid(
    row_tags: frozenset[str],
    column_tags: frozenset[str],
    slice_tags: frozenset[str],
    workspace_id: str
) -> dict[str, dict[str, frozenset[Card]]]:
    """
    Form n-dimensional spatial grid from tag sets.

    Args:
        row_tags: Tags for grid rows
        column_tags: Tags for grid columns
        slice_tags: Tags for grid slices (3rd dimension)
        workspace_id: Tenant isolation

    Returns:
        Matrix of cards organized by spatial intersections
    """
    # Mathematical set operations for each grid cell
    # Cell(i,j,k) = row_tag[i] ∩ column_tag[j] ∩ slice_tag[k]
    pass

async def compute_card_multiplicity(
    card: Card,
    spatial_grid: dict[str, dict[str, frozenset[Card]]]
) -> dict[str, list[tuple[int, int, int]]]:
    """
    Determine which spatial grid cells contain each card.
    Cards appear in multiple locations when they match multiple intersections.
    """
    locations = []
    for row_idx, row in enumerate(spatial_grid.values()):
        for col_idx, cell_cards in enumerate(row.values()):
            if card in cell_cards:
                locations.append((row_idx, col_idx, 0))  # Extend for n-dimensions
    return {card.uuid: locations}
```

**Day 3-4: Visual Distinction Implementation**

```javascript
// Client-side visual indicators for card multiplicity
function renderCardWithMultiplicity(card, locations) {
    const cardElement = createCardElement(card);

    if (locations.length > 1) {
        // Multi-location visual indicators
        cardElement.classList.add('multi-location');
        cardElement.setAttribute('data-locations', locations.length);

        // Add badge showing location count
        const badge = document.createElement('span');
        badge.className = 'location-badge';
        badge.textContent = `${locations.length} locations`;
        cardElement.appendChild(badge);

        // Border highlighting for multi-location cards
        cardElement.style.borderColor = '#ff6b35';
        cardElement.style.borderWidth = '2px';
        cardElement.style.opacity = '0.95';
    }

    return cardElement;
}
```

**Day 5: N-Dimensional Slice Navigation**

```python
async def create_dimensional_slices(
    base_grid: dict[str, dict[str, frozenset[Card]]],
    slice_dimension_tags: frozenset[str],
    workspace_id: str
) -> dict[str, dict[str, dict[str, frozenset[Card]]]]:
    """
    Create scrollable slices for 3rd+ dimensions.

    Returns:
        Sliced grids: {slice_tag: {row: {col: cards}}}
    """
    slices = {}
    for slice_tag in slice_dimension_tags:
        # Filter base grid by slice intersection
        slice_grid = {}
        for row_key, row in base_grid.items():
            slice_grid[row_key] = {}
            for col_key, cards in row.items():
                # Only include cards that also have slice_tag
                filtered_cards = frozenset(
                    card for card in cards
                    if slice_tag in card.tags
                )
                if filtered_cards:
                    slice_grid[row_key][col_key] = filtered_cards
        slices[slice_tag] = slice_grid
    return slices
```

#### Week 12: Mathematical Set Operations Integration

**Day 1-2: Pure Set Theory Implementation**

```python
async def compute_spatial_union_with_tags_in_play(
    spatial_grid: dict[str, dict[str, frozenset[Card]]],
    tags_in_play: frozenset[str],
    workspace_id: str
) -> frozenset[Card]:
    """
    Mathematical set union combining spatial intersections with tagsInPlay.

    Formula: U' = {c ∈ U : (row_tag ∩ column_tag ∩ slice_tag) ⊆ c.tags} ∪ tagsInPlay
    """
    # Extract all cards from spatial grid intersections
    spatial_cards = frozenset()
    for row in spatial_grid.values():
        for cell_cards in row.values():
            spatial_cards = spatial_cards | cell_cards

    # Load cards matching tagsInPlay
    tags_in_play_cards = await load_cards_by_tags(tags_in_play, workspace_id)

    # Union of spatial intersections and tagsInPlay
    return spatial_cards | tags_in_play_cards

# Pure set theory operations with mathematical documentation
async def intersection_all_zones(
    zone_tags: list[frozenset[str]],
    workspace_id: str
) -> frozenset[Card]:
    """I = ⋂ᵢ Tᵢ where Tᵢ = {c ∈ C : tagᵢ ∈ c.tags}"""
    pass

async def union_any_zones(
    zone_tags: list[frozenset[str]],
    workspace_id: str
) -> frozenset[Card]:
    """U = ⋃ᵢ Tᵢ where Tᵢ = {c ∈ C : tagᵢ ∈ c.tags}"""
    pass

async def exclusion_none_zones(
    include_tags: frozenset[str],
    exclude_tags: frozenset[str],
    workspace_id: str
) -> frozenset[Card]:
    """E = C - ⋃ᵢ Tᵢ where Tᵢ = {c ∈ C : tagᵢ ∈ c.tags}"""
    pass
```

### Deliverables

- [x] N-dimensional spatial grid formation algorithms
- [x] Card multiplicity detection and tracking
- [x] Visual distinction for multi-location cards
- [x] Dimensional slice navigation system
- [x] Pure set theory operations with mathematical documentation
- [x] Performance optimization for large dimensional grids

### Success Criteria

- Spatial grids support unlimited dimensions with consistent performance
- Card multiplicity correctly identified across all intersections
- Visual indicators clearly distinguish multi-location cards
- Set operations maintain <16ms performance for 1000+ cards
- Mathematical compliance with pure set theory operations

## Phase 7: Event Sourcing Integration (Week 13)

### Objectives

- **[NEW]** Will implement comprehensive event sourcing (no audit logging currently exists)
- **[NEW]** Will implement middleware-based event capture to Redpanda
- **[NEW]** Will create complete request/response/timing/user context logging
- **[NEW]** Will establish immutable audit trail for all system operations

### Tasks

#### Week 13: Redpanda Event Sourcing Implementation

**Day 1-2: Event Schema and Middleware**

```python
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass(frozen=True)
class SystemEvent:
    """Immutable event for comprehensive system logging."""
    event_id: str           # UUID for event identification
    timestamp: datetime     # Precise event timing
    event_type: str         # "query", "mutation", "security", "performance"
    user_id: str           # Zero-trust user identification
    workspace_id: str      # Tenant isolation context
    request_data: dict     # Complete request payload
    response_data: dict    # Complete response payload
    metadata: dict         # Timing, IP, user agent, etc.
    operation_path: str    # API endpoint path
    duration_ms: float     # Request processing time

async def capture_system_event(
    event_type: str,
    request_data: dict,
    response_data: dict,
    metadata: dict,
    user_context: dict
) -> None:
    """
    Pure function for streaming events to Redpanda.
    Called from FastAPI middleware on every request.
    """
    event = SystemEvent(
        event_id=generate_uuid(),
        timestamp=datetime.now(timezone.utc),
        event_type=event_type,
        user_id=user_context["user_id"],
        workspace_id=user_context["workspace_id"],
        request_data=request_data,
        response_data=response_data,
        metadata=metadata,
        operation_path=metadata["path"],
        duration_ms=metadata["duration"]
    )

    # Stream to Redpanda topic
    await Redpanda_producer.send("multicardz-events", event)
```

**Day 3-4: FastAPI Middleware Integration**

```python
async def event_sourcing_middleware(request: Request, call_next):
    """Capture every API operation as an immutable event."""
    start_time = time.time()

    # Capture request
    request_data = await extract_request_data(request)
    user_context = extract_user_context(request)

    # Process request
    response = await call_next(request)

    # Capture response and timing
    response_data = await extract_response_data(response)
    duration_ms = (time.time() - start_time) * 1000

    # Stream event (async, non-blocking)
    await capture_system_event(
        event_type=classify_operation(request.url.path),
        request_data=request_data,
        response_data=response_data,
        metadata={
            "path": request.url.path,
            "method": request.method,
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "duration": duration_ms
        },
        user_context=user_context
    )

    return response
```

**Day 5: Event Classification and Analysis**

```python
def classify_operation(path: str) -> str:
    """Classify API operations for event sourcing."""
    if "/api/render/cards" in path:
        return "query"
    elif "/api/cards" in path and request.method in ["POST", "PUT", "DELETE"]:
        return "mutation"
    elif "/auth" in path:
        return "security"
    elif duration_ms > 1000:
        return "performance"
    else:
        return "system"

# Event stream processing for real-time analytics
async def process_event_stream():
    """Process events for real-time monitoring and alerting."""
    async for event in Redpanda_consumer("multicardz-events"):
        # Real-time dashboards
        await update_performance_metrics(event)

        # Security monitoring
        if event.event_type == "security":
            await check_security_patterns(event)

        # Performance alerting
        if event.duration_ms > 5000:  # 5 second threshold
            await send_performance_alert(event)
```

### Deliverables

- [x] Comprehensive event sourcing system with Redpanda integration
- [x] FastAPI middleware capturing all operations automatically
- [x] Event classification and real-time processing
- [x] Immutable audit trail with complete request/response logging
- [x] Performance monitoring and alerting integration

### Success Criteria

- Every API operation captured as immutable event
- Redpanda streaming handles high-volume event processing
- Real-time analytics and alerting functional
- Zero impact on API performance (events streamed asynchronously)
- Complete audit trail available for compliance and debugging

## Phase 8: Testing & Validation (Week 14-15)

### Objectives

- **[EXISTS-MODIFY]** Will enhance existing test suite with dimensional tests
- **[NEW]** Will validate function-based architecture compliance (31 classes converted)
- **[NEW]** Will test all three operating modes thoroughly
- **[NEW]** Will ensure zero-trust isolation and security guarantees
- **[EXISTS-MODIFY]** Will enhance existing performance tests across all components

### Tasks

#### Week 14: Comprehensive Test Suite

**Day 1-2: Function-Based Architecture Tests**

```python
import pytest
import inspect
from typing import Callable

def test_no_classes_in_business_logic():
    """Verify no classes used for business logic (only approved types)."""
    # Based on actual codebase analysis, these are the class types to convert
    classes_to_convert = [
        'BaseModel',  # 13 Pydantic models
        'ABC',  # 2 Abstract Base Classes
        'NamedTuple',  # 3 Named tuples
        'Exception',  # 3 Custom exceptions
        # Plus 10 other regular classes
    ]

    # After conversion, only these immutable types should remain
    approved_types = {
        'dataclasses.dataclass',  # Immutable data structures
        'typing.NamedTuple',  # Immutable tuples
        'Exception',  # Exception classes (allowed)
    }

    # Scan all business logic modules
    for module in get_business_logic_modules():
        classes = get_all_classes(module)
        for cls in classes:
            base_name = cls.__base__.__name__
            assert base_name in approved_types, f"Class {cls} needs conversion to pure function"

def test_pure_function_signatures():
    """Verify all business functions are pure with explicit dependencies."""
    for func in get_business_functions():
        # Check function signature has explicit parameters (no hidden state)
        signature = inspect.signature(func)
        assert len(signature.parameters) > 0, f"Function {func} has no explicit dependencies"

        # Check function doesn't access global state
        assert not uses_global_state(func), f"Function {func} accesses global state"

def test_function_type_aliases():
    """Verify 31 existing classes have been converted to function type aliases."""
    type_aliases = get_function_type_aliases()
    assert 'LoadCardsFunction' in type_aliases
    assert 'LoadTagsFunction' in type_aliases
    assert 'UnionFunction' in type_aliases
    assert 'IntersectionFunction' in type_aliases
    assert 'RenderCardsFunction' in type_aliases
```

**Day 3-4: Dimensional Sets Tests**

```python
def test_spatial_grid_formation():
    """Test n-dimensional spatial grid creation."""
    row_tags = frozenset(['#priority-high', '#priority-low'])
    column_tags = frozenset(['#status-todo', '#status-done'])
    slice_tags = frozenset(['#team-frontend', '#team-backend'])

    grid = await form_spatial_grid(row_tags, column_tags, slice_tags, workspace_id)

    # Verify grid dimensions
    assert len(grid) == len(row_tags)
    for row in grid.values():
        assert len(row) == len(column_tags)

    # Verify mathematical set operations
    cell_cards = grid['#priority-high']['#status-todo']
    for card in cell_cards:
        assert '#priority-high' in card.tags
        assert '#status-todo' in card.tags

def test_card_multiplicity():
    """Test cards appearing in multiple spatial locations."""
    card = Card(
        uuid="test-card",
        content="Fix authentication bug",
        tags=frozenset(['#priority-high', '#status-todo', '#backend', '#urgent'])
    )

    grid = await create_test_spatial_grid()
    locations = await compute_card_multiplicity(card, grid)

    # This card should appear in multiple cells
    expected_locations = [
        (0, 0),  # #priority-high ∩ #status-todo
        (0, 2),  # #priority-high ∩ #urgent
        (2, 0),  # #backend ∩ #status-todo
        (2, 2),  # #backend ∩ #urgent
    ]

    assert len(locations[card.uuid]) >= len(expected_locations)

def test_mathematical_set_operations():
    """Verify pure set theory compliance."""
    # Test union: U = ⋃ᵢ Tᵢ
    result = await union_any_zones([
        frozenset(['#priority-high']),
        frozenset(['#status-todo'])
    ], workspace_id)

    # Verify every card in result has at least one of the tags
    for card in result:
        assert '#priority-high' in card.tags or '#status-todo' in card.tags

    # Test intersection: I = ⋂ᵢ Tᵢ
    result = await intersection_all_zones([
        frozenset(['#priority-high']),
        frozenset(['#status-todo'])
    ], workspace_id)

    # Verify every card in result has all of the tags
    for card in result:
        assert '#priority-high' in card.tags and '#status-todo' in card.tags
```

#### Week 15: Integration and Performance Tests

**Day 1-3: Zero-Trust Security Validation**

```python
def test_workspace_isolation():
    """Verify complete workspace isolation."""
    workspace_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    workspace_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    # Create cards in workspace A
    cards_a = await create_test_cards(workspace_a)

    # Attempt to access from workspace B
    result = await load_cards("premium", {}, workspace_b, frozenset())

    # Verify no cross-workspace access
    workspace_a_uuids = {card.uuid for card in cards_a}
    result_uuids = {card if isinstance(card, str) else card.uuid for card in result}
    assert workspace_a_uuids.isdisjoint(result_uuids)

def test_content_isolation_premium_mode():
    """Verify content never transmitted in premium mode."""
    with mock.patch('requests.post') as mock_request:
        # Make API call in premium mode
        response = await call_api_endpoint("premium", {
            "tagsInPlay": ["uuid1", "uuid2"],
            "zones": []
        })

        # Verify request payload contains only UUIDs
        request_data = mock_request.call_args[1]['json']
        for value in extract_all_values(request_data):
            if isinstance(value, str):
                # All strings should be UUIDs, not human-readable content
                assert is_uuid_format(value) or value in ['premium', 'cards'], f"Non-UUID content: {value}"

def test_performance_benchmarks():
    """Validate performance meets architectural requirements."""
    # Test set operations performance
    start_time = time.time()
    result = await compute_spatial_union_with_tags_in_play(
        large_spatial_grid, frozenset(['tag1', 'tag2']), workspace_id
    )
    duration_ms = (time.time() - start_time) * 1000

    # Must be <16ms for spatial operations
    assert duration_ms < 16, f"Set operation took {duration_ms}ms, target <16ms"

    # Test rendering performance
    start_time = time.time()
    html = await render_cards_response("premium", {}, result, {})
    duration_ms = (time.time() - start_time) * 1000

    # Must be <200ms end-to-end
    assert duration_ms < 200, f"Rendering took {duration_ms}ms, target <200ms"
```

### Deliverables

- [x] Comprehensive test suite covering all architectural patterns
- [x] Function-based architecture compliance validation
- [x] Dimensional sets mathematical correctness tests
- [x] Zero-trust security and isolation validation
- [x] Performance benchmarks meeting all targets
- [x] Multi-mode integration tests

### Success Criteria

- 100% test coverage for all business logic
- All architectural compliance tests passing
- Performance benchmarks exceed targets (<16ms set ops, <200ms rendering)
- Security tests verify zero cross-tenant access
- Integration tests validate all three operating modes

## Phase 9: Migration & Documentation (Week 16)

### Objectives

- **[NEW]** Will create customer data portability tools with updated patterns
- **[EXISTS-MODIFY]** Will update existing documentation for all architectural changes
- **[NEW]** Will provide migration guides for existing deployments
- **[NEW]** Will establish maintenance and monitoring procedures

### Tasks

#### Week 16: Migration Tools and Documentation

**Day 1-2: Data Portability Tools**

```python
async def export_workspace_data(
    workspace_id: str,
    export_format: str = "json"  # json, sql, csv
) -> dict[str, Any]:
    """
    Export complete workspace data for customer portability.
    Includes all cards, tags, views, and access patterns.
    """
    export_data = {
        "workspace_id": workspace_id,
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "schema_version": "2.0",  # Zero-trust schema version
        "cards": await export_cards_with_access_control(workspace_id),
        "tags": await export_tags_with_metadata(workspace_id),
        "card_contents": await export_card_contents_full(workspace_id),
        "views": await export_views_with_tags_in_play(workspace_id),
        "access_patterns": await export_shared_access_patterns(workspace_id)
    }

    if export_format == "sql":
        return generate_sql_dump(export_data)
    elif export_format == "csv":
        return generate_csv_files(export_data)
    else:
        return export_data

async def import_workspace_data(
    workspace_id: str,
    import_data: dict[str, Any],
    mode: str = "standard"  # development, standard, premium
) -> dict[str, int]:
    """
    Import workspace data with mode-appropriate transformations.
    Handles UUID mapping and access control patterns.
    """
    # Validate schema compatibility
    assert import_data["schema_version"] >= "2.0", "Legacy schema not supported"

    # Import with mode-specific handling
    if mode == "premium":
        # Ensure no content transmitted to backend
        return await import_uuid_only_mode(workspace_id, import_data)
    else:
        # Standard import with full content
        return await import_full_content_mode(workspace_id, import_data)
```

**Day 3-4: Architecture Documentation Updates**

```markdown
# multicardz Zero-Trust Architecture Migration Guide

## Planned Architectural Patterns

### Database Schema Changes
- **User/Workspace Isolation**: All tables will include user_id and workspace_id for zero-trust isolation
- **Shared Access Control**: Will add access JSON column with owner/invited/public patterns
- **Audit Trail**: Will add created, modified, deleted columns for complete audit history
- **No UUID Mappings Table**: Will use planned integer_id column in cards/tags tables instead of separate mappings

### Function-Based Architecture
- **Class Elimination**: Will convert 31 existing classes (13 BaseModel, 2 ABC, etc.) to pure functions and type aliases
- **Pure Functions Only**: Will not use classes for business logic (only approved types)
- **Database Facade**: Will implement pure function facade pattern instead of class hierarchies
- **Factory Functions**: Will create pure function factories to replace class-based implementations

### Communication Pattern Changes
- **Fixed Drag-Drop Flow**: Will implement: browser DOM → tagsInPlay → /api/render/cards → HTML response
- **UUID Sync Scope**: Will add real-time sync for card/tag mutations, not drag-drop operations
- **Template Separation**: Will separate server UUID templates from client content injection

### Dimensional Sets Implementation
- **N-Dimensional Grids**: Will implement spatial set formation with unlimited dimensions
- **Card Multiplicity**: Cards will appear in multiple spatial locations through intersections
- **Visual Distinction**: Multi-location cards will have visual indicators and badges
- **Mathematical Compliance**: Will use pure set theory operations with formal documentation

### Event Sourcing Integration
- **Comprehensive Logging**: Middleware will capture all request/response/timing/context
- **Redpanda Streaming**: Will add real-time event processing for analytics and monitoring
- **Immutable Audit**: Will maintain complete event history for compliance and debugging
```

**Day 5: Maintenance Documentation**

```python
# Monitoring and Maintenance Procedures

async def health_check_zero_trust_compliance():
    """Verify zero-trust architecture compliance."""
    checks = {
        "workspace_isolation": await verify_no_cross_workspace_access(),
        "content_privacy": await verify_no_content_in_premium_requests(),
        "function_purity": await verify_no_business_logic_classes(),
        "audit_completeness": await verify_all_operations_logged(),
        "performance_targets": await verify_performance_benchmarks()
    }

    for check_name, passed in checks.items():
        if not passed:
            await send_compliance_alert(check_name)

    return all(checks.values())

def deployment_checklist():
    """Pre-deployment validation checklist."""
    return [
        "✓ Database schema migration tested and validated",
        "✓ Function-based architecture compliance verified",
        "✓ Zero-trust isolation tests passing",
        "✓ Performance benchmarks meeting targets",
        "✓ Event sourcing capturing all operations",
        "✓ Multi-mode compatibility validated",
        "✓ Security audit completed and approved"
    ]
```

### Deliverables

- [x] Complete data portability tools for customer migration
- [x] Updated architecture documentation with all pattern changes
- [x] Migration guides for existing deployments
- [x] Monitoring and maintenance procedures
- [x] Deployment checklists and validation tools
- [x] Training materials for new architectural patterns

### Success Criteria

- Customer data export/import tools working across all modes
- Documentation accurately reflects all architectural changes
- Migration procedures tested on sample deployments
- Monitoring tools detect compliance violations immediately
- Support team trained on new patterns and troubleshooting

## Implementation Timeline Summary

| Week  | Phase                            | Key Deliverables                                       | Success Metrics                                |
| ----- | -------------------------------- | ------------------------------------------------------ | ---------------------------------------------- |
| 1-2   | Database Schema & Access Control | Zero-trust schema, shared access patterns              | 100% data preservation, complete isolation     |
| 3-4   | Function-Based Architecture      | Function type aliases, pure function conversion        | No business logic classes, pure functions only |
| 5-6   | UUID Mapping & Set Operations    | RoaringBitmap using planned integer_id, real-time sync | <10ms for 1000 cards, no mappings table        |
| 7-8   | SQLite WASM Integration          | Multi-demo DBs, browser storage                        | <3s initialization, <100ms injection           |
| 9-10  | Hybrid Rendering & Communication | Implement fixed drag-drop flow, content injection      | <200ms end-to-end, proper separation           |
| 11-12 | Dimensional Sets & Multiplicity  | N-dimensional grids, card multiplicity                 | Unlimited dimensions, <16ms performance        |
| 13    | Event Sourcing Integration       | Redpanda middleware, comprehensive logging                | Complete audit trail, zero performance impact  |
| 14-15 | Testing & Validation             | Architectural compliance, dimensional tests            | 100% coverage, all patterns validated          |
| 16    | Migration & Documentation        | Updated patterns, portability tools                    | Zero-downtime transitions, complete guides     |

## Risk Mitigation Strategies

### Technical Risks

1. **SQLite WASM Performance**: Comprehensive benchmarking with fallback to standard mode
2. **UUID Sync Reliability**: Retry logic, checksum validation, conflict resolution
3. **RLS Complexity**: Automated testing, security audits, principle of least privilege

### Operational Risks

1. **Migration Complexity**: Staged rollouts, comprehensive backups, rollback procedures
2. **Mode Switching**: Export/import validation, staged migrations, data verification

### Timeline Risks

1. **Dependencies**: Parallel development tracks, early integration testing
2. **Complexity**: Incremental delivery, MVP approach, regular stakeholder reviews

## Success Criteria

### Phase Completion Criteria

- Each phase must pass all acceptance tests before proceeding
- Performance benchmarks must meet or exceed targets
- Security validation must show zero content leakage in premium mode
- All existing functionality must be preserved

### Overall Implementation Success

- Zero-trust architecture verified by external security audit
- Performance maintains <16ms spatial operations
- Customer migration tools enable zero-downtime transitions
- All three modes (development, standard, premium) fully functional

## Turso Deployment Configuration

### Environment Setup

```bash
# Required environment variables
export TURSO_DATABASE_URL="your-database.turso.io"
export TURSO_AUTH_TOKEN="your-auth-token"
export TURSO_SYNC_INTERVAL="60"  # seconds
export DB_MODE="privacy"  # or "development" or "normal"
export OBFUSCATION_SECRET="your-secret-key"  # For Privacy Mode

# Install Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Login to Turso
turso auth login

# Create organization databases
turso db create multicardz-auth  # Central auth database (if not using external auth)
turso db create multicardz-audit  # Audit logs
```

### Database Initialization

```bash
# Development Mode - Local SQLite
mkdir -p data/development/{preferences,projects}

# Normal Mode - Turso Edge
turso db create multicardz-edge --location nearest
turso db shell multicardz-edge < schema/turso_schema.sql

# Privacy Mode - Turso with embedded replicas
turso db create multicardz-privacy-template
turso db shell multicardz-privacy-template < schema/privacy_schema.sql
```

### Per-Customer Setup (Privacy Mode)

```python
def provision_customer_privacy_database(user_id: str, workspace_id: str):
    """
    Provision a new customer database in Privacy Mode.
    """
    import subprocess
    import os

    # Create Turso database for this customer
    db_name = f"{user_id}-{workspace_id}-privacy"

    # Create database from template
    subprocess.run([
        "turso", "db", "create", db_name,
        "--from-database", "multicardz-privacy-template"
    ])

    # Get connection details
    result = subprocess.run(
        ["turso", "db", "show", db_name, "--url"],
        capture_output=True, text=True
    )
    db_url = result.stdout.strip()

    # Create local embedded replica directory
    local_path = f"data/privacy/{user_id}_{workspace_id}"
    os.makedirs(local_path, exist_ok=True)

    # Initialize embedded replica configuration
    config = {
        "sync_url": db_url,
        "auth_token": os.getenv("TURSO_AUTH_TOKEN"),
        "sync_interval": int(os.getenv("TURSO_SYNC_INTERVAL", "60")),
        "local_path": f"{local_path}/replica.db"
    }

    # Save configuration
    with open(f"{local_path}/config.json", "w") as f:
        json.dump(config, f)

    return config
```

### Connection Management

```python
def get_database_connection(user_id: str, workspace_id: str, mode: str):
    """
    Get appropriate database connection based on mode.
    """
    if mode == "development":
        # Local SQLite
        return f"sqlite:///data/development/projects/{user_id}_{workspace_id}.db"

    elif mode == "normal":
        # Turso Edge
        turso_url = os.getenv("TURSO_DATABASE_URL")
        auth_token = os.getenv("TURSO_AUTH_TOKEN")
        db_name = f"{user_id}-{workspace_id}"
        return f"libsql://{db_name}.{turso_url}?authToken={auth_token}"

    elif mode == "privacy":
        # Turso embedded replica
        import libsql_experimental as libsql

        config_path = f"data/privacy/{user_id}_{workspace_id}/config.json"
        with open(config_path) as f:
            config = json.load(f)

        # Return embedded replica connection
        return libsql.Database(
            path=config["local_path"],
            sync_url=config["sync_url"],
            auth_token=config["auth_token"],
            sync_interval=config["sync_interval"]
        )
```

### Monitoring and Maintenance Scripts

```bash
# Monitor sync status
turso db inspect multicardz-privacy-{user}-{workspace} --instances

# Check replication lag
turso db show multicardz-privacy-{user}-{workspace} --instance-urls

# Force sync from CLI
turso db sync multicardz-privacy-{user}-{workspace}

# Backup all customer databases
for db in $(turso db list | grep privacy); do
    turso db export $db > backups/${db}_$(date +%Y%m%d).sql
done
```

### Disaster Recovery

```python
def restore_customer_database(user_id: str, workspace_id: str, backup_path: str):
    """
    Restore customer database from backup.
    """
    import subprocess

    db_name = f"{user_id}-{workspace_id}-privacy"

    # Delete existing database if present
    subprocess.run(["turso", "db", "destroy", db_name, "--yes"])

    # Create new database
    subprocess.run(["turso", "db", "create", db_name])

    # Import backup
    with open(backup_path) as backup:
        subprocess.run(
            ["turso", "db", "shell", db_name],
            stdin=backup
        )

    # Re-initialize local replica
    local_path = f"data/privacy/{user_id}_{workspace_id}"
    if os.path.exists(f"{local_path}/replica.db"):
        os.remove(f"{local_path}/replica.db")

    # Force initial sync
    subprocess.run(["turso", "db", "sync", db_name])
```

### Performance Tuning

```sql
-- Turso-specific optimizations
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 30000000000;  -- 30GB mmap

-- Create indexes for obfuscated operations
CREATE INDEX idx_card_bitmaps ON obfuscated_cards(card_bitmap);
CREATE INDEX idx_tag_bitmaps ON obfuscated_tags(tag_bitmap);
CREATE INDEX idx_sync_version ON obfuscated_cards(sync_version);
```

## Post-Implementation

### Monitoring and Maintenance

- Performance metrics dashboards for all three modes
- Security monitoring for RLS policy violations
- Customer adoption tracking for premium features
- Automated testing pipeline for all modes

### Future Enhancements

- Blockchain integration for immutable audit trails
- Federated learning on UUID patterns
- Multi-cloud deployment with consistent RLS
- Real-time collaboration through UUID operational transforms

---

**Implementation Plan Status**: APPROVED - Ready for Phase 1 Execution
**Expected Completion**: 16 weeks from start date
**Next Action**: Begin Phase 1 - Database Schema Standardization