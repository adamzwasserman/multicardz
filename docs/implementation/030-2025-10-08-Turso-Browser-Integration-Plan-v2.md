# Turso DB in Browser Integration Plan - Privacy-First Bitmap Slave Architecture

## Document Metadata
**Document Version**: 2.0 (CORRECTED ARCHITECTURE - THREE MODES)
**Date**: 2025-10-09
**Previous Version**: v1.0 (DEPRECATED - incorrect architecture)
**Status**: ARCHITECTURE DESIGN - READY FOR IMPLEMENTATION
**Estimated Duration**: 7-9 days (Privacy Mode implementation only)
**Reference**: Zero-Trust UUID Architecture + Privacy-Preserving Obfuscation Architecture

**Implementation Scope**:
- 🔧 Dev Mode: Migrate to Turso CLI (0.5 days - switch from raw SQLite to `turso dev`)
- 🔧 Normal Mode: Add Turso cloud support (1 day)
- ❌ Privacy Mode: Full implementation (7-9 days - this plan)

## Critical Corrections from v1.0

### ❌ INCORRECT (v1.0):
- Server had full database replica
- RoaringBitmap operations in browser
- Sync pushed full content to cloud
- Three operational modes (Privacy/Hybrid/Cloud)
- Used generic `@libsql/client` package

### ✅ CORRECT (v2.0):
- **Three operational modes**: Dev (local Turso), Normal (Turso cloud), Privacy (browser WASM + bitmap slave)
- **Privacy mode**: Server is bitmap-slave only (special subscription feature)
  - Server has ONLY 2 tables: card_bitmaps, tag_bitmaps (no content)
  - Browser has FULL dataset in WASM
  - RoaringBitmap operations on server
  - Server never sees actual content
- **Normal mode**: Standard Turso cloud/edge database (server-side queries)
- **Dev mode**: Local Turso database file (development only)
- **Uses Turso DB everywhere**: Turso CLI (dev), Turso cloud (normal), Turso WASM (privacy)

## Executive Summary

Integrate **Turso DB** with **three operational modes** to support different use cases from development to privacy-focused deployments:

### Mode 1: Dev Mode (Local Development)
- **Database**: Local Turso database using Turso CLI (`turso dev`)
- **Tool**: Turso CLI for local development database
- **Purpose**: Fast local development without cloud dependencies
- **Use Case**: Development, testing, CI/CD pipelines
- **Network**: None required
- **Why Turso CLI**: Official Turso development tool, ensures consistency with cloud

### Mode 2: Normal Mode (Production Default)
- **Database**: Turso cloud/edge database (server-side)
- **Purpose**: Standard production deployment with edge replication
- **Use Case**: Most users, standard deployment
- **Network**: Required for all operations
- **Performance**: Low-latency edge queries (<50ms globally)

### Mode 3: Privacy Mode (Special Subscription)
- **Database**: Browser WASM (primary) + Server bitmap slave (secondary)
- **Purpose**: Maximum privacy - server never sees actual content
- **Use Case**: Privacy-conscious users, GDPR/HIPAA compliance, special subscription
- **Network**: Optional (works offline, syncs bitmaps only when online)
- **Architecture**:
  - **100% of actual data in browser** (cards, tags, content)
  - **Server has ONLY integer bitmaps** (no content, no PII)
  - **Set operations on server** using bitmap algebra
  - **Browser queries locally** for all content
  - **Server returns only UUIDs** (resolved to content in browser)

**Technology Stack**:
- **Database Service (All Modes)**: Turso DB
  - Dev Mode: `turso dev` (Turso CLI local development server)
  - Normal Mode: Turso cloud/edge database
  - Privacy Mode: Turso WASM in browser
- **Browser (Privacy Mode)**: `@tursodatabase/database-wasm` - Turso's browser database
- **Server (All Modes)**: Turso edge database with zero-trust isolation
- **Bundle (Privacy Mode)**: ~50KB JavaScript wrapper + ~500KB WASM binary (cached)
- **Storage (Privacy Mode)**: Origin Private File System (OPFS) - 50MB+ capacity

**What is Turso DB?**
- Turso's managed database service (edge SQLite)
- SQLite-compatible database with Turso's enhancements
- Same database across all modes (dev, production, browser)
- Key features:
  - Edge replication (global low latency)
  - Embedded replicas (local-first sync)
  - Browser WASM support
  - Zero-downtime migrations
- Ensures consistency: code tested in dev works identically in production

**Key Benefits**:
- ✅ **Flexible deployment**: Dev, production, or privacy modes
- ✅ **Privacy Mode**: Server never sees actual content (special subscription)
- ✅ **Offline-first (Privacy Mode)**: Full functionality without network
- ✅ **Sub-millisecond queries (Privacy Mode)**: libSQL WASM engine
- ✅ **Scalable set operations (Privacy Mode)**: Server-side bitmap algebra
- ✅ **Edge performance (Normal Mode)**: Global low-latency access
- ✅ **Zero cloud cost (Dev Mode)**: Local-only development

## Three-Mode Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATABASE MODE COMPARISON                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Mode 1: DEV MODE (Local Development)                               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Database: Local Turso database (turso dev)                         │
│  Tool:     Turso CLI for local development                          │
│  Location: Developer machine                                         │
│  Network:  None required                                             │
│  Status:   🔧 Switch to Turso CLI (minimal change)                   │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Mode 2: NORMAL MODE (Production Default)                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Database: Turso cloud/edge database (server-side)                  │
│  Location: Edge locations globally (<50ms latency)                  │
│  Network:  Required for all operations                              │
│  Status:   🔧 Minimal config needed (1 day)                          │
│  Tier:     Standard subscription (default for most users)           │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Mode 3: PRIVACY MODE (Premium Subscription)                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Database: Browser WASM (primary) + Server bitmap slave             │
│  Location: 100% content in browser, only bitmaps on server          │
│  Network:  Optional (works offline, syncs bitmaps when online)      │
│  Status:   ❌ Full implementation required (7-9 days)                │
│  Tier:     Premium subscription (privacy-focused users)             │
│  Privacy:  🔒 Server NEVER sees actual content                       │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Architecture Overview

### Mode 1: Dev Mode Architecture (Local Development)

```
┌─────────────────────────────────────┐
│     FastAPI Backend (Dev Server)    │
├─────────────────────────────────────┤
│  Connects to:                        │
│  ┌───────────────────────────────┐  │
│  │  Turso CLI Local Server       │  │
│  │  $ turso dev                  │  │
│  │  http://127.0.0.1:8080        │  │
│  │  - Full schema (all tables)   │  │
│  │  - Zero-trust isolation       │  │
│  │  - Auto-migration             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         ▲
         │ HTTP API
         │
┌─────────────────────────────────────┐
│         Browser (Thin Client)        │
│  - Makes API calls to localhost      │
│  - No local database                 │
└─────────────────────────────────────┘
```

**Characteristics**:
- **Turso CLI** (`turso dev`) for local development server
- Same database as production (Turso cloud)
- Fast iteration without cloud dependencies
- Full schema with all content
- Zero network costs
- Perfect for CI/CD and testing

### Mode 2: Normal Mode Architecture (Production Default)

```
┌─────────────────────────────────────┐
│         Browser (Thin Client)        │
│  - Makes API calls to server         │
│  - No local database                 │
└─────────────────────────────────────┘
         │
         │ HTTPS API
         ▼
┌─────────────────────────────────────┐
│      FastAPI Backend (Server)        │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐  │
│  │  Turso Cloud/Edge Database    │  │
│  │  - Edge replicas globally     │  │
│  │  - Full schema (all tables)   │  │
│  │  - Zero-trust isolation       │  │
│  │  - Auto-migration             │  │
│  │  - <50ms global latency       │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Characteristics**:
- Server-side database (standard production)
- Edge replication for global performance
- All queries run on server
- Full content visible to server
- Most users use this mode

### Mode 3: Privacy Mode Architecture (Special Subscription)

```
┌─────────────────────────────────────────────────────────────┐
│                  Browser (Primary Database)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Turso WASM Database (Full Dataset)          │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ cards table:                                  │  │   │
│  │  │  - card_id, name, description                 │  │   │
│  │  │  - workspace_id, user_id (zero-trust)         │  │   │
│  │  │  - tags (CSV: "uuid1,uuid2,uuid3")            │  │   │
│  │  │  - card_bitmap (INTEGER - computed)           │  │   │
│  │  │  - created, modified, deleted                 │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ tags table:                                   │  │   │
│  │  │  - tag_id, tag (name), workspace_id, user_id  │  │   │
│  │  │  - tag_bitmap (INTEGER - computed)            │  │   │
│  │  │  - card_count, created, deleted               │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ + all other tables (user_preferences, etc)    │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │  Storage: Origin Private File System (OPFS)          │   │
│  │  Capacity: 50MB+ (unlimited quota in Chrome)         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Operations:                                                 │
│  • Content queries (SELECT name, description FROM cards)     │
│  • Card/tag CRUD (INSERT, UPDATE, DELETE)                    │
│  • Bitmap computation (triggers auto-calculate bitmaps)      │
│  • Local rendering (all UI data from local DB)               │
└──────────────────────────────────────────────────────────────┘
                           │
                           │ Sync bitmaps only
                           │ (POST /api/sync/bitmaps)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Server/Edge (Bitmap Slave - Read Only)          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │     Turso Edge Database (Bitmap Tables ONLY)        │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ card_bitmaps table (SLAVE):                   │  │   │
│  │  │  - card_id (UUID)                             │  │   │
│  │  │  - card_bitmap (INTEGER)                      │  │   │
│  │  │  - tag_bitmaps (TEXT - JSON array of ints)   │  │   │
│  │  │  - workspace_id, user_id (zero-trust)         │  │   │
│  │  │  - synced_at                                  │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │  ┌───────────────────────────────────────────────┐  │   │
│  │  │ tag_bitmaps table (SLAVE):                    │  │   │
│  │  │  - tag_id (UUID)                              │  │   │
│  │  │  - tag_bitmap (INTEGER)                       │  │   │
│  │  │  - workspace_id, user_id (zero-trust)         │  │   │
│  │  │  - synced_at                                  │  │   │
│  │  └───────────────────────────────────────────────┘  │   │
│  │  NO CONTENT - NO PII - ONLY INTEGER BITMAPS          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Operations:                                                 │
│  • Set operations (RoaringBitmap: UNION, INTERSECTION, etc)  │
│  • Bitmap queries (SELECT card_bitmap WHERE ...)             │
│  • Returns: Array of card_ids matching bitmap filters        │
│  • NEVER mutates bitmaps (slave receives updates from browser)│
└──────────────────────────────────────────────────────────────┘
```

## Mode Selection and Switching

### Database Mode Configuration

Users can switch between modes at any time (with appropriate subscription):

```javascript
// In user settings or environment config
const DB_MODE = 'dev' | 'normal' | 'privacy';

// Mode selection persisted in user preferences
localStorage.setItem('db_mode', DB_MODE);
```

### Mode Switching Strategy

```
Dev Mode ←→ Normal Mode: Easy (just config change)
Normal Mode → Privacy Mode: Requires data migration (one-time)
Privacy Mode → Normal Mode: User choice (data stays in browser or syncs full to server)
```

### Subscription Requirements

| Mode | Subscription | Use Case |
|------|-------------|----------|
| Dev | Free | Developers only |
| Normal | Standard | Most users (default) |
| Privacy | Premium | Privacy-conscious users, GDPR/HIPAA compliance |

## Core Principles (Privacy Mode Only)

**Note**: These principles apply specifically to **Privacy Mode**. Dev and Normal modes use standard server-side database architecture.

### 1. Privacy-First Data Separation (Privacy Mode)

**Browser (Primary Source of Truth)**:
- All actual content (card names, descriptions, tag names)
- All user data and preferences
- Full database schema with content columns

**Server (Bitmap Slave - Zero Content)**:
- ONLY integer bitmaps derived from tag associations
- ONLY UUIDs for entity references
- NO readable content, NO PII, NO decryptable data

### 2. Query Routing Pattern (Privacy Mode)

```javascript
// Content queries → Browser WASM DB (Privacy Mode only)
const cards = await browserDB.execute(
  "SELECT card_id, name, description, tags FROM cards WHERE workspace_id = ?",
  [workspaceId]
);

// Set operation queries → Server bitmap slave (Privacy Mode only)
const matchingCardIds = await serverAPI.post('/api/bitmap/filter', {
  operations: [
    { type: 'UNION', tag_bitmaps: [bitmap1, bitmap2] },
    { type: 'INTERSECTION', tag_bitmaps: [bitmap3] }
  ]
});

// Combine: Get bitmaps from server, resolve content in browser
const filteredCards = cards.filter(c => matchingCardIds.includes(c.card_id));
```

**Dev/Normal Mode**: All queries go to server API (standard pattern)

### 3. Bitmap Sync Pattern (Privacy Mode Only)

```
Browser                          Server
   │                                │
   │  1. Modify card tags locally   │
   │  2. Trigger recalculates       │
   │     card_bitmap                │
   │                                │
   │  3. POST /api/sync/bitmaps     │
   ├──────────────────────────────► │
   │  {                             │
   │    card_id: "uuid",            │
   │    card_bitmap: 12345,         │
   │    tag_bitmaps: [11, 22, 33]   │
   │  }                             │
   │                                │
   │                   4. UPSERT to │
   │              card_bitmaps table│
   │              (slave receives)  │
   │                                │
   │  5. 204 No Content             │
   │ ◄────────────────────────────── │
   │                                │
```

## Current State Analysis

### Existing Architecture Strengths
✅ Zero-Trust UUID isolation (workspace_id, user_id on all tables)
✅ Auto-migration middleware (can work with browser DB)
✅ Pure function architecture (WASM-compatible)
✅ Bitmap calculation triggers (already computing card_bitmap)
✅ Card creation in spatial grid cells (apps/static/js/app.js:154-199)

### Integration Requirements
- ✅ Browser WASM database for full content storage
- ✅ Minimal server schema (2 tables: card_bitmaps, tag_bitmaps)
- ✅ Bitmap-only sync endpoint (POST /api/sync/bitmaps)
- ✅ Query router (content → browser, sets → server)
- ✅ Server-side RoaringBitmap operations endpoint

## Implementation Phases

**Note**: Dev and Normal modes largely already exist. This implementation plan focuses on adding **Privacy Mode** (browser WASM + bitmap slave server).

### Current State:
- 🔧 **Dev Mode**: Need to migrate to Turso CLI (`turso dev`)
- 🔧 **Normal Mode**: Need to add Turso cloud connection (minimal config)
- ❌ **Privacy Mode**: Requires full implementation (this plan)

### Implementation Focus: Privacy Mode

### Phase 0: Mode Infrastructure (Day 1)
**Duration**: 1 day
**Risk**: Low

#### Task 0.1: Add Mode Selection System
**Duration**: 4 hours

**File**: `apps/shared/config/database_mode.py`

```python
"""
Database mode configuration.
Determines which database backend to use.
"""
from enum import Enum
from typing import Literal

class DatabaseMode(str, Enum):
    """Database operational modes."""
    DEV = "dev"           # Local SQLite file (data/multicardz_dev.db)
    NORMAL = "normal"     # Turso cloud/edge database (default production)
    PRIVACY = "privacy"   # Browser WASM + bitmap slave server (premium)

# Environment variable or user preference
def get_database_mode() -> DatabaseMode:
    """Get current database mode from config."""
    import os
    mode = os.getenv('DB_MODE', 'normal').lower()
    return DatabaseMode(mode)

# Check if privacy mode is enabled for current user
def is_privacy_mode_enabled(user_id: str, workspace_id: str) -> bool:
    """Check if user has privacy mode subscription."""
    # TODO: Check subscription status
    return False  # Default: standard mode
```

**File**: `apps/static/js/config/database_mode.js`

```javascript
/**
 * Client-side database mode configuration.
 */

// Get mode from user preferences
export function getDatabaseMode() {
  return localStorage.getItem('db_mode') || 'normal';
}

// Set mode (requires subscription check for 'privacy')
export function setDatabaseMode(mode) {
  if (mode === 'privacy') {
    // TODO: Verify subscription
  }
  localStorage.setItem('db_mode', mode);
}

// Check if privacy mode is active
export function isPrivacyMode() {
  return getDatabaseMode() === 'privacy';
}
```

#### Task 0.2: Update Existing Connection Logic
**Duration**: 4 hours

Update existing database connection to support mode switching:

**File**: `apps/shared/config/database.py`

```python
from .database_mode import get_database_mode, DatabaseMode

def get_database_connection():
    """Get database connection based on current mode."""
    mode = get_database_mode()

    if mode == DatabaseMode.DEV:
        # Local Turso dev server (turso dev)
        return connect_to_turso_dev()

    elif mode == DatabaseMode.NORMAL:
        # Turso cloud/edge connection
        return connect_to_turso_cloud()

    elif mode == DatabaseMode.PRIVACY:
        # Server-side bitmap slave only
        return connect_to_turso_bitmap_slave()

    else:
        raise ValueError(f"Unknown database mode: {mode}")

def connect_to_turso_dev():
    """Connect to local Turso dev server (turso dev)."""
    import turso  # Turso's Python SDK
    return turso.connect(
        url='http://127.0.0.1:8080'  # Default turso dev port
    )

def connect_to_turso_cloud():
    """Connect to Turso cloud/edge database."""
    import os
    import turso
    return turso.connect(
        url=os.getenv('TURSO_DATABASE_URL'),
        auth_token=os.getenv('TURSO_AUTH_TOKEN')
    )

def connect_to_turso_bitmap_slave():
    """Connect to Turso bitmap slave database (Privacy Mode server)."""
    # In Privacy Mode, server only has bitmap tables
    import os
    import turso
    return turso.connect(
        url=os.getenv('TURSO_BITMAP_URL'),  # Separate Turso DB for bitmaps
        auth_token=os.getenv('TURSO_AUTH_TOKEN')
    )
```

### Phase 1: Browser Database Foundation (Days 2-3)
**Duration**: 2 days
**Risk**: Medium (new technology)
**Applies to**: Privacy Mode only

#### Task 1.1: Install and Configure Turso WASM
**Duration**: 3 hours

**NPM Packages (Turso Browser Database)**:
```bash
# Turso Browser Database (WASM-based)
npm install @tursodatabase/database-wasm

# Optional: For sync features
npm install @tursodatabase/sync-wasm
```

**Expected Bundle Size**:
- JavaScript wrapper: ~50KB (gzipped) - TypeScript/JS API layer
- WASM binary: ~500KB (gzipped) - Turso database compiled to WebAssembly
- Total initial: ~50KB JavaScript + 500KB WASM on first load
- Subsequent loads: ~50KB (WASM cached by browser)

**Architecture**:
```
Turso Browser Database Stack:
┌────────────────────────────────────┐
│  JavaScript Wrapper (~50KB)        │  ← TypeScript/JS API
├────────────────────────────────────┤
│  Turso WASM (500KB)                │  ← Turso database as WASM
├────────────────────────────────────┤
│  SQLite-compatible Engine          │  ← Database engine
└────────────────────────────────────┘
```

**Build Configuration** (Vite):
```javascript
// vite.config.js
export default {
  optimizeDeps: {
    exclude: ['@tursodatabase/database-wasm', '@tursodatabase/sync-wasm']
  },
  server: {
    headers: {
      // Required for SharedArrayBuffer (WASM threading)
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin'
    }
  }
}
```

**Minimal Connection Code (Local-Only)**:
```javascript
import { createClient } from '@tursodatabase/database-wasm';

// Lowest-cost initialization (local-only, no sync)
const db = await createClient({
  url: 'file:multicardz_local.db'  // Local OPFS storage
});

// Execute query
const result = await db.execute(
  'SELECT card_id, name FROM cards WHERE workspace_id = ?',
  [workspaceId]
);
```

**With Sync (Optional)**:
```javascript
import { createClient } from '@tursodatabase/sync-wasm';

const db = await createClient({
  url: 'file:multicardz_local.db',
  syncUrl: 'https://[your-db].turso.io',  // Turso edge database
  authToken: process.env.TURSO_AUTH_TOKEN,
  syncInterval: 5000  // Auto-sync every 5 seconds
});

// Sync manually
await db.sync();
```

**Cost Analysis**:
- **JavaScript size**: ~50KB (minimal overhead)
- **WASM size**: ~500KB (one-time download, cached)
- **Initialization speed**: <100ms (OPFS + WASM load)
- **Memory overhead**: ~2-5MB for WASM runtime
- **Query speed**: <1ms for indexed queries

✅ **This is the lowest-cost connection approach using Turso's browser database**

#### Task 1.2: Create Browser Database Service
**Duration**: 4 hours

**File**: `apps/static/js/services/browser_database.js`

```javascript
/**
 * Pure function service for browser-side database operations.
 * All content lives here - server only gets bitmaps.
 * Uses Turso's browser database (WASM).
 */
import { createClient } from '@tursodatabase/database-wasm';

// Module-level singleton
let dbConnection = null;

/**
 * Initialize browser database (local-first, no remote sync).
 * This is the primary database - all content lives here.
 */
export async function initializeBrowserDatabase() {
  if (dbConnection) {
    return { success: true, cached: true };
  }

  try {
    // Local-only Turso database in OPFS (WASM-based)
    dbConnection = await createClient({
      url: 'file:multicardz_local.db'
    });

    console.log('✅ Browser database initialized (OPFS, Turso WASM)');
    return { success: true, storage: 'opfs', engine: 'turso-wasm' };

  } catch (error) {
    console.error('❌ Failed to initialize browser database:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Execute query on browser database.
 * All content queries run here (NOT on server).
 */
export async function executeQuery(sql, params = []) {
  if (!dbConnection) {
    throw new Error('Database not initialized');
  }

  try {
    const result = await dbConnection.execute(sql, params);
    return {
      success: true,
      rows: result.rows,
      rowsAffected: result.rowsAffected
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Execute transaction (multiple statements).
 */
export async function executeTransaction(statements) {
  if (!dbConnection) {
    throw new Error('Database not initialized');
  }

  try {
    // Use batch for transaction
    await dbConnection.batch(statements.map(({ sql, params }) => ({
      sql,
      args: params || []
    })));

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Get database statistics.
 */
export async function getDatabaseStats() {
  if (!dbConnection) {
    return { initialized: false };
  }

  try {
    const sizeResult = await dbConnection.execute(
      "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"
    );

    const tableResult = await dbConnection.execute(
      "SELECT count(*) as count FROM sqlite_master WHERE type='table'"
    );

    return {
      initialized: true,
      sizeBytes: sizeResult.rows[0].size,
      tableCount: tableResult.rows[0].count
    };
  } catch (error) {
    return { initialized: true, error: error.message };
  }
}
```

#### Task 1.3: Integrate Auto-Migration with Browser DB
**Duration**: 3 hours

**File**: `apps/static/js/services/browser_migration.js`

```javascript
/**
 * Browser-side auto-migration (adapted from server middleware).
 * Uses same migration files as server.
 */
import { executeQuery, executeTransaction } from './browser_database.js';

// Migration registry (same as server-side)
const MIGRATIONS = [
  { version: 1, file: '001_zero_trust_schema.sql' },
  { version: 2, file: '002_add_bitmap_sequences.sql' }
];

// Track applied migrations in memory
let appliedMigrations = new Set();

/**
 * Initialize migration tracking.
 */
export async function initMigrationTracking() {
  try {
    // Ensure schema_version table exists
    await executeQuery(`
      CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY,
        applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Load applied migrations
    const result = await executeQuery('SELECT version FROM schema_version');
    if (result.success) {
      result.rows.forEach(row => appliedMigrations.add(row.version));
    }

    return { success: true, applied: Array.from(appliedMigrations) };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Apply migration if needed (error-triggered).
 */
export async function applyMigrationIfNeeded(error) {
  const errorMsg = error.message.toLowerCase();

  // Detect schema error (same patterns as server)
  let migration = null;

  if (errorMsg.includes('no such table: cards')) {
    migration = MIGRATIONS[0];
  } else if (errorMsg.includes('no such column: card_bitmap')) {
    migration = MIGRATIONS[1];
  }

  if (!migration) {
    return { applied: false, error: 'No migration available' };
  }

  if (appliedMigrations.has(migration.version)) {
    return { applied: false, error: 'Migration already applied' };
  }

  // Fetch and apply migration SQL
  try {
    const response = await fetch(`/migrations/${migration.file}`);
    const sql = await response.text();

    // Execute migration
    await executeTransaction([{ sql, params: [] }]);

    // Record in schema_version
    await executeQuery(
      'INSERT INTO schema_version (version) VALUES (?)',
      [migration.version]
    );

    appliedMigrations.add(migration.version);

    console.log(`✅ Migration ${migration.version} applied`);
    return { applied: true, version: migration.version };

  } catch (migrationError) {
    console.error(`❌ Migration ${migration.version} failed:`, migrationError);
    return { applied: false, error: migrationError.message };
  }
}
```

### Phase 2: Server Bitmap Slave Schema (Day 3)
**Duration**: 1 day
**Risk**: Low

#### Task 2.1: Create Bitmap-Only Server Schema
**Duration**: 4 hours

**File**: `migrations/003_bitmap_slave_tables.sql`

```sql
-- Server-side bitmap slave tables (CONTENT-FREE)
-- These tables contain ONLY integer bitmaps and UUIDs
-- NO readable content, NO PII, NO card/tag names

-- Card bitmap slave table
CREATE TABLE IF NOT EXISTS card_bitmaps (
    card_id TEXT PRIMARY KEY,           -- UUID reference (no readable content)
    workspace_id TEXT NOT NULL,         -- Zero-trust isolation
    user_id TEXT NOT NULL,              -- Zero-trust isolation
    card_bitmap INTEGER NOT NULL,       -- Integer bitmap from tag associations
    tag_bitmaps TEXT NOT NULL,          -- JSON array of tag integer bitmaps
    synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Last sync timestamp

    -- Zero-trust constraint
    CONSTRAINT fk_workspace FOREIGN KEY (workspace_id, user_id)
        REFERENCES workspaces(workspace_id, user_id)
);

-- Tag bitmap slave table
CREATE TABLE IF NOT EXISTS tag_bitmaps (
    tag_id TEXT PRIMARY KEY,            -- UUID reference (no readable content)
    workspace_id TEXT NOT NULL,         -- Zero-trust isolation
    user_id TEXT NOT NULL,              -- Zero-trust isolation
    tag_bitmap INTEGER NOT NULL,        -- Integer bitmap for this tag
    synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Last sync timestamp

    -- Zero-trust constraint
    CONSTRAINT fk_workspace FOREIGN KEY (workspace_id, user_id)
        REFERENCES workspaces(workspace_id, user_id)
);

-- Indexes for fast bitmap lookups
CREATE INDEX IF NOT EXISTS idx_card_bitmaps_workspace
    ON card_bitmaps(workspace_id, user_id);
CREATE INDEX IF NOT EXISTS idx_tag_bitmaps_workspace
    ON tag_bitmaps(workspace_id, user_id);

-- Comment documenting privacy guarantees
COMMENT ON TABLE card_bitmaps IS
    'BITMAP SLAVE TABLE - Contains ONLY integer bitmaps and UUIDs.
     NO content, NO PII, NO readable data.
     Server performs set operations on bitmaps and returns matching UUIDs to browser.';
```

**Schema Validation**:
```sql
-- Verify no content columns exist
SELECT column_name FROM information_schema.columns
WHERE table_name IN ('card_bitmaps', 'tag_bitmaps')
  AND column_name NOT IN (
    'card_id', 'tag_id', 'workspace_id', 'user_id',
    'card_bitmap', 'tag_bitmap', 'tag_bitmaps', 'synced_at'
  );
-- Must return 0 rows (no content columns)
```

#### Task 2.2: Create Bitmap Sync Endpoint
**Duration**: 4 hours

**File**: `apps/user/routes/bitmap_sync_api.py`

```python
"""
Bitmap sync endpoint - receives bitmap updates from browser.
Server is SLAVE - never mutates bitmaps, only receives updates.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter(prefix="/api/sync", tags=["bitmap_sync"])
logger = logging.getLogger(__name__)


class BitmapSyncRequest(BaseModel):
    """Request payload for bitmap sync (content-free)."""
    card_id: str
    workspace_id: str
    user_id: str
    card_bitmap: int
    tag_bitmaps: list[int]  # Array of tag integer bitmaps


@router.post("/bitmaps")
async def sync_bitmaps(request: BitmapSyncRequest):
    """
    Receive bitmap updates from browser (slave endpoint).

    Server NEVER mutates bitmaps - only receives updates from browser.
    Server has NO knowledge of actual content (card names, tag names, etc).
    """
    try:
        # Import database connection
        from apps.shared.repositories.card_repository import get_card_db_connection

        with get_card_db_connection() as conn:
            # UPSERT card bitmap (slave receives update)
            conn.execute("""
                INSERT INTO card_bitmaps
                    (card_id, workspace_id, user_id, card_bitmap, tag_bitmaps, synced_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(card_id) DO UPDATE SET
                    card_bitmap = excluded.card_bitmap,
                    tag_bitmaps = excluded.tag_bitmaps,
                    synced_at = CURRENT_TIMESTAMP
            """, (
                request.card_id,
                request.workspace_id,
                request.user_id,
                request.card_bitmap,
                ','.join(map(str, request.tag_bitmaps))  # CSV of integers
            ))

            conn.commit()

        logger.info(
            f"✅ Bitmap sync: card {request.card_id} "
            f"(bitmap={request.card_bitmap}, tags={len(request.tag_bitmaps)})"
        )

        return {"status": "synced", "card_id": request.card_id}

    except Exception as e:
        logger.error(f"❌ Bitmap sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TagBitmapSyncRequest(BaseModel):
    """Request payload for tag bitmap sync."""
    tag_id: str
    workspace_id: str
    user_id: str
    tag_bitmap: int


@router.post("/tag-bitmaps")
async def sync_tag_bitmaps(request: TagBitmapSyncRequest):
    """
    Receive tag bitmap updates from browser (slave endpoint).
    """
    try:
        from apps.shared.repositories.card_repository import get_card_db_connection

        with get_card_db_connection() as conn:
            # UPSERT tag bitmap
            conn.execute("""
                INSERT INTO tag_bitmaps
                    (tag_id, workspace_id, user_id, tag_bitmap, synced_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(tag_id) DO UPDATE SET
                    tag_bitmap = excluded.tag_bitmap,
                    synced_at = CURRENT_TIMESTAMP
            """, (
                request.tag_id,
                request.workspace_id,
                request.user_id,
                request.tag_bitmap
            ))

            conn.commit()

        logger.info(f"✅ Tag bitmap sync: {request.tag_id} (bitmap={request.tag_bitmap})")

        return {"status": "synced", "tag_id": request.tag_id}

    except Exception as e:
        logger.error(f"❌ Tag bitmap sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 3: Query Routing & Integration (Days 4-5)
**Duration**: 2 days
**Risk**: Medium

#### Task 3.1: Create Query Router
**Duration**: 4 hours

**File**: `apps/static/js/services/query_router.js`

```javascript
/**
 * Query router - routes queries to appropriate execution context.
 *
 * Content queries → Browser WASM DB (SELECT name, description, etc)
 * Set operations → Server bitmap API (bitmap algebra)
 */
import { executeQuery as executeBrowserQuery } from './browser_database.js';

/**
 * Fetch cards from browser DB (content queries).
 */
export async function fetchCards(workspaceId, userId, options = {}) {
  const { limit = 1000, offset = 0 } = options;

  const result = await executeBrowserQuery(
    `SELECT card_id, name, description, tags, card_bitmap, created, modified
     FROM cards
     WHERE workspace_id = ? AND user_id = ? AND deleted IS NULL
     ORDER BY created DESC
     LIMIT ? OFFSET ?`,
    [workspaceId, userId, limit, offset]
  );

  if (!result.success) {
    throw new Error(`Failed to fetch cards: ${result.error}`);
  }

  return result.rows.map(row => ({
    id: row.card_id,
    name: row.name,
    description: row.description || '',
    tags: row.tags ? row.tags.split(',') : [],
    card_bitmap: row.card_bitmap,
    created: row.created,
    modified: row.modified
  }));
}

/**
 * Perform set operations on server (bitmap queries).
 * Returns array of card UUIDs matching the set operations.
 */
export async function executeSetOperations(workspaceId, userId, operations) {
  const response = await fetch('/api/bitmap/filter', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
      'X-Workspace-Id': workspaceId,
      'X-User-Id': userId
    },
    body: JSON.stringify({ operations })
  });

  if (!response.ok) {
    throw new Error(`Bitmap filter failed: ${response.statusText}`);
  }

  const data = await response.json();
  return data.card_ids;  // Array of UUIDs
}

/**
 * Combined query: Set operations on server, content resolution in browser.
 * This is the primary query pattern for filtered card views.
 */
export async function fetchCardsWithSetOperations(
  workspaceId,
  userId,
  setOperations = []
) {
  // Step 1: Get all cards from browser DB (content)
  const allCards = await fetchCards(workspaceId, userId);

  // Step 2: If no set operations, return all cards
  if (setOperations.length === 0) {
    return allCards;
  }

  // Step 3: Execute set operations on server (bitmaps only)
  const matchingCardIds = await executeSetOperations(
    workspaceId,
    userId,
    setOperations
  );

  // Step 4: Filter cards in browser (resolve UUIDs to content)
  const matchingCardIdSet = new Set(matchingCardIds);
  const filteredCards = allCards.filter(card =>
    matchingCardIdSet.has(card.id)
  );

  return filteredCards;
}

// Auth token helper
function getAuthToken() {
  return localStorage.getItem('auth_token') || '';
}
```

#### Task 3.2: Create Server-Side Bitmap Filter Endpoint
**Duration**: 6 hours

**File**: `apps/user/routes/bitmap_filter_api.py`

```python
"""
Server-side bitmap filter endpoint - performs set operations on bitmaps.
Returns array of card UUIDs matching the set operations.
NO content is returned - only UUIDs for browser to resolve.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Literal
import logging

router = APIRouter(prefix="/api/bitmap", tags=["bitmap_filter"])
logger = logging.getLogger(__name__)


class SetOperation(BaseModel):
    """Set operation definition."""
    type: Literal['UNION', 'INTERSECTION', 'DIFFERENCE', 'EXCLUSION']
    tag_bitmaps: list[int]  # Array of tag integer bitmaps


class BitmapFilterRequest(BaseModel):
    """Request payload for bitmap-based set operations."""
    operations: list[SetOperation]


def perform_bitmap_set_operations(
    operations: list[SetOperation],
    card_bitmaps: dict[str, tuple[int, list[int]]]
) -> set[str]:
    """
    Pure function to perform set operations on bitmaps.

    Args:
        operations: List of set operations to apply
        card_bitmaps: Dict mapping card_id → (card_bitmap, [tag_bitmaps])

    Returns:
        Set of card_ids matching all operations
    """
    # Start with all cards
    result_card_ids = set(card_bitmaps.keys())

    for op in operations:
        if op.type == 'UNION':
            # Cards that have ANY of the specified tag bitmaps
            matching = {
                card_id
                for card_id, (card_bitmap, tag_bitmaps) in card_bitmaps.items()
                if any(tag_bm in tag_bitmaps for tag_bm in op.tag_bitmaps)
            }
            result_card_ids = result_card_ids.union(matching)

        elif op.type == 'INTERSECTION':
            # Cards that have ALL of the specified tag bitmaps
            matching = {
                card_id
                for card_id, (card_bitmap, tag_bitmaps) in card_bitmaps.items()
                if all(tag_bm in tag_bitmaps for tag_bm in op.tag_bitmaps)
            }
            result_card_ids = result_card_ids.intersection(matching)

        elif op.type == 'DIFFERENCE':
            # Remove cards that have ANY of the specified tag bitmaps
            matching = {
                card_id
                for card_id, (card_bitmap, tag_bitmaps) in card_bitmaps.items()
                if any(tag_bm in tag_bitmaps for tag_bm in op.tag_bitmaps)
            }
            result_card_ids = result_card_ids.difference(matching)

        elif op.type == 'EXCLUSION':
            # Cards that have NONE of the specified tag bitmaps
            matching = {
                card_id
                for card_id, (card_bitmap, tag_bitmaps) in card_bitmaps.items()
                if not any(tag_bm in tag_bitmaps for tag_bm in op.tag_bitmaps)
            }
            result_card_ids = result_card_ids.intersection(matching)

    return result_card_ids


@router.post("/filter")
async def filter_by_bitmaps(
    request: BitmapFilterRequest,
    x_workspace_id: str = Header(...),
    x_user_id: str = Header(...)
):
    """
    Execute set operations on bitmaps and return matching card UUIDs.

    Server performs bitmap algebra, browser resolves UUIDs to actual content.
    This endpoint has NO knowledge of card names, tags, or any readable content.
    """
    try:
        from apps.shared.repositories.card_repository import get_card_db_connection

        with get_card_db_connection() as conn:
            # Fetch all card bitmaps for workspace (content-free query)
            cursor = conn.execute("""
                SELECT card_id, card_bitmap, tag_bitmaps
                FROM card_bitmaps
                WHERE workspace_id = ? AND user_id = ?
            """, (x_workspace_id, x_user_id))

            # Parse bitmap data
            card_bitmaps = {}
            for row in cursor.fetchall():
                card_id = row[0]
                card_bitmap = row[1]
                tag_bitmaps = [int(x) for x in row[2].split(',')] if row[2] else []
                card_bitmaps[card_id] = (card_bitmap, tag_bitmaps)

        # Perform set operations (pure function)
        matching_card_ids = perform_bitmap_set_operations(
            request.operations,
            card_bitmaps
        )

        logger.info(
            f"✅ Bitmap filter: {len(request.operations)} operations, "
            f"{len(matching_card_ids)}/{len(card_bitmaps)} cards match"
        )

        # Return ONLY UUIDs (no content)
        return {
            "card_ids": list(matching_card_ids),
            "total_cards": len(card_bitmaps),
            "matched_cards": len(matching_card_ids)
        }

    except Exception as e:
        logger.error(f"❌ Bitmap filter failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 4: Browser-Side Bitmap Sync (Day 6)
**Duration**: 1 day
**Risk**: Low

#### Task 4.1: Create Bitmap Sync Service
**Duration**: 4 hours

**File**: `apps/static/js/services/bitmap_sync.js`

```javascript
/**
 * Bitmap sync service - pushes bitmap updates to server.
 * Server is slave - receives bitmap updates, never mutates.
 */

/**
 * Sync card bitmap to server (after local mutation).
 */
export async function syncCardBitmap(card) {
  try {
    const response = await fetch('/api/sync/bitmaps', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        card_id: card.id,
        workspace_id: card.workspace_id,
        user_id: card.user_id,
        card_bitmap: card.card_bitmap,
        tag_bitmaps: card.tag_bitmaps  // Array of integers
      })
    });

    if (!response.ok) {
      throw new Error(`Bitmap sync failed: ${response.statusText}`);
    }

    console.log(`✅ Synced bitmap for card ${card.id}`);
    return { success: true };

  } catch (error) {
    console.error(`❌ Failed to sync bitmap for card ${card.id}:`, error);
    return { success: false, error: error.message };
  }
}

/**
 * Sync tag bitmap to server.
 */
export async function syncTagBitmap(tag) {
  try {
    const response = await fetch('/api/sync/tag-bitmaps', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        tag_id: tag.id,
        workspace_id: tag.workspace_id,
        user_id: tag.user_id,
        tag_bitmap: tag.tag_bitmap
      })
    });

    if (!response.ok) {
      throw new Error(`Tag bitmap sync failed: ${response.statusText}`);
    }

    console.log(`✅ Synced bitmap for tag ${tag.id}`);
    return { success: true };

  } catch (error) {
    console.error(`❌ Failed to sync bitmap for tag ${tag.id}:`, error);
    return { success: false, error: error.message };
  }
}

/**
 * Background sync loop - pushes dirty bitmaps periodically.
 */
let syncInterval = null;
const dirtyCards = new Set();
const dirtyTags = new Set();

export function markCardDirty(cardId) {
  dirtyCards.add(cardId);
}

export function markTagDirty(tagId) {
  dirtyTags.add(tagId);
}

export function startBitmapSyncLoop(intervalMs = 5000) {
  if (syncInterval) {
    console.warn('Bitmap sync loop already running');
    return;
  }

  syncInterval = setInterval(async () => {
    await syncDirtyBitmaps();
  }, intervalMs);

  console.log(`✅ Bitmap sync loop started (every ${intervalMs}ms)`);
}

export function stopBitmapSyncLoop() {
  if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = null;
    console.log('Bitmap sync loop stopped');
  }
}

async function syncDirtyBitmaps() {
  if (dirtyCards.size === 0 && dirtyTags.size === 0) {
    return;  // Nothing to sync
  }

  const cardIds = Array.from(dirtyCards);
  const tagIds = Array.from(dirtyTags);

  console.log(`🔄 Syncing ${cardIds.length} cards, ${tagIds.length} tags...`);

  // Fetch full card/tag data from browser DB
  // (In production, optimize to batch sync)
  for (const cardId of cardIds) {
    const card = await fetchCardById(cardId);
    if (card) {
      await syncCardBitmap(card);
      dirtyCards.delete(cardId);
    }
  }

  for (const tagId of tagIds) {
    const tag = await fetchTagById(tagId);
    if (tag) {
      await syncTagBitmap(tag);
      dirtyTags.delete(tagId);
    }
  }

  console.log(`✅ Bitmap sync complete`);
}

// Helpers
function getAuthToken() {
  return localStorage.getItem('auth_token') || '';
}

async function fetchCardById(cardId) {
  const { executeQuery } = await import('./browser_database.js');
  const result = await executeQuery(
    'SELECT * FROM cards WHERE card_id = ?',
    [cardId]
  );
  return result.success && result.rows.length > 0 ? result.rows[0] : null;
}

async function fetchTagById(tagId) {
  const { executeQuery } = await import('./browser_database.js');
  const result = await executeQuery(
    'SELECT * FROM tags WHERE tag_id = ?',
    [tagId]
  );
  return result.success && result.rows.length > 0 ? result.rows[0] : null;
}
```

#### Task 4.2: Integrate with Card Creation
**Duration**: 4 hours

Update existing card creation to sync bitmaps after local creation.

**File**: `apps/static/js/app.js` (modify existing createNewCard function)

```javascript
// Existing function at line 154-199
async function createNewCard(rowTag = null, colTag = null) {
  // ... existing tag collection logic ...

  const cardId = crypto.randomUUID();

  try {
    // Step 1: Create card in browser DB (local-first)
    const { executeQuery } = await import('./services/browser_database.js');

    const tagIdsCSV = tagIds.join(',');
    const result = await executeQuery(`
      INSERT INTO cards (card_id, name, workspace_id, user_id, tags)
      VALUES (?, ?, ?, ?, ?)
    `, [cardId, 'Untitled', workspaceId, userId, tagIdsCSV]);

    if (!result.success) {
      throw new Error(result.error);
    }

    // Step 2: Triggers auto-calculate card_bitmap (local)
    // Fetch computed bitmap
    const cardResult = await executeQuery(
      'SELECT card_bitmap, tags FROM cards WHERE card_id = ?',
      [cardId]
    );

    const card = cardResult.rows[0];

    // Step 3: Sync bitmap to server (async, non-blocking)
    const { syncCardBitmap, markCardDirty } = await import('./services/bitmap_sync.js');

    markCardDirty(cardId);  // Will sync in background

    // Or sync immediately:
    syncCardBitmap({
      id: cardId,
      workspace_id: workspaceId,
      user_id: userId,
      card_bitmap: card.card_bitmap,
      tag_bitmaps: card.tags.split(',').map(tagId => getTagBitmap(tagId))
    }).catch(err => {
      console.warn('Bitmap sync failed (will retry in background):', err);
    });

    console.log(`✅ Card created locally: ${cardId}`);

    // Re-render cards
    await renderCards();

  } catch (error) {
    console.error('Failed to create card:', error);
    alert('Failed to create card: ' + error.message);
  }
}
```

### Phase 5: Testing & Documentation (Days 7-8)
**Duration**: 2 days
**Risk**: Low

#### Task 5.1: Integration Tests
**File**: `tests/integration/browser_bitmap_integration_test.js`

```javascript
/**
 * Integration test for browser-server bitmap architecture.
 */

async function testBrowserBitmapIntegration() {
  console.log('🧪 Testing browser-server bitmap integration...');

  // Test 1: Initialize browser database
  const { initializeBrowserDatabase } = await import('../../apps/static/js/services/browser_database.js');
  const initResult = await initializeBrowserDatabase();
  assert(initResult.success, 'Failed to initialize browser database');
  console.log('✅ Browser database initialized');

  // Test 2: Create card in browser (local-first)
  const { executeQuery } = await import('../../apps/static/js/services/browser_database.js');
  const cardId = crypto.randomUUID();
  const tagIds = ['tag-uuid-1', 'tag-uuid-2'];

  const createResult = await executeQuery(`
    INSERT INTO cards (card_id, name, workspace_id, user_id, tags)
    VALUES (?, ?, ?, ?, ?)
  `, [cardId, 'Test Card', 'ws-1', 'user-1', tagIds.join(',')]);

  assert(createResult.success, 'Failed to create card locally');
  console.log('✅ Card created locally');

  // Test 3: Verify bitmap computed locally
  const bitmapResult = await executeQuery(
    'SELECT card_bitmap FROM cards WHERE card_id = ?',
    [cardId]
  );
  assert(bitmapResult.rows[0].card_bitmap > 0, 'Bitmap not computed');
  console.log(`✅ Bitmap computed: ${bitmapResult.rows[0].card_bitmap}`);

  // Test 4: Sync bitmap to server
  const { syncCardBitmap } = await import('../../apps/static/js/services/bitmap_sync.js');
  const syncResult = await syncCardBitmap({
    id: cardId,
    workspace_id: 'ws-1',
    user_id: 'user-1',
    card_bitmap: bitmapResult.rows[0].card_bitmap,
    tag_bitmaps: [11, 22]
  });
  assert(syncResult.success, 'Failed to sync bitmap');
  console.log('✅ Bitmap synced to server');

  // Test 5: Query server bitmap filter
  const { executeSetOperations } = await import('../../apps/static/js/services/query_router.js');
  const matchingIds = await executeSetOperations('ws-1', 'user-1', [
    { type: 'UNION', tag_bitmaps: [11, 22] }
  ]);
  assert(matchingIds.includes(cardId), 'Card not returned by bitmap filter');
  console.log(`✅ Server bitmap filter returned ${matchingIds.length} cards`);

  // Test 6: Verify server has NO content
  const serverCheck = await fetch('/api/bitmap/verify-no-content', {
    headers: { 'X-Workspace-Id': 'ws-1', 'X-User-Id': 'user-1' }
  });
  const serverData = await serverCheck.json();
  assert(serverData.has_content === false, 'Server has content (PRIVACY VIOLATION)');
  console.log('✅ Server verified content-free (privacy preserved)');

  console.log('🎉 All integration tests passed!');
}
```

#### Task 5.2: Documentation
**Duration**: 4 hours

**File**: `docs/architecture/turso-browser-bitmap-architecture.md`

- Browser-server separation of concerns
- Privacy guarantees (server never sees content)
- Query routing patterns (content vs bitmaps)
- Bitmap sync lifecycle
- Performance characteristics

## Architecture Compliance Checklist

✅ **Pure Functions**: All database operations as pure functions
✅ **Privacy-First**: Server has ONLY bitmaps, NO content
✅ **Local-First**: Browser is primary source of truth
✅ **Zero-Trust**: workspace_id + user_id on all operations
✅ **Minimal Bundle**: ~50KB JS + 500KB WASM (cached)
✅ **Bitmap Slave**: Server never mutates, only receives updates
✅ **Set Operations**: Server-side bitmap algebra
✅ **File Sizes**: All files <700 lines

## Performance Targets

| Operation | Target | Method |
|-----------|--------|--------|
| Browser Query (10K cards) | <10ms | WASM SQLite |
| Bitmap Sync (single card) | <50ms | POST /api/sync/bitmaps |
| Server Bitmap Filter | <100ms | In-memory bitmap ops |
| Database Init | <100ms | OPFS + WASM load (cached) |
| Card Creation (local) | <5ms | Browser DB INSERT |

## Privacy Guarantees

✅ **Server Schema Verification**:
```sql
-- These queries must return 0 rows (no content columns)
SELECT column_name FROM information_schema.columns
WHERE table_name = 'card_bitmaps'
  AND column_name LIKE '%name%' OR column_name LIKE '%description%';
-- Must return: 0 rows

SELECT column_name FROM information_schema.columns
WHERE table_name = 'tag_bitmaps'
  AND column_name = 'tag';
-- Must return: 0 rows (tag name not stored on server)
```

✅ **Network Traffic Analysis**:
- All `/api/sync/bitmaps` requests: Only integers and UUIDs
- All `/api/bitmap/filter` responses: Only UUID arrays
- No readable strings in bitmap sync payloads

## Success Criteria

✅ Browser database initialized (OPFS, <100ms)
✅ Card creation works locally (local-first)
✅ Bitmaps auto-computed by triggers
✅ Bitmaps sync to server successfully
✅ Server bitmap filter returns correct UUIDs
✅ Browser resolves UUIDs to content
✅ Server has ZERO content (verified by schema + traffic analysis)
✅ <10ms local queries (10K cards)
✅ <100ms server bitmap operations

## Implementation Summary

### Three-Mode Architecture

| Mode | Status | Implementation | Duration |
|------|--------|----------------|----------|
| **Dev Mode** | 🔧 Migrate | Switch to Turso CLI (`turso dev`) | 0.5 days |
| **Normal Mode** | 🔧 Config only | Add Turso cloud connection | 1 day |
| **Privacy Mode** | ❌ Build required | Full browser WASM + bitmap slave | 7-9 days |

### Privacy Mode Implementation (Primary Focus)

**Total Duration**: 7-9 days

**Phases**:
0. Mode Infrastructure (1 day) - Mode selection system
1. Browser Database Foundation (2 days) - Turso WASM in browser
2. Server Bitmap Slave Schema (1 day) - Bitmap-only tables
3. Query Routing & Integration (2 days) - Content vs bitmap routing
4. Browser-Side Bitmap Sync (1 day) - Background bitmap sync
5. Testing & Documentation (2 days) - Privacy verification

**Key Deliverables**:
- Mode selection system (dev/normal/privacy)
- Browser WASM database (Privacy Mode - local-first, full content)
- Server bitmap-only tables (Privacy Mode - 2 tables, zero content)
- Query router (Privacy Mode - content → browser, sets → server)
- Bitmap sync service (Privacy Mode - browser → server, slave pattern)
- Integration tests (Privacy Mode - privacy verification)
- Turso cloud connection (Normal Mode - standard production)

### Deployment Strategy

**Phase 1: Dev Mode** (Already Complete)
- Local development continues as-is
- No changes required

**Phase 2: Normal Mode** (1 day)
- Add Turso cloud connection support
- Default mode for production users
- Standard subscription tier

**Phase 3: Privacy Mode** (7-9 days)
- Build browser WASM + bitmap slave architecture
- Premium subscription feature
- Maximum privacy guarantee

## Next Steps

1. ✅ Review and approve corrected plan (v2.0 - THREE MODES)
2. Decide implementation priority:
   - Option A: Normal Mode first (1 day), then Privacy Mode (7-9 days)
   - Option B: Privacy Mode only (7-9 days), Normal Mode later
3. Set up development environment with WASM headers (for Privacy Mode)
4. Install `@tursodatabase/database-wasm` NPM package (for Privacy Mode)
5. Begin Phase 0: Mode Infrastructure (mode selection system)
6. Configure Turso cloud credentials (for Normal Mode)

---

**Status**: Ready for implementation approval
**Previous Version**: v1.0 (DEPRECATED - incorrect architecture, single mode only)
**This Version**: v2.0 (CORRECTED - three-mode architecture with privacy-focused bitmap slave)

**Key Architectural Decision**: Privacy Mode is a **premium subscription feature** that provides maximum privacy by keeping all content in browser and syncing only integer bitmaps to server.
