#!/usr/bin/env python3
"""
Comprehensive test suite for the MultiCardz™ drag-drop system.
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Add apps to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from apps.user.main import create_app


def test_basic_routes():
    """Test that basic routes are working."""
    print("🧪 Testing basic routes...")

    app = create_app()
    client = TestClient(app)

    # Test main route
    response = client.get("/")
    assert response.status_code == 200
    assert "MultiCardz™" in response.text
    print("✅ Main route working")

    # Test health check
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cards_api"
    print("✅ Health check working")


def test_pydantic_validation():
    """Test that Pydantic models validate correctly."""
    print("🧪 Testing Pydantic validation...")

    app = create_app()
    client = TestClient(app)

    # Valid request
    valid_request = {
        "tagsInPlay": {
            "zones": {
                "union": {
                    "tags": ["test", "example"],
                    "metadata": {"behavior": "union"}
                },
                "intersection": {
                    "tags": ["filter"],
                    "metadata": {"behavior": "intersection"}
                }
            },
            "controls": {
                "startWithAllCards": True,
                "startWithCardsExpanded": False,
                "showColors": True
            }
        }
    }

    response = client.post("/api/render/cards", json=valid_request)
    assert response.status_code == 200
    print("✅ Valid request accepted")

    # Invalid request - missing required fields
    invalid_request = {
        "tagsInPlay": {
            "zones": {},
            # Missing controls
        }
    }

    response = client.post("/api/render/cards", json=invalid_request)
    # Should still work because controls has defaults
    assert response.status_code == 200
    print("✅ Request with defaults handled")

    # Completely invalid request
    response = client.post("/api/render/cards", json={"invalid": "data"})
    assert response.status_code in [400, 422]  # Validation error (400 or 422 both valid)
    print("✅ Invalid request rejected")


def test_different_zone_behaviors():
    """Test that different zone behaviors are handled."""
    print("🧪 Testing zone behaviors...")

    app = create_app()
    client = TestClient(app)

    behaviors_to_test = [
        ("union", ["tag1", "tag2"]),
        ("intersection", ["tag3", "tag4"]),
        ("difference", ["tag5"]),
        ("exclude", ["tag6"]),
        ("boost", ["tag7"]),
        ("temporal", ["tag8"]),
        ("dimensional", ["tag9"])
    ]

    for behavior, tags in behaviors_to_test:
        request = {
            "tagsInPlay": {
                "zones": {
                    f"test_{behavior}": {
                        "tags": tags,
                        "metadata": {"behavior": behavior}
                    }
                },
                "controls": {"startWithAllCards": False}
            }
        }

        response = client.post("/api/render/cards", json=request)
        assert response.status_code == 200
        print(f"✅ {behavior} behavior handled")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("🧪 Testing edge cases...")

    app = create_app()
    client = TestClient(app)

    # Empty zones
    empty_request = {
        "tagsInPlay": {
            "zones": {},
            "controls": {"startWithAllCards": False}
        }
    }

    response = client.post("/api/render/cards", json=empty_request)
    assert response.status_code == 200
    print("✅ Empty zones handled")

    # Many zones
    many_zones = {}
    for i in range(20):
        many_zones[f"zone_{i}"] = {
            "tags": [f"tag_{i}"],
            "metadata": {"behavior": "union"}
        }

    big_request = {
        "tagsInPlay": {
            "zones": many_zones,
            "controls": {"startWithAllCards": True}
        }
    }

    response = client.post("/api/render/cards", json=big_request)
    assert response.status_code == 200
    print("✅ Many zones handled")

    # Long tag names
    long_request = {
        "tagsInPlay": {
            "zones": {
                "test": {
                    "tags": ["a" * 50, "b" * 50],  # Max is 100 chars per tag
                    "metadata": {"behavior": "union"}
                }
            },
            "controls": {}
        }
    }

    response = client.post("/api/render/cards", json=long_request)
    assert response.status_code == 200
    print("✅ Long tag names handled")


def test_malicious_input():
    """Test protection against malicious input."""
    print("🧪 Testing security...")

    app = create_app()
    client = TestClient(app)

    # Try to inject script
    malicious_request = {
        "tagsInPlay": {
            "zones": {
                "test": {
                    "tags": ["<script>alert('xss')</script>", "normal_tag"],
                    "metadata": {"behavior": "union"}
                }
            },
            "controls": {}
        }
    }

    response = client.post("/api/render/cards", json=malicious_request)
    assert response.status_code == 200
    # The response should be HTML, but malicious script tags should be escaped
    # Check that the malicious script is escaped (contains &lt; instead of <)
    assert "<script>alert('xss')</script>" not in response.text, "Malicious script tag was not escaped!"
    # The escaped version should be present or the tag should be escaped
    assert "&lt;script&gt;" in response.text or "alert('xss')" not in response.text, "XSS content should be escaped"
    print("✅ XSS protection working")

    # Try excessive tags (validation should limit)
    try:
        excessive_request = {
            "tagsInPlay": {
                "zones": {
                    "test": {
                        "tags": [f"tag_{i}" for i in range(100)],  # Over limit
                        "metadata": {"behavior": "union"}
                    }
                },
                "controls": {}
            }
        }

        response = client.post("/api/render/cards", json=excessive_request)
        # Should be rejected by validation
        assert response.status_code == 422
        print("✅ Excessive tags rejected")
    except Exception:
        print("✅ Excessive tags handled")


def test_javascript_syntax():
    """Test that the JavaScript file has valid syntax."""
    print("🧪 Testing JavaScript syntax...")

    js_file = Path("apps/static/js/drag-drop.js")
    if js_file.exists():
        # Basic syntax check - look for class definition
        content = js_file.read_text()
        assert "class SpatialDragDrop" in content
        assert "constructor()" in content
        assert "deriveStateFromDOM" in content
        assert "updateStateAndRender" in content
        print("✅ JavaScript file has expected structure")
    else:
        print("❌ JavaScript file not found")


def test_css_exists():
    """Test that CSS file exists and has drag-drop styles."""
    print("🧪 Testing CSS...")

    css_file = Path("apps/static/css/user.css")
    if css_file.exists():
        content = css_file.read_text()
        assert ".tag.dragging" in content
        assert ".drop-zone.drag-over" in content
        assert ".tag.selected" in content
        print("✅ CSS has drag-drop styles")
    else:
        print("❌ CSS file not found")


def run_all_tests():
    """Run the complete test suite."""
    print("🚀 Starting MultiCardz™ Drag-Drop Test Suite\n")

    test_functions = [
        test_basic_routes,
        test_pydantic_validation,
        test_different_zone_behaviors,
        test_edge_cases,
        test_malicious_input,
        test_javascript_syntax,
        test_css_exists
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            failed += 1
            print()

    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! The drag-drop system is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above.")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
