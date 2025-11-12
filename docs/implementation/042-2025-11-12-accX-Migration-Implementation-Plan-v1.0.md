# accX Migration Implementation Plan
**Document Version**: 1.0
**Date**: 2025-11-12
**Status**: READY FOR IMPLEMENTATION
**Architecture Refs**:
- accX Architecture: /Users/adam/dev/genX/docs/architecture/accx-architecture-v1.0.md
- genX Infrastructure: /Users/adam/dev/genX/docs/architecture/genx-common-infrastructure-architecture-v1.0.md

---

## Executive Summary

This implementation plan details the complete migration of all accessibility features in the multicardz codebase from manual ARIA implementations to declarative accX attributes. The migration will eliminate 100% of manual accessibility code, replacing it with accX's declarative approach while maintaining full WCAG 2.1 AA compliance.

### Current State Analysis

**Existing Accessibility Implementations Found:**
- **48 files** containing accessibility-related code
- **ARIA Attributes**: aria-label, aria-expanded, aria-describedby, aria-hidden, aria-live, aria-atomic, aria-controls
- **Role Attributes**: button, region, tooltip roles manually applied
- **Keyboard Handling**: Custom keydown/keyup handlers for drag-drop, navigation
- **Focus Management**: CSS :focus and :focus-visible styles, tabindex attributes
- **Screen Reader Support**: Custom announcements, sr-only class for hidden text
- **Form Labels**: Manual label/input associations
- **Visual Indicators**: Custom focus styles, hover states

### Migration Scope

**Complete replacement of:**
1. All manual ARIA attribute applications (aria-*, role attributes)
2. Custom keyboard event handlers for accessibility
3. Screen reader announcement mechanisms
4. Focus management and trap implementations
5. Manual semantic HTML enhancements
6. Custom accessibility CSS classes (sr-only, etc.)
7. Form label associations and fieldset/legend structures

---

## Phase 1: Foundation Setup (Days 1-2)

### Task 1.1: Create BDD Tests for accX Integration
**Priority**: 0 (Critical)
**Dependencies**: None
**Technical Requirements**:
```markdown
1. Create feature file: tests/features/accx-integration.feature
2. Create step definitions: tests/step_definitions/test_accx_integration_steps.py
3. Framework: pytest-bdd with Playwright for browser testing
4. Test scenarios:
   - accX bootloader loads successfully
   - ax- attributes are detected and processed
   - ARIA attributes are automatically applied
   - Keyboard handlers are attached
   - Screen reader announcements work
5. Reference: tests/step_definitions/test_drag_drop_steps.py
6. Validation: uv run pytest tests/features/accx-integration.feature -v
```

**Acceptance Criteria**:
- [ ] Tests fail initially (RED phase) with assertion errors
- [ ] No StepDefinitionNotFound errors
- [ ] All core accX behaviors have test coverage

### Task 1.2: Integrate accX Bootloader
**Priority**: 0 (Critical)
**Dependencies**: Task 1.1
**Technical Requirements**:
```markdown
1. Add accX bootloader script to base.html
2. Configure bootloader for multicardz patterns
3. Set up development/production CDN URLs
4. Implement lazy loading after first paint
5. Add integrity checks and fallback mechanisms
```

**Files to Modify**:
- `apps/static/templates/base.html`
- `apps/static/js/app.js` (initialization sequence)

### Task 1.3: Create accX Attribute Mapping Documentation
**Priority**: 1 (High)
**Dependencies**: Task 1.2
**Technical Requirements**:
```markdown
1. Document all current accessibility patterns
2. Map each pattern to accX declarative equivalents
3. Create migration checklist for each component
4. Generate test matrix for validation
```

---

## Phase 2: Drag-Drop System Migration (Days 3-5)

### Task 2.1: Create BDD Tests for Drag-Drop accX Migration
**Priority**: 0 (Critical)
**Dependencies**: Phase 1 complete
**Technical Requirements**:
```markdown
1. Create feature file: tests/features/accx-drag-drop.feature
2. Test scenarios:
   - Tags have ax-draggable attribute
   - Drop zones have ax-droppable attribute
   - Keyboard navigation works via accX
   - Screen reader announces drag operations
3. Include Playwright drag-drop simulations
4. Reference: tests/playwright/test_multi_selection_integration.py
```

### Task 2.2: Replace Manual ARIA in drag-drop.js
**Priority**: 0 (Critical)
**Dependencies**: Task 2.1
**Current Implementation to Replace**:
```javascript
// CURRENT (lines 1206-1208, 2619)
liveRegion.setAttribute('aria-live', 'polite');
liveRegion.setAttribute('aria-atomic', 'true');
zoneElement.setAttribute('aria-label', zoneElement.dataset.zoneType + ' drop zone');

// REPLACEMENT
// Add ax-enhance="draggable" to tags
// Add ax-enhance="droppable" to zones
// Add ax-announce="polite" for announcements
```

**Files to Modify**:
- `apps/static/js/drag-drop.js` (remove lines 1181-1350, 2619)
- `apps/static/templates/user_home.html` (add ax- attributes)
- `apps/static/templates/drop_zone.html` (add ax- attributes)

### Task 2.3: Remove Custom Keyboard Handlers
**Priority**: 0 (Critical)
**Dependencies**: Task 2.2
**Current Implementation to Remove**:
```javascript
// Lines 1198, 1213, 1217-1350
tag.addEventListener('keydown', (event) => this.handleTagKeyboard(event));
document.addEventListener('keydown', (event) => this.handleGlobalKeyboard(event));
```

**Replacement**:
- Add `ax-keyboard="drag-drop"` to container
- accX handles all keyboard navigation automatically

### Task 2.4: Migrate Screen Reader Announcements
**Priority**: 1 (High)
**Dependencies**: Task 2.3
**Current Implementation to Replace**:
```javascript
// Lines 987-988, 1021-1022, 1159-1176
this.announceSelection(`Added ${tag.dataset.tag} to selection`);
```

**Replacement**:
- Add `ax-announce="selection"` to tags
- Add `ax-live-region="polite"` to announcement area
- Remove all manual announceSelection calls

---

## Phase 3: Group Tags Migration (Days 6-7)

### Task 3.1: Create BDD Tests for Group Tags accX
**Priority**: 1 (High)
**Dependencies**: Phase 2 complete
**Technical Requirements**:
```markdown
1. Create feature file: tests/features/accx-group-tags.feature
2. Test group expansion/collapse with accX
3. Test keyboard navigation in groups
4. Verify ARIA states are properly managed
```

### Task 3.2: Replace Group Tag ARIA Attributes
**Priority**: 1 (High)
**Dependencies**: Task 3.1
**Current Implementation**:
```javascript
// group-ui-integration.js lines 150-151, 346, 366
span.setAttribute('aria-label', `Group: ${group.name} with ${group.member_count} members`);
span.setAttribute('aria-expanded', 'false');
```

**Replacement**:
- Add `ax-enhance="expandable"` to group containers
- Add `ax-group-size="${member_count}"` for member count
- Remove manual aria-expanded toggling

### Task 3.3: Migrate Group Visual Service
**Priority**: 1 (High)
**Dependencies**: Task 3.2
**Files to Modify**:
- `apps/shared/services/group_visual.py` (lines 130-132, 287, 326)
- Replace hardcoded ARIA with ax- attributes in HTML generation

---

## Phase 4: Form and Input Migration (Days 8-9)

### Task 4.1: Create BDD Tests for Form accX
**Priority**: 1 (High)
**Dependencies**: Phase 3 complete
**Technical Requirements**:
```markdown
1. Create feature file: tests/features/accx-forms.feature
2. Test form field labeling
3. Test validation messages
4. Test keyboard navigation between fields
```

### Task 4.2: Replace Form Labels and Associations
**Priority**: 1 (High)
**Dependencies**: Task 4.1
**Current Implementation**:
```html
<!-- user_home.html lines 15-16, 43, 124 -->
<label for="tagsInPlay">tags in play</label>
<textarea id="tagsInPlay" placeholder="waiting..." aria-label="Tags in play">
```

**Replacement**:
- Add `ax-enhance="field"` to all inputs
- Add `ax-label="descriptive label"` where needed
- Remove manual label/aria-label attributes

### Task 4.3: Migrate Placeholder and Title Attributes
**Priority**: 2 (Medium)
**Dependencies**: Task 4.2
**Files to Modify**:
- All instances of `placeholder=` and `title=` attributes
- Replace with `ax-hint=` and `ax-tooltip=` respectively

---

## Phase 5: CSS and Visual Indicators Migration (Days 10-11)

### Task 5.1: Create BDD Tests for Visual accX Features
**Priority**: 2 (Medium)
**Dependencies**: Phase 4 complete
**Technical Requirements**:
```markdown
1. Create feature file: tests/features/accx-visual.feature
2. Test focus indicators are properly applied
3. Test contrast adjustments work
4. Test hover states are accessible
```

### Task 5.2: Remove Custom Focus Styles
**Priority**: 2 (Medium)
**Dependencies**: Task 5.1
**Current CSS to Remove**:
```css
/* user.css lines 1138-1151, 2372, 3291 */
.tag-item:focus-visible,
.drop-zone:focus-visible {
  /* custom styles */
}
```

**Replacement**:
- Add `ax-focus="high-contrast"` to elements
- Let accX manage all focus indicators

### Task 5.3: Remove sr-only Class
**Priority**: 2 (Medium)
**Dependencies**: Task 5.2
**Current Implementation**:
```css
/* user.css lines 3384-3385 */
.sr-only {
  /* screen reader only styles */
}
```

**Replacement**:
- Add `ax-visible="screen-reader"` for SR-only content
- Remove all sr-only class usage

---

## Phase 6: Navigation and Landmarks Migration (Days 12-13)

### Task 6.1: Create BDD Tests for Navigation accX
**Priority**: 2 (Medium)
**Dependencies**: Phase 5 complete
**Technical Requirements**:
```markdown
1. Create feature file: tests/features/accx-navigation.feature
2. Test landmark regions are properly defined
3. Test skip links are automatically generated
4. Test navigation keyboard shortcuts
```

### Task 6.2: Add Semantic Landmarks via accX
**Priority**: 2 (Medium)
**Dependencies**: Task 6.1
**Implementation**:
```html
<!-- Add to main containers -->
<div ax-enhance="landmark" ax-landmark="main">
<nav ax-enhance="navigation" ax-nav-type="primary">
<aside ax-enhance="landmark" ax-landmark="complementary">
```

### Task 6.3: Implement Skip Links
**Priority**: 1 (High)
**Dependencies**: Task 6.2
**Implementation**:
- Add `ax-skip-link="main"` to body
- Add `ax-skip-target="main"` to main content area
- accX automatically generates skip navigation

---

## Phase 7: Testing and Validation (Days 14-15)

### Task 7.1: Comprehensive accX Testing
**Priority**: 0 (Critical)
**Dependencies**: All phases complete
**Test Suite**:
```bash
# Run all accX BDD tests
uv run pytest tests/features/accx-*.feature -v

# Run WCAG compliance tests
uv run pytest tests/accessibility/wcag_compliance.py -v

# Run Playwright accessibility tests
uv run pytest tests/playwright/test_accx_integration.py -v
```

### Task 7.2: Remove Legacy Accessibility Code
**Priority**: 0 (Critical)
**Dependencies**: Task 7.1 passes
**Cleanup Tasks**:
1. Remove all manual ARIA attribute setting code
2. Remove all keyboard event handlers for accessibility
3. Remove all screen reader announcement functions
4. Remove sr-only and other a11y CSS classes
5. Remove manual focus management code

### Task 7.3: Performance Validation
**Priority**: 1 (High)
**Dependencies**: Task 7.2
**Metrics to Validate**:
- accX bootloader loads in <10ms
- Pattern detection completes in <20ms
- No performance regression in drag-drop operations
- Memory usage remains stable

---

## Phase 8: Documentation and Deployment (Days 16-17)

### Task 8.1: Update Developer Documentation
**Priority**: 1 (High)
**Dependencies**: Phase 7 complete
**Documentation Updates**:
1. Remove all references to manual ARIA implementation
2. Add accX attribute reference guide
3. Update onboarding documentation
4. Create migration guide for future components

### Task 8.2: Create accX Configuration
**Priority**: 1 (High)
**Dependencies**: Task 8.1
**Configuration File**: `accx.config.js`
```javascript
export default {
  bootloader: {
    cdnUrl: 'https://cdn.genx.software/accx@1.0/loader.js',
    loadAfterPaint: true,
    patterns: ['drag-drop', 'forms', 'navigation']
  },
  enhancements: {
    autoDetect: true,
    wcagLevel: 'AA',
    keyboardShortcuts: true,
    skipLinks: true
  }
};
```

### Task 8.3: Production Deployment
**Priority**: 0 (Critical)
**Dependencies**: Task 8.2
**Deployment Checklist**:
- [ ] All tests passing at 100%
- [ ] No accessibility regressions
- [ ] accX CDN configured for production
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented

---

## bd Task Structure

```bash
# Create epic
EPIC_ID=$(bd create "Migrate all accessibility to accX" -t epic -p 0 \
  -d "Complete migration from manual ARIA to declarative accX attributes" --json | jq -r '.id')

# Phase 1: Foundation
PHASE1_ID=$(bd create "Phase 1: accX Foundation Setup" -t feature -p 0 \
  --deps parent-child:$EPIC_ID --json | jq -r '.id')

# Phase 1 Tasks
bd create "Create BDD tests for accX integration" -t task -p 0 \
  --deps parent-child:$PHASE1_ID --json

bd create "Integrate accX bootloader" -t task -p 0 \
  --deps parent-child:$PHASE1_ID,blocks:<previous-task-id> --json

# Phase 2: Drag-Drop
PHASE2_ID=$(bd create "Phase 2: Drag-Drop System Migration" -t feature -p 0 \
  --deps parent-child:$EPIC_ID,blocks:$PHASE1_ID --json | jq -r '.id')

# Continue for all phases...
```

---

## Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| accX CDN unavailable | Low | High | Local fallback, cached version |
| Performance degradation | Medium | Medium | Comprehensive benchmarking before/after |
| Incompatible patterns | Low | High | Thorough testing, gradual rollout |
| Browser compatibility | Low | Medium | accX handles cross-browser support |

### Rollback Strategy

1. **Feature flags**: Implement accX behind feature flag initially
2. **Parallel implementation**: Keep legacy code during migration
3. **Staged rollout**: Deploy to subset of users first
4. **Quick revert**: Single flag to disable accX and restore legacy

---

## Success Metrics

### Technical Metrics
- **Code Reduction**: >80% reduction in accessibility-related code
- **Performance**: <10ms accX initialization time
- **Test Coverage**: 100% of accessibility features tested
- **WCAG Compliance**: Maintain AA rating throughout

### Quality Metrics
- **Zero Regressions**: No loss of existing accessibility features
- **Improved Consistency**: All components follow same patterns
- **Simplified Maintenance**: Single declarative approach
- **Developer Velocity**: 50% faster to add accessibility to new features

---

## Implementation Timeline

| Phase | Duration | Start Date | End Date | Status |
|-------|----------|------------|----------|---------|
| Phase 1: Foundation | 2 days | Day 1 | Day 2 | Pending |
| Phase 2: Drag-Drop | 3 days | Day 3 | Day 5 | Pending |
| Phase 3: Group Tags | 2 days | Day 6 | Day 7 | Pending |
| Phase 4: Forms | 2 days | Day 8 | Day 9 | Pending |
| Phase 5: Visual | 2 days | Day 10 | Day 11 | Pending |
| Phase 6: Navigation | 2 days | Day 12 | Day 13 | Pending |
| Phase 7: Testing | 2 days | Day 14 | Day 15 | Pending |
| Phase 8: Deployment | 2 days | Day 16 | Day 17 | Pending |

**Total Duration**: 17 working days

---

## Appendix A: Current Accessibility Inventory

### Files Requiring Migration (Priority Order)

1. **Critical Path (Phase 2)**:
   - `apps/static/js/drag-drop.js` - 200+ lines of a11y code
   - `apps/static/js/drag-drop.min.js` - Minified version
   - `apps/static/templates/user_home.html` - Primary UI

2. **High Priority (Phase 3)**:
   - `apps/static/js/group-tags.js` - Group interaction code
   - `apps/static/js/group-ui-integration.js` - Group UI code
   - `apps/shared/services/group_visual.py` - Server-side rendering

3. **Medium Priority (Phase 4-5)**:
   - `apps/static/css/user.css` - Focus and visual styles
   - `apps/static/templates/drop_zone.html` - Zone templates
   - `apps/static/templates/base.html` - Base template

4. **Lower Priority (Phase 6)**:
   - `apps/static/templates/components/navigation.html`
   - `apps/admin/templates/pages/users.html`
   - Various documentation files

### Patterns to Replace

| Current Pattern | accX Replacement |
|-----------------|------------------|
| `aria-label="text"` | `ax-label="text"` |
| `aria-expanded="false"` | `ax-enhance="expandable"` |
| `role="button"` | `ax-enhance="button"` |
| `aria-live="polite"` | `ax-announce="polite"` |
| `tabindex="0"` | Automatic with `ax-enhance` |
| `.sr-only` class | `ax-visible="screen-reader"` |
| `:focus-visible` styles | `ax-focus="high-contrast"` |
| Manual keyboard handlers | `ax-keyboard="pattern"` |

---

## Appendix B: Validation Checklist

### Pre-Migration Validation
- [ ] Current WCAG score documented
- [ ] All accessibility features inventoried
- [ ] User journey tests passing
- [ ] Screen reader testing baseline established

### Post-Migration Validation
- [ ] WCAG score maintained or improved
- [ ] All accX attributes properly applied
- [ ] No manual ARIA code remaining
- [ ] Screen reader announces all operations
- [ ] Keyboard navigation fully functional
- [ ] Focus indicators visible and clear
- [ ] Skip links working
- [ ] Form labels properly associated
- [ ] Color contrast passing
- [ ] No JavaScript errors in console

### Performance Validation
- [ ] Page load time not increased
- [ ] Drag-drop operations <16ms
- [ ] No memory leaks
- [ ] accX bundle cached properly

---

**Document Status**: Complete and ready for implementation
**Next Steps**: Create bd epic and begin Phase 1 task execution
**Review Date**: Before Phase 7 completion