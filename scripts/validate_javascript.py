#!/usr/bin/env python3
"""
Architectural Purity Validator - Minimal JavaScript

Enforces the architectural principle that JavaScript usage is EXTREMELY limited:
- ONLY Web Components (custom elements) are allowed
- ONLY ViewTransitions API usage is allowed
- NO direct DOM manipulation outside of Web Components
- NO external JavaScript frameworks (React, Vue, jQuery, etc.)
- NO client-side state management
- ALL interactivity must use HTMX

This ensures patent compliance and maintains our backend-first architecture.
"""

import re
import sys
from pathlib import Path


def validate_javascript_file(file_path: Path) -> list[str]:
    """Validate a JavaScript/TypeScript file for architectural compliance."""
    violations = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Track if this is a valid Web Component file
        is_web_component = False
        has_custom_elements = "customElements.define" in content
        has_html_element_class = "extends HTMLElement" in content
        has_web_component_lifecycle = any(
            method in content
            for method in [
                "connectedCallback",
                "disconnectedCallback",
                "attributeChangedCallback",
            ]
        )

        if (
            has_custom_elements
            and has_html_element_class
            and has_web_component_lifecycle
        ):
            is_web_component = True

        # Prohibited patterns
        prohibited_patterns = {
            # Framework imports/usage
            r"import.*react": "React framework prohibited - use Web Components",
            r"import.*vue": "Vue framework prohibited - use Web Components",
            r"import.*angular": "Angular framework prohibited - use Web Components",
            r"\$\(": "jQuery prohibited - use Web Components",
            r"jQuery": "jQuery prohibited - use Web Components",
            r"import.*lodash": "Lodash prohibited - use native JavaScript",
            r"import.*underscore": "Underscore prohibited - use native JavaScript",
            # Direct DOM manipulation (outside Web Components)
            r"document\.querySelector(?!.*shadowRoot)": "Direct DOM manipulation prohibited outside Web Components",
            r"document\.getElementById(?!.*shadowRoot)": "Direct DOM manipulation prohibited outside Web Components",
            r"document\.createElement(?!.*shadowRoot)": "Direct DOM manipulation prohibited outside Web Components",
            r"\.innerHTML\s*=(?!.*shadowRoot)": "Direct innerHTML manipulation prohibited outside Web Components",
            r"\.textContent\s*=(?!.*shadowRoot)": "Direct textContent manipulation prohibited outside Web Components",
            # Event handling (outside Web Components)
            r"addEventListener(?!.*this\.shadowRoot)": "Direct event handling prohibited - use HTMX",
            r"\.onclick\s*=": "Direct event handling prohibited - use HTMX",
            r"\.onchange\s*=": "Direct event handling prohibited - use HTMX",
            r"\.onsubmit\s*=": "Direct event handling prohibited - use HTMX",
            # State management
            r"localStorage": "Client-side storage prohibited - use server state",
            r"sessionStorage": "Client-side storage prohibited - use server state",
            r"new\s+Map\s*\(": "Client-side state maps prohibited",
            r"new\s+Set\s*\(": "Client-side state sets prohibited",
            r"class.*Store": "Client-side stores prohibited",
            r"useState": "Client-side state prohibited",
            r"useEffect": "Client-side effects prohibited",
            # AJAX/Fetch outside HTMX
            r"fetch\s*\(": "Direct fetch prohibited - use HTMX",
            r"XMLHttpRequest": "XMLHttpRequest prohibited - use HTMX",
            r"axios": "Axios prohibited - use HTMX",
            # SPA patterns
            r"router": "Client-side routing prohibited",
            r"history\.pushState": "History manipulation prohibited",
            r"location\.hash": "Hash routing prohibited",
        }

        # Allowed patterns for Web Components
        allowed_patterns = {
            r"customElements\.define",
            r"extends HTMLElement",
            r"connectedCallback",
            r"disconnectedCallback",
            r"attributeChangedCallback",
            r"this\.shadowRoot",
            r"this\.attachShadow",
            r"document\.startViewTransition",
            r"view-transition-name",
        }

        for line_no, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("//") or line.strip().startswith("/*"):
                continue

            # Check prohibited patterns
            for pattern, message in prohibited_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # Allow some patterns if we're in a Web Component
                    if is_web_component and any(
                        allowed in line
                        for allowed in ["shadowRoot", "customElements", "HTMLElement"]
                    ):
                        continue

                    violations.append(
                        f"{file_path}:{line_no}: JavaScript restriction violation - {message}\n"
                        f"  Line: {line.strip()}"
                    )

        # Check for valid Web Component structure
        if content.strip() and not is_web_component:
            # Check if it contains any JavaScript that's not just ViewTransitions
            has_non_allowed_js = any(
                pattern in content.lower()
                for pattern in [
                    "function",
                    "const ",
                    "let ",
                    "var ",
                    "class ",
                    "document.",
                    "window.",
                    "console.",
                ]
            )

            # Allow ViewTransitions API usage
            if "startViewTransition" in content or "view-transition" in content:
                has_non_allowed_js = False

            if has_non_allowed_js:
                violations.append(
                    f"{file_path}:1: Invalid JavaScript file - must be a Web Component\n"
                    f"  Only Web Components and ViewTransitions API are allowed"
                )

    except Exception as e:
        violations.append(f"{file_path}: Error reading file: {e}")

    return violations


def validate_html_file(file_path: Path) -> list[str]:
    """Validate HTML files for inline JavaScript violations."""
    violations = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        # Check for inline JavaScript
        prohibited_html_patterns = {
            r"onclick\s*=": "Inline onclick prohibited - use HTMX hx-* attributes",
            r"onchange\s*=": "Inline onchange prohibited - use HTMX hx-* attributes",
            r"onsubmit\s*=": "Inline onsubmit prohibited - use HTMX hx-* attributes",
            r"<script[^>]*>(?!.*web.*component)": "Inline scripts prohibited except for Web Components",
            r"javascript:": "javascript: URLs prohibited - use HTMX",
        }

        for line_no, line in enumerate(lines, 1):
            for pattern, message in prohibited_html_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # Allow if it's HTMX or Web Component related
                    if any(
                        allowed in line.lower()
                        for allowed in [
                            "hx-",
                            "htmx",
                            "custom-element",
                            "web-component",
                        ]
                    ):
                        continue

                    violations.append(
                        f"{file_path}:{line_no}: HTML JavaScript violation - {message}\n"
                        f"  Line: {line.strip()}"
                    )

    except Exception as e:
        violations.append(f"{file_path}: Error reading file: {e}")

    return violations


def main():
    """Main validator function called by pre-commit."""
    if len(sys.argv) < 2:
        print("Usage: validate_javascript.py <file1> [file2] ...")
        return 1

    all_violations = []

    for file_path in sys.argv[1:]:
        path = Path(file_path)

        if path.suffix in [".js", ".ts"]:
            violations = validate_javascript_file(path)
            all_violations.extend(violations)
        elif path.suffix in [".html", ".htm"]:
            violations = validate_html_file(path)
            all_violations.extend(violations)

    if all_violations:
        print("🚫 ARCHITECTURAL PURITY VIOLATION: Unauthorized JavaScript Found")
        print("=" * 65)
        print()
        for violation in all_violations:
            print(violation)
            print()

        print("JAVASCRIPT ARCHITECTURAL GUIDANCE:")
        print("• JavaScript is SEVERELY RESTRICTED in this architecture")
        print("• ONLY allowed JavaScript:")
        print("  - Web Components (custom elements extending HTMLElement)")
        print("  - ViewTransitions API (document.startViewTransition)")
        print("  - HTMX integration code")
        print("• PROHIBITED:")
        print("  - Any JavaScript frameworks (React, Vue, Angular, jQuery)")
        print("  - Direct DOM manipulation outside Web Components")
        print("  - Client-side state management")
        print("  - Direct event handling (use HTMX hx-* attributes)")
        print("  - AJAX/fetch (use HTMX)")
        print("  - Client-side routing")
        print("• ALL interactivity must use HTMX server interactions")
        print("• Use Web Components ONLY for reusable UI elements")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
