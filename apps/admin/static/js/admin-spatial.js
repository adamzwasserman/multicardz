/**
 * multicardz Admin Spatial Management System
 * Extends the core spatial paradigm for administrative operations
 */

class AdminSpatialSystem {
    constructor() {
        this.draggedElement = null;
        this.zones = new Map();
        this.entities = new Map();
        this.operations = [];

        this.initialize();
    }

    initialize() {
        console.log('Initializing Admin Spatial System...');
        this.setupDragAndDrop();
        this.setupZones();
        this.setupKeyboardShortcuts();
    }

    setupDragAndDrop() {
        // Setup draggable elements
        document.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('admin-tag') || e.target.hasAttribute('draggable')) {
                this.handleDragStart(e);
            }
        });

        document.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('admin-tag') || e.target.hasAttribute('draggable')) {
                this.handleDragEnd(e);
            }
        });

        // Setup drop zones
        document.addEventListener('dragover', (e) => {
            if (e.target.closest('.admin-spatial-zone')) {
                this.handleDragOver(e);
            }
        });

        document.addEventListener('drop', (e) => {
            if (e.target.closest('.admin-spatial-zone')) {
                this.handleDrop(e);
            }
        });

        document.addEventListener('dragleave', (e) => {
            if (e.target.closest('.admin-spatial-zone')) {
                this.handleDragLeave(e);
            }
        });
    }

    setupZones() {
        const zones = document.querySelectorAll('.admin-spatial-zone[data-accepts]');
        zones.forEach(zone => {
            const zoneId = zone.dataset.zone;
            const accepts = zone.dataset.accepts ? zone.dataset.accepts.split(',') : [];

            this.zones.set(zoneId, {
                element: zone,
                accepts: accepts,
                contents: new Set()
            });
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R: Refresh metrics
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.refreshAllMetrics();
            }

            // Ctrl/Cmd + D: Toggle debug mode
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                this.toggleDebugMode();
            }

            // ESC: Clear all spatial operations
            if (e.key === 'Escape') {
                this.clearAllOperations();
            }
        });
    }

    handleDragStart(e) {
        this.draggedElement = e.target;
        e.target.classList.add('dragging');

        // Store entity data
        const entityId = e.target.dataset.entity || e.target.textContent.trim();
        const entityType = this.determineEntityType(entityId);

        e.dataTransfer.setData('text/plain', JSON.stringify({
            id: entityId,
            type: entityType,
            element: e.target.outerHTML
        }));

        // Visual feedback
        e.target.style.opacity = '0.5';

        console.log(`Spatial drag started: ${entityId} (${entityType})`);
    }

    handleDragEnd(e) {
        e.target.classList.remove('dragging');
        e.target.style.opacity = '';
        this.draggedElement = null;
    }

    handleDragOver(e) {
        e.preventDefault();
        const zone = e.target.closest('.admin-spatial-zone');
        if (!zone) return;

        zone.classList.add('drag-over');

        // Check if drop is valid
        const entityData = this.getDraggedEntityData(e);
        if (entityData && this.isValidDrop(zone, entityData.type)) {
            e.dataTransfer.dropEffect = 'copy';
        } else {
            e.dataTransfer.dropEffect = 'none';
        }
    }

    handleDragLeave(e) {
        const zone = e.target.closest('.admin-spatial-zone');
        if (zone) {
            zone.classList.remove('drag-over');
        }
    }

    handleDrop(e) {
        e.preventDefault();
        const zone = e.target.closest('.admin-spatial-zone');
        if (!zone) return;

        zone.classList.remove('drag-over');

        try {
            const entityData = JSON.parse(e.dataTransfer.getData('text/plain'));
            const zoneId = zone.dataset.zone;

            if (this.isValidDrop(zone, entityData.type)) {
                this.executeAdminOperation(entityData, zoneId, zone);
            } else {
                this.showFeedback('Invalid drop target for this entity type', 'error');
            }
        } catch (error) {
            console.error('Error handling drop:', error);
            this.showFeedback('Drop operation failed', 'error');
        }
    }

    getDraggedEntityData(e) {
        try {
            return JSON.parse(e.dataTransfer.getData('text/plain'));
        } catch {
            return null;
        }
    }

    isValidDrop(zone, entityType) {
        const zoneData = this.zones.get(zone.dataset.zone);
        if (!zoneData) return false;

        return zoneData.accepts.includes(entityType) || zoneData.accepts.includes('*');
    }

    determineEntityType(entityId) {
        if (entityId.includes('user')) return 'user';
        if (entityId.includes('workspace')) return 'workspace';
        if (entityId.includes('alert')) return 'alert';
        if (entityId.includes('service')) return 'service';
        if (entityId.includes('deployment')) return 'deployment';
        if (entityId.includes('metric')) return 'metric';
        return 'unknown';
    }

    executeAdminOperation(entityData, zoneId, zoneElement) {
        console.log(`Executing admin operation: ${entityData.id} → ${zoneId}`);

        // Create operation record
        const operation = {
            id: Date.now(),
            entity: entityData,
            zone: zoneId,
            timestamp: new Date(),
            status: 'executed'
        };

        this.operations.push(operation);

        // Update zone visual state
        zoneElement.classList.add('has-content');
        this.updateZoneContent(zoneElement, entityData);

        // Show operation result
        this.showOperationResult(operation);

        // Log to console (in production, this would be sent to backend)
        this.logOperation(operation);

        // Trigger any follow-up actions
        this.triggerAdminActions(operation);
    }

    updateZoneContent(zoneElement, entityData) {
        let contentDiv = zoneElement.querySelector('.zone-content');
        if (!contentDiv) {
            contentDiv = document.createElement('div');
            contentDiv.className = 'zone-content';
            contentDiv.style.marginTop = '12px';
            contentDiv.style.padding = '8px';
            contentDiv.style.background = 'rgba(255,255,255,0.1)';
            contentDiv.style.borderRadius = '4px';
            contentDiv.style.fontSize = '0.875rem';
            zoneElement.appendChild(contentDiv);
        }

        const entityBadge = document.createElement('span');
        entityBadge.className = 'admin-tag';
        entityBadge.style.fontSize = '0.75rem';
        entityBadge.style.margin = '2px';
        entityBadge.textContent = entityData.id;

        contentDiv.appendChild(entityBadge);
    }

    showOperationResult(operation) {
        const resultArea = document.getElementById('spatialResults') || this.createResultArea();
        const resultContent = document.getElementById('resultContent') || resultArea.querySelector('.result-content');

        resultArea.style.display = 'block';
        resultContent.innerHTML = `
            <div style="margin-bottom: 12px;">
                <strong>🔄 Spatial Operation Executed</strong>
                <span style="float: right; font-size: 0.75rem; color: var(--color-text-secondary);">
                    ${operation.timestamp.toLocaleTimeString()}
                </span>
            </div>
            <div style="font-family: monospace; font-size: 0.875rem; line-height: 1.4;">
                <div><strong>Entity:</strong> ${operation.entity.id}</div>
                <div><strong>Type:</strong> ${operation.entity.type}</div>
                <div><strong>Zone:</strong> ${operation.zone}</div>
                <div><strong>Operation:</strong> apply_admin_spatial("${operation.entity.id}", "${operation.zone}")</div>
                <div style="color: var(--color-status-healthy);"><strong>Status:</strong> ✅ Executed successfully</div>
            </div>
            <div style="margin-top: 12px; padding: 8px; background: var(--color-admin-accent); border-radius: 4px; font-size: 0.8rem; color: var(--color-text-secondary);">
                <em>In production, this would trigger backend administrative actions based on the spatial operation.</em>
            </div>
        `;

        // Auto-hide after 10 seconds
        setTimeout(() => {
            resultArea.style.display = 'none';
        }, 10000);
    }

    createResultArea() {
        const resultArea = document.createElement('div');
        resultArea.id = 'spatialResults';
        resultArea.style.cssText = `
            margin-top: 24px;
            padding: 16px;
            background: var(--color-admin-accent);
            border-radius: 8px;
            border: 1px solid var(--color-border-light);
        `;

        const resultContent = document.createElement('div');
        resultContent.id = 'resultContent';
        resultContent.className = 'result-content';
        resultArea.appendChild(resultContent);

        const container = document.querySelector('.admin-container') || document.body;
        container.appendChild(resultArea);

        return resultArea;
    }

    logOperation(operation) {
        // In production, this would send to backend logging system
        console.group('🔧 Admin Spatial Operation');
        console.log('Entity:', operation.entity);
        console.log('Zone:', operation.zone);
        console.log('Timestamp:', operation.timestamp);
        console.log('Operation ID:', operation.id);
        console.groupEnd();

        // Store in local storage for demo purposes
        const existingOps = JSON.parse(localStorage.getItem('adminSpatialOps') || '[]');
        existingOps.push(operation);
        localStorage.setItem('adminSpatialOps', JSON.stringify(existingOps.slice(-50))); // Keep last 50
    }

    triggerAdminActions(operation) {
        const { entity, zone } = operation;

        // Example: trigger different actions based on zone type
        switch (zone) {
            case 'investigate':
                this.triggerInvestigation(entity);
                break;
            case 'monitor':
                this.enhanceMonitoring(entity);
                break;
            case 'escalate':
                this.escalateIssue(entity);
                break;
            case 'archive':
                this.archiveEntity(entity);
                break;
            default:
                console.log(`No specific action for zone: ${zone}`);
        }
    }

    triggerInvestigation(entity) {
        console.log(`🔍 Triggering investigation for: ${entity.id}`);
        this.showFeedback(`Investigation initiated for ${entity.id}`, 'info');
    }

    enhanceMonitoring(entity) {
        console.log(`📊 Enhancing monitoring for: ${entity.id}`);
        this.showFeedback(`Enhanced monitoring enabled for ${entity.id}`, 'success');
    }

    escalateIssue(entity) {
        console.log(`🚨 Escalating issue: ${entity.id}`);
        this.showFeedback(`Issue ${entity.id} has been escalated to senior admin`, 'warning');
    }

    archiveEntity(entity) {
        console.log(`📦 Archiving: ${entity.id}`);
        this.showFeedback(`${entity.id} has been archived`, 'success');
    }

    showFeedback(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            top: 80px;
            right: 24px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        switch (type) {
            case 'success':
                toast.style.background = 'var(--color-status-healthy)';
                break;
            case 'warning':
                toast.style.background = 'var(--color-status-warning)';
                break;
            case 'error':
                toast.style.background = 'var(--color-status-critical)';
                break;
            default:
                toast.style.background = 'var(--color-action-primary)';
        }

        toast.textContent = message;
        document.body.appendChild(toast);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    refreshAllMetrics() {
        console.log('🔄 Refreshing all admin metrics...');

        // Trigger refresh on any refresh buttons
        const refreshButtons = document.querySelectorAll('[onclick*="refresh"]');
        refreshButtons.forEach(button => {
            if (button.onclick) button.onclick();
        });

        this.showFeedback('Metrics refreshed', 'success');
    }

    toggleDebugMode() {
        const body = document.body;
        body.classList.toggle('admin-debug-mode');

        if (body.classList.contains('admin-debug-mode')) {
            this.showDebugInfo();
            this.showFeedback('Debug mode enabled', 'info');
        } else {
            this.hideDebugInfo();
            this.showFeedback('Debug mode disabled', 'info');
        }
    }

    showDebugInfo() {
        // Add debug styles
        const style = document.createElement('style');
        style.id = 'admin-debug-styles';
        style.textContent = `
            .admin-debug-mode .admin-spatial-zone {
                border: 2px dashed var(--color-admin-primary) !important;
                position: relative;
            }
            .admin-debug-mode .admin-spatial-zone::before {
                content: attr(data-zone) ' (' attr(data-accepts) ')';
                position: absolute;
                top: -20px;
                left: 0;
                font-size: 0.75rem;
                background: var(--color-admin-primary);
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
            }
            .admin-debug-mode .admin-tag {
                position: relative;
            }
            .admin-debug-mode .admin-tag::after {
                content: attr(data-entity);
                position: absolute;
                bottom: -20px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 0.7rem;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 1px 4px;
                border-radius: 2px;
                white-space: nowrap;
            }
        `;
        document.head.appendChild(style);
    }

    hideDebugInfo() {
        const debugStyles = document.getElementById('admin-debug-styles');
        if (debugStyles) debugStyles.remove();
    }

    clearAllOperations() {
        // Clear all zone contents
        this.zones.forEach((zoneData, zoneId) => {
            const zoneElement = zoneData.element;
            zoneElement.classList.remove('has-content');
            const content = zoneElement.querySelector('.zone-content');
            if (content) content.remove();
            zoneData.contents.clear();
        });

        // Clear operations log
        this.operations = [];
        localStorage.removeItem('adminSpatialOps');

        // Hide result area
        const resultArea = document.getElementById('spatialResults');
        if (resultArea) resultArea.style.display = 'none';

        this.showFeedback('All spatial operations cleared', 'info');
        console.log('🧹 Cleared all admin spatial operations');
    }

    // Public API for external integration
    getOperationHistory() {
        return this.operations;
    }

    getZoneContents(zoneId) {
        const zone = this.zones.get(zoneId);
        return zone ? Array.from(zone.contents) : [];
    }

    exportSpatialState() {
        const state = {
            zones: Array.from(this.zones.entries()).map(([id, data]) => ({
                id,
                accepts: data.accepts,
                contents: Array.from(data.contents)
            })),
            operations: this.operations,
            timestamp: new Date()
        };

        console.log('📤 Exported spatial state:', state);
        return state;
    }
}

// CSS animations
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(animationStyles);

// Initialize global admin spatial system
let adminSpatialSystem = null;

function initializeAdminSpatialSystem() {
    if (!adminSpatialSystem) {
        adminSpatialSystem = new AdminSpatialSystem();

        // Expose to global scope for debugging
        window.adminSpatial = adminSpatialSystem;

        console.log('✅ Admin Spatial System initialized');
    }
    return adminSpatialSystem;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdminSpatialSystem;
}