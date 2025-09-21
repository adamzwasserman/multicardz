#!/usr/bin/env python3
"""
Unified MultiCardz™ Test Runner with Parallel Execution & Smart Selection.
Optimized for speed with git-aware test selection and parallel processing.

Usage:
    python test_runner.py frontend           # Frontend drag-drop tests
    python test_runner.py backend            # Backend set operations tests
    python test_runner.py all                # All automated tests (parallel)
    python test_runner.py performance        # Backend performance tests
    python test_runner.py stress             # Backend stress tests
    python test_runner.py bdd                # Backend BDD tests
    python test_runner.py playwright         # Manual Playwright instructions
    python test_runner.py smart              # Only tests affected by changed files
    python test_runner.py --help             # Show this help

Modifiers:
    --time                                   # Show timing information for each test
    --profile                               # Run with profiling enabled
    --smart                                 # Only run tests affected by git changes
    --parallel                              # Force parallel execution (default for 'all')
    --no-cache                              # Disable pytest cache for clean runs
    --coverage                              # Generate test coverage report

Examples:
    python test_runner.py frontend --time         # Frontend tests with timing
    python test_runner.py all --profile          # All tests with profiling (parallel)
    python test_runner.py smart                  # Only changed-file tests
    python test_runner.py backend --time --profile  # Backend with time + profile
    python test_runner.py all --coverage           # All tests with coverage report
    python test_runner.py all --smart            # Optimized for pre-commit hooks
"""

import asyncio
import concurrent.futures
import cProfile
import json
import os
import pstats
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TestResult:
    """Container for test execution results."""
    def __init__(self, name: str, success: bool, duration: float, output: str = "", error: str = ""):
        self.name = name
        self.success = success
        self.duration = duration
        self.output = output
        self.error = error


def get_changed_files() -> Set[str]:
    """Get list of changed files from git."""
    try:
        # Get staged files
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip().split('\n')

        # Get unstaged files
        unstaged = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip().split('\n')

        # Get untracked files
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=10
        ).stdout.strip().split('\n')

        changed = set()
        for files in [staged, unstaged, untracked]:
            changed.update(f for f in files if f and f.strip())

        return changed
    except Exception:
        # If git fails, run all tests
        return set()


def should_run_tests(changed_files: Set[str], test_patterns: List[str]) -> bool:
    """Determine if tests should run based on changed files."""
    if not changed_files:
        return True  # No git or no changes - run all tests

    # Always run if test files themselves changed
    for file in changed_files:
        if file.startswith('tests/') or file.endswith('test_runner.py'):
            return True

        # Check if any pattern matches
        for pattern in test_patterns:
            if pattern in file:
                return True

    return False


def run_command_with_timing(cmd: List[str], description: str, show_output: bool = False,
                          timeout: int = 120) -> TestResult:
    """Run a command and return detailed results with timing."""
    start_time = time.time()

    try:
        if show_output:
            result = subprocess.run(cmd, timeout=timeout)
            duration = time.time() - start_time
            return TestResult(description, result.returncode == 0, duration)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            duration = time.time() - start_time

            return TestResult(
                description,
                result.returncode == 0,
                duration,
                result.stdout,
                result.stderr
            )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return TestResult(description, False, duration, "", "TIMEOUT")
    except Exception as e:
        duration = time.time() - start_time
        return TestResult(description, False, duration, "", str(e))


def print_test_result(result: TestResult, show_timing: bool = False):
    """Print formatted test result."""
    status = "✅ PASSED" if result.success else "❌ FAILED"
    timing_info = f" ({result.duration:.2f}s)" if show_timing else ""

    print(f"🧪 {result.name}{timing_info}")
    print(f"   {status}")

    if not result.success and result.error:
        print(f"   Error: {result.error[:300]}...")


def run_frontend_tests(show_timing: bool = False, use_smart: bool = False,
                      changed_files: Set[str] = None) -> Tuple[bool, List[TestResult]]:
    """Run frontend drag-drop tests with optional smart selection."""
    print("🎨 Frontend Drag-Drop Tests")
    print("=" * 40)

    # Smart test selection patterns
    frontend_patterns = [
        'apps/static/js/', 'apps/static/css/', 'apps/user/', 'apps/templates/',
        'tests/api/', 'tests/playwright/'
    ]

    if use_smart and changed_files is not None:
        if not should_run_tests(changed_files, frontend_patterns):
            print("📈 Smart mode: Skipping frontend tests (no relevant changes)")
            return True, []

    tests = [
        (["uv", "run", "python", "tests/api/test_drag_drop_api.py"], "API endpoint tests"),
        (["uv", "run", "python", "tests/playwright/test_static_html.py"], "Static HTML tests"),
        (["uv", "run", "python", "tests/playwright/test_comprehensive_drag_drop.py"], "Comprehensive drag-drop tests"),
        (["uv", "run", "python", "tests/playwright/test_responsive_resizing.py"], "Responsive & resizing tests")
    ]

    results = []

    # Run tests with optimizations
    for cmd, description in tests:
        # Add performance flags
        optimized_cmd = cmd + ["-O"]  # Python optimization
        result = run_command_with_timing(optimized_cmd, description)
        results.append(result)
        print_test_result(result, show_timing)

    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed

    if show_timing and results:
        total_time = sum(r.duration for r in results)
        print(f"\n⏱️  Total frontend time: {total_time:.2f}s")

    print(f"\n📊 Frontend Tests: {passed} passed, {failed} failed")
    return failed == 0, results


def run_backend_tests(test_type: str = "all", show_timing: bool = False,
                     use_smart: bool = False, changed_files: Set[str] = None,
                     use_parallel: bool = False, no_cache: bool = False,
                     use_coverage: bool = False) -> Tuple[bool, List[TestResult]]:
    """Run backend set operations tests with optimizations."""
    print("⚙️ Backend Set Operations Tests")
    print("=" * 40)

    # Smart test selection patterns
    backend_patterns = [
        'apps/backend/', 'apps/shared/', 'tests/test_', 'tests/features/',
        'pyproject.toml', 'requirements.txt'
    ]

    if use_smart and changed_files is not None:
        if not should_run_tests(changed_files, backend_patterns):
            print("📈 Smart mode: Skipping backend tests (no relevant changes)")
            return True, []

    # Base pytest command with speed optimizations
    base_cmd = ["uv", "run", "python", "-O", "-m", "pytest"]

    # Speed flags
    speed_flags = [
        "--tb=short",           # Shorter tracebacks
        "--disable-warnings",   # Suppress warnings for speed
        "-q",                   # Quiet mode
        "--no-header",          # No pytest header
        "--asyncio-mode=auto",  # Auto async mode
    ]

    if no_cache:
        speed_flags.append("--cache-clear")

    if use_coverage:
        speed_flags.extend([
            "--cov=apps",              # Cover the apps directory
            "--cov-report=html",       # Generate HTML report
            "--cov-report=term-missing", # Show missing lines in terminal
            "--cov-report=json",       # Generate JSON report for CI
        ])
        print("📊 Coverage reporting enabled")

    if use_parallel:
        # Try to detect CPU count and use parallel execution
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            speed_flags.extend(["-n", str(max(2, cpu_count - 1))])  # Leave 1 CPU free
            print(f"🚀 Using {max(2, cpu_count - 1)} parallel workers")
        except:
            print("⚠️  Parallel execution not available (install pytest-xdist)")

    # Map test types to specific paths/patterns (exclude frontend tests)
    test_commands = {
        "all": base_cmd + ["tests/", "--ignore=tests/api", "--ignore=tests/playwright"] + speed_flags + ["-v"],
        "performance": base_cmd + ["tests/test_set_operations_performance.py"] + speed_flags + ["-v"],
        "stress": base_cmd + ["tests/test_set_operations_performance.py", "-k", "stress"] + speed_flags + ["-v"],
        "bdd": base_cmd + ["tests/test_*_bdd.py"] + speed_flags + ["-v"],
        "quick": base_cmd + ["tests/", "--ignore=tests/api", "--ignore=tests/playwright", "-x"] + speed_flags
    }

    cmd = test_commands.get(test_type, test_commands["all"])

    result = run_command_with_timing(cmd, f"Backend {test_type} tests", show_output=True)
    print_test_result(result, show_timing)

    return result.success, [result]


def show_manual_tests():
    """Show instructions for manual tests."""
    print("📋 Manual Test Instructions")
    print("=" * 40)
    print("\n🔗 Integration Tests:")
    print("   1. Start server: uv run python tests/integration/test_server.py")
    print("   2. Open browser: http://localhost:8011")
    print("   3. Test drag-drop manually")

    print("\n🎭 Playwright Browser Tests:")
    print("   1. Start server: uv run python tests/integration/test_server.py")
    print("   2. Comprehensive test: uv run python tests/playwright/test_comprehensive_drag_drop.py")
    print("   3. Responsive test: uv run python tests/playwright/test_responsive_resizing.py")
    print("   4. Legacy test: uv run python tests/playwright/test_real_mouse_interactions.py")
    print("   5. Run replay: uv run python tests/playwright/test_real_mouse_interactions.py replay")

    print("\n📸 Test Artifacts:")
    print("   - tests/artifacts/final_state.png (screenshots)")
    print("   - tests/artifacts/multicardz_test_recording.json (replayable actions)")
    print("   - tests/artifacts/comprehensive_test_final.png (comprehensive test screenshot)")
    print("   - tests/artifacts/comprehensive_test_report.json (detailed test report)")
    print("   - tests/artifacts/responsive_*.png (responsive screenshots)")
    print("   - tests/artifacts/responsive_test_report.json (responsive test report)")


def show_help():
    """Show help message."""
    print(__doc__)


async def run_tests_parallel(show_timing: bool = False, use_smart: bool = False,
                            changed_files: Set[str] = None) -> bool:
    """Run frontend and backend tests in parallel."""
    print("🚀 Running Tests in Parallel Mode")
    print("=" * 40)

    async def run_frontend():
        return run_frontend_tests(show_timing, use_smart, changed_files)

    async def run_backend():
        return run_backend_tests("quick", show_timing, use_smart, changed_files, use_parallel=True, use_coverage=False)

    # Run both test suites concurrently
    start_time = time.time()

    frontend_result, backend_result = await asyncio.gather(
        asyncio.to_thread(lambda: run_frontend_tests(show_timing, use_smart, changed_files)),
        asyncio.to_thread(lambda: run_backend_tests("quick", show_timing, use_smart, changed_files, use_parallel=True, use_coverage=False))
    )

    total_time = time.time() - start_time

    frontend_ok, frontend_results = frontend_result
    backend_ok, backend_results = backend_result

    if show_timing:
        print(f"\n⏱️  Total parallel execution time: {total_time:.2f}s")

    if frontend_ok and backend_ok:
        print("\n🎉 All automated tests passed!")
        return True
    else:
        print(f"\n⚠️ Some tests failed:")
        print(f"   Frontend: {'✅' if frontend_ok else '❌'}")
        print(f"   Backend: {'✅' if backend_ok else '❌'}")
        return False


def parse_args() -> Tuple[str, Dict[str, bool]]:
    """Parse command line arguments."""
    args = sys.argv[1:]
    if not args or args[0] in ["--help", "-h", "help"]:
        return "help", {}

    test_type = args[0].lower()

    # Parse modifiers
    modifiers = {
        "show_timing": "--time" in args,
        "use_profile": "--profile" in args,
        "use_smart": "--smart" in args or test_type == "smart",
        "use_parallel": "--parallel" in args or test_type == "all",
        "no_cache": "--no-cache" in args,
        "use_coverage": "--coverage" in args
    }

    return test_type, modifiers


def main():
    """Main test runner with full optimization support."""
    test_type, modifiers = parse_args()

    if test_type == "help":
        show_help()
        return True

    print("🚀 MultiCardz™ Unified Test Runner")
    print("=" * 50)

    # Get changed files for smart mode
    changed_files = get_changed_files() if modifiers["use_smart"] else set()

    if modifiers["use_smart"] and changed_files:
        print(f"📈 Smart mode: Found {len(changed_files)} changed files")
        if modifiers["show_timing"]:
            print(f"   Changed: {', '.join(list(changed_files)[:5])}{'...' if len(changed_files) > 5 else ''}")

    # Profile wrapper
    def run_tests():
        if test_type == "frontend":
            success, _ = run_frontend_tests(
                modifiers["show_timing"], modifiers["use_smart"], changed_files
            )
            return success

        elif test_type == "backend":
            success, _ = run_backend_tests(
                "all", modifiers["show_timing"], modifiers["use_smart"],
                changed_files, modifiers["use_parallel"], modifiers["no_cache"],
                modifiers["use_coverage"]
            )
            return success

        elif test_type in ["performance", "stress", "bdd", "quick"]:
            success, _ = run_backend_tests(
                test_type, modifiers["show_timing"], modifiers["use_smart"],
                changed_files, modifiers["use_parallel"], modifiers["no_cache"],
                modifiers["use_coverage"]
            )
            return success

        elif test_type == "all":
            if modifiers["use_parallel"]:
                return asyncio.run(run_tests_parallel(
                    modifiers["show_timing"], modifiers["use_smart"], changed_files
                ))
            else:
                # Sequential execution
                frontend_ok, _ = run_frontend_tests(
                    modifiers["show_timing"], modifiers["use_smart"], changed_files
                )
                print()
                backend_ok, _ = run_backend_tests(
                    "quick", modifiers["show_timing"], modifiers["use_smart"],
                    changed_files, False, modifiers["no_cache"], modifiers["use_coverage"]
                )

                if frontend_ok and backend_ok:
                    print("\n🎉 All automated tests passed!")
                    show_manual_tests()
                    return True
                else:
                    print(f"\n⚠️ Some tests failed:")
                    print(f"   Frontend: {'✅' if frontend_ok else '❌'}")
                    print(f"   Backend: {'✅' if backend_ok else '❌'}")
                    return False

        elif test_type == "smart":
            # Smart mode - run all with smart selection
            return asyncio.run(run_tests_parallel(
                modifiers["show_timing"], True, changed_files
            ))

        elif test_type == "playwright":
            show_manual_tests()
            return True

        else:
            print(f"❌ Unknown test type: {test_type}")
            show_help()
            return False

    # Execute with optional profiling
    if modifiers["use_profile"]:
        print("📊 Running with profiling enabled...")
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            success = run_tests()
        finally:
            profiler.disable()

            # Save profile stats
            stats_file = "test_runner_profile.stats"
            profiler.dump_stats(stats_file)

            # Print top functions
            stats = pstats.Stats(stats_file)
            stats.sort_stats('cumulative')
            print("\n📊 Top 10 time-consuming functions:")
            stats.print_stats(10)

            print(f"\n💾 Full profile saved to: {stats_file}")

        return success
    else:
        return run_tests()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)