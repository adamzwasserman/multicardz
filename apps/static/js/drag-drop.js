/**
 * MultiCardz™ Spatial Drag-Drop System
 * Handles dynamic zone discovery, multi-tag operations, and immutable DOM manipulation
 */

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
  }

  // Initialize the entire system
  initialize() {
    this.initializeZones();
    this.initializeControls();
    this.initializeTagDragging();
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
      controls: this.getRenderingControls()
    };

    // Update cache
    this.stateCache = state;
    this.stateCacheTime = now;

    return state;
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
        startWithCardsExpanded: false,
        showColors: true
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

    return controls;
  }

  // Initialize zones with event delegation
  initializeZones() {
    // Use event delegation on container
    const zoneContainer = document.querySelector('.zones-wrapper') ||
                         document.querySelector('.spatial-grid') ||
                         document.body;

    zoneContainer.addEventListener('drop', (e) => {
      const zone = e.target.closest('[data-zone-type]:not([data-zone-type="tag-cloud"])');
      if (zone) this.handleZoneDrop(e, zone);
    });

    zoneContainer.addEventListener('dragover', (e) => {
      const zone = e.target.closest('[data-zone-type]:not([data-zone-type="tag-cloud"])');
      if (zone) this.handleZoneDragOver(e, zone);
    });

    zoneContainer.addEventListener('dragleave', (e) => {
      const zone = e.target.closest('[data-zone-type]:not([data-zone-type="tag-cloud"])');
      if (zone) this.handleZoneDragLeave(e, zone);
    });

    // Handle cloud drops for returning tags
    const clouds = document.querySelectorAll('.cloud');
    clouds.forEach(cloud => {
      cloud.addEventListener('drop', (e) => this.handleCloudDrop(e));
      cloud.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
      });
      cloud.addEventListener('dragleave', (e) => {
        e.currentTarget.classList.remove('drag-over');
      });
    });
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

  // Zone drag over handler
  handleZoneDragOver(event, zone) {
    event.preventDefault();
    zone.classList.add('drag-over');

    if (this.draggedElements.length > 1) {
      zone.dataset.dropCount = this.draggedElements.length;
    }
  }

  // Zone drag leave handler
  handleZoneDragLeave(event, zone) {
    zone.classList.remove('drag-over');
    delete zone.dataset.dropCount;
  }

  // Zone drop handler
  handleZoneDrop(event, zone) {
    event.preventDefault();
    zone.classList.remove('drag-over');
    delete zone.dataset.dropCount;

    if (!this.draggedElements || this.draggedElements.length === 0) return;

    const targetZone = zone.dataset.zoneType;
    this.moveTags(this.draggedElements, targetZone);

    // Cleanup
    this.draggedElements.forEach(el => {
      el.classList.remove('dragging');
      el.setAttribute('aria-grabbed', 'false');
    });
    this.draggedElements = [];
    this.clearSelection();
  }

  // Handle cloud drop (return to cloud)
  handleCloudDrop(event) {
    event.preventDefault();
    event.currentTarget.classList.remove('drag-over');

    if (!this.draggedElements || this.draggedElements.length === 0) return;

    this.moveTags(this.draggedElements, 'cloud');

    // Cleanup
    this.draggedElements.forEach(el => {
      el.classList.remove('dragging');
      el.setAttribute('aria-grabbed', 'false');
    });
    this.draggedElements = [];
    this.clearSelection();
  }

  // Move tags with validation
  moveTags(tagElements, targetZone) {
    // Validate tag elements
    const validTags = tagElements.filter(el =>
      el && el.dataset && el.dataset.tag && el.nodeType === Node.ELEMENT_NODE
    );

    if (validTags.length === 0) return;

    if (targetZone === 'cloud') {
      this.returnTagsToCloud(validTags);
    } else {
      const targetZoneElement = document.querySelector(`[data-zone-type="${targetZone}"]`);
      if (!targetZoneElement) {
        console.error(`Zone not found: ${targetZone}`);
        return;
      }

      const targetContainer = targetZoneElement.querySelector('.tag-collection');
      if (!targetContainer) {
        console.error(`No tag collection in zone: ${targetZone}`);
        return;
      }

      // Check max tags constraint
      const maxTags = this.parseMaxTags(targetZoneElement.dataset.maxTags);
      if (maxTags && targetContainer.children.length + validTags.length > maxTags) {
        console.warn(`Zone ${targetZone} would exceed max tags: ${maxTags}`);
        return;
      }

      // Move tags
      validTags.forEach(tag => {
        if (!targetContainer.contains(tag)) {
          targetContainer.appendChild(tag);
          tag.classList.remove('tag-cloud');
          tag.classList.add('tag-active');
        }
      });
    }

    // Invalidate cache and update
    this.invalidateCache();
    this.updateStateAndRender();
  }

  // Return tags to cloud
  returnTagsToCloud(tagElements) {
    const tagsByType = {};

    tagElements.forEach(tag => {
      const type = tag.dataset.type || 'tag';
      if (!tagsByType[type]) tagsByType[type] = [];
      tagsByType[type].push(tag);
    });

    for (const [tagType, tags] of Object.entries(tagsByType)) {
      const cloudSelector = tagType === 'ai-tag' ? '.cloud-ai .tags-wrapper' : '.cloud-user .tags-wrapper';
      const cloudContainer = document.querySelector(cloudSelector);

      if (cloudContainer) {
        tags.forEach(tag => {
          if (!cloudContainer.contains(tag)) {
            cloudContainer.appendChild(tag);
            tag.classList.remove('tag-active', 'selected');
            tag.classList.add('tag-cloud');
          }
        });
      }
    }
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
    }, this.DEBOUNCE_DELAY);
  }

  // Send to backend
  async renderCards(tagsInPlay) {
    try {
      const response = await fetch('/api/v2/render/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

  // Observe zone changes with scoped observer
  observeZoneChanges() {
    const container = document.querySelector('.zones-wrapper') ||
                     document.querySelector('.spatial-grid') ||
                     document.body;

    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === 1 && node.dataset?.zoneType) {
              this.attachZoneListeners(node);
            }
          });

          mutation.removedNodes.forEach(node => {
            if (node.nodeType === 1 && node.dataset?.zoneType) {
              this.detachZoneListeners(node);
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

  // Attach zone listeners
  attachZoneListeners(zoneElement) {
    if (!zoneElement || this.listeners.has(zoneElement)) return;

    const handlers = {
      drop: (e) => this.handleZoneDrop(e, zoneElement),
      dragover: (e) => this.handleZoneDragOver(e, zoneElement),
      dragleave: (e) => this.handleZoneDragLeave(e, zoneElement)
    };

    zoneElement.addEventListener('drop', handlers.drop);
    zoneElement.addEventListener('dragover', handlers.dragover);
    zoneElement.addEventListener('dragleave', handlers.dragleave);

    // Add ARIA attributes
    zoneElement.setAttribute('role', 'region');
    zoneElement.setAttribute('aria-label', zoneElement.dataset.zoneType + ' drop zone');

    // Store handlers for cleanup
    this.listeners.set(zoneElement, handlers);
  }

  // Detach zone listeners
  detachZoneListeners(zoneElement) {
    if (!zoneElement || !this.listeners.has(zoneElement)) return;

    const handlers = this.listeners.get(zoneElement);
    zoneElement.removeEventListener('drop', handlers.drop);
    zoneElement.removeEventListener('dragover', handlers.dragover);
    zoneElement.removeEventListener('dragleave', handlers.dragleave);

    this.listeners.delete(zoneElement);
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
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const dragDrop = new SpatialDragDrop();
  dragDrop.initialize();
  window.spatialDragDrop = dragDrop; // For debugging
});