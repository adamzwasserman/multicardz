# MultiCardz Project - Local Configuration

## Python Execution Standard

**ALWAYS use `uv run` for all Python commands** - This automatically activates the virtual environment.

### Common Commands for This Project

```bash
# Run the main application
uv run python -m apps.user.main
uv run python -m apps.shared.main

# Run tests
uv run pytest                           # All tests
uv run pytest -xvs                      # Stop on first failure, verbose
uv run pytest tests/                    # Specific directory
uv run pytest -k "test_name"            # Specific test pattern
uv run pytest --co -q                   # Collect tests only

# Run Playwright tests
uv run pytest tests/playwright/test_real_mouse_interactions.py -v

# Run performance tests
uv run pytest tests/test_set_operations_performance.py

# Dependency management
uv sync                                 # Sync dependencies from lock file
uv add <package>                        # Add a package
uv remove <package>                     # Remove a package
uv pip install <package>                # Install via pip

# Database migrations (if using alembic)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "message"

# Code quality
uv run ruff check .
uv run mypy apps/
uv run pre-commit run --all-files
```

### Project-Specific Notes

- Virtual environment located at: `.venv/`
- Main application modules: `apps.user.main` and `apps.shared.main`
- Test timeout: Use `timeout 180 uv run pytest -xvs` for potentially long-running tests
- Pre-commit hooks are configured - commits will auto-format code

## Database Modes

This project uses different database modes:
- **Normal mode**: Server-side database
- **Privacy mode**: Browser-based WASM database (Turso)
- **Offline mode**: Local-only operation

Mode selection is handled by `apps/shared/config/database_mode.py`

## Architecture Notes

- Function-based architecture (no classes except approved patterns)
- Zero-trust UUID isolation (workspace_id, user_id on all tables)
- RoaringBitmap for set operations
- Pure functions with explicit state passing
