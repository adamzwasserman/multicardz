# multicardz Keyboard Navigation Audit
## Complete Inventory of Keyboard Event Handlers

**Audit Date**: 2025-11-12
**Purpose**: Document all keyboard handlers for migration to accX
**Scope**: Identify keydown/keypress handlers, navigation patterns, shortcuts, focus management

---

## 1. drag-drop.js Keyboard Handlers

### 1.1 Tag Keyboard Navigation (handleTagKeyboard)
**Location**: `apps/static/js/drag-drop.js` lines 1220-1301

**Registered**: Line 1198 - `tag.addEventListener('keydown', (event) => this.handleTagKeyboard(event))`

**Keys Handled**:
- **ArrowRight / ArrowDown** (lines 1230-1244):
  - Navigate to next tag
  - `event.preventDefault()` called
  - If `Shift` held: Add to selection
  - Calls `ensureFocusVisible()` for scroll management
  - Calls `updateARIAStates()` after selection

- **ArrowLeft / ArrowUp** (lines 1247-1262):
  - Navigate to previous tag
  - `event.preventDefault()` called
  - If `Shift` held: Add to selection
  - Focus management + ARIA updates

- **Space / Enter** (lines 1264-1286):
  - `event.preventDefault()` called
  - **Ctrl/Cmd + Space/Enter**: Toggle selection
  - **Shift + Space/Enter**: Range selection
  - **Plain Space/Enter**: Clear and select single
  - Announces selection changes via `announceSelectionChange()`
  - Updates ARIA states

- **Escape** (lines 1288-1292):
  - Clear all selections
  - Update ARIA states
  - Announce "Selection cleared"

**Pattern**: Complete arrow key navigation with modifier key support (Shift, Ctrl/Cmd)

**accX Migration**: accX provides `ax-enhance="keyboard-nav"` for arrow keys, but may need custom pattern for multi-selection modifiers

---

### 1.2 Global Keyboard Shortcuts (handleGlobalKeyboard)
**Location**: `apps/static/js/drag-drop.js` lines 1307-1318

**Registered**: Line 1213 - `document.addEventListener('keydown', (event) => this.handleGlobalKeyboard(event))`

**Keys Handled**:
- **Ctrl/Cmd + A** (lines 1309-1316):
  - Select all tags in current container
  - `event.preventDefault()` only if focus in tag area
  - Context-aware: Only works in `.cloud`, `.tag-collection`, or `[data-tag]`
  - Calls `selectAllTags()` method

**Pattern**: Global shortcut with context awareness

**accX Migration**: Custom shortcut pattern - accX may not provide select-all out of box

---

### 1.3 Supporting Methods

**selectAllTags()** (lines 1323-1333):
- Selects all visible `[data-tag]:not([hidden])` elements
- Clears existing selection first
- Updates ARIA states
- Announces count: "All X tags selected"

**announceSelectionChange()** (lines 1338-1349):
- Screen reader announcements for individual selections
- Messages: "added", "removed", "selected"
- Calls `announceSelection()` with formatted message

**ensureFocusVisible()** (lines 1355-1359+):
- Scrolls focused element into view if needed
- Checks `getBoundingClientRect()` vs viewport
- Manual scroll management

**Pattern**: Custom focus management, screen reader integration

**accX Migration**: accX should handle focus visibility automatically

---

## 2. app.js Keyboard Handlers

### 2.1 Tag Input - Comma/Enter Submission
**Location**: `apps/static/js/app.js` line 406

**Code**: `input.addEventListener('keypress', (e) => { ... })`

**Keys Handled**:
- **Comma (,)**: Submit tag and clear input
- **Enter**: Submit tag and clear input

**Pattern**: Form submission on delimiter keys

**accX Migration**: Keep as-is (business logic, not accessibility)

---

### 2.2 Group Input - Enter Submission
**Location**: `apps/static/js/app.js` line 420

**Code**: `input.addEventListener('keypress', async function(e) { ... })`

**Keys Handled**:
- **Enter**: Submit group and clear input (async)

**Pattern**: Async form submission

**accX Migration**: Keep as-is (business logic)

---

### 2.3 Global Document Shortcuts
**Location**: `apps/static/js/app.js` line 798

**Code**: `document.addEventListener('keydown', (e) => { ... })`

**Keys Handled**: Not specified in audit (need to read full handler)

**Pattern**: Global shortcuts

**accX Migration**: TBD - need full handler code

---

## 3. group-tags.js Keyboard Handler

### 3.1 Document-Level Keyboard Events
**Location**: `apps/static/js/group-tags.js` line 390

**Code**: `document.addEventListener('keydown', (e) => { ... })`

**Keys Handled**: Not specified in audit (need to read full handler)

**Pattern**: Global keyboard handling for groups

**accX Migration**: TBD - need full handler code

---

## 4. group-ui-integration.js Keyboard Handlers

### 4.1 Element-Specific Handler
**Location**: `apps/static/js/group-ui-integration.js` line 215

**Code**: `element.addEventListener('keydown', (e) => { ... })`

**Keys Handled**: Not specified (need context)

**Pattern**: Element-specific keyboard interaction

**accX Migration**: TBD

---

### 4.2 Group Input Handler
**Location**: `apps/static/js/group-ui-integration.js` line 648

**Code**: `groupInput.addEventListener('keydown', (e) => { ... })`

**Keys Handled**: Not specified (likely Enter/Escape for input)

**Pattern**: Input-specific keyboard handling

**accX Migration**: TBD

---

### 4.3 Document-Level Handler
**Location**: `apps/static/js/group-ui-integration.js` line 660

**Code**: `document.addEventListener('keydown', (e) => { ... })`

**Keys Handled**: Not specified (global shortcuts)

**Pattern**: Global keyboard shortcuts

**accX Migration**: TBD

---

## 5. Summary Statistics

### Keyboard Handlers Identified
- **drag-drop.js**: 2 handlers (tag navigation + global shortcuts)
- **app.js**: 3 handlers (tag input + group input + global)
- **group-tags.js**: 1 handler (global)
- **group-ui-integration.js**: 3 handlers (element + input + global)

**Total**: 9 keyboard event handlers

### Keys Handled (Confirmed)
- **Arrow Keys**: Full 4-direction navigation with Shift modifier
- **Space/Enter**: Selection with Ctrl/Cmd/Shift modifiers
- **Escape**: Clear selection
- **Ctrl/Cmd + A**: Select all
- **Comma**: Tag input submission
- **Enter**: Form submissions (multiple contexts)

### Additional Investigation Needed
- app.js line 798 global handler
- group-tags.js line 390 handler
- group-ui-integration.js all 3 handlers

---

## 6. Focus Management Patterns

### Manual Focus Control
- **Line 1237, 1254**: `tag.focus()` - Explicit focus movement
- **Line 1355+**: `ensureFocusVisible()` - Manual scroll into view

### Focus Indicators
- ARIA states updated after focus changes
- Screen reader announcements on focus movement

**Pattern**: Full manual focus management

**accX Migration**: accX provides automatic focus management with `ax-enhance="focusable"`

---

## 7. Screen Reader Integration

### Announcement Patterns
- Selection changes announced immediately
- Count-based announcements ("All X tags selected")
- Action-specific messages ("added", "removed", "selected")

### Live Region Usage
- Uses live region created in setup (see accessibility-audit.md)
- Polite assertions (non-intrusive)

**Pattern**: Comprehensive screen reader feedback

**accX Migration**: Use `ax-announce` pattern for announcements

---

## 8. accX Migration Strategy

### High Priority (Core Accessibility)
1. **Arrow key navigation** (drag-drop.js handleTagKeyboard)
   - Replace with `ax-enhance="keyboard-nav"`
   - May need custom pattern for Shift modifier multi-select

2. **Focus management** (ensureFocusVisible)
   - Let accX handle automatically
   - Remove manual scroll logic

3. **Screen reader announcements** (announceSelectionChange)
   - Replace with `ax-announce` pattern
   - Remove manual live region updates

### Medium Priority (Enhanced Interactions)
4. **Ctrl/Cmd + A select all** (handleGlobalKeyboard)
   - Custom accX shortcut pattern
   - Preserve context awareness

5. **Space/Enter selection** (handleTagKeyboard)
   - May need custom pattern for multi-select modes
   - accX default may not support Ctrl/Cmd/Shift modifiers

### Low Priority (Business Logic)
6. **Form submissions** (app.js comma/enter handlers)
   - Keep as-is (not accessibility, business logic)
   - No accX migration needed

### Requires Investigation
7. **Remaining handlers** (app.js:798, group-tags.js:390, group-ui-integration.js:215/648/660)
   - Need to read full handler code
   - Determine if accessibility or business logic
   - Plan migration accordingly

---

## 9. Code Removal Targets

### After accX Migration Complete
Remove from drag-drop.js:
- `handleTagKeyboard()` method (lines 1220-1301)
- `handleGlobalKeyboard()` method (lines 1307-1318)
- `selectAllTags()` method (lines 1323-1333)
- `announceSelectionChange()` method (lines 1338-1349)
- `ensureFocusVisible()` method (lines 1355+)
- Event listeners on lines 1198, 1213

**Estimated LOC Removed**: ~150 lines from drag-drop.js

---

## 10. Acceptance Criteria

- [ ] All arrow key navigation handled by accX
- [ ] Multi-select modifiers (Shift, Ctrl/Cmd) preserved
- [ ] Ctrl/Cmd + A select-all working
- [ ] Focus visible without manual scroll management
- [ ] Screen reader announcements via ax-announce
- [ ] Zero keydown addEventListener in accessibility code
- [ ] Business logic handlers preserved (comma, enter for forms)
- [ ] All keyboard shortcuts documented in user guide
- [ ] Keyboard-only users can navigate entire interface
- [ ] Tab order logical and complete

---

**Audit Status**: Partial - 9 handlers identified, 5 need detailed investigation
**Next Step**: Complete investigation of remaining handlers, then proceed to BDD test creation
