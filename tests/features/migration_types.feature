Feature: High-Performance Migration Type Definitions
  As a migration system
  I need lightweight immutable types with minimal memory footprint
  So that type operations have zero overhead

  Scenario: SchemaError uses minimal memory with __slots__
    Given I create 1000 SchemaError instances
    When I measure memory usage
    Then total memory should be less than 100KB
    And attribute access should be faster than 10 nanoseconds

  Scenario: SchemaErrorCategory uses integer enum for fast comparisons
    Given I have two SchemaErrorCategory values
    When I compare them for equality
    Then comparison should use integer comparison (not string)
    And comparison should complete in less than 5 nanoseconds

  Scenario: Migration metadata is immutable
    Given I create a Migration instance
    When I attempt to modify any attribute
    Then it should raise AttributeError
    And the object should remain unchanged

  Scenario: Migration sql_path construction is inline
    Given I have a Migration with sql_file "002_add_bitmap_sequences.sql"
    When I call sql_path with base_dir "/migrations"
    Then it should return Path("/migrations/002_add_bitmap_sequences.sql")
    And operation should complete in less than 100 nanoseconds

  Scenario: MigrationResult is lightweight
    Given I create 10000 MigrationResult instances
    When I measure memory usage
    Then total memory should be less than 500KB
    And creation time should be less than 1 millisecond total

  Scenario: Type instantiation is fast
    Given I need to create error objects rapidly
    When I create 1000 SchemaError instances
    Then total creation time should be less than 1 millisecond
    And average per-instance should be less than 1 microsecond
