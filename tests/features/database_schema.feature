Feature: Zero-Trust Database Schema
  As a multicardz system
  I need separate databases by mode with proper schema
  So that user data is isolated and privacy is maintained

  Background:
    Given the multicardz system is initialized
    And the database mode is configured

  Scenario: Development mode database creation
    Given I am using "development" mode
    When I create the database schema
    Then the following tables should exist:
      | table_name        | primary_key |
      | cards            | card_id     |
      | tags             | tag_id      |
      | card_contents    | id          |
      | user_preferences | user_id     |
      | saved_views      | view_id     |
    And the cards table should have columns:
      | column_name  | type    | nullable |
      | card_id      | TEXT    | no       |
      | user_id      | TEXT    | no       |
      | workspace_id | TEXT    | no       |
      | name         | TEXT    | no       |
      | description  | TEXT    | yes      |
      | created      | DATETIME| no       |
      | modified     | DATETIME| no       |
      | deleted      | DATETIME| yes      |
      | tag_ids      | JSON    | no       |
      | tag_bitmaps  | JSON    | yes      |
    And the tags table should have columns:
      | column_name  | type    | nullable |
      | tag_id       | TEXT    | no       |
      | user_id      | TEXT    | no       |
      | workspace_id | TEXT    | no       |
      | name         | TEXT    | no       |
      | tag_bitmap   | INTEGER | no       |
      | card_count   | INTEGER | no       |
      | created      | DATETIME| no       |
      | modified     | DATETIME| no       |
      | deleted      | DATETIME| yes      |

  Scenario: Normal mode database creation
    Given I am using "normal" mode
    When I create the database schema
    Then the database should be created with Turso
    And the schema should match development mode
    And Turso Cloud sync should be optional

  Scenario: Privacy mode database separation
    Given I am using "privacy" mode
    When I create the database schema for user "test_user" and workspace "test_ws"
    Then three separate databases should exist:
      | database_type | location           | content_type    |
      | browser       | WASM SQLite       | full_content    |
      | server        | Turso embedded    | obfuscated_only |
      | cloud         | Turso Cloud       | obfuscated_only |
    And the server database should contain only:
      | table_name         | data_stored                |
      | obfuscated_cards  | card_bitmap, tag_bitmaps   |
      | obfuscated_tags   | tag_bitmap                 |
      | sync_metadata     | sync status and versions   |

  Scenario: Database isolation verification
    Given I have created databases for multiple users
    When I access the database for user "user1" and workspace "ws1"
    Then I should not be able to access data from user "user2"
    And I should not be able to access data from workspace "ws2"
    And each user-workspace combination should have separate database files

  Scenario: Card count auto-maintenance
    Given I have a tag with tag_id "tag1"
    And the tag has card_count of 0
    When I add "tag1" to a card
    Then the card_count for "tag1" should be 1
    When I add "tag1" to another card
    Then the card_count for "tag1" should be 2
    When I remove "tag1" from one card
    Then the card_count for "tag1" should be 1