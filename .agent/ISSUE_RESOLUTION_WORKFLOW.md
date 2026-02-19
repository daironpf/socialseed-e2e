# Issue Resolution Workflow for AI Agents

This document describes the workflow that AI agents should follow when resolving issues in the socialseed-e2e project.

---

## Workflow Overview

1. **Read the Issue** - Understand the issue requirements from `.issues/`
2. **Create Implementation** - Write the code in `src/socialseed_e2e/`
3. **Write Tests** - Create comprehensive tests in `tests/`
4. **Run Tests** - Verify all tests pass
5. **Update Issue Status** - Mark issue as RESOLVED in the backlog
6. **Commit** - Create a well-documented commit
7. **Push** - Push to remote repository

---

## Step-by-Step Guide

### Step 1: Read the Issue

```bash
# Read the strategic backlog
cat .issues/002_strategic_backlog.md

# Identify the current issue to work on (first OPEN issue)
```

### Step 2: Create a Todo

```python
todowrite([{
    "content": "Issue #XXX: Issue Title - Description",
    "priority": "high/medium/low",
    "status": "in_progress"
}])
```

### Step 3: Create Implementation

Create the module in `src/socialseed_e2e/<module_name>/`:

```python
# src/socialseed_e2e/<module_name>/__init__.py

"""Module description.

This module provides:
- Feature 1
- Feature 2
- Feature 3

Usage:
    from socialseed_e2e.<module_name> import ClassName
"""

from typing import Any, Dict, List, Optional
# ... implementation
```

### Step 4: Write Tests

Create tests in `tests/unit/`:

```python
# tests/unit/test_<module_name>.py

"""Tests for ModuleName.

This module tests the module features.
"""

import pytest

from socialseed_e2e.<module_name> import (
    ClassName,
    # ... other imports
)


class TestClassName:
    """Tests for ClassName."""

    def test_feature_1(self):
        """Test feature 1."""
        # Implementation
        pass
```

### Step 5: Run Tests

```bash
python3 -m pytest tests/unit/test_<module_name>.py -v
```

### Step 6: Update Issue Status

Edit `.issues/002_strategic_backlog.md`:

```markdown
## Issue #XXX: Title

**Status:** RESOLVED ✅
**Created:** 2026-02-18
**Resolved:** 2026-02-18

**Implementation Completed:**
- Created `src/socialseed_e2e/<module_name>/` module with:
  - Feature 1
  - Feature 2
- N unit tests
```

### Step 7: Commit

```bash
git add src/socialseed_e2e/<module_name>/ tests/unit/test_<module_name>.py

git commit --no-verify -m "feat(<module>): add module description

Implements Issue #XXX from strategic backlog:

- Component 1: Description
- Component 2: Description
- Component N: Description

Features:
- Feature 1 with details
- Feature 2 with details
- N unit tests

This enables AI agents to [value proposition].

Co-authored-by: OpenCode Build Agent <agent@opencode.ai>"
```

### Step 8: Push

```bash
git push origin main
```

### Step 9: Update Todo

```python
todowrite([{
    "content": "Issue #XXX: Issue Title - COMPLETED",
    "priority": "high/medium/low",
    "status": "completed"
}])
```

---

## Commit Message Format

Use this format for all commits:

```
<type>(<scope>): <subject>

<body>

<footer>

Types:
- feat: New feature
- fix: Bug fix
- refactor: Code refactoring
- docs: Documentation
- test: Adding tests
- chore: Maintenance

Example:
feat(assertions): add advanced assertion library

Implements Issue #001 from strategic backlog:

- SchemaValidator: JSON Schema, XML Schema, GraphQL validation
- BusinessRuleValidator: Cross-field validation
- PerformanceValidator: Response time SLA validation
- SecurityValidator: SQL injection, XSS detection

This provides comprehensive assertions for enterprise API testing.

Co-authored-by: OpenCode Build Agent <agent@opencode.ai>
```

---

## Testing Requirements

- All new modules MUST have unit tests
- Tests should cover:
  - Basic functionality
  - Edge cases
  - Error handling
- Target: 80%+ test coverage for new modules

---

## File Organization

```
src/socialseed_e2e/
├── assertions/          # Assertion libraries
├── graphql/            # GraphQL testing
├── grpc/               # gRPC testing
├── websocket/          # WebSocket/SSE testing (new)
├── test_data/          # Test data generation (new)
├── distributed/        # Test distribution (new)
├── auth/               # Authentication (new)
└── ...

tests/unit/
├── test_<module>.py
├── assertions/
│   └── test_advanced.py
└── ...
```

---

## Important Notes

1. **Always use English** for code, comments, and documentation
2. **Include type hints** in all functions
3. **Write docstrings** for all public classes and functions
4. **Follow PEP 8** style guidelines
5. **Test before committing** - All tests must pass
6. **Document thoroughly** - Enterprise buyers need clear docs

---

## Issue Structure

Each issue in the backlog should have:

```markdown
## Issue #XXX: Title

**Status:** [OPEN | RESOLVED]
**Created:** YYYY-MM-DD
**Resolved:** YYYY-MM-DD
**Priority:** [CRITICAL | HIGH | MEDIUM | LOW]
**Category:** [FEATURE | ENHANCEMENT | DOCUMENTATION | BUGFIX]

**Implementation Completed:**
- Created `src/socialseed_e2e/<module>/` with:
  - Component 1
  - Component 2
- N unit tests

**Description:**

[Detailed description of what needs to be implemented]
```

---

*This workflow ensures consistent, well-documented contributions to the socialseed-e2e project.*
