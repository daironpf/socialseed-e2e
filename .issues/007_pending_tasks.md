# Pending Tasks - Framework Improvements

**Created:** 2026-02-19
**Status:** Pending
**Agent:** minimax-m2.5-free

---

## Overview

This document tracks the pending tasks for the socialseed-e2e framework improvements. These tasks were identified during the architectural review and CLI refactoring sessions.

---

## High Priority Tasks

### 1. Complete CLI Modular Migration

**Description:** Migrate remaining commands from cli.py to modular structure

**Commands to migrate:**
- [ ] run_cmd.py - Test execution
- [ ] new_service_cmd.py - Create new service
- [ ] new_test_cmd.py - Create new test
- [ ] config_cmd.py - Show configuration
- [ ] lint_cmd.py - Validate tests
- [ ] set_url_cmd.py - Configure service URL
- [ ] install_demo_cmd.py - Install demos
- [ ] manifest_cmd.py - Generate project manifest

**Sub-commands to migrate (35+ remaining):**
- [ ] run tests
- [ ] ai-learning
- [ ] analyze-flaky
- [ ] autonomous-run
- [ ] build-index
- [ ] community
- [ ] dashboard
- [ ] debug-execution
- [ ] deep-scan
- [ ] discover
- [ ] generate-tests
- [ ] gherkin-translate
- [ ] healing-stats
- [ ] import-cmd
- [ ] install-extras
- [ ] mock-analyze
- [ ] mock-generate
- [ ] mock-run
- [ ] mock-validate
- [ ] plan-strategy
- [ ] recorder
- [ ] red-team
- [ ] regression
- [ ] security-test
- [ ] semantic-analyze
- [ ] set
- [ ] shadow
- [ ] setup-ci
- [ ] translate
- [ ] tui
- [ ] telemetry
- [ ] perf-profile
- [ ] perf-report
- [ ] watch

**Effort:** High (39 commands total)
**Dependencies:** None

---

### 2. Add Lazy Loading to Commands

**Description:** Implement lazy loading so commands are only loaded when invoked, improving startup time

**Tasks:**
- [ ] Modify commands/__init__.py to support lazy loading
- [ ] Update cli.py to use lazy command discovery
- [ ] Test startup time improvement

**Effort:** Medium
**Dependencies:** Task #1 partially complete

---

### 3. Implement Auto-Discovery

**Description:** Auto-discover commands from commands/ directory

**Tasks:**
- [ ] Create discovery mechanism in commands/__init__.py
- [ ] Remove manual registration requirement
- [ ] Test that all commands are discovered

**Effort:** Low
**Dependencies:** Task #2

---

## Medium Priority Tasks

### 4. Add Type Safety with MyPy

**Description:** Improve type annotations and add mypy to CI

**Tasks:**
- [ ] Fix LSP errors in cli.py (~30 errors)
- [ ] Fix LSP errors in project_manifest/api.py
- [ ] Fix LSP errors in nlp/code_generator.py
- [ ] Fix LSP errors in nlp/translator.py
- [ ] Add mypy to CI pipeline

**Effort:** Medium
**Dependencies:** None

---

### 5. Command Grouping

**Description:** Organize commands into logical groups

**Proposed structure:**
```
commands/
├── __init__.py
├── project/
│   ├── __init__.py
│   ├── init_cmd.py
│   ├── new_service_cmd.py
│   └── new_test_cmd.py
├── test/
│   ├── __init__.py
│   ├── run_cmd.py
│   ├── lint_cmd.py
│   └── ...
├── config/
│   ├── __init__.py
│   ├── config_cmd.py
│   ├── set_cmd.py
│   └── doctor_cmd.py
└── ai/
    ├── __init__.py
    ├── generate_tests_cmd.py
    ├── analyze_flaky_cmd.py
    └── ...
```

**Effort:** Medium
**Dependencies:** Task #1 complete

---

### 6. Performance Optimization

**Description:** Optimize test suite execution time

**Tasks:**
- [ ] Mark slow tests with @pytest.mark.slow
- [ ] Enable pytest-xdist parallel execution
- [ ] Split tests: unit / integration / e2e
- [ ] Add CI pipeline for each test type

**Effort:** Low
**Dependencies:** None

---

## Low Priority Tasks

### 7. Unify Manifest Locations

**Description:** Consolidate multiple manifest locations into one

**Current locations:**
- `/manifests/<service>/`
- `src/manifests/<service>/`
- `.e2e/`

**Proposed:** Single location in project root or `.e2e/manifests/`

**Effort:** Low
**Dependencies:** None

---

### 8. Add More Examples

**Description:** Add more command examples to docs

**Tasks:**
- [ ] Add run_cmd.py example
- [ ] Add new_service_cmd.py example
- [ ] Add config_cmd.py example

**Effort:** Low
**Dependencies:** Task #1 for examples

---

## Completed Tasks (Reference)

These tasks were completed in previous sessions:

- ✅ Dependencies reorganization (grpcio, flask to optional)
- ✅ CLI architecture documentation (docs/cli-architecture.md)
- ✅ Command template (commands/template_cmd.py)
- ✅ Command registry (commands/__init__.py)
- ✅ Architectural review (ARCHITECTURAL_REVIEW.md)
- ✅ Agent documentation (TROUBLESHOOTING.md, REST_TESTING.md, GRPC_TESTING.md)
- ✅ Config loader null handling fix

---

## Notes

- The CLI monolith (8245 lines) remains unchanged for backward compatibility
- New commands should be created in the modular format
- Focus on high priority tasks first to improve maintainability

---

## Quick Start for Tomorrow

To continue working on these tasks:

```bash
# 1. Check current state
python3 -m socialseed_e2e --version
python3 -m socialseed_e2e --help

# 2. Start with CLI migration
# Edit cli.py to remove a command, add to commands/<name>_cmd.py

# 3. Test changes
python3 -m socialseed_e2e <command> --help

# 4. Run tests
pytest tests/ -v --tb=short
```

---

*Last updated: 2026-02-19*
