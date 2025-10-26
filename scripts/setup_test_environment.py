#!/usr/bin/env python3
"""
Setup script to install testing dependencies for optimal performance.
"""

import subprocess


def run_command(cmd, description):
    """Run a command and show progress."""
    print(f"📦 {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("   ✅ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False


def main():
    """Install all testing dependencies."""
    print("🚀 Setting up multicardz™ Test Environment")
    print("=" * 50)

    # Install parallel testing
    if not run_command(["uv", "add", "--dev", "pytest-xdist"], "Installing pytest-xdist for parallel testing"):
        print("⚠️  Parallel testing may not work without pytest-xdist")

    # Install coverage tools
    if not run_command(["uv", "add", "--dev", "pytest-cov"], "Installing pytest-cov for coverage"):
        print("⚠️  Coverage reporting may not work")

    # Install profiling tools (already in stdlib but ensure we have visualization)
    if not run_command(["uv", "add", "--dev", "snakeviz"], "Installing snakeviz for profile visualization"):
        print("⚠️  Profile visualization may not work")

    # Install async testing support
    if not run_command(["uv", "add", "--dev", "pytest-asyncio"], "Installing pytest-asyncio"):
        print("⚠️  Async testing may not work properly")

    # Ensure playwright is installed
    if not run_command(["uv", "add", "--dev", "playwright"], "Ensuring playwright is installed"):
        print("⚠️  Browser testing may not work")

    # Install playwright browsers
    if not run_command(["uv", "run", "playwright", "install", "chromium"], "Installing chromium for playwright"):
        print("⚠️  Browser automation may not work")

    # Set up git hooks
    print("🔗 Setting up git hooks...")
    try:
        subprocess.run(["git", "config", "core.hooksPath", ".githooks"], check=True)
        print("   ✅ Git hooks configured")
    except subprocess.CalledProcessError:
        print("   ⚠️  Could not configure git hooks")

    print("\n🎉 Test environment setup complete!")
    print("\nTo test the setup, run:")
    print("   python test_runner.py all --smart --time --parallel")


if __name__ == "__main__":
    main()
