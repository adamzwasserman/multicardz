# MultiCardz

A JavaScript-based spatial tag manipulation system maintaining patent compliance and set theory operations.

## Architecture

MultiCardz implements a clean, patent-compliant system where:
- Backend generates ALL HTML content using Python/FastAPI
- Frontend uses JavaScript ONLY for polymorphic dispatch and HTMX integration
- All filtering uses mathematical set theory operations
- DOM serves as single source of truth (no client-side state)

## Project Structure

```
multicardz/
├── apps/
│   ├── user/          # User-facing application
│   ├── admin/         # Administrative interface
│   ├── public/        # Public API
│   ├── shared/        # Common utilities and set operations
│   └── static/        # Static assets (CSS, JS)
├── docs/
│   ├── architecture/  # Technical architecture documents
│   ├── implementation/# Implementation plans
│   ├── patents/       # Patent documentation
│   └── standards/     # Coding standards
└── tests/             # Test suites
```

## Development Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management with a workspace configuration.

### Prerequisites

- Python 3.11+
- uv (install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Installation

```bash
# Install all workspace dependencies
uv sync

# Install development dependencies
uv sync --extra dev

# Install specific app dependencies
uv sync --package multicardz-user
```

### Development Commands

```bash
# Run the user application
cd apps/user && uv run uvicorn main:app --reload --port 8000

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=apps --cov-report=term-missing

# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy apps/
```

### Testing

The project follows the mandatory 8-step process for all development:

1. Capture start time
2. Create BDD feature file
3. Create test fixtures
4. Run red test (verify failure)
5. Write implementation
6. Run green test (100% pass required)
7. Commit and push
8. Capture end time

```bash
# Run all tests
uv run pytest tests/

# Run performance tests
uv run pytest tests/ -m performance

# Run with property-based testing
uv run pytest tests/ --hypothesis-show-statistics
```

## Performance Requirements

- JavaScript dispatch operations: <16ms (60 FPS)
- Set operations: <10ms for 1,000 cards, <25ms for 5,000 cards
- HTML generation: <200ms complete response
- Memory usage: <500MB for 10,000 card workspace

## Architecture Compliance

All code must follow:
- Pure set theory operations using frozenset
- Functional programming (no classes for business logic)
- Immutable data structures
- Backend-only HTML generation
- HTMX-only frontend interactions
- Mathematical correctness for all filtering

## Documentation

- Architecture: `docs/architecture/001-2025-09-16-MultiCardz-JavaScript-Architecture-v1.md`
- Implementation: `docs/implementation/002-2025-09-16-MultiCardz-JavaScript-Implementation-Plan-v1.md`
- Standards: `docs/standards/elite-javascript-programming-standards.md`

## License

See patent documentation in `docs/patents/` for IP considerations.
