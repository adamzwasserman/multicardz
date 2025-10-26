Feature: Group Tag Storage
  As a system storing group tags
  I need to persist group definitions and memberships
  So that groups can be retrieved and expanded efficiently

  Scenario: Create new group
    Given I have workspace "workspace-123"
    And I have tags "frontend", "backend", "api"
    When I create group "engineering" with members "frontend", "backend", "api"
    Then the group should be persisted with id
    And the group should have 3 members
    And the group should belong to workspace "workspace-123"

  Scenario: Add member to group
    Given I have group "team" with members "alice", "bob"
    When I add member "charlie" to group "team"
    Then the group "team" should have 3 members
    And the membership should be persisted

  Scenario: Prevent duplicate members
    Given I have group "status" with member "active"
    When I add member "active" to group "status" again
    Then the group should still have 1 member
    And no duplicate entry should exist

  Scenario: Delete group
    Given I have group "temporary" with members "tag1", "tag2"
    When I delete group "temporary"
    Then the group should not exist
    And the membership records should be deleted
    But the member tags should still exist

  Scenario: Prevent self-reference
    Given I have group "recursive"
    When I attempt to add group "recursive" to itself
    Then the operation should fail with error "Cannot add group to itself"
    And the group should remain unchanged

  Scenario: Validate group name
    Given I have workspace "workspace-123"
    When I attempt to create group with empty name
    Then the operation should fail with error "Group name must be 1-100 characters"

  Scenario: Enforce workspace uniqueness
    Given I have workspace "workspace-123"
    And I have group "engineering" in workspace "workspace-123"
    When I attempt to create another group "engineering" in workspace "workspace-123"
    Then the operation should fail with error "already exists"

  Scenario: Batch add members to group
    Given I have group "team" with members "alice", "bob"
    When I add members "charlie", "david", "eve" to group "team" in batch
    Then the group "team" should have 5 members
    And all additions should succeed
