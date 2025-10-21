# Turso DB in Browser Integration Plan - Privacy-First Architecture

**STATUS**: SUPERSEDED
**SUPERSEDED BY**: docs/implementation/030-2025-10-08-Turso-Browser-Integration-Plan-v2.md
**SUPERSEDED DATE**: 2025-10-08
**REASON**: Version 2 created with three operational modes architecture (Privacy/Hybrid/Cloud) instead of single-mode approach

## Document Metadata
**Document Version**: 1.0
**Date**: 2025-10-08
**Status**: ARCHITECTURE DESIGN - SUPERSEDED
**Estimated Duration**: 8-10 days
**Reference**: Zero-Trust UUID Architecture + Multi-Tier Database Architecture

## Executive Summary

Integrate **Turso DB in Browser** with **Turso Sync** to enable true offline-first, privacy-preserving database capabilities in MultiCardz. This implementation creates three operational modes:

1. **Privacy Mode** (Local-Only): 100% client-side WASM database, zero server communication
2. **Hybrid Mode** (Sync): Local WASM database with selective cloud sync
3. **Cloud Mode** (Standard): Server-side Turso with browser as thin client

**Key Benefits**:
- ✅ True offline-first operation (works with zero network)
- ✅ Sub-millisecond local queries (WASM SQLite performance)
- ✅ Privacy-preserving (data never leaves device in Privacy Mode)
- ✅ Seamless cross-device sync (Hybrid Mode)
- ✅ Zero server load for read operations (all queries local)
- ✅ Patent-compliant set operations (RoaringBitmap in WASM)

## Current State Analysis

### Existing Architecture Strengths
✅ Zero-Trust UUID isolation (workspace_id, user_id on all tables)
✅ Auto-migration middleware (can work with browser DB)
✅ Pure function architecture (WASM-compatible)
✅ RoaringBitmap set operations (performance-critical)
✅ Multi-tier separation (auth, data, preferences)

### Integration Gaps
❌ No browser-based database (relies on server)
❌ No offline capability (requires network)
❌ No privacy mode (all data touches server)
❌ No sync infrastructure (no embedded replica pattern)
❌ Server handles all queries (scalability bottleneck)

## Success Metrics

| Metric | Target | Validation Method |
|--------|--------|------------------|
| Offline Operation | 100% functional | Disconnect test |
| Local Query Speed | <10ms for 10K cards | Performance benchmark |
| Sync Latency | <500ms for 100 changes | Sync test |
| Privacy Guarantee | Zero network in Privacy Mode | Traffic analysis |
| Storage Capacity | 50MB+ in browser | OPFS capacity test |
| Cross-Browser Support | Chrome, Firefox, Safari | Compatibility matrix |

## Technical Architecture

### Three Operational Modes

#### Mode 1: Privacy Mode (Local-Only)
```
┌─────────────────────────────────────┐
│         Browser (Client)            │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐  │
│  │  Turso WASM Database          │  │
│  │  (@tursodatabase/database-wasm)│  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Origin Private File Sys │  │  │
│  │  │ (OPFS) - 50MB+ Storage  │  │  │
│  │  └─────────────────────────┘  │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ RoaringBitmap WASM      │  │  │
│  │  │ (Set Operations)        │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │  JavaScript Application       │  │
│  │  - Pure function queries      │  │
│  │  - Local set operations       │  │
│  │  - No network calls           │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ▼
    NO NETWORK
```

**Characteristics**:
- 100% local operation
- No authentication required (local-only access)
- Data encrypted in OPFS (browser-level encryption)
- Auto-migration works locally
- Perfect for air-gapped environments

#### Mode 2: Hybrid Mode (Sync)
```
┌─────────────────────────────────────┐
│         Browser (Client)            │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐  │
│  │  Turso WASM Database          │  │
│  │  + Turso Sync                 │  │
│  │  (@tursodatabase/sync-wasm)   │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Local Database (Full)   │  │  │
│  │  └─────────────────────────┘  │  │
│  │           ↕ Sync              │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         ▼ push()/pull()
┌─────────────────────────────────────┐
│      Turso Cloud (Remote)           │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐  │
│  │  Remote Database              │  │
│  │  (Source of Truth)            │  │
│  │  - Full dataset               │  │
│  │  - Conflict resolution        │  │
│  │  - Multi-device sync          │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Sync Operations**:
- `connect(url, token)` - Establish sync connection
- `push()` - Send local changes as logical mutations
- `pull()` - Receive remote changes as physical pages
- `checkpoint()` - Optimize WAL and finalize sync

**Conflict Resolution**:
- Default: Last-Push-Wins at row level
- Custom: Transform hook for business logic
- Zero-Trust: workspace_id + user_id prevent cross-contamination

#### Mode 3: Cloud Mode (Standard)
```
┌─────────────────────────────────────┐
│         Browser (Client)            │
├─────────────────────────────────────┤
│  Thin Client - REST API calls only  │
│  No local database                   │
└─────────────────────────────────────┘
         │
         ▼ HTTPS API
┌─────────────────────────────────────┐
│      FastAPI Backend                │
├─────────────────────────────────────┤
│  ┌───────────────────────────────┐  │
│  │  Turso Cloud Database         │  │
│  │  (Server-Side Queries)        │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Characteristics**:
- Current architecture (backward compatible)
- Server handles all queries
- Best for untrusted clients
- Simplest deployment

## Implementation Phases

### Phase 1: Browser Database Foundation (Days 1-2)
**Duration**: 2 days
**Risk**: Medium (new technology)

#### Task 1.1: Install and Configure Turso WASM
**Duration**: 4 hours

**NPM Packages**:
```bash
npm install @tursodatabase/database-wasm
npm install @tursodatabase/sync-wasm
```

**Build Configuration** (Vite/Webpack):
```javascript
// vite.config.js
export default {
  optimizeDeps: {
    exclude: ['@tursodatabase/database-wasm']
  },
  server: {
    headers: {
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin'
    }
  }
}
```

**Required HTTP Headers** (for SharedArrayBuffer):
```
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
```

#### Task 1.2: Create Browser Database Service
**Duration**: 4 hours

**File**: `apps/static/js/services/browser_database.js`

```javascript
// Pure function service for browser database operations
import { connect } from '@tursodatabase/database-wasm';

// Module-level database connection (singleton pattern)
let dbConnection = null;
let dbMode = null; // 'privacy', 'hybrid', 'cloud'

/**
 * Initialize browser database with mode selection.
 * Pure function with explicit side effects (DB initialization).
 */
export async function initializeBrowserDatabase(mode, config = {}) {
  dbMode = mode;

  if (mode === 'cloud') {
    // No local DB needed
    dbConnection = null;
    return { success: true, mode: 'cloud' };
  }

  try {
    if (mode === 'privacy') {
      // Local-only database in OPFS
      dbConnection = await connect('multicardz_local.db');
      return { success: true, mode: 'privacy', storage: 'opfs' };
    }

    if (mode === 'hybrid') {
      // Local database with sync capability
      const { connect: syncConnect } = await import('@tursodatabase/sync-wasm');

      dbConnection = await syncConnect('multicardz_sync.db', {
        remoteUrl: config.remoteUrl,
        authToken: config.authToken,
        syncInterval: config.syncInterval || 5000 // 5 seconds
      });

      return { success: true, mode: 'hybrid', storage: 'opfs', sync: 'enabled' };
    }

    throw new Error(`Unknown mode: ${mode}`);

  } catch (error) {
    console.error('Failed to initialize browser database:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Execute query on browser database.
 * Pure function with explicit DB side effect.
 */
export async function executeQuery(sql, params = []) {
  if (dbMode === 'cloud') {
    throw new Error('Cloud mode uses server-side queries');
  }

  if (!dbConnection) {
    throw new Error('Database not initialized');
  }

  try {
    const result = await dbConnection.execute(sql, params);
    return { success: true, rows: result.rows, rowsAffected: result.rowsAffected };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Execute multiple statements in transaction.
 */
export async function executeTransaction(statements) {
  if (!dbConnection) {
    throw new Error('Database not initialized');
  }

  try {
    await dbConnection.execute('BEGIN TRANSACTION');

    for (const { sql, params } of statements) {
      await dbConnection.execute(sql, params);
    }

    await dbConnection.execute('COMMIT');
    return { success: true };

  } catch (error) {
    await dbConnection.execute('ROLLBACK');
    return { success: false, error: error.message };
  }
}

/**
 * Sync operations (Hybrid mode only).
 */
export async function syncDatabase(operation) {
  if (dbMode !== 'hybrid') {
    return { success: false, error: 'Sync only available in hybrid mode' };
  }

  try {
    switch (operation) {
      case 'push':
        await dbConnection.push();
        return { success: true, operation: 'push' };

      case 'pull':
        await dbConnection.pull();
        return { success: true, operation: 'pull' };

      case 'checkpoint':
        await dbConnection.checkpoint();
        return { success: true, operation: 'checkpoint' };

      case 'full':
        await dbConnection.push();
        await dbConnection.pull();
        await dbConnection.checkpoint();
        return { success: true, operation: 'full-sync' };

      default:
        throw new Error(`Unknown sync operation: ${operation}`);
    }
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
      mode: dbMode,
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

Auto-migration middleware already exists - just need to make it work with browser DB:

**File**: `apps/static/js/services/browser_migration.js`

```javascript
// Adapt server-side auto-migration for browser environment
import { executeQuery, executeTransaction } from './browser_database.js';

// Migration registry (same as server-side)
const MIGRATIONS = [
  { version: 1, file: '001_zero_trust_schema.sql' },
  { version: 2, file: '002_add_bitmap_sequences.sql' }
];

export async function applyMigrationIfNeeded(error) {
  const errorMsg = error.message.toLowerCase();

  // Detect schema error (same patterns as server)
  let migration = null;

  if (errorMsg.includes('no such table: cards')) {
    migration = MIGRATIONS[0];
  } else if (errorMsg.includes('no such table: bitmap_sequences')) {
    migration = MIGRATIONS[1];
  }

  if (!migration) {
    return { applied: false, error: 'No migration available' };
  }

  // Fetch and apply migration SQL
  try {
    const response = await fetch(`/migrations/${migration.file}`);
    const sql = await response.text();

    await executeTransaction([{ sql, params: [] }]);

    return { applied: true, version: migration.version };
  } catch (migrationError) {
    return { applied: false, error: migrationError.message };
  }
}
```

### Phase 2: Mode Selection & Initialization (Day 3)
**Duration**: 1 day
**Risk**: Low

#### Task 2.1: Create Mode Selection UI
**File**: `apps/static/templates/mode_selector.html`

```html
<!-- Privacy Mode Selector -->
<div id="database-mode-selector" class="mode-selector">
  <h3>Choose Your Privacy Level</h3>

  <div class="mode-option" data-mode="privacy">
    <h4>🔒 Privacy Mode</h4>
    <p>100% local, zero network. Your data never leaves your device.</p>
    <ul>
      <li>✅ Works offline</li>
      <li>✅ Maximum privacy</li>
      <li>❌ No cross-device sync</li>
    </ul>
  </div>

  <div class="mode-option" data-mode="hybrid">
    <h4>🔄 Hybrid Mode</h4>
    <p>Local-first with optional cloud sync for multiple devices.</p>
    <ul>
      <li>✅ Works offline</li>
      <li>✅ Cross-device sync</li>
      <li>⚠️ Data syncs to cloud</li>
    </ul>
  </div>

  <div class="mode-option" data-mode="cloud">
    <h4>☁️ Cloud Mode</h4>
    <p>Traditional cloud-based storage. Requires internet connection.</p>
    <ul>
      <li>❌ Requires network</li>
      <li>✅ Cross-device sync</li>
      <li>✅ Managed backups</li>
    </ul>
  </div>
</div>
```

#### Task 2.2: Mode Initialization Logic
**File**: `apps/static/js/mode_initializer.js`

```javascript
import { initializeBrowserDatabase } from './services/browser_database.js';

export async function initializeApplicationMode() {
  // Check for saved preference
  const savedMode = localStorage.getItem('db_mode') || 'privacy';

  // Show mode selector on first run
  if (!localStorage.getItem('mode_selected')) {
    return await showModeSelector();
  }

  // Initialize with saved mode
  return await initializeBrowserDatabase(savedMode, await getModeConfig(savedMode));
}

async function showModeSelector() {
  // Display mode selection UI
  // Wait for user choice
  // Return selected mode
}

async function getModeConfig(mode) {
  if (mode === 'hybrid') {
    // Get Turso sync credentials
    const response = await fetch('/api/turso/credentials', {
      headers: { 'Authorization': `Bearer ${getAuthToken()}` }
    });
    return await response.json();
  }
  return {};
}
```

### Phase 3: Local Query Routing (Days 4-5)
**Duration**: 2 days
**Risk**: Medium

#### Task 3.1: Create Query Router
**File**: `apps/static/js/services/query_router.js`

```javascript
/**
 * Route queries to appropriate database (local or remote).
 * Pure function that selects execution strategy.
 */
export function routeQuery(query, params, mode) {
  if (mode === 'privacy' || mode === 'hybrid') {
    // Execute locally in browser
    return executeQueryLocally(query, params);
  }

  if (mode === 'cloud') {
    // Send to server API
    return executeQueryOnServer(query, params);
  }

  throw new Error(`Unknown mode: ${mode}`);
}

async function executeQueryLocally(query, params) {
  const { executeQuery } = await import('./browser_database.js');
  return await executeQuery(query, params);
}

async function executeQueryOnServer(query, params) {
  const response = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, params })
  });
  return await response.json();
}
```

#### Task 3.2: Integrate with Existing Card Operations
**File**: `apps/static/js/card_operations.js`

```javascript
import { routeQuery } from './services/query_router.js';

/**
 * Fetch cards with local or remote execution.
 * Pure function with explicit DB dependency.
 */
export async function fetchCards(workspaceId, userId, filterTags = []) {
  const mode = localStorage.getItem('db_mode');

  // Build query (same for local and remote)
  const query = `
    SELECT card_id, name, tags, created, modified
    FROM cards
    WHERE workspace_id = ?
      AND user_id = ?
      AND deleted IS NULL
  `;

  const params = [workspaceId, userId];

  // Route to appropriate execution context
  const result = await routeQuery(query, params, mode);

  return result.rows.map(row => ({
    id: row.card_id,
    name: row.name,
    tags: row.tags ? row.tags.split(',') : [],
    created: row.created,
    modified: row.modified
  }));
}
```

### Phase 4: Sync Implementation (Days 6-7)
**Duration**: 2 days
**Risk**: High

#### Task 4.1: Background Sync Loop
**File**: `apps/static/js/services/sync_manager.js`

```javascript
/**
 * Background sync manager for hybrid mode.
 * Continuously syncs local changes with cloud.
 */
let syncInterval = null;
let lastSyncTime = null;

export function startSyncLoop(intervalMs = 5000) {
  if (syncInterval) {
    console.warn('Sync loop already running');
    return;
  }

  syncInterval = setInterval(async () => {
    await performSync();
  }, intervalMs);

  console.log(`Sync loop started (every ${intervalMs}ms)`);
}

export function stopSyncLoop() {
  if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = null;
    console.log('Sync loop stopped');
  }
}

async function performSync() {
  const { syncDatabase } = await import('./browser_database.js');

  try {
    const startTime = performance.now();

    // Push local changes
    await syncDatabase('push');

    // Pull remote changes
    await syncDatabase('pull');

    // Checkpoint to optimize WAL
    await syncDatabase('checkpoint');

    const duration = performance.now() - startTime;
    lastSyncTime = new Date();

    console.log(`Sync completed in ${duration.toFixed(2)}ms`);

    // Dispatch event for UI updates
    window.dispatchEvent(new CustomEvent('turso-sync-complete', {
      detail: { duration, timestamp: lastSyncTime }
    }));

  } catch (error) {
    console.error('Sync failed:', error);

    window.dispatchEvent(new CustomEvent('turso-sync-failed', {
      detail: { error: error.message }
    }));
  }
}

export function getSyncStatus() {
  return {
    running: syncInterval !== null,
    lastSync: lastSyncTime
  };
}
```

#### Task 4.2: Conflict Resolution
**File**: `apps/static/js/services/conflict_resolver.js`

```javascript
/**
 * Custom conflict resolution for Turso Sync.
 * Default: Last-Push-Wins at row level.
 * Custom: Business logic for specific tables.
 */
export function configureConflictResolution(db) {
  // Transform hook for advanced conflict handling
  db.setTransformHook((mutations) => {
    return mutations.map(mutation => {
      // Apply business rules
      if (mutation.table === 'cards') {
        return resolveCardConflict(mutation);
      }

      if (mutation.table === 'tags') {
        return resolveTagConflict(mutation);
      }

      // Default: accept as-is (Last-Push-Wins)
      return mutation;
    });
  });
}

function resolveCardConflict(mutation) {
  // Custom logic: preserve local changes if modified within last minute
  const now = Date.now();
  const localModified = new Date(mutation.local.modified).getTime();

  if (now - localModified < 60000) {
    // Keep local version (within 1 minute of modification)
    return { ...mutation, action: 'keep-local' };
  }

  // Accept remote version
  return { ...mutation, action: 'keep-remote' };
}

function resolveTagConflict(mutation) {
  // Tags use Last-Push-Wins (default)
  return mutation;
}
```

### Phase 5: Testing & Optimization (Days 8-9)
**Duration**: 2 days
**Risk**: Low

#### Task 5.1: Performance Benchmarks
**File**: `tests/performance/browser_db_benchmark.js`

```javascript
// Benchmark local query performance
export async function benchmarkLocalQueries() {
  const iterations = 1000;
  const start = performance.now();

  for (let i = 0; i < iterations; i++) {
    await executeQuery('SELECT * FROM cards WHERE workspace_id = ?', ['test-ws']);
  }

  const duration = performance.now() - start;
  const avgMs = duration / iterations;

  console.log(`Average query time: ${avgMs.toFixed(3)}ms`);
  assert(avgMs < 10, `Query too slow: ${avgMs}ms`);
}
```

#### Task 5.2: Offline Operation Test
**File**: `tests/integration/offline_test.js`

```javascript
// Test complete offline operation
export async function testOfflineMode() {
  // Initialize in privacy mode
  await initializeBrowserDatabase('privacy');

  // Disconnect network (manual test)
  console.log('❌ Disconnect network now...');
  await sleep(5000);

  // Perform operations
  const result = await fetchCards('test-ws', 'test-user');
  assert(result.length > 0, 'Failed to fetch cards offline');

  // Create new card
  const newCard = await createCard({
    workspace_id: 'test-ws',
    user_id: 'test-user',
    name: 'Offline Card'
  });
  assert(newCard.id, 'Failed to create card offline');

  console.log('✅ Offline mode working perfectly');
}
```

### Phase 6: Documentation & Deployment (Day 10)
**Duration**: 1 day
**Risk**: Low

#### Task 6.1: User Documentation
- Privacy mode benefits and limitations
- Sync setup instructions
- Troubleshooting guide

#### Task 6.2: Developer Documentation
- Architecture decisions
- Browser compatibility matrix
- Performance characteristics

## Architecture Compliance Checklist

✅ **Pure Functions**: All database operations as pure functions
✅ **No Classes**: Only functional services (except middleware wrapper)
✅ **Zero-Trust**: workspace_id + user_id on all operations
✅ **Event-Sourcing**: Sync operations logged for audit trail
✅ **Auto-Migration**: Works seamlessly with browser DB
✅ **File Sizes**: All files <700 lines

## Risk Mitigation

### High Risk: Browser Compatibility
**Risk**: SharedArrayBuffer requires COOP/COEP headers
**Mitigation**:
- Test across Chrome, Firefox, Safari
- Provide fallback mode without SharedArrayBuffer
- Document header requirements clearly

### Medium Risk: Storage Limits
**Risk**: OPFS may have browser-specific limits
**Mitigation**:
- Test with 50MB+ datasets
- Implement storage quota monitoring
- Provide warnings before hitting limits

### Medium Risk: Sync Conflicts
**Risk**: Complex conflict resolution needed
**Mitigation**:
- Start with Last-Push-Wins (simple)
- Add custom logic incrementally
- Provide manual conflict resolution UI

## Performance Targets

| Operation | Target | Method |
|-----------|--------|--------|
| Local Query (10K cards) | <10ms | WASM SQLite |
| Set Operation (intersection) | <5ms | RoaringBitmap WASM |
| Sync Push (100 changes) | <500ms | Logical mutations |
| Sync Pull (100 changes) | <300ms | Physical pages |
| Database Init | <2000ms | OPFS + WASM load |

## Deployment Strategy

### Phase 1: Alpha (Privacy Mode Only)
- Limited release to test users
- Local-only operation
- Gather feedback on performance

### Phase 2: Beta (Add Hybrid Mode)
- Enable Turso Sync
- Test cross-device scenarios
- Monitor sync performance

### Phase 3: Production
- All three modes available
- Default: Privacy Mode
- Full documentation

## Success Criteria

✅ Works offline (100% functionality)
✅ <10ms local queries (10K cards)
✅ <500ms sync latency
✅ Zero network in Privacy Mode
✅ Cross-browser compatible
✅ Auto-migration working
✅ Event-sourcing integrated

## Technical References

- Turso Browser Announcement: https://turso.tech/blog/introducing-turso-in-the-browser
- Turso Sync Documentation: https://turso.tech/blog/introducing-databases-anywhere-with-turso-sync
- libSQL WASM Experimental: https://github.com/tursodatabase/libsql-wasm-experimental
- Turso Database GitHub: https://github.com/tursodatabase

## Next Steps

1. Review and approve plan
2. Set up development environment with WASM tooling
3. Install NPM packages
4. Begin Phase 1 implementation
5. Create test environment with proper headers

---

**Status**: Ready for implementation approval
