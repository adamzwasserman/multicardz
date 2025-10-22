# multicardz™ Polymorphic Drag-Drop System Specification

**Document ID**: drag-drop-polymorphic-specification-v1
**Created**: October 3, 2025
**Author**: System Architect
**Status**: Active Architecture Specification

---

## Executive Summary

This document specifies the complete polymorphic drag-drop system for multicardz, defining all valid drag/drop combinations, their behaviors, and implementation requirements. The system uses a state table-driven approach to enable extensible, maintainable drag-drop interactions while maintaining strict compliance with DOM manipulation rules and set theory operations.

**Core Principle**: Every drag/drop combination has exactly one well-defined behavior specified in the state table. No ambiguity, no if/else chains, pure polymorphic dispatch.

---

## 1. Droppable Element Types

### 1.1 Tag Clouds (Type: `tag-cloud`)
Drop zones that contain tags in their default/inactive state.

**Subtypes**:
- `tag-cloud-user` - User-created tags
- `tag-cloud-ai` - AI-generated tags
- `tag-cloud-system` - System tags (#COUNT, #SORT, etc.)
- `tag-cloud-group` - Tag groups (meta-tags containing multiple tags)

**DOM Selector**: `.cloud[data-cloud-type]`
**Accepts**: Tags (returns them to inactive state)

### 1.2 Drop Zones (Type: `drop-zone`)
Spatial manipulation zones that apply set operations to cards.

**Subtypes**:
- `union` - OR operation (cards matching ANY tag)
- `intersection` - AND operation (cards matching ALL tags)
- `exclusion` - NOT operation (cards NOT matching tags)
- `difference` - Subtraction operation
- `row` - Row dimension for 2D grid
- `column` - Column dimension for 2D grid
- *Unlimited custom types via `data-zone-type`*

**DOM Selector**: `[data-zone-type]:not([data-zone-type="tag-cloud"])`
**Accepts**: Tags (adds to tagsInPlay), Zones (cosmetic repositioning)

### 1.3 Cards (Type: `card`)
Individual data cards displayed in the spatial matrix.

**Subtypes**: None (cards are uniform)

**DOM Selector**: `.card-item[data-card-id]`
**Accepts**: Tags (adds to card's inverted index)

### 1.4 Card Tag Areas (Type: `card-tags`)
The tag display area within a card where tags can be dropped.

**Subtypes**: None

**DOM Selector**: `.card-tags`
**Accepts**: Tags (adds to card's tag collection)

### 1.5 Control Areas (Type: `control-area`)
Spatially arranged areas for zone organization (above, below, left, right of card display).

**Subtypes**:
- `control-area-left` - Left sidebar
- `control-area-right` - Right sidebar
- `control-area-top` - Top bar
- `control-area-bottom` - Bottom bar

**DOM Selector**: `.control-area-container[data-position]`
**Accepts**: Zones (cosmetic repositioning only)

### 1.6 Tag Groups (Type: `tag-group`)
Meta-tags that represent collections of tags.

**Subtypes**: None

**DOM Selector**: `.tag[data-type="group-tag"]`
**Accepts**: Tags (adds to group membership)

### 1.7 Spatial Matrix Cells (Type: `matrix-cell`)
Individual cells in the 2D spatial grid where cards are displayed.

**Subtypes**: Determined by row/column intersection

**DOM Selector**: `.grid-cell[data-row][data-column]`
**Accepts**: Cards (changes card's dimensional membership)

---

## 2. Draggable Element Types

### 2.1 Tags (Type: `tag`)
Individual filter/attribute tags.

**DOM Selector**: `[data-tag]:not([data-type="group-tag"])`
**Attributes Required**:
- `data-tag` - Tag name
- `data-tag-id` - UUID
- `data-type` - Tag type (user-tag, ai-tag, system-tag)

### 2.2 Tag Groups (Type: `tag-group`)
Meta-tags containing multiple tags.

**DOM Selector**: `[data-tag][data-type="group-tag"]`
**Attributes Required**:
- `data-tag` - Group name
- `data-tag-id` - UUID
- `data-members` - Comma-separated tag names

**Behavior**: Expands to individual tags on drag

### 2.3 Drop Zones (Type: `drop-zone`)
Zone containers that can be repositioned.

**DOM Selector**: `.drop-zone[data-zone-type]`
**Attributes Required**:
- `data-zone-type` - Zone type identifier

---

## 3. Drag/Drop State Table

### 3.1 Complete Behavior Matrix

| Draggable ↓ \ Droppable → | Tag Cloud | Drop Zone | Card Tags | Control Area | Tag Group | Matrix Cell |
|---------------------------|-----------|-----------|-----------|--------------|-----------|-------------|
| **Tag**                   | MOVE + Remove from tagsInPlay | MOVE + Add to tagsInPlay | ADD to card inverted index | ❌ Invalid | ADD to group members | ❌ Invalid |
| **Tag Group**             | MOVE all members | MOVE all members | ADD all to card | ❌ Invalid | ❌ Invalid | ❌ Invalid |
| **Drop Zone**             | ❌ Invalid | ❌ Invalid | ❌ Invalid | MOVE cosmetic | ❌ Invalid | ❌ Invalid |

**Legend**:
- ✅ Valid operation
- ❌ Invalid operation (prevent drop)
- MOVE = DOM element moved (not recreated)
- ADD = Create representation (original stays)

### 3.2 Detailed Behavior Specifications

#### 3.2.1 Tag → Tag Cloud
```javascript
{
  action: 'MOVE',
  domOperation: 'appendChild', // Move DOM element
  tagsInPlayMutation: 'REMOVE', // Remove tag_id from zone
  callsRender: true,
  validation: [
    'Tag must not already be in target cloud',
    'Tag type must match cloud type (user/ai/system)'
  ]
}
```

**Steps**:
1. Validate tag type matches cloud type
2. Move tag element to cloud's `.tags-wrapper`
3. Remove tag classes: `tag-active`
4. Add tag classes: `tag-cloud`
5. Remove tag_id from tagsInPlay.zones[sourceZone]
6. Call `updateStateAndRender()`

#### 3.2.2 Tag → Drop Zone
```javascript
{
  action: 'MOVE',
  domOperation: 'appendChild', // Move DOM element
  tagsInPlayMutation: 'ADD', // Add tag_id to zone
  callsRender: true,
  validation: [
    'Tag must not already be in target zone',
    'Zone must not exceed maxTags limit',
    'Zone must accept this tag type'
  ]
}
```

**Steps**:
1. Validate zone accepts tag type
2. Validate maxTags constraint
3. Move tag element to zone's `.tag-collection`
4. Remove tag classes: `tag-cloud`
5. Add tag classes: `tag-active`
6. Add tag_id to tagsInPlay.zones[zoneType].tags
7. Call `updateStateAndRender()`

#### 3.2.3 Tag → Card Tags
```javascript
{
  action: 'ADD_REPRESENTATION',
  domOperation: 'custom', // Create tag representation, keep original
  tagsInPlayMutation: 'NONE', // Does not affect tagsInPlay
  callsRender: false, // No card re-render needed
  validation: [
    'Card must have valid card_id',
    'Tag must not already be on card'
  ]
}
```

**Steps**:
1. Validate card has `data-card-id`
2. Check tag not already in card's `.card-tags`
3. Call `/api/v2/cards/add-tag` with `{card_id, tag_id}`
4. On success, create tag representation element
5. Append to `.card-tags` container
6. Original tag element stays in source location
7. Dispatch `cardTagDrop` custom event

#### 3.2.4 Tag → Control Area
**INVALID** - Tags cannot be dropped in control areas

#### 3.2.5 Tag → Tag Group
```javascript
{
  action: 'ADD_TO_GROUP',
  domOperation: 'updateAttribute', // Update group's data-members
  tagsInPlayMutation: 'CONDITIONAL', // Depends on group location
  callsRender: false,
  validation: [
    'Tag must not already be in group',
    'Group must accept this tag type'
  ]
}
```

**Steps**:
1. Validate tag not in group's `data-members`
2. Parse `data-members` attribute
3. Add tag name to members array
4. Update `data-members` attribute
5. If group is in a zone, update tagsInPlay to include new member
6. Dispatch `tagGroupModified` event

#### 3.2.6 Tag → Matrix Cell
**INVALID** - Tags cannot be dropped in matrix cells (cards can)

#### 3.2.7 Tag Group → Tag Cloud
```javascript
{
  action: 'MOVE_ALL_MEMBERS',
  domOperation: 'appendChild', // Move each member
  tagsInPlayMutation: 'REMOVE_ALL', // Remove all members from zones
  callsRender: true,
  validation: [
    'All member tags must exist',
    'Cloud must accept member tag types'
  ]
}
```

**Steps**:
1. Expand group to individual tag elements
2. For each member tag:
   - Move to appropriate cloud (user/ai/system)
   - Remove from tagsInPlay
3. Call `updateStateAndRender()`

#### 3.2.8 Tag Group → Drop Zone
```javascript
{
  action: 'MOVE_ALL_MEMBERS',
  domOperation: 'appendChild', // Move each member
  tagsInPlayMutation: 'ADD_ALL', // Add all members to zone
  callsRender: true,
  validation: [
    'All member tags must exist',
    'Zone must accept all member tags',
    'Zone must not exceed maxTags with all members'
  ]
}
```

**Steps**:
1. Expand group to individual tag elements
2. Validate zone capacity
3. For each member tag:
   - Move to zone's `.tag-collection`
   - Add to tagsInPlay.zones[zoneType].tags
4. Call `updateStateAndRender()`

#### 3.2.9 Tag Group → Card Tags
```javascript
{
  action: 'ADD_ALL_REPRESENTATIONS',
  domOperation: 'custom', // Create representations for all
  tagsInPlayMutation: 'NONE',
  callsRender: false,
  validation: [
    'All member tags must exist',
    'Card must have valid card_id'
  ]
}
```

**Steps**:
1. Expand group to individual tag elements
2. For each member tag:
   - Execute "Tag → Card Tags" behavior
   - Skip if tag already on card

#### 3.2.10 Drop Zone → Control Area
```javascript
{
  action: 'MOVE_COSMETIC',
  domOperation: 'appendChild', // Move zone container
  tagsInPlayMutation: 'NONE', // Cosmetic only
  callsRender: false,
  validation: [
    'Control area must exist',
    'Zone must be draggable (has drag handle)'
  ]
}
```

**Steps**:
1. Move zone element to control area
2. Update zone's `data-position` attribute
3. No tagsInPlay mutation
4. No card re-render

#### 3.2.11 Card → Matrix Cell
```javascript
{
  action: 'CHANGE_DIMENSION_MEMBERSHIP',
  domOperation: 'custom', // Complex tag manipulation
  tagsInPlayMutation: 'NONE', // Doesn't affect zone state
  callsRender: true,
  validation: [
    'Cell must have valid row/column coordinates',
    'Card must have valid card_id'
  ]
}
```

**Steps**:
1. Determine source cell's row/column tags
2. Determine target cell's row/column tags
3. Calculate tag diff (remove source, add target)
4. Call `/api/v2/cards/update-dimensions` with diff
5. Update card's tag representation in DOM
6. Call `updateStateAndRender()` to refresh grid

---

## 4. DOM Manipulation Rules

### 4.1 MOVE Operations (Critical)
**Rule**: When moving tags or zones, ALWAYS use DOM manipulation, NEVER delete and recreate.

**Correct Pattern**:
```javascript
targetContainer.appendChild(tagElement); // Moves element
```

**WRONG Pattern** (Never do this):
```javascript
tagElement.remove();
const newTag = document.createElement('span');
// ... recreate tag
targetContainer.appendChild(newTag);
```

**Reason**: Moving preserves:
- Event listeners
- Data attributes
- State consistency
- Memory references

### 4.2 ADD_REPRESENTATION Operations
**Rule**: When adding tag to card, create NEW element, keep original.

**Pattern**:
```javascript
// Original tag stays in source
const representation = document.createElement('span');
representation.className = 'card-tag';
representation.setAttribute('data-tag', tagName);
representation.innerHTML = `${tagName} <span class="tag-remove">×</span>`;
cardTags.appendChild(representation);
```

### 4.3 Cosmetic Operations
**Rule**: Pure visual changes, no state mutations.

**Pattern**:
```javascript
targetContainer.appendChild(zoneElement);
zoneElement.dataset.position = targetPosition;
// NO updateStateAndRender() call
```

---

## 5. tagsInPlay Mutation Rules

### 5.1 Structure
```javascript
tagsInPlay = {
  zones: {
    union: { tags: ['tag-id-1', 'tag-id-2'], metadata: {...} },
    intersection: { tags: ['tag-id-3'], metadata: {...} },
    exclusion: { tags: [], metadata: {...} },
    row: { tags: ['tag-id-4'], metadata: {...} },
    column: { tags: ['tag-id-5'], metadata: {...} }
  },
  controls: {
    startWithAllCards: false,
    startWithCardsExpanded: true,
    showColors: false
  }
}
```

### 5.2 Mutation Operations

#### ADD to Zone
```javascript
if (!tagsInPlay.zones[zoneType]) {
  tagsInPlay.zones[zoneType] = { tags: [], metadata: {} };
}
if (!tagsInPlay.zones[zoneType].tags.includes(tagId)) {
  tagsInPlay.zones[zoneType].tags.push(tagId);
}
```

#### REMOVE from Zone
```javascript
if (tagsInPlay.zones[zoneType]) {
  tagsInPlay.zones[zoneType].tags =
    tagsInPlay.zones[zoneType].tags.filter(id => id !== tagId);
}
```

#### MOVE between Zones
```javascript
// Remove from source
if (tagsInPlay.zones[sourceZone]) {
  tagsInPlay.zones[sourceZone].tags =
    tagsInPlay.zones[sourceZone].tags.filter(id => id !== tagId);
}

// Add to target
if (!tagsInPlay.zones[targetZone]) {
  tagsInPlay.zones[targetZone] = { tags: [], metadata: {} };
}
tagsInPlay.zones[targetZone].tags.push(tagId);
```

---

## 6. Polymorphic Handler Architecture

### 6.1 Handler Interface
```javascript
class DropHandler {
  /**
   * Check if this handler can process the drop
   */
  canHandle(dragType, dropType, dragElement, dropElement) {
    throw new Error('Must implement canHandle()');
  }

  /**
   * Validate the drop operation
   */
  validate(dragElement, dropElement) {
    throw new Error('Must implement validate()');
  }

  /**
   * Handle dragover event
   */
  handleDragOver(event, dropElement, draggedElements) {
    throw new Error('Must implement handleDragOver()');
  }

  /**
   * Handle drop event
   */
  async handleDrop(event, dropElement, draggedElements) {
    throw new Error('Must implement handleDrop()');
  }

  /**
   * Declare if handler mutates tagsInPlay
   */
  mutatesTagsInPlay() {
    return false;
  }

  /**
   * Declare if handler requires card re-render
   */
  requiresRerender() {
    return false;
  }
}
```

### 6.2 Handler Registry
```javascript
class DropTargetRegistry {
  constructor() {
    this.handlers = new Map();
    this.registerDefaultHandlers();
  }

  register(dragType, dropType, handler) {
    if (!this.handlers.has(dragType)) {
      this.handlers.set(dragType, new Map());
    }
    this.handlers.get(dragType).set(dropType, handler);
  }

  getHandler(dragType, dropType) {
    return this.handlers.get(dragType)?.get(dropType) || null;
  }

  findHandler(dragElement, dropElement) {
    const dragType = this.identifyDragType(dragElement);
    const dropType = this.identifyDropType(dropElement);

    const handler = this.getHandler(dragType, dropType);
    if (handler && handler.canHandle(dragType, dropType, dragElement, dropElement)) {
      return handler;
    }
    return null;
  }

  identifyDragType(element) {
    if (element.dataset.type === 'group-tag') return 'tag-group';
    if (element.dataset.tag) return 'tag';
    if (element.dataset.zoneType) return 'drop-zone';
    if (element.dataset.cardId) return 'card';
    return 'unknown';
  }

  identifyDropType(element) {
    if (element.classList.contains('cloud')) return 'tag-cloud';
    if (element.classList.contains('card-tags')) return 'card-tags';
    if (element.dataset.zoneType && element.dataset.zoneType !== 'tag-cloud') return 'drop-zone';
    if (element.classList.contains('control-area-container')) return 'control-area';
    if (element.dataset.type === 'group-tag') return 'tag-group';
    if (element.classList.contains('grid-cell')) return 'matrix-cell';
    return 'unknown';
  }

  registerDefaultHandlers() {
    // Tag handlers
    this.register('tag', 'tag-cloud', new TagToCloudHandler());
    this.register('tag', 'drop-zone', new TagToZoneHandler());
    this.register('tag', 'card-tags', new TagToCardHandler());
    this.register('tag', 'tag-group', new TagToGroupHandler());

    // Tag group handlers
    this.register('tag-group', 'tag-cloud', new GroupToCloudHandler());
    this.register('tag-group', 'drop-zone', new GroupToZoneHandler());
    this.register('tag-group', 'card-tags', new GroupToCardHandler());

    // Zone handlers
    this.register('drop-zone', 'control-area', new ZoneToControlHandler());

    // Card handlers
    this.register('card', 'matrix-cell', new CardToMatrixCellHandler());
  }
}
```

### 6.3 Event Delegation Pattern
```javascript
class SpatialDragDrop {
  constructor() {
    this.registry = new DropTargetRegistry();
    this.draggedElements = [];
    // ... other properties
  }

  initializeZones() {
    const container = document.body; // Universal delegation

    container.addEventListener('drop', (e) => {
      const dropTarget = e.target.closest('[data-droppable]') || e.target;
      const handler = this.registry.findHandler(
        this.draggedElements[0],
        dropTarget
      );

      if (handler) {
        e.preventDefault();
        if (handler.validate(this.draggedElements[0], dropTarget)) {
          handler.handleDrop(e, dropTarget, this.draggedElements);
        }
      }
    });

    container.addEventListener('dragover', (e) => {
      const dropTarget = e.target.closest('[data-droppable]') || e.target;
      const handler = this.registry.findHandler(
        this.draggedElements[0],
        dropTarget
      );

      if (handler) {
        handler.handleDragOver(e, dropTarget, this.draggedElements);
      }
    });
  }
}
```

---

## 7. Validation Rules

### 7.1 Drop Target Validation
- Tag cloud: Must match tag type (user/ai/system)
- Drop zone: Must accept tag type, must not exceed maxTags
- Card tags: Card must exist, tag must not duplicate
- Tag group: Tag must not already be member
- Control area: Only zones allowed
- Matrix cell: Only cards allowed

### 7.2 Error Handling
- Invalid drops: Prevent default, show visual rejection
- Failed API calls: Rollback DOM changes, show error
- Validation failures: Log warning, do not execute drop

---

## 8. Performance Requirements

### 8.1 Drop Operation Targets
- Handler lookup: < 1ms (Map-based O(1) lookup)
- DOM manipulation: < 5ms (direct appendChild, no jQuery)
- API calls: < 50ms (debounced, cached)
- Total drop operation: < 100ms (perceived instant)

### 8.2 Optimization Strategies
- Registry uses Map for O(1) handler lookup
- No DOM queries in hot path (cache elements)
- Debounce card re-renders (100ms)
- Batch multiple tag moves

---

## 9. Extension Points

### 9.1 Adding New Drop Target Types
1. Define drop type identifier
2. Implement DropHandler subclass
3. Register in `registerDefaultHandlers()`
4. Update `identifyDropType()` method
5. Add to state table documentation

### 9.2 Adding New Draggable Types
1. Define drag type identifier
2. Implement handlers for valid drop targets
3. Update `identifyDragType()` method
4. Add to state table documentation

---

## 10. Testing Requirements

### 10.1 State Table Coverage
- Test EVERY cell in state table
- Valid operations: Assert correct behavior
- Invalid operations: Assert drop prevented

### 10.2 Edge Cases
- Drop tag on self (should no-op)
- Drop in full zone (maxTags exceeded)
- Drop invalid type (should reject)
- Multiple simultaneous drops
- Network failures during API calls

---

## 11. Patent Compliance

This drag-drop system implements:
- **Claim 57**: Polymorphic tag behavior based on drop target type
- **Claims 121-174**: Multi-intersection visualization through spatial drop zones
- **Claim 1**: Spatial manipulation as primary interaction paradigm

The state table ensures consistent, patent-compliant behavior across all spatial manipulations while maintaining mathematical rigor of set operations.

---

**This specification provides the complete foundation for implementing a maintainable, extensible, and patent-compliant polymorphic drag-drop system.**