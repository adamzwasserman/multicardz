/**
 * multicardz™ Spatial Drag-Drop System
 * Handles dynamic zone discovery, multi-tag operations, and immutable DOM manipulation
 *
 * Architecture: Polymorphic state table-driven drag-drop with handler registry
 * See: /docs/Architecture/drag-drop-polymorphic-specification.md
 */

/**
 * Debounce utility - prevents rapid repeated calls
 */
function debounce(func, wait) {
  let timeout;
  let lastCall = 0;

  return function executedFunction(...args) {
    const now = Date.now();
    const timeSinceLastCall = now - lastCall;

    const later = () => {
      timeout = null;
      lastCall = now;
      func(...args);
    };

    clearTimeout(timeout);

    // If enough time has passed, execute immediately
    if (timeSinceLastCall >= wait) {
      lastCall = now;
      func(...args);
    } else {
      // Otherwise, schedule for later
      timeout = setTimeout(later, wait - timeSinceLastCall);
    }
  };
}

/**
 * Simple EventEmitter for pub/sub pattern
 * Allows decoupled communication between components
 */
class EventEmitter {
  constructor() {
    this.events = {};
  }

  on(event, listener) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
    return () => this.off(event, listener);
  }

  off(event, listener) {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(l => l !== listener);
  }

  emit(event, data) {
    if (!this.events[event]) return;
    this.events[event].forEach(listener => listener(data));
  }
}

// Global event emitter for tag/card count updates
window.tagCountEmitter = new EventEmitter();

/**
 * Base class for all drop handlers
 * Implements polymorphic dispatch pattern for drag-drop operations
 */
class DropHandler {
  /**
   * Check if this handler can process the drop
   */
  canHandle(dragType, dropType, dragElement, dropElement) {
    return false;
  }

  /**
   * Validate the drop operation
   */
  validate(dragElement, dropElement) {
    return true;
  }

  /**
   * Validate batch operation before execution
   * Returns { valid: boolean, errors: string[] }
   */
  validateBatch(draggedElements, dropElement) {
    const errors = [];

    // Check basic drop validity
    if (!dropElement.hasAttribute('data-droppable') &&
        !dropElement.classList.contains('cloud') &&
        !dropElement.classList.contains('card-tags') &&
        !dropElement.dataset.zoneType) {
      errors.push('Invalid drop target');
      return { valid: false, errors };
    }

    // Validate each element individually
    for (const element of draggedElements) {
      if (!this.validate(element, dropElement)) {
        const tagName = element.dataset.tag || 'unknown';
        errors.push(`Cannot drop ${tagName} here`);
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Handle dragover event for visual feedback
   */
  handleDragOver(event, dropElement, draggedElements) {
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move';
    }
    dropElement.classList.add('drag-over');
  }

  /**
   * Handle dragleave event to remove visual feedback
   */
  handleDragLeave(event, dropElement, draggedElements) {
    dropElement.classList.remove('drag-over');
  }

  /**
   * Handle drop event (override in subclasses)
   */
  async handleDrop(event, dropElement, draggedElements) {
    throw new Error('Must implement handleDrop() in subclass');
  }

  /**
   * Declare if handler supports optimized batch operations
   */
  supportsBatch() {
    return false;
  }

  /**
   * Handle batch drop operation (optional optimization)
   * Override in subclasses that can process batches more efficiently
   */
  async handleBatchDrop(event, dropElement, draggedElements) {
    // Default: process sequentially
    return await this.processBatchSequentially(event, dropElement, draggedElements);
  }

  /**
   * Process batch sequentially with error collection
   */
  async processBatchSequentially(event, dropElement, draggedElements) {
    const total = draggedElements.length;
    let completed = 0;
    const errors = [];
    const successful = [];

    for (const element of draggedElements) {
      try {
        if (this.validate(element, dropElement)) {
          await this.handleDrop(event, dropElement, [element]);
          completed++;
          successful.push(element);
        } else {
          const tagName = element.dataset.tag || 'unknown';
          errors.push(`Cannot drop ${tagName} here`);
        }
      } catch (error) {
        const tagName = element.dataset.tag || 'unknown';
        errors.push(`Failed to process ${tagName}: ${error.message}`);
      }
    }

    return {
      success: errors.length === 0,
      completed,
      total,
      errors,
      successful
    };
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

/**
 * Registry for drag-drop handlers using state table pattern
 * Maps (dragType, dropType) → Handler instance
 */
class DropTargetRegistry {
  constructor(dragDropSystem) {
    this.system = dragDropSystem;
    this.handlers = new Map();
    this.registerDefaultHandlers();
  }

  /**
   * Register a handler for a specific drag/drop combination
   */
  register(dragType, dropType, handler) {
    if (!this.handlers.has(dragType)) {
      this.handlers.set(dragType, new Map());
    }
    this.handlers.get(dragType).set(dropType, handler);
  }

  /**
   * Get handler for specific drag/drop types
   */
  getHandler(dragType, dropType) {
    return this.handlers.get(dragType)?.get(dropType) || null;
  }

  /**
   * Find appropriate handler for drag and drop elements
   */
  findHandler(dragElement, dropElement) {
    if (!dragElement || !dropElement) return null;

    const dragType = this.identifyDragType(dragElement);
    const dropType = this.identifyDropType(dropElement);

    if (dragType === 'unknown' || dropType === 'unknown') return null;

    const handler = this.getHandler(dragType, dropType);
    if (handler && handler.canHandle(dragType, dropType, dragElement, dropElement)) {
      return handler;
    }
    return null;
  }

  /**
   * Identify drag element type
   */
  identifyDragType(element) {
    if (element.dataset.type === 'group-tag') return 'tag-group';
    if (element.dataset.tag) return 'tag';
    if (element.dataset.zoneType) return 'drop-zone';
    if (element.dataset.cardId) return 'card';
    return 'unknown';
  }

  /**
   * Identify drop target type
   */
  identifyDropType(element) {
    if (element.classList.contains('cloud')) return 'tag-cloud';
    if (element.classList.contains('card-tags')) return 'card-tags';
    if (element.dataset.zoneType && element.dataset.zoneType !== 'tag-cloud') return 'drop-zone';
    if (element.classList.contains('control-area-container')) return 'control-area';
    if (element.dataset.type === 'group-tag') return 'tag-group';
    if (element.classList.contains('grid-cell')) return 'matrix-cell';
    return 'unknown';
  }

  /**
   * Register all default handlers from state table
   */
  registerDefaultHandlers() {
    // Tag handlers
    this.register('tag', 'tag-cloud', new TagToCloudHandler(this.system));
    this.register('tag', 'drop-zone', new TagToZoneHandler(this.system));
    this.register('tag', 'card-tags', new TagToCardHandler(this.system));

    // Tag group handlers
    this.register('tag-group', 'tag-cloud', new GroupToCloudHandler(this.system));
    this.register('tag-group', 'drop-zone', new GroupToZoneHandler(this.system));
    this.register('tag-group', 'card-tags', new GroupToCardHandler(this.system));

    // Card handlers
    this.register('card', 'matrix-cell', new CardToCellHandler(this.system));
  }
}

/**
 * Tag → Tag Cloud Handler
 * MOVE tag back to cloud, REMOVE from tagsInPlay
 */
class TagToCloudHandler extends DropHandler {
  constructor(system) {
    super();
    this.system = system;
  }

  canHandle(dragType, dropType, dragElement, dropElement) {
    return dragType === 'tag' && dropType === 'tag-cloud';
  }

  validate(dragElement, dropElement) {
    // Check tag type matches cloud type
    const tagType = dragElement.dataset.type || 'user-tag';
    const cloudType = dropElement.dataset.cloudType;

    // User and AI tags can both go to user cloud if preference is set
    if (cloudType === 'user') return tagType === 'user-tag' || tagType === 'ai-tag';
    if (cloudType === 'ai') return tagType === 'ai-tag';
    if (cloudType === 'system') return tagType === 'system-tag';
    if (cloudType === 'group') return tagType === 'group-tag';

    return false;
  }

  async handleDrop(event, dropElement, draggedElements) {
    event.preventDefault();
    dropElement.classList.remove('drag-over');

    const cloudWrapper = dropElement.querySelector('.tags-wrapper');
    if (!cloudWrapper) return;

    for (const tagElement of draggedElements) {
      if (!this.validate(tagElement, dropElement)) continue;

      // MOVE tag to cloud (DOM manipulation, not recreation)
      cloudWrapper.appendChild(tagElement);
      tagElement.classList.remove('tag-active', 'selected');
      tagElement.classList.add('tag-cloud');
    }
  }

  mutatesTagsInPlay() {
    return true; // Removes tags from zones
  }

  requiresRerender() {
    return true;
  }
}

/**
 * Tag → Drop Zone Handler
 * MOVE tag to zone, ADD to tagsInPlay
 */
class TagToZoneHandler extends DropHandler {
  constructor(system) {
    super();
    this.system = system;
  }

  canHandle(dragType, dropType, dragElement, dropElement) {
    return dragType === 'tag' && dropType === 'drop-zone';
  }

  validate(dragElement, dropElement) {
    const tagCollection = dropElement.querySelector('.tag-collection');
    if (!tagCollection) return false;

    // Check if already in zone
    if (tagCollection.contains(dragElement)) return false;

    // Check maxTags constraint
    const maxTags = this.system.parseMaxTags(dropElement.dataset.maxTags);
    if (maxTags && tagCollection.children.length >= maxTags) return false;

    return true;
  }

  validateBatch(draggedElements, dropElement) {
    const errors = [];
    const tagCollection = dropElement.querySelector('.tag-collection');

    if (!tagCollection) {
      errors.push('Invalid zone - no tag collection found');
      return { valid: false, errors };
    }

    // Check zone capacity for batch
    const maxTags = this.system.parseMaxTags(dropElement.dataset.maxTags);
    const currentCount = tagCollection.children.length;
    const newCount = draggedElements.length;

    if (maxTags && (currentCount + newCount) > maxTags) {
      const available = maxTags - currentCount;
      errors.push(`Zone can only accept ${available} more tag${available !== 1 ? 's' : ''}`);
    }

    // Check for duplicates
    const existingTags = new Set();
    tagCollection.querySelectorAll('[data-tag]').forEach(tag => {
      existingTags.add(tag.dataset.tag);
    });

    for (const element of draggedElements) {
      const tagName = element.dataset.tag;
      if (existingTags.has(tagName)) {
        errors.push(`${tagName} is already in this zone`);
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  supportsBatch() {
    return true; // Optimized batch processing available
  }

  async handleDrop(event, dropElement, draggedElements) {
    event.preventDefault();
    dropElement.classList.remove('drag-over');

    const tagCollection = dropElement.querySelector('.tag-collection');
    if (!tagCollection) return;

    for (const tagElement of draggedElements) {
      if (!this.validate(tagElement, dropElement)) continue;

      // MOVE tag to zone (DOM manipulation, not recreation)
      tagCollection.appendChild(tagElement);
      tagElement.classList.remove('tag-cloud');
      tagElement.classList.add('tag-active');
    }
  }

  async handleBatchDrop(event, dropElement, draggedElements) {
    event.preventDefault();
    dropElement.classList.remove('drag-over');

    const tagCollection = dropElement.querySelector('.tag-collection');
    if (!tagCollection) {
      return {
        success: false,
        errors: ['No tag collection found in zone'],
        completed: 0,
        total: draggedElements.length
      };
    }

    // Use document fragment for batch DOM manipulation
    const fragment = document.createDocumentFragment();
    const successful = [];

    for (const tagElement of draggedElements) {
      // Move tag to fragment
      tagElement.classList.remove('tag-cloud', 'tag-selected');
      tagElement.classList.add('tag-active');
      fragment.appendChild(tagElement);
      successful.push(tagElement);
    }

    // Single DOM reflow for all tags
    tagCollection.appendChild(fragment);

    return {
      success: true,
      completed: successful.length,
      total: draggedElements.length,
      errors: [],
      successful
    };
  }

  mutatesTagsInPlay() {
    return true; // Adds tags to zone
  }

  requiresRerender() {
    return true;
  }
}

/**
 * Tag → Card Tags Handler
 * ADD representation to card, keep original tag in place
 */
class TagToCardHandler extends DropHandler {
  constructor(system) {
    super();
    this.system = system;
  }

  canHandle(dragType, dropType, dragElement, dropElement) {
    return dragType === 'tag' && dropType === 'card-tags';
  }

  validate(dragElement, dropElement) {
    const card = dropElement.closest('.card-item');
    if (!card || !card.dataset.cardId) return false;

    // Check if tag already on card
    const tagName = dragElement.dataset.tag;
    if (dropElement.querySelector(`[data-tag="${tagName}"]`)) return false;

    return true;
  }

  async handleDrop(event, dropElement, draggedElements) {
    event.preventDefault();
    dropElement.classList.remove('drag-over');

    const card = dropElement.closest('.card-item');
    const cardId = card?.dataset.cardId;
    if (!cardId) {
      console.error('TagToCardHandler: No cardId found');
      return;
    }

    for (const tagElement of draggedElements) {
      if (!this.validate(tagElement, dropElement)) {
        continue;
      }

      const tagName = tagElement.getAttribute('data-tag');
      const tagId = tagElement.getAttribute('data-tag-id');

      if (tagName && tagId) {
        window.dispatchEvent(new CustomEvent('cardTagDrop', {
          detail: { cardId, tagId, tagName, cardTags: dropElement }
        }));
      } else {
        console.error('TagToCardHandler: Missing tagName or tagId', { tagName, tagId });
      }
    }
  }

  mutatesTagsInPlay() {
    return false; // Does not affect tagsInPlay
  }

  requiresRerender() {
    return true; // Cards may need to move to different grid cells based on new tags
  }
}

/**
 * Card → Grid Cell Handler
 * MOVE card to different grid cell, UPDATE tags based on row/column
 */
class CardToCellHandler extends DropHandler {
  constructor(system) {
    super();
    this.system = system;
  }

  canHandle(dragType, dropType, dragElement, dropElement) {
    return dragType === 'card' && dropType === 'matrix-cell';
  }

  validate(dragElement, dropElement) {
    const sourceCell = dragElement.closest('.grid-cell');
    return sourceCell !== dropElement; // Can't drop in same cell
  }

  async handleDrop(event, dropElement, draggedElements) {
    event.preventDefault();
    dropElement.classList.remove('drag-over');

    const card = draggedElements[0];
    const sourceCell = card.closest('.grid-cell');

    window.dispatchEvent(new CustomEvent('cardCellMove', {
      detail: {
        cardId: card.dataset.cardId,
        sourceRow: sourceCell?.dataset.row,
        sourceCol: sourceCell?.dataset.col,
        destRow: dropElement.dataset.row,
        destCol: dropElement.dataset.col
      }
    }));
  }

  mutatesTagsInPlay() {
    return false; // Does not affect zone tags
  }

  requiresRerender() {
    return true; // Card needs to move to new cell
  }
}

/**
 * Tag Group → Tag Cloud Handler
 * MOVE all group members to cloud, REMOVE from tagsInPlay
 */
class GroupToCloudHandler extends DropHandler {
  constructor(system) {
    super();
    this.system = system;
  }

  canHandle(dragType, dropType, dragElement, dropElement) {
    return dragType === 'tag-group' && dropType === 'tag-cloud';
  }

  async handleDrop(event, dropElement, draggedElements) {
    event.preventDefault();
    dropElement.classList.remove('drag-over');

    for (const groupElement of draggedElements) {
      // Expand group to individual tags
      const memberTags = this.system.expandGroupTag(groupElement);

      // Move each member to cloud
      for (const tagElement of memberTags) {
        const tagToCloud = new TagToCloudHandler(this.system);
        await tagToCloud.handleDrop(event, dropElement, [tagElement]);
      }
    }
  }

  mutatesTagsInPlay() {
    return true;
  }

  requiresRerender() {
    return true;
  }
}

/**
 * Tag Group → Drop Zone Handler
 * MOVE all group members to zone, ADD to tagsInPlay
 */
class GroupToZoneHandler extends DropHandler {
  constructor(system) {
    super();
    this.system = system;
  }

  canHandle(dragType, dropType, dragElement, dropElement) {
    return dragType === 'tag-group' && dropType === 'drop-zone';
  }

  async handleDrop(event, dropElement, draggedElements) {
    event.preventDefault();
    dropElement.classList.remove('drag-over');

    for (const groupElement of draggedElements) {
      // Expand group to individual tags
      const memberTags = this.system.expandGroupTag(groupElement);

      // Move each member to zone
      for (const tagElement of memberTags) {
        const tagToZone = new TagToZoneHandler(this.system);
        await tagToZone.handleDrop(event, dropElement, [tagElement]);
      }
    }
  }

  mutatesTagsInPlay() {
    return true;
  }

  requiresRerender() {
    return true;
  }
}

/**
 * Tag Group → Card Tags Handler
 * ADD all group members to card
 */
class GroupToCardHandler extends DropHandler {
  constructor(system) {
    super();
    this.system = system;
  }

  canHandle(dragType, dropType, dragElement, dropElement) {
    return dragType === 'tag-group' && dropType === 'card-tags';
  }

  async handleDrop(event, dropElement, draggedElements) {
    event.preventDefault();
    dropElement.classList.remove('drag-over');

    for (const groupElement of draggedElements) {
      // Expand group to individual tags
      const memberTags = this.system.expandGroupTag(groupElement);

      // Add each member to card
      for (const tagElement of memberTags) {
        const tagToCard = new TagToCardHandler(this.system);
        await tagToCard.handleDrop(event, dropElement, [tagElement]);
      }
    }
  }

  mutatesTagsInPlay() {
    return false;
  }

  requiresRerender() {
    return false;
  }
}

class SpatialDragDrop {
  constructor() {
    this.selectedTags = new Set();
    this.draggedElements = [];
    this.stateCache = null;
    this.stateCacheTime = 0;
    this.CACHE_DURATION = 1000; // 1 second cache
    this.listeners = new WeakMap();
    this.renderDebounceTimer = null;
    this.DEBOUNCE_DELAY = 100;
    this.registry = new DropTargetRegistry(this); // Polymorphic handler registry

    // Multi-selection state management
    this.selectionState = {
      selectedTags: new Set(), // Set of tag element references for O(1) operations
      selectionMode: 'single', // 'single' | 'range' | 'toggle'
      anchorTag: null, // For shift-selection range operations
      lastSelectedTag: null, // For range operations
      lastShiftClickedTag: null, // Track last Shift+clicked tag for toggle detection
      selectionBounds: null, // For lasso selection (future)
      isDragging: false, // Selection lock during drag operations
      selectionMetadata: {
        selectionStartTime: null,
        selectionMethod: 'click', // 'click' | 'keyboard' | 'lasso'
        selectionCount: 0,
        selectionSequence: [] // Order of selection for undo
      }
    };

    // Ghost image configuration
    this.ghostImageConfig = {
      maxVisibleTags: 5, // Show first N tags in ghost
      thumbnailSize: { width: 200, height: 100 },
      opacity: 0.7,
      offset: { x: 10, y: 10 }, // Cursor offset
      canvas: {
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderRadius: 8,
        padding: 10,
        tagSpacing: 5,
        font: '14px Inter, system-ui, sans-serif',
        textColor: '#2c3e50',
        badgeColor: '#3498db'
      }
    };

    // Ghost image state
    this.currentGhostCanvas = null;
    this.currentGhostImage = null;
  }

  // ============================================================
  // MULTI-SELECTION STATE MANAGEMENT
  // Set-based O(1) operations for selection management
  // ============================================================

  /**
   * Add tag to current selection with O(1) performance
   * Updates visual state and maintains selection metadata
   */
  addToSelection(tag) {
    if (!tag || !tag.dataset || !tag.dataset.tag) {
      return;
    }

    this.selectionState.selectedTags.add(tag);
    tag.classList.add('tag-selected');
    tag.setAttribute('aria-selected', 'true');

    // Update metadata
    this.selectionState.selectionMetadata.selectionCount++;
    this.selectionState.selectionMetadata.selectionSequence.push(tag);
    this.selectionState.lastSelectedTag = tag;

    // Dispatch event for group UI integration
    document.dispatchEvent(new CustomEvent('tag-selected', {
      detail: {
        tagId: tag.dataset.tagId || tag.dataset.tag,
        tagElement: tag
      }
    }));

    // Announce to screen readers
    this.announceSelection(`Added ${tag.dataset.tag} to selection`);
  }

  /**
   * Remove tag from selection with O(1) performance
   */
  removeFromSelection(tag) {
    if (!tag || !this.selectionState.selectedTags.has(tag)) {
      return;
    }

    this.selectionState.selectedTags.delete(tag);
    tag.classList.remove('tag-selected');
    tag.setAttribute('aria-selected', 'false');

    // Update metadata
    this.selectionState.selectionMetadata.selectionCount--;
    const sequenceIndex = this.selectionState.selectionMetadata.selectionSequence.indexOf(tag);
    if (sequenceIndex > -1) {
      this.selectionState.selectionMetadata.selectionSequence.splice(sequenceIndex, 1);
    }

    // Dispatch event for group UI integration
    document.dispatchEvent(new CustomEvent('tag-deselected', {
      detail: {
        tagId: tag.dataset.tagId || tag.dataset.tag,
        tagElement: tag
      }
    }));

    // Announce to screen readers
    this.announceSelection(`Removed ${tag.dataset.tag} from selection`);
  }

  /**
   * Clear entire selection and reset state
   */
  clearSelection() {
    this.selectionState.selectedTags.forEach(tag => {
      tag.classList.remove('tag-selected');
      tag.setAttribute('aria-selected', 'false');
    });

    this.selectionState.selectedTags.clear();
    this.selectionState.selectionMetadata.selectionCount = 0;
    this.selectionState.selectionMetadata.selectionSequence = [];
    this.selectionState.lastSelectedTag = null;
    this.selectionState.anchorTag = null;

    // Legacy compatibility - also clear old selectedTags set
    this.selectedTags.clear();

    // Dispatch event for group UI integration
    document.dispatchEvent(new CustomEvent('selection-cleared'));
  }

  /**
   * Toggle tag selection state (XOR operation)
   */
  toggleTagSelection(tag) {
    if (!tag) return;

    if (this.selectionState.selectedTags.has(tag)) {
      this.removeFromSelection(tag);
    } else {
      this.addToSelection(tag);
    }
  }

  /**
   * Select range of tags between anchor and target
   * Uses DOM order for determining range boundaries
   */
  selectRange(anchor, target) {
    if (!anchor || !target) return;

    const allTags = Array.from(document.querySelectorAll('[data-tag]'));
    const anchorIndex = allTags.indexOf(anchor);
    const targetIndex = allTags.indexOf(target);

    if (anchorIndex === -1 || targetIndex === -1) return;

    const start = Math.min(anchorIndex, targetIndex);
    const end = Math.max(anchorIndex, targetIndex);

    this.clearSelection();
    for (let i = start; i <= end; i++) {
      this.addToSelection(allTags[i]);
    }

    const count = end - start + 1;
    this.announceSelection(`${count} tags selected`);
  }

  /**
   * Handle tag selection based on click modifiers
   * Implements single, range (Shift), and toggle (Ctrl/Cmd) selection
   */
  handleSelectionClick(event, tag) {
    if (!tag) return;

    // Record performance
    const startTime = performance.now();

    if (event.shiftKey) {
      // Shift+click: Range selection
      // Special case: if clicking the same tag twice in a row, toggle it off
      const lastTag = this.selectionState.lastShiftClickedTag;
      const isConsecutiveClick = lastTag && lastTag.dataset.tag === tag.dataset.tag;
      const isSelected = this.selectionState.selectedTags.has(tag);

      if (isConsecutiveClick && isSelected) {
        this.toggleTagSelection(tag);
      } else {
        const anchor = this.selectionState.anchorTag || tag;
        this.selectRange(anchor, tag);
      }
      this.selectionState.lastShiftClickedTag = tag;
    } else if (event.ctrlKey || event.metaKey) {
      // Ctrl/Cmd+click: Toggle selection
      this.toggleTagSelection(tag);
      if (!this.selectionState.anchorTag) {
        this.selectionState.anchorTag = tag;
      }
      this.selectionState.lastShiftClickedTag = null; // Clear on non-Shift click
    } else {
      // Regular click: Clear and select single
      this.clearSelection();
      this.addToSelection(tag);
      this.selectionState.anchorTag = tag;
      this.selectionState.lastShiftClickedTag = null; // Clear on non-Shift click
    }

    // Update ARIA states for all tags
    this.updateARIAStates();

    // Performance monitoring
    const duration = performance.now() - startTime;
    if (duration > 5) {
      console.warn(`Selection operation took ${duration.toFixed(2)}ms (target: <5ms)`);
    }
  }

  /**
   * Update ARIA attributes for all tags based on selection
   * Maintains proper ARIA attributes for accessibility tools
   */
  updateARIAStates() {
    document.querySelectorAll('[data-tag]').forEach(tag => {
      const isSelected = this.selectionState.selectedTags.has(tag);
      tag.setAttribute('aria-selected', isSelected.toString());

      if (isSelected) {
        tag.classList.add('tag-selected');
      } else {
        tag.classList.remove('tag-selected');
      }
    });

    // Announce selection summary
    const count = this.selectionState.selectedTags.size;
    if (count > 0) {
      this.announceSelection(`${count} tag${count > 1 ? 's' : ''} selected`);
    }
  }

  /**
   * Announce message to screen readers via live region
   */
  announceSelection(message) {
    const announcer = document.getElementById('selection-announcer');
    if (announcer) {
      // Clear and set for proper announcement
      announcer.textContent = '';

      // Use setTimeout to ensure change is detected
      setTimeout(() => {
        announcer.textContent = message;
      }, 10);

      // Clear after announcement
      setTimeout(() => {
        announcer.textContent = '';
      }, 1000);
    }
  }

  /**
   * Initialize accessibility support for multi-selection
   * Sets up ARIA states, live region, and keyboard navigation
   */
  initializeAccessibility() {
    // Set container as multi-selectable
    const tagContainers = document.querySelectorAll('.cloud, .tag-collection');
    tagContainers.forEach(container => {
      container.setAttribute('aria-multiselectable', 'true');
      container.setAttribute('role', 'listbox');
    });

    // Initialize all tags with ARIA states and keyboard handlers
    document.querySelectorAll('[data-tag]').forEach(tag => {
      tag.setAttribute('role', 'option');
      tag.setAttribute('aria-selected', 'false');
      tag.setAttribute('tabindex', '0');

      // Add keyboard navigation handler
      tag.addEventListener('keydown', (event) => this.handleTagKeyboard(event));
    });

    // Create live region for announcements if it doesn't exist
    let liveRegion = document.getElementById('selection-announcer');
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = 'selection-announcer';
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.className = 'sr-only';
      document.body.appendChild(liveRegion);
    }

    // Set up global keyboard shortcuts
    document.addEventListener('keydown', (event) => this.handleGlobalKeyboard(event));
  }

  /**
   * Handle keyboard navigation for tag selection
   * Implements arrow keys, space/enter selection, and modifiers
   */
  handleTagKeyboard(event) {
    const tag = event.target;
    const allTags = Array.from(document.querySelectorAll('[data-tag]'));
    const currentIndex = allTags.indexOf(tag);

    if (currentIndex === -1) return;

    let handled = true;

    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        const nextIndex = Math.min(currentIndex + 1, allTags.length - 1);
        const nextTag = allTags[nextIndex];

        if (nextTag) {
          nextTag.focus();
          this.ensureFocusVisible(nextTag);

          if (event.shiftKey) {
            this.addToSelection(nextTag);
            this.updateARIAStates();
          }
        }
        break;

      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        const prevIndex = Math.max(currentIndex - 1, 0);
        const prevTag = allTags[prevIndex];

        if (prevTag) {
          prevTag.focus();
          this.ensureFocusVisible(prevTag);

          if (event.shiftKey) {
            this.addToSelection(prevTag);
            this.updateARIAStates();
          }
        }
        break;

      case ' ':
      case 'Enter':
        event.preventDefault();

        if (event.ctrlKey || event.metaKey) {
          // Ctrl/Cmd+Space/Enter: Toggle selection
          this.toggleTagSelection(tag);
          const action = this.selectionState.selectedTags.has(tag) ? 'added' : 'removed';
          this.announceSelectionChange(action, tag);
        } else if (event.shiftKey) {
          // Shift+Space/Enter: Range selection
          const anchor = this.selectionState.anchorTag || tag;
          this.selectRange(anchor, tag);
        } else {
          // Regular Space/Enter: Clear and select
          this.clearSelection();
          this.addToSelection(tag);
          this.selectionState.anchorTag = tag;
          this.announceSelectionChange('selected', tag);
        }

        this.updateARIAStates();
        break;

      case 'Escape':
        this.clearSelection();
        this.updateARIAStates();
        this.announceSelection('Selection cleared');
        break;

      default:
        handled = false;
    }

    if (handled) {
      event.stopPropagation();
    }
  }

  /**
   * Handle global keyboard shortcuts
   * Implements Ctrl/Cmd+A for select all
   */
  handleGlobalKeyboard(event) {
    // Select all: Ctrl/Cmd+A
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'a') {
      const target = event.target;

      // Only handle if focus is in tag area
      if (target.closest('.cloud') || target.closest('.tag-collection') || target.hasAttribute('data-tag')) {
        event.preventDefault();
        this.selectAllTags();
      }
    }
  }

  /**
   * Select all visible tags in the current container
   */
  selectAllTags() {
    const allTags = document.querySelectorAll('[data-tag]:not([hidden])');

    this.clearSelection();
    allTags.forEach(tag => {
      this.addToSelection(tag);
    });

    this.updateARIAStates();
    this.announceSelection(`All ${allTags.length} tags selected`);
  }

  /**
   * Announce individual selection change with specific action
   */
  announceSelectionChange(action, tag) {
    const tagName = tag.dataset.tag;

    const messages = {
      'added': `${tagName} added to selection`,
      'removed': `${tagName} removed from selection`,
      'selected': `${tagName} selected`
    };

    const message = messages[action] || `${tagName} ${action}`;
    this.announceSelection(message);
  }

  /**
   * Ensure focused element is visible in viewport
   * Scrolls element into view if needed
   */
  ensureFocusVisible(element) {
    const rect = element.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    const isVisible = (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= viewportHeight &&
      rect.right <= viewportWidth
    );

    if (!isVisible) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'nearest'
      });
    }
  }

  // Initialize the entire system
  initialize() {
    this.initializeZones();
    this.initializeControls();
    this.initializeTagDragging();
    this.setupCardTagEventDelegation();
    this.startTagCountPolling();
    this.observeZoneChanges();
    this.initializeAccessibility(); // NEW: Initialize accessibility for multi-selection

    // Initial render
    this.updateStateAndRender();
  }

  // Derive state with caching
  deriveStateFromDOM() {
    // Check cache
    const now = Date.now();
    if (this.stateCache && (now - this.stateCacheTime) < this.CACHE_DURATION) {
      return this.stateCache;
    }

    const state = {
      zones: this.discoverZones(),
      controls: this.getRenderingControls(),
      currentLesson: this.getCurrentLesson()
    };

    // Update cache
    this.stateCache = state;
    this.stateCacheTime = now;

    return state;
  }

  // Get current lesson from URL parameters or localStorage
  getCurrentLesson() {
    // First check URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const lessonParam = urlParams.get('lesson');
    if (lessonParam) {
      return parseInt(lessonParam, 10);
    }

    // Fallback to localStorage
    const storedLesson = localStorage.getItem('currentLesson');
    if (storedLesson) {
      return parseInt(storedLesson, 10);
    }

    // Default to lesson 1
    return 1;
  }

  // Discover zones with null checks
  discoverZones() {
    const zones = {};

    const zoneElements = document.querySelectorAll('[data-zone-type]:not([data-zone-type="tag-cloud"])');
    if (!zoneElements || zoneElements.length === 0) {
      return zones;
    }

    zoneElements.forEach(zone => {
      const zoneType = zone.dataset.zoneType;
      if (!zoneType) return;

      const tags = [];
      const collection = zone.querySelector('.tag-collection');

      if (collection) {
        collection.querySelectorAll('[data-tag]').forEach(tag => {
          const tagName = tag.dataset.tag;
          if (tagName) tags.push(tagName);
        });
      }

      zones[zoneType] = {
        tags: tags,
        metadata: this.getZoneMetadata(zone)
      };
    });

    return zones;
  }

  // Get zone metadata with defaults
  getZoneMetadata(zoneElement) {
    if (!zoneElement) return {};

    return {
      label: zoneElement.querySelector('.zone-label')?.textContent || '',
      accepts: zoneElement.dataset.accepts?.split(',') || ['tags'],
      position: zoneElement.dataset.position || 'static',
      maxTags: this.parseMaxTags(zoneElement.dataset.maxTags),
      behavior: zoneElement.dataset.behavior || 'standard',
      temporalRange: zoneElement.dataset.temporalRange || null
    };
  }

  // Safely parse maxTags
  parseMaxTags(value) {
    if (!value) return null;
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? null : parsed;
  }

  // Get rendering controls with defaults
  getRenderingControls() {
    const controls = {};

    const controlElements = document.querySelectorAll('[data-affects-rendering="true"]');
    if (!controlElements || controlElements.length === 0) {
      return {
        startWithAllCards: false,
        startWithCardsExpanded: true,
        showColors: true,
        colorPalette: 'muji'
      };
    }

    controlElements.forEach(control => {
      const key = control.id || control.name || control.dataset.controlKey;
      if (!key) return;

      if (control.type === 'checkbox') {
        controls[key] = control.checked || false;
      } else if (control.tagName === 'SELECT') {
        controls[key] = control.value || '';
      } else if (control.type === 'radio' && control.checked) {
        controls[control.name] = control.value || '';
      }
    });

    // Apply show-colors class to body when showColors is enabled
    if (controls.showColors) {
      document.body.classList.add('show-colors');
    } else {
      document.body.classList.remove('show-colors');
    }

    // Apply color palette data attribute to body
    if (controls.colorPalette) {
      document.body.setAttribute('data-palette', controls.colorPalette);
    }

    return controls;
  }

  // Initialize zones with polymorphic event delegation
  initializeZones() {
    const container = document.body; // Universal delegation

    // Drop handler with debouncing to prevent rapid repeated drops
    const handleDrop = debounce(async (e) => {
      e.preventDefault();
      e.stopPropagation();

      if (!this.draggedElements || this.draggedElements.length === 0) {
        return;
      }

      const dropTarget = this.findDropTarget(e.target);
      if (!dropTarget) {
        return;
      }

      // Use batch dispatch for multi-element operations
      let result;
      if (this.draggedElements.length > 1) {
        result = await this.dispatchBatchOperation(this.draggedElements, dropTarget, e);
      } else {
        // Single element - use direct handler
        const handler = this.registry.findHandler(this.draggedElements[0], dropTarget);

        if (handler && handler.validate(this.draggedElements[0], dropTarget)) {
          await handler.handleDrop(e, dropTarget, this.draggedElements);
          result = { success: true };
        } else {
          result = { success: false };
        }
      }

      // Cleanup dragged elements
      this.draggedElements.forEach(el => {
        el.classList.remove('dragging');
        el.setAttribute('aria-grabbed', 'false');
      });

      const handler = this.registry.findHandler(this.draggedElements[0], dropTarget);
      this.draggedElements = [];

      // Clear selection after successful drop
      if (result.success) {
        this.clearSelection();

        // Update state if handler mutates tagsInPlay
        if (handler && (handler.mutatesTagsInPlay() || handler.requiresRerender())) {
          this.invalidateCache();
          this.updateStateAndRender();
        }
      }
    }, 100); // 100ms debounce

    // Drop event - polymorphic dispatch
    container.addEventListener('drop', handleDrop, false);

    // Dragover event - polymorphic dispatch
    container.addEventListener('dragover', (e) => {
      if (!this.draggedElements || this.draggedElements.length === 0) return;

      const dropTarget = this.findDropTarget(e.target);
      if (!dropTarget) return;

      const handler = this.registry.findHandler(this.draggedElements[0], dropTarget);

      if (handler && handler.validate(this.draggedElements[0], dropTarget)) {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer) {
          e.dataTransfer.dropEffect = 'move';
        }
        dropTarget.classList.add('drag-over');
      }
    });

    // Dragleave event - polymorphic dispatch
    container.addEventListener('dragleave', (e) => {
      const dropTarget = this.findDropTarget(e.target);
      if (!dropTarget) return;

      const handler = this.registry.findHandler(
        this.draggedElements[0],
        dropTarget
      );

      if (handler) {
        handler.handleDragLeave(e, dropTarget, this.draggedElements);
      }
    });
  }

  // Find closest droppable element
  findDropTarget(element) {
    // Check for specific drop targets in priority order
    const target = element.closest('.cloud') ||
                   element.closest('.card-tags') ||
                   element.closest('[data-zone-type]:not([data-zone-type="tag-cloud"])') ||
                   element.closest('.control-area-container') ||
                   element.closest('[data-type="group-tag"]') ||
                   element.closest('.grid-cell') ||
                   null;

    return target;
  }

  // Initialize tag dragging with event delegation
  initializeTagDragging() {
    const tagContainer = document.body;

    // Drag start - use capture phase to run before zone's inline handler
    tagContainer.addEventListener('dragstart', (e) => {
      if (e.target.matches('[data-tag]')) {
        this.handleTagDragStart(e);
      }
    }, true); // Capture phase

    // Drag end
    tagContainer.addEventListener('dragend', (e) => {
      if (e.target.matches('[data-tag]')) {
        this.handleTagDragEnd(e);
      }
    });

    // Click for selection
    tagContainer.addEventListener('click', (e) => {
      if (e.target.matches('[data-tag]')) {
        this.handleTagClick(e);
      }
    });

    // Card dragging
    tagContainer.addEventListener('dragstart', (e) => {
      if (e.target.matches('.card-item')) {
        this.handleCardDragStart(e);
      }
    }, true); // Capture phase

    tagContainer.addEventListener('dragend', (e) => {
      if (e.target.matches('.card-item')) {
        this.handleCardDragEnd(e);
      }
    });

    // Set draggable on all tags and add ARIA
    document.querySelectorAll('[data-tag]').forEach(tag => {
      tag.draggable = true;
      tag.setAttribute('role', 'button');
      tag.setAttribute('aria-grabbed', 'false');
      tag.setAttribute('tabindex', '0');
    });
  }

  // ============================================================
  // GHOST IMAGE GENERATION
  // Canvas-based composite ghost image for multi-tag drag operations
  // ============================================================

  /**
   * Generate composite ghost image for selected tags
   * Creates canvas rendering with tag preview and count badge
   * Target: <16ms for 60 FPS performance
   */
  generateGhostImage(selectedTags) {
    const startTime = performance.now();

    // Check if canvas is supported
    if (!this.canUseCanvas()) {
      return this.createFallbackGhostImage(selectedTags);
    }

    const config = this.ghostImageConfig;
    const tagCount = selectedTags.size;
    const visibleTags = Array.from(selectedTags).slice(0, config.maxVisibleTags);

    // Create canvas
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      return this.createFallbackGhostImage(selectedTags);
    }

    // Set canvas dimensions
    canvas.width = config.thumbnailSize.width;
    canvas.height = config.thumbnailSize.height;

    // Draw background with rounded corners
    ctx.fillStyle = config.canvas.backgroundColor;
    ctx.beginPath();
    this.roundRect(ctx, 0, 0, canvas.width, canvas.height, config.canvas.borderRadius);
    ctx.fill();

    // Draw tag previews
    ctx.font = config.canvas.font;
    let yOffset = config.canvas.padding;
    const tagHeight = 24;

    visibleTags.forEach((tag, index) => {
      const tagText = tag.dataset.tag || 'unknown';
      const tagType = tag.dataset.type || 'user-tag';

      // Draw tag background
      const tagColor = this.getTagColor(tagType);
      ctx.fillStyle = tagColor;
      ctx.beginPath();
      this.roundRect(
        ctx,
        config.canvas.padding,
        yOffset,
        canvas.width - 2 * config.canvas.padding,
        tagHeight,
        4
      );
      ctx.fill();

      // Draw tag text
      ctx.fillStyle = '#ffffff';
      ctx.textBaseline = 'middle';
      const truncatedText = this.truncateText(
        ctx,
        tagText,
        canvas.width - 2 * config.canvas.padding - 16
      );
      ctx.fillText(
        truncatedText,
        config.canvas.padding + 8,
        yOffset + tagHeight / 2
      );

      yOffset += tagHeight + config.canvas.tagSpacing;
    });

    // Draw count badge if more tags than visible
    if (tagCount > config.maxVisibleTags) {
      const badgeX = canvas.width - 30;
      const badgeY = canvas.height - 30;
      const overflowCount = tagCount - config.maxVisibleTags;

      // Draw circle
      ctx.fillStyle = config.canvas.badgeColor;
      ctx.beginPath();
      ctx.arc(badgeX, badgeY, 20, 0, Math.PI * 2);
      ctx.fill();

      // Draw count text
      ctx.fillStyle = '#ffffff';
      ctx.font = '12px Inter, system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`+${overflowCount}`, badgeX, badgeY);
    }

    // Set canvas opacity
    canvas.style.opacity = config.opacity.toString();

    // Performance monitoring
    const duration = performance.now() - startTime;
    if (duration > 16) {
      console.warn(`Ghost image generation took ${duration.toFixed(2)}ms (target: <16ms)`);
    }

    return canvas;
  }

  /**
   * Helper to draw rounded rectangle (for browsers without roundRect)
   */
  roundRect(ctx, x, y, width, height, radius) {
    if (typeof ctx.roundRect === 'function') {
      ctx.roundRect(x, y, width, height, radius);
    } else {
      // Manual rounded rectangle
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + width - radius, y);
      ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
      ctx.lineTo(x + width, y + height - radius);
      ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
      ctx.lineTo(x + radius, y + height);
      ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
    }
  }

  /**
   * Get color for tag type
   */
  getTagColor(tagType) {
    const colors = {
      'user-tag': '#3498db',
      'ai-tag': '#9b59b6',
      'system-tag': '#e74c3c',
      'group-tag': '#2ecc71'
    };
    return colors[tagType] || '#95a5a6';
  }

  /**
   * Truncate text to fit within width
   */
  truncateText(ctx, text, maxWidth) {
    const metrics = ctx.measureText(text);
    if (metrics.width <= maxWidth) {
      return text;
    }

    const ellipsis = '...';
    for (let i = text.length; i > 0; i--) {
      const truncated = text.substring(0, i) + ellipsis;
      if (ctx.measureText(truncated).width <= maxWidth) {
        return truncated;
      }
    }

    return ellipsis;
  }

  /**
   * Check if browser supports canvas
   */
  canUseCanvas() {
    try {
      const canvas = document.createElement('canvas');
      return !!(canvas.getContext && canvas.getContext('2d'));
    } catch (e) {
      return false;
    }
  }

  /**
   * Create DOM-based fallback ghost for browsers without canvas support
   */
  createFallbackGhostImage(selectedTags) {
    const ghost = document.createElement('div');
    ghost.className = 'ghost-image-fallback';
    ghost.style.cssText = `
      position: fixed;
      padding: 10px;
      background: rgba(255, 255, 255, 0.9);
      border: 2px solid #3498db;
      border-radius: 8px;
      pointer-events: none;
      z-index: 10000;
      font-family: Inter, system-ui, sans-serif;
    `;

    // Add count
    const count = document.createElement('div');
    const tagCount = selectedTags.size;
    count.textContent = `${tagCount} tag${tagCount > 1 ? 's' : ''} selected`;
    count.style.fontWeight = 'bold';
    ghost.appendChild(count);

    // Show first few tag names
    const previewTags = Array.from(selectedTags).slice(0, 3);
    if (previewTags.length > 0) {
      const preview = document.createElement('div');
      preview.style.fontSize = '0.9em';
      preview.style.marginTop = '5px';

      const names = previewTags.map(t => t.dataset.tag).join(', ');
      preview.textContent = names;

      if (selectedTags.size > 3) {
        preview.textContent += ` and ${selectedTags.size - 3} more`;
      }

      ghost.appendChild(preview);
    }

    document.body.appendChild(ghost);
    return ghost;
  }

  /**
   * Attach ghost image to drag event
   * Manages canvas lifecycle and memory cleanup
   */
  attachGhostImage(event, selectedTags) {
    // Clean up any existing ghost
    this.cleanupGhostImage();

    // Generate ghost canvas
    this.currentGhostCanvas = this.generateGhostImage(selectedTags);

    // Convert canvas to image for drag image
    const ghostImage = new Image();

    if (this.currentGhostCanvas instanceof HTMLCanvasElement) {
      ghostImage.src = this.currentGhostCanvas.toDataURL();
    } else {
      // Fallback DOM element - can't use as drag image directly
      // Browser will use default drag image
      return;
    }

    this.currentGhostImage = ghostImage;

    // Set drag image once loaded
    ghostImage.onload = () => {
      if (event.dataTransfer && event.dataTransfer.setDragImage) {
        event.dataTransfer.setDragImage(
          ghostImage,
          this.ghostImageConfig.offset.x,
          this.ghostImageConfig.offset.y
        );
      }
    };
  }

  /**
   * Clean up ghost image resources
   */
  cleanupGhostImage() {
    if (this.currentGhostCanvas) {
      if (this.currentGhostCanvas instanceof HTMLCanvasElement) {
        // Clear canvas context to free memory
        const ctx = this.currentGhostCanvas.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, this.currentGhostCanvas.width, this.currentGhostCanvas.height);
        }
      } else if (this.currentGhostCanvas.parentElement) {
        // Remove DOM fallback element
        this.currentGhostCanvas.remove();
      }
      this.currentGhostCanvas = null;
    }

    if (this.currentGhostImage) {
      this.currentGhostImage.src = '';
      this.currentGhostImage = null;
    }
  }

  // ============================================================
  // BATCH OPERATIONS
  // Batch polymorphic dispatch with atomicity and rollback
  // ============================================================

  /**
   * Dispatch batch drag-drop operation with atomicity
   * Maintains individual tag semantics while processing as batch
   */
  async dispatchBatchOperation(draggedElements, dropTarget, event) {
    // Start performance tracking
    const startTime = performance.now();

    // Find appropriate handler
    const handler = this.registry.findHandler(draggedElements[0], dropTarget);
    if (!handler) {
      this.showBatchError(['No handler found for drop target']);
      return { success: false, errors: ['No handler found'] };
    }

    // Validate batch operation
    const validation = handler.validateBatch(draggedElements, dropTarget);
    if (!validation.valid) {
      this.showBatchError(validation.errors);
      return { success: false, errors: validation.errors };
    }

    // Show progress for large batches
    let progress = null;
    if (draggedElements.length > 10) {
      progress = this.showBatchProgress(draggedElements.length);
    }

    try {
      // Create batch operation payload for rollback
      const batchOp = this.prepareBatchOperation(draggedElements, dropTarget);

      // Execute batch operation
      let result;
      if (handler.supportsBatch()) {
        // Use optimized batch handler
        result = await handler.handleBatchDrop(event, dropTarget, draggedElements);
      } else {
        // Fall back to sequential processing
        result = await this.processBatchWithProgress(
          handler,
          event,
          dropTarget,
          draggedElements,
          progress
        );
      }

      // Check performance
      const duration = performance.now() - startTime;
      if (draggedElements.length >= 50 && duration > 500) {
        console.warn(`Large batch operation took ${duration.toFixed(2)}ms (target: <500ms for 50 tags)`);
      }

      // Show errors if any
      if (result.errors && result.errors.length > 0) {
        this.showBatchError(result.errors);
      }

      return result;

    } catch (error) {
      console.error('Batch operation failed:', error);

      // Rollback changes
      await this.rollbackBatchOperation(batchOp);

      this.showBatchError(['Operation failed. Changes have been rolled back.']);
      return { success: false, errors: [error.message] };

    } finally {
      if (progress) {
        progress.close();
      }
    }
  }

  /**
   * Prepare batch operation payload for rollback
   */
  prepareBatchOperation(draggedElements, dropTarget) {
    return {
      operationId: `batch-${Date.now()}-${Math.random().toString(36).substring(7)}`,
      timestamp: Date.now(),
      tags: draggedElements.map(element => ({
        element: element,
        tagId: element.dataset.tagId,
        tagName: element.dataset.tag,
        tagType: element.dataset.type,
        sourceZone: element.closest('[data-zone-type]')?.dataset.zoneType ||
                   element.closest('.cloud')?.dataset.cloudType ||
                   'unknown',
        sourceParent: element.parentElement
      })),
      targetZone: dropTarget.dataset.zoneType ||
                  dropTarget.dataset.cloudType ||
                  dropTarget.classList.contains('card-tags') ? 'card-tags' : 'unknown'
    };
  }

  /**
   * Process batch with progress updates
   */
  async processBatchWithProgress(handler, event, dropTarget, draggedElements, progress) {
    const total = draggedElements.length;
    let completed = 0;
    const errors = [];
    const successful = [];

    for (const element of draggedElements) {
      try {
        if (handler.validate(element, dropTarget)) {
          await handler.handleDrop(event, dropTarget, [element]);
          completed++;
          successful.push(element);

          // Update progress
          if (progress) {
            progress.update(completed, total);
          }
        } else {
          const tagName = element.dataset.tag || 'unknown';
          errors.push(`Cannot drop ${tagName} here`);
        }
      } catch (error) {
        const tagName = element.dataset.tag || 'unknown';
        errors.push(`Failed to process ${tagName}: ${error.message}`);
      }
    }

    return {
      success: errors.length === 0,
      completed,
      total,
      errors,
      successful
    };
  }

  /**
   * Rollback failed batch operation
   */
  async rollbackBatchOperation(batchOp) {
    console.log(`Rolling back batch operation ${batchOp.operationId}`);

    // Restore each tag to original position
    for (const tagInfo of batchOp.tags) {
      if (tagInfo.sourceParent && tagInfo.element) {
        try {
          // Move tag back to source
          tagInfo.sourceParent.appendChild(tagInfo.element);

          // Restore original classes
          tagInfo.element.classList.remove('tag-active', 'dragging', 'tag-selected');

          if (tagInfo.sourceZone === 'unknown' || tagInfo.sourceZone.includes('cloud')) {
            tagInfo.element.classList.add('tag-cloud');
          } else {
            tagInfo.element.classList.add('tag-active');
          }
        } catch (error) {
          console.error(`Failed to rollback tag ${tagInfo.tagName}:`, error);
        }
      }
    }
  }

  /**
   * Show progress indicator for batch operations
   */
  showBatchProgress(total) {
    const progressContainer = document.createElement('div');
    progressContainer.className = 'batch-progress';
    progressContainer.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(255, 255, 255, 0.95);
      border: 2px solid #3498db;
      border-radius: 8px;
      padding: 20px;
      z-index: 10000;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      min-width: 300px;
    `;

    const message = document.createElement('div');
    message.textContent = `Processing ${total} tags...`;
    message.style.cssText = `
      font-weight: bold;
      margin-bottom: 10px;
      font-family: Inter, system-ui, sans-serif;
    `;

    const progressBar = document.createElement('div');
    progressBar.style.cssText = `
      width: 100%;
      height: 20px;
      background: #ecf0f1;
      border-radius: 10px;
      overflow: hidden;
    `;

    const progressFill = document.createElement('div');
    progressFill.style.cssText = `
      width: 0%;
      height: 100%;
      background: #3498db;
      transition: width 0.3s ease;
    `;

    const progressText = document.createElement('div');
    progressText.textContent = '0 / ' + total;
    progressText.style.cssText = `
      margin-top: 10px;
      text-align: center;
      font-family: Inter, system-ui, sans-serif;
      color: #666;
    `;

    progressBar.appendChild(progressFill);
    progressContainer.appendChild(message);
    progressContainer.appendChild(progressBar);
    progressContainer.appendChild(progressText);
    document.body.appendChild(progressContainer);

    return {
      update: (current, total) => {
        const percentage = (current / total) * 100;
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${current} / ${total}`;
      },
      close: () => {
        progressContainer.remove();
      }
    };
  }

  /**
   * Display batch operation errors to user
   */
  showBatchError(errors) {
    // Create error notification
    const errorContainer = document.createElement('div');
    errorContainer.className = 'batch-error';
    errorContainer.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #e74c3c;
      color: white;
      padding: 15px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      z-index: 10000;
      max-width: 400px;
      font-family: Inter, system-ui, sans-serif;
    `;

    const title = document.createElement('div');
    title.textContent = 'Batch Operation Failed';
    title.style.cssText = `
      font-weight: bold;
      margin-bottom: 10px;
    `;

    const errorList = document.createElement('div');
    errorList.style.cssText = `
      font-size: 0.9em;
      max-height: 200px;
      overflow-y: auto;
    `;

    // Show first 5 errors
    const displayErrors = errors.slice(0, 5);
    displayErrors.forEach(error => {
      const errorItem = document.createElement('div');
      errorItem.textContent = `• ${error}`;
      errorItem.style.marginBottom = '5px';
      errorList.appendChild(errorItem);
    });

    // Show "and X more" if needed
    if (errors.length > 5) {
      const moreItem = document.createElement('div');
      moreItem.textContent = `... and ${errors.length - 5} more errors`;
      moreItem.style.cssText = `
        margin-top: 5px;
        font-style: italic;
        opacity: 0.8;
      `;
      errorList.appendChild(moreItem);
    }

    errorContainer.appendChild(title);
    errorContainer.appendChild(errorList);
    document.body.appendChild(errorContainer);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      errorContainer.remove();
    }, 5000);

    // Announce to screen readers
    this.announceSelection(`Batch operation failed: ${errors[0]}`);
  }

  // Handle tag drag start
  handleTagDragStart(event) {
    const draggedTag = event.target;

    // Validate it's actually a tag
    if (!draggedTag.dataset.tag) return;

    // Stop event from bubbling to zone's dragstart handler
    event.stopPropagation();

    // Lock selection during drag
    this.selectionState.isDragging = true;

    // Determine what's being dragged
    if (draggedTag.dataset.type === 'group-tag') {
      this.draggedElements = this.expandGroupTag(draggedTag);
    } else if (this.selectionState.selectedTags.has(draggedTag)) {
      // If dragged tag is part of selection, drag all selected tags
      this.draggedElements = Array.from(this.selectionState.selectedTags);
    } else {
      // If dragged tag not selected, drag only it and clear selection
      this.draggedElements = [draggedTag];
      this.clearSelection();
    }

    // Visual feedback
    this.draggedElements.forEach(el => {
      el.classList.add('dragging');
      el.setAttribute('aria-grabbed', 'true');
    });

    // Generate and attach ghost image for multi-tag selections
    if (this.draggedElements.length > 1) {
      const draggedSet = new Set(this.draggedElements);
      this.attachGhostImage(event, draggedSet);
    }

    // Set transfer data
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', this.draggedElements.length.toString());
  }

  // Handle tag drag end
  handleTagDragEnd(event) {
    this.draggedElements.forEach(el => {
      el.classList.remove('dragging');
      el.setAttribute('aria-grabbed', 'false');
    });
    this.draggedElements = [];

    // Clean up ghost image
    this.cleanupGhostImage();

    // Unlock selection after drag
    this.selectionState.isDragging = false;
  }

  // Handle card drag start
  handleCardDragStart(event) {
    const card = event.target.closest('.card-item');
    if (!card) return;

    card.classList.add('dragging');
    this.draggedElements = [card];

    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
    }
  }

  // Handle card drag end
  handleCardDragEnd(event) {
    const card = event.target.closest('.card-item');
    if (!card) return;

    card.classList.remove('dragging');
  }

  // Handle tag click for selection
  handleTagClick(event) {
    const tag = event.target.matches('[data-tag]') ? event.target : event.target.closest('[data-tag]');
    if (!tag) {
      return;
    }

    if (event.metaKey || event.ctrlKey || event.shiftKey) {
      event.preventDefault();
      this.handleSelectionClick(event, tag);
    } else {
      // Regular click: clear all and select only this tag
      event.preventDefault();
      this.clearSelection();
      this.addToSelection(tag);
    }
  }


  // Legacy method kept for backwards compatibility (now uses polymorphic handlers)
  moveTags(tagElements, targetZone) {
    // This method is deprecated - polymorphic handlers now handle all drops
    console.warn('moveTags() is deprecated - using polymorphic handler system');
  }

  // Expand group tag to individual tags
  expandGroupTag(groupTagElement) {
    const groupId = groupTagElement.dataset.group;
    const memberTags = groupTagElement.dataset.members?.split(',') || [];

    const tagElements = [];
    memberTags.forEach(tagName => {
      const tagElement = document.querySelector(`[data-tag="${tagName}"]`);
      if (tagElement) {
        tagElements.push(tagElement);
      }
    });

    return tagElements;
  }

  // Invalidate cache
  invalidateCache() {
    this.stateCache = null;
    this.stateCacheTime = 0;
  }

  // Update state and render with debouncing
  async updateStateAndRender() {
    // Clear existing timer
    if (this.renderDebounceTimer) {
      clearTimeout(this.renderDebounceTimer);
    }

    // Set new timer
    this.renderDebounceTimer = setTimeout(async () => {
      const tagsInPlay = this.deriveStateFromDOM();

      // Update display
      const tagsField = document.getElementById('tagsInPlay');
      if (tagsField) {
        tagsField.value = JSON.stringify(tagsInPlay, null, 2);
      }

      // Send to backend
      await this.renderCards(tagsInPlay);

      await this.updateLessonHint(tagsInPlay);
    }, this.DEBOUNCE_DELAY);
  }

  async updateLessonHint(tagsInPlay) {
    try {
      const params = new URLSearchParams();

      if (tagsInPlay.zones) {
        Object.entries(tagsInPlay.zones).forEach(([zoneType, zoneData]) => {
          if (zoneData.tags && Array.isArray(zoneData.tags)) {
            zoneData.tags.forEach(tag => {
              params.append(zoneType, tag);
            });
          }
        });
      }

      // Add completed lessons from localStorage
      const completedLessons = JSON.parse(localStorage.getItem('completedLessons') || '[]');
      if (completedLessons.length > 0) {
        params.append('completed', JSON.stringify(completedLessons));
      }

      // Fetch updated hint
      const response = await fetch(`/api/lessons/hint?${params}`);
      if (response.ok) {
        const hintHtml = await response.text();
        const instructionalText = document.getElementById('instructionalText');
        if (instructionalText) {
          instructionalText.innerHTML = hintHtml;

          // Check if lesson completion hint is showing
          if (hintHtml.includes('LESSON 1 COMPLETE')) {
            this.markLessonComplete(1);
            this.refreshLessonSelector();
          } else if (hintHtml.includes('LESSON 2 COMPLETE')) {
            this.markLessonComplete(2);
            this.refreshLessonSelector();
          }
        }
      }
    } catch (error) {
      console.warn('Failed to update lesson hint:', error);
    }
  }

  // Mark lesson as complete in localStorage
  markLessonComplete(lessonNumber) {
    try {
      const completedLessons = JSON.parse(localStorage.getItem('completedLessons') || '[]');
      if (!completedLessons.includes(lessonNumber)) {
        completedLessons.push(lessonNumber);
        localStorage.setItem('completedLessons', JSON.stringify(completedLessons));
      }
    } catch (error) {
      console.warn('Failed to save lesson completion:', error);
    }
  }

  // Refresh lesson selector to show updated status
  refreshLessonSelector() {
    try {
      // Update hidden input with completed lessons from localStorage
      const completedLessons = JSON.parse(localStorage.getItem('completedLessons') || '[]');
      const hiddenInput = document.getElementById('completedLessons');
      if (hiddenInput) {
        hiddenInput.value = JSON.stringify(completedLessons);
      }

      // Trigger HTMX reload
      const selector = document.getElementById('navLessonSelector');
      if (selector && typeof htmx !== 'undefined') {
        htmx.trigger(selector, 'load');
      }
    } catch (error) {
      console.warn('Failed to refresh lesson selector:', error);
    }
  }

  // Send to backend
  async renderCards(tagsInPlay) {
    try {
      // Get workspace context from DOM
      const workspaceId = this.getWorkspaceContext();

      const headers = { 'Content-Type': 'application/json' };
      if (workspaceId) {
        headers['X-Workspace-Id'] = workspaceId;
      }

      const response = await fetch('/api/render/cards', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ tagsInPlay })
      });

      if (response.ok) {
        const html = await response.text();
        const container = document.getElementById('cardContainer');
        if (container) {
          container.innerHTML = html;

          // Apply pending collapsed rows/columns after grid is rendered
          if (window.settingsManager) {
            window.settingsManager.applyPendingGridState();
          }
        }
      }
    } catch (error) {
      console.error('Failed to render cards:', error);
    }
  }

  // Get workspace context from DOM
  getWorkspaceContext() {
    const container = document.querySelector('[data-workspace]');
    return container ? container.dataset.workspace : null;
  }

  // Observe zone changes with scoped observer
  observeZoneChanges() {
    // With universal event delegation, we only need to observe for ARIA updates
    const container = document.querySelector('.zones-wrapper') ||
                     document.querySelector('.spatial-grid') ||
                     document.body;

    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === 1 && node.dataset?.zoneType) {
              this.addZoneARIA(node);
            }
          });
        }
      });
    });

    observer.observe(container, {
      childList: true,
      subtree: true
    });
  }

  // Add ARIA attributes to zones
  addZoneARIA(zoneElement) {
    if (!zoneElement) return;
    zoneElement.setAttribute('role', 'region');
    zoneElement.setAttribute('aria-label', zoneElement.dataset.zoneType + ' drop zone');
  }

  // Initialize controls
  initializeControls() {
    document.querySelectorAll('[data-affects-rendering="true"]').forEach(control => {
      const eventType = control.type === 'checkbox' ? 'change' :
                       control.tagName === 'SELECT' ? 'change' :
                       'input';

      control.addEventListener(eventType, () => {
        this.invalidateCache();
        this.updateStateAndRender();
      });

      // Apply immediate visual feedback if specified
      if (control.dataset.immediateVisual === 'true') {
        control.addEventListener('change', (e) => {
          this.applyImmediateVisualFeedback(control);
        });
      }
    });
  }

  // Apply immediate visual changes (before backend render)
  applyImmediateVisualFeedback(control) {
    const action = control.dataset.visualAction;
    if (!action) return;

    switch(action) {
      case 'toggle-class':
        const className = control.dataset.className;
        document.body.classList.toggle(className, control.checked);
        break;
      case 'show-hide':
        const targetId = control.dataset.targetId;
        const target = document.getElementById(targetId);
        if (target) {
          target.style.display = control.checked ? 'block' : 'none';
        }
        break;
    }
  }

  // Restore saved view by rearranging tags in DOM
  restoreView(tagsInPlay) {
    // First, move all tags back to their original clouds
    this.clearAllZones();

    // Then move tags to their saved positions
    if (tagsInPlay && tagsInPlay.zones) {
      Object.entries(tagsInPlay.zones).forEach(([zoneId, zoneData]) => {
        const zone = document.querySelector(`[data-zone-type="${zoneId}"]`);
        if (!zone) {
          console.warn(`Zone ${zoneId} not found`);
          return;
        }

        const zoneWrapper = zone.querySelector('.tags-wrapper') || zone.querySelector('.drop-zone-content');
        if (!zoneWrapper) {
          console.warn(`No wrapper found in zone ${zoneId}`);
          return;
        }

        // Move each tag to the zone
        if (zoneData.tags && Array.isArray(zoneData.tags)) {
          zoneData.tags.forEach(tagName => {
            const tag = document.querySelector(`[data-tag="${tagName}"]`);
            if (tag) {
              zoneWrapper.appendChild(tag);
            }
          });
        }
      });
    }

    // Update the tagsInPlay textarea
    const tagsTextarea = document.getElementById('tagsInPlay');
    if (tagsTextarea) {
      tagsTextarea.value = JSON.stringify(tagsInPlay, null, 2);
    }

    // Trigger card refresh with the restored state
    this.updateStateAndRender();
  }

  // Clear all zones (move tags back to clouds)
  clearAllZones() {
    const zones = document.querySelectorAll('.drop-zone');
    zones.forEach(zone => {
      const tags = zone.querySelectorAll('.tag');
      tags.forEach(tag => {
        // Find the appropriate cloud based on tag type
        const tagType = tag.dataset.type || 'tag';
        let cloud;

        if (tagType === 'ai-tag') {
          cloud = document.querySelector('.cloud-ai .tags-wrapper');
        } else if (tagType === 'group-tag') {
          cloud = document.querySelector('.cloud-group .tags-wrapper');
        } else if (tagType === 'system-tag') {
          cloud = document.querySelector('.cloud-system .tags-wrapper');
        } else {
          cloud = document.querySelector('.cloud-user .tags-wrapper');
        }

        if (cloud) {
          cloud.appendChild(tag);
        }
      });
    });
  }

  // Card and Tag Management Methods

  async createTag(tagName, cloudType = 'user') {
    try {
      const response = await fetch('/api/tags/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: tagName })
      });

      if (response.ok) {
        const data = await response.json();
        const cloud = document.querySelector(`.cloud-${cloudType} .tags-wrapper`);
        if (cloud) {
          // Count existing tags to determine color index
          const existingTags = cloud.querySelectorAll('.tag');
          const tagIndex = existingTags.length;

          const tagElement = document.createElement('span');
          tagElement.className = `tag tag-${cloudType}`;
          tagElement.setAttribute('data-tag', tagName);
          tagElement.setAttribute('data-tag-id', data.tag_id);
          tagElement.setAttribute('data-type', 'tag');
          tagElement.setAttribute('draggable', 'true');
          tagElement.id = `tag-${tagName}`;
          tagElement.style.setProperty('--tag-index', tagIndex);
          tagElement.innerHTML = `<span class="tag-color-dot"></span>${tagName} (0) <button class="tag-delete" data-tag-id="${data.tag_id}" title="Delete tag">×</button>`;
          cloud.appendChild(tagElement);
        }
        return data;
      }
    } catch (error) {
      console.error('Failed to create tag:', error);
    }
  }

  async removeTagFromCard(cardId, tagId, removeButton) {
    try {
      const response = await fetch('/api/cards/remove-tag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: cardId, tag_id: tagId })
      });

      if (response.ok) {
        const tagRep = removeButton.closest('.card-tag');
        const tagName = tagRep?.getAttribute('data-tag');
        const card = removeButton.closest('.card-item');
        if (tagRep) tagRep.remove();

        // Update card tag count
        if (card) {
          const cardTagsLabel = card.querySelector('.card-tags-label');
          if (cardTagsLabel) {
            const cardTagsContainer = card.querySelector('.card-tags');
            const remainingTagCount = cardTagsContainer ? cardTagsContainer.querySelectorAll('.card-tag').length : 0;
            const arrowSpan = cardTagsLabel.querySelector('.card-tags-arrow');
            if (arrowSpan) {
              cardTagsLabel.childNodes[0].textContent = `tags (${remainingTagCount}) `;
            } else {
              cardTagsLabel.textContent = `tags (${remainingTagCount})`;
            }
          }
        }

        // Tag count will be updated automatically via polling service

        // Re-render cards because spatial relationships may have changed
        this.updateStateAndRender();
      }
    } catch (error) {
      console.error('Failed to remove tag from card:', error);
    }
  }

  async deleteCard(cardId, deleteButton) {
    if (!confirm('Delete this card?')) return;

    try {
      const cardElement = deleteButton.closest('.card-item');

      const response = await fetch('/api/cards/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: cardId })
      });

      if (response.ok) {
        if (cardElement) cardElement.remove();

        // Tag counts will be updated automatically via polling service
      }
    } catch (error) {
      console.error('Failed to delete card:', error);
    }
  }

  async deleteTag(tagId, deleteButton) {
    if (!confirm('Delete this tag? It will be removed from all cards.')) return;

    try {
      const response = await fetch('/api/tags/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tag_id: tagId })
      });

      if (response.ok) {
        const tagElement = deleteButton.closest('.tag');
        if (tagElement) tagElement.remove();
        this.updateStateAndRender();
      }
    } catch (error) {
      console.error('Failed to delete tag:', error);
    }
  }

  startTagCountPolling() {
    // Tag counts are managed locally via DOM updates
    // Backend changes will be handled via WebSocket/SSE when implemented
    // No promiscuous polling for multi-user scalability
  }

  setupCardTagEventDelegation() {
    // Delegate card and tag button clicks
    document.body.addEventListener('click', async (e) => {
      // Tag delete button
      if (e.target.classList.contains('tag-delete')) {
        e.stopPropagation();
        const tagId = e.target.dataset.tagId;
        await this.deleteTag(tagId, e.target);
        return;
      }

      // Tag remove button (on cards)
      if (e.target.classList.contains('tag-remove')) {
        e.stopPropagation();
        const cardId = e.target.closest('.card-item')?.dataset.cardId;
        const tagId = e.target.closest('.card-tag')?.dataset.tagId;
        if (cardId && tagId) {
          await this.removeTagFromCard(cardId, tagId, e.target);
        }
        return;
      }

      // Card delete button
      if (e.target.classList.contains('card-delete')) {
        e.stopPropagation();
        const cardId = e.target.closest('.card-item')?.dataset.cardId;
        if (cardId) {
          await this.deleteCard(cardId, e.target);
        }
        return;
      }
    });
  }
}

// Global function wrappers for HTML onclick handlers
window.removeTagFromCard = function(cardId, tagName, removeButton) {
  if (window.dragDropSystem) {
    // Look up tag ID from the tag cloud
    const tagInCloud = document.querySelector(`[data-tag="${tagName}"][data-tag-id]`);
    const tagId = tagInCloud?.dataset.tagId;

    if (tagId) {
      window.dragDropSystem.removeTagFromCard(cardId, tagId, removeButton);
    } else {
      console.error('Could not find tag ID for tag:', tagName);
    }
  }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.dragDropSystem = new SpatialDragDrop();
    window.dragDropSystem.initialize();
  });
} else {
  // DOM already loaded
  window.dragDropSystem = new SpatialDragDrop();
  window.dragDropSystem.initialize();
}