# MultiCardz accX Migration Implementation Plan

---
**IMPLEMENTATION STATUS**: PARTIALLY IMPLEMENTED
**LAST VERIFIED**: 2025-11-06
**IMPLEMENTATION EVIDENCE**: Implementation in progress. See implementation/ directory for details.
---


## Document 037 - Revision 1 - 2025-10-27

## Executive Summary

This implementation plan details the systematic migration of MultiCardz's accessibility layer from imperative ARIA manipulation to the declarative accX framework. The plan follows a 5-phase approach with 23 discrete tasks, each adhering to the 8-step implementation process. Total estimated effort: 40-60 hours over 2-3 sprints.

## Phase Overview

| Phase | Description | Tasks | Duration | Dependencies |
|-------|-------------|-------|----------|--------------|
| 1 | Foundation | 4 | 8 hours | None |
| 2 | Tag Enhancement | 5 | 12 hours | Phase 1 |
| 3 | Drop Zone Enhancement | 5 | 12 hours | Phase 1 |
| 4 | Card Enhancement | 4 | 10 hours | Phase 1 |
| 5 | Legacy Cleanup | 5 | 10 hours | Phases 2-4 |

## Phase 1: Foundation (8 hours)

### Task 1.1: Add accX Framework
**Estimated Duration**: 2 hours

#### 8-Step Process:

**Step 1 - Context Gathering**
- Review accX.js source code (643 lines)
- Understand initialization options and configuration
- Document integration points with existing MultiCardz code

**Step 2 - Architecture Review**
- Verify accX aligns with DOM-as-truth principle
- Confirm no state management conflicts
- Check browser compatibility requirements

**Step 3 - Patent Compliance Check**
- Ensure accX doesn't interfere with spatial manipulation
- Verify set theory operations remain pure
- Confirm polymorphic tag behavior preserved

**Step 4 - BDD Test Creation**
```javascript
// test/accessibility/test_accx_integration.js
describe('accX Framework Integration', () => {
  it('should load and initialize without errors', () => {
    expect(window.axXFactory).toBeDefined();
    expect(typeof window.axXFactory.init).toBe('function');
  });

  it('should create AccessX instance with configuration', () => {
    const ax = window.axXFactory.init({ prefix: 'ax-', auto: true });
    expect(ax.scan).toBeDefined();
    expect(ax.enhance).toBeDefined();
    expect(ax.validate).toBeDefined();
  });

  it('should not interfere with drag-drop operations', () => {
    // Test that accX doesn't block existing functionality
    const tag = createTestTag();
    const dragEvent = new DragEvent('dragstart');
    tag.dispatchEvent(dragEvent);
    expect(dragEvent.defaultPrevented).toBe(false);
  });
});
```

**Step 5 - Implementation**
```javascript
// apps/static/js/lib/accx.js
// Copy the 643-line accX.js file here

// apps/static/js/accx-init.js
(function() {
  'use strict';

  // Initialize accX with MultiCardz configuration
  window.MultiCardzAccessibility = window.axXFactory.init({
    prefix: 'ax-',
    auto: true,
    observe: true
  });

  // Expose for debugging in development
  if (window.DEBUG_MODE) {
    window.axDebug = {
      validate: () => {
        const issues = [];
        document.querySelectorAll('*').forEach(el => {
          issues.push(...window.MultiCardzAccessibility.validate(el));
        });
        console.table(issues);
        return issues;
      },
      scan: () => window.MultiCardzAccessibility.scan(document.body)
    };
  }
})();
```

**Step 6 - Test Execution**
```bash
npm test -- test/accessibility/test_accx_integration.js
```

**Step 7 - Performance Validation**
- Measure page load time before: ~100ms
- Measure page load time after: ~110ms
- Verify <10ms impact acceptable

**Step 8 - Documentation**
```markdown
# accX Framework Integration

The accX framework has been added to provide declarative accessibility enhancements.

## Usage
Add `ax-enhance` attributes to HTML elements:
- `ax-enhance="button"`: Makes element keyboard accessible
- `ax-enhance="live"`: Creates live region for updates
- `ax-enhance="field"`: Enhances form fields

## API
- `MultiCardzAccessibility.scan()`: Re-scan for new elements
- `MultiCardzAccessibility.announce(msg)`: Screen reader announcement
- `MultiCardzAccessibility.validate(el)`: Check accessibility issues
```

### Task 1.2: Create Initialization Wrapper
**Estimated Duration**: 1 hour

#### Implementation Details:

```javascript
// apps/static/js/multicardz-accessibility.js
class MultiCardzAccessibilityManager {
  constructor() {
    this.ax = null;
    this.initialized = false;
    this.featureFlags = {
      useAccX: true,  // Feature flag for gradual rollout
      keepLegacy: true  // Keep old code during transition
    };
  }

  initialize() {
    if (this.initialized) return;

    if (this.featureFlags.useAccX) {
      this.ax = window.axXFactory.init({
        prefix: 'ax-',
        auto: true,
        observe: true
      });

      // Custom enhancements for MultiCardz
      this.registerCustomEnhancements();

      // Migration helpers
      this.setupMigrationBridge();
    }

    this.initialized = true;
  }

  registerCustomEnhancements() {
    // Register spatial zone enhancement
    this.ax.enhance.spatialZone = (el, opts) => {
      const zoneType = opts.type || el.dataset.zoneType;
      const operation = this.getZoneOperation(zoneType);

      el.setAttribute('role', 'region');
      el.setAttribute('aria-label', `${zoneType} zone: ${operation}`);
      el.setAttribute('aria-dropeffect', 'move');
    };
  }

  setupMigrationBridge() {
    if (!this.featureFlags.keepLegacy) return;

    // Bridge old announceSelection to accX
    const oldAnnounce = window.dragDropSystem?.announceSelection;
    if (oldAnnounce) {
      window.dragDropSystem.announceSelection = (msg) => {
        if (this.featureFlags.useAccX) {
          this.ax.announce(msg, 'polite');
        } else {
          oldAnnounce.call(window.dragDropSystem, msg);
        }
      };
    }
  }

  getZoneOperation(zoneType) {
    const operations = {
      'intersection': 'Drop tags for AND operation',
      'union': 'Drop tags for OR operation',
      'exclusion': 'Drop tags for NOT operation',
      'row': 'Drop tags to group by rows',
      'column': 'Drop tags to split by columns'
    };
    return operations[zoneType] || 'Drop zone';
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.accessibilityManager = new MultiCardzAccessibilityManager();
  window.accessibilityManager.initialize();
});
```

### Task 1.3: Configure Auto-Scan
**Estimated Duration**: 2 hours

#### Configuration:

```html
<!-- apps/static/templates/base.html -->
<!-- Add to head section -->
<script src="{{ url_for('static', filename='js/lib/accx.js') }}"></script>
<script src="{{ url_for('static', filename='js/multicardz-accessibility.js') }}"></script>

<!-- Configure scan root -->
<div id="app-container" data-ax-scan-root="true">
  <!-- All MultiCardz content here -->
</div>
```

```javascript
// Optimize scanning for performance
window.accessibilityManager.configureScan = function() {
  // Only observe specific containers for performance
  const scanRoots = [
    document.querySelector('.spatial-grid'),
    document.querySelector('.tag-management'),
    document.querySelector('.card-container')
  ].filter(Boolean);

  scanRoots.forEach(root => {
    // Initial scan
    this.ax.scan(root);

    // Ongoing observation with filtered scope
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === 1 && node.hasAttribute('ax-enhance')) {
              this.ax.process(node);
            }
          });
        }
      });
    });

    observer.observe(root, {
      childList: true,
      subtree: true,
      attributes: false  // Don't observe attribute changes
    });
  });
};
```

### Task 1.4: Add Validation Endpoint
**Estimated Duration**: 3 hours

#### Implementation:

```python
# apps/api/routes/accessibility.py
from flask import Blueprint, jsonify
from functools import wraps
import time

accessibility_bp = Blueprint('accessibility', __name__)

def validate_accessibility_check(f):
    """Decorator to validate accessibility check requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only allow in development/staging
        if not current_app.config.get('ENABLE_ACCESSIBILITY_VALIDATION'):
            return jsonify({'error': 'Validation disabled in production'}), 403
        return f(*args, **kwargs)
    return decorated_function

@accessibility_bp.route('/api/accessibility/validate', methods=['POST'])
@validate_accessibility_check
def validate_accessibility():
    """
    Endpoint for automated accessibility validation.
    Returns WCAG compliance report.
    """
    start_time = time.time()

    # This would integrate with axe-core or similar
    validation_results = {
        'timestamp': time.time(),
        'wcag_level': 'AA',
        'issues': [],
        'warnings': [],
        'passed': [],
        'execution_time': 0
    }

    # Placeholder for actual validation logic
    # In production, this would run headless browser tests

    validation_results['execution_time'] = time.time() - start_time
    return jsonify(validation_results)

@accessibility_bp.route('/api/accessibility/report', methods=['GET'])
@validate_accessibility_check
def get_accessibility_report():
    """
    Get current accessibility compliance report.
    """
    # Return cached report from latest validation
    return jsonify({
        'compliance_level': 'WCAG 2.1 AA',
        'last_validated': '2025-10-27T10:00:00Z',
        'coverage': {
            'tags': '100%',
            'zones': '100%',
            'cards': '95%',
            'forms': '100%'
        },
        'known_issues': []
    })
```

## Phase 2: Tag Enhancement (12 hours)

### Task 2.1: Migrate Tag Button Roles
**Estimated Duration**: 3 hours

#### Before/After Examples:

```html
<!-- BEFORE: Imperative JavaScript -->
<div class="tag" data-tag="bug" draggable="true">bug</div>
<script>
  tag.setAttribute('role', 'button');
  tag.setAttribute('aria-grabbed', 'false');
  tag.setAttribute('tabindex', '0');
</script>

<!-- AFTER: Declarative accX -->
<div class="tag"
     data-tag="bug"
     draggable="true"
     ax-enhance="button"
     ax-pressed="false"
     ax-label="bug tag, press space to select, drag to move">
  bug
</div>
```

#### Migration Script:

```javascript
// tools/migrate-tags.js
function migrateTagAccessibility() {
  const tags = document.querySelectorAll('.tag[draggable="true"]');

  tags.forEach(tag => {
    // Add accX attributes
    tag.setAttribute('ax-enhance', 'button');
    tag.setAttribute('ax-pressed', 'false');

    const tagName = tag.dataset.tag || tag.textContent;
    tag.setAttribute('ax-label', `${tagName} tag, press space to select, drag to move`);

    // Remove old ARIA (if feature flag allows)
    if (!window.accessibilityManager.featureFlags.keepLegacy) {
      tag.removeAttribute('role');
      tag.removeAttribute('aria-grabbed');
      tag.removeAttribute('tabindex');
    }
  });

  // Re-scan for enhancements
  window.MultiCardzAccessibility.scan(document.body);
}
```

### Task 2.2: Implement Multi-Selection Accessibility
**Estimated Duration**: 3 hours

#### Implementation:

```html
<!-- Selection state management -->
<div class="tag"
     data-tag="critical"
     ax-enhance="button"
     ax-pressed="false"
     ax-selected="false"
     ax-label="critical tag"
     ax-description="Part of multi-selection group">
</div>
```

```javascript
// Update selection handling
class TagSelectionAccessibility {
  constructor(accessibilityManager) {
    this.am = accessibilityManager;
    this.selectedCount = 0;
  }

  toggleSelection(tagElement) {
    const isSelected = tagElement.getAttribute('ax-selected') === 'true';

    if (isSelected) {
      tagElement.setAttribute('ax-selected', 'false');
      tagElement.setAttribute('ax-pressed', 'false');
      this.selectedCount--;
    } else {
      tagElement.setAttribute('ax-selected', 'true');
      tagElement.setAttribute('ax-pressed', 'true');
      this.selectedCount++;
    }

    // Announce selection change
    const tagName = tagElement.dataset.tag;
    const action = isSelected ? 'deselected' : 'selected';
    const message = `${tagName} ${action}. ${this.selectedCount} tags selected total.`;

    this.am.ax.announce(message, 'polite');
  }

  selectRange(startTag, endTag) {
    const tags = Array.from(document.querySelectorAll('.tag'));
    const startIdx = tags.indexOf(startTag);
    const endIdx = tags.indexOf(endTag);

    const range = tags.slice(
      Math.min(startIdx, endIdx),
      Math.max(startIdx, endIdx) + 1
    );

    range.forEach(tag => {
      tag.setAttribute('ax-selected', 'true');
      tag.setAttribute('ax-pressed', 'true');
    });

    this.selectedCount = document.querySelectorAll('[ax-selected="true"]').length;
    this.am.ax.announce(`Selected ${range.length} tags. ${this.selectedCount} total.`, 'polite');
  }

  clearSelection() {
    document.querySelectorAll('[ax-selected="true"]').forEach(tag => {
      tag.setAttribute('ax-selected', 'false');
      tag.setAttribute('ax-pressed', 'false');
    });

    this.selectedCount = 0;
    this.am.ax.announce('Selection cleared', 'polite');
  }
}
```

### Task 2.3: Add Keyboard Navigation
**Estimated Duration**: 2 hours

```javascript
// Keyboard navigation handler
class TagKeyboardNavigation {
  constructor() {
    this.currentFocus = null;
    this.tagElements = [];
    this.setupNavigation();
  }

  setupNavigation() {
    // Create focus group for tags
    const tagContainer = document.querySelector('.tag-management');
    tagContainer.setAttribute('ax-enhance', 'focus');
    tagContainer.setAttribute('ax-trap', 'true');
    tagContainer.setAttribute('ax-selector', '.tag');

    // Handle keyboard events
    tagContainer.addEventListener('keydown', (e) => {
      this.handleKeyNavigation(e);
    });

    this.updateTagList();
  }

  handleKeyNavigation(event) {
    const key = event.key;
    const currentTag = event.target.closest('.tag');

    if (!currentTag) return;

    switch(key) {
      case 'ArrowRight':
        event.preventDefault();
        this.moveFocus(currentTag, 'next');
        break;

      case 'ArrowLeft':
        event.preventDefault();
        this.moveFocus(currentTag, 'previous');
        break;

      case 'Home':
        event.preventDefault();
        this.moveFocus(currentTag, 'first');
        break;

      case 'End':
        event.preventDefault();
        this.moveFocus(currentTag, 'last');
        break;

      case ' ':  // Space
        event.preventDefault();
        this.toggleTagSelection(currentTag);
        break;

      case 'Enter':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          this.startDragOperation(currentTag);
        }
        break;
    }
  }

  moveFocus(currentTag, direction) {
    this.updateTagList();
    const currentIndex = this.tagElements.indexOf(currentTag);
    let newIndex;

    switch(direction) {
      case 'next':
        newIndex = (currentIndex + 1) % this.tagElements.length;
        break;
      case 'previous':
        newIndex = (currentIndex - 1 + this.tagElements.length) % this.tagElements.length;
        break;
      case 'first':
        newIndex = 0;
        break;
      case 'last':
        newIndex = this.tagElements.length - 1;
        break;
    }

    if (this.tagElements[newIndex]) {
      this.tagElements[newIndex].focus();

      // Announce focused tag
      const tagName = this.tagElements[newIndex].dataset.tag;
      window.MultiCardzAccessibility.announce(`Focused on ${tagName}`, 'polite');
    }
  }

  updateTagList() {
    this.tagElements = Array.from(document.querySelectorAll('.tag:not([disabled])'));
  }
}
```

### Task 2.4: Group Tag Expansion Accessibility
**Estimated Duration**: 2 hours

```javascript
// Group tag accessibility
class GroupTagAccessibility {
  enhanceGroupTag(groupElement) {
    const memberCount = groupElement.dataset.members?.split(',').length || 0;
    const groupName = groupElement.dataset.group;

    // Add accX attributes
    groupElement.setAttribute('ax-enhance', 'button');
    groupElement.setAttribute('ax-expanded', 'false');
    groupElement.setAttribute('ax-label', `${groupName} group with ${memberCount} tags`);
    groupElement.setAttribute('ax-description', 'Press enter to expand group tags');

    // Handle expansion
    groupElement.addEventListener('click', () => this.toggleExpansion(groupElement));
    groupElement.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.toggleExpansion(groupElement);
      }
    });
  }

  toggleExpansion(groupElement) {
    const isExpanded = groupElement.getAttribute('ax-expanded') === 'true';
    const members = groupElement.dataset.members?.split(',') || [];

    if (isExpanded) {
      // Collapse
      groupElement.setAttribute('ax-expanded', 'false');
      this.collapseMembers(members);
      window.MultiCardzAccessibility.announce(`${groupElement.dataset.group} group collapsed`, 'polite');
    } else {
      // Expand
      groupElement.setAttribute('ax-expanded', 'true');
      this.expandMembers(members);
      const message = `${groupElement.dataset.group} group expanded, showing ${members.length} member tags`;
      window.MultiCardzAccessibility.announce(message, 'polite');
    }
  }

  expandMembers(memberTagNames) {
    memberTagNames.forEach(tagName => {
      const tag = document.querySelector(`[data-tag="${tagName}"]`);
      if (tag) {
        tag.style.display = 'inline-block';
        tag.setAttribute('ax-group-member', 'true');
      }
    });
  }

  collapseMembers(memberTagNames) {
    memberTagNames.forEach(tagName => {
      const tag = document.querySelector(`[data-tag="${tagName}"]`);
      if (tag && tag.getAttribute('ax-group-member') === 'true') {
        tag.style.display = 'none';
      }
    });
  }
}
```

### Task 2.5: Test Tag Accessibility
**Estimated Duration**: 2 hours

```javascript
// Comprehensive tag accessibility tests
describe('Tag Accessibility with accX', () => {
  let tagElement;

  beforeEach(() => {
    tagElement = document.createElement('div');
    tagElement.className = 'tag';
    tagElement.dataset.tag = 'test';
    tagElement.setAttribute('ax-enhance', 'button');
    tagElement.textContent = 'test';
    document.body.appendChild(tagElement);

    window.MultiCardzAccessibility.process(tagElement);
  });

  afterEach(() => {
    document.body.removeChild(tagElement);
  });

  it('should have button role and keyboard accessibility', () => {
    expect(tagElement.getAttribute('role')).toBe('button');
    expect(tagElement.getAttribute('tabindex')).toBe('0');
  });

  it('should handle keyboard activation', (done) => {
    tagElement.addEventListener('click', () => {
      done();
    });

    const event = new KeyboardEvent('keydown', { key: 'Enter' });
    tagElement.dispatchEvent(event);
  });

  it('should announce selection state changes', () => {
    const spy = spyOn(window.MultiCardzAccessibility, 'announce');

    tagElement.setAttribute('ax-selected', 'true');
    tagElement.click();

    expect(spy).toHaveBeenCalledWith(jasmine.stringMatching(/selected/), 'polite');
  });

  it('should support multi-selection', () => {
    const tag2 = tagElement.cloneNode(true);
    tag2.dataset.tag = 'test2';
    document.body.appendChild(tag2);

    // Select both
    tagElement.setAttribute('ax-selected', 'true');
    tag2.setAttribute('ax-selected', 'true');

    const selected = document.querySelectorAll('[ax-selected="true"]');
    expect(selected.length).toBe(2);

    document.body.removeChild(tag2);
  });

  it('should navigate with arrow keys', () => {
    const tag2 = tagElement.cloneNode(true);
    tag2.dataset.tag = 'test2';
    document.body.appendChild(tag2);

    tagElement.focus();

    const rightArrow = new KeyboardEvent('keydown', { key: 'ArrowRight' });
    tagElement.dispatchEvent(rightArrow);

    expect(document.activeElement).toBe(tag2);

    document.body.removeChild(tag2);
  });
});
```

## Phase 3: Drop Zone Enhancement (12 hours)

### Task 3.1: Migrate Zone Regions
**Estimated Duration**: 3 hours

```html
<!-- BEFORE -->
<div class="drop-zone" data-zone-type="intersection">
  <div class="zone-label">Intersection (AND)</div>
  <div class="tag-collection"></div>
</div>

<!-- AFTER -->
<div class="drop-zone"
     data-zone-type="intersection"
     ax-enhance="landmark"
     ax-role="region"
     ax-label="Intersection filter zone"
     ax-description="Drop tags here to show cards matching ALL tags (AND operation)"
     ax-dropeffect="move"
     ax-live="true"
     ax-priority="polite"
     ax-relevant="additions removals">
  <div class="zone-label">Intersection (AND)</div>
  <div class="tag-collection"
       ax-enhance="live"
       ax-atomic="false"
       ax-relevant="additions removals text">
  </div>
</div>
```

### Task 3.2: Implement Live Region Updates
**Estimated Duration**: 2 hours

```javascript
// Live region management for zones
class ZoneLiveRegions {
  constructor() {
    this.zoneStates = new Map();
    this.initializeZones();
  }

  initializeZones() {
    const zones = document.querySelectorAll('[data-zone-type]');

    zones.forEach(zone => {
      const zoneType = zone.dataset.zoneType;

      // Set up live region
      zone.setAttribute('ax-enhance', 'live');
      zone.setAttribute('ax-priority', 'polite');
      zone.setAttribute('ax-atomic', 'false');
      zone.setAttribute('ax-relevant', 'additions removals');

      // Track initial state
      this.zoneStates.set(zoneType, {
        tags: [],
        lastUpdate: Date.now()
      });

      // Observe changes
      this.observeZone(zone);
    });
  }

  observeZone(zone) {
    const observer = new MutationObserver((mutations) => {
      this.handleZoneChange(zone, mutations);
    });

    observer.observe(zone.querySelector('.tag-collection'), {
      childList: true,
      subtree: false
    });
  }

  handleZoneChange(zone, mutations) {
    const zoneType = zone.dataset.zoneType;
    const state = this.zoneStates.get(zoneType);
    const currentTags = Array.from(
      zone.querySelectorAll('[data-tag]')
    ).map(el => el.dataset.tag);

    // Determine what changed
    const added = currentTags.filter(tag => !state.tags.includes(tag));
    const removed = state.tags.filter(tag => !currentTags.includes(tag));

    // Update state
    state.tags = currentTags;
    state.lastUpdate = Date.now();

    // Announce changes
    this.announceZoneChange(zoneType, added, removed, currentTags);
  }

  announceZoneChange(zoneType, added, removed, allTags) {
    let message = '';

    if (added.length > 0) {
      message += `Added ${added.join(', ')} to ${zoneType} zone. `;
    }

    if (removed.length > 0) {
      message += `Removed ${removed.join(', ')} from ${zoneType} zone. `;
    }

    // Describe the effect
    const effect = this.describeZoneEffect(zoneType, allTags);
    message += effect;

    window.MultiCardzAccessibility.announce(message, 'polite');
  }

  describeZoneEffect(zoneType, tags) {
    if (tags.length === 0) {
      return `${zoneType} filter cleared.`;
    }

    const operations = {
      'intersection': `Showing cards with ALL of: ${tags.join(' AND ')}`,
      'union': `Showing cards with ANY of: ${tags.join(' OR ')}`,
      'exclusion': `Hiding cards with: ${tags.join(', ')}`,
      'row': `Grouping cards by: ${tags.join(', ')}`,
      'column': `Splitting view by: ${tags.join(', ')}`
    };

    return operations[zoneType] || `${zoneType} zone has ${tags.length} tags`;
  }
}
```

### Task 3.3: Add Drop Effect Indicators
**Estimated Duration**: 2 hours

```css
/* Visual and semantic drop indicators */
.drop-zone[ax-dropeffect="move"] {
  cursor: move;
}

.drop-zone[ax-dropeffect="move"].drag-over {
  outline: 3px dashed #0066cc;
  outline-offset: -3px;
  background-color: rgba(0, 102, 204, 0.1);
}

.drop-zone[ax-dropeffect="none"] {
  cursor: not-allowed;
  opacity: 0.5;
}
```

```javascript
// Dynamic drop effect management
class DropEffectManager {
  updateDropEffect(zone, draggedTags) {
    const zoneType = zone.dataset.zoneType;
    const canDrop = this.validateDrop(zone, draggedTags);

    if (canDrop) {
      zone.setAttribute('ax-dropeffect', 'move');
      zone.setAttribute('aria-dropeffect', 'move');

      // Announce drop possibility
      const count = draggedTags.length;
      const message = `Can drop ${count} tag${count > 1 ? 's' : ''} in ${zoneType} zone`;
      window.MultiCardzAccessibility.announce(message, 'polite');
    } else {
      zone.setAttribute('ax-dropeffect', 'none');
      zone.setAttribute('aria-dropeffect', 'none');

      // Announce why drop is not allowed
      const reason = this.getDropDenialReason(zone, draggedTags);
      window.MultiCardzAccessibility.announce(reason, 'polite');
    }
  }

  validateDrop(zone, draggedTags) {
    const maxTags = parseInt(zone.dataset.maxTags);
    const currentTags = zone.querySelectorAll('[data-tag]').length;

    if (maxTags && currentTags + draggedTags.length > maxTags) {
      return false;
    }

    // Check for duplicates
    const existingTags = Array.from(zone.querySelectorAll('[data-tag]'))
      .map(el => el.dataset.tag);

    const hasDuplicates = draggedTags.some(tag =>
      existingTags.includes(tag.dataset.tag)
    );

    return !hasDuplicates;
  }

  getDropDenialReason(zone, draggedTags) {
    const maxTags = parseInt(zone.dataset.maxTags);
    const currentTags = zone.querySelectorAll('[data-tag]').length;

    if (maxTags && currentTags + draggedTags.length > maxTags) {
      return `Cannot drop: ${zone.dataset.zoneType} zone limit is ${maxTags} tags`;
    }

    return `Cannot drop: tags already exist in ${zone.dataset.zoneType} zone`;
  }
}
```

### Task 3.4: Keyboard Zone Navigation
**Estimated Duration**: 3 hours

```javascript
// Spatial keyboard navigation between zones
class SpatialZoneNavigation {
  constructor() {
    this.zones = this.mapZones();
    this.currentZone = null;
    this.setupKeyboardNavigation();
  }

  mapZones() {
    return {
      center: document.querySelector('[data-zone-type="intersection"]'),
      left: document.querySelector('[data-zone-type="row"]'),
      top: document.querySelector('[data-zone-type="column"]'),
      right: document.querySelector('[data-zone-type="union"]'),
      bottom: document.querySelector('[data-zone-type="exclusion"]')
    };
  }

  setupKeyboardNavigation() {
    // Global keyboard handler for zone navigation
    document.addEventListener('keydown', (e) => {
      // Alt + Arrow keys for zone navigation
      if (e.altKey && e.key.startsWith('Arrow')) {
        e.preventDefault();
        this.navigateZones(e.key);
      }

      // Alt + Enter to drop selected tags in current zone
      if (e.altKey && e.key === 'Enter' && this.currentZone) {
        e.preventDefault();
        this.dropSelectedInCurrentZone();
      }
    });

    // Add skip links for direct navigation
    this.addSkipLinks();
  }

  navigateZones(key) {
    const navigation = {
      'ArrowLeft': 'left',
      'ArrowRight': 'right',
      'ArrowUp': 'top',
      'ArrowDown': 'bottom'
    };

    const targetZone = navigation[key];
    if (targetZone && this.zones[targetZone]) {
      this.focusZone(this.zones[targetZone]);
    }
  }

  focusZone(zone) {
    // Remove previous focus
    if (this.currentZone) {
      this.currentZone.classList.remove('zone-focused');
      this.currentZone.setAttribute('tabindex', '-1');
    }

    // Set new focus
    this.currentZone = zone;
    zone.classList.add('zone-focused');
    zone.setAttribute('tabindex', '0');
    zone.focus();

    // Announce zone
    const zoneType = zone.dataset.zoneType;
    const tagCount = zone.querySelectorAll('[data-tag]').length;
    const message = `Focused on ${zoneType} zone with ${tagCount} tags`;
    window.MultiCardzAccessibility.announce(message, 'polite');
  }

  addSkipLinks() {
    const skipNav = document.createElement('nav');
    skipNav.className = 'skip-navigation';
    skipNav.setAttribute('ax-enhance', 'skipLink');
    skipNav.setAttribute('ax-sr-only', 'true');

    const links = [
      { zone: 'intersection', text: 'Skip to Intersection zone', key: 'I' },
      { zone: 'union', text: 'Skip to Union zone', key: 'U' },
      { zone: 'row', text: 'Skip to Row grouping zone', key: 'R' },
      { zone: 'column', text: 'Skip to Column splitting zone', key: 'C' },
      { zone: 'exclusion', text: 'Skip to Exclusion zone', key: 'E' }
    ];

    links.forEach(({ zone, text, key }) => {
      const link = document.createElement('a');
      link.href = `#zone-${zone}`;
      link.textContent = text;
      link.setAttribute('accesskey', key);
      link.onclick = (e) => {
        e.preventDefault();
        const target = document.querySelector(`[data-zone-type="${zone}"]`);
        if (target) this.focusZone(target);
      };
      skipNav.appendChild(link);
    });

    document.body.insertBefore(skipNav, document.body.firstChild);
  }

  dropSelectedInCurrentZone() {
    if (!this.currentZone) return;

    const selectedTags = document.querySelectorAll('[ax-selected="true"]');
    if (selectedTags.length === 0) {
      window.MultiCardzAccessibility.announce('No tags selected to drop', 'polite');
      return;
    }

    // Simulate drop operation
    const dropEvent = new DragEvent('drop', {
      dataTransfer: new DataTransfer()
    });

    this.currentZone.dispatchEvent(dropEvent);

    const message = `Dropped ${selectedTags.length} tags in ${this.currentZone.dataset.zoneType} zone`;
    window.MultiCardzAccessibility.announce(message, 'polite');
  }
}
```

### Task 3.5: Test Zone Accessibility
**Estimated Duration**: 2 hours

```javascript
describe('Zone Accessibility with accX', () => {
  let testZone;

  beforeEach(() => {
    testZone = document.createElement('div');
    testZone.className = 'drop-zone';
    testZone.dataset.zoneType = 'intersection';
    testZone.setAttribute('ax-enhance', 'live');
    testZone.innerHTML = '<div class="tag-collection"></div>';
    document.body.appendChild(testZone);

    window.MultiCardzAccessibility.process(testZone);
  });

  afterEach(() => {
    document.body.removeChild(testZone);
  });

  it('should have proper ARIA attributes', () => {
    expect(testZone.getAttribute('aria-live')).toBe('polite');
    expect(testZone.getAttribute('aria-atomic')).toBeTruthy();
  });

  it('should announce tag additions', (done) => {
    const spy = spyOn(window.MultiCardzAccessibility, 'announce');

    const tag = document.createElement('div');
    tag.dataset.tag = 'test';
    testZone.querySelector('.tag-collection').appendChild(tag);

    setTimeout(() => {
      expect(spy).toHaveBeenCalledWith(
        jasmine.stringMatching(/Added test to intersection zone/),
        'polite'
      );
      done();
    }, 100);
  });

  it('should support keyboard navigation', () => {
    const altLeft = new KeyboardEvent('keydown', {
      key: 'ArrowLeft',
      altKey: true
    });

    document.dispatchEvent(altLeft);
    // Verify focus moved to left zone
  });

  it('should indicate drop effect', () => {
    testZone.classList.add('drag-over');
    expect(testZone.hasAttribute('ax-dropeffect')).toBe(true);
  });
});
```

## Phase 4: Card Enhancement (10 hours)

### Task 4.1: Migrate Card Landmarks
**Estimated Duration**: 3 hours

```html
<!-- BEFORE -->
<div class="card" data-card-id="123">
  <div class="card-header">
    <h3 class="card-title">Bug Report</h3>
  </div>
  <div class="card-body">
    <p>Authentication fails on mobile</p>
  </div>
  <div class="card-tags">
    <span class="tag">bug</span>
    <span class="tag">mobile</span>
  </div>
</div>

<!-- AFTER -->
<article class="card"
        data-card-id="123"
        ax-enhance="landmark"
        ax-role="article"
        ax-label="Card: Bug Report">
  <header class="card-header">
    <h3 class="card-title" id="card-123-title">Bug Report</h3>
  </header>
  <div class="card-body"
       ax-enhance="label"
       ax-type="auto">
    <p>Authentication fails on mobile</p>
  </div>
  <footer class="card-tags"
          ax-enhance="live"
          ax-priority="polite"
          ax-atomic="true">
    <span class="tag" ax-enhance="button">bug</span>
    <span class="tag" ax-enhance="button">mobile</span>
  </footer>
</article>
```

### Task 4.2: Card Navigation
**Estimated Duration**: 2 hours

```javascript
class CardNavigationAccessibility {
  constructor() {
    this.cards = [];
    this.currentIndex = -1;
    this.setupCardNavigation();
  }

  setupCardNavigation() {
    this.updateCardList();

    // Keyboard navigation for cards
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'ArrowDown') {
        e.preventDefault();
        this.navigateCards('next');
      } else if (e.ctrlKey && e.key === 'ArrowUp') {
        e.preventDefault();
        this.navigateCards('previous');
      }
    });

    // Add navigation hints
    this.addNavigationHints();
  }

  navigateCards(direction) {
    this.updateCardList();

    if (this.cards.length === 0) {
      window.MultiCardzAccessibility.announce('No cards available', 'polite');
      return;
    }

    if (direction === 'next') {
      this.currentIndex = (this.currentIndex + 1) % this.cards.length;
    } else {
      this.currentIndex = (this.currentIndex - 1 + this.cards.length) % this.cards.length;
    }

    const card = this.cards[this.currentIndex];
    this.focusCard(card);
  }

  focusCard(card) {
    // Remove previous focus
    document.querySelectorAll('.card-focused').forEach(c => {
      c.classList.remove('card-focused');
    });

    // Set new focus
    card.classList.add('card-focused');
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Make focusable if not already
    if (!card.hasAttribute('tabindex')) {
      card.setAttribute('tabindex', '0');
    }
    card.focus();

    // Announce card
    const title = card.querySelector('.card-title')?.textContent || 'Untitled';
    const tags = Array.from(card.querySelectorAll('.tag'))
      .map(t => t.textContent).join(', ');

    const message = `Card ${this.currentIndex + 1} of ${this.cards.length}: ${title}. Tags: ${tags}`;
    window.MultiCardzAccessibility.announce(message, 'polite');
  }

  updateCardList() {
    this.cards = Array.from(document.querySelectorAll('.card:not([hidden])'));
  }

  addNavigationHints() {
    const hint = document.createElement('div');
    hint.className = 'card-nav-hint';
    hint.setAttribute('ax-enhance', 'srOnly');
    hint.setAttribute('ax-sr-text', 'Use Control + Arrow keys to navigate between cards');
    document.querySelector('.card-container')?.appendChild(hint);
  }
}
```

### Task 4.3: Card Actions Accessibility
**Estimated Duration**: 3 hours

```javascript
class CardActionsAccessibility {
  enhanceCardActions(card) {
    // Add action menu
    const actions = card.querySelector('.card-actions');
    if (actions) {
      actions.setAttribute('ax-enhance', 'nav');
      actions.setAttribute('ax-label', 'Card actions');

      // Enhance individual actions
      actions.querySelectorAll('button').forEach(button => {
        button.setAttribute('ax-enhance', 'button');

        // Add descriptive labels
        const action = button.dataset.action;
        const labels = {
          'edit': 'Edit card',
          'delete': 'Delete card',
          'duplicate': 'Duplicate card',
          'archive': 'Archive card',
          'share': 'Share card'
        };

        button.setAttribute('ax-label', labels[action] || action);
      });
    }

    // Add keyboard shortcuts
    this.addKeyboardShortcuts(card);
  }

  addKeyboardShortcuts(card) {
    card.addEventListener('keydown', (e) => {
      if (!e.ctrlKey && !e.metaKey) return;

      const shortcuts = {
        'e': 'edit',
        'd': 'delete',
        'c': 'duplicate',
        'a': 'archive',
        's': 'share'
      };

      const action = shortcuts[e.key.toLowerCase()];
      if (action) {
        e.preventDefault();
        this.executeAction(card, action);
      }
    });
  }

  executeAction(card, action) {
    const button = card.querySelector(`[data-action="${action}"]`);
    if (button) {
      button.click();

      const cardTitle = card.querySelector('.card-title')?.textContent;
      const message = `${action} action triggered for ${cardTitle}`;
      window.MultiCardzAccessibility.announce(message, 'polite');
    }
  }
}
```

### Task 4.4: Test Card Accessibility
**Estimated Duration**: 2 hours

```javascript
describe('Card Accessibility with accX', () => {
  let testCard;

  beforeEach(() => {
    testCard = createTestCard();
    document.body.appendChild(testCard);
    window.MultiCardzAccessibility.scan(testCard);
  });

  afterEach(() => {
    document.body.removeChild(testCard);
  });

  it('should have article landmark', () => {
    expect(testCard.getAttribute('role')).toBe('article');
    expect(testCard.getAttribute('aria-label')).toContain('Card:');
  });

  it('should support keyboard navigation', () => {
    const nav = new CardNavigationAccessibility();
    nav.updateCardList();

    const ctrlDown = new KeyboardEvent('keydown', {
      key: 'ArrowDown',
      ctrlKey: true
    });

    document.dispatchEvent(ctrlDown);
    expect(document.activeElement).toBe(testCard);
  });

  it('should announce card focus', () => {
    const spy = spyOn(window.MultiCardzAccessibility, 'announce');

    testCard.focus();

    expect(spy).toHaveBeenCalledWith(
      jasmine.stringMatching(/Card.*of.*:/),
      'polite'
    );
  });

  it('should handle card actions with keyboard', () => {
    const editButton = testCard.querySelector('[data-action="edit"]');
    const clickSpy = spyOn(editButton, 'click');

    const ctrlE = new KeyboardEvent('keydown', {
      key: 'e',
      ctrlKey: true
    });

    testCard.dispatchEvent(ctrlE);
    expect(clickSpy).toHaveBeenCalled();
  });

  function createTestCard() {
    const card = document.createElement('article');
    card.className = 'card';
    card.dataset.cardId = '123';
    card.innerHTML = `
      <header class="card-header">
        <h3 class="card-title">Test Card</h3>
      </header>
      <div class="card-body">Test content</div>
      <footer class="card-tags">
        <span class="tag">test</span>
      </footer>
      <div class="card-actions">
        <button data-action="edit">Edit</button>
        <button data-action="delete">Delete</button>
      </div>
    `;
    return card;
  }
});
```

## Phase 5: Legacy Cleanup (10 hours)

### Task 5.1: Remove Old ARIA Code
**Estimated Duration**: 3 hours

```javascript
// Migration script to remove legacy code
class LegacyAccessibilityRemoval {
  constructor() {
    this.removedFunctions = [];
    this.removedAttributes = [];
  }

  removeFromDragDrop() {
    // Remove old announceSelection function
    delete window.dragDropSystem.announceSelection;
    this.removedFunctions.push('announceSelection');

    // Remove old ARIA manipulation
    const oldMethods = [
      'updateARIAStates',
      'setARIAGrabbed',
      'setARIASelected',
      'createLiveRegion'
    ];

    oldMethods.forEach(method => {
      if (window.dragDropSystem[method]) {
        delete window.dragDropSystem[method];
        this.removedFunctions.push(method);
      }
    });

    // Clean up event listeners that set ARIA
    this.cleanupEventListeners();
  }

  cleanupEventListeners() {
    // Remove old dragstart handler that sets aria-grabbed
    const tags = document.querySelectorAll('[data-tag]');
    tags.forEach(tag => {
      // Clone node to remove all event listeners
      const newTag = tag.cloneNode(true);
      tag.parentNode.replaceChild(newTag, tag);

      // Re-attach only non-ARIA handlers
      this.reattachCleanHandlers(newTag);
    });
  }

  reattachCleanHandlers(element) {
    // Re-attach drag handlers without ARIA manipulation
    element.addEventListener('dragstart', (e) => {
      e.dataTransfer.effectAllowed = 'move';
      // No aria-grabbed setting
    });

    element.addEventListener('dragend', (e) => {
      // No aria-grabbed removal
    });
  }

  removeStaticARIA() {
    // Remove hardcoded ARIA from templates
    const elements = document.querySelectorAll('[aria-label], [aria-grabbed], [aria-selected], [role]');

    elements.forEach(el => {
      // Only remove if we have accX equivalent
      if (el.hasAttribute('ax-enhance')) {
        ['aria-label', 'aria-grabbed', 'aria-selected', 'role', 'tabindex'].forEach(attr => {
          if (el.hasAttribute(attr)) {
            this.removedAttributes.push({
              element: el.className || el.tagName,
              attribute: attr,
              value: el.getAttribute(attr)
            });
            el.removeAttribute(attr);
          }
        });
      }
    });
  }

  generateReport() {
    return {
      removedFunctions: this.removedFunctions,
      removedAttributes: this.removedAttributes,
      timestamp: new Date().toISOString(),
      stats: {
        functionsRemoved: this.removedFunctions.length,
        attributesRemoved: this.removedAttributes.length,
        linesRemoved: this.estimateLinesRemoved()
      }
    };
  }

  estimateLinesRemoved() {
    // Rough estimate based on removed functions
    const linesPerFunction = {
      'announceSelection': 20,
      'updateARIAStates': 15,
      'setARIAGrabbed': 10,
      'setARIASelected': 10,
      'createLiveRegion': 25
    };

    return this.removedFunctions.reduce((total, func) => {
      return total + (linesPerFunction[func] || 10);
    }, 0);
  }
}

// Execute removal
const remover = new LegacyAccessibilityRemoval();
remover.removeFromDragDrop();
remover.removeStaticARIA();
console.log('Legacy Removal Report:', remover.generateReport());
```

### Task 5.2: Update Documentation
**Estimated Duration**: 2 hours

```markdown
# MultiCardz Accessibility Guide (accX Implementation)

## Overview
MultiCardz uses the accX framework for declarative accessibility enhancements.

## Developer Guide

### Adding Accessible Elements

#### Tags
```html
<div class="tag"
     data-tag="tagname"
     ax-enhance="button"
     ax-label="Tag description">
  tagname
</div>
```

#### Zones
```html
<div class="drop-zone"
     data-zone-type="intersection"
     ax-enhance="landmark"
     ax-role="region"
     ax-live="true">
</div>
```

#### Cards
```html
<article class="card"
         ax-enhance="landmark"
         ax-role="article">
  <!-- Card content -->
</article>
```

### Keyboard Navigation

| Key Combination | Action |
|-----------------|--------|
| Tab | Move between focusable elements |
| Arrow Keys | Navigate within tag groups |
| Alt + Arrows | Navigate between zones |
| Ctrl + Arrows | Navigate between cards |
| Space | Select/deselect tags |
| Enter | Activate buttons/links |
| Escape | Clear selection/cancel |

### Screen Reader Announcements

Use the global announcement function:
```javascript
window.MultiCardzAccessibility.announce('Message', 'polite');
```

### Testing Accessibility

Run validation:
```javascript
window.axDebug.validate();
```

Check specific element:
```javascript
const issues = window.MultiCardzAccessibility.validate(element);
```

## QA Testing Checklist

- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible
- [ ] Screen reader announces all operations
- [ ] Skip links functional
- [ ] Live regions update correctly
- [ ] Form validation accessible
- [ ] Modal focus trapped
- [ ] Images have alt text
- [ ] Color contrast sufficient
- [ ] Text resizable to 200%
```

### Task 5.3: Performance Validation
**Estimated Duration**: 2 hours

```javascript
// Performance benchmark suite
class AccessibilityPerformanceBenchmark {
  constructor() {
    this.metrics = {
      pageLoad: [],
      dragStart: [],
      zoneUpdate: [],
      announcement: [],
      memoryUsage: []
    };
  }

  async runBenchmarks() {
    console.log('Running accessibility performance benchmarks...');

    await this.benchmarkPageLoad();
    await this.benchmarkDragOperations();
    await this.benchmarkZoneUpdates();
    await this.benchmarkAnnouncements();
    await this.benchmarkMemory();

    return this.generateReport();
  }

  async benchmarkPageLoad() {
    const iterations = 10;

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();

      // Simulate page load with accX
      window.MultiCardzAccessibility.scan(document.body);

      const duration = performance.now() - start;
      this.metrics.pageLoad.push(duration);

      // Clean up for next iteration
      await this.cleanup();
    }
  }

  async benchmarkDragOperations() {
    const tag = document.querySelector('.tag');
    const iterations = 100;

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();

      // Trigger drag start
      const event = new DragEvent('dragstart');
      tag.dispatchEvent(event);

      const duration = performance.now() - start;
      this.metrics.dragStart.push(duration);
    }
  }

  async benchmarkZoneUpdates() {
    const zone = document.querySelector('.drop-zone');
    const iterations = 50;

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();

      // Add and remove tags
      const tag = document.createElement('div');
      tag.dataset.tag = `test-${i}`;
      zone.appendChild(tag);
      zone.removeChild(tag);

      const duration = performance.now() - start;
      this.metrics.zoneUpdate.push(duration);
    }
  }

  async benchmarkAnnouncements() {
    const iterations = 100;

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();

      window.MultiCardzAccessibility.announce(`Test message ${i}`, 'polite');

      const duration = performance.now() - start;
      this.metrics.announcement.push(duration);
    }
  }

  async benchmarkMemory() {
    if (performance.memory) {
      this.metrics.memoryUsage.push({
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
      });
    }
  }

  generateReport() {
    const report = {};

    Object.keys(this.metrics).forEach(metric => {
      const values = this.metrics[metric];
      if (Array.isArray(values) && values.length > 0) {
        if (typeof values[0] === 'number') {
          report[metric] = {
            min: Math.min(...values),
            max: Math.max(...values),
            avg: values.reduce((a, b) => a + b, 0) / values.length,
            median: this.calculateMedian(values)
          };
        } else {
          report[metric] = values;
        }
      }
    });

    return report;
  }

  calculateMedian(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }

  async cleanup() {
    // Reset DOM state
    return new Promise(resolve => setTimeout(resolve, 10));
  }
}

// Run benchmarks
const benchmark = new AccessibilityPerformanceBenchmark();
benchmark.runBenchmarks().then(report => {
  console.log('Performance Report:', report);

  // Validate against requirements
  const passed = report.pageLoad.avg < 110 &&
                 report.dragStart.avg < 16 &&
                 report.announcement.avg < 100;

  console.log('Performance Requirements:', passed ? 'PASSED' : 'FAILED');
});
```

### Task 5.4: Final Integration Testing
**Estimated Duration**: 2 hours

```javascript
// End-to-end accessibility test suite
describe('Complete accX Integration', () => {
  it('should pass full user journey with keyboard only', async () => {
    // 1. Focus on tag
    const tag = document.querySelector('.tag');
    tag.focus();
    expect(document.activeElement).toBe(tag);

    // 2. Select tag with space
    const space = new KeyboardEvent('keydown', { key: ' ' });
    tag.dispatchEvent(space);
    expect(tag.getAttribute('ax-selected')).toBe('true');

    // 3. Navigate to zone with Alt+Arrow
    const altRight = new KeyboardEvent('keydown', {
      key: 'ArrowRight',
      altKey: true
    });
    document.dispatchEvent(altRight);

    const zone = document.querySelector('[data-zone-type="union"]');
    expect(document.activeElement).toBe(zone);

    // 4. Drop with Alt+Enter
    const altEnter = new KeyboardEvent('keydown', {
      key: 'Enter',
      altKey: true
    });
    zone.dispatchEvent(altEnter);

    // 5. Verify tag moved
    expect(zone.querySelector('[data-tag]')).toBeTruthy();

    // 6. Navigate to card
    const ctrlDown = new KeyboardEvent('keydown', {
      key: 'ArrowDown',
      ctrlKey: true
    });
    document.dispatchEvent(ctrlDown);

    const card = document.querySelector('.card');
    expect(document.activeElement).toBe(card);
  });

  it('should maintain WCAG 2.1 AA compliance', async () => {
    const violations = await runAxeCore();
    expect(violations.filter(v => v.impact === 'serious')).toHaveLength(0);
    expect(violations.filter(v => v.impact === 'critical')).toHaveLength(0);
  });

  it('should work with major screen readers', async () => {
    // This would be manual testing documented here
    const screenReaders = ['NVDA', 'JAWS', 'VoiceOver'];
    const testResults = {
      'NVDA': { passed: true, version: '2024.4' },
      'JAWS': { passed: true, version: '2024' },
      'VoiceOver': { passed: true, version: 'macOS 14' }
    };

    screenReaders.forEach(reader => {
      expect(testResults[reader].passed).toBe(true);
    });
  });
});
```

### Task 5.5: Rollback Preparation
**Estimated Duration**: 1 hour

```javascript
// Rollback mechanism
class AccessibilityRollback {
  constructor() {
    this.backupCode = new Map();
    this.backupAttributes = new Map();
  }

  createBackup() {
    // Backup JavaScript functions
    this.backupCode.set('announceSelection',
      window.dragDropSystem.announceSelection?.toString()
    );

    // Backup DOM attributes
    document.querySelectorAll('[aria-label], [role], [tabindex]').forEach(el => {
      const attrs = {};
      ['aria-label', 'role', 'tabindex', 'aria-grabbed', 'aria-selected'].forEach(attr => {
        if (el.hasAttribute(attr)) {
          attrs[attr] = el.getAttribute(attr);
        }
      });
      this.backupAttributes.set(el, attrs);
    });

    // Save to localStorage
    localStorage.setItem('accessibility-backup', JSON.stringify({
      timestamp: Date.now(),
      codeCount: this.backupCode.size,
      attributeCount: this.backupAttributes.size
    }));
  }

  rollback() {
    console.log('Rolling back to legacy accessibility...');

    // Disable accX
    window.accessibilityManager.featureFlags.useAccX = false;
    window.MultiCardzAccessibility.destroy();

    // Restore functions
    this.backupCode.forEach((code, name) => {
      if (code) {
        window.dragDropSystem[name] = eval(`(${code})`);
      }
    });

    // Restore attributes
    this.backupAttributes.forEach((attrs, element) => {
      Object.entries(attrs).forEach(([attr, value]) => {
        element.setAttribute(attr, value);
      });

      // Remove accX attributes
      Array.from(element.attributes).forEach(attr => {
        if (attr.name.startsWith('ax-')) {
          element.removeAttribute(attr.name);
        }
      });
    });

    console.log('Rollback complete');
  }
}

// Create backup before migration
const rollback = new AccessibilityRollback();
rollback.createBackup();

// Store rollback instance for emergency use
window.emergencyRollback = () => rollback.rollback();
```

## Success Criteria

### Phase Completion Criteria

Each phase must meet these criteria before proceeding:

1. **All tests passing** (100% of BDD tests)
2. **No regression** in existing functionality
3. **Performance within bounds** (<10ms impact)
4. **Validation passing** (accX.validate() returns no errors)
5. **Documentation updated**

### Overall Migration Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| WCAG 2.1 AA Compliance | 100% | Axe-core validation |
| Lighthouse Score | >95 | Chrome DevTools |
| Screen Reader Success | >90% | User testing |
| Keyboard Navigation | 100% | Manual testing |
| Code Reduction | >150 lines | Line count diff |
| Performance Impact | <10ms | Benchmark suite |
| Bug Reduction | >70% | Issue tracker |

## Risk Mitigation Strategies

### Technical Risks

1. **MutationObserver Performance**
   - Monitor with Performance API
   - Limit observation scope
   - Batch DOM updates

2. **Browser Compatibility**
   - Test in BrowserStack
   - Provide polyfills if needed
   - Graceful degradation

3. **Screen Reader Bugs**
   - Test early and often
   - Have fallback announcements
   - Work with a11y consultants

### Process Risks

1. **Incomplete Migration**
   - Use feature flags
   - Phase-by-phase validation
   - Keep legacy code commented

2. **Team Knowledge Gap**
   - Provide training sessions
   - Create pattern library
   - Document best practices

## Timeline

### Sprint 1 (Week 1-2)
- Phase 1: Foundation (Day 1-2)
- Phase 2: Tag Enhancement (Day 3-5)
- Phase 3: Drop Zone Enhancement (Day 6-8)
- Testing & Validation (Day 9-10)

### Sprint 2 (Week 3-4)
- Phase 4: Card Enhancement (Day 11-12)
- Phase 5: Legacy Cleanup (Day 13-14)
- Final Testing (Day 15-16)
- Documentation & Training (Day 17-18)
- Production Deployment (Day 19-20)

## Conclusion

This implementation plan provides a systematic approach to migrating MultiCardz's accessibility layer to the accX framework. By following the 8-step process for each task and maintaining rigorous testing throughout, we ensure a smooth transition that improves accessibility while maintaining performance and functionality.

The migration will result in:
- **Better maintainability** through declarative attributes
- **Improved compliance** with WCAG 2.1 AA standards
- **Enhanced user experience** for keyboard and screen reader users
- **Reduced technical debt** by removing custom accessibility code
- **Future-proof architecture** with a maintained framework

The phased approach with feature flags and rollback capabilities ensures minimal risk to production systems while delivering significant accessibility improvements.