# Pre-Commit Architectural Purity Hooks

**Document Version**: 1.0
**Date**: 2025-09-16
**Author**: System Architect
**Status**: IMPLEMENTATION COMPLETE

---

## Overview

multicardz enforces architectural purity through comprehensive pre-commit hooks that validate every code change against our core architectural principles. These hooks prevent violations of patent compliance, state management rules, and technology restrictions before they enter the codebase.

## Installation and Setup

### Initial Setup
```bash
# Install pre-commit (already in pyproject.toml)
uv add pre-commit --dev

# Install hooks to .git/hooks/
uv run pre-commit install

# Run hooks on all files
uv run pre-commit run --all-files
```

### Manual Hook Execution
```bash
# Test specific validator
uv run python scripts/validate_no_classes.py apps/shared/models/card.py

# Test all validators on specific file
uv run python scripts/validate_*.py test_file.py

# Run only architectural validators
uv run pre-commit run --hook-stage manual
```

## Architectural Validators

### 1. No Classes Validator (`validate_no_classes.py`)

**Purpose**: Enforces function-first architecture by blocking unauthorized class usage.

**Allowed Classes**:
- Pydantic models (`BaseModel` subclasses)
- SQLAlchemy models
- Test fixtures and pytest classes
- Required external library patterns

**Prohibited**:
- Business logic classes
- Service classes
- Controller classes
- State management classes

**Example Violation**:
```python
# ❌ VIOLATION
class CardService:
    def filter_cards(self, cards):
        return [card for card in cards]

# ✅ CORRECT
def filter_cards(cards: FrozenSet[Card]) -> FrozenSet[Card]:
    return cards.intersection(frozenset())
```

### 2. Set Theory Validator (`validate_set_theory.py`)

**Purpose**: Ensures patent compliance by enforcing pure set theory operations for all filtering.

**Required Operations**:
- `frozenset.intersection()` for AND operations
- `frozenset.union()` for OR operations
- `frozenset.difference()` for NOT operations
- `frozenset.symmetric_difference()` for XOR operations

**Prohibited**:
- List comprehensions for filtering
- Dictionary lookups for tag operations
- Pandas/numpy for tag filtering
- `filter()`, `map()`, `reduce()` functions

**Example Violation**:
```python
# ❌ VIOLATION
def filter_urgent_cards(cards):
    return [card for card in cards if "urgent" in card.tags]

# ✅ CORRECT
def filter_urgent_cards(cards: FrozenSet[Card]) -> FrozenSet[Card]:
    urgent_filter = frozenset(["urgent"])
    return frozenset(card for card in cards
                    if card.tags.intersection(urgent_filter))
```

### 3. JavaScript Restrictions Validator (`validate_javascript.py`)

**Purpose**: Enforces minimal JavaScript usage aligned with HTMX-first architecture.

**Allowed JavaScript**:
- Web Components (custom elements extending HTMLElement)
- ViewTransitions API (`document.startViewTransition`)
- HTMX integration code

**Prohibited**:
- JavaScript frameworks (React, Vue, Angular, jQuery)
- Direct DOM manipulation outside Web Components
- Client-side state management
- AJAX/fetch outside HTMX
- Client-side routing

**Example Violation**:
```javascript
// ❌ VIOLATION
import React from 'react';
$('.card').click(function() { /* ... */ });

// ✅ CORRECT
class CardComponent extends HTMLElement {
    connectedCallback() {
        this.attachShadow({mode: 'open'});
    }
}
customElements.define('card-component', CardComponent);
```

### 4. Immutability Validator (`validate_immutability.py`)

**Purpose**: Ensures data integrity through immutability patterns.

**Requirements**:
- All Pydantic models must have `frozen=True`
- Use `FrozenSet` instead of `List`/`Set` for collections
- No mutable default arguments
- No global mutable state
- No parameter mutation

**Example Violation**:
```python
# ❌ VIOLATION
class Card(BaseModel):
    tags: List[str] = []  # Mutable default

def process_cards(cards):
    cards.append(new_card)  # Parameter mutation

# ✅ CORRECT
class Card(BaseModel):
    tags: FrozenSet[str] = Field(default_factory=frozenset)

    model_config = {"frozen": True}

def process_cards(cards: FrozenSet[Card]) -> FrozenSet[Card]:
    return cards.union(frozenset([new_card]))
```

### 5. Import Control Validator (`validate_imports.py`)

**Purpose**: Controls technology stack and prevents architectural violations through dependency analysis.

**Approved Packages**:
- Core: FastAPI, Pydantic, SQLAlchemy, HTMX
- Database: SQLite, Alembic
- Development: pytest, ruff, mypy
- Production: Granian (ASGI server)

**Prohibited Packages**:
- Other web frameworks (Django, Flask, Tornado)
- JavaScript frameworks (React, Vue, Angular, jQuery)
- Heavy ML libraries (numpy, pandas, tensorflow)
- Alternative databases (PostgreSQL, MongoDB, Redis)

**Example Violation**:
```python
# ❌ VIOLATION
import pandas as pd
import react
from django.http import HttpResponse

# ✅ CORRECT
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine
```

### 6. Two-Tier Architecture Validator (`validate_two_tier.py`)

**Purpose**: Enforces optimal performance through proper CardSummary/CardDetail usage.

**Rules**:
- Use `CardSummary` for list operations and bulk handling
- Use `CardDetail` only for on-demand individual card operations
- No mixing of tiers in inappropriate contexts
- Proper lazy loading patterns

**Example Violation**:
```python
# ❌ VIOLATION
def get_all_cards():
    return [CardDetail(id=i, content="...") for i in range(1000)]

# ✅ CORRECT
def get_all_cards():
    return [CardSummary(id=i, title="Card") for i in range(1000)]

def get_card_detail(card_id: str):
    return CardDetail.load(card_id)  # Lazy loading
```

## Hook Configuration

The hooks are configured in `.pre-commit-config.yaml`:

```yaml
repos:
  # Standard tools
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Custom architectural validators
  - repo: local
    hooks:
      - id: validate-no-classes
        name: Architectural Purity - No Classes
        entry: python scripts/validate_no_classes.py
        language: system
        files: '\\.py$'
        exclude: '^(tests/|apps/shared/models/)'
```

## Bypassing Hooks (Emergency Only)

### Temporary Skip
```bash
# Skip hooks for emergency commit
git commit --no-verify -m "Emergency fix"

# Skip specific hook
SKIP=validate-no-classes git commit -m "Legitimate class addition"
```

### Permanent Exclusions
Add to `.pre-commit-config.yaml`:
```yaml
exclude: '^(legacy/|external/|vendor/)'
```

## Error Messages and Guidance

Each validator provides specific architectural guidance:

```
🚫 ARCHITECTURAL PURITY VIOLATION: Unauthorized Classes Found
============================================================

test.py:10: Unauthorized class 'BadBusinessLogic'
  Architecture violation: Use functions instead of classes

ARCHITECTURAL GUIDANCE:
• Use pure functions instead of classes for business logic
• Classes are ONLY allowed for:
  - Pydantic models (data validation)
  - SQLAlchemy models (database mapping)
  - Test fixtures and pytest classes
```

## Development Workflow

### 1. Write Code
```python
# Write new functionality following architectural principles
def filter_cards_by_tags(cards: FrozenSet[Card], tags: FrozenSet[str]) -> FrozenSet[Card]:
    return frozenset(card for card in cards if card.tags.intersection(tags))
```

### 2. Commit Triggers Validation
```bash
git add .
git commit -m "Add card filtering function"
# Hooks run automatically, check for violations
```

### 3. Fix Violations if Any
```bash
# Hooks provide specific guidance for fixes
# Update code to comply with architectural principles
```

### 4. Successful Commit
```bash
# All hooks pass - commit is allowed
[main abc1234] Add card filtering function
```

## Benefits

**Patent Compliance**: Automatic verification of set theory operations
**Performance**: Enforces two-tier lazy loading patterns
**Architecture Purity**: Prevents classes and state management violations
**Technology Control**: Blocks unauthorized dependencies
**Consistency**: Ensures all code follows identical patterns
**Education**: Provides guidance on proper architectural patterns

## Maintenance

### Adding New Validators
1. Create new script in `scripts/validate_*.py`
2. Follow existing validator patterns
3. Add to `.pre-commit-config.yaml`
4. Document in this guide

### Updating Validators
1. Modify validator logic
2. Test on existing codebase
3. Update documentation
4. Communicate changes to team

The pre-commit hooks ensure every code change maintains architectural purity and patent compliance automatically.
