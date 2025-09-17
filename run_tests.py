#!/usr/bin/env python3
"""
Test Runner for MultiCardz Set Operations.

Provides convenient commands to run different test suites:
- Basic performance tests (1k-10k cards)
- Stress tests (20k-1M cards)
- BDD feature tests
- All tests

Usage:
    python run_tests.py performance    # Basic performance tests
    python run_tests.py stress         # Stress tests (large datasets)
    python run_tests.py bdd            # BDD feature tests
    python run_tests.py all            # All tests
    python run_tests.py quick          # Fast unit tests only
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a pytest command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    duration = time.time() - start_time

    if result.returncode == 0:
        print(f"\n✅ {description} PASSED in {duration:.1f}s")
    else:
        print(f"\n❌ {description} FAILED in {duration:.1f}s")

    return result.returncode == 0


def run_performance_tests():
    """Run basic performance tests (1k-10k cards)."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/test_set_operations_performance.py::TestSetOperationsPerformance",
        "-m",
        "performance",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd, "Performance Tests (1k-10k cards)")


def run_stress_tests():
    """Run stress tests (20k-1M cards, targeting <1s for 1M)."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/test_set_operations_performance.py::TestSetOperationsStress",
        "-m",
        "stress",
        "-v",
        "--tb=short",
        "-s",  # -s to see print output
    ]
    return run_command(cmd, "Stress Tests (20k-1M cards, <1s for 1M)")


def run_bdd_tests():
    """Run BDD feature tests."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/step_definitions/",
        "-m",
        "bdd",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd, "BDD Feature Tests")


def run_quick_tests():
    """Run quick unit tests only."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "-m",
        "not stress and not slow",
        "-v",
        "--tb=short",
        "--durations=5",
    ]
    return run_command(cmd, "Quick Unit Tests")


def run_all_tests():
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--durations=10"]
    return run_command(cmd, "All Tests")


def run_memory_tests():
    """Run memory efficiency tests."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/test_set_operations_performance.py",
        "-m",
        "stress",
        "-k",
        "memory",
        "-v",
        "--tb=short",
        "-s",
    ]
    return run_command(cmd, "Memory Efficiency Tests")


def run_scaling_benchmarks():
    """Run scaling benchmark tests."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/test_set_operations_performance.py::TestSetOperationsStress::test_scaling_benchmarks",
        "-v",
        "--tb=short",
        "-s",
    ]
    return run_command(cmd, "Scaling Benchmarks")


def run_million_card_test():
    """Run the 1 million card test specifically."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/test_set_operations_performance.py::TestSetOperationsStress::test_ultra_dataset_1M",
        "-v",
        "--tb=short",
        "-s",
    ]
    return run_command(cmd, "1 Million Card Test")


def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    test_type = sys.argv[1].lower()

    print("MultiCardz Set Operations Test Runner")
    print(f"Working directory: {Path.cwd()}")

    success = False

    if test_type == "performance":
        success = run_performance_tests()
    elif test_type == "stress":
        success = run_stress_tests()
    elif test_type == "bdd":
        success = run_bdd_tests()
    elif test_type == "quick":
        success = run_quick_tests()
    elif test_type == "all":
        success = run_all_tests()
    elif test_type == "memory":
        success = run_memory_tests()
    elif test_type == "scaling":
        success = run_scaling_benchmarks()
    elif test_type == "million":
        success = run_million_card_test()
    else:
        print(f"Unknown test type: {test_type}")
        print(__doc__)
        sys.exit(1)

    if success:
        print(f"\n🎉 Test suite '{test_type}' completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Test suite '{test_type}' failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
