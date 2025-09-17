#!/usr/bin/env python3
"""
Architectural Purity Validator - Immutability

Enforces immutability principles throughout the codebase:
- All Pydantic models must have frozen=True
- No mutable default arguments
- frozenset usage for collections in models
- No global mutable state
- Function parameters should not be mutated

This ensures data integrity and enables horizontal scaling.
"""

import ast
import re
import sys
from pathlib import Path


class ImmutabilityVisitor(ast.NodeVisitor):
    """AST visitor to find immutability violations."""

    def __init__(self):
        self.violations: list[tuple] = []
        self.class_names: set[str] = set()
        self.imports: set[str] = set()
        self.current_class = None

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.class_names.add(node.name)

        # Check if it's a Pydantic model
        is_pydantic_model = any(
            isinstance(base, ast.Name) and base.id == "BaseModel" for base in node.bases
        )

        if is_pydantic_model:
            self._check_pydantic_model(node)

        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        # Check for mutable default arguments
        for default in node.args.defaults:
            if self._is_mutable_default(default):
                self.violations.append(
                    (
                        default.lineno,
                        f"Mutable default argument in function '{node.name}'",
                        "Use None and initialize inside function, or use immutable types",
                    )
                )

        # Check for parameter mutation
        self._check_parameter_mutation(node)

        self.generic_visit(node)

    def visit_Assign(self, node):
        # Check for global mutable state
        if self.current_class is None:  # Global scope
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if self._is_mutable_assignment(node.value):
                        self.violations.append(
                            (
                                node.lineno,
                                f"Global mutable state assignment: {target.id}",
                                "Use immutable types or move to function scope",
                            )
                        )

        self.generic_visit(node)

    def _check_pydantic_model(self, node):
        """Check Pydantic model for immutability requirements."""
        has_frozen_config = False
        has_model_config = False

        for item in node.body:
            # Check for model_config
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "model_config":
                        has_model_config = True
                        if isinstance(item.value, ast.Dict):
                            for key, value in zip(
                                item.value.keys, item.value.values, strict=False
                            ):
                                if (
                                    isinstance(key, ast.Constant)
                                    and key.value == "frozen"
                                    and isinstance(value, ast.Constant)
                                    and value.value is True
                                ):
                                    has_frozen_config = True

            # Check field definitions for frozenset usage
            elif isinstance(item, ast.AnnAssign):
                if item.target and isinstance(item.target, ast.Name):
                    field_name = item.target.id
                    if item.annotation:
                        # Check if it's a collection that should be frozenset
                        if self._should_use_frozenset(item.annotation):
                            self.violations.append(
                                (
                                    item.lineno,
                                    f"Field '{field_name}' should use FrozenSet for immutability",
                                    "Replace List/Set with FrozenSet for model fields",
                                )
                            )

        if has_model_config and not has_frozen_config:
            self.violations.append(
                (
                    node.lineno,
                    f"Pydantic model '{node.name}' missing frozen=True in model_config",
                    "Add 'frozen': True to model_config for immutability",
                )
            )
        elif not has_model_config:
            self.violations.append(
                (
                    node.lineno,
                    f"Pydantic model '{node.name}' missing model_config with frozen=True",
                    "Add model_config = {'frozen': True} for immutability",
                )
            )

    def _is_mutable_default(self, node) -> bool:
        """Check if a default argument is mutable."""
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # Common mutable constructors
                mutable_constructors = {"list", "dict", "set", "defaultdict", "Counter"}
                return node.func.id in mutable_constructors
        return False

    def _is_mutable_assignment(self, node) -> bool:
        """Check if an assignment creates mutable state."""
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                mutable_constructors = {"list", "dict", "set", "defaultdict", "Counter"}
                return node.func.id in mutable_constructors
        return False

    def _should_use_frozenset(self, annotation) -> bool:
        """Check if annotation should use FrozenSet instead of List/Set."""
        if isinstance(annotation, ast.Subscript):
            if isinstance(annotation.value, ast.Name):
                return annotation.value.id in ["List", "Set"]
        elif isinstance(annotation, ast.Name):
            return annotation.id in ["list", "set"]
        return False

    def _check_parameter_mutation(self, node):
        """Check for parameter mutation within function."""
        param_names = {arg.arg for arg in node.args.args}

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id in param_names:
                        self.violations.append(
                            (
                                child.lineno,
                                f"Parameter '{target.id}' mutation in function '{node.name}'",
                                "Create new variables instead of mutating parameters",
                            )
                        )
            elif isinstance(child, ast.Call):
                # Check for mutating methods called on parameters
                if isinstance(child.func, ast.Attribute):
                    if (
                        isinstance(child.func.value, ast.Name)
                        and child.func.value.id in param_names
                    ):
                        mutating_methods = {
                            "append",
                            "extend",
                            "insert",
                            "remove",
                            "pop",
                            "clear",
                            "sort",
                            "reverse",
                            "update",
                            "add",
                            "discard",
                        }
                        if child.func.attr in mutating_methods:
                            self.violations.append(
                                (
                                    child.lineno,
                                    f"Mutating method '{child.func.attr}' called on parameter '{child.func.value.id}'",
                                    "Create a copy before mutation or use immutable operations",
                                )
                            )


def validate_file(file_path: Path) -> list[str]:
    """Validate a single Python file for immutability violations."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        visitor = ImmutabilityVisitor()
        visitor.visit(tree)

        violations = []
        for line_no, violation, suggestion in visitor.violations:
            violations.append(
                f"{file_path}:{line_no}: Immutability violation - {violation}\n"
                f"  Architectural guidance: {suggestion}"
            )

        return violations

    except SyntaxError as e:
        return [f"{file_path}:{e.lineno}: Syntax error: {e.msg}"]
    except Exception as e:
        return [f"{file_path}: Error parsing file: {e}"]


def validate_content_patterns(file_path: Path) -> list[str]:
    """Additional pattern-based validation for immutability."""
    violations = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Pattern-based checks
        problematic_patterns = {
            r"global\s+\w+": "Global variables discouraged - use function parameters",
            r"\.append\s*\(": "Mutable list operations - consider using immutable patterns",
            r"\.extend\s*\(": "Mutable list operations - consider using immutable patterns",
            r"\.update\s*\(": "Mutable dict operations - consider using immutable patterns",
            r"\.pop\s*\(": "Mutable operations - consider using immutable patterns",
            r"\.remove\s*\(": "Mutable operations - consider using immutable patterns",
            r"del\s+\w+\[": "Mutable deletion - consider using immutable patterns",
        }

        for line_no, line in enumerate(lines, 1):
            # Skip comments and docstrings
            if line.strip().startswith("#") or '"""' in line or "'''" in line:
                continue

            for pattern, message in problematic_patterns.items():
                if re.search(pattern, line):
                    violations.append(
                        f"{file_path}:{line_no}: Mutability pattern - {message}\n"
                        f"  Line: {line.strip()}"
                    )

    except Exception as e:
        violations.append(f"{file_path}: Error reading file: {e}")

    return violations


def main():
    """Main validator function called by pre-commit."""
    if len(sys.argv) < 2:
        print("Usage: validate_immutability.py <file1> [file2] ...")
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
        print("🚫 ARCHITECTURAL PURITY VIOLATION: Immutability Violations Found")
        print("=" * 65)
        print()
        for violation in all_violations:
            print(violation)
            print()

        print("IMMUTABILITY ARCHITECTURAL GUIDANCE:")
        print("• ALL Pydantic models MUST have frozen=True in model_config")
        print("• Use FrozenSet instead of List/Set for model collections")
        print(
            "• NO mutable default arguments - use None and initialize inside function"
        )
        print("• NO global mutable state - use function parameters")
        print("• NO parameter mutation - create new variables")
        print("• Preferred patterns:")
        print("  - frozenset() for immutable collections")
        print("  - tuple() for ordered immutable sequences")
        print("  - New objects instead of in-place modifications")
        print("  - Functional composition over mutation")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
