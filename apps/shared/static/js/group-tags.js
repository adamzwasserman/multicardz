/**
 * Group Tags Client-Side Functionality
 *
 * Handles drag-drop interactions, visual feedback, and expansion/collapse
 * for group tags in the multicardz spatial tag manipulation system.
 */

// ============ State Management ============

const GroupTagState = {
    expandedGroups: new Set(),
    selectedGroups: new Set(),
    draggedGroup: null,
    dropTarget: null,
};

// ============ Group Expansion ============

/**
 * Toggle group expansion state
 * @param {string} groupId - ID of group to toggle
 */
function toggleGroupExpansion(groupId) {
    if (GroupTagState.expandedGroups.has(groupId)) {
        GroupTagState.expandedGroups.delete(groupId);
    } else {
        GroupTagState.expandedGroups.add(groupId);
    }

    updateGroupVisualState(groupId);
}

/**
 * Update visual state of a group element
 * @param {string} groupId - ID of group to update
 */
function updateGroupVisualState(groupId) {
    const element = document.querySelector(`[data-group-id="${groupId}"]`);
    if (!element) return;

    const isExpanded = GroupTagState.expandedGroups.has(groupId);
    const isSelected = GroupTagState.selectedGroups.has(groupId);

    element.setAttribute('data-expanded', isExpanded);
    element.setAttribute('aria-expanded', isExpanded);

    if (isSelected) {
        element.classList.add('selected');
    } else {
        element.classList.remove('selected');
    }
}

// ============ Drag and Drop ============

/**
 * Handle drag start on group tag
 * @param {DragEvent} event - Drag event
 */
function handleGroupDragStart(event) {
    const groupElement = event.target.closest('.group-tag');
    if (!groupElement) return;

    const groupId = groupElement.getAttribute('data-group-id');
    GroupTagState.draggedGroup = groupId;

    // Set drag data
    event.dataTransfer.effectAllowed = 'copy';
    event.dataTransfer.setData('application/x-multicardz-group', groupId);
    event.dataTransfer.setData('text/plain', groupElement.textContent);

    // Add dragging class
    groupElement.classList.add('dragging');

    // Custom drag image (optional)
    const dragImage = groupElement.cloneNode(true);
    dragImage.style.opacity = '0.8';
    document.body.appendChild(dragImage);
    event.dataTransfer.setDragImage(dragImage, 0, 0);
    setTimeout(() => document.body.removeChild(dragImage), 0);
}

/**
 * Handle drag end on group tag
 * @param {DragEvent} event - Drag event
 */
function handleGroupDragEnd(event) {
    const groupElement = event.target.closest('.group-tag');
    if (groupElement) {
        groupElement.classList.remove('dragging');
    }

    GroupTagState.draggedGroup = null;
    clearDropFeedback();
}

/**
 * Handle drag over drop zone
 * @param {DragEvent} event - Drag event
 */
function handleGroupDragOver(event) {
    if (!GroupTagState.draggedGroup) return;

    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';

    const dropZone = event.target.closest('.drop-zone, .card, .group-tag');
    if (dropZone) {
        showDropFeedback(dropZone);
    }
}

/**
 * Handle drop on zone
 * @param {DragEvent} event - Drag event
 */
async function handleGroupDrop(event) {
    event.preventDefault();

    const groupId = event.dataTransfer.getData('application/x-multicardz-group');
    if (!groupId) return;

    const dropZone = event.target.closest('.drop-zone, .card, .group-tag');
    if (!dropZone) return;

    // Determine target type
    const targetType = getTargetType(dropZone);
    const targetId = getTargetId(dropZone);

    // Show loading state
    showExpandingState(groupId);

    try {
        // Call backend API to process drop
        const result = await processGroupDrop(groupId, targetType, targetId);

        if (result.success) {
            // Update UI with result
            handleDropSuccess(result);
        } else {
            // Show error
            handleDropError(result.error_message);
        }
    } catch (error) {
        console.error('Group drop failed:', error);
        handleDropError(error.message);
    } finally {
        hideExpandingState(groupId);
        clearDropFeedback();
    }
}

// ============ API Communication ============

/**
 * Process group drop via backend API
 * @param {string} groupId - ID of dropped group
 * @param {string} targetType - Type of drop target
 * @param {string} targetId - ID of drop target
 * @returns {Promise<Object>} - Operation result
 */
async function processGroupDrop(groupId, targetType, targetId) {
    const response = await fetch('/api/groups/drop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            source_type: 'group',
            source_id: groupId,
            target_type: targetType,
            target_id: targetId,
        }),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

/**
 * Fetch group expansion preview
 * @param {string} groupId - ID of group
 * @returns {Promise<Object>} - Expansion data
 */
async function fetchGroupExpansion(groupId) {
    const response = await fetch(`/api/groups/${groupId}/expand`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// ============ Visual Feedback ============

/**
 * Show drop feedback on target
 * @param {HTMLElement} dropZone - Drop zone element
 */
function showDropFeedback(dropZone) {
    if (GroupTagState.dropTarget !== dropZone) {
        clearDropFeedback();
        GroupTagState.dropTarget = dropZone;
        dropZone.classList.add('group-hover');
    }
}

/**
 * Clear drop feedback
 */
function clearDropFeedback() {
    if (GroupTagState.dropTarget) {
        GroupTagState.dropTarget.classList.remove('group-hover', 'group-valid-drop');
        GroupTagState.dropTarget = null;
    }
}

/**
 * Show expanding state on group
 * @param {string} groupId - ID of group
 */
function showExpandingState(groupId) {
    const element = document.querySelector(`[data-group-id="${groupId}"]`);
    if (element) {
        element.classList.add('expanding');
    }
}

/**
 * Hide expanding state
 * @param {string} groupId - ID of group
 */
function hideExpandingState(groupId) {
    const element = document.querySelector(`[data-group-id="${groupId}"]`);
    if (element) {
        element.classList.remove('expanding');
    }
}

// ============ Success/Error Handlers ============

/**
 * Handle successful drop operation
 * @param {Object} result - Operation result from backend
 */
function handleDropSuccess(result) {
    // Show success feedback
    showNotification(`Group expanded: ${result.metadata?.expanded_count || 0} tags added`, 'success');

    // Trigger UI update event
    const event = new CustomEvent('groupDropSuccess', {
        detail: result,
    });
    document.dispatchEvent(event);
}

/**
 * Handle drop operation error
 * @param {string} errorMessage - Error message
 */
function handleDropError(errorMessage) {
    showNotification(`Error: ${errorMessage}`, 'error');
}

/**
 * Show notification to user
 * @param {string} message - Notification message
 * @param {string} type - Notification type ('success', 'error', 'info')
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.setAttribute('role', 'alert');

    document.body.appendChild(notification);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============ Helper Functions ============

/**
 * Get target type from drop zone element
 * @param {HTMLElement} element - Drop zone element
 * @returns {string} - Target type
 */
function getTargetType(element) {
    if (element.classList.contains('union-zone')) return 'union-zone';
    if (element.classList.contains('intersection-zone')) return 'intersection-zone';
    if (element.classList.contains('exclusion-zone')) return 'exclusion-zone';
    if (element.classList.contains('card')) return 'card';
    if (element.classList.contains('group-tag')) return 'group';
    return 'unknown';
}

/**
 * Get target ID from drop zone element
 * @param {HTMLElement} element - Drop zone element
 * @returns {string} - Target ID
 */
function getTargetId(element) {
    if (element.hasAttribute('data-card-id')) {
        return element.getAttribute('data-card-id');
    }
    if (element.hasAttribute('data-group-id')) {
        return element.getAttribute('data-group-id');
    }
    return element.getAttribute('data-zone-id') || 'unknown';
}

// ============ Keyboard Navigation ============

/**
 * Handle keyboard interactions on group tags
 * @param {KeyboardEvent} event - Keyboard event
 */
function handleGroupKeyboard(event) {
    const groupElement = event.target.closest('.group-tag');
    if (!groupElement) return;

    const groupId = groupElement.getAttribute('data-group-id');

    switch (event.key) {
        case ' ':
        case 'Enter':
            event.preventDefault();
            toggleGroupExpansion(groupId);
            break;

        case 'ArrowRight':
            event.preventDefault();
            if (!GroupTagState.expandedGroups.has(groupId)) {
                toggleGroupExpansion(groupId);
            }
            break;

        case 'ArrowLeft':
            event.preventDefault();
            if (GroupTagState.expandedGroups.has(groupId)) {
                toggleGroupExpansion(groupId);
            }
            break;

        case 'Delete':
        case 'Backspace':
            event.preventDefault();
            if (GroupTagState.selectedGroups.has(groupId)) {
                GroupTagState.selectedGroups.delete(groupId);
                updateGroupVisualState(groupId);
            }
            break;
    }
}

// ============ Initialization ============

/**
 * Initialize group tag interactions
 */
function initGroupTags() {
    // Attach event listeners to all group tags
    document.addEventListener('dragstart', (e) => {
        if (e.target.closest('.group-tag')) {
            handleGroupDragStart(e);
        }
    });

    document.addEventListener('dragend', (e) => {
        if (e.target.closest('.group-tag')) {
            handleGroupDragEnd(e);
        }
    });

    document.addEventListener('dragover', (e) => {
        handleGroupDragOver(e);
    });

    document.addEventListener('drop', (e) => {
        handleGroupDrop(e);
    });

    document.addEventListener('keydown', (e) => {
        handleGroupKeyboard(e);
    });

    // Click to expand/collapse
    document.addEventListener('click', (e) => {
        const groupElement = e.target.closest('.group-tag');
        if (groupElement) {
            const groupId = groupElement.getAttribute('data-group-id');

            // Shift+click for multi-select
            if (e.shiftKey) {
                if (GroupTagState.selectedGroups.has(groupId)) {
                    GroupTagState.selectedGroups.delete(groupId);
                } else {
                    GroupTagState.selectedGroups.add(groupId);
                }
                updateGroupVisualState(groupId);
            }
        }
    });

    console.log('Group tags initialized');
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGroupTags);
} else {
    initGroupTags();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        toggleGroupExpansion,
        processGroupDrop,
        fetchGroupExpansion,
    };
}
