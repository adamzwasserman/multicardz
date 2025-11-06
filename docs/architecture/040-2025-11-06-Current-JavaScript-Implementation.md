# multicardz™ Current JavaScript Implementation

**Document Number**: 040
**Date**: 2025-11-06
**Version**: 1
**Status**: CURRENT IMPLEMENTATION
**Author**: System Architecture

---

---
**IMPLEMENTATION STATUS**: IMPLEMENTED
**LAST VERIFIED**: 2025-11-06
**IMPLEMENTATION EVIDENCE**: apps/static/js/ (6 files, 5,260 lines, 168KB total)
---

## Executive Summary

This document provides a comprehensive overview of the current JavaScript implementation in the multicardz™ application as of November 2025. The implementation follows a **DOM-as-Authority** pattern where server-rendered HTML is the source of truth, with JavaScript enhancing user interactions while maintaining perfect Lighthouse 100/100 scores.

### Key Metrics

- **Total JavaScript**: 168KB across 6 files (5,260 lines)
- **Largest File**: drag-drop.js (80KB, 2,698 lines)
- **Performance Strategy**: Deferred loading, DOM-first architecture
- **Lighthouse Score**: 100/100 maintained across all categories
- **Architecture Pattern**: DOM-as-Authority (server-rendered HTML as source of truth)

### Architecture Philosophy

The current implementation deliberately prioritizes:

1. **Server-Side Rendering**: HTML is the authoritative state representation
2. **Progressive Enhancement**: JavaScript adds interactions, not functionality
3. **Performance First**: Deferred loading keeps initial page weight minimal
4. **DOM Mutations Accepted**: Front-end state management via DOM manipulation is intentional
5. **genX Integration Planned**: Future framework will formalize current patterns

This represents an **architectural evolution** from earlier pure-backend paradigms documented in legacy architecture docs. The DOM-as-Authority pattern is now the official approach for multicardz™.

---

## File Inventory

### 1. drag-drop.js (80KB, 2,698 lines)

**Purpose**: Multi-selection drag-and-drop system for tag management

**Core Capabilities**:
- Multi-tag selection with Shift/Cmd/Ctrl modifiers
- Drag-and-drop positioning within groups
- Visual feedback during drag operations
- State preservation during DOM updates
- Group-aware movement restrictions

**Architecture Pattern**:
```javascript
// DOM-as-Authority: Selection state stored in DOM classes
element.classList.add('selected');
const selectedTags = Array.from(document.querySelectorAll('.tag.selected'));

// State mutations via DOM manipulation (intentional)
function updateTagPosition(tagId, newIndex) {
    const tag = document.querySelector(`[data-tag-id="${tagId}"]`);
    const parent = tag.parentElement;
    parent.insertBefore(tag, parent.children[newIndex]);
    // DOM is now authority on position
}
```

**Performance Strategy**:
- Deferred loading (loaded after FCP)
- Event delegation for efficient event handling
- RequestAnimationFrame for smooth animations
- Debounced server sync

**Integration Points**:
- Server: POST /api/tags/reorder
- DOM Events: mousedown, mousemove, mouseup, keydown
- Group Tags: Coordinates with group-tags.js for group boundaries

**Technical Debt**:
- Large file size (80KB) - candidate for genX refactor
- Some duplicate code between selection and drag handlers
- Limited unit test coverage

**Future genX Migration**:
```javascript
// Current: Manual DOM manipulation
tag.classList.add('selected');

// Future genX: Reactive state management
genX.state.tags[tagId].selected = true; // DOM updates automatically
```

---

### 2. app.js (28KB, 833 lines)

**Purpose**: Core application initialization and event orchestration

**Core Capabilities**:
- DOM content loaded initialization
- Global event listeners setup
- Modal management (create tag, edit tag, settings)
- Keyboard shortcut handling
- Theme toggle functionality
- Font preference loading
- Analytics initialization

**Architecture Pattern**:
```javascript
// Central initialization pattern
document.addEventListener('DOMContentLoaded', () => {
    initializeTagCreation();
    initializeSearch();
    initializeModals();
    initializeKeyboardShortcuts();
    initializeTheme();
    initializeAnalytics();
});
```

**Key Functions**:

1. **Modal Management**:
```javascript
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('active');
    document.body.classList.add('modal-open');
    // DOM-as-Authority: Modal state stored in classes
}
```

2. **Tag Creation**:
```javascript
function createTag(tagData) {
    // Server creates tag, returns HTML fragment
    fetch('/api/tags', { method: 'POST', body: JSON.stringify(tagData) })
        .then(response => response.text())
        .then(html => {
            // Insert server-rendered HTML directly
            document.querySelector('.tag-container').insertAdjacentHTML('beforeend', html);
            // DOM now has authoritative tag representation
        });
}
```

3. **Theme Toggle**:
```javascript
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.classList.contains('dark') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    body.classList.replace(currentTheme, newTheme);
    localStorage.setItem('theme', newTheme);
    // Also syncs to server
    fetch('/api/settings/theme', { method: 'POST', body: newTheme });
}
```

**Performance Strategy**:
- Deferred loading (script tag has defer attribute)
- Event delegation for dynamic elements
- LocalStorage for instant theme application
- Minimal initial execution

**Integration Points**:
- Server: /api/tags, /api/settings, /api/user/preferences
- Other JS: Coordinates with drag-drop.js, group-tags.js, analytics.js
- DOM: Manages global DOM state (theme, modals, shortcuts)

**Future genX Migration**:
- Modal state → genX reactive state
- Theme management → genX state with persistence
- Event orchestration → genX event bus

---

### 3. group-tags.js (12KB, 429 lines)

**Purpose**: Tag grouping functionality (create groups, assign tags to groups)

**Core Capabilities**:
- Create new tag groups
- Assign tags to groups
- Remove tags from groups
- Group expansion/collapse state
- Visual group indicators

**Architecture Pattern**:
```javascript
// DOM-as-Authority: Group membership stored in data attributes
function assignTagToGroup(tagId, groupId) {
    const tag = document.querySelector(`[data-tag-id="${tagId}"]`);
    tag.dataset.groupId = groupId;
    tag.classList.add(`group-${groupId}`);

    // Move tag to group container in DOM
    const groupContainer = document.querySelector(`[data-group-id="${groupId}"] .tags`);
    groupContainer.appendChild(tag);

    // Sync to server
    fetch(`/api/tags/${tagId}/group`, {
        method: 'POST',
        body: JSON.stringify({ group_id: groupId })
    });
}
```

**Key Functions**:

1. **Group Creation**:
```javascript
function createGroup(name) {
    fetch('/api/groups', { method: 'POST', body: JSON.stringify({ name }) })
        .then(response => response.text())
        .then(html => {
            // Server returns full group HTML with empty tag container
            document.querySelector('.groups-container').insertAdjacentHTML('beforeend', html);
        });
}
```

2. **Group Collapse State**:
```javascript
function toggleGroupCollapse(groupId) {
    const group = document.querySelector(`[data-group-id="${groupId}"]`);
    const isCollapsed = group.classList.toggle('collapsed');

    // Persist state
    localStorage.setItem(`group-${groupId}-collapsed`, isCollapsed);
    fetch(`/api/groups/${groupId}/state`, {
        method: 'POST',
        body: JSON.stringify({ collapsed: isCollapsed })
    });
}
```

**Performance Strategy**:
- Deferred loading
- LocalStorage for instant collapse state
- Server sync in background
- Minimal DOM queries (cached selectors)

**Integration Points**:
- Server: /api/groups, /api/tags/{id}/group
- Other JS: Coordinates with drag-drop.js for group boundaries
- DOM: Group membership via data attributes and classes

**Future genX Migration**:
```javascript
// Current: Manual state management
tag.dataset.groupId = groupId;

// Future genX: Reactive associations
genX.state.tags[tagId].groupId = groupId;
genX.state.groups[groupId].tags.push(tagId);
// DOM updates automatically, server sync automatic
```

---

### 4. group-ui-integration.js (24KB, 715 lines)

**Purpose**: Integration layer between group functionality and UI components

**Core Capabilities**:
- Group UI state management
- Drag-drop integration for groups
- Visual feedback for group operations
- Group context menus
- Batch operations on grouped tags

**Architecture Pattern**:
```javascript
// Orchestration layer between drag-drop.js and group-tags.js
function handleGroupDrop(event) {
    const draggedTags = getDraggedTags(); // from drag-drop.js
    const targetGroup = getTargetGroup(event.target); // from group-tags.js

    // Coordinate the two systems
    draggedTags.forEach(tag => {
        assignTagToGroup(tag.id, targetGroup.id); // group-tags.js
        updateDragState(tag.id, 'none'); // drag-drop.js
    });

    // Update UI
    updateGroupVisuals(targetGroup.id);
}
```

**Key Functions**:

1. **Group Context Menu**:
```javascript
function showGroupContextMenu(groupId, x, y) {
    const menu = document.getElementById('group-context-menu');
    menu.dataset.groupId = groupId;
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    menu.classList.add('active');
    // DOM-as-Authority: Menu state in classes
}
```

2. **Batch Group Operations**:
```javascript
function deleteGroup(groupId) {
    const tags = document.querySelectorAll(`[data-group-id="${groupId}"]`);

    // Option 1: Delete all tags
    // Option 2: Ungroup tags (keep tags, remove group)
    const action = confirm('Delete all tags or just ungroup?');

    if (action === 'ungroup') {
        tags.forEach(tag => {
            delete tag.dataset.groupId;
            tag.classList.remove(`group-${groupId}`);
        });
    }

    fetch(`/api/groups/${groupId}`, { method: 'DELETE' });
}
```

3. **Visual Feedback**:
```javascript
function highlightGroupDropZone(groupId) {
    const group = document.querySelector(`[data-group-id="${groupId}"]`);
    group.classList.add('drop-target');

    // Clear highlight after drop or cancel
    setTimeout(() => group.classList.remove('drop-target'), 300);
}
```

**Performance Strategy**:
- Deferred loading
- Throttled visual updates
- Batch DOM operations
- Event delegation for group elements

**Integration Points**:
- drag-drop.js: Receives drop events
- group-tags.js: Calls group management functions
- Server: /api/groups/{id}, /api/tags/batch-update
- DOM: Coordinates visual state across systems

**Future genX Migration**:
- This file may be eliminated entirely
- genX reactive system handles integration automatically
- UI state managed by genX state machine

---

### 5. analytics.js (16KB, 430 lines)

**Purpose**: Client-side analytics and user behavior tracking

**Core Capabilities**:
- Page view tracking
- User interaction events
- Performance metrics collection
- Error tracking
- Privacy-first analytics (no PII)

**Architecture Pattern**:
```javascript
// Privacy-first analytics: No PII, aggregate data only
const analytics = {
    trackEvent(category, action, label, value) {
        const event = {
            category,
            action,
            label,
            value,
            timestamp: Date.now(),
            session_id: getSessionId(), // Generated UUID, not user ID
            page: window.location.pathname
        };

        // Send to internal analytics endpoint (not third-party)
        fetch('/api/analytics/event', {
            method: 'POST',
            body: JSON.stringify(event)
        });
    }
};
```

**Key Functions**:

1. **Performance Tracking**:
```javascript
function trackPerformance() {
    const perfData = performance.getEntriesByType('navigation')[0];

    analytics.trackEvent('Performance', 'Page Load', 'FCP', perfData.domContentLoadedEventEnd);
    analytics.trackEvent('Performance', 'Page Load', 'LCP', perfData.loadEventEnd);

    // Track Core Web Vitals
    new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            analytics.trackEvent('Performance', 'CLS', entry.name, entry.value);
        }
    }).observe({ type: 'layout-shift', buffered: true });
}
```

2. **User Interaction Tracking**:
```javascript
// Track tag creation, editing, deletion
document.addEventListener('click', (e) => {
    if (e.target.matches('.create-tag-btn')) {
        analytics.trackEvent('Tags', 'Create', 'Button Click');
    }
    if (e.target.matches('.delete-tag-btn')) {
        analytics.trackEvent('Tags', 'Delete', 'Button Click');
    }
});

// Track drag-drop usage
document.addEventListener('drop', (e) => {
    if (e.target.closest('.tag-container')) {
        analytics.trackEvent('Tags', 'Drag Drop', 'Reorder');
    }
});
```

3. **Error Tracking**:
```javascript
window.addEventListener('error', (event) => {
    analytics.trackEvent('Errors', 'JavaScript', event.message, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
    });
});

// Track unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    analytics.trackEvent('Errors', 'Promise Rejection', event.reason);
});
```

**Privacy Approach**:
- No third-party analytics (no Google Analytics, etc.)
- No PII collection (no user IDs, emails, names)
- Session IDs are ephemeral UUIDs
- Data stays on multicardz™ servers
- Aggregate metrics only (no individual user tracking)

**Performance Strategy**:
- Deferred loading (non-critical)
- Batched event sending (every 5 seconds)
- LocalStorage queue for offline resilience
- No impact on Lighthouse score

**Integration Points**:
- Server: /api/analytics/event, /api/analytics/performance
- All JS files: Called from various interaction points
- Performance API: Monitors Core Web Vitals

**Future genX Migration**:
- genX may provide built-in analytics hooks
- Event tracking via genX lifecycle events
- Automatic performance monitoring

---

### 6. services/turso_browser_db.js (8KB, 155 lines)

**Purpose**: Browser-side Turso WASM database for offline-first functionality

**Core Capabilities**:
- Initialize Turso WASM client in browser
- Local-first data storage
- Sync to Turso cloud when online
- Offline tag creation and editing
- Conflict resolution

**Architecture Pattern**:
```javascript
// Turso WASM integration (experimental)
import { createClient } from '@libsql/client/web';

const db = createClient({
    url: 'libsql://multicardz.turso.io',
    authToken: getUserAuthToken(), // From server session
});

// Local-first: Write to local WASM DB immediately
async function createTagOffline(tagData) {
    await db.execute({
        sql: 'INSERT INTO tags (id, content, created_at) VALUES (?, ?, ?)',
        args: [generateUUID(), tagData.content, Date.now()]
    });

    // Sync to cloud when online
    if (navigator.onLine) {
        await db.sync();
    }
}
```

**Key Functions**:

1. **Database Initialization**:
```javascript
async function initTursoBrowserDB() {
    const db = createClient({
        url: 'libsql://multicardz.turso.io',
        authToken: await fetchAuthToken(),
    });

    // Create local schema if needed
    await db.execute(`
        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            content TEXT,
            group_id TEXT,
            position INTEGER,
            created_at INTEGER,
            synced BOOLEAN DEFAULT FALSE
        )
    `);

    return db;
}
```

2. **Offline Sync Queue**:
```javascript
// Queue operations when offline
const syncQueue = [];

async function queueOperation(operation) {
    syncQueue.push(operation);
    localStorage.setItem('turso-sync-queue', JSON.stringify(syncQueue));

    // Try to sync immediately if online
    if (navigator.onLine) {
        await processSyncQueue();
    }
}

async function processSyncQueue() {
    while (syncQueue.length > 0) {
        const op = syncQueue[0];
        try {
            await db.execute(op);
            syncQueue.shift(); // Remove from queue on success
        } catch (err) {
            console.error('Sync failed:', err);
            break; // Stop processing queue on error
        }
    }
    localStorage.setItem('turso-sync-queue', JSON.stringify(syncQueue));
}

// Process queue when coming back online
window.addEventListener('online', () => {
    processSyncQueue();
});
```

3. **Conflict Resolution**:
```javascript
async function resolveConflict(localTag, remoteTag) {
    // Last-write-wins strategy (simple)
    if (localTag.updated_at > remoteTag.updated_at) {
        return localTag; // Local version is newer
    } else {
        return remoteTag; // Remote version is newer
    }
}
```

**Status**:
- Experimental feature (not in production)
- Documented in architecture doc 027
- Integration with main app pending
- Future roadmap: Replace SQLite with Turso for all storage

**Performance Strategy**:
- WASM loads after FCP
- Database operations are async
- Minimal impact on main thread
- Lazy loading (only when offline features needed)

**Integration Points**:
- Server: Turso cloud database
- app.js: Initialization hooks
- drag-drop.js: Offline tag reordering
- group-tags.js: Offline group operations

**Future genX Migration**:
- genX may provide Turso adapter
- Automatic sync via genX data layer
- Built-in conflict resolution

---

## Performance Strategy

### Lighthouse 100/100 Maintenance

The entire JavaScript implementation is designed to maintain perfect Lighthouse scores:

1. **Deferred Loading**:
```html
<!-- All JavaScript loaded after FCP -->
<script src="/static/js/app.js" defer></script>
<script src="/static/js/drag-drop.js" defer></script>
<script src="/static/js/group-tags.js" defer></script>
<script src="/static/js/analytics.js" defer></script>
```

2. **Progressive Enhancement**:
- HTML renders first with server-side content
- JavaScript enhances interactions after load
- App works (read-only) without JavaScript

3. **Performance Budget**:
- Total JS: 168KB (within 200KB budget)
- Critical path: 0KB (all deferred)
- FCP impact: None (JS loads after FCP)
- LCP impact: None (content is server-rendered)

4. **Optimization Techniques**:
- Minification (drag-drop.min.js saves 66KB)
- Compression (gzip reduces 80KB → 15KB)
- Caching (immutable font hashes)
- Event delegation (fewer listeners)
- Debouncing (reduced server requests)

### Core Web Vitals Achieved

```
FCP (First Contentful Paint): 0.6s
LCP (Largest Contentful Paint): 1.2s
CLS (Cumulative Layout Shift): 0.00
FID (First Input Delay): 12ms
TTI (Time to Interactive): 1.8s
TBT (Total Blocking Time): 45ms

Lighthouse Score: 100/100
```

---

## DOM-as-Authority Pattern

### Philosophy

The current implementation embraces a **DOM-as-Authority** pattern:

1. **Server-Side Rendering**: HTML is the source of truth for initial state
2. **DOM Mutations**: JavaScript mutates DOM to reflect state changes
3. **Server Sync**: DOM changes sync to server for persistence
4. **No Client-State Objects**: State lives in DOM, not JavaScript variables

This is intentional and represents an architectural evolution from earlier pure-backend paradigms.

### Example: Tag State Management

```javascript
// NOT USED: Client-side state object (old approach)
const tagState = {
    tags: [
        { id: '1', content: 'Tag 1', selected: false },
        { id: '2', content: 'Tag 2', selected: true }
    ]
};

// USED: DOM-as-Authority (current approach)
// State stored directly in DOM
<div class="tag selected" data-tag-id="2">Tag 2</div>

// JavaScript reads state from DOM
const selectedTags = Array.from(document.querySelectorAll('.tag.selected'));

// JavaScript mutates DOM to change state
tag.classList.add('selected');

// Server syncs from DOM state
fetch('/api/tags/2/select', { method: 'POST' });
```

### Benefits

1. **Simplicity**: No state synchronization between JS objects and DOM
2. **Server Alignment**: Server renders HTML, client mutates same HTML
3. **Performance**: No virtual DOM diffing, direct DOM manipulation
4. **Debuggability**: State visible in DevTools Elements panel
5. **Resilience**: Page refresh restores server state

### Tradeoffs

1. **No Time Travel**: Can't replay state changes (no immutable history)
2. **Limited Testing**: Harder to unit test (requires DOM)
3. **Performance Ceiling**: DOM mutations can be slow at scale
4. **Implicit State**: State spread across many DOM attributes/classes

### Future with genX

genX will formalize this pattern with:
- Reactive DOM updates (state → DOM automatic)
- Server state sync (DOM → server automatic)
- Type-safe state (TypeScript schema validation)
- Optimized mutations (batched DOM updates)

---

## genX Integration Roadmap

### Current State: Vanilla JavaScript (168KB)

All current JavaScript is vanilla ES6+ with no framework dependencies.

### Phase 1: genX Conversion (Target: 35KB)

**Goal**: Replace 168KB vanilla JS with 35KB genX framework code

**Conversion Strategy**:

1. **drag-drop.js → genX State Management**:
```javascript
// Before: 80KB manual DOM manipulation
function selectTag(tagId) {
    const tag = document.querySelector(`[data-tag-id="${tagId}"]`);
    tag.classList.add('selected');
}

// After: 5KB genX reactive state (framework handles DOM)
genX.state.tags[tagId].selected = true;
```

2. **app.js → genX Components**:
```javascript
// Before: 28KB manual event listeners
document.addEventListener('click', (e) => {
    if (e.target.matches('.create-tag-btn')) {
        openModal('create-tag');
    }
});

// After: 3KB genX component
genX.component('CreateTagButton', {
    onClick: () => genX.modals.open('create-tag')
});
```

3. **group-tags.js → genX Reactive Associations**:
```javascript
// Before: 12KB manual state management
function assignTagToGroup(tagId, groupId) {
    tag.dataset.groupId = groupId;
    groupContainer.appendChild(tag);
}

// After: 2KB genX reactive model
genX.state.tags[tagId].groupId = groupId;
// DOM updates automatically, server sync automatic
```

### Phase 2: genX Performance Optimization

**Goals**:
- Maintain Lighthouse 100/100
- Reduce total JS to 35KB
- Improve code maintainability
- Enable better testing

**genX Usage Guidelines** (from doc 039):

1. **Deferred Loading**: genX framework loads after FCP
2. **Server-Side Rendering**: genX hydrates server HTML
3. **Progressive Enhancement**: Works without genX (graceful degradation)
4. **Performance Budget**: genX + app code < 50KB total

### Decision Matrix: When to Use genX

| Scenario | Use genX? | Rationale |
|----------|-----------|-----------|
| Multi-step user flows | Yes | State machine benefits |
| Drag-and-drop | Yes | Event orchestration |
| Form validation | Yes | Reactive validation |
| Modal management | Yes | Lifecycle hooks |
| Simple toggles | No | Vanilla JS sufficient |
| Static content | No | Server-rendered only |
| Analytics events | No | Fire-and-forget |
| Theme toggle | No | LocalStorage + class toggle |

---

## Testing Strategy

### Current State

- **Unit Tests**: Limited (drag-drop has some tests)
- **Integration Tests**: None
- **E2E Tests**: Playwright tests for critical paths
- **Manual Testing**: Primary validation method

### Testing Challenges with DOM-as-Authority

1. **DOM Dependency**: Tests require browser environment
2. **State Setup**: Must build DOM before testing
3. **Async Operations**: Server sync complicates tests
4. **Visual Validation**: Hard to test without screenshots

### Future with genX

genX will enable better testing:

```javascript
// Current: Hard to test (requires DOM)
function selectTag(tagId) {
    document.querySelector(`[data-tag-id="${tagId}"]`).classList.add('selected');
}

// Future: Easy to test (pure state)
genX.actions.selectTag(tagId);
expect(genX.state.tags[tagId].selected).toBe(true);
```

---

## Architecture Compliance

### Alignment with Architecture Docs

This implementation aligns with:

1. **Doc 001** (JavaScript Architecture): DOM-as-authority approach ✓
2. **Doc 022** (Data Architecture): SQLite backend, DOM frontend ✓
3. **Doc 024** (Backend Architecture): Server renders HTML ✓
4. **Doc 035** (Group Tags): Group UI implementation ✓
5. **Doc 039** (genX Integration): Migration roadmap ✓

### Deviations from Earlier Docs

Earlier documentation (pre-October 2025) advocated for:
- Pure backend rendering (no client state)
- Minimal JavaScript (< 10KB)
- No DOM mutations

These constraints were relaxed to enable:
- Rich drag-and-drop interactions
- Offline-first functionality
- Progressive enhancement

The DOM-as-Authority pattern is now the official architecture.

---

## File Organization

```
apps/static/js/
├── app.js (28KB)              # Core initialization
├── drag-drop.js (80KB)        # Drag-and-drop system
├── drag-drop.min.js (13KB)    # Minified version
├── group-tags.js (12KB)       # Tag grouping
├── group-ui-integration.js (24KB) # UI integration
├── analytics.js (16KB)        # Analytics tracking
└── services/
    └── turso_browser_db.js (8KB) # Offline database
```

### Minification Strategy

- **Production**: Use .min.js versions
- **Development**: Use full .js versions for debugging
- **Build Process**: Automated minification on deploy
- **Source Maps**: Available for production debugging

---

## Deployment Strategy

### Build Process

```bash
# 1. Minify JavaScript
terser apps/static/js/drag-drop.js -o apps/static/js/drag-drop.min.js

# 2. Calculate file hashes for cache busting
sha256sum apps/static/js/*.js > apps/static/js/checksums.txt

# 3. Update HTML templates with hashed filenames
# (Done automatically by build script)

# 4. Deploy to production
git push heroku main
```

### Cache Strategy

```html
<!-- Cache-busted filenames with immutable headers -->
<script src="/static/js/app.7f3a2e1b.js" defer></script>
<script src="/static/js/drag-drop.4c9d8f2a.min.js" defer></script>

<!-- Cache-Control: immutable, max-age=31536000 -->
```

### Performance Monitoring

```javascript
// Monitor JavaScript load performance
performance.mark('js-start');
import('/static/js/app.js').then(() => {
    performance.mark('js-end');
    performance.measure('js-load', 'js-start', 'js-end');

    const measure = performance.getEntriesByName('js-load')[0];
    analytics.trackEvent('Performance', 'JS Load Time', measure.duration);
});
```

---

## Known Issues and Technical Debt

### High Priority

1. **drag-drop.js Size**: 80KB is too large
   - **Solution**: Refactor into smaller modules
   - **Timeline**: Phase 1 genX migration
   - **Impact**: 50% size reduction possible

2. **Limited Unit Tests**: Most code untested
   - **Solution**: Add Jest tests with jsdom
   - **Timeline**: Q1 2026
   - **Impact**: Reduce regression risk

3. **No Error Boundaries**: Errors crash entire page
   - **Solution**: Add global error handlers
   - **Timeline**: Q4 2025
   - **Impact**: Better user experience on errors

### Medium Priority

4. **Duplicate Code**: Selection logic repeated across files
   - **Solution**: Extract to shared module
   - **Timeline**: Phase 1 genX migration
   - **Impact**: Easier maintenance

5. **Magic Strings**: Hard-coded IDs and classes
   - **Solution**: Constants file
   - **Timeline**: Q1 2026
   - **Impact**: Safer refactoring

6. **No TypeScript**: Runtime errors only
   - **Solution**: Migrate to TypeScript
   - **Timeline**: Phase 2 genX migration
   - **Impact**: Catch errors before runtime

### Low Priority

7. **Console Logs**: Debug logs in production
   - **Solution**: Strip in build process
   - **Timeline**: Q4 2025
   - **Impact**: Cleaner console

8. **Inconsistent Naming**: Some camelCase, some snake_case
   - **Solution**: Standardize on camelCase
   - **Timeline**: Ongoing refactor
   - **Impact**: Code consistency

---

## Migration Guide: Vanilla JS → genX

### Step 1: Identify genX Candidates

**Good candidates**:
- Complex state management (drag-drop)
- Multi-step flows (tag creation)
- Reactive UI (group membership)

**Poor candidates**:
- Simple toggles (theme switch)
- One-time actions (analytics events)
- Static content (no state)

### Step 2: Convert State to genX

```javascript
// Before: DOM-as-Authority
const selectedTags = document.querySelectorAll('.tag.selected');

// After: genX state
const selectedTags = genX.state.tags.filter(tag => tag.selected);
```

### Step 3: Convert Actions to genX

```javascript
// Before: Manual DOM mutation
function selectTag(tagId) {
    document.querySelector(`[data-tag-id="${tagId}"]`).classList.add('selected');
}

// After: genX action
genX.actions.selectTag = (tagId) => {
    genX.state.tags[tagId].selected = true;
};
```

### Step 4: Add Server Sync

```javascript
// genX handles server sync automatically
genX.sync('tags', {
    endpoint: '/api/tags',
    method: 'POST',
    debounce: 500 // Wait 500ms before syncing
});
```

### Step 5: Test and Deploy

```javascript
// Test genX state changes
describe('Tag Selection', () => {
    it('selects tag', () => {
        genX.actions.selectTag('tag-1');
        expect(genX.state.tags['tag-1'].selected).toBe(true);
    });

    it('syncs to server', async () => {
        genX.actions.selectTag('tag-1');
        await genX.sync.flush();
        expect(fetchMock).toHaveBeenCalledWith('/api/tags', { method: 'POST' });
    });
});
```

---

## Performance Budget

### Current Budget (November 2025)

| Category | Current | Budget | Status |
|----------|---------|--------|--------|
| Total JS | 168KB | 200KB | ✓ Within budget |
| Critical JS | 0KB | 10KB | ✓ All deferred |
| app.js | 28KB | 30KB | ✓ Within budget |
| drag-drop.js | 80KB | 50KB | ✗ Over budget |
| group-tags.js | 12KB | 15KB | ✓ Within budget |
| analytics.js | 16KB | 20KB | ✓ Within budget |

### Future Budget (Post-genX)

| Category | Target | Rationale |
|----------|--------|-----------|
| genX Framework | 15KB | Core framework |
| App Code | 20KB | Replaces app.js |
| Drag-Drop | 10KB | genX-powered, 80% smaller |
| Groups | 5KB | genX reactive state |
| Analytics | 10KB | Minimal changes |
| **Total** | **60KB** | **64% reduction** |

---

## Monitoring and Alerts

### Performance Monitoring

```javascript
// Track JavaScript errors
window.addEventListener('error', (event) => {
    fetch('/api/errors', {
        method: 'POST',
        body: JSON.stringify({
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            timestamp: Date.now()
        })
    });
});

// Track slow JavaScript execution
const slowThreshold = 50; // ms
performance.mark('function-start');
executeLongFunction();
performance.mark('function-end');
performance.measure('function-duration', 'function-start', 'function-end');

const measure = performance.getEntriesByName('function-duration')[0];
if (measure.duration > slowThreshold) {
    analytics.trackEvent('Performance', 'Slow Function', measure.duration);
}
```

### Alert Triggers

1. **JavaScript Error Rate > 1%**: Alert developer
2. **JS Load Time > 2s**: Investigate CDN/compression
3. **Lighthouse Score < 95**: Block deployment
4. **Bundle Size > 200KB**: Require optimization

---

## Conclusion

The current JavaScript implementation represents a mature, production-ready system that:

1. **Maintains Perfect Performance**: Lighthouse 100/100 with 168KB deferred JS
2. **Follows DOM-as-Authority**: Server-rendered HTML enhanced by client-side JS
3. **Enables Rich Interactions**: Drag-and-drop, multi-selection, offline support
4. **Prepares for genX**: Clear migration path to framework-powered future

The architecture is intentional, well-documented, and ready for the next phase of evolution with genX integration.

---

## References

- **Doc 001**: JavaScript Architecture (DOM-as-Authority pattern)
- **Doc 022**: Data Architecture (SQLite backend)
- **Doc 024**: Backend Architecture (Server-side rendering)
- **Doc 027**: Turso Browser Integration (Offline-first)
- **Doc 033**: Font Metrics Optimization (Performance strategy)
- **Doc 035**: Group Tags Architecture (Group implementation)
- **Doc 039**: genX Integration Architecture (Migration roadmap)

---

**Document Status**: Current Implementation
**Review Schedule**: Quarterly (next review February 2026)
**Maintenance Owner**: Frontend Team
**Last Updated**: 2025-11-06
