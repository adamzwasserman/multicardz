/**
 * Group Tags UI Integration
 * Connects group tag functionality with multicardz UI
 * Handles group creation, display, and interaction
 */

// ============================================================================
// Group UI State Management
// ============================================================================

const GroupUIState = {
    selectedTags: new Set(),
    currentWorkspace: 'default-workspace',
    currentUser: 'default-user',
    groups: new Map(),
    isCreatingGroup: false,
    multiSelectMode: false,
};

/**
 * Initialize group tags UI system
 */
function initializeGroupUI() {
    console.log('🏷️ Initializing Group Tags UI...');

    // Get workspace and user from body element
    const body = document.body;
    GroupUIState.currentWorkspace = body.dataset.workspace || 'default-workspace';
    GroupUIState.currentUser = body.dataset.user || 'default-user';

    console.log(`📍 Workspace: ${GroupUIState.currentWorkspace}, User: ${GroupUIState.currentUser}`);

    // Load groups from server
    loadWorkspaceGroups();

    // Set up event listeners
    setupGroupEventListeners();

    // Integrate with existing drag-drop system
    enhanceDragDropForGroups();

    // Set up multi-selection integration
    setupMultiSelectionGroupIntegration();

    console.log('✅ Group Tags UI initialized');
}

// ============================================================================
// Group Loading and Display
// ============================================================================

/**
 * Load all groups for current workspace
 */
async function loadWorkspaceGroups() {
    try {
        const response = await fetch(`/api/groups/workspace/${GroupUIState.currentWorkspace}`);
        const data = await response.json();

        if (data.success) {
            // Clear existing groups
            GroupUIState.groups.clear();

            // Store groups in state
            data.groups.forEach(group => {
                GroupUIState.groups.set(group.group_id, group);
            });

            // Update UI
            renderGroupsCloud();

            console.log(`✅ Loaded ${data.groups.length} groups`);
        }
    } catch (error) {
        console.error('Failed to load groups:', error);
        showNotification('Failed to load groups', 'error');
    }
}

/**
 * Render groups in the tag cloud
 */
function renderGroupsCloud() {
    const groupsWrapper = document.querySelector('.cloud-group .tags-wrapper');
    if (!groupsWrapper) return;

    // Clear existing groups
    groupsWrapper.innerHTML = '';

    // Render each group
    GroupUIState.groups.forEach((group, groupId) => {
        const groupElement = createGroupElement(group);
        groupsWrapper.appendChild(groupElement);
    });

    // Update count
    const countElement = document.querySelector('.cloud-group .tag-count');
    if (countElement) {
        countElement.textContent = `(${GroupUIState.groups.size})`;
    }
}

/**
 * Create group tag DOM element
 */
function createGroupElement(group) {
    const span = document.createElement('span');
    span.className = 'tag tag-group group-tag';
    span.dataset.groupId = group.group_id;
    span.dataset.group = group.group_id;  // For drag-drop system compatibility
    span.dataset.type = 'group-tag';
    span.dataset.nestingLevel = '0';
    span.dataset.expanded = 'false';
    span.dataset.members = group.member_tag_ids ? group.member_tag_ids.join(',') : '';
    span.draggable = true;

    // Add ARIA attributes
    span.setAttribute('role', 'button');
    span.setAttribute('tabindex', '0');
    span.setAttribute('aria-label', `Group: ${group.name} with ${group.member_count} members`);
    span.setAttribute('aria-expanded', 'false');

    // Group icon (chevron)
    const icon = document.createElement('span');
    icon.className = 'group-icon';
    icon.innerHTML = `
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none" stroke="currentColor">
            <path d="M3 5 L6 8 L9 5" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
    `;

    // Group name
    const name = document.createElement('span');
    name.className = 'tag-name';
    name.textContent = group.name;

    // Member count
    const count = document.createElement('span');
    count.className = 'member-count';
    count.textContent = `(${group.member_count})`;

    // Member tags preview (collapsed)
    const membersPreview = document.createElement('span');
    membersPreview.className = 'members-preview';
    if (group.member_tag_ids && group.member_tag_ids.length > 0) {
        const preview = group.member_tag_ids.slice(0, 3).join(', ');
        const more = group.member_tag_ids.length > 3 ? ` +${group.member_tag_ids.length - 3}` : '';
        membersPreview.textContent = ` [${preview}${more}]`;
    }

    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'tag-delete';
    deleteBtn.textContent = '×';
    deleteBtn.title = 'Delete group';
    deleteBtn.onclick = (e) => {
        e.stopPropagation();
        deleteGroup(group.group_id);
    };

    // Assemble element
    span.appendChild(icon);
    span.appendChild(name);
    span.appendChild(count);
    span.appendChild(membersPreview);
    span.appendChild(deleteBtn);

    // Add event listeners
    setupGroupElementListeners(span, group);

    return span;
}

/**
 * Set up event listeners for group element
 */
function setupGroupElementListeners(element, group) {
    // Click to expand/collapse
    element.addEventListener('click', (e) => {
        if (e.target.classList.contains('tag-delete')) return;
        toggleGroupExpansion(group.group_id, element);
    });

    // Keyboard navigation
    element.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleGroupExpansion(group.group_id, element);
        } else if (e.key === 'Delete') {
            e.preventDefault();
            deleteGroup(group.group_id);
        }
    });

    // Drag start
    element.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/group-id', group.group_id);
        e.dataTransfer.setData('text/type', 'group-tag');
        element.classList.add('dragging');
        console.log(`🔵 Dragging group: ${group.name}`);
    });

    // Drag end
    element.addEventListener('dragend', (e) => {
        element.classList.remove('dragging');
    });

    // Drop handler (for adding tags to group)
    element.addEventListener('dragover', (e) => {
        if (e.dataTransfer.types.includes('text/tag-id')) {
            e.preventDefault();
            element.classList.add('group-hover');
        }
    });

    element.addEventListener('dragleave', (e) => {
        element.classList.remove('group-hover');
    });

    element.addEventListener('drop', async (e) => {
        e.preventDefault();
        element.classList.remove('group-hover');

        const tagId = e.dataTransfer.getData('text/tag-id');
        if (tagId) {
            await addTagToGroup(group.group_id, tagId);
        }
    });
}

// ============================================================================
// Group Creation
// ============================================================================

/**
 * Create group from selected tags
 */
async function createGroupFromSelection(groupName) {
    if (GroupUIState.selectedTags.size === 0) {
        showNotification('No tags selected. Select tags first.', 'warning');
        return;
    }

    if (!groupName || groupName.trim() === '') {
        showNotification('Group name is required', 'warning');
        return;
    }

    try {
        GroupUIState.isCreatingGroup = true;

        const memberTagIds = Array.from(GroupUIState.selectedTags);
        console.log('Creating group:', {
            name: groupName,
            workspace: GroupUIState.currentWorkspace,
            user: GroupUIState.currentUser,
            memberCount: memberTagIds.length,
            memberIds: memberTagIds
        });

        const response = await fetch('/api/groups/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: groupName.trim(),
                workspace_id: GroupUIState.currentWorkspace,
                user_id: GroupUIState.currentUser,
                member_tag_ids: memberTagIds,
                visual_style: {}
            })
        });

        const data = await response.json();
        console.log('API response:', data);

        if (data.success) {
            showNotification(`Group "${groupName}" created with ${GroupUIState.selectedTags.size} members`, 'success');

            // Reload groups
            await loadWorkspaceGroups();

            // Clear selection
            clearTagSelection();
        } else {
            console.error('API error:', data);
            showNotification(data.message || 'Failed to create group', 'error');
        }
    } catch (error) {
        console.error('Failed to create group:', error);
        showNotification(`Failed to create group: ${error.message}`, 'error');
    } finally {
        GroupUIState.isCreatingGroup = false;
    }
}

/**
 * Show group creation dialog
 */
function showGroupCreationDialog() {
    const selectedCount = GroupUIState.selectedTags.size;

    if (selectedCount === 0) {
        showNotification('Select tags first to create a group', 'info');
        return;
    }

    const groupName = prompt(`Create group with ${selectedCount} selected tags.\n\nGroup name:`);

    if (groupName) {
        createGroupFromSelection(groupName);
    }
}

// ============================================================================
// Group Operations
// ============================================================================

/**
 * Toggle group expansion to show member tags
 */
async function toggleGroupExpansion(groupId, element) {
    const isExpanded = element.dataset.expanded === 'true';

    if (isExpanded) {
        // Collapse
        element.dataset.expanded = 'false';
        element.setAttribute('aria-expanded', 'false');
        element.classList.remove('expanded');
    } else {
        // Expand - show loading state
        element.classList.add('expanding');

        try {
            const response = await fetch('/api/groups/expand', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    group_id: groupId,
                    use_cache: true
                })
            });

            const data = await response.json();

            if (data.success) {
                element.dataset.expanded = 'true';
                element.setAttribute('aria-expanded', 'true');
                element.classList.add('expanded');

                // Show expanded tags (visual feedback)
                showExpandedTagsPreview(element, data.expanded_tag_ids);
            }
        } catch (error) {
            console.error('Failed to expand group:', error);
            showNotification('Failed to expand group', 'error');
        } finally {
            element.classList.remove('expanding');
        }
    }
}

/**
 * Show preview of expanded tags
 */
function showExpandedTagsPreview(element, tagIds) {
    // Remove existing preview
    const existing = element.querySelector('.expansion-preview');
    if (existing) existing.remove();

    // Create preview element
    const preview = document.createElement('div');
    preview.className = 'expansion-preview';
    preview.textContent = `Expands to: ${tagIds.join(', ')}`;

    element.appendChild(preview);
}

/**
 * Add tag to existing group
 */
async function addTagToGroup(groupId, tagId) {
    try {
        const response = await fetch('/api/groups/add-member', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                group_id: groupId,
                member_tag_id: tagId,
                user_id: GroupUIState.currentUser
            })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Tag added to group', 'success');

            // Reload groups to update member count
            await loadWorkspaceGroups();
        } else {
            showNotification(data.message || 'Failed to add tag', 'error');
        }
    } catch (error) {
        console.error('Failed to add tag to group:', error);
        showNotification('Failed to add tag to group', 'error');
    }
}

/**
 * Delete group
 */
async function deleteGroup(groupId) {
    const group = GroupUIState.groups.get(groupId);
    if (!group) return;

    if (!confirm(`Delete group "${group.name}"?\n\nMember tags will not be deleted.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/groups/${groupId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification(`Group "${group.name}" deleted`, 'success');

            // Reload groups
            await loadWorkspaceGroups();
        } else {
            showNotification('Failed to delete group', 'error');
        }
    } catch (error) {
        console.error('Failed to delete group:', error);
        showNotification('Failed to delete group', 'error');
    }
}

// ============================================================================
// Multi-Selection Integration
// ============================================================================

/**
 * Set up multi-selection for group creation
 */
function setupMultiSelectionGroupIntegration() {
    // Listen for tag selection events
    document.addEventListener('tag-selected', (e) => {
        GroupUIState.selectedTags.add(e.detail.tagId);
        updateSelectionUI();
    });

    document.addEventListener('tag-deselected', (e) => {
        GroupUIState.selectedTags.delete(e.detail.tagId);
        updateSelectionUI();
    });

    document.addEventListener('selection-cleared', () => {
        clearTagSelection();
    });
}

/**
 * Update selection UI to show group creation option
 */
function updateSelectionUI() {
    const count = GroupUIState.selectedTags.size;

    if (count > 0) {
        showGroupCreationButton();
    } else {
        hideGroupCreationButton();
    }
}

/**
 * Show group creation button in UI
 */
function showGroupCreationButton() {
    let button = document.getElementById('create-group-btn');

    if (!button) {
        button = document.createElement('button');
        button.id = 'create-group-btn';
        button.className = 'create-group-button';
        button.textContent = `Create Group (${GroupUIState.selectedTags.size})`;
        button.onclick = showGroupCreationDialog;

        // Add to tag cloud controls
        const cloudGroup = document.querySelector('.cloud-group .input-wrapper');
        if (cloudGroup) {
            cloudGroup.insertBefore(button, cloudGroup.firstChild);
        }
    } else {
        button.textContent = `Create Group (${GroupUIState.selectedTags.size})`;
    }
}

/**
 * Hide group creation button
 */
function hideGroupCreationButton() {
    const button = document.getElementById('create-group-btn');
    if (button) {
        button.remove();
    }
}

/**
 * Clear tag selection
 */
function clearTagSelection() {
    GroupUIState.selectedTags.clear();
    updateSelectionUI();

    // Don't dispatch event here - it's dispatched from drag-drop.js
    // to prevent infinite recursion
}

// ============================================================================
// Drag-Drop Integration
// ============================================================================

/**
 * Enhance existing drag-drop system to support groups
 */
function enhanceDragDropForGroups() {
    // Groups can be dropped on zones
    const dropZones = document.querySelectorAll('[data-drop-zone]');

    dropZones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
            if (e.dataTransfer.types.includes('text/group-id')) {
                e.preventDefault();
                zone.classList.add('zone-active');
            }
        });

        zone.addEventListener('dragleave', (e) => {
            zone.classList.remove('zone-active');
        });

        zone.addEventListener('drop', async (e) => {
            if (e.dataTransfer.types.includes('text/group-id')) {
                e.preventDefault();
                zone.classList.remove('zone-active');

                const groupId = e.dataTransfer.getData('text/group-id');
                const zoneType = zone.dataset.zone;

                await handleGroupDropOnZone(groupId, zoneType, zone);
            }
        });
    });
}

/**
 * Handle group dropped on zone
 */
async function handleGroupDropOnZone(groupId, zoneType, zoneElement) {
    try {
        // Get current zone tags
        const currentTags = getCurrentZoneTags(zoneElement);

        // Call drop API
        const response = await fetch('/api/groups/drop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_type: 'group',
                source_id: groupId,
                target_type: `${zoneType}-zone`,
                target_id: zoneElement.id,
                workspace_id: GroupUIState.currentWorkspace,
                user_id: GroupUIState.currentUser,
                current_zone_tags: currentTags
            })
        });

        const data = await response.json();

        if (data.success) {
            // Update zone with result tags
            updateZoneTags(zoneElement, data.result_tag_ids);

            showNotification(`Group expanded in ${zoneType} zone`, 'success');
        } else {
            showNotification(data.message || 'Drop operation failed', 'error');
        }
    } catch (error) {
        console.error('Failed to handle group drop:', error);
        showNotification('Drop operation failed', 'error');
    }
}

/**
 * Get current tags in a zone
 */
function getCurrentZoneTags(zoneElement) {
    const tags = zoneElement.querySelectorAll('[data-tag-id]');
    return Array.from(tags).map(tag => tag.dataset.tagId);
}

/**
 * Update zone with new tags
 */
function updateZoneTags(zoneElement, tagIds) {
    // This would integrate with existing zone update logic
    // For now, just trigger a zone update event
    const event = new CustomEvent('zone-updated', {
        detail: { zoneId: zoneElement.id, tagIds }
    });
    document.dispatchEvent(event);
}

// ============================================================================
// Event Listeners Setup
// ============================================================================

/**
 * Set up all group-related event listeners
 */
function setupGroupEventListeners() {
    // Group input field for manual group creation
    const groupInput = document.querySelector('.cloud-group .tag-input');
    if (groupInput) {
        groupInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const groupName = groupInput.value.trim();
                if (groupName) {
                    createGroupFromSelection(groupName);
                    groupInput.value = '';
                }
            }
        });
    }

    // Keyboard shortcut for group creation (Ctrl+G or Cmd+G)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
            e.preventDefault();
            showGroupCreationDialog();
        }
    });
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
    // This would integrate with existing notification system
    console.log(`[${type.toUpperCase()}] ${message}`);

    // Create simple toast notification
    const toast = document.createElement('div');
    toast.className = `notification notification-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================================================
// Initialization
// ============================================================================

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeGroupUI);
} else {
    initializeGroupUI();
}

// Export for external use
window.GroupUI = {
    state: GroupUIState,
    createGroup: createGroupFromSelection,
    deleteGroup,
    addTagToGroup,
    loadGroups: loadWorkspaceGroups,
    showCreationDialog: showGroupCreationDialog
};
