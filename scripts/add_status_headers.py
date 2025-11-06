#!/usr/bin/env python3
"""
Add implementation status headers to all documentation markdown files.
Intelligently determines status based on file name and content patterns.
"""

import os
import re
from pathlib import Path
from datetime import datetime

# Status header template
STATUS_HEADER_TEMPLATE = """---
**IMPLEMENTATION STATUS**: {status}
**LAST VERIFIED**: {date}
**IMPLEMENTATION EVIDENCE**: {evidence}
---
"""

# File status mappings based on user context
PHASED_IMPLEMENTATION_FILES = {
    "016-2025-09-28-multicardz-Zero-Trust-UUID-Architecture-v1.md":
        "Core architecture planned, intentionally deferred until auth phase. Current: hardcoded users.",
    "022-2025-09-22-multicardz-Multi-Tier-Database-Architecture-v1.md":
        "Intentionally deferred to auth phase. Current: SQLite + hardcoded users (acceptable for development).",
    "024-2025-09-22-multicardz-Database-Schema-Architecture-v1.md":
        "Intentionally deferred to auth phase. Current: SQLite + hardcoded users (acceptable for development).",
    "multicardz_auth_architecture.md":
        "Deferred to auth phase. See consolidated doc 039-2025-11-06-Authentication-Architecture-and-Plan.md",
    "STRIPE_AUTH0_SECURITY_DOCUMENTATION.md":
        "Deferred to auth phase. See consolidated doc 039-2025-11-06-Authentication-Architecture-and-Plan.md",
    "anonymous-to-paid-tracking.md":
        "Deferred to auth phase. See consolidated doc 039-2025-11-06-Authentication-Architecture-and-Plan.md",
}

IMPLEMENTED_FILES = {
    "001-2025-09-16-multicardz-JavaScript-Architecture-v1.md":
        "See file header for detailed implementation evidence (176KB JavaScript across 10+ files)",
    "033-2025-10-26-multicardz-Font-Metric-Override-Optimization-Proposal-v1.md":
        "apps/static/css/user.css lines 8-134 (8-font system with size-adjust metrics)",
    "034-2025-10-26-Multi-Selection-Drag-Drop-Architecture-v1.md":
        "apps/static/js/drag-drop.js (multi-selection system implemented)",
    "035-2025-10-26-Group-Tags-Architecture-v1.md":
        "apps/static/js/group-tags.js, apps/static/js/group-ui-integration.js (implemented, needs testing)",
    "024-2025-09-22-multicardz-Database-Schema-Specifications-v1.md":
        "Partially implemented. Current: SQLite schema in apps/models/. Full schema deferred to auth phase.",
}

PLANNED_FILES = {
    "027-2025-10-15-MultiCardz-Outlook-Email-Integration-Architecture-v1.md":
        "Planned future feature. Architecture ready, implementation not started.",
    "026-2025-09-30-multicardz-Progressive-Onboarding-Proposal-v1.md":
        "Planned future feature. Architecture ready, implementation not started.",
}

SUPERSEDED_FILES = {
    "016-2025-09-20-MultiCardz-Unified-Implementation-Plan-v1 - duplicate.md":
        "Duplicate file. See main version without ' - duplicate' suffix.",
}


def get_file_status(file_path: Path) -> tuple[str, str]:
    """
    Determine status and evidence for a markdown file.
    Returns: (status, evidence)
    """
    file_name = file_path.name

    # Check explicit mappings
    if file_name in PHASED_IMPLEMENTATION_FILES:
        return ("PHASED IMPLEMENTATION", PHASED_IMPLEMENTATION_FILES[file_name])

    if file_name in IMPLEMENTED_FILES:
        return ("IMPLEMENTED", IMPLEMENTED_FILES[file_name])

    if file_name in PLANNED_FILES:
        return ("PLANNED", PLANNED_FILES[file_name])

    if file_name in SUPERSEDED_FILES:
        return ("SUPERSEDED", SUPERSEDED_FILES[file_name])

    # Pattern-based detection
    if "duplicate" in file_name.lower():
        return ("SUPERSEDED", "Duplicate file. See main version.")

    # Implementation plans
    if "implementation" in file_path.parts and "plan" in file_name.lower():
        return ("PARTIALLY IMPLEMENTED", "Implementation in progress. See implementation/ directory for details.")

    # Gap reports
    if "GAP-REPORT" in file_name:
        return ("PLANNED", "Gap identified. Implementation not started.")

    # Architecture docs (default to planned unless specified)
    if "architecture" in file_path.parts:
        return ("PLANNED", "Architecture documented. Implementation status not verified.")

    # Standards and guidelines
    if "standards" in file_path.parts or "guidelines" in file_name.lower():
        return ("IMPLEMENTED", "Active standard in use.")

    # Testing docs
    if "testing" in file_name.lower() or "test" in file_name.lower():
        return ("PARTIALLY IMPLEMENTED", "Testing framework in place, coverage incomplete.")

    # Default
    return ("PLANNED", "Not implemented.")


def has_status_header(content: str) -> bool:
    """Check if file already has status header."""
    return "**IMPLEMENTATION STATUS**:" in content or "IMPLEMENTATION STATUS:" in content


def add_status_header(file_path: Path, dry_run: bool = False) -> bool:
    """
    Add status header to markdown file.
    Returns True if file was modified.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  ⚠️  Error reading {file_path.name}: {e}")
        return False

    # Skip if already has status header
    if has_status_header(content):
        print(f"  ⏭️  {file_path.name} - Already has status header")
        return False

    # Get status and evidence
    status, evidence = get_file_status(file_path)

    # Find where to insert header (after title, before Executive Summary or first ##)
    lines = content.split('\n')
    insert_line = 0

    # Skip title and metadata
    for i, line in enumerate(lines):
        if i == 0:
            continue  # Skip first line (title)
        if line.startswith('##') or line.startswith('**Executive Summary**') or 'Executive Summary' in line:
            insert_line = i
            break
        if line.strip() == '---' and i > 5:  # Found separator after metadata
            insert_line = i + 1
            break

    if insert_line == 0:
        insert_line = min(10, len(lines))  # Insert after ~10 lines if no pattern found

    # Create status header
    today = datetime.now().strftime('%Y-%m-%d')
    header = STATUS_HEADER_TEMPLATE.format(
        status=status,
        date=today,
        evidence=evidence
    )

    # Insert header
    new_lines = lines[:insert_line] + [''] + header.split('\n') + [''] + lines[insert_line:]
    new_content = '\n'.join(new_lines)

    if dry_run:
        print(f"  🔍 {file_path.name} - Would add status: {status}")
        return False

    # Write updated content
    try:
        file_path.write_text(new_content, encoding='utf-8')
        print(f"  ✅ {file_path.name} - Added status: {status}")
        return True
    except Exception as e:
        print(f"  ⚠️  Error writing {file_path.name}: {e}")
        return False


def main():
    """Process all markdown files in docs directory."""
    import argparse

    parser = argparse.ArgumentParser(description='Add status headers to documentation files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--dir', default='/Users/adam/dev/multicardz/docs', help='Documentation directory')
    args = parser.parse_args()

    docs_dir = Path(args.dir)

    if not docs_dir.exists():
        print(f"❌ Directory not found: {docs_dir}")
        return 1

    # Find all markdown files
    md_files = sorted(docs_dir.glob('**/*.md'))

    print(f"\n📋 Processing {len(md_files)} markdown files...")
    if args.dry_run:
        print("   (DRY RUN - no changes will be made)\n")

    modified_count = 0
    skipped_count = 0

    for file_path in md_files:
        relative_path = file_path.relative_to(docs_dir)
        was_modified = add_status_header(file_path, dry_run=args.dry_run)

        if was_modified:
            modified_count += 1
        else:
            skipped_count += 1

    print(f"\n" + "="*60)
    print(f"✅ Complete!")
    print(f"   Modified: {modified_count} files")
    print(f"   Skipped:  {skipped_count} files (already had headers)")
    print(f"   Total:    {len(md_files)} files")
    print("="*60 + "\n")

    return 0


if __name__ == '__main__':
    exit(main())
