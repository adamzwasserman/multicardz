# multicardz Accessibility Audit
## Complete Inventory of Manual ARIA Implementations

**Audit Date**: 2025-11-12
**Purpose**: Document all manual accessibility implementations for migration to accX
**Scope**: Identify ARIA attributes, keyboard handlers, focus management, and screen reader patterns

---

## 1. JavaScript ARIA Implementation (drag-drop.js)

### 1.1 Selection State (aria-selected)
**Location**: `apps/static/js/drag-drop.js`

- **Line 969**: `tag.setAttribute('aria-selected', 'true');` - Mark tag as selected
- **Line 1002**: `tag.setAttribute('aria-selected', 'false');` - Deselect tag
- **Line 1033**: `tag.setAttribute('aria-selected', 'false');` - Clear selection
- **Line 1142**: `tag.setAttribute('aria-selected', isSelected.toString());` - Toggle selection state
- **Line 1194**: `tag.setAttribute('aria-selected', 'false');` - Initialize selection state

**Pattern**: Manual selection state management with aria-selected attribute

**accX Migration**: Replace with `ax-enhance="selectable"` or custom selection pattern

---

### 1.2 Multi-Selection Container (aria-multiselectable)
**Location**: `apps/static/js/drag-drop.js`

- **Line 1187**: `container.setAttribute('aria-multiselectable', 'true');` - Enable multi-selection

**Pattern**: Container-level multi-selection support

**accX Migration**: Container should have `ax-enhance="multi-select-container"`

---

### 1.3 Keyboard Navigation (tabindex)
**Location**: `apps/static/js/drag-drop.js`

- **Line 1195**: `tag.setAttribute('tabindex', '0');` - Make tag keyboard focusable
- **Line 1685**: `tag.setAttribute('tabindex', '0');` - Enable keyboard navigation

**Pattern**: Manual tabindex management for keyboard accessibility

**accX Migration**: accX automatically manages tabindex for interactive elements

---

### 1.4 Live Region Announcements (aria-live, aria-atomic)
**Location**: `apps/static/js/drag-drop.js`

- **Line 1206**: `liveRegion.setAttribute('aria-live', 'polite');` - Screen reader announcements
- **Line 1207**: `liveRegion.setAttribute('aria-atomic', 'true');` - Announce complete content
- **Line 1208**: `liveRegion.className = 'sr-only';` - Visually hide live region

**Pattern**: Custom live region creation for screen reader feedback

**accX Migration**: Use `ax-announce` pattern for dynamic announcements

---

### 1.5 Drag State (aria-grabbed)
**Location**: `apps/static/js/drag-drop.js`

- **Line 1562**: `el.setAttribute('aria-grabbed', 'false');` - Initialize drag state
- **Line 1684**: `tag.setAttribute('aria-grabbed', 'false');` - Not being dragged
- **Line 2323**: `el.setAttribute('aria-grabbed', 'true');` - Currently dragging
- **Line 2348**: `el.setAttribute('aria-grabbed', 'false');` - Drag ended

**Pattern**: Manual drag state for screen readers

**accX Migration**: Combined with dragX if used, or custom `ax-drag-state` pattern

---

### 1.6 Drop Zone Labels (aria-label)
**Location**: `apps/static/js/drag-drop.js`

- **Line 2619**: `zoneElement.setAttribute('aria-label', zoneElement.dataset.zoneType + ' drop zone');` - Dynamic zone labeling

**Pattern**: Programmatic aria-label creation

**accX Migration**: Use `ax-label` or template-based labeling

---

## 2. HTML Template ARIA Implementation

### 2.1 Form Elements (aria-label)
**Location**: `apps/static/templates/base.html`

- **Line 223**: `<div class="settings-input" aria-label="User email address">` - Input label
- **Line 233**: `<select class="settings-select" id="fontSelector" aria-label="Font family selector">` - Select label

**Location**: `apps/static/templates/user_home.html`

- **Line 16**: `<textarea ... aria-label="Tags in play" readonly>` - Textarea label
- **Line 43**: `<input type="text" class="tag-input" aria-label="add user tag">` - Input label
- **Line 124**: `<input type="text" class="tag-input group-input" aria-label="Add group">` - Input label

**Pattern**: Manual aria-label on form inputs

**accX Migration**: Use `ax-enhance="field"` with automatic label association

---

### 2.2 Interactive Buttons (role, tabindex, aria-label, aria-expanded)
**Location**: `apps/static/templates/user_home.html`

- **Lines 9, 146, 281**: Collapse toggle buttons with `aria-label="Toggle row X"`
- **Lines 103-106**: Group tag with:
  - `role="button"` - Button semantics
  - `tabindex="0"` - Keyboard focusable
  - `aria-label="Group: {{ group.name }}"` - Descriptive label
  - `aria-expanded="false"` - Expandable state

**Pattern**: Manual button role and state management

**accX Migration**: Use `ax-enhance="button"` for buttons, `ax-enhance="expandable"` for collapsible sections

---

### 2.3 Data Role Attribute
**Location**: `apps/static/templates/drop_zone.html`

- **Line 26**: `<span data-role="prompt">` - Non-ARIA semantic marker

**Pattern**: Custom data attribute for component identification

**accX Migration**: Can remain as-is (not ARIA-related)

---

## 3. CSS Accessibility Classes

### 3.1 Screen Reader Only (.sr-only)
**Location**: `apps/static/css/user.css`

- **Line 3385**: `.sr-only` class definition (likely contains position: absolute; clip: rect(0,0,0,0))

**Location**: `apps/static/js/drag-drop.js`

- **Line 1208**: Applied to live region: `liveRegion.className = 'sr-only';`

**Pattern**: Visually hidden but screen reader accessible content

**accX Migration**: Replace with `ax-visible="screen-reader"` attribute

---

## 4. Summary Statistics

### Total Manual ARIA Attributes
- **aria-selected**: 5 occurrences
- **aria-multiselectable**: 1 occurrence
- **aria-live**: 1 occurrence
- **aria-atomic**: 1 occurrence
- **aria-grabbed**: 4 occurrences
- **aria-label**: 8 occurrences
- **aria-expanded**: 1 occurrence
- **role**: 1 occurrence
- **tabindex**: 2 occurrences (manual)
- **.sr-only**: 1 CSS class + 1 JS usage

**Total**: 25 manual accessibility implementations across 13 files

---

## 5. Migration Priority

### High Priority (Frequently Used)
1. **aria-selected** (5 uses) - Tag selection state
2. **aria-grabbed** (4 uses) - Drag state
3. **aria-label** (8 uses) - Element labels

### Medium Priority (Component-Specific)
4. **aria-live/aria-atomic** (2 uses) - Live regions
5. **role/tabindex** (3 uses) - Interactive elements
6. **.sr-only** (2 uses) - Hidden content

### Low Priority (Single Use)
7. **aria-multiselectable** (1 use) - Container state
8. **aria-expanded** (1 use) - Expandable state

---

## 6. Files Requiring Modification

1. **apps/static/js/drag-drop.js** - 14 ARIA attribute assignments, 1 .sr-only usage
2. **apps/static/templates/user_home.html** - 7 ARIA attributes
3. **apps/static/templates/base.html** - 2 ARIA attributes
4. **apps/static/css/user.css** - 1 .sr-only class definition

---

## 7. accX Migration Strategy

### Phase 1: Replace Common Patterns
- Convert aria-label to `ax-label=""`
- Convert aria-selected to `ax-enhance="selectable"`
- Convert role="button" + tabindex to `ax-enhance="button"`

### Phase 2: Custom Patterns
- Create custom accX pattern for drag state (aria-grabbed)
- Create custom pattern for multi-selection containers
- Create custom pattern for live region announcements

### Phase 3: Visual Classes
- Replace .sr-only with `ax-visible="screen-reader"`
- Remove CSS class definitions

### Phase 4: Remove Manual Code
- Remove all setAttribute('aria-*') calls from drag-drop.js
- Remove manual tabindex management
- Remove manual live region creation

---

## 8. Acceptance Criteria

- [ ] All manual ARIA attributes replaced with accX declarations
- [ ] Zero aria-* setAttribute calls in JavaScript
- [ ] .sr-only CSS class removed
- [ ] All existing screen reader functionality preserved
- [ ] Lighthouse accessibility score remains 100
- [ ] WCAG 2.1 AA compliance maintained
- [ ] Performance <10ms for accX initialization

---

**Audit Complete**: Ready for Phase 2 (accX Integration)
