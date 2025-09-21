Feature: Architectural Purity Enforcement System
  As a system architect
  I want automated enforcement of architectural principles
  So that the codebase maintains pure functional design without class-based anti-patterns

  Scenario: Prevent unauthorized class definitions
    Given I attempt to create a class for business logic
    When the pre-commit hooks validate the code
    Then the commit should be rejected with clear error message
    And only approved class types should be allowed (Pydantic, SQLAlchemy, Protocols)

  Scenario: Enforce frozenset usage for set operations
    Given I attempt to use list or dict for filtering operations
    When the architectural validator runs
    Then the code should be rejected as non-compliant
    And the validator should suggest frozenset alternatives

  Scenario: Validate pure function architecture
    Given I create functions with hidden state or side effects
    When the purity validator examines the code
    Then violations should be detected and reported
    And explicit dependency injection should be required

  Scenario: JavaScript Web Components compliance
    Given I attempt to write JavaScript outside Web Components
    When the JavaScript validator runs
    Then non-compliant code should be rejected
    And only functional delegation patterns should be allowed

  Scenario: Performance regression detection
    Given I modify code that affects performance-critical paths
    When automated benchmarks run
    Then any regression should be detected and reported
    And the commit should be blocked until performance is restored