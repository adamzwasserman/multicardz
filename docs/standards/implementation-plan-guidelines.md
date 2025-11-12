# Implementation Plan Guidelines
**Document Version**: 4.0
**Date**: 2025-11-10
**Status**: MANDATORY FOR ALL IMPLEMENTATION TASKS
**Revision**: Enhanced with explicit BDD technical requirements based on failure analysis

---

## IMPLEMENTATION STATUS: IMPLEMENTED

**LAST VERIFIED**: 2025-01-13
**IMPLEMENTATION EVIDENCE**: Integrated with bd (beads) task tracking system

---

## Overview

This document defines comprehensive guidelines for creating and executing implementation plans using the `bd` (beads) task tracking system as the single source of truth. The workflow eliminates manual timestamp tracking, leverages automatic issue management, and generates documentation from actual execution data.

## 🔴 CRITICAL: The bd-First Implementation Workflow

**FUNDAMENTAL PRINCIPLE**: `bd` (beads) is the source of truth for all implementation work. The markdown document is a historical record generated AFTER completion, not a tracking tool.

## Core Workflow Overview

### Phase 1: Planning (BEFORE Implementation)

Create the complete issue structure in bd with proper relationships:

```bash
# Create the epic for the overall implementation
bd create "Implement [Feature Name]" -t epic -p 1 -d "Implementation of [description]" --json

# Create phases as features with parent relationship
bd create "Phase 1: Foundation" -t feature -p 1 --deps parent-child:<epic-id> --json
bd create "Phase 2: Business Logic" -t feature -p 1 --deps parent-child:<epic-id>,blocks:<phase1-id> --json

# Create tasks for each step with dependencies
bd create "Create BDD feature files" -t task -p 1 --deps parent-child:<phase1-id> --json
bd create "Implement domain models" -t task -p 1 --deps parent-child:<phase1-id>,blocks:<bdd-task-id> --json
```

### Phase 2: Execution (DURING Implementation)

Work through issues using bd's ready queue:

```bash
# Find next available work
bd ready --json

# Claim your task
bd update <task-id> --status in_progress --json

# Work on the task following TDD/BDD principles
# ... do the actual work ...

# Complete the task
bd close <task-id> --reason "Implemented with tests" --json

# If you discover issues during work
bd create "Found bug in X" -t bug -p 0 --deps discovered-from:<task-id> --json
```

### Phase 3: Documentation (AFTER Implementation)

Generate the final markdown document from bd data:

```bash
# Extract timing and completion data
bd show <epic-id> --json > /tmp/epic-data.json
bd dep tree <epic-id> > /tmp/dependency-tree.txt

# Generate markdown document with actual metrics
# The document becomes a permanent record of what was accomplished
```

## Task Specification Quality Standards

### Critical Requirements for Task Descriptions

**MANDATORY**: All BDD/TDD tasks must include explicit technical specifications to ensure correct implementation on first attempt.

#### Insufficient Task Description (❌ WILL FAIL)
```
Title: Create BDD tests for DATAOS cache violations
Description: Write Gherkin scenarios in tests/features/dataos-compliance.feature
testing that deriveStateFromDOM() always returns fresh data.
```

#### Sufficient Task Description (✅ WILL SUCCEED)
```
Title: Create BDD tests for DATAOS cache violations
Description:
1. Create Gherkin feature file at: tests/features/dataos-compliance.feature
2. Create step definitions at: tests/step_definitions/test_dataos_compliance_steps.py
3. Implement using pytest-bdd framework with @given/@when/@then decorators
4. Include scenarios() function to load feature file
5. Create Playwright fixtures for browser/page management
6. Reference pattern: tests/step_definitions/test_set_operations_steps.py
7. Validation: uv run pytest tests/features/dataos-compliance.feature -v
8. Initial state: Tests must fail with assertion errors (not StepDefinitionNotFound)
```

### BDD Task Creation Template

```markdown
## Task: Create BDD tests for [feature]

### Technical Requirements:
- Framework: pytest-bdd (NOT standalone pytest)
- Feature file: tests/features/[name].feature
- Step definitions: tests/step_definitions/test_[name]_steps.py
- Pattern reference: tests/step_definitions/test_set_operations_steps.py

### Implementation Checklist:
- [ ] Create Gherkin feature file with scenarios
- [ ] Create step definitions file with scenarios() import
- [ ] Implement @given steps for setup
- [ ] Implement @when steps for actions
- [ ] Implement @then steps for assertions
- [ ] Create pytest fixtures for test context
- [ ] Load scenarios using scenarios('/path/to/feature.feature')
- [ ] Do NOT create standalone test classes
- [ ] Do NOT create tests outside step_definitions/

### Acceptance Criteria:
- [ ] Feature file exists at specified location
- [ ] Step definitions file exists with all steps implemented
- [ ] Tests executable via: uv run pytest tests/features/[name].feature -v
- [ ] Initial run shows assertion failures (RED phase, not missing steps)
- [ ] No StepDefinitionNotFound errors
- [ ] No standalone test files created
```

## The 8-Step TDD/BDD Process (Tracked in bd)

Each task in bd follows this mandatory process with EXPLICIT technical requirements:

### Step 1: Create BDD Task with Full Specifications

```bash
bd create "Write BDD tests for [feature]" -t task -p 1 \
  -d "1. Create feature file: tests/features/[name].feature
      2. Create step definitions: tests/step_definitions/test_[name]_steps.py
      3. Use pytest-bdd with @given/@when/@then decorators
      4. Include scenarios() to load feature file
      5. Reference: tests/step_definitions/test_set_operations_steps.py
      6. Validate: uv run pytest tests/features/[name].feature -v" \
  --deps parent-child:<phase-id> --json

bd update <task-id> --status in_progress --json
```

### Step 2: Create BDD Feature File AND Step Definitions

**CRITICAL**: Both files MUST be created together for executable tests.

```gherkin
# tests/features/[feature_name].feature
Feature: [Feature Name]
  As a [user/system]
  I want [functionality]
  So that [business value]

  Scenario: [Happy path]
    Given [initial context]
    When [action taken]
    Then [expected outcome]
```

```python
# tests/step_definitions/test_[feature_name]_steps.py
from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from typing import Dict, Any

# MANDATORY: Load scenarios from feature file
scenarios("/Users/adam/dev/multicardz/tests/features/[feature_name].feature")

@pytest.fixture
def test_context() -> Dict[str, Any]:
    """Fixture to share state between steps."""
    return {}

@given("initial context")
def setup_initial_context(test_context: Dict[str, Any]) -> None:
    """Set up the initial test context."""
    test_context["setup"] = True

@when("action taken")
def perform_action(test_context: Dict[str, Any]) -> None:
    """Perform the action being tested."""
    # Implementation here
    test_context["action_performed"] = True

@then("expected outcome")
def verify_outcome(test_context: Dict[str, Any]) -> None:
    """Verify the expected outcome."""
    assert test_context.get("action_performed") is True
```

### Step 3: Create Test Fixtures Task with Explicit Requirements

```bash
bd create "Create test fixtures for [feature]" -t task -p 1 \
  -d "Create pytest fixtures in step_definitions file:
      1. test_context fixture for state sharing
      2. Browser/page fixtures if using Playwright
      3. Database fixtures if needed
      4. Mock fixtures for external dependencies" \
  --deps blocks:<bdd-task-id> --json
```

### Step 4: Verify Red State with Proper Validation

```bash
# MUST show assertion failures, NOT StepDefinitionNotFound
uv run pytest tests/features/[feature_name].feature -v

# Expected output for properly implemented tests:
# FAILED tests/features/[feature_name].feature::test_scenario - AssertionError
# NOT: StepDefinitionNotFound: Step 'Given initial context' not found
```

### Step 5: Create Implementation Task

```bash
bd create "Implement [feature] functionality" -t task -p 1 --deps blocks:<fixtures-task-id> --json
bd update <task-id> --status in_progress --json
```

### Step 6: Achieve Green State

```bash
uv run pytest tests/features/[feature_name].feature -v
# Block until 100% tests pass - this is a quality gate
bd close <task-id> --reason "All tests passing" --json
```

### Step 7: Handle Discovered Issues

```bash
# If bugs found during implementation
bd create "Fix edge case in [feature]" -t bug -p 0 --deps discovered-from:<task-id> --json
```

### Step 8: Complete Parent Task

```bash
# When all subtasks complete
bd close <parent-task-id> --reason "Feature complete with tests" --json
```

## BDD Test Implementation Patterns

### Pattern 1: Playwright BDD Tests

**CRITICAL**: Playwright tests MUST use pytest-bdd step definitions, NOT standalone test classes.

#### ❌ INCORRECT: Standalone Playwright Test
```python
# tests/playwright/test_drag_drop.py - WRONG APPROACH
class TestDragDrop:
    def test_drag_operation(self, page):
        page.goto("http://localhost:8011/")
        # Direct test implementation
```

#### ✅ CORRECT: BDD Step Definitions with Playwright
```python
# tests/step_definitions/test_drag_drop_steps.py - CORRECT APPROACH
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page
import pytest

scenarios("/Users/adam/dev/multicardz/tests/features/drag_drop.feature")

@pytest.fixture
def drag_drop_page(page: Page) -> Page:
    """Initialize drag-drop system for testing."""
    page.goto("http://localhost:8011/")
    page.wait_for_selector('[data-zone-type]')
    return page

@given("the drag-drop system is initialized")
def initialize_system(drag_drop_page: Page) -> None:
    """Ensure system is ready."""
    assert drag_drop_page.evaluate("typeof window.dragDropSystem") == "object"

@when(parsers.parse("I drag tag '{tag_id}' to zone '{zone_type}'"))
def drag_tag_to_zone(drag_drop_page: Page, tag_id: str, zone_type: str) -> None:
    """Perform drag operation."""
    tag = drag_drop_page.locator(f"[data-tag-id='{tag_id}']")
    zone = drag_drop_page.locator(f"[data-zone-type='{zone_type}']")
    tag.drag_to(zone)

@then(parsers.parse("the tag should be in zone '{zone_type}'"))
def verify_tag_location(drag_drop_page: Page, zone_type: str) -> None:
    """Verify tag moved to correct zone."""
    # Verification logic here
```

### Pattern 2: Unit Test BDD Implementation

```python
# tests/step_definitions/test_set_operations_steps.py
from pytest_bdd import scenarios, given, when, then, parsers
from apps.shared.services.set_operations import filter_cards_intersection_first

scenarios("/Users/adam/dev/multicardz/tests/features/set_operations.feature")

@given(parsers.parse("a set of cards with tags {tags}"))
def create_card_set(test_context, tags):
    """Create test cards with specified tags."""
    test_context["cards"] = create_test_cards(tags)

@when(parsers.parse("I filter with intersection tags {int_tags} and union tags {union_tags}"))
def apply_filters(test_context, int_tags, union_tags):
    """Apply set theory filters."""
    result = filter_cards_intersection_first(
        test_context["cards"],
        frozenset(int_tags.split(",")),
        frozenset(union_tags.split(","))
    )
    test_context["result"] = result

@then(parsers.parse("the result should contain {expected_count:d} cards"))
def verify_result_count(test_context, expected_count):
    """Verify filtering results."""
    assert len(test_context["result"]) == expected_count
```

### Pattern 3: Performance BDD Tests

```python
# tests/step_definitions/test_performance_steps.py
import time
from pytest_bdd import scenarios, given, when, then, parsers

scenarios("/Users/adam/dev/multicardz/tests/features/performance.feature")

@given(parsers.parse("{count:d} cards in the system"))
def create_large_dataset(test_context, count):
    """Create performance test dataset."""
    test_context["cards"] = generate_test_cards(count)
    test_context["start_time"] = None

@when("I perform a complex filter operation")
def perform_complex_operation(test_context):
    """Execute performance-critical operation."""
    start = time.perf_counter()
    # Perform operation
    test_context["duration"] = time.perf_counter() - start

@then(parsers.parse("the operation completes in less than {max_ms:d}ms"))
def verify_performance(test_context, max_ms):
    """Assert performance requirements."""
    assert test_context["duration"] * 1000 < max_ms
```

## bd Issue Structure for Implementation Plans

### Hierarchical Organization

```text
Epic: Full Implementation Plan
├── Feature: Phase 1 - Foundation
│   ├── Task: Create BDD tests for domain models
│   ├── Task: Implement domain entities
│   └── Task: Add domain validation rules
├── Feature: Phase 2 - Business Logic
│   ├── Task: Create BDD tests for services
│   ├── Task: Implement service layer
│   └── Task: Add business rules
└── Feature: Phase 3 - API Integration
    ├── Task: Create API endpoint tests
    ├── Task: Implement REST endpoints
    └── Task: Add authentication
```

### Dependency Types Usage

- **parent-child**: Hierarchical organization (epic → phase → task)
- **blocks**: Sequential dependencies (test → implementation)
- **discovered-from**: Issues found during work
- **related**: Soft relationships between related features

### Priority Guidelines

- **Priority 0**: Critical blockers, broken builds, security issues
- **Priority 1**: Core implementation tasks
- **Priority 2**: Nice-to-have enhancements
- **Priority 3**: Polish and optimization
- **Priority 4**: Future ideas discovered during work

## Creating the bd Structure (BEFORE Starting Work)

### Step 1: Analyze Architecture Document

Read the architecture document and identify:

- Major phases of work
- Dependencies between phases
- Individual tasks within each phase
- Risk factors and complexity

### Step 2: Create Epic

```bash
# Main implementation epic
bd create "Implement [Module Name] per Architecture Doc v2.0" \
  -t epic \
  -p 1 \
  -d "Complete implementation of [module] following architecture specifications. Success criteria: [list criteria]" \
  --json

# Capture the epic ID for relationships
EPIC_ID=$(bd list --type epic --json | jq -r '.[-1].id')
```

### Step 3: Create Phases as Features

```bash
# Phase 1: Foundation
PHASE1_ID=$(bd create "Phase 1: Foundation - Domain Layer" \
  -t feature \
  -p 1 \
  -d "Implement core domain models, entities, and value objects" \
  --deps parent-child:$EPIC_ID \
  --json | jq -r '.id')

# Phase 2: Business Logic (depends on Phase 1)
PHASE2_ID=$(bd create "Phase 2: Business Logic - Services" \
  -t feature \
  -p 1 \
  -d "Implement service layer with business rules" \
  --deps parent-child:$EPIC_ID,blocks:$PHASE1_ID \
  --json | jq -r '.id')

# Phase 3: API (depends on Phase 2)
PHASE3_ID=$(bd create "Phase 3: API Integration" \
  -t feature \
  -p 1 \
  -d "Implement REST endpoints and authentication" \
  --deps parent-child:$EPIC_ID,blocks:$PHASE2_ID \
  --json | jq -r '.id')
```

### Step 4: Create Tasks for Each Phase

```bash
# Phase 1 Tasks
TASK1_1=$(bd create "Write BDD tests for User entity" \
  -t task -p 1 \
  --deps parent-child:$PHASE1_ID \
  --json | jq -r '.id')

TASK1_2=$(bd create "Implement User entity with validation" \
  -t task -p 1 \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_1 \
  --json | jq -r '.id')

TASK1_3=$(bd create "Write BDD tests for Workspace entity" \
  -t task -p 1 \
  --deps parent-child:$PHASE1_ID,blocks:$TASK1_2 \
  --json | jq -r '.id')

# Continue for all tasks...
```

### Step 5: Verify Structure

```bash
# View the complete dependency tree
bd dep tree $EPIC_ID

# Check what's ready to start
bd ready --json

# View all issues in the epic
bd list --deps parent-child:$EPIC_ID --json
```

## Working Through Implementation (DURING Execution)

### Daily Workflow Pattern

```bash
# Start of day: Check ready work
bd ready --json

# Select highest priority task
TASK_ID=$(bd ready --json | jq -r '.[0].id')

# Claim the task
bd update $TASK_ID --status in_progress --json

# Do the work following TDD/BDD
# ... implement, test, verify ...

# If you find issues
bd create "Bug: Validation fails for edge case X" \
  -t bug -p 0 \
  --deps discovered-from:$TASK_ID \
  --json

# Complete the task
bd close $TASK_ID --reason "Implemented with 100% test coverage" --json

# Check next ready task
bd ready --json
```

### Handling Blockers

```bash
# If blocked by external dependency
bd update $TASK_ID --status blocked --json
bd create "Waiting for API documentation from team X" \
  -t task -p 0 \
  --deps blocks:$TASK_ID \
  --json

# When unblocked
bd close $BLOCKER_ID --reason "Documentation received" --json
# Task automatically becomes ready again
```

### Progress Monitoring

```bash
# Check epic progress
bd show $EPIC_ID --json | jq '.subtasks | group_by(.status)'

# View in-progress work
bd list --status in_progress --json

# Check completion percentage
bd dep tree $EPIC_ID | grep -c "CLOSED"
bd dep tree $EPIC_ID | wc -l
```

## Generating Documentation (AFTER Completion)

### Step 1: Extract bd Data

```bash
#!/bin/bash
# generate_implementation_report.sh

EPIC_ID=$1
OUTPUT_FILE="docs/implementation/$(date +%Y%m%d)-implementation-report.md"

# Get epic details
EPIC_DATA=$(bd show $EPIC_ID --json)
EPIC_TITLE=$(echo $EPIC_DATA | jq -r '.title')
EPIC_CREATED=$(echo $EPIC_DATA | jq -r '.created_at')
EPIC_CLOSED=$(echo $EPIC_DATA | jq -r '.closed_at')

# Generate markdown header
cat > $OUTPUT_FILE <<EOF
# Implementation Report: $EPIC_TITLE

## Overview
- **Epic ID**: $EPIC_ID
- **Started**: $EPIC_CREATED
- **Completed**: $EPIC_CLOSED
- **Total Duration**: $(calculate_duration $EPIC_CREATED $EPIC_CLOSED)

## Execution Summary
EOF

# Extract phase data
bd list --deps parent-child:$EPIC_ID --type feature --json | while read phase; do
  PHASE_ID=$(echo $phase | jq -r '.id')
  PHASE_TITLE=$(echo $phase | jq -r '.title')

  echo "### $PHASE_TITLE" >> $OUTPUT_FILE
  echo "" >> $OUTPUT_FILE

  # Extract task data for phase
  bd list --deps parent-child:$PHASE_ID --json | while read task; do
    TASK_TITLE=$(echo $task | jq -r '.title')
    TASK_CREATED=$(echo $task | jq -r '.created_at')
    TASK_CLOSED=$(echo $task | jq -r '.closed_at')
    TASK_DURATION=$(calculate_duration $TASK_CREATED $TASK_CLOSED)

    echo "- ✅ $TASK_TITLE (Duration: $TASK_DURATION)" >> $OUTPUT_FILE
  done
  echo "" >> $OUTPUT_FILE
done

# Add discovered issues section
echo "## Issues Discovered During Implementation" >> $OUTPUT_FILE
bd list --deps discovered-from:$EPIC_ID --json | while read issue; do
  ISSUE_TITLE=$(echo $issue | jq -r '.title')
  ISSUE_STATUS=$(echo $issue | jq -r '.status')
  echo "- [$ISSUE_STATUS] $ISSUE_TITLE" >> $OUTPUT_FILE
done

echo "Report generated: $OUTPUT_FILE"
```

### Step 2: Generate Metrics Report

```python
#!/usr/bin/env python3
# generate_metrics.py

import json
import subprocess
from datetime import datetime

def get_bd_data(epic_id):
    """Extract all bd data for an epic"""
    cmd = f"bd show {epic_id} --json"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(result.stdout)

def calculate_metrics(epic_id):
    """Calculate implementation metrics from bd data"""

    # Get all tasks
    cmd = f"bd list --deps parent-child:{epic_id} --json"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    tasks = json.loads(result.stdout)

    metrics = {
        'total_tasks': len(tasks),
        'completed_tasks': len([t for t in tasks if t['status'] == 'closed']),
        'bugs_found': len([t for t in tasks if t['type'] == 'bug']),
        'total_duration': calculate_total_duration(tasks),
        'average_task_duration': calculate_average_duration(tasks),
    }

    return metrics

def generate_markdown_report(epic_id, metrics):
    """Generate final markdown documentation"""

    template = f"""
# Implementation Metrics Report

## Epic: {epic_id}

### Execution Metrics
- **Total Tasks**: {metrics['total_tasks']}
- **Completed**: {metrics['completed_tasks']}
- **Completion Rate**: {metrics['completed_tasks']/metrics['total_tasks']*100:.1f}%
- **Bugs Discovered**: {metrics['bugs_found']}
- **Total Duration**: {metrics['total_duration']}
- **Average Task Duration**: {metrics['average_task_duration']}

### Quality Metrics
- **Test Coverage**: Extracted from test runs
- **TDD Compliance**: 100% (enforced by workflow)
- **BDD Scenarios**: Count from feature files

### Lessons Learned
[Generated from discovered-from issues]
"""

    return template

# Usage
if __name__ == "__main__":
    import sys
    epic_id = sys.argv[1]

    metrics = calculate_metrics(epic_id)
    report = generate_markdown_report(epic_id, metrics)

    output_file = f"docs/implementation/{datetime.now():%Y%m%d}-metrics.md"
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"Metrics report generated: {output_file}")
```

## Advanced bd Patterns for Implementation

### Pattern 1: Test-First Task Creation

```bash
# Always create test task before implementation task
TEST_ID=$(bd create "Write BDD tests for $FEATURE" -t task -p 1 --json | jq -r '.id')
IMPL_ID=$(bd create "Implement $FEATURE" -t task -p 1 --deps blocks:$TEST_ID --json | jq -r '.id')
```

### Pattern 2: Parallel Work Streams

```bash
# Create independent work streams that can be worked in parallel
bd create "Frontend: Implement UI components" -t feature -p 1 --deps parent-child:$EPIC_ID --json
bd create "Backend: Implement API endpoints" -t feature -p 1 --deps parent-child:$EPIC_ID --json
bd create "Infrastructure: Setup deployment" -t feature -p 1 --deps parent-child:$EPIC_ID --json

# Check all ready work across streams
bd ready --json
```

### Pattern 3: Risk Management

```bash
# Tag high-risk tasks for special attention
bd create "Implement complex algorithm X" \
  -t task -p 1 \
  -d "HIGH RISK: Complex implementation, needs senior review" \
  --json

# Create contingency tasks
bd create "Fallback: Simple implementation of X" \
  -t task -p 3 \
  -d "Contingency if complex algorithm fails" \
  --json
```

### Pattern 4: Review Gates

```bash
# Create review tasks that block deployment
REVIEW_ID=$(bd create "Architecture review of Phase 1" \
  -t task -p 0 \
  --deps blocks:$PHASE2_ID \
  --json | jq -r '.id')

# Phase 2 can't start until review completes
bd close $REVIEW_ID --reason "Review passed, no issues" --json
```

## Quality Enforcement Through bd

### Automatic Quality Gates

1. **Test-First Enforcement**: Implementation tasks depend on test tasks
2. **Sequential Phases**: Later phases blocked until earlier ones complete
3. **Review Requirements**: Deployment blocked until reviews complete
4. **Bug Priority**: Discovered bugs get priority 0 (critical)

### Tracking Quality Metrics

```bash
# Count test tasks vs implementation tasks
TEST_COUNT=$(bd list --type task --json | jq '[.[] | select(.title | contains("test"))] | length')
IMPL_COUNT=$(bd list --type task --json | jq '[.[] | select(.title | contains("Implement"))] | length')

# Verify test-first compliance
if [ $TEST_COUNT -lt $IMPL_COUNT ]; then
  echo "WARNING: Missing tests for some implementations"
fi

# Check for incomplete high-priority items
bd list --priority 0 --status pending --json
```

## Migration from Manual Tracking

### For Existing Plans

1. Parse existing markdown for tasks
2. Create bd issues for incomplete work
3. Link dependencies based on plan structure
4. Archive old tracking documents
5. Use bd going forward

### Example Migration Script

```bash
#!/bin/bash
# migrate_to_bd.sh

# Parse existing plan and create bd structure
grep "^### Task" implementation-plan.md | while read line; do
  TASK_NAME=$(echo $line | sed 's/### Task [0-9.]*: //')
  bd create "$TASK_NAME" -t task -p 2 --json
done

# Now manually add dependencies and relationships
bd list --json | jq -r '.[] | "\(.id): \(.title)"'
# Add dependencies based on original plan structure
```

## BDD Test Validation Requirements

### Mandatory Validation Commands

Every BDD test task MUST include these validation steps:

```bash
# 1. Verify feature file exists
ls -la tests/features/[name].feature

# 2. Verify step definitions exist
ls -la tests/step_definitions/test_[name]_steps.py

# 3. Check for missing step definitions
uv run pytest tests/features/[name].feature --collect-only 2>&1 | grep -E "StepDefinitionNotFound|not found"

# 4. Run tests to verify RED phase (should fail with assertions, not missing steps)
uv run pytest tests/features/[name].feature -v

# 5. Verify no standalone test files were created
find tests -name "test_*.py" -type f | grep -v step_definitions | grep [feature_name]
```

### Common BDD Implementation Failures

#### 1. Missing scenarios() Import
```python
# ❌ WRONG - Forgot to load scenarios
from pytest_bdd import given, when, then

@given("some condition")
def setup():
    pass
# Result: Tests won't be discovered

# ✅ CORRECT - scenarios() loads the feature file
from pytest_bdd import scenarios, given, when, then

scenarios("/Users/adam/dev/multicardz/tests/features/my_feature.feature")
```

#### 2. Incorrect Step Definition Syntax
```python
# ❌ WRONG - Missing parsers for parameterized steps
@when("I drag tag 'tag1' to zone 'available'")
def drag_specific_tag():
    pass

# ✅ CORRECT - Use parsers for parameters
@when(parsers.parse("I drag tag '{tag_id}' to zone '{zone_type}'"))
def drag_tag(tag_id: str, zone_type: str):
    pass
```

#### 3. Test Context Not Shared
```python
# ❌ WRONG - No state sharing between steps
@given("initial state")
def setup():
    data = {"key": "value"}  # Lost after this step

@then("verify state")
def verify():
    # Can't access 'data' from setup
    pass

# ✅ CORRECT - Use fixture for state sharing
@pytest.fixture
def test_context():
    return {}

@given("initial state")
def setup(test_context):
    test_context["data"] = {"key": "value"}

@then("verify state")
def verify(test_context):
    assert test_context["data"]["key"] == "value"
```

## Common Pitfalls and Solutions

### BDD-Specific Pitfalls

#### ❌ DON'T

- Create feature files without corresponding step definitions
- Write standalone Playwright tests instead of BDD step definitions
- Use test classes for BDD scenarios
- Forget the scenarios() import in step definition files
- Create test files outside of tests/step_definitions/ for BDD tests
- Mix BDD and non-BDD test approaches in the same feature

#### ✅ DO

- Always create both feature file AND step definitions together
- Use pytest-bdd decorators exclusively for BDD tests
- Reference existing step definition patterns in the codebase
- Validate tests can run before marking task complete
- Include explicit file paths in task descriptions
- Specify validation commands in task requirements

### General Implementation Pitfalls

#### ❌ DON'T

- Create markdown documents before work is complete
- Track timestamps manually when bd does it automatically
- Update multiple tracking systems (bd is the single source)
- Skip creating bd issues for "quick tasks"
- Ignore discovered issues during implementation

#### ✅ DO

- Create complete bd structure before starting any work
- Let bd handle all timestamp tracking automatically
- Generate documentation from bd data after completion
- Create bd issues even for small tasks (maintains history)
- Link all discovered issues with discovered-from

## Enforcement and Compliance

### Pre-Implementation Checklist

- [ ] Epic created in bd with clear success criteria
- [ ] All phases created as features with dependencies
- [ ] All tasks created with proper parent-child relationships
- [ ] Test tasks created before implementation tasks
- [ ] Dependencies properly set with blocks relationships
- [ ] Ready queue shows correct first tasks

### During Implementation Checklist

- [ ] Working from bd ready queue only
- [ ] One task in_progress at a time
- [ ] Discovered issues linked with discovered-from
- [ ] Tasks closed only when fully complete
- [ ] Test coverage verified before closing tasks

### Post-Implementation Checklist

- [ ] All tasks in epic marked closed
- [ ] Timing data extracted from bd
- [ ] Markdown report generated from bd data
- [ ] Metrics calculated and documented
- [ ] Lessons learned captured from discovered issues
- [ ] bd data exported for archival

## Complete Example: BDD Task Creation to Validation

### Example: Creating DATAOS Compliance Tests

#### Step 1: Create Properly Specified bd Task

```bash
bd create "Create BDD tests for DATAOS cache violations" \
  -t task -p 1 \
  -d "Requirements:
      1. Create feature file: tests/features/dataos-compliance.feature
      2. Create step definitions: tests/step_definitions/test_dataos_compliance_steps.py
      3. Framework: pytest-bdd with @given/@when/@then decorators
      4. Must include scenarios() to load feature file
      5. Create Playwright fixtures for browser/page management
      6. Pattern reference: tests/step_definitions/test_set_operations_steps.py
      7. Scenarios to test:
         - deriveStateFromDOM() returns fresh data on every call
         - No caching exists in the system
         - Rapid operations maintain consistency
      8. Validation commands:
         - uv run pytest tests/features/dataos-compliance.feature -v
         - Must fail with assertion errors, not StepDefinitionNotFound
      9. Acceptance: Tests executable and failing appropriately" \
  --json
```

#### Step 2: Implementation Following Specifications

```gherkin
# tests/features/dataos-compliance.feature
Feature: DATAOS Compliance - No Caching
  As a system architect
  I want to ensure the drag-drop system never caches DOM state
  So that we maintain DATAOS principle compliance

  Scenario: deriveStateFromDOM returns fresh data
    Given the drag-drop system is initialized
    And a tag with id "test-tag" is in zone "available"
    When I call deriveStateFromDOM() twice in rapid succession
    Then both calls should return identical fresh data from the DOM
    And the data should reflect the current DOM state

  Scenario: No caching during rapid operations
    Given the drag-drop system is initialized
    When I perform 100 rapid deriveStateFromDOM() calls
    Then each call should query the DOM directly
    And no cached values should be returned
```

```python
# tests/step_definitions/test_dataos_compliance_steps.py
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page
import pytest
from typing import Dict, Any, List

# MANDATORY: Load scenarios from feature file
scenarios("/Users/adam/dev/multicardz/tests/features/dataos-compliance.feature")

@pytest.fixture
def test_context() -> Dict[str, Any]:
    """Fixture to share state between steps."""
    return {"states": [], "measurements": []}

@pytest.fixture
def drag_drop_page(page: Page, test_context: Dict[str, Any]) -> Page:
    """Initialize drag-drop system for testing."""
    page.goto("http://localhost:8011/")
    page.wait_for_selector('[data-zone-type]')

    # Verify system is loaded
    assert page.evaluate("typeof window.dragDropSystem") == "object"

    test_context["page"] = page
    return page

@given("the drag-drop system is initialized")
def initialize_system(drag_drop_page: Page) -> None:
    """Ensure drag-drop system is ready."""
    result = drag_drop_page.evaluate("""
        typeof window.dragDropSystem !== 'undefined' &&
        typeof window.dragDropSystem.deriveStateFromDOM === 'function'
    """)
    assert result is True, "Drag-drop system not properly initialized"

@given(parsers.parse('a tag with id "{tag_id}" is in zone "{zone_type}"'))
def setup_tag_in_zone(drag_drop_page: Page, tag_id: str, zone_type: str) -> None:
    """Place a tag in a specific zone for testing."""
    # Implementation to set up tag in zone
    pass

@when("I call deriveStateFromDOM() twice in rapid succession")
def call_derive_state_twice(drag_drop_page: Page, test_context: Dict[str, Any]) -> None:
    """Call deriveStateFromDOM twice and capture results."""
    result = drag_drop_page.evaluate("""
        () => {
            const state1 = window.dragDropSystem.deriveStateFromDOM();
            const state2 = window.dragDropSystem.deriveStateFromDOM();
            return {
                state1: JSON.stringify(state1),
                state2: JSON.stringify(state2),
                identical: JSON.stringify(state1) === JSON.stringify(state2)
            };
        }
    """)
    test_context["comparison_result"] = result

@when(parsers.parse("I perform {count:d} rapid deriveStateFromDOM() calls"))
def perform_rapid_calls(drag_drop_page: Page, test_context: Dict[str, Any], count: int) -> None:
    """Perform multiple rapid calls to test for caching."""
    result = drag_drop_page.evaluate(f"""
        () => {{
            const states = [];
            for (let i = 0; i < {count}; i++) {{
                states.push(window.dragDropSystem.deriveStateFromDOM());
            }}
            return states;
        }}
    """)
    test_context["states"] = result

@then("both calls should return identical fresh data from the DOM")
def verify_identical_fresh_data(test_context: Dict[str, Any]) -> None:
    """Verify both calls returned the same fresh data."""
    assert test_context["comparison_result"]["identical"] is True

@then("the data should reflect the current DOM state")
def verify_current_dom_state(drag_drop_page: Page, test_context: Dict[str, Any]) -> None:
    """Verify the returned data matches actual DOM state."""
    # Implementation to verify DOM state matches returned data
    pass

@then("each call should query the DOM directly")
def verify_dom_queries(test_context: Dict[str, Any]) -> None:
    """Verify each call queries the DOM (no caching)."""
    states = test_context["states"]
    # All states should be identical if querying fresh DOM
    assert all(s == states[0] for s in states)

@then("no cached values should be returned")
def verify_no_caching(test_context: Dict[str, Any]) -> None:
    """Ensure no caching mechanism is in place."""
    # Implementation to verify no caching
    pass
```

#### Step 3: Validation

```bash
# Run validation commands from task specification
uv run pytest tests/features/dataos-compliance.feature -v

# Expected output (RED phase - tests fail with assertions):
# tests/features/dataos-compliance.feature::test_derive_state_from_dom_returns_fresh_data FAILED
# AssertionError: Drag-drop system not properly initialized
#
# NOT this error:
# StepDefinitionNotFound: Step 'Given the drag-drop system is initialized' not found
```

## Conclusion

The bd-first workflow with enhanced BDD specifications eliminates implementation ambiguity. By providing explicit technical requirements:

1. **Explicit Framework Requirements**: Specify pytest-bdd, not just "BDD tests"
2. **File Location Specifications**: Exact paths for features and step definitions
3. **Pattern References**: Point to existing implementations as templates
4. **Validation Commands**: Include exact commands to verify correctness
5. **Acceptance Criteria**: Clear definition of "done" for each task
6. **Implementation Checklists**: Step-by-step guidance for developers

The enhanced guidelines ensure that:
- Tasks are sufficiently prescriptive for correct first-attempt implementation
- BDD tests are always executable, not just stubs
- The RED-GREEN-REFACTOR cycle is properly followed
- No confusion between BDD and standalone test approaches

---

**Remember**:
- bd is your implementation tracker
- Task descriptions must be technically explicit
- BDD requires BOTH feature files AND step definitions
- Validation must show assertion failures, not missing steps
- Always reference existing patterns in the codebase
