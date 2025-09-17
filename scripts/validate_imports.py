#!/usr/bin/env python3
"""
Architectural Purity Validator - Import Control

Enforces strict control over dependencies and imports:
- Only approved packages can be imported
- No circular imports between apps
- Models can only be imported in specific contexts
- No unauthorized external dependencies
- Prevents architectural violations through dependency analysis

This maintains clean architecture boundaries and prevents scope creep.
"""

import ast
import sys
from pathlib import Path


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to analyze imports."""

    def __init__(self, file_path: Path):
        self.violations: list[tuple] = []
        self.file_path = file_path
        self.imports: set[str] = set()
        self.from_imports: dict[str, set[str]] = {}

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name
            self.imports.add(module_name)
            self._check_import(node.lineno, module_name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module_name = node.module
            imported_names = {alias.name for alias in node.names}

            if module_name not in self.from_imports:
                self.from_imports[module_name] = set()
            self.from_imports[module_name].update(imported_names)

            self._check_from_import(node.lineno, module_name, imported_names)

        self.generic_visit(node)

    def _check_import(self, line_no: int, module_name: str):
        """Check if a direct import is allowed."""
        # Split module name to get top-level package
        top_level = module_name.split(".")[0]

        # Approved packages
        approved_packages = {
            # Standard library - always allowed
            "os",
            "sys",
            "pathlib",
            "typing",
            "datetime",
            "uuid",
            "json",
            "collections",
            "itertools",
            "functools",
            "operator",
            "math",
            "random",
            "hashlib",
            "hmac",
            "base64",
            "urllib",
            "http",
            # Core dependencies
            "pydantic",
            "fastapi",
            "uvicorn",
            "jinja2",
            "starlette",
            "httpx",
            "requests",
            # Database
            "sqlalchemy",
            "alembic",
            "sqlite3",
            # Testing
            "pytest",
            "hypothesis",
            "pytest_bdd",
            # Development tools
            "ruff",
            "mypy",
            "coverage",
            # Architecture-approved packages
            "granian",  # ASGI server
            "atlas",  # DB migrations
        }

        # Prohibited packages that violate architecture
        prohibited_packages = {
            "django": "Django prohibited - use FastAPI",
            "flask": "Flask prohibited - use FastAPI",
            "tornado": "Tornado prohibited - use FastAPI",
            "react": "React prohibited - use Web Components",
            "vue": "Vue prohibited - use Web Components",
            "angular": "Angular prohibited - use Web Components",
            "jquery": "jQuery prohibited - use Web Components",
            "numpy": "NumPy prohibited for tag operations - use Python sets",
            "pandas": "Pandas prohibited for tag operations - use Python sets",
            "redis": "Redis prohibited - use SQLite for simplicity",
            "mongodb": "MongoDB prohibited - use SQLite",
            "postgresql": "PostgreSQL prohibited - use SQLite for portability",
            "mysql": "MySQL prohibited - use SQLite for portability",
            "celery": "Celery prohibited - use simple background tasks",
            "tensorflow": "TensorFlow prohibited - keep architecture simple",
            "torch": "PyTorch prohibited - keep architecture simple",
            "keras": "Keras prohibited - keep architecture simple",
        }

        if top_level in prohibited_packages:
            self.violations.append(
                (
                    line_no,
                    f"Prohibited package import: {module_name}",
                    prohibited_packages[top_level],
                )
            )
        elif top_level not in approved_packages and not self._is_local_import(
            module_name
        ):
            self.violations.append(
                (
                    line_no,
                    f"Unapproved package import: {module_name}",
                    "Add to approved packages list or find alternative",
                )
            )

    def _check_from_import(
        self, line_no: int, module_name: str, imported_names: set[str]
    ):
        """Check if a from-import is allowed."""
        # Check the module itself
        self._check_import(line_no, module_name)

        # Additional checks for specific import patterns
        if module_name.startswith("apps."):
            self._check_cross_app_imports(line_no, module_name, imported_names)

        # Check for model imports in inappropriate contexts
        if any("models" in module_name.split(".") for name in imported_names):
            self._check_model_import_context(line_no, module_name, imported_names)

    def _check_cross_app_imports(
        self, line_no: int, module_name: str, imported_names: set[str]
    ):
        """Check for inappropriate cross-app imports."""
        current_app = self._get_current_app()
        imported_app = (
            module_name.split(".")[1] if len(module_name.split(".")) > 1 else None
        )

        if current_app and imported_app and current_app != imported_app:
            # Only shared can be imported across apps
            if imported_app != "shared":
                self.violations.append(
                    (
                        line_no,
                        f"Cross-app import: {module_name}",
                        "Apps should only import from apps.shared, not each other",
                    )
                )

    def _check_model_import_context(
        self, line_no: int, module_name: str, imported_names: set[str]
    ):
        """Check if model imports are in appropriate contexts."""
        file_name = self.file_path.name
        file_dir = str(self.file_path.parent)

        # Models should primarily be imported in:
        # - Other model files
        # - Service layer
        # - API endpoints
        # - Tests

        inappropriate_contexts = ["static", "templates", "frontend", "js", "css"]

        if any(context in file_dir.lower() for context in inappropriate_contexts):
            self.violations.append(
                (
                    line_no,
                    f"Model import in inappropriate context: {module_name}",
                    "Models should not be imported in frontend/static contexts",
                )
            )

    def _is_local_import(self, module_name: str) -> bool:
        """Check if import is from local project."""
        return (
            module_name.startswith("apps.")
            or module_name.startswith("tests.")
            or module_name.startswith("scripts.")
            or module_name in ["conftest"]
        )

    def _get_current_app(self) -> str:
        """Determine which app the current file belongs to."""
        parts = self.file_path.parts
        if "apps" in parts:
            app_index = parts.index("apps")
            if app_index + 1 < len(parts):
                return parts[app_index + 1]
        return None


def validate_file(file_path: Path) -> list[str]:
    """Validate a single Python file for import violations."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        visitor = ImportVisitor(file_path)
        visitor.visit(tree)

        violations = []
        for line_no, violation, suggestion in visitor.violations:
            violations.append(
                f"{file_path}:{line_no}: Import violation - {violation}\n"
                f"  Architectural guidance: {suggestion}"
            )

        return violations

    except SyntaxError as e:
        return [f"{file_path}:{e.lineno}: Syntax error: {e.msg}"]
    except Exception as e:
        return [f"{file_path}: Error parsing file: {e}"]


def check_circular_imports(files: list[Path]) -> list[str]:
    """Check for circular imports between modules."""
    violations = []

    # Build dependency graph
    dependencies = {}

    for file_path in files:
        if file_path.suffix != ".py":
            continue

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            visitor = ImportVisitor(file_path)
            visitor.visit(tree)

            # Convert file path to module name
            module_name = str(file_path).replace("/", ".").replace(".py", "")
            dependencies[module_name] = set()

            # Add local imports
            for import_name in visitor.imports:
                if visitor._is_local_import(import_name):
                    dependencies[module_name].add(import_name)

            for module, names in visitor.from_imports.items():
                if visitor._is_local_import(module):
                    dependencies[module_name].add(module)

        except Exception:
            continue

    # Simple cycle detection (could be more sophisticated)
    for module, deps in dependencies.items():
        for dep in deps:
            if dep in dependencies and module in dependencies[dep]:
                violations.append(
                    f"Circular import detected: {module} <-> {dep}\n"
                    f"  Architectural guidance: Refactor to remove circular dependency"
                )

    return violations


def main():
    """Main validator function called by pre-commit."""
    if len(sys.argv) < 2:
        print("Usage: validate_imports.py <file1> [file2] ...")
        return 1

    all_violations = []
    files = [Path(f) for f in sys.argv[1:]]

    # Check individual files
    for file_path in files:
        if file_path.suffix == ".py":
            violations = validate_file(file_path)
            all_violations.extend(violations)

    # Check for circular imports
    circular_violations = check_circular_imports(files)
    all_violations.extend(circular_violations)

    if all_violations:
        print("🚫 ARCHITECTURAL PURITY VIOLATION: Import Control Violations Found")
        print("=" * 70)
        print()
        for violation in all_violations:
            print(violation)
            print()

        print("IMPORT CONTROL ARCHITECTURAL GUIDANCE:")
        print("• Only approved packages may be imported")
        print("• Apps should only import from apps.shared")
        print("• No cross-app dependencies (except shared)")
        print("• No circular imports between modules")
        print("• Approved core packages:")
        print("  - FastAPI, Pydantic, SQLAlchemy")
        print("  - Granian, HTMX (via CDN)")
        print("  - Standard library modules")
        print("• Prohibited packages:")
        print("  - Other web frameworks (Django, Flask)")
        print("  - JavaScript frameworks (React, Vue)")
        print("  - Heavy ML libraries (unless specifically needed)")
        print("  - Alternative databases (PostgreSQL, MongoDB)")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
