#!/usr/bin/env python3
"""
Architectural Purity Validator - Set Theory Operations

Enforces the patent-compliant architectural principle that ALL filtering and query
operations MUST use pure set theory operations (union, intersection, difference, complement).

This prevents the use of lists, dictionaries, or other data structures for core
filtering logic, ensuring patent compliance and mathematical soundness.
"""

import ast
import re
import sys
from pathlib import Path


class FilteringVisitor(ast.NodeVisitor):
    """AST visitor to find filtering operations that should use set theory."""

    def __init__(self):
        self.violations: list[tuple] = []
        self.has_set_imports = False
        self.function_names: set[str] = set()

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ["sets", "frozenset", "set"]:
                self.has_set_imports = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and "set" in node.module.lower():
            self.has_set_imports = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.function_names.add(node.name.lower())
        # Check function names that suggest filtering
        filtering_patterns = [
            "filter",
            "search",
            "query",
            "find",
            "select",
            "match",
            "get_by",
            "find_by",
            "search_by",
            "filter_by",
        ]

        if any(pattern in node.name.lower() for pattern in filtering_patterns):
            # Analyze function body for set operations
            self._check_function_body(node)

        self.generic_visit(node)

    def visit_ListComp(self, node):
        """Check list comprehensions that might be filtering operations."""
        # Look for comprehensions in filtering contexts
        if self._is_in_filtering_context():
            self.violations.append(
                (
                    node.lineno,
                    "List comprehension used for filtering",
                    "Use set operations like intersection() or union() instead",
                )
            )
        self.generic_visit(node)

    def visit_DictComp(self, node):
        """Check dictionary comprehensions in filtering contexts."""
        if self._is_in_filtering_context():
            self.violations.append(
                (
                    node.lineno,
                    "Dictionary comprehension used for filtering",
                    "Use set operations with appropriate data structures",
                )
            )
        self.generic_visit(node)

    def visit_Call(self, node):
        """Check function calls for non-set filtering operations."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id.lower()

            # Check for prohibited filtering functions
            prohibited_functions = {
                "filter": "Use set intersection instead of filter()",
                "map": "Use set operations instead of map() for filtering",
                "reduce": "Use set operations instead of reduce() for filtering",
            }

            if func_name in prohibited_functions and self._is_in_filtering_context():
                self.violations.append(
                    (
                        node.lineno,
                        f"Prohibited function '{func_name}' used for filtering",
                        prohibited_functions[func_name],
                    )
                )

        # Check for pandas/numpy operations in filtering contexts
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr.lower()
            filtering_methods = ["query", "filter", "select", "where", "isin"]

            if attr_name in filtering_methods and self._is_in_filtering_context():
                self.violations.append(
                    (
                        node.lineno,
                        f"DataFrame/array method '{attr_name}' used for filtering",
                        "Use Python set operations for tag filtering instead",
                    )
                )

        self.generic_visit(node)

    def _check_function_body(self, node):
        """Check if function body uses appropriate set operations."""
        has_set_operations = False

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    method_name = child.func.attr
                    if method_name in [
                        "intersection",
                        "union",
                        "difference",
                        "symmetric_difference",
                    ]:
                        has_set_operations = True
                        break
                elif isinstance(child.func, ast.Name):
                    func_name = child.func.id
                    if func_name in ["frozenset", "set"]:
                        has_set_operations = True

        # If it's a filtering function but doesn't use set operations, flag it
        if not has_set_operations:
            self.violations.append(
                (
                    node.lineno,
                    f"Filtering function '{node.name}' doesn't use set operations",
                    "Implement using frozenset.intersection(), union(), or difference()",
                )
            )

    def _is_in_filtering_context(self) -> bool:
        """Determine if we're in a filtering context based on function names."""
        filtering_keywords = [
            "filter",
            "search",
            "query",
            "find",
            "select",
            "match",
            "tag",
            "card",
            "workspace",
        ]
        return any(
            keyword in name
            for name in self.function_names
            for keyword in filtering_keywords
        )


def validate_file(file_path: Path) -> list[str]:
    """Validate a single Python file for set theory compliance."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Skip files that don't contain filtering-related code
        filtering_indicators = [
            "filter",
            "search",
            "query",
            "find",
            "select",
            "match",
            "tag",
            "card",
            "workspace",
            "intersection",
            "union",
        ]

        if not any(indicator in content.lower() for indicator in filtering_indicators):
            return []

        tree = ast.parse(content, filename=str(file_path))
        visitor = FilteringVisitor()
        visitor.visit(tree)

        violations = []
        for line_no, violation, suggestion in visitor.violations:
            violations.append(
                f"{file_path}:{line_no}: Set theory violation - {violation}\n"
                f"  Patent compliance requirement: {suggestion}"
            )

        return violations

    except SyntaxError as e:
        return [f"{file_path}:{e.lineno}: Syntax error: {e.msg}"]
    except Exception as e:
        return [f"{file_path}: Error parsing file: {e}"]


def validate_content_patterns(file_path: Path) -> list[str]:
    """Additional pattern-based validation for set theory compliance."""
    violations = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Pattern-based checks
        problematic_patterns = {
            r"\.query\s*\(": "Use set operations instead of .query()",
            r"\.filter\s*\(": "Use set operations instead of .filter()",
            r"\[.*for.*in.*if.*\]": "Use set comprehensions instead of list comprehensions for filtering",
            r"pandas\.": "Avoid pandas for tag operations - use Python sets",
            r"numpy\.": "Avoid numpy for tag operations - use Python sets",
            r"\.isin\s*\(": "Use set intersection instead of .isin()",
        }

        for line_no, line in enumerate(lines, 1):
            # Skip comments and docstrings
            if line.strip().startswith("#") or '"""' in line or "'''" in line:
                continue

            for pattern, message in problematic_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(
                        f"{file_path}:{line_no}: Pattern violation - {message}\n"
                        f"  Line: {line.strip()}"
                    )

    except Exception as e:
        violations.append(f"{file_path}: Error reading file: {e}")

    return violations


def main():
    """Main validator function called by pre-commit."""
    if len(sys.argv) < 2:
        print("Usage: validate_set_theory.py <file1> [file2] ...")
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

    if all_violations:
        print("🚫 PATENT COMPLIANCE VIOLATION: Non-Set Theory Operations Found")
        print("=" * 70)
        print()
        for violation in all_violations:
            print(violation)
            print()

        print("PATENT COMPLIANCE GUIDANCE:")
        print("• ALL filtering operations MUST use pure set theory")
        print("• Allowed operations:")
        print("  - frozenset.intersection() for AND operations")
        print("  - frozenset.union() for OR operations")
        print("  - frozenset.difference() for NOT operations")
        print("  - frozenset.symmetric_difference() for XOR operations")
        print("• Prohibited:")
        print("  - List comprehensions for filtering")
        print("  - Dictionary lookups for tag operations")
        print("  - Pandas/numpy for tag filtering")
        print("  - filter(), map(), reduce() functions")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
