"""
Pytest configuration and fixtures for MultiCardz test suite.

Provides tqdm integration for test progress tracking and performance optimizations.
"""

import pytest
from tqdm import tqdm


class TqdmTestReporter:
    """Custom pytest plugin for tqdm progress reporting."""

    def __init__(self):
        self.total_tests = 0
        self.progress_bar = None
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def pytest_collection_finish(self, session):
        """Called after test collection is complete."""
        self.total_tests = len(session.items)
        if self.total_tests > 0:
            self.progress_bar = tqdm(
                total=self.total_tests,
                desc="Running tests",
                unit="test",
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] P:{postfix[passed]} F:{postfix[failed]} S:{postfix[skipped]}",
                postfix={"passed": 0, "failed": 0, "skipped": 0}
            )

    def pytest_runtest_logreport(self, report):
        """Called for each test result."""
        if not self.progress_bar:
            return

        if report.when == "call":  # Only count the actual test execution
            if report.outcome == "passed":
                self.passed += 1
            elif report.outcome == "failed":
                self.failed += 1
            elif report.outcome == "skipped":
                self.skipped += 1

            # Update progress bar
            self.progress_bar.set_postfix(
                passed=self.passed,
                failed=self.failed,
                skipped=self.skipped
            )
            self.progress_bar.update(1)

    def pytest_sessionfinish(self, session, exitstatus):
        """Called when test session finishes."""
        if self.progress_bar:
            self.progress_bar.close()

            # Final summary
            total_run = self.passed + self.failed + self.skipped
            print(f"\n🎯 Test Summary: {total_run} tests run")
            print(f"✅ Passed: {self.passed}")
            if self.failed > 0:
                print(f"❌ Failed: {self.failed}")
            if self.skipped > 0:
                print(f"⏭️  Skipped: {self.skipped}")


def pytest_configure(config):
    """Register our custom plugin."""
    if config.option.verbose and not config.option.tb == "no":
        # Only use tqdm in verbose mode and when not in parallel mode
        worker_id = getattr(config, "workerinput", {}).get("workerid")
        if worker_id is None:  # Not running in parallel
            config.pluginmanager.register(TqdmTestReporter(), "tqdm_reporter")


# Performance test fixtures
@pytest.fixture
def small_card_dataset():
    """Generate small card dataset for quick tests."""
    import random
    from apps.shared.models.card import CardSummary

    cards = []
    tags_pool = [f"tag_{i}" for i in range(20)]

    for i in range(1000):
        num_tags = random.randint(1, 3)
        card_tags = frozenset(random.sample(tags_pool, num_tags))
        card = CardSummary(
            id=f"SMALL{i+1:04d}",
            title=f"Small Card {i+1}",
            tags=card_tags
        )
        cards.append(card)

    return frozenset(cards)


@pytest.fixture
def medium_card_dataset():
    """Generate medium card dataset for performance tests."""
    import random
    from apps.shared.models.card import CardSummary

    cards = []
    tags_pool = [f"tag_{i}" for i in range(50)]

    for i in range(10000):
        num_tags = random.randint(1, 4)
        card_tags = frozenset(random.sample(tags_pool, num_tags))
        card = CardSummary(
            id=f"MED{i+1:05d}",
            title=f"Medium Card {i+1}",
            tags=card_tags
        )
        cards.append(card)

    return frozenset(cards)


@pytest.fixture(autouse=True)
def auto_reset_registry():
    """Automatically reset CardRegistrySingleton for each test."""
    from apps.shared.services.set_operations_unified import CardRegistrySingleton

    # Store original instance
    original_instance = CardRegistrySingleton._instance

    # Reset for test
    CardRegistrySingleton._instance = None

    yield

    # Restore original instance after test
    CardRegistrySingleton._instance = original_instance


@pytest.fixture
def reset_singleton():
    """Reset CardRegistrySingleton before each test that needs it."""
    from apps.shared.services.set_operations_unified import CardRegistrySingleton

    # Store original instance
    original_instance = CardRegistrySingleton._instance

    # Reset for test
    CardRegistrySingleton._instance = None

    yield

    # Restore original instance after test
    CardRegistrySingleton._instance = original_instance


# Pytest markers for test organization
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "performance: Performance benchmark tests")
    config.addinivalue_line("markers", "stress: Stress tests with large datasets")
    config.addinivalue_line("markers", "integration: Integration tests across modules")
    config.addinivalue_line("markers", "unit: Unit tests for individual functions")
    config.addinivalue_line("markers", "slow: Tests that take more than 5 seconds")
    config.addinivalue_line("markers", "registry: Tests that use CardRegistrySingleton")