Feature: Group Expansion
  As a system expanding group tags
  I need to recursively resolve all member tags
  So that operations apply to the complete set

  Scenario: Simple group expansion
    Given I have group "team" with members "alice", "bob", "charlie"
    When I expand group "team"
    Then I should get tags "alice", "bob", "charlie"
    And the expansion should contain 3 tags

  Scenario: Nested group expansion
    Given I have group "backend" with members "python", "java"
    And I have group "frontend" with members "react", "vue"
    And I have group "engineering" with members "backend", "frontend", "devops"
    When I expand group "engineering"
    Then I should get tags "python", "java", "react", "vue", "devops"
    And the expansion should contain 5 tags

  Scenario: Multi-level nesting expansion
    Given I have a 3-level nested group hierarchy
    When I expand the top-level group
    Then I should get all leaf tags from all levels
    And the expansion should complete in under 10ms

  Scenario: Circular reference handling
    Given I have group "parent" with member "child"
    And I have group "child" with member "parent"
    When I expand group "parent"
    Then the expansion should terminate without infinite loop
    And I should get unique tags

  Scenario: Prevent circular reference on add
    Given I have group "parent" with member "child"
    And I have group "child" with member "grandchild"
    When I attempt to add "parent" to group "grandchild"
    Then the operation should fail with error "circular reference"
    And no cycle should be created

  Scenario: Cache hit on repeated expansion
    Given I have group "large" with 50 members
    When I expand group "large" twice
    Then the second expansion should use cache
    And the cache hit rate should be greater than 90%

  Scenario: Expansion depth calculation
    Given I have a 4-level nested group hierarchy
    When I calculate expansion depth
    Then the depth should be 4

  Scenario: Max depth enforcement
    Given I have a 15-level nested group hierarchy
    When I expand the top-level group with max depth 10
    Then the expansion should stop at depth 10
    And no infinite recursion should occur

  Scenario: Apply group to union zone
    Given I have group "priorities" with members "urgent", "high", "medium"
    And the union zone has tags "low", "normal"
    When I apply group "priorities" to union zone
    Then the union zone should have tags "low", "normal", "urgent", "high", "medium"

  Scenario: Apply group to intersection zone
    Given I have group "active" with members "tag1", "tag2", "tag3"
    And the intersection zone has tags "tag2", "tag3", "tag4"
    When I apply group "active" to intersection zone
    Then the intersection zone should have tags "tag2", "tag3"

  Scenario: Apply group to card
    Given I have group "categories" with members "work", "personal", "urgent"
    And a card has tags "draft", "review"
    When I apply group "categories" to the card
    Then the card should have tags "draft", "review", "work", "personal", "urgent"

  Scenario: Empty group expansion
    Given I have group "empty" with no members
    When I expand group "empty"
    Then the expansion should return empty set

  Scenario: Cache invalidation on membership change
    Given I have group "team" with members "alice", "bob"
    And I have expanded group "team"
    When I add member "charlie" to group "team"
    Then the cache for group "team" should be invalidated
    And the next expansion should reflect new member
