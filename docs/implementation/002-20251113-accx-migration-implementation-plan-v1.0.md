# accX Accessibility Migration Implementation Plan
## Document Version: 1.0
## Date: 2025-11-13
## Ordinal: 002
## Status: READY FOR EXECUTION

---

## Executive Summary

This implementation plan details the comprehensive migration of all accessibility features in multicardz to use the accX declarative accessibility system from the genX platform. The migration will replace 300+ lines of manual ARIA implementations, custom keyboard handlers, focus management code, and screen reader optimizations with declarative accX attributes.

**Key Outcomes:**
- Replace all manual ARIA attributes with declarative `ax-enhance` patterns
- Eliminate custom keyboard handling code (200+ lines)
- Remove `.sr-only` CSS class in favor of `ax-visible="screen-reader"`
- Integrate genx.software universal bootloader (1KB)
- Achieve <10ms initialization time
- Maintain 100% Lighthouse accessibility scores
- Enable WCAG 2.1 AA compliance through automation

---

## Technical Architecture Alignment

### multicardz Current State
- **Manual ARIA**: 12 files with hand-coded ARIA attributes
- **Custom Keyboard**: 200+ lines of keyboard navigation in drag-drop.js
- **Focus Management**: Custom focus tracking and restoration
- **Screen Reader**: `.sr-only` CSS class for hidden announcements
- **Live Regions**: Manual ARIA live region management

### Target State with accX
- **Declarative Attributes**: `ax-enhance="drag-drop"` replaces all manual ARIA
- **Automatic Keyboard**: accX handles navigation, no custom code needed
- **Smart Focus**: accX focus management with intent-based restoration
- **Screen Reader**: `ax-visible="screen-reader"` declarative attribute
- **Live Announcements**: `ax-announce="polite"` for state changes

### Patent Compliance Verification
- ✅ Set theory operations remain in Python backend (unchanged)
- ✅ Polymorphic drop zones continue using backend HTML rendering
- ✅ DATAOS compliance maintained (no caching in accX)
- ✅ Spatial tag manipulation paradigms preserved

---

## Phase Structure

### Phase 1: Foundation and Analysis (Day 1)
- Comprehensive codebase audit for accessibility code
- Create BDD test suite for current behavior
- Set up accX integration environment
- Establish performance benchmarks

### Phase 2: accX Integration (Day 2)
- Integrate genx.software bootloader
- Configure accX for multicardz requirements
- Create custom drag-drop enhancement pattern
- Implement progressive disclosure strategy

### Phase 3: Migration Execution (Days 3-4)
- Replace manual ARIA with ax-enhance attributes
- Remove custom keyboard handlers
- Migrate focus management to accX
- Update templates with declarative patterns

### Phase 4: Validation and Optimization (Day 5)
- Run comprehensive BDD test suite
- Performance benchmarking (<10ms target)
- Lighthouse accessibility audit (100 score)
- WCAG 2.1 AA compliance verification

### Phase 5: Documentation and Rollout (Day 6)
- Update developer documentation
- Create migration guide for similar projects
- Implement feature flags for safe deployment
- Production rollout with monitoring

---

## bd Task Structure

### Epic Creation and Phase Setup

```bash
# Create the main epic
EPIC_ID=$(bd create "Migrate multicardz accessibility to accX declarative system" \
  -t epic \
  -p 1 \
  -d "Complete migration of all accessibility features from manual ARIA/keyboard handling to accX declarative patterns. Success criteria: 100% Lighthouse score, <10ms init time, all BDD tests passing, zero regression in functionality." \
  --json | jq -r '.id')

# Phase 1: Foundation and Analysis
PHASE1_ID=$(bd create "Phase 1: Foundation - Audit and BDD Test Suite" \
  -t feature \
  -p 1 \
  -d "Comprehensive audit of current accessibility implementation and creation of BDD test suite to prevent regression" \
  --deps parent-child:$EPIC_ID \
  --json | jq -r '.id')

# Phase 2: accX Integration (depends on Phase 1)
PHASE2_ID=$(bd create "Phase 2: accX Integration - Bootloader and Configuration" \
  -t feature \
  -p 1 \
  -d "Integrate genx.software bootloader and configure accX for multicardz-specific requirements" \
  --deps parent-child:$EPIC_ID,blocks:$PHASE1_ID \
  --json | jq -r '.id')

# Phase 3: Migration Execution (depends on Phase 2)
PHASE3_ID=$(bd create "Phase 3: Migration - Replace Manual Implementations" \
  -t feature \
  -p 1 \
  -d "Replace all manual ARIA, keyboard handlers, and focus management with accX declarative patterns" \
  --deps parent-child:$EPIC_ID,blocks:$PHASE2_ID \
  --json | jq -r '.id')

# Phase 4: Validation (depends on Phase 3)
PHASE4_ID=$(bd create "Phase 4: Validation - Testing and Performance" \
  -t feature \
  -p 1 \
  -d "Comprehensive testing, performance benchmarking, and accessibility compliance verification" \
  --deps parent-child:$EPIC_ID,blocks:$PHASE3_ID \
  --json | jq -r '.id')

# Phase 5: Rollout (depends on Phase 4)
PHASE5_ID=$(bd create "Phase 5: Documentation and Production Rollout" \
  -t feature \
  -p 1 \
  -d "Documentation updates, feature flags, and safe production deployment" \
  --deps parent-child:$EPIC_ID,blocks:$PHASE4_ID \
  --json | jq -r '.id')
```

### Phase 1 Tasks: Foundation and Analysis

```bash
# Task 1.1: Audit manual ARIA implementations
TASK1_1=$(bd create "Audit all manual ARIA attribute implementations" \
  -t task -p 1 \
  -d "Files to audit:
      - apps/static/js/drag-drop.js (lines 969, 1002, 1033, 1142, 1187-1209, 1562, 1684, 2323, 2348, 2619)
      - apps/static/templates/base.html
      - apps/static/templates/user_home.html
      - apps/static/templates/drop_zone.html
      - apps/admin/templates/pages/users.html
      Document all ARIA patterns: role, aria-selected, aria-grabbed, aria-label, aria-live, aria-atomic, tabindex
      Output: accessibility-audit.md with complete inventory" \
  --deps parent-child:$PHASE1_ID \
  --json | jq -r '.id')

# Task 1.2: Audit keyboard handling code
TASK1_2=$(bd create "Audit all keyboard event handlers and navigation" \
  -t task -p 1 \
  -d "Files to audit:
      - apps/static/js/drag-drop.js: handleTagKeyboard (line 1220), handleGlobalKeyboard (line 1213)
      - apps/static/js/app.js: keypress handlers (lines 406, 420, 798)
      - apps/static/js/group-tags.js: keyboard handler (line 390)
      - apps/static/js/group-ui-integration.js: keyboard handlers (lines 215, 648, 660)
      Document: navigation patterns, shortcuts, focus management
      Output: keyboard-audit.md with handler inventory" \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_1 \
  --json | jq -r '.id')

# Task 1.3: Create BDD tests for current accessibility
TASK1_3=$(bd create "Create BDD tests for current accessibility behavior" \
  -t task -p 1 \
  -d "1. Create feature file: tests/features/accessibility-current.feature
      2. Create step definitions: tests/step_definitions/test_accessibility_current_steps.py
      3. Framework: pytest-bdd with Playwright for browser testing
      4. Test scenarios:
         - ARIA attributes properly applied to tags and zones
         - Keyboard navigation (arrow keys, tab, space/enter)
         - Screen reader announcements for state changes
         - Focus management during drag operations
         - Live region updates for tag selection
      5. Include scenarios() to load feature file
      6. Reference: tests/step_definitions/test_set_operations_steps.py
      7. Validation: uv run pytest tests/features/accessibility-current.feature -v
      8. Must fail initially with assertion errors (not missing steps)" \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_2 \
  --json | jq -r '.id')

# Task 1.4: Benchmark current performance
TASK1_4=$(bd create "Benchmark current accessibility implementation performance" \
  -t task -p 1 \
  -d "Create performance benchmarks:
      1. Script location: tests/benchmarks/accessibility_performance.py
      2. Metrics to capture:
         - Initial ARIA application time
         - Keyboard event handler response time
         - Focus management overhead
         - Live region update latency
         - Memory usage for accessibility features
      3. Test with 100, 1000, 5000 tags
      4. Output: baseline-performance.json
      5. Target: Establish baseline for <10ms accX target" \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_3 \
  --json | jq -r '.id')
```

### Phase 2 Tasks: accX Integration

```bash
# Task 2.1: Integrate genx.software bootloader
TASK2_1=$(bd create "Integrate genx.software universal bootloader" \
  -t task -p 1 \
  -d "1. Add bootloader script to base.html template:
         <script src='https://cdn.genx.software/bootloader.min.js'
                 integrity='sha384-...' crossorigin='anonymous' defer></script>
      2. Configure bootloader in template:
         <script>window.genxConfig = { modules: ['accX'], lazyLoad: true }</script>
      3. Update Content Security Policy if needed
      4. Verify bootloader loads after first paint (0ms TBT)
      5. Confirm module detection for ax- attributes
      6. Test with: uv run uvicorn apps.user.main:create_app --factory --reload --port 8011" \
  --deps parent-child:$PHASE2_ID \
  --json | jq -r '.id')

# Task 2.2: Configure accX for multicardz
TASK2_2=$(bd create "Configure accX for multicardz-specific requirements" \
  -t task -p 1 \
  -d "1. Create configuration in apps/static/js/accx-config.js:
         window.accXConfig = {
           progressive: true,  // Start with lightweight features
           dragDrop: {
             zones: ['available', 'included', 'excluded'],
             multiSelect: true,
             announcePattern: 'Tag {name} moved to {zone}',
             preserveState: false  // DATAOS compliance
           },
           keyboard: {
             navigation: 'arrow',
             selection: 'space',
             multiSelect: 'ctrl',
             shortcuts: { clearAll: 'escape' }
           }
         }
      2. Load config before bootloader
      3. Verify accX respects DATAOS (no caching)
      4. Test configuration with browser console" \
  --deps parent-child:$PHASE2_ID,blocks:$TASK2_1 \
  --json | jq -r '.id')

# Task 2.3: Create custom drag-drop enhancement pattern
TASK2_3=$(bd create "Create accX custom pattern for multicardz drag-drop" \
  -t task -p 1 \
  -d "1. Create pattern file: apps/static/js/accx-multicardz-pattern.js
      2. Register pattern with accX:
         accX.registerPattern('multicardz-drag', {
           selector: '[data-tag], [data-zone-type]',
           enhance: (element) => {
             // Pattern for tags and zones
             // Must preserve set theory operations
             // Backend HTML rendering unchanged
           },
           keyboard: {
             // Arrow navigation between tags
             // Space/Enter for selection
             // Drag to zones with keyboard
           },
           announce: {
             // Screen reader announcements
             // Selection state changes
             // Zone drop confirmations
           }
         })
      3. Pattern must handle polymorphic zones
      4. Maintain backend-driven state
      5. Test with existing drag-drop system" \
  --deps parent-child:$PHASE2_ID,blocks:$TASK2_2 \
  --json | jq -r '.id')

# Task 2.4: Implement progressive disclosure
TASK2_4=$(bd create "Configure accX progressive disclosure for performance" \
  -t task -p 1 \
  -d "1. Configure two-tier loading:
         Tier 1 (immediate): Focus indicators, contrast
         Tier 2 (on-demand): Full ARIA, keyboard nav, announcements
      2. Implement in accx-config.js:
         progressive: {
           immediate: ['focus', 'contrast'],
           lazy: ['aria', 'keyboard', 'announce'],
           trigger: 'interaction'  // Load Tier 2 on first interaction
         }
      3. Measure load times:
         - Tier 1: <5ms target
         - Tier 2: <10ms after trigger
      4. Test with Lighthouse performance audit
      5. Verify no impact on initial page load" \
  --deps parent-child:$PHASE2_ID,blocks:$TASK2_3 \
  --json | jq -r '.id')
```

### Phase 3 Tasks: Migration Execution

```bash
# Task 3.1: Replace ARIA attributes with ax-enhance
TASK3_1=$(bd create "Replace all manual ARIA with ax-enhance declarations" \
  -t task -p 1 \
  -d "Files to modify:
      1. apps/static/js/drag-drop.js:
         - Remove lines 969, 1002, 1033 (aria-selected)
         - Remove lines 1187-1195 (role, aria-multiselectable)
         - Remove lines 1562, 2323, 2348 (aria-grabbed)
         - Remove lines 1684-1685 (role=button, aria-grabbed)
         - Remove line 2619 (aria-label)
      2. apps/static/templates/base.html:
         - Add ax-enhance='page' to body
         - Add ax-landmarks='auto' for sections
      3. apps/static/templates/drop_zone.html:
         - Replace manual ARIA with ax-enhance='drop-zone'
         - Add ax-drop-zone='{type}' for zone type
      4. Update tag rendering:
         - Add ax-enhance='draggable-tag'
         - Add ax-selectable='multi'
      5. Test each change incrementally
      6. Verify with browser DevTools accessibility tree" \
  --deps parent-child:$PHASE3_ID \
  --json | jq -r '.id')

# Task 3.2: Remove custom keyboard handlers
TASK3_2=$(bd create "Remove custom keyboard event handlers" \
  -t task -p 1 \
  -d "Files to modify:
      1. apps/static/js/drag-drop.js:
         - Remove handleTagKeyboard method (lines 1220-1280)
         - Remove handleGlobalKeyboard method
         - Remove keyboard event listeners (lines 1198, 1213)
         - Keep drag-drop logic, remove keyboard navigation
      2. Configure accX to handle keyboard:
         - Add ax-keyboard='navigate' to tag containers
         - Add ax-keyboard-nav='arrow' for arrow key navigation
         - Add ax-keyboard-select='space' for selection
      3. apps/static/js/app.js:
         - Review keyboard handlers (may need to keep app-specific)
      4. Test keyboard navigation still works via accX
      5. Verify all shortcuts documented in config" \
  --deps parent-child:$PHASE3_ID,blocks:$TASK3_1 \
  --json | jq -r '.id')

# Task 3.3: Migrate focus management
TASK3_3=$(bd create "Replace custom focus management with accX patterns" \
  -t task -p 1 \
  -d "Files to modify:
      1. apps/static/js/drag-drop.js:
         - Remove focus() calls (lines 1237, 1254)
         - Remove ensureFocusVisible method
         - Remove focus tracking variables
      2. Add accX focus attributes:
         - ax-focus='restore' for focus restoration
         - ax-focus-trap='modal' for modals
         - ax-focus-visible='always' for visibility
      3. apps/static/css/user.css:
         - Remove custom focus styles (lines 1138-1152)
         - accX provides WCAG-compliant focus indicators
      4. Test focus management:
         - Tab navigation works
         - Focus visible on keyboard nav
         - Focus restored after operations
      5. Verify with keyboard-only navigation" \
  --deps parent-child:$PHASE3_ID,blocks:$TASK3_2 \
  --json | jq -r '.id')

# Task 3.4: Update screen reader helpers
TASK3_4=$(bd create "Replace .sr-only with ax-visible attribute" \
  -t task -p 1 \
  -d "Files to modify:
      1. apps/static/css/user.css:
         - Remove .sr-only class definition (line 3385)
      2. apps/static/js/drag-drop.js:
         - Remove live region creation (lines 1204-1210)
         - Remove sr-only class usage
      3. Templates using .sr-only:
         - Replace class='sr-only' with ax-visible='screen-reader'
         - Search all templates: grep -r 'sr-only' apps/static/templates/
      4. Live regions:
         - Replace aria-live with ax-announce='polite'
         - Replace aria-atomic with ax-announce-atomic='true'
      5. Test with screen reader:
         - NVDA on Windows or VoiceOver on Mac
         - Verify announcements work
         - Check content is properly hidden/shown" \
  --deps parent-child:$PHASE3_ID,blocks:$TASK3_3 \
  --json | jq -r '.id')

# Task 3.5: Update templates with declarative patterns
TASK3_5=$(bd create "Apply ax- attributes to all templates" \
  -t task -p 1 \
  -d "Templates to update:
      1. apps/static/templates/base.html:
         - Add ax-enhance='application' to main container
         - Add ax-shortcuts='{"?":"help", "/":"search"}'
      2. apps/static/templates/user_home.html:
         - Add ax-enhance='workspace' to workspace area
         - Add ax-region='main' for main content
      3. apps/static/templates/drop_zone.html:
         - Add ax-drop-target='true' to zones
         - Add ax-drop-accept='[data-tag]' for accepted elements
      4. apps/admin/templates/pages/users.html:
         - Add ax-enhance='data-table' to tables
         - Add ax-sortable='true' to sortable columns
      5. Component templates:
         - Add appropriate ax- attributes
         - Follow accX pattern library
      6. Validate HTML remains valid
      7. Test server-side rendering unchanged" \
  --deps parent-child:$PHASE3_ID,blocks:$TASK3_4 \
  --json | jq -r '.id')
```

### Phase 4 Tasks: Validation and Optimization

```bash
# Task 4.1: Run BDD test suite
TASK4_1=$(bd create "Execute comprehensive BDD test suite" \
  -t task -p 1 \
  -d "1. Run accessibility regression tests:
         uv run pytest tests/features/accessibility-current.feature -v
      2. All tests must pass (100% GREEN)
      3. Create new accX-specific tests:
         - tests/features/accessibility-accx.feature
         - tests/step_definitions/test_accessibility_accx_steps.py
      4. Test scenarios:
         - accX attributes properly applied
         - Keyboard navigation via accX
         - Screen reader with ax-visible
         - Focus management automatic
         - Live announcements via ax-announce
      5. Run full test suite:
         uv run pytest tests -v --cov=apps --cov-report=html
      6. Coverage must remain >85%
      7. Document any test updates needed" \
  --deps parent-child:$PHASE4_ID \
  --json | jq -r '.id')

# Task 4.2: Performance benchmarking
TASK4_2=$(bd create "Benchmark accX performance vs baseline" \
  -t task -p 1 \
  -d "1. Run performance benchmarks:
         python tests/benchmarks/accessibility_performance.py
      2. Compare with baseline-performance.json:
         - accX initialization: <10ms required
         - First interaction: <16ms (60 FPS)
         - Memory usage: Should decrease
         - Event handler count: Should decrease
      3. Profile with Chrome DevTools:
         - Performance tab recording
         - Check for jank during interactions
         - Verify no render blocking
      4. Test with varying data sizes:
         - 100 tags: <5ms
         - 1000 tags: <10ms
         - 5000 tags: <20ms
      5. Output: accx-performance.json
      6. Create comparison report" \
  --deps parent-child:$PHASE4_ID,blocks:$TASK4_1 \
  --json | jq -r '.id')

# Task 4.3: Lighthouse accessibility audit
TASK4_3=$(bd create "Run Lighthouse audit for 100 accessibility score" \
  -t task -p 1 \
  -d "1. Run Lighthouse CLI:
         npx lighthouse http://localhost:8011 --only-categories=accessibility
      2. Target: 100 accessibility score
      3. Fix any issues found:
         - Color contrast
         - ARIA attributes
         - Focus management
         - Semantic HTML
      4. Run on multiple pages:
         - Home page
         - Workspace with tags
         - Admin pages
      5. Generate reports:
         - lighthouse-before-accx.html
         - lighthouse-after-accx.html
      6. Document improvements
      7. Verify no regressions" \
  --deps parent-child:$PHASE4_ID,blocks:$TASK4_2 \
  --json | jq -r '.id')

# Task 4.4: WCAG 2.1 AA compliance check
TASK4_4=$(bd create "Verify WCAG 2.1 AA compliance" \
  -t task -p 1 \
  -d "1. Run axe DevTools:
         - Install axe browser extension
         - Scan all pages
         - Fix any violations
      2. Manual testing checklist:
         - Keyboard navigation complete
         - Focus indicators visible
         - Color contrast 4.5:1 minimum
         - Text resizable to 200%
         - No keyboard traps
         - Skip links present
      3. Screen reader testing:
         - Test with NVDA/JAWS (Windows)
         - Test with VoiceOver (Mac)
         - Verify all content accessible
      4. Document compliance:
         - Create WCAG compliance matrix
         - Note any exceptions
         - Provide remediation timeline
      5. Generate VPAT if needed" \
  --deps parent-child:$PHASE4_ID,blocks:$TASK4_3 \
  --json | jq -r '.id')
```

### Phase 5 Tasks: Documentation and Rollout

```bash
# Task 5.1: Update developer documentation
TASK5_1=$(bd create "Update developer documentation for accX" \
  -t task -p 1 \
  -d "1. Update CLAUDE.md:
         - Add accX integration section
         - Document ax- attribute usage
         - Remove manual ARIA guidelines
         - Add accX pattern examples
      2. Create docs/guides/accessibility-with-accx.md:
         - Quick start guide
         - Common patterns
         - Custom enhancements
         - Troubleshooting
      3. Update README.md:
         - Note accX integration
         - Link to accessibility guide
      4. Create migration guide:
         - docs/guides/migrating-to-accx.md
         - Step-by-step migration
         - Before/after examples
         - Common pitfalls
      5. Update inline code comments
      6. Remove obsolete accessibility comments" \
  --deps parent-child:$PHASE5_ID \
  --json | jq -r '.id')

# Task 5.2: Implement feature flags
TASK5_2=$(bd create "Create feature flags for safe rollout" \
  -t task -p 1 \
  -d "1. Add feature flag system:
         - apps/shared/config/feature_flags.py
         - ACCX_ENABLED = env.bool('ACCX_ENABLED', False)
      2. Conditional loading in templates:
         {% if features.ACCX_ENABLED %}
           <script src='genx.software/bootloader.min.js'></script>
         {% else %}
           <!-- Keep existing implementation -->
         {% endif %}
      3. Gradual rollout plan:
         - 10% of users initially
         - Monitor for issues
         - Increase to 50%
         - Full rollout after validation
      4. Add kill switch:
         - Emergency disable capability
         - Fallback to manual implementation
      5. Test flag toggles
      6. Document flag usage" \
  --deps parent-child:$PHASE5_ID,blocks:$TASK5_1 \
  --json | jq -r '.id')

# Task 5.3: Production deployment preparation
TASK5_3=$(bd create "Prepare production deployment" \
  -t task -p 1 \
  -d "1. Update deployment configs:
         - Add CSP for genx.software CDN
         - Update nginx/apache configs
         - Add SRI hashes for security
      2. Monitoring setup:
         - Track accX initialization time
         - Monitor accessibility errors
         - Set up alerting
      3. Rollback plan:
         - Document rollback procedure
         - Test rollback locally
         - Prepare rollback scripts
      4. Performance monitoring:
         - Set up Real User Monitoring
         - Track Core Web Vitals
         - Monitor accX metrics
      5. Create deployment checklist
      6. Schedule deployment window" \
  --deps parent-child:$PHASE5_ID,blocks:$TASK5_2 \
  --json | jq -r '.id')

# Task 5.4: Production deployment and monitoring
TASK5_4=$(bd create "Deploy to production with monitoring" \
  -t task -p 1 \
  -d "1. Deploy with feature flag at 10%:
         - Enable for test group
         - Monitor for 24 hours
         - Check error rates
      2. Increase to 50%:
         - Expand user group
         - Monitor for 48 hours
         - Gather user feedback
      3. Full rollout:
         - Enable for all users
         - Monitor closely for 1 week
         - Track metrics
      4. Post-deployment:
         - Remove old accessibility code
         - Clean up unused CSS
         - Update documentation
      5. Success metrics:
         - 0 accessibility regressions
         - <10ms initialization
         - 100 Lighthouse score
         - Positive user feedback
      6. Close epic when stable" \
  --deps parent-child:$PHASE5_ID,blocks:$TASK5_3 \
  --json | jq -r '.id')
```

---

## Risk Management

### Identified Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| accX breaks drag-drop functionality | High | Low | Comprehensive BDD tests before migration |
| Performance regression | Medium | Low | Benchmark before/after, progressive disclosure |
| Browser compatibility issues | Medium | Low | Test on all major browsers, polyfills if needed |
| Screen reader compatibility | High | Low | Test with NVDA, JAWS, VoiceOver |
| CDN availability | Low | Low | Local fallback copy, SRI hashes |
| Patent compliance violation | High | Very Low | accX doesn't affect set theory operations |

### Contingency Tasks

```bash
# Create contingency tasks for high-impact risks
bd create "Contingency: Local accX fallback if CDN fails" \
  -t task -p 3 \
  -d "Host accX locally as backup, implement CDN failure detection" \
  --deps related:$PHASE2_ID --json

bd create "Contingency: Manual ARIA restoration script" \
  -t task -p 3 \
  -d "Script to quickly restore manual implementation if needed" \
  --deps related:$PHASE3_ID --json

bd create "Contingency: Browser polyfills for older browsers" \
  -t task -p 3 \
  -d "Add polyfills for MutationObserver, WeakMap if needed" \
  --deps related:$PHASE2_ID --json
```

---

## Success Criteria

### Technical Metrics
- ✅ 100% BDD tests passing
- ✅ <10ms accX initialization time
- ✅ 100 Lighthouse accessibility score
- ✅ WCAG 2.1 AA compliance verified
- ✅ <16ms interaction response time (60 FPS)
- ✅ Zero console errors or warnings
- ✅ Memory usage reduced by >20%

### Code Quality Metrics
- ✅ 300+ lines of accessibility code removed
- ✅ Zero manual ARIA attributes remaining
- ✅ No custom keyboard handlers for navigation
- ✅ All accessibility via declarative attributes
- ✅ >85% test coverage maintained

### User Experience Metrics
- ✅ Screen reader users report improvements
- ✅ Keyboard navigation more intuitive
- ✅ Focus management more predictable
- ✅ No visual regressions
- ✅ Performance improvements noticeable

---

## Execution Timeline

### Day 1: Foundation
- Morning: Codebase audit (Tasks 1.1, 1.2)
- Afternoon: BDD test creation (Task 1.3)
- End of day: Performance baseline (Task 1.4)

### Day 2: Integration
- Morning: Bootloader setup (Task 2.1)
- Midday: accX configuration (Task 2.2)
- Afternoon: Custom patterns (Task 2.3)
- End of day: Progressive disclosure (Task 2.4)

### Day 3-4: Migration
- Day 3 AM: ARIA replacement (Task 3.1)
- Day 3 PM: Keyboard handler removal (Task 3.2)
- Day 4 AM: Focus management (Task 3.3)
- Day 4 PM: Screen reader helpers and templates (Tasks 3.4, 3.5)

### Day 5: Validation
- Morning: BDD tests (Task 4.1)
- Midday: Performance tests (Task 4.2)
- Afternoon: Lighthouse audit (Task 4.3)
- End of day: WCAG compliance (Task 4.4)

### Day 6: Rollout
- Morning: Documentation (Task 5.1)
- Midday: Feature flags (Task 5.2)
- Afternoon: Deployment prep (Task 5.3)
- End of day: Production deploy (Task 5.4)

---

## Post-Implementation Review

### Lessons Learned Documentation
- Document challenges encountered
- Record performance improvements
- Note user feedback
- Capture best practices

### Knowledge Transfer
- Team training on accX
- Update onboarding docs
- Create video tutorials
- Share with genX community

### Future Enhancements
- Consider other genX modules (dragX alternative investigation)
- Extend accX patterns for new features
- Contribute patterns back to genX

---

## Appendix A: File Modification Summary

### Files to Modify
1. **apps/static/js/drag-drop.js** - Remove 200+ lines of accessibility code
2. **apps/static/css/user.css** - Remove focus styles and .sr-only
3. **apps/static/templates/base.html** - Add ax- attributes
4. **apps/static/templates/user_home.html** - Update with ax- patterns
5. **apps/static/templates/drop_zone.html** - Replace ARIA with ax-enhance
6. **apps/admin/templates/pages/users.html** - Add table accessibility

### Files to Create
1. **apps/static/js/accx-config.js** - accX configuration
2. **apps/static/js/accx-multicardz-pattern.js** - Custom patterns
3. **tests/features/accessibility-accx.feature** - New BDD tests
4. **tests/step_definitions/test_accessibility_accx_steps.py** - Test implementation
5. **docs/guides/accessibility-with-accx.md** - Developer guide
6. **docs/guides/migrating-to-accx.md** - Migration guide

### Files to Delete (After Validation)
1. Manual accessibility helper functions
2. Custom keyboard navigation code
3. Focus management utilities
4. ARIA attribute management code

---

## Appendix B: bd Command Reference

### Quick Start
```bash
# View ready work
bd ready --json

# Start a task
bd update <task-id> --status in_progress --json

# Complete a task
bd close <task-id> --reason "Implemented" --json

# Create discovered issue
bd create "Bug found" -t bug -p 0 --deps discovered-from:<task-id> --json

# View dependency tree
bd dep tree <epic-id>

# Check progress
bd show <epic-id> --json | jq '.subtasks | group_by(.status)'
```

### Monitoring Progress
```bash
# In-progress work
bd list --status in_progress --json

# Completed today
bd list --status closed --json | jq '.[] | select(.closed_at > (now - 86400))'

# Blockers
bd list --status blocked --json

# High priority items
bd list --priority 0 --json
bd list --priority 1 --json
```

---

## Document Control

- **Created**: 2025-11-13
- **Version**: 1.0
- **Author**: System Architect
- **Review Status**: Ready for Execution
- **Epic ID**: To be assigned upon execution
- **Estimated Duration**: 6 days
- **Estimated Effort**: 48 engineering hours