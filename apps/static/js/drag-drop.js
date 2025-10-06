/**
 * MultiCardz™ Spatial Drag-Drop System
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
    if (cloudType === 'user') return true;
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
    return false; // No card re-render needed
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
  }

  // Initialize the entire system
  initialize() {
    this.initializeZones();
    this.initializeControls();
    this.initializeTagDragging();
    this.setupCardTagEventDelegation();
    this.startTagCountPolling();
    this.observeZoneChanges();

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

      const handler = this.registry.findHandler(this.draggedElements[0], dropTarget);

      if (handler && handler.validate(this.draggedElements[0], dropTarget)) {
        await handler.handleDrop(e, dropTarget, this.draggedElements);

        // Cleanup dragged elements
        this.draggedElements.forEach(el => {
          el.classList.remove('dragging');
          el.setAttribute('aria-grabbed', 'false');
        });
        this.draggedElements = [];
        this.clearSelection();

        // Update state if handler mutates tagsInPlay
        if (handler.mutatesTagsInPlay() || handler.requiresRerender()) {
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

    // Drag start
    tagContainer.addEventListener('dragstart', (e) => {
      if (e.target.matches('[data-tag]')) {
        this.handleTagDragStart(e);
      }
    });

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

    // Set draggable on all tags and add ARIA
    document.querySelectorAll('[data-tag]').forEach(tag => {
      tag.draggable = true;
      tag.setAttribute('role', 'button');
      tag.setAttribute('aria-grabbed', 'false');
      tag.setAttribute('tabindex', '0');
    });
  }

  // Handle tag drag start
  handleTagDragStart(event) {
    const draggedTag = event.target;

    // Validate it's actually a tag
    if (!draggedTag.dataset.tag) return;

    // Determine what's being dragged
    if (draggedTag.dataset.type === 'group-tag') {
      this.draggedElements = this.expandGroupTag(draggedTag);
    } else if (this.selectedTags.has(draggedTag)) {
      this.draggedElements = Array.from(this.selectedTags);
    } else {
      this.draggedElements = [draggedTag];
      this.clearSelection();
    }

    // Visual feedback
    this.draggedElements.forEach(el => {
      el.classList.add('dragging');
      el.setAttribute('aria-grabbed', 'true');
    });

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
  }

  // Handle tag click for selection
  handleTagClick(event) {
    const tag = event.currentTarget;

    if (event.metaKey || event.ctrlKey) {
      event.preventDefault();
      this.toggleTagSelection(tag);
    } else {
      this.clearSelection();
    }
  }

  // Toggle tag selection
  toggleTagSelection(tagElement) {
    if (!tagElement) return;

    if (this.selectedTags.has(tagElement)) {
      this.selectedTags.delete(tagElement);
      tagElement.classList.remove('selected');
      tagElement.setAttribute('aria-selected', 'false');
    } else {
      this.selectedTags.add(tagElement);
      tagElement.classList.add('selected');
      tagElement.setAttribute('aria-selected', 'true');
    }
  }

  // Clear selection properly
  clearSelection() {
    this.selectedTags.forEach(tag => {
      tag.classList.remove('selected');
      tag.setAttribute('aria-selected', 'false');
    });
    this.selectedTags.clear();
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

      // Update lesson hint with current zone state
      await this.updateLessonHint(tagsInPlay);
    }, this.DEBOUNCE_DELAY);
  }

  // Update lesson hint based on current zone state
  async updateLessonHint(tagsInPlay) {
    try {
      // Build query parameters from zone state
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