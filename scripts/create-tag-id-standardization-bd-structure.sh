#!/bin/bash

# Tag ID Standardization Implementation - bd Issue Structure Creation Script
# This script creates the complete bd issue structure for implementing
# the Tag ID Standardization Architecture (Document 040-2025-11-09-v1)
#
# Usage: ./create-tag-id-standardization-bd-structure.sh
#
# The script will create:
# - 1 Epic for the overall implementation
# - 5 Phases as Features with dependencies
# - Multiple tasks per phase following TDD/BDD principles
# - All proper dependency relationships (parent-child, blocks, etc.)

set -e  # Exit on error

echo "Creating bd issue structure for Tag ID Standardization Implementation..."
echo "============================================================"

# Create the main EPIC
echo "Creating Epic..."
EPIC_ID=$(bd create "Implement Tag ID Standardization Architecture" \
  -t epic \
  -p 1 \
  -d "Complete implementation of Tag ID Standardization per Architecture Document 040-2025-11-09-v1. Success criteria: 1) All tag elements have data-tag-id attributes, 2) removeTagFromCard() works reliably without DOM traversal, 3) No performance regression >10%, 4) Full backward compatibility maintained" \
  --json | jq -r '.id')

echo "✅ Epic created: $EPIC_ID"

# Phase 1: Backend Data Model Enhancement
echo ""
echo "Creating Phase 1: Backend Data Model Enhancement..."
PHASE1_ID=$(bd create "Phase 1: Backend Data Model Enhancement" \
  -t feature \
  -p 1 \
  -d "Implement TagInfo model and tag enhancement functions with full set theory compliance. Includes creating the immutable TagInfo model, tag repository integration, and error handling patterns." \
  --deps parent-child:$EPIC_ID \
  --json | jq -r '.id')

echo "✅ Phase 1 created: $PHASE1_ID"

# Phase 1 Tasks
echo "Creating Phase 1 tasks..."

# Task 1.1: BDD tests for TagInfo model
TASK1_1=$(bd create "Write BDD tests for TagInfo model and validation" \
  -t task \
  -p 1 \
  -d "Create comprehensive BDD scenarios for TagInfo model including: immutability verification, validation rules, serialization/deserialization, and error cases" \
  --deps parent-child:$PHASE1_ID \
  --json | jq -r '.id')

# Task 1.2: Implement TagInfo model
TASK1_2=$(bd create "Implement TagInfo Pydantic model with frozen=True" \
  -t task \
  -p 1 \
  -d "Create the immutable TagInfo model in apps/shared/models/ with id and name fields, proper type hints, and Pydantic validation" \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_1 \
  --json | jq -r '.id')

# Task 1.3: BDD tests for tag enhancement function
TASK1_3=$(bd create "Write BDD tests for enhance_card_with_tag_objects function" \
  -t task \
  -p 1 \
  -d "Create BDD scenarios testing: successful tag enhancement, missing tags handling, immutability preservation, and performance within O(k) complexity" \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_2 \
  --json | jq -r '.id')

# Task 1.4: Implement tag enhancement function
TASK1_4=$(bd create "Implement enhance_card_with_tag_objects pure function" \
  -t task \
  -p 1 \
  -d "Create the pure functional tag enhancement in apps/shared/services/ using frozenset operations, maintaining O(k) complexity where k=|card.tags|" \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_3 \
  --json | jq -r '.id')

# Task 1.5: BDD tests for error handling
TASK1_5=$(bd create "Write BDD tests for safe_tag_lookup with error handling" \
  -t task \
  -p 1 \
  -d "Create scenarios for: successful lookups, missing tags, repository errors, and monadic Result pattern verification" \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_4 \
  --json | jq -r '.id')

# Task 1.6: Implement safe tag lookup
TASK1_6=$(bd create "Implement safe_tag_lookup with Result monad pattern" \
  -t task \
  -p 1 \
  -d "Create monadic error handling for tag lookups using Result pattern, ensuring no exceptions leak to callers" \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_5 \
  --json | jq -r '.id')

echo "✅ Phase 1 tasks created"

# Phase 2: Template Layer Updates
echo ""
echo "Creating Phase 2: Template Layer Updates..."
PHASE2_ID=$(bd create "Phase 2: Template Layer Updates" \
  -t feature \
  -p 1 \
  -d "Update all Jinja2 templates to render tag objects with data-tag-id attributes. Includes tag cloud, card displays, and dimensional grids while maintaining backward compatibility." \
  --deps parent-child:$EPIC_ID,blocks:$PHASE1_ID \
  --json | jq -r '.id')

echo "✅ Phase 2 created: $PHASE2_ID"

# Phase 2 Tasks
echo "Creating Phase 2 tasks..."

# Task 2.1: BDD tests for tag cloud template
TASK2_1=$(bd create "Write BDD tests for tag cloud template with IDs" \
  -t task \
  -p 1 \
  -d "Create scenarios verifying tag cloud renders both data-tag-id and data-tag attributes correctly" \
  --deps parent-child:$PHASE2_ID \
  --json | jq -r '.id')

# Task 2.2: Update tag cloud template
TASK2_2=$(bd create "Update tag cloud template to include data-tag-id" \
  -t task \
  -p 1 \
  -d "Modify apps/static/templates/components/tag-cloud.html to render tag.id in data-tag-id attribute" \
  --deps parent-child:$PHASE2_ID,blocks:$TASK2_1 \
  --json | jq -r '.id')

# Task 2.3: BDD tests for card tag display
TASK2_3=$(bd create "Write BDD tests for card tag rendering with IDs" \
  -t task \
  -p 1 \
  -d "Create scenarios for card templates verifying tag IDs are present in rendered HTML" \
  --deps parent-child:$PHASE2_ID,blocks:$TASK2_2 \
  --json | jq -r '.id')

# Task 2.4: Update card display templates
TASK2_4=$(bd create "Update card templates to render tag objects" \
  -t task \
  -p 1 \
  -d "Modify apps/static/templates/components/card.html and related templates to use tag.id and tag.name" \
  --deps parent-child:$PHASE2_ID,blocks:$TASK2_3 \
  --json | jq -r '.id')

# Task 2.5: Create reusable tag rendering partial
TASK2_5=$(bd create "Create tag-render.html partial template for consistency" \
  -t task \
  -p 1 \
  -d "Create a reusable Jinja2 partial for consistent tag rendering across all templates" \
  --deps parent-child:$PHASE2_ID,blocks:$TASK2_4 \
  --json | jq -r '.id')

echo "✅ Phase 2 tasks created"

# Phase 3: API Endpoint Integration
echo ""
echo "Creating Phase 3: API Endpoint Integration..."
PHASE3_ID=$(bd create "Phase 3: API Endpoint Integration" \
  -t feature \
  -p 1 \
  -d "Integrate tag enhancement into all card rendering API endpoints. Update /api/v2/render/cards and related endpoints to use enhanced card data with tag objects." \
  --deps parent-child:$EPIC_ID,blocks:$PHASE2_ID \
  --json | jq -r '.id')

echo "✅ Phase 3 created: $PHASE3_ID"

# Phase 3 Tasks
echo "Creating Phase 3 tasks..."

# Task 3.1: BDD tests for API endpoints
TASK3_1=$(bd create "Write BDD tests for /api/v2/render/cards with tag IDs" \
  -t task \
  -p 1 \
  -d "Create API test scenarios verifying endpoints return HTML with data-tag-id attributes" \
  --deps parent-child:$PHASE3_ID \
  --json | jq -r '.id')

# Task 3.2: Update render_cards endpoint
TASK3_2=$(bd create "Integrate tag enhancement into render_cards endpoint" \
  -t task \
  -p 1 \
  -d "Modify apps/user/routes/cards.py to use enhance_card_with_tag_objects before rendering" \
  --deps parent-child:$PHASE3_ID,blocks:$TASK3_1 \
  --json | jq -r '.id')

# Task 3.3: Performance testing
TASK3_3=$(bd create "Write performance benchmarks for tag enhancement overhead" \
  -t task \
  -p 1 \
  -d "Create benchmarks measuring overhead of tag enhancement for 100, 1000, and 10000 cards" \
  --deps parent-child:$PHASE3_ID,blocks:$TASK3_2 \
  --json | jq -r '.id')

# Task 3.4: Optimize tag repository lookups
TASK3_4=$(bd create "Implement batched tag lookups to prevent N+1 queries" \
  -t task \
  -p 1 \
  -d "Optimize tag repository to batch fetch all workspace tags once, use in-memory lookup" \
  --deps parent-child:$PHASE3_ID,blocks:$TASK3_3 \
  --json | jq -r '.id')

echo "✅ Phase 3 tasks created"

# Phase 4: JavaScript Updates
echo ""
echo "Creating Phase 4: JavaScript Updates..."
PHASE4_ID=$(bd create "Phase 4: JavaScript Updates for Tag ID Usage" \
  -t feature \
  -p 1 \
  -d "Update JavaScript drag-drop system to use data-tag-id attributes. Simplify removeTagFromCard and related functions to use direct ID lookups instead of DOM traversal." \
  --deps parent-child:$EPIC_ID,blocks:$PHASE3_ID \
  --json | jq -r '.id')

echo "✅ Phase 4 created: $PHASE4_ID"

# Phase 4 Tasks
echo "Creating Phase 4 tasks..."

# Task 4.1: BDD tests for removeTagFromCard
TASK4_1=$(bd create "Write BDD tests for removeTagFromCard with tag IDs" \
  -t task \
  -p 1 \
  -d "Create browser test scenarios for tag removal using tag IDs, verify no DOM traversal needed" \
  --deps parent-child:$PHASE4_ID \
  --json | jq -r '.id')

# Task 4.2: Update removeTagFromCard function
TASK4_2=$(bd create "Refactor removeTagFromCard to use data-tag-id directly" \
  -t task \
  -p 1 \
  -d "Simplify apps/static/js/drag-drop.js removeTagFromCard to use querySelector with data-tag-id" \
  --deps parent-child:$PHASE4_ID,blocks:$TASK4_1 \
  --json | jq -r '.id')

# Task 4.3: BDD tests for tag operations
TASK4_3=$(bd create "Write BDD tests for all tag manipulation functions" \
  -t task \
  -p 1 \
  -d "Create comprehensive tests for addTagToCard, removeTagFromCard, and tag filtering with IDs" \
  --deps parent-child:$PHASE4_ID,blocks:$TASK4_2 \
  --json | jq -r '.id')

# Task 4.4: Update all tag operations
TASK4_4=$(bd create "Update remaining JavaScript to prefer data-tag-id" \
  -t task \
  -p 1 \
  -d "Refactor all tag-related JavaScript functions to use data-tag-id as primary identifier" \
  --deps parent-child:$PHASE4_ID,blocks:$TASK4_3 \
  --json | jq -r '.id')

# Task 4.5: Add backward compatibility layer
TASK4_5=$(bd create "Implement fallback to data-tag for backward compatibility" \
  -t task \
  -p 1 \
  -d "Add temporary fallback logic to use data-tag if data-tag-id not present, with console warnings" \
  --deps parent-child:$PHASE4_ID,blocks:$TASK4_4 \
  --json | jq -r '.id')

echo "✅ Phase 4 tasks created"

# Phase 5: Testing and Validation
echo ""
echo "Creating Phase 5: Testing and Validation..."
PHASE5_ID=$(bd create "Phase 5: Comprehensive Testing and Validation" \
  -t feature \
  -p 1 \
  -d "Complete end-to-end testing, performance validation, and rollback procedures. Verify all success criteria are met before deployment." \
  --deps parent-child:$EPIC_ID,blocks:$PHASE4_ID \
  --json | jq -r '.id')

echo "✅ Phase 5 created: $PHASE5_ID"

# Phase 5 Tasks
echo "Creating Phase 5 tasks..."

# Task 5.1: Integration test suite
TASK5_1=$(bd create "Write comprehensive integration test suite" \
  -t task \
  -p 1 \
  -d "Create integration tests covering full pipeline from database to rendered HTML with tag IDs" \
  --deps parent-child:$PHASE5_ID \
  --json | jq -r '.id')

# Task 5.2: End-to-end browser tests
TASK5_2=$(bd create "Create Playwright tests for tag operations with IDs" \
  -t task \
  -p 1 \
  -d "Write E2E tests verifying drag-drop, tag removal, and filtering work with new ID system" \
  --deps parent-child:$PHASE5_ID,blocks:$TASK5_1 \
  --json | jq -r '.id')

# Task 5.3: Performance validation
TASK5_3=$(bd create "Validate performance targets are met" \
  -t task \
  -p 1 \
  -d "Run benchmarks confirming: removeTagFromCard <5ms, rendering overhead <10%, no memory leaks" \
  --deps parent-child:$PHASE5_ID,blocks:$TASK5_2 \
  --json | jq -r '.id')

# Task 5.4: Rollback procedure documentation
TASK5_4=$(bd create "Document and test rollback procedures" \
  -t task \
  -p 1 \
  -d "Create rollback plan and test reverting to tag-name-only system if issues discovered" \
  --deps parent-child:$PHASE5_ID,blocks:$TASK5_3 \
  --json | jq -r '.id')

# Task 5.5: Migration guide
TASK5_5=$(bd create "Create migration guide for dependent systems" \
  -t task \
  -p 1 \
  -d "Document changes needed for any external systems or plugins using tag data" \
  --deps parent-child:$PHASE5_ID,blocks:$TASK5_4 \
  --json | jq -r '.id')

echo "✅ Phase 5 tasks created"

# Create Review Gates
echo ""
echo "Creating Review Gates..."

# Architecture review after Phase 1
REVIEW1=$(bd create "Architecture Review: Backend Implementation" \
  -t task \
  -p 0 \
  -d "Review Phase 1 implementation for patent compliance, set theory correctness, and performance" \
  --deps blocks:$PHASE2_ID,related:$PHASE1_ID \
  --json | jq -r '.id')

# UI/UX review after Phase 2
REVIEW2=$(bd create "UI/UX Review: Template Changes" \
  -t task \
  -p 0 \
  -d "Review template changes to ensure no visual regressions or accessibility issues" \
  --deps blocks:$PHASE3_ID,related:$PHASE2_ID \
  --json | jq -r '.id')

# Performance review after Phase 3
REVIEW3=$(bd create "Performance Review: API Integration" \
  -t task \
  -p 0 \
  -d "Review API performance metrics, ensure <10% overhead target is met" \
  --deps blocks:$PHASE4_ID,related:$PHASE3_ID \
  --json | jq -r '.id')

# Security review before deployment
REVIEW4=$(bd create "Security Review: Final Implementation" \
  -t task \
  -p 0 \
  -d "Security audit of tag ID implementation, check for injection vulnerabilities" \
  --deps blocks:$PHASE5_ID,related:$PHASE4_ID \
  --json | jq -r '.id')

echo "✅ Review gates created"

# Create monitoring tasks
echo ""
echo "Creating Monitoring Tasks..."

MONITOR1=$(bd create "Setup performance monitoring for tag operations" \
  -t task \
  -p 2 \
  -d "Add metrics collection for tag enhancement overhead and operation latency" \
  --deps parent-child:$EPIC_ID,related:$PHASE5_ID \
  --json | jq -r '.id')

MONITOR2=$(bd create "Add error tracking for tag lookup failures" \
  -t task \
  -p 2 \
  -d "Implement error logging for missing tags and repository failures" \
  --deps parent-child:$EPIC_ID,related:$PHASE5_ID \
  --json | jq -r '.id')

echo "✅ Monitoring tasks created"

# Display summary
echo ""
echo "============================================================"
echo "✅ BD ISSUE STRUCTURE CREATION COMPLETE!"
echo "============================================================"
echo ""
echo "Created:"
echo "  - 1 Epic (ID: $EPIC_ID)"
echo "  - 5 Feature phases with dependencies"
echo "  - 25 Implementation tasks following TDD/BDD"
echo "  - 4 Review gates at critical points"
echo "  - 2 Monitoring tasks"
echo ""
echo "Next Steps:"
echo "1. View the dependency tree:"
echo "   bd dep tree $EPIC_ID"
echo ""
echo "2. Check what's ready to start:"
echo "   bd ready --json"
echo ""
echo "3. View all issues in the epic:"
echo "   bd list --deps parent-child:$EPIC_ID --json"
echo ""
echo "4. Start working on the first task:"
echo "   TASK_ID=\$(bd ready --json | jq -r '.[0].id')"
echo "   bd update \$TASK_ID --status in_progress --json"
echo ""
echo "Remember: Follow TDD/BDD principles - tests first, then implementation!"
echo "============================================================"

# Optional: Save epic ID for reference
echo $EPIC_ID > .tag-id-standardization-epic-id
echo "Epic ID saved to .tag-id-standardization-epic-id for reference"