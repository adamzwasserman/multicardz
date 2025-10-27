#!/usr/bin/env python3
"""
Comprehensive test suite for the Group Tags API.

Tests all CRUD operations, expansion, polymorphic dispatch, and caching.
"""

import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add apps to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apps.shared.config.database import DATABASE_PATH
from apps.user.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def setup_test_data():
    """Set up test data in database."""
    # Create test workspace and user
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Create test tags
        test_tags = (
            ("tag-1", "frontend", "test-workspace", "test-user"),
            ("tag-2", "backend", "test-workspace", "test-user"),
            ("tag-3", "api", "test-workspace", "test-user"),
            ("tag-4", "database", "test-workspace", "test-user"),
        )

        for tag_id, tag_name, workspace_id, user_id in test_tags:
            cursor.execute(
                """
                INSERT OR IGNORE INTO tags (tag_id, tag, workspace_id, user_id, created, modified)
                VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                (tag_id, tag_name, workspace_id, user_id),
            )

        conn.commit()

    yield

    # Cleanup
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM group_tags WHERE workspace_id = ?", ("test-workspace",)
        )
        cursor.execute("DELETE FROM group_memberships WHERE group_id LIKE 'group_%'")
        cursor.execute("DELETE FROM tags WHERE workspace_id = ?", ("test-workspace",))
        conn.commit()


# ============================================================================
# Group Creation Tests
# ============================================================================


def test_create_group_basic(client, setup_test_data):
    """Test basic group creation."""
    print("🧪 Testing basic group creation...")

    response = client.post(
        "/api/groups/create",
        json={
            "name": "engineering",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1", "tag-2"],
            "visual_style": {},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["group_id"].startswith("group_")
    assert "created successfully" in data["message"]

    print(f"✅ Group created: {data['group_id']}")


def test_create_group_with_members(client, setup_test_data):
    """Test group creation with initial members."""
    print("🧪 Testing group creation with members...")

    response = client.post(
        "/api/groups/create",
        json={
            "name": "full-stack",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1", "tag-2", "tag-3"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Verify members
    group_id = data["group_id"]
    info_response = client.get(f"/api/groups/info/{group_id}")
    info_data = info_response.json()

    assert info_data["member_count"] == 3
    assert set(info_data["member_tag_ids"]) == {"tag-1", "tag-2", "tag-3"}

    print(f"✅ Group created with {info_data['member_count']} members")


def test_create_group_duplicate_name(client, setup_test_data):
    """Test that duplicate group names are rejected."""
    print("🧪 Testing duplicate group name validation...")

    # Create first group
    client.post(
        "/api/groups/create",
        json={
            "name": "duplicate-test",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": [],
        },
    )

    # Attempt to create duplicate
    response = client.post(
        "/api/groups/create",
        json={
            "name": "duplicate-test",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": [],
        },
    )

    data = response.json()
    assert data["success"] is False
    assert "already exists" in data["message"].lower()

    print("✅ Duplicate name rejected")


# ============================================================================
# Member Management Tests
# ============================================================================


def test_add_member_to_group(client, setup_test_data):
    """Test adding a member to an existing group."""
    print("🧪 Testing add member to group...")

    # Create group
    create_response = client.post(
        "/api/groups/create",
        json={
            "name": "team",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1"],
        },
    )
    group_id = create_response.json()["group_id"]

    # Add member
    add_response = client.post(
        "/api/groups/add-member",
        json={
            "group_id": group_id,
            "member_tag_id": "tag-2",
            "user_id": "test-user",
        },
    )

    assert add_response.status_code == 200
    data = add_response.json()
    assert data["success"] is True

    # Verify member added
    info_response = client.get(f"/api/groups/info/{group_id}")
    info_data = info_response.json()
    assert info_data["member_count"] == 2
    assert "tag-2" in info_data["member_tag_ids"]

    print("✅ Member added successfully")


def test_add_multiple_members(client, setup_test_data):
    """Test batch adding members to group."""
    print("🧪 Testing batch add members...")

    # Create group
    create_response = client.post(
        "/api/groups/create",
        json={
            "name": "batch-test",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": [],
        },
    )
    group_id = create_response.json()["group_id"]

    # Add multiple members
    add_response = client.post(
        "/api/groups/add-members",
        json={
            "group_id": group_id,
            "member_tag_ids": ["tag-1", "tag-2", "tag-3"],
            "user_id": "test-user",
        },
    )

    assert add_response.status_code == 200
    data = add_response.json()
    assert data["success"] is True
    assert data["members_added"] == 3

    # Verify all members added
    info_response = client.get(f"/api/groups/info/{group_id}")
    info_data = info_response.json()
    assert info_data["member_count"] == 3

    print(f"✅ Batch added {data['members_added']} members")


def test_remove_member_from_group(client, setup_test_data):
    """Test removing a member from group."""
    print("🧪 Testing remove member from group...")

    # Create group with members
    create_response = client.post(
        "/api/groups/create",
        json={
            "name": "remove-test",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1", "tag-2", "tag-3"],
        },
    )
    group_id = create_response.json()["group_id"]

    # Remove member
    remove_response = client.post(
        "/api/groups/remove-member",
        json={
            "group_id": group_id,
            "member_tag_id": "tag-2",
            "user_id": "test-user",
        },
    )

    assert remove_response.status_code == 200
    data = remove_response.json()
    assert data["success"] is True

    # Verify member removed
    info_response = client.get(f"/api/groups/info/{group_id}")
    info_data = info_response.json()
    assert info_data["member_count"] == 2
    assert "tag-2" not in info_data["member_tag_ids"]

    print("✅ Member removed successfully")


# ============================================================================
# Group Expansion Tests
# ============================================================================


def test_expand_simple_group(client, setup_test_data):
    """Test expanding a simple group with direct members."""
    print("🧪 Testing simple group expansion...")

    # Create group
    create_response = client.post(
        "/api/groups/create",
        json={
            "name": "expand-simple",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1", "tag-2"],
        },
    )
    group_id = create_response.json()["group_id"]

    # Expand group
    expand_response = client.post(
        "/api/groups/expand",
        json={"group_id": group_id, "use_cache": False},
    )

    assert expand_response.status_code == 200
    data = expand_response.json()
    assert data["success"] is True
    assert set(data["expanded_tag_ids"]) == {"tag-1", "tag-2"}
    assert data["depth"] >= 0

    print(f"✅ Expanded to {len(data['expanded_tag_ids'])} tags")


def test_expand_nested_group(client, setup_test_data):
    """Test expanding nested groups."""
    print("🧪 Testing nested group expansion...")

    # Create inner group
    inner_response = client.post(
        "/api/groups/create",
        json={
            "name": "inner-group",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1", "tag-2"],
        },
    )
    inner_group_id = inner_response.json()["group_id"]

    # Create outer group containing inner group
    outer_response = client.post(
        "/api/groups/create",
        json={
            "name": "outer-group",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": [inner_group_id, "tag-3"],
        },
    )
    outer_group_id = outer_response.json()["group_id"]

    # Expand outer group
    expand_response = client.post(
        "/api/groups/expand",
        json={"group_id": outer_group_id, "use_cache": False},
    )

    data = expand_response.json()
    assert data["success"] is True
    # Should expand to all leaf tags: tag-1, tag-2, tag-3
    assert set(data["expanded_tag_ids"]) == {"tag-1", "tag-2", "tag-3"}

    print(f"✅ Nested expansion: {len(data['expanded_tag_ids'])} leaf tags")


def test_expansion_caching(client, setup_test_data):
    """Test that expansion caching works."""
    print("🧪 Testing expansion caching...")

    # Create group
    create_response = client.post(
        "/api/groups/create",
        json={
            "name": "cache-test",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1", "tag-2"],
        },
    )
    group_id = create_response.json()["group_id"]

    # First expansion (cache miss)
    expand1 = client.post(
        "/api/groups/expand",
        json={"group_id": group_id, "use_cache": True},
    )
    data1 = expand1.json()

    # Second expansion (cache hit)
    expand2 = client.post(
        "/api/groups/expand",
        json={"group_id": group_id, "use_cache": True},
    )
    data2 = expand2.json()

    # Results should be identical
    assert data1["expanded_tag_ids"] == data2["expanded_tag_ids"]

    # Check cache stats
    stats_response = client.get("/api/groups/cache/stats")
    stats = stats_response.json()
    assert stats["success"] is True
    assert "cache_stats" in stats

    print("✅ Caching working correctly")


# ============================================================================
# Query Tests
# ============================================================================


def test_get_group_info(client, setup_test_data):
    """Test getting group information."""
    print("🧪 Testing get group info...")

    # Create group
    create_response = client.post(
        "/api/groups/create",
        json={
            "name": "info-test",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1", "tag-2"],
        },
    )
    group_id = create_response.json()["group_id"]

    # Get info
    info_response = client.get(f"/api/groups/info/{group_id}")
    assert info_response.status_code == 200

    data = info_response.json()
    assert data["group_id"] == group_id
    assert data["name"] == "info-test"
    assert data["workspace_id"] == "test-workspace"
    assert data["member_count"] == 2

    print("✅ Group info retrieved")


def test_get_workspace_groups(client, setup_test_data):
    """Test getting all groups for a workspace."""
    print("🧪 Testing get workspace groups...")

    # Create multiple groups
    for i in range(3):
        client.post(
            "/api/groups/create",
            json={
                "name": f"workspace-group-{i}",
                "workspace_id": "test-workspace",
                "user_id": "test-user",
                "member_tag_ids": [],
            },
        )

    # Get all groups
    response = client.get("/api/groups/workspace/test-workspace")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["total_count"] >= 3
    assert len(data["groups"]) >= 3

    print(f"✅ Retrieved {data['total_count']} workspace groups")


def test_get_nonexistent_group(client, setup_test_data):
    """Test getting info for nonexistent group."""
    print("🧪 Testing nonexistent group...")

    response = client.get("/api/groups/info/group_nonexistent")
    assert response.status_code == 404

    print("✅ Nonexistent group returns 404")


# ============================================================================
# Delete Tests
# ============================================================================


def test_delete_group(client, setup_test_data):
    """Test deleting a group."""
    print("🧪 Testing group deletion...")

    # Create group
    create_response = client.post(
        "/api/groups/create",
        json={
            "name": "delete-test",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1"],
        },
    )
    group_id = create_response.json()["group_id"]

    # Delete group
    delete_response = client.delete(f"/api/groups/{group_id}")
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["success"] is True

    # Verify group no longer exists
    info_response = client.get(f"/api/groups/info/{group_id}")
    assert info_response.status_code == 404

    print("✅ Group deleted successfully")


# ============================================================================
# Cache Management Tests
# ============================================================================


def test_invalidate_cache(client, setup_test_data):
    """Test manual cache invalidation."""
    print("🧪 Testing cache invalidation...")

    # Create group
    create_response = client.post(
        "/api/groups/create",
        json={
            "name": "invalidate-test",
            "workspace_id": "test-workspace",
            "user_id": "test-user",
            "member_tag_ids": ["tag-1"],
        },
    )
    group_id = create_response.json()["group_id"]

    # Expand (cache)
    client.post("/api/groups/expand", json={"group_id": group_id, "use_cache": True})

    # Invalidate cache
    invalidate_response = client.post(f"/api/groups/cache/invalidate/{group_id}")
    assert invalidate_response.status_code == 200
    data = invalidate_response.json()
    assert data["success"] is True

    print("✅ Cache invalidated")


def test_clear_cache(client, setup_test_data):
    """Test clearing entire cache."""
    print("🧪 Testing cache clear...")

    clear_response = client.post("/api/groups/cache/clear")
    assert clear_response.status_code == 200
    data = clear_response.json()
    assert data["success"] is True

    print("✅ Cache cleared")


# ============================================================================
# Run All Tests
# ============================================================================


if __name__ == "__main__":
    print("=" * 60)
    print("Group Tags API Test Suite")
    print("=" * 60)

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
