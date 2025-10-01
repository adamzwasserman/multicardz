Feature: Workspace-Aware Templates
  As a user
  I want templates to respect workspace context
  So that I only see my workspace data

  Scenario: Render cards for workspace
    Given I am in workspace A
    When the card grid template renders
    Then only workspace A cards should appear
    And workspace_id should be in data attributes
    And drag-drop should maintain context

  Scenario: Tag filtering with workspace
    Given I have tags from my workspace
    When I drag tags to filter area
    Then filtering should apply to workspace cards only
    And tagsInPlay should update correctly
    And /api/render/cards should receive workspace context

  Scenario: Visual workspace indicator
    Given I am logged into a workspace
    When any template renders
    Then workspace name should be visible
    And workspace ID should be in page metadata
    And switching workspaces should refresh all data
