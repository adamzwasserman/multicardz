Feature: Load Testing & Performance Benchmarking
  As a system architect
  I want to validate performance under load
  So that the system can handle production traffic

  Scenario: API response time benchmarks
    Given the FastAPI application is running
    When I measure response times for 100 requests to each endpoint
    Then GET /health should average <10ms
    And GET /api/landing/{slug} should average <50ms
    And POST /api/analytics/page-view should average <100ms
    And GET /api/funnel/metrics should average <200ms
    And 95th percentile should be within 2x of average

  Scenario: Concurrent user simulation
    Given the system has 10 active landing pages
    When 50 concurrent users visit different landing pages
    Then all requests should complete within 5 seconds
    And no requests should timeout
    And all analytics sessions should be created
    And average response time should be <500ms

  Scenario: Analytics ingestion stress test
    Given the analytics API is available
    When I send 1000 page view events in 10 seconds
    Then all events should be accepted (200 status)
    And database should contain all 1000 events
    And average ingestion time should be <50ms
    And no events should be lost

  Scenario: Database query performance under load
    Given the database has 100000 analytics sessions
    And the database has 500000 page view events
    When I execute 100 concurrent dashboard metric queries
    Then all queries should complete within 10 seconds
    And average query time should be <200ms
    And database connection pool should not exhaust
    And no slow query warnings should occur

  Scenario: Memory usage stability
    Given the application is running
    When I simulate 1 hour of traffic (1000 requests)
    Then memory usage should remain stable
    And memory growth should be <10%
    And no memory leaks should be detected
    And garbage collection should be healthy

  Scenario: Static asset delivery performance
    Given the application serves static files
    When I request analytics.js 100 times
    Then average response time should be <20ms
    And all responses should be cacheable
    And gzip compression should be enabled
    And response size should be <50KB
