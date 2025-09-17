#!/usr/bin/env python3
"""
Architectural Purity Validator - No Classes

Enforces the architectural principle that NO classes should be used except:
- Pydantic models (BaseModel subclasses)
- SQLAlchemy models
- Test fixtures and pytest classes
- Required external library classes

This prevents object-oriented patterns that violate our function-first architecture.
"""

import ast
import sys
from pathlib import Path


class ClassVisitor(ast.NodeVisitor):
    """AST visitor to find class definitions."""

    def __init__(self):
        self.classes: list[tuple] = []
        self.imports: set[str] = set()

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
        # Check if class inherits from allowed base classes
        allowed_bases = {
            "BaseModel",  # Pydantic
            "Model",  # SQLAlchemy
            "TestCase",  # unittest
            "pytest.Class",  # pytest
            "Protocol",  # typing protocols
            "TypedDict",  # typed dictionaries
            "Enum",  # enums
            "IntEnum",  # int enums
            "Exception",  # custom exceptions
        }

        base_names = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_names.append(
                    f"{base.value.id if isinstance(base.value, ast.Name) else 'unknown'}.{base.attr}"
                )

        # Check if any base class is allowed
        is_allowed = False
        for base_name in base_names:
            if base_name in allowed_bases:
                is_allowed = True
                break
            # Check if it's a Pydantic model based on imports
            if "pydantic" in self.imports and base_name == "BaseModel":
                is_allowed = True
                break

        # Also allow if no base classes (but this is suspicious)
        if not base_names:
            # Empty classes are suspicious unless they're exceptions or protocols
            if not (
                node.name.endswith("Error")
                or node.name.endswith("Exception")
                or any(
                    "Protocol" in str(decorator.id)
                    if hasattr(decorator, "id")
                    else False
                    for decorator in node.decorator_list
                )
            ):
                self.classes.append(
                    (node.lineno, node.name, "plain class without inheritance")
                )
        elif not is_allowed:
            self.classes.append(
                (node.lineno, node.name, f"inherits from {', '.join(base_names)}")
            )

        self.generic_visit(node)


def validate_file(file_path: Path) -> list[str]:
    """Validate a single Python file for unauthorized classes."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        visitor = ClassVisitor()
        visitor.visit(tree)

        violations = []
        for line_no, class_name, reason in visitor.classes:
            violations.append(
                f"{file_path}:{line_no}: Unauthorized class '{class_name}' - {reason}\n"
                f"  Architecture violation: Use functions instead of classes for business logic"
            )

        return violations

    except SyntaxError as e:
        return [f"{file_path}:{e.lineno}: Syntax error: {e.msg}"]
    except Exception as e:
        return [f"{file_path}: Error parsing file: {e}"]


def main():
    """Main validator function called by pre-commit."""
    if len(sys.argv) < 2:
        print("Usage: validate_no_classes.py <file1> [file2] ...")
        return 1

    all_violations = []

    for file_path in sys.argv[1:]:
        path = Path(file_path)
        if path.suffix == ".py":
            violations = validate_file(path)
            all_violations.extend(violations)

    if all_violations:
        print("🚫 ARCHITECTURAL PURITY VIOLATION: Unauthorized Classes Found")
        print("=" * 60)
        print()
        for violation in all_violations:
            print(violation)
            print()

        print("ARCHITECTURAL GUIDANCE:")
        print("• Use pure functions instead of classes for business logic")
        print("• Classes are ONLY allowed for:")
        print("  - Pydantic models (data validation)")
        print("  - SQLAlchemy models (database mapping)")
        print("  - Test fixtures and pytest classes")
        print("  - Required external library patterns")
        print("• Move business logic to separate function modules")
        print("• Use dependency injection instead of class instantiation")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
