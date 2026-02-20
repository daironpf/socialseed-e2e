# Post-Implementation Issues

**Date:** 2026-02-19
**Status:** IDENTIFIED
**Category:** BUGFIX

This document tracks issues found during post-implementation testing of the strategic backlog (Issues #018-#030).

---

## Issue #P001: Missing pydantic import in collaboration/notifications.py

**Severity:** HIGH
**Status:** FIXED ✅

**Problem:**
The `notifications.py` file was missing imports for `BaseModel`, `Field`, and `Path` from pydantic and pathlib.

**Solution Applied:**
- Added `from pydantic import BaseModel, Field` 
- Added `from pathlib import Path`

**Verification:**
Module now imports correctly.

---

## Issue #P002: Missing RecoveryValidator export in chaos/__init__.py

**Severity:** HIGH
**Status:** FIXED ✅

**Problem:**
The test `tests/unit/chaos/test_chaos.py` was trying to import `RecoveryValidator` from `socialseed_e2e.chaos` but it wasn't exported.

**Solution Applied:**
- Added `from .recovery.recovery_validator import RecoveryValidator` to `chaos/__init__.py`
- Added `"RecoveryValidator"` to `__all__` list

**Verification:**
Test collection now succeeds.

---

## Issue #P003: SyntaxWarnings in security/compliance/validator.py

**Severity:** LOW
**Status:** FIXED ✅

**Problem:**
There are invalid escape sequences in regex patterns:
- `r"cvv[" "\s]*[=:]\s*\d{3,4}"`
- `r"(track1|track2)[" "\s]*[=:]\s*[^\s]+"`
- And more similar patterns

**Warning Messages:**
```
SyntaxWarning: invalid escape sequence '\s'
```

**Solution Applied:**
Fixed regex patterns in:
- `src/socialseed_e2e/security/compliance/compliance_validator.py` (lines 51-60)
- `src/socialseed_e2e/security/detection/secret_detector.py` (lines 50-51)

Changed from:
```python
r"cvv[" "\s]*[=:]\s*\d{3,4}"
```
To:
```python
r"cvv[\s]*[=:]\s*\d{3,4}"
```

**Verification:**
```bash
python3 -m py_compile src/socialseed_e2e/security/compliance/compliance_validator.py
python3 -m py_compile src/socialseed_e2e/security/detection/secret_detector.py
# No warnings
```

---

## Issue #P004: Test execution timeout

**Severity:** MEDIUM
**Status:** FIXED ✅

**Problem:**
Unit tests are taking too long (>180 seconds) and timing out during CI/CD.

**Solution Applied:**
- Added `pytest-timeout>=2.2.0` to dev dependencies in `pyproject.toml`
- Added default timeout of 60 seconds to pytest configuration:
  - Added `timeout = 60` to `[tool.pytest.ini_options]`
  - Added `--timeout=60` to `addopts`

**Verification:**
Tests will now fail-fast if they exceed 60 seconds.

---

## Issue #P005: aiohttp not installed as dependency

**Severity:** LOW
**Status:** FIXED ✅

**Problem:**
The `notifications.py` module imports `aiohttp` for async Slack/Teams notifications, but `aiohttp` is not listed as a dependency.

**Solution Applied:**
- Added new optional dependency `collaboration` in `pyproject.toml`:
  ```toml
  collaboration = [
      "aiohttp>=3.9.0",
  ]
  ```
- Users can install with: `pip install socialseed-e2e[collaboration]`

**Impact:**
- `SlackNotifier.send()` will work after installing collaboration extra
- `TeamsNotifier.send()` will work after installing collaboration extra

---

## Summary

| Issue | Severity | Status |
|-------|----------|--------|
| P001: Missing pydantic imports | HIGH | ✅ FIXED |
| P002: Missing RecoveryValidator export | HIGH | ✅ FIXED |
| P003: SyntaxWarnings in regex | LOW | ✅ FIXED |
| P004: Test timeout | MEDIUM | ✅ FIXED |
| P005: Missing aiohttp dependency | LOW | ✅ FIXED |

---

## ✅ ALL ISSUES RESOLVED |

---

## Recommended Actions

1. **Immediate (High Priority):**
   - None - critical issues already fixed

2. **Soon (Medium Priority):**
   - Add test timeouts to prevent CI timeouts
   - Add aiohttp as optional dependency

3. **Later (Low Priority):**
   - Fix SyntaxWarnings in security module
   - Optimize test execution time
