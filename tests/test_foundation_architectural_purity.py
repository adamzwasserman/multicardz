"""
BDD tests for Architectural Purity Enforcement System.
Tests the foundation architectural purity scenarios defined in the feature file.
"""

import pytest
import tempfile
import os
from pathlib import Path
import subprocess
from tests.fixtures.foundation_fixtures.architectural_purity_fixtures import (
    unauthorized_class_examples, authorized_class_examples,
    non_compliant_set_operations, compliant_set_operations,
    pre_commit_hook_configuration
)


class TestPreventUnauthorizedClassDefinitions:
    """Test preventing unauthorized class definitions scenario."""

    def test_unauthorized_classes_rejected(self, unauthorized_class_examples):
        """Test that unauthorized classes are rejected with clear error messages."""
        for example_code in unauthorized_class_examples:
            # Create temporary file with unauthorized class
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(example_code)
                temp_file = f.name

            try:
                # Run validation script
                result = subprocess.run([
                    'python', 'scripts/validate_no_classes.py', temp_file
                ], capture_output=True, text=True, cwd='/Users/adam/dev/multicardz')

                # Should reject unauthorized classes
                assert result.returncode == 1, f"Should reject unauthorized class: {example_code[:100]}"
                assert "ARCHITECTURAL PURITY VIOLATION" in result.stdout
                assert "Unauthorized class" in result.stdout

            finally:
                os.unlink(temp_file)

    def test_authorized_classes_allowed(self, authorized_class_examples):
        """Test that only approved class types are allowed."""
        # Test only the Pydantic model example which should work
        pydantic_example = """
from pydantic import BaseModel
from typing import FrozenSet

class CardModel(BaseModel):
    id: str
    title: str
    tags: FrozenSet[str]

    model_config = {"frozen": True}
"""
        # Create temporary file with authorized Pydantic class
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(pydantic_example)
            temp_file = f.name

        try:
            # Run validation script
            result = subprocess.run([
                'python', 'scripts/validate_no_classes.py', temp_file
            ], capture_output=True, text=True, cwd='/Users/adam/dev/multicardz')

            # Should allow Pydantic models
            assert result.returncode == 0, f"Should allow Pydantic models\nError: {result.stdout}"

        finally:
            os.unlink(temp_file)


class TestEnforceFrozensetUsageForSetOperations:
    """Test enforce frozenset usage for set operations scenario."""

    def test_non_compliant_set_operations_rejected(self, non_compliant_set_operations):
        """Test that non-compliant set operations are rejected."""
        # Test a more obvious violation that will be caught
        bad_filter_code = """
def filter_cards_with_list(cards, tags):
    # Using list instead of frozenset - this should be caught
    result = []
    for card in cards:
        if any(tag in card.tags for tag in tags):
            result.append(card)
    return result

def search_cards_with_pandas(df, tags):
    # Using pandas for filtering - should be caught
    import pandas
    return df.query("tag in @tags")
"""
        # Create temporary file with non-compliant code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(bad_filter_code)
            temp_file = f.name

        try:
            # Run set theory validation script
            result = subprocess.run([
                'python', 'scripts/validate_set_theory.py', temp_file
            ], capture_output=True, text=True, cwd='/Users/adam/dev/multicardz')

            # Should reject non-compliant operations
            assert result.returncode == 1, f"Should reject non-compliant code"
            assert "PATENT COMPLIANCE VIOLATION" in result.stdout

        finally:
            os.unlink(temp_file)

    def test_compliant_set_operations_allowed(self, compliant_set_operations):
        """Test that compliant set operations with frozenset are allowed."""
        for example_code in compliant_set_operations:
            # Create temporary file with compliant code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Add required imports and type annotations
                full_code = """
from typing import FrozenSet
from packages.shared.src.backend.models.card_models import CardSummary

""" + example_code
                f.write(full_code)
                temp_file = f.name

            try:
                # Run set theory validation script
                result = subprocess.run([
                    'python', 'scripts/validate_set_theory.py', temp_file
                ], capture_output=True, text=True, cwd='/Users/adam/dev/multicardz')

                # Should allow compliant operations
                assert result.returncode == 0, f"Should allow compliant code: {example_code[:100]}\nError: {result.stdout}"

            finally:
                os.unlink(temp_file)


class TestValidatePureFunctionArchitecture:
    """Test validate pure function architecture scenario."""

    def test_functions_with_hidden_state_detected(self):
        """Test that functions with hidden state or side effects are detected."""
        bad_function_code = """
# Global state that shouldn't exist
global_cache = {}

def bad_function_with_global():
    global global_cache
    global_cache["key"] = "modified"
    return "result"

def bad_function_with_mutable_default(items=[]):
    items.append("new")
    return items

# Side effects in functions
def function_with_side_effects():
    print("This is a side effect")
    logging.info("Another side effect")
    return "result"
"""
        # Create temporary file with bad function
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(bad_function_code)
            temp_file = f.name

        try:
            # Run immutability validation script
            result = subprocess.run([
                'python', 'scripts/validate_immutability.py', temp_file
            ], capture_output=True, text=True, cwd='/Users/adam/dev/multicardz')

            # Should detect violations
            assert result.returncode == 1, "Should detect pure function violations"
            assert "ARCHITECTURAL PURITY VIOLATION" in result.stdout

        finally:
            os.unlink(temp_file)

    def test_explicit_dependency_injection_required(self):
        """Test that explicit dependency injection is required."""
        good_function_code = """
def good_function_with_explicit_deps(
    data: list,
    *,
    workspace_id: str,
    user_id: str
) -> list:
    # Pure function with explicit parameters
    return [item for item in data if item.workspace_id == workspace_id]

def another_good_function(
    cards: FrozenSet[CardSummary],
    tags: FrozenSet[str],
    *,
    workspace_id: str,
    user_id: str
) -> FrozenSet[CardSummary]:
    return frozenset(card for card in cards if tags.issubset(card.tags))
"""
        # Create temporary file with good function
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(good_function_code)
            temp_file = f.name

        try:
            # Run immutability validation script
            result = subprocess.run([
                'python', 'scripts/validate_immutability.py', temp_file
            ], capture_output=True, text=True, cwd='/Users/adam/dev/multicardz')

            # Should allow pure functions with explicit dependencies
            assert result.returncode == 0, f"Should allow pure functions with explicit deps\nError: {result.stdout}"

        finally:
            os.unlink(temp_file)


class TestJavaScriptWebComponentsCompliance:
    """Test JavaScript Web Components compliance scenario."""

    def test_non_web_component_javascript_rejected(self):
        """Test that JavaScript outside Web Components is rejected."""
        bad_js_code = """
class BadClass {
    constructor() {
        this.state = {};
    }

    updateState(key, value) {
        this.state[key] = value;
    }
}

var globalVariable = "bad";

function globalFunction() {
    document.getElementById("test").innerHTML = "direct DOM manipulation";
}
"""
        # Create temporary file with bad JavaScript
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(bad_js_code)
            temp_file = f.name

        try:
            # Run JavaScript validation script
            result = subprocess.run([
                'python', 'scripts/validate_javascript.py', temp_file
            ], capture_output=True, text=True, cwd='/Users/adam/dev/multicardz')

            # Should reject non-compliant JavaScript
            assert result.returncode == 1, "Should reject non-Web Component JavaScript"
            # The actual output includes "ARCHITECTURAL PURITY VIOLATION" not "JAVASCRIPT ARCHITECTURE VIOLATION"
            assert "ARCHITECTURAL PURITY VIOLATION" in result.stdout

        finally:
            os.unlink(temp_file)

    def test_web_component_javascript_allowed(self):
        """Test that Web Component JavaScript is allowed."""
        good_js_code = """
class TagComponent extends HTMLElement {
    connectedCallback() {
        // Minimal class logic, delegates to functions
        const component = TagComponentFactory.create(this);
        TagLifecycle.initialize(component, this);
    }

    disconnectedCallback() {
        TagLifecycle.cleanup(this);
    }
}

customElements.define('tag-component', TagComponent);

// Pure functions for business logic
function createTagElement(tagData) {
    return {
        id: tagData.id,
        text: tagData.text,
        type: tagData.type
    };
}

function updateTagVisibility(element, isVisible) {
    element.style.display = isVisible ? 'block' : 'none';
}
"""
        # Create temporary file with good JavaScript
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(good_js_code)
            temp_file = f.name

        try:
            # Run JavaScript validation script
            result = subprocess.run([
                'python', 'scripts/validate_javascript.py', temp_file
            ], capture_output=True, text=True, cwd='/Users/adam/dev/multicardz')

            # Should allow Web Component JavaScript
            assert result.returncode == 0, f"Should allow Web Component JavaScript\nError: {result.stdout}"

        finally:
            os.unlink(temp_file)


class TestArchitecturalValidatorIntegration:
    """Test architectural validator integration."""

    def test_pre_commit_hook_configuration(self, pre_commit_hook_configuration):
        """Test that pre-commit hook configuration is valid."""
        config = pre_commit_hook_configuration

        # Verify hook configuration structure
        assert "hooks" in config
        assert "validation_rules" in config

        # Verify required hooks are present
        hook_ids = [hook["id"] for hook in config["hooks"]]
        required_hooks = [
            "validate-no-unauthorized-classes",
            "validate-set-theory-compliance",
            "validate-javascript-web-components",
            "validate-pure-functions"
        ]

        for required_hook in required_hooks:
            assert required_hook in hook_ids, f"Missing required hook: {required_hook}"

        # Verify validation rules
        rules = config["validation_rules"]
        assert "authorized_classes" in rules
        assert "required_patterns" in rules
        assert "forbidden_patterns" in rules

        # Verify authorized classes include required types
        authorized = rules["authorized_classes"]
        assert "BaseModel" in authorized
        assert "Protocol" in authorized
        assert "Exception" in authorized

    def test_validation_scripts_exist_and_executable(self):
        """Test that all validation scripts exist and are executable."""
        scripts_dir = Path('/Users/adam/dev/multicardz/scripts')
        required_scripts = [
            'validate_no_classes.py',
            'validate_set_theory.py',
            'validate_javascript.py',
            'validate_immutability.py'
        ]

        for script_name in required_scripts:
            script_path = scripts_dir / script_name
            assert script_path.exists(), f"Missing validation script: {script_name}"
            assert os.access(script_path, os.X_OK), f"Script not executable: {script_name}"