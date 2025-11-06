# Documentation Maintenance Process

**Document Type**: Standards & Process
**Date**: 2025-11-06
**Version**: 1
**Status**: ACTIVE
**Owner**: Engineering Team

---

## Executive Summary

This document establishes a systematic process for maintaining the multicardz™ documentation suite. The goal is to prevent the documentation drift that occurred between September-November 2025, where 96 documents fell out of sync with actual implementation.

### Core Principles

1. **Documentation is Code**: Docs live in repo, reviewed in PRs, versioned with git
2. **Update on Ship**: Features aren't "done" until docs are updated
3. **Quarterly Reviews**: Systematic audit every 3 months
4. **Automated Validation**: Pre-commit hooks enforce standards
5. **Single Source of Truth**: Implementation matrix tracks doc → code alignment

---

## Quarterly Documentation Review

### Schedule

Reviews occur on the **first Monday** of:
- **February** (Q1 review)
- **May** (Q2 review)
- **August** (Q3 review)
- **November** (Q4 review)

**Duration**: 4-6 hours
**Attendees**: Tech lead, 2 senior engineers, documentation owner

---

### Review Process

#### Step 1: Generate Documentation Health Report

Run automated script to assess documentation quality:

```bash
./scripts/docs-health-check.sh
```

**Output**:
```
Documentation Health Report - 2025-11-06
=========================================

Total Documents: 96
With Status Headers: 96 (100%)
Without Status Headers: 0 (0%)

Implementation Status Distribution:
- IMPLEMENTED: 45 (47%)
- PLANNED: 12 (13%)
- PHASED: 8 (8%)
- SUPERSEDED: 15 (16%)
- DEPRECATED: 3 (3%)
- IN PROGRESS: 13 (14%)

Last Verified Distribution:
- Within 30 days: 62 (65%)
- 30-90 days: 24 (25%)
- 90+ days: 10 (10%) ⚠️

Missing Implementation Evidence: 8 (8%) ⚠️

Documentation Health Score: 87/100
```

**Health Score Formula**:
```
Score = (
    (docs_with_headers / total_docs) * 30 +
    (docs_verified_30_days / total_docs) * 30 +
    (docs_with_evidence / total_docs) * 20 +
    (implemented_docs / (implemented_docs + planned_docs)) * 20
)
```

**Target**: Health Score ≥ 90/100

---

#### Step 2: Review Flagged Documents

Focus on documents flagged by health check:

1. **Last Verified > 90 days**: May be outdated
2. **Missing Evidence**: Claims implementation without proof
3. **Status = IN PROGRESS**: May have completed
4. **Status = PLANNED**: Check if implemented

**Process**:
1. Read document
2. Verify claims against codebase
3. Update status header
4. Add/update implementation evidence
5. Mark as verified (update LAST VERIFIED date)

---

#### Step 3: Update Implementation Matrix

The **Implementation Matrix** tracks doc → code alignment:

```markdown
# Implementation Matrix

| Doc # | Title | Status | Plan Doc | Implementation | % Complete | Last Verified |
|-------|-------|--------|----------|----------------|------------|---------------|
| 001 | JavaScript Architecture | IMPLEMENTED | N/A | apps/static/js/*.js | 100% | 2025-11-06 |
| 022 | Data Architecture | IMPLEMENTED | 016 | apps/user/database.py | 100% | 2025-11-06 |
| 024 | Backend Architecture | IMPLEMENTED | 016 | apps/user/main.py | 100% | 2025-11-06 |
| 033 | Font Metrics | IMPLEMENTED | N/A | apps/static/css/user.css:8-134 | 100% | 2025-11-06 |
| 035 | Group Tags | IMPLEMENTED | 036 | apps/static/js/group-*.js | 100% | 2025-11-06 |
| 039 | genX Integration | PLANNED | N/A | N/A | 0% | 2025-11-06 |
| 016 | Unified Plan | PHASED | N/A | Partial (auth deferred) | 40% | 2025-11-06 |
| 026 | Onboarding | PHASED | 027 | Partial (lesson loading) | 25% | 2025-11-06 |
```

**Fields**:
- **Doc #**: Document number (e.g., 001, 022)
- **Title**: Short title
- **Status**: IMPLEMENTED, PLANNED, PHASED, SUPERSEDED, DEPRECATED, IN PROGRESS
- **Plan Doc**: Reference to implementation plan (if separate)
- **Implementation**: File path or description of implementation
- **% Complete**: 0-100% (estimates acceptable)
- **Last Verified**: Date of last verification

**Location**: `docs/implementation-matrix.md`

---

#### Step 4: Consolidate Duplicates

Identify and merge duplicate documentation:

**Indicators of Duplication**:
- Multiple docs covering same feature
- Same content in different files
- Superseded docs not marked as such

**Process**:
1. Identify canonical document (most recent, most comprehensive)
2. Update canonical with any missing content from duplicates
3. Mark duplicates as SUPERSEDED
4. Add cross-reference in superseded doc

**Example**:
```markdown
# multicardz™ Authentication Architecture (OLD)

---
**IMPLEMENTATION STATUS**: SUPERSEDED
**SUPERSEDED BY**: docs/architecture/041-Authentication-Architecture-and-Plan.md
**SUPERSEDED DATE**: 2025-11-06
---

**NOTE**: This document has been superseded. See doc 041 for current authentication architecture.

[Rest of document preserved for historical reference]
```

---

#### Step 5: Update Roadmap Alignment

Verify architecture docs align with product roadmap:

**Roadmap** (from product team):
- Q4 2025: Group Tags ✓ (implemented)
- Q1 2026: genX Migration (planned)
- Q2 2026: Authentication Upgrade (planned)
- Q3 2026: Turso Migration (planned)

**Documentation Gaps**:
- Missing: genX Migration implementation plan
- Missing: Auth0 integration detailed architecture
- Missing: Turso migration plan

**Action**: Create missing docs or flag as backlog

---

#### Step 6: Generate Review Summary

Create summary report:

```markdown
# Q4 2025 Documentation Review Summary

**Date**: 2025-11-06
**Attendees**: Alice (Tech Lead), Bob (Senior Eng), Carol (Senior Eng), Dave (Docs Owner)
**Duration**: 5 hours

## Health Score

**Previous Quarter**: 72/100 (August 2025)
**Current Quarter**: 87/100 (November 2025)
**Change**: +15 points ✓

## Actions Completed

1. Updated 24 docs with missing status headers
2. Verified 18 docs with outdated verification dates
3. Consolidated 4 duplicate authentication docs into single doc 041
4. Marked 3 legacy docs as SUPERSEDED
5. Created implementation matrix (96 docs tracked)
6. Added implementation evidence to 12 docs

## Issues Identified

1. **drag-drop.js undocumented**: 80KB file with no architecture doc
   - **Resolution**: Created doc 040 (Current JavaScript Implementation)

2. **Font metrics undocumented**: Implemented but not in docs
   - **Resolution**: Added implementation notes to doc 033

3. **genX architecture unclear**: Future direction not documented
   - **Resolution**: Created doc 039 (genX Integration Architecture)

## Action Items for Next Quarter

1. Create genX Migration Implementation Plan (Q1 2026)
2. Create Auth0 Integration Architecture (Q2 2026)
3. Review and update all PHASED docs (verify still deferred)
4. Achieve 95/100 health score target

## Next Review

**Date**: February 3, 2026 (Q1 2026 review)
**Owner**: Dave (Docs Owner)
```

**Location**: `docs/reviews/2025-Q4-documentation-review.md`

---

## Feature Shipment Documentation Process

### Requirement

**No feature ships without documentation.**

This means:
1. Architecture doc (if new feature) or update (if existing feature)
2. Implementation evidence in doc
3. Status header updated to IMPLEMENTED
4. Tests documented
5. Deployment notes (if infrastructure changes)

---

### Process

#### Step 1: Create Architecture Doc (New Features)

**When**: During design phase, before implementation

**Template**:
```markdown
# multicardz™ [Feature Name]

**Document Number**: [Next available number]
**Date**: YYYY-MM-DD
**Version**: 1
**Status**: PLANNED
**Author**: [Your name]

---

---
**IMPLEMENTATION STATUS**: PLANNED
**LAST VERIFIED**: [Today's date]
**IMPLEMENTATION EVIDENCE**: Not yet implemented
---

## Executive Summary

[What this feature does, why it exists, key benefits]

## Architecture

[Technical design, data models, API endpoints, etc.]

## Implementation Plan

[Step-by-step plan, dependencies, timeline]

## Testing Strategy

[Unit tests, integration tests, E2E tests]

## Deployment

[Deployment steps, infrastructure changes, rollback plan]

## Success Criteria

[How to verify feature works]
```

**Review**: Tech lead reviews before implementation starts

---

#### Step 2: Update During Implementation

**When**: As implementation progresses

**Actions**:
1. Update status to IN PROGRESS
2. Add implementation evidence (file paths, line numbers)
3. Document any deviations from plan
4. Update LAST VERIFIED date

**Example PR**:
```
feat: implement drag-and-drop for tags

- Implement multi-selection with Shift/Cmd/Ctrl
- Add drag-and-drop positioning
- Update doc 035 status to IN PROGRESS
- Add implementation evidence (apps/static/js/drag-drop.js)

Related: docs/architecture/035-Group-Tags.md
```

---

#### Step 3: Finalize on Ship

**When**: Before merging to main

**Actions**:
1. Update status to IMPLEMENTED
2. Verify implementation evidence is accurate
3. Add screenshots/videos if UI feature
4. Document any known issues or limitations
5. Update LAST VERIFIED date

**Pre-Merge Checklist**:
- [ ] Architecture doc exists
- [ ] Status = IMPLEMENTED
- [ ] Implementation evidence accurate
- [ ] Tests documented
- [ ] Deployment notes added (if applicable)
- [ ] LAST VERIFIED = today

**Enforcement**: Pre-commit hook validates documentation

---

### Example: Full Feature Documentation Lifecycle

**Feature**: Group Tags

**Phase 1: Planning (Oct 22, 2025)**
- Create `docs/architecture/035-2025-10-26-Group-Tags-Architecture.md`
- Status: PLANNED
- Implementation evidence: "Not yet implemented"
- Create `docs/implementation/036-Group-Tags-Implementation-Plan-v1.md`

**Phase 2: Implementation Start (Oct 28, 2025)**
- Update doc 035 status to IN PROGRESS
- Add evidence: "apps/static/js/group-tags.js (partial)"
- Commit message: `feat: start group tags implementation (doc 035)`

**Phase 3: Implementation Progress (Nov 1, 2025)**
- Add more evidence: "apps/static/js/group-ui-integration.js"
- Document deviations: "Used DOM-as-Authority pattern instead of backend state"
- Update LAST VERIFIED: 2025-11-01

**Phase 4: Feature Complete (Nov 5, 2025)**
- Update status to IMPLEMENTED
- Finalize evidence: "apps/static/js/group-tags.js, group-ui-integration.js (715 lines)"
- Add screenshots to doc
- Document known issues: "No undo for group deletion"
- Update LAST VERIFIED: 2025-11-05

**Phase 5: Post-Ship (Nov 6, 2025)**
- Add to implementation matrix
- Update quarterly review checklist
- Close tracking issue in bd

---

## Pre-Commit Hook for Status Validation

### Purpose

Enforce documentation standards automatically:
1. All architecture docs have status headers
2. Status headers are valid
3. LAST VERIFIED is recent (within 90 days)
4. Implementation evidence present for IMPLEMENTED docs

---

### Hook Script

**Location**: `.git/hooks/pre-commit`

```bash
#!/bin/bash
# Documentation validation pre-commit hook

echo "Running documentation validation..."

# Find all markdown files in docs/
docs=$(find docs/ -name "*.md" -not -path "docs/reviews/*")

errors=0

for doc in $docs; do
    # Skip README files
    if [[ "$doc" == *"README.md" ]]; then
        continue
    fi

    # Check for status header
    if ! grep -q "^**IMPLEMENTATION STATUS**:" "$doc"; then
        echo "❌ Missing status header: $doc"
        errors=$((errors + 1))
    fi

    # Check for last verified date
    if ! grep -q "^**LAST VERIFIED**:" "$doc"; then
        echo "❌ Missing LAST VERIFIED: $doc"
        errors=$((errors + 1))
    fi

    # Extract status
    status=$(grep "^**IMPLEMENTATION STATUS**:" "$doc" | sed 's/.*: //')

    # Validate status value
    valid_statuses=("IMPLEMENTED" "PLANNED" "PHASED" "SUPERSEDED" "DEPRECATED" "IN PROGRESS")
    if [[ ! " ${valid_statuses[@]} " =~ " ${status} " ]]; then
        echo "❌ Invalid status '$status' in: $doc"
        echo "   Valid statuses: ${valid_statuses[*]}"
        errors=$((errors + 1))
    fi

    # Check IMPLEMENTED docs have evidence
    if [[ "$status" == "IMPLEMENTED" ]]; then
        if ! grep -q "^**IMPLEMENTATION EVIDENCE**:" "$doc"; then
            echo "❌ Missing implementation evidence in IMPLEMENTED doc: $doc"
            errors=$((errors + 1))
        fi
    fi

    # Check LAST VERIFIED is recent (within 90 days)
    last_verified=$(grep "^**LAST VERIFIED**:" "$doc" | sed 's/.*: //')
    if [[ -n "$last_verified" ]]; then
        verified_timestamp=$(date -j -f "%Y-%m-%d" "$last_verified" +%s 2>/dev/null)
        current_timestamp=$(date +%s)
        days_ago=$(( (current_timestamp - verified_timestamp) / 86400 ))

        if [[ $days_ago -gt 90 ]]; then
            echo "⚠️  LAST VERIFIED >90 days ago ($days_ago days): $doc"
            # Warning only, don't block commit
        fi
    fi
done

if [[ $errors -gt 0 ]]; then
    echo ""
    echo "❌ Documentation validation failed with $errors error(s)"
    echo ""
    echo "To fix:"
    echo "1. Add missing status headers using template in docs/standards/"
    echo "2. Ensure status is one of: IMPLEMENTED, PLANNED, PHASED, SUPERSEDED, DEPRECATED, IN PROGRESS"
    echo "3. Add implementation evidence to IMPLEMENTED docs"
    echo "4. Update LAST VERIFIED dates (within 90 days recommended)"
    echo ""
    exit 1
fi

echo "✓ Documentation validation passed"
exit 0
```

**Installation**:
```bash
chmod +x .git/hooks/pre-commit
```

**Skip Hook** (emergency only):
```bash
git commit --no-verify -m "Emergency fix"
```

---

### Hook Customization

**Strictness Levels**:

1. **Strict** (production): Block commits for any violation
2. **Warning** (default): Warn for old docs, block for missing headers
3. **Permissive** (development): Warn only, never block

**Configuration** (`.git/hooks/pre-commit.config`):
```bash
# Documentation validation config
STRICTNESS="warning"  # strict, warning, permissive
MAX_VERIFIED_DAYS=90
REQUIRE_EVIDENCE=true
BLOCK_ON_OLD_DOCS=false
```

---

## Implementation Matrix Format

### Purpose

The implementation matrix provides a **single source of truth** mapping documentation to code:

- **Documentation → Code**: Which files implement which docs
- **% Complete**: How much of the plan is done
- **Status Tracking**: Quick view of implementation progress

---

### Matrix Structure

**Location**: `docs/implementation-matrix.md`

**Format**:
```markdown
# Implementation Matrix

**Last Updated**: 2025-11-06
**Total Documents**: 96
**Implementation Rate**: 47/96 (49%)

## Legend

**Status**:
- IMPLEMENTED: Feature is fully implemented and shipped
- IN PROGRESS: Implementation underway
- PLANNED: Design complete, not yet started
- PHASED: Intentionally deferred to future phase
- SUPERSEDED: Replaced by newer doc
- DEPRECATED: No longer relevant

**% Complete**: Rough estimate (0-100%)

---

## Architecture Documents

| Doc # | Title | Status | Plan Doc | Implementation | % Complete | Last Verified |
|-------|-------|--------|----------|----------------|------------|---------------|
| 001 | JavaScript Architecture | IMPLEMENTED | N/A | apps/static/js/*.js | 100% | 2025-11-06 |
| 002 | Tag Management System | SUPERSEDED | N/A | See doc 035 | N/A | 2025-11-06 |
| 003 | Database Schema | IMPLEMENTED | 016 | apps/user/database.py | 100% | 2025-11-06 |
| ... | ... | ... | ... | ... | ... | ... |

## Implementation Plans

| Doc # | Title | Status | Architecture | Implementation | % Complete | Last Verified |
|-------|-------|--------|--------------|----------------|------------|---------------|
| 016 | Unified Implementation Plan | PHASED | 022, 024 | Partial (auth deferred) | 40% | 2025-11-06 |
| 036 | Group Tags Plan | IMPLEMENTED | 035 | apps/static/js/group-*.js | 100% | 2025-11-06 |
| ... | ... | ... | ... | ... | ... | ... |

## Standards & Guidelines

| Doc # | Title | Status | Applies To | % Complete | Last Verified |
|-------|-------|--------|------------|------------|---------------|
| performance-monitoring-standards | Performance Standards | ACTIVE | All JS files | 100% | 2025-11-06 |
| documentation-maintenance-process | Docs Process | ACTIVE | All docs | 100% | 2025-11-06 |
| ... | ... | ... | ... | ... | ... |
```

---

### Updating the Matrix

**When**:
1. New doc created → Add row
2. Feature ships → Update status, % complete
3. Doc superseded → Mark as SUPERSEDED
4. Quarterly review → Verify all rows

**Process**:
```bash
# Add new doc
echo "| 042 | New Feature | PLANNED | N/A | N/A | 0% | 2025-11-06 |" >> docs/implementation-matrix.md

# Update status
sed -i '' 's/| 042 | New Feature | PLANNED/| 042 | New Feature | IN PROGRESS/' docs/implementation-matrix.md

# Mark complete
sed -i '' 's/| 042 | .* | IN PROGRESS | .* | .* | 50%/| 042 | New Feature | IMPLEMENTED | apps/feature.py | 100%/' docs/implementation-matrix.md
```

**Automation** (future):
```bash
# Generate matrix from doc headers
./scripts/generate-implementation-matrix.sh > docs/implementation-matrix.md
```

---

## Escalation Path for Conflicts

### Conflict Types

1. **Doc says IMPLEMENTED, code doesn't exist**
   - **Resolution**: Update doc to PLANNED or PHASED
   - **Owner**: Tech lead
   - **Timeline**: Same day

2. **Code exists, no doc**
   - **Resolution**: Create doc, mark IMPLEMENTED
   - **Owner**: Original developer or tech lead
   - **Timeline**: Within 1 week

3. **Doc and code disagree on design**
   - **Resolution**: Determine source of truth (usually code), update doc
   - **Owner**: Tech lead + original developer
   - **Timeline**: Within 3 days

4. **Multiple docs claim to be authoritative**
   - **Resolution**: Identify canonical doc, mark others SUPERSEDED
   - **Owner**: Documentation owner
   - **Timeline**: During quarterly review

---

### Escalation Process

**Level 1: Developer** (0-1 day)
- Developer notices discrepancy
- Attempts to resolve (update doc or code)
- Creates PR with fix

**Level 2: Tech Lead** (1-3 days)
- PR review identifies deeper conflict
- Tech lead investigates
- Determines correct approach
- Developer implements fix

**Level 3: Architecture Review** (3-7 days)
- Conflict involves architectural decision
- Schedule architecture review meeting
- Attendees: Tech lead, senior engineers, product manager
- Decision documented in new architecture doc

**Level 4: CTO** (7+ days)
- Conflict involves product direction or major refactor
- Escalate to CTO
- Decision may require customer input or market research

---

### Conflict Resolution Template

```markdown
# Documentation Conflict Resolution: [Issue]

**Date**: YYYY-MM-DD
**Reported By**: [Name]
**Severity**: Low / Medium / High / Critical

## Conflict Description

**Doc Claims**: [What the documentation says]
**Code Reality**: [What the code actually does]
**Impact**: [User impact, technical debt, etc.]

## Investigation

**Evidence**:
- Doc: [file path, lines]
- Code: [file path, lines]
- Git History: [relevant commits]

**Root Cause**: [Why did this divergence occur?]

## Resolution

**Decision**: [What is the source of truth?]
**Action Plan**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Updated Docs**: [List of docs updated]
**Updated Code**: [List of code files changed]

**Verified By**: [Name]
**Verified Date**: YYYY-MM-DD

## Prevention

**Lesson Learned**: [What can prevent this in future?]
**Process Update**: [Any changes to documentation process]
```

**Location**: `docs/resolutions/YYYY-MM-DD-conflict-[issue].md`

---

## Tools and Automation

### Script 1: Documentation Health Check

**Location**: `scripts/docs-health-check.sh`

```bash
#!/bin/bash
# Documentation health check script

echo "Documentation Health Report - $(date +%Y-%m-%d)"
echo "========================================="
echo ""

# Count total docs
total_docs=$(find docs/ -name "*.md" ! -name "README.md" ! -path "docs/reviews/*" | wc -l)
echo "Total Documents: $total_docs"

# Count docs with status headers
docs_with_headers=$(grep -l "^**IMPLEMENTATION STATUS**:" docs/**/*.md | wc -l)
echo "With Status Headers: $docs_with_headers ($((docs_with_headers * 100 / total_docs))%)"
echo "Without Status Headers: $((total_docs - docs_with_headers)) ($(((total_docs - docs_with_headers) * 100 / total_docs))%)"
echo ""

# Status distribution
echo "Implementation Status Distribution:"
grep "^**IMPLEMENTATION STATUS**:" docs/**/*.md | sed 's/.*: //' | sort | uniq -c | while read count status; do
    pct=$((count * 100 / total_docs))
    echo "- $status: $count ($pct%)"
done
echo ""

# Last verified distribution
echo "Last Verified Distribution:"
current_timestamp=$(date +%s)

within_30=0
within_90=0
over_90=0

grep "^**LAST VERIFIED**:" docs/**/*.md | sed 's/.*: //' | while read verified_date; do
    verified_timestamp=$(date -j -f "%Y-%m-%d" "$verified_date" +%s 2>/dev/null)
    days_ago=$(( (current_timestamp - verified_timestamp) / 86400 ))

    if [[ $days_ago -le 30 ]]; then
        within_30=$((within_30 + 1))
    elif [[ $days_ago -le 90 ]]; then
        within_90=$((within_90 + 1))
    else
        over_90=$((over_90 + 1))
    fi
done

echo "- Within 30 days: $within_30 ($((within_30 * 100 / total_docs))%)"
echo "- 30-90 days: $within_90 ($((within_90 * 100 / total_docs))%)"
echo "- 90+ days: $over_90 ($((over_90 * 100 / total_docs))%) ⚠️"
echo ""

# Missing evidence
missing_evidence=$(grep -l "^**IMPLEMENTATION STATUS**: IMPLEMENTED" docs/**/*.md | xargs grep -L "^**IMPLEMENTATION EVIDENCE**:" | wc -l)
echo "Missing Implementation Evidence: $missing_evidence ($((missing_evidence * 100 / total_docs))%) ⚠️"
echo ""

# Calculate health score
score=$(( (docs_with_headers * 30 / total_docs) + (within_30 * 30 / total_docs) + ((total_docs - missing_evidence) * 20 / total_docs) ))
echo "Documentation Health Score: $score/100"

if [[ $score -lt 90 ]]; then
    echo "⚠️  Below target (90)"
else
    echo "✓ Target achieved"
fi
```

**Usage**:
```bash
./scripts/docs-health-check.sh
```

---

### Script 2: Generate Implementation Matrix

**Location**: `scripts/generate-implementation-matrix.sh`

```bash
#!/bin/bash
# Generate implementation matrix from doc headers

echo "# Implementation Matrix"
echo ""
echo "**Last Updated**: $(date +%Y-%m-%d)"
echo ""
echo "| Doc # | Title | Status | Implementation | Last Verified |"
echo "|-------|-------|--------|----------------|---------------|"

find docs/ -name "[0-9]*.md" | sort -V | while read doc; do
    doc_num=$(basename "$doc" | grep -o "^[0-9]*")
    title=$(grep "^# " "$doc" | head -1 | sed 's/# //' | sed 's/multicardz™ //')
    status=$(grep "^**IMPLEMENTATION STATUS**:" "$doc" | sed 's/.*: //')
    evidence=$(grep "^**IMPLEMENTATION EVIDENCE**:" "$doc" | sed 's/.*: //')
    verified=$(grep "^**LAST VERIFIED**:" "$doc" | sed 's/.*: //')

    echo "| $doc_num | $title | $status | $evidence | $verified |"
done
```

**Usage**:
```bash
./scripts/generate-implementation-matrix.sh > docs/implementation-matrix.md
```

---

### Script 3: Find Outdated Docs

**Location**: `scripts/find-outdated-docs.sh`

```bash
#!/bin/bash
# Find docs that haven't been verified recently

threshold_days=${1:-90}
echo "Finding docs not verified in last $threshold_days days..."
echo ""

current_timestamp=$(date +%s)

grep -H "^**LAST VERIFIED**:" docs/**/*.md | while IFS=: read file verified_line; do
    verified_date=$(echo "$verified_line" | sed 's/.*: //')
    verified_timestamp=$(date -j -f "%Y-%m-%d" "$verified_date" +%s 2>/dev/null)

    if [[ -z "$verified_timestamp" ]]; then
        echo "⚠️  Invalid date in $file: $verified_date"
        continue
    fi

    days_ago=$(( (current_timestamp - verified_timestamp) / 86400 ))

    if [[ $days_ago -gt $threshold_days ]]; then
        echo "⚠️  $file: $days_ago days ago ($(basename "$file"))"
    fi
done
```

**Usage**:
```bash
# Find docs >90 days old
./scripts/find-outdated-docs.sh 90

# Find docs >30 days old
./scripts/find-outdated-docs.sh 30
```

---

### Script 4: Validate Documentation PR

**Location**: `scripts/validate-docs-pr.sh`

```bash
#!/bin/bash
# Validate documentation changes in PR

echo "Validating documentation PR..."

# Get changed markdown files
changed_docs=$(git diff --name-only main...HEAD | grep "^docs/.*\.md$")

if [[ -z "$changed_docs" ]]; then
    echo "✓ No documentation changes"
    exit 0
fi

errors=0

for doc in $changed_docs; do
    echo "Checking $doc..."

    # Check status header
    if ! grep -q "^**IMPLEMENTATION STATUS**:" "$doc"; then
        echo "❌ Missing status header: $doc"
        errors=$((errors + 1))
    fi

    # Check LAST VERIFIED is today (for updated docs)
    today=$(date +%Y-%m-%d)
    if ! grep -q "^**LAST VERIFIED**: $today" "$doc"; then
        echo "⚠️  LAST VERIFIED should be today ($today): $doc"
    fi

    # If adding IMPLEMENTED status, require evidence
    if git diff main...HEAD "$doc" | grep "^+.*IMPLEMENTED"; then
        if ! grep -q "^**IMPLEMENTATION EVIDENCE**:" "$doc"; then
            echo "❌ IMPLEMENTED docs must have evidence: $doc"
            errors=$((errors + 1))
        fi
    fi
done

if [[ $errors -gt 0 ]]; then
    echo ""
    echo "❌ Documentation validation failed"
    exit 1
fi

echo "✓ Documentation validation passed"
exit 0
```

**Usage** (in GitHub Actions):
```yaml
- name: Validate documentation
  run: ./scripts/validate-docs-pr.sh
```

---

## Success Metrics

### Documentation Quality Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Health Score | ≥ 90/100 | 87/100 | ⚠️ |
| Docs with Headers | 100% | 100% | ✓ |
| Verified <30 days | ≥ 70% | 65% | ⚠️ |
| Verified <90 days | ≥ 95% | 90% | ⚠️ |
| Missing Evidence | 0% | 8% | ⚠️ |
| Implementation Rate | N/A | 49% | ℹ️ |

**Targets**:
- **Q1 2026**: 90/100 health score
- **Q2 2026**: 95/100 health score
- **Q3 2026**: Maintain 95/100

---

### Process Adoption Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Features shipped without docs | 0 | 1 (Nov) | ⚠️ |
| PRs blocked by doc validation | N/A | 0 | ℹ️ |
| Quarterly reviews completed | 100% | 100% | ✓ |
| Conflicts resolved <7 days | ≥ 90% | N/A | ℹ️ |

---

### Developer Satisfaction

**Survey Questions** (quarterly):
1. "Documentation accurately reflects codebase" (1-5 scale)
2. "Easy to find relevant documentation" (1-5 scale)
3. "Documentation process is reasonable" (1-5 scale)

**Target**: Average ≥ 4.0/5.0

---

## Migration Plan (Existing Docs)

### Phase 1: Add Status Headers (Completed)

**Goal**: All 96 docs have status headers
**Duration**: 1 day (Nov 6, 2025)
**Status**: ✓ Complete

---

### Phase 2: Verify Evidence (In Progress)

**Goal**: All IMPLEMENTED docs have accurate evidence
**Duration**: 2 weeks (Nov 7-20, 2025)
**Status**: In progress (8 docs missing evidence)

**Process**:
1. Review each IMPLEMENTED doc
2. Locate implementation in codebase
3. Add file paths and line numbers to doc
4. Verify implementation matches design
5. Update LAST VERIFIED date

---

### Phase 3: Create Implementation Matrix (Planned)

**Goal**: Single matrix tracking all 96 docs
**Duration**: 1 week (Nov 21-27, 2025)
**Status**: Planned

**Process**:
1. Run `generate-implementation-matrix.sh`
2. Manually verify % complete estimates
3. Add plan doc cross-references
4. Review with tech lead
5. Publish to `docs/implementation-matrix.md`

---

### Phase 4: Install Pre-Commit Hook (Planned)

**Goal**: Automated validation on every commit
**Duration**: 1 day (Nov 28, 2025)
**Status**: Planned

**Process**:
1. Test hook on dev machines
2. Document hook in README
3. Add to onboarding checklist
4. Install on all team members' machines
5. Monitor for false positives

---

### Phase 5: First Quarterly Review (Planned)

**Goal**: Establish baseline, identify gaps
**Duration**: 1 day (Feb 3, 2026)
**Status**: Planned

**Process**:
1. Run health check script
2. Review flagged documents
3. Update outdated docs
4. Generate review summary
5. Create action items for Q1

---

## Roles and Responsibilities

### Documentation Owner

**Responsibilities**:
- Run quarterly reviews
- Maintain implementation matrix
- Triage documentation conflicts
- Monitor health score
- Report to engineering team

**Time Commitment**: 8 hours/month

**Current Owner**: Dave (Docs Owner)

---

### Tech Lead

**Responsibilities**:
- Review architecture docs before implementation
- Approve doc updates in PRs
- Resolve doc/code conflicts
- Enforce doc-on-ship policy

**Time Commitment**: 4 hours/month

**Current Owner**: Alice (Tech Lead)

---

### Engineers

**Responsibilities**:
- Create architecture docs for new features
- Update docs when shipping features
- Verify LAST VERIFIED dates
- Report documentation conflicts

**Time Commitment**: 2 hours/month per engineer

---

### Product Manager

**Responsibilities**:
- Provide roadmap for documentation planning
- Review user-facing documentation
- Prioritize documentation gaps

**Time Commitment**: 2 hours/quarter

---

## Appendix A: Status Header Template

**Location**: `docs/templates/status-header-template.md`

```markdown
---
**IMPLEMENTATION STATUS**: [IMPLEMENTED | PLANNED | PHASED | SUPERSEDED | DEPRECATED | IN PROGRESS]
**LAST VERIFIED**: YYYY-MM-DD
**IMPLEMENTATION EVIDENCE**: [File paths, line numbers, or "Not yet implemented"]
---

<!-- Optional: Additional metadata -->
**SUPERSEDED BY**: [doc number] (if SUPERSEDED)
**SUPERSEDED DATE**: YYYY-MM-DD (if SUPERSEDED)
**PLANNED FOR**: [Quarter or date] (if PLANNED)
**DEFERRED UNTIL**: [Milestone] (if PHASED)
**DEPRECATION REASON**: [Reason] (if DEPRECATED)
```

---

## Appendix B: Architecture Doc Template

**Location**: `docs/templates/architecture-doc-template.md`

```markdown
# multicardz™ [Feature Name]

**Document Number**: [Next available number]
**Date**: YYYY-MM-DD
**Version**: 1
**Status**: [PLANNED | IN PROGRESS | IMPLEMENTED]
**Author**: [Your name]

---

---
**IMPLEMENTATION STATUS**: [PLANNED | IN PROGRESS | IMPLEMENTED]
**LAST VERIFIED**: YYYY-MM-DD
**IMPLEMENTATION EVIDENCE**: [File paths or "Not yet implemented"]
---

## Executive Summary

[2-3 paragraphs: What this feature does, why it exists, key benefits]

## Problem Statement

[What problem are we solving?]

## Proposed Solution

[High-level approach]

## Architecture

### Data Model

[Database schema, data structures]

### API Endpoints

[If applicable: REST endpoints, request/response formats]

### Frontend Components

[If applicable: UI components, user flows]

### Integration Points

[How this feature integrates with existing systems]

## Implementation Plan

[Step-by-step plan with dependencies and timeline]

## Testing Strategy

[Unit tests, integration tests, E2E tests]

## Deployment

[Deployment steps, infrastructure changes, rollback plan]

## Performance Considerations

[Impact on Lighthouse score, bundle size, etc.]

## Security Considerations

[Authentication, authorization, data validation]

## Success Criteria

[How to verify feature works]

## Open Questions

[Unresolved design decisions]

## References

[Related docs, external resources]

---

**Document Status**: [PLANNED | IN PROGRESS | IMPLEMENTED]
**Review Required**: [Tech Lead | CTO | None]
**Implementation Priority**: [Critical | High | Medium | Low]
**Estimated Effort**: [Time estimate]
**Impact**: [User impact description]
```

---

## Appendix C: Review Checklist

**Location**: `docs/templates/quarterly-review-checklist.md`

```markdown
# Quarterly Documentation Review Checklist

**Quarter**: Q[1-4] [Year]
**Review Date**: YYYY-MM-DD
**Attendees**: [Names]

## Pre-Review (1 hour)

- [ ] Run `docs-health-check.sh`
- [ ] Run `find-outdated-docs.sh 90`
- [ ] Generate implementation matrix
- [ ] Review previous quarter's action items
- [ ] Prepare agenda

## During Review (4-5 hours)

### Health Check (30 min)
- [ ] Review health score
- [ ] Identify concerning trends
- [ ] Flag critical issues

### Document Review (3 hours)
- [ ] Review docs with LAST VERIFIED >90 days
- [ ] Review docs with missing evidence
- [ ] Review IN PROGRESS docs (are they done?)
- [ ] Review PLANNED docs (are they started?)
- [ ] Review PHASED docs (still deferred?)

### Consolidation (1 hour)
- [ ] Identify duplicate documentation
- [ ] Mark superseded docs
- [ ] Create missing docs (if critical)
- [ ] Update implementation matrix

### Roadmap Alignment (30 min)
- [ ] Compare docs to product roadmap
- [ ] Identify gaps in upcoming features
- [ ] Plan new architecture docs needed

## Post-Review (30 min)

- [ ] Generate review summary
- [ ] Create action items for next quarter
- [ ] Schedule next review
- [ ] Publish summary to docs/reviews/

## Action Items

1. [Action item 1]
2. [Action item 2]
3. ...

## Next Review

**Date**: [First Monday of next quarter]
**Owner**: [Name]
```

---

## Conclusion

This documentation maintenance process ensures the multicardz™ documentation suite remains accurate, complete, and aligned with the codebase. By following quarterly reviews, enforcing doc-on-ship policies, and using automated validation, we prevent the documentation drift that occurred in 2025.

**Key Takeaways**:

1. **Documentation is Code**: Treat docs with same rigor as code
2. **No Ship Without Docs**: Features aren't done until documented
3. **Automate Validation**: Pre-commit hooks enforce standards
4. **Review Quarterly**: Systematic audits catch drift early
5. **Single Source of Truth**: Implementation matrix tracks alignment

By maintaining high documentation quality, we enable:
- Faster onboarding (new engineers understand system quickly)
- Better collaboration (shared understanding of architecture)
- Confident refactoring (docs explain why decisions were made)
- Reduced technical debt (documentation prevents knowledge loss)

---

## References

- **Doc 001**: JavaScript Architecture (Example of well-documented feature)
- **Doc 033**: Font Metrics Optimization (Example of implementation notes)
- **Doc 040**: Current JavaScript Implementation (Comprehensive implementation doc)
- **performance-monitoring-standards.md**: Related standards document

---

**Document Status**: Active Process
**Review Schedule**: Quarterly (next review February 2026)
**Maintenance Owner**: Documentation Owner
**Last Updated**: 2025-11-06
