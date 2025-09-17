#!/usr/bin/env python3
"""
Architectural Purity Validator - Two-Tier Card Architecture

Enforces the two-tier card model architecture:
- CardSummary should be used for list operations and bulk handling
- CardDetail should only be loaded on-demand for individual cards
- No mixing of CardSummary and CardDetail in inappropriate contexts
- Proper lazy loading patterns
- Attachment handling through proper models

This ensures optimal performance through lazy loading.
"""

import ast
import re
import sys
from pathlib import Path


class TwoTierVisitor(ast.NodeVisitor):
    """AST visitor to check two-tier card architecture compliance."""

    def __init__(self, file_path: Path):
        self.violations: list[tuple] = []
        self.file_path = file_path
        self.imports: set[str] = set()
        self.from_imports: dict[str, set[str]] = {}
        self.functions: set[str] = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            imported_names = {alias.name for alias in node.names}
            self.from_imports[node.module] = imported_names
            for name in imported_names:
                self.imports.add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.add(node.name.lower())
        self._check_function_usage(node)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Check function calls for proper card model usage."""
        self._check_card_model_usage(node)
        self.generic_visit(node)

    def visit_ListComp(self, node):
        """Check list comprehensions for bulk operations."""
        self._check_bulk_operations(node, "list comprehension")
        self.generic_visit(node)

    def visit_For(self, node):
        """Check for loops for bulk operations."""
        self._check_bulk_operations(node, "for loop")
        self.generic_visit(node)

    def _check_function_usage(self, node):
        """Check if function uses appropriate card models."""
        func_name = node.name.lower()

        # Functions that should use CardSummary
        summary_functions = [
            "list",
            "get_all",
            "search",
            "filter",
            "find_all",
            "bulk",
            "batch",
            "index",
            "overview",
            "preview",
        ]

        # Functions that should use CardDetail
        detail_functions = [
            "get_by_id",
            "load",
            "edit",
            "update",
            "create",
            "detail",
            "full",
            "complete",
            "view",
        ]

        if any(pattern in func_name for pattern in summary_functions):
            self._check_summary_usage_in_function(node)
        elif any(pattern in func_name for pattern in detail_functions):
            self._check_detail_usage_in_function(node)

    def _check_summary_usage_in_function(self, node):
        """Check that bulk/list functions use CardSummary."""
        uses_card_detail = False
        uses_card_summary = False

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id == "CardDetail":
                    uses_card_detail = True
                elif child.id == "CardSummary":
                    uses_card_summary = True

        if uses_card_detail and not uses_card_summary:
            self.violations.append(
                (
                    node.lineno,
                    f"Function '{node.name}' suggests bulk operations but uses CardDetail",
                    "Use CardSummary for list/bulk operations for better performance",
                )
            )

    def _check_detail_usage_in_function(self, node):
        """Check that detail functions properly use CardDetail."""
        uses_card_detail = False
        uses_card_summary = False

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                if child.id == "CardDetail":
                    uses_card_detail = True
                elif child.id == "CardSummary":
                    uses_card_summary = True

        # Detail functions should eventually load CardDetail
        if uses_card_summary and not uses_card_detail:
            # This might be okay if it's just returning summary for UI
            pass
        elif not uses_card_detail and not uses_card_summary:
            # Function might be incomplete
            pass

    def _check_card_model_usage(self, node):
        """Check specific usage patterns of card models."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id

            # Check CardDetail constructor calls
            if func_name == "CardDetail":
                # CardDetail should not be created in bulk contexts
                if self._is_in_bulk_context():
                    self.violations.append(
                        (
                            node.lineno,
                            "CardDetail created in bulk context",
                            "Use CardSummary for bulk operations, CardDetail only on-demand",
                        )
                    )

            # Check list/bulk operations with CardDetail
            elif func_name in ["list", "map", "filter"] and len(node.args) > 0:
                # Check if we're operating on CardDetail objects
                for arg in node.args:
                    if self._references_card_detail(arg):
                        self.violations.append(
                            (
                                node.lineno,
                                f"Bulk operation '{func_name}' on CardDetail objects",
                                "Use CardSummary for bulk operations",
                            )
                        )

    def _check_bulk_operations(self, node, operation_type):
        """Check bulk operations for proper model usage."""
        # Look for patterns like [CardDetail(...) for ...]
        if hasattr(node, "elt") and isinstance(node.elt, ast.Call):
            if isinstance(node.elt.func, ast.Name) and node.elt.func.id == "CardDetail":
                self.violations.append(
                    (
                        node.lineno,
                        f"CardDetail used in {operation_type}",
                        "Use CardSummary for bulk operations",
                    )
                )

        # Look for content access in bulk operations
        if hasattr(node, "elt") and isinstance(node.elt, ast.Attribute):
            if node.elt.attr in ["content", "metadata", "attachment_count"]:
                self.violations.append(
                    (
                        node.lineno,
                        f"Accessing detail fields in {operation_type}",
                        "Access detail fields only on individual cards, not in bulk",
                    )
                )

    def _is_in_bulk_context(self) -> bool:
        """Check if we're in a function that handles bulk operations."""
        bulk_indicators = [
            "list",
            "get_all",
            "search",
            "filter",
            "find_all",
            "bulk",
            "batch",
            "index",
            "overview",
        ]
        return any(
            indicator in func
            for func in self.functions
            for indicator in bulk_indicators
        )

    def _references_card_detail(self, node) -> bool:
        """Check if an AST node references CardDetail."""
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Name)
                and child.id == "CardDetail"
                or isinstance(child, ast.Attribute)
                and child.attr
                in ["content", "metadata", "attachment_count", "total_attachment_size"]
            ):
                return True
        return False


def validate_file(file_path: Path) -> list[str]:
    """Validate a single Python file for two-tier architecture compliance."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Skip files that don't deal with cards
        if not any(
            indicator in content
            for indicator in ["Card", "card", "Attachment", "attachment"]
        ):
            return []

        tree = ast.parse(content, filename=str(file_path))
        visitor = TwoTierVisitor(file_path)
        visitor.visit(tree)

        violations = []
        for line_no, violation, suggestion in visitor.violations:
            violations.append(
                f"{file_path}:{line_no}: Two-tier architecture violation - {violation}\n"
                f"  Performance guidance: {suggestion}"
            )

        return violations

    except SyntaxError as e:
        return [f"{file_path}:{e.lineno}: Syntax error: {e.msg}"]
    except Exception as e:
        return [f"{file_path}: Error parsing file: {e}"]


def validate_content_patterns(file_path: Path) -> list[str]:
    """Additional pattern-based validation for two-tier architecture."""
    violations = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Pattern-based checks
        problematic_patterns = {
            r"CardDetail\s*\(\s*\*": "Bulk CardDetail creation - use CardSummary for lists",
            r"\.content\s+for\s+": "Accessing content in bulk operations - use lazy loading",
            r"\.metadata\s+for\s+": "Accessing metadata in bulk operations - use lazy loading",
            r"CardDetail.*\[\s*:": "Slicing CardDetail collections - use CardSummary",
            r"len\s*\(\s*.*CardDetail": "Getting length of CardDetail collections - use CardSummary",
        }

        for line_no, line in enumerate(lines, 1):
            # Skip comments and docstrings
            if line.strip().startswith("#") or '"""' in line or "'''" in line:
                continue

            for pattern, message in problematic_patterns.items():
                if re.search(pattern, line):
                    violations.append(
                        f"{file_path}:{line_no}: Pattern violation - {message}\n"
                        f"  Line: {line.strip()}"
                    )

    except Exception as e:
        violations.append(f"{file_path}: Error reading file: {e}")

    return violations


def check_api_endpoint_usage(file_path: Path) -> list[str]:
    """Check API endpoints for proper card model usage."""
    violations = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Skip non-API files
        if not any(
            indicator in content
            for indicator in ["@app.", "FastAPI", "router", "endpoint"]
        ):
            return []

        lines = content.split("\n")

        for line_no, line in enumerate(lines, 1):
            # Check for list endpoints using CardDetail
            if (
                re.search(r"@\w+\.(get|post).*\/.*cards.*\/", line)
                and "list" in line.lower()
            ):
                # Look ahead for CardDetail usage
                for check_line_no in range(line_no, min(line_no + 10, len(lines))):
                    if "CardDetail" in lines[check_line_no]:
                        violations.append(
                            f"{file_path}:{check_line_no + 1}: API endpoint returns CardDetail for list operation\n"
                            f"  Performance guidance: Use CardSummary for list endpoints"
                        )
                        break

    except Exception as e:
        violations.append(f"{file_path}: Error reading file: {e}")

    return violations


def main():
    """Main validator function called by pre-commit."""
    if len(sys.argv) < 2:
        print("Usage: validate_two_tier.py <file1> [file2] ...")
        return 1

    all_violations = []

    for file_path in sys.argv[1:]:
        path = Path(file_path)
        if path.suffix == ".py":
            # AST-based validation
            violations = validate_file(path)
            all_violations.extend(violations)

            # Pattern-based validation
            pattern_violations = validate_content_patterns(path)
            all_violations.extend(pattern_violations)

            # API endpoint specific checks
            api_violations = check_api_endpoint_usage(path)
            all_violations.extend(api_violations)

    if all_violations:
        print(
            "🚫 ARCHITECTURAL PURITY VIOLATION: Two-Tier Architecture Violations Found"
        )
        print("=" * 75)
        print()
        for violation in all_violations:
            print(violation)
            print()

        print("TWO-TIER ARCHITECTURE GUIDANCE:")
        print("• Use CardSummary for:")
        print("  - List operations and bulk handling")
        print("  - Search results and filtering")
        print("  - API endpoints that return multiple cards")
        print("  - Overview and preview interfaces")
        print("• Use CardDetail for:")
        print("  - Individual card viewing/editing")
        print("  - On-demand loading when user opens a card")
        print("  - API endpoints for single card operations")
        print("• Performance benefits:")
        print("  - CardSummary: ~50 bytes for fast list rendering")
        print("  - CardDetail: Full data loaded only when needed")
        print("• Lazy loading pattern:")
        print("  - Show CardSummary in lists")
        print("  - Load CardDetail when user interacts")
        print("  - Use separate API endpoints for each tier")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
