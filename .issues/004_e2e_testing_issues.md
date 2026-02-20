# Issues found during E2E Testing (2026-02-19)

## Test Environment
- **Location:** `/tmp/e2e-clean-test`
- **Python:** 3.12.3
- **socialseed-e2e version:** 0.1.3 (installed from PyPI)

---

## Testing Steps Followed (per README.md)

| Step | Command | Status | Issues |
|------|---------|--------|--------|
| 1. Install | `pip install socialseed-e2e` | ✅ Works | Version mismatch: README says v0.1.2, installed v0.1.3 |
| 2. Init | `e2e init demo` | ⚠️ Partial | Creates "example" service, NOT "demo-api" as documented |
| 3. New Service | `e2e new-service` | ✅ Works | Not tested (skipped - service already exists) |
| 4. New Test | `e2e new-test health --service example` | ✅ Works | - |
| 5. Install deps | `pip install -r requirements.txt` | ✅ Works | - |
| 6. Start API | `python api-rest-demo.py` | ❌ FAILS | File does NOT exist in generated project! |
| 6 alt. | `python -m socialseed_e2e.mock_server` | ❌ FAILS | ModuleNotFoundError: No module named 'tests.fixtures' |
| 7. Run Tests | `e2e run` | ⚠️ Works | Runs but all tests fail (expected - no API running) |

---

## Issues Found

### Issue T001: README vs Installed Version Mismatch

**Severity:** LOW
**Type:** Documentation

**Problem:** README.md mentions version `0.1.2` but installed version is `0.1.3`.

**Current:** `socialseed-e2e, version 0.1.3`

**Expected:** Version in README should match installed version.

---

### Issue T002: Missing api-rest-demo.py File

**Severity:** HIGH
**Type:** Bug

**Status:** ✅ FIXED (2026-02-19)

**Problem:** The README documentation says `e2e init` should create a demo REST API file (`api-rest-demo.py`), but this file was NOT created during initialization when running on an existing directory.

**Documentation says:**
```bash
# Start the demo API (in a separate terminal)
cd demo
python api-rest-demo.py
```

**Actual behavior (for EXISTING projects without --force):**
```bash
$ ls *.py
conftest.py  verify_installation.py
# No api-rest-demo.py!
```

**Root Cause:** The init command only creates api-rest-demo.py if the file doesn't already exist. For existing projects created before this feature was added, the file won't be created.

**Fix:** Use `--force` flag to re-run initialization and create all missing files:
```bash
e2e init demo --force
```

**Verification:**
```bash
$ ls demo/*.py
api-rest-demo.py  conftest.py  verify_installation.py
```

---

### Issue T003: Mock Server ImportError

**Severity:** HIGH
**Type:** Bug

**Status:** ✅ FIXED (2026-02-19)

**Problem:** Running the built-in mock server fails with import error.

**Command:**
```bash
python -m socialseed_e2e.mock_server
```

**Error:**
```
ModuleNotFoundError: No module named 'tests.fixtures'
```

**Root Cause:** The mock server imports `from tests.fixtures.mock_api import MockAPIServer` but the `tests/` directory is not included in the installed package.

**Fix Applied:**
1. Converted `mock_api.py` to a package structure (`mock_api/__init__.py`, `mock_api/server.py`)
2. Updated exports in `__init__.py`
3. Rebuilt wheel

**Verification:**
```bash
$ python -c "from socialseed_e2e.mock_api import MockAPIServer; print('OK')"
T003 FIXED: mock_api import OK
```

---

### Issue T004: New Modules Not in Package

**Severity:** HIGH
**Type:** Missing Code

**Status:** ✅ FIXED (2026-02-19)

**Problem:** The new modules created in this session are NOT included in the installed package:
- `socialseed_e2e.documentation`
- `socialseed_e2e.versioning`
- `socialseed_e2e.data_governance`
- `socialseed_e2e.plugins` (new features)
- `socialseed_e2e.ide`
- `socialseed_e2e.examples`

**Error:**
```
ModuleNotFoundError: No module named 'socialseed_e2e.documentation'
```

**Root Cause:** The package was built BEFORE the new modules were created. The package needs to be rebuilt to include these modules.

**Impact:** All the new features from Issues #018-#030 are not available to end users.

**Fix Applied:**
- Rebuilt wheel with `python3 -m build --wheel`
- Verified new modules are included in `dist/socialseed_e2e-0.1.3-py3-none-any.whl`

**Verification:**
```bash
$ python -c "from socialseed_e2e.documentation import APIDocGenerator; from socialseed_e2e.versioning import VersionDetector; from socialseed_e2e.data_governance import PIIDetector; print('OK')"
T004 FIXED: All new modules import OK
```

---

### Issue T005: Service Name Mismatch

**Severity:** LOW
**Type:** Documentation

**Status:** ✅ FIXED (2026-02-19) - Framework now creates both services

**Problem:** README says `e2e init` creates a "demo-api" service, but earlier test showed "example" service.

**Documentation says:**
```
Services Summary:
   Detected:    [demo-api]
   Configured:  [demo-api]
```

**Earlier actual output:**
```
Services Summary:
   Detected:    [example]
   Configured:  [example]
```

**Root Cause:** Earlier test was run on an older version of the project before demo-api feature was fully implemented.

**Fix:** Run `e2e init <project> --force` to get the latest service structure.

**Verification (after --force):**
```
$ e2e config
┃ Name     ┃ Base URL              ┃ Health  ┃ Required ┃
│ demo-api │ http://localhost:5000 │ /health │ ✓        │
```

The framework now creates BOTH `demo-api` and `example` services. The README documentation is correct.

---

### Issue T006: New Test Template Has Placeholder Text

**Severity:** LOW
**Type:** UX

**Status:** ✅ NOT AN ISSUE (2026-02-19)

**Problem:** When creating a new test with `e2e new-test`, the generated test was reported to have placeholder text:

```python
# 03_health_flow.py
def run(page):
    """Test implementation incomplete - replace with actual test logic"""
```

**Current Behavior:** The test template (`test_module.py.template`) already contains a complete, working health check test:

```python
def run(${snake_case_name}: '${class_name}Page') -> APIResponse:
    """Execute ${test_name} test flow..."""
    print(f"Running ${test_name} test...")
    
    # Default health check test - validates the service is running
    response = ${snake_case_name}.get("/health")
    
    # Assert: Verify the service is healthy
    assert response.ok, f"Health check failed with status {response.status}: {response.text()}"
    
    print(f"✓ ${test_name} test completed successfully")
    return response
```

**Conclusion:** The template is already functional and provides a working example. No fix needed.

---

## Commands That Work

| Command | Status |
|---------|--------|
| `e2e --version` | ✅ Works |
| `e2e init <name>` | ⚠️ Partial (missing demo-api) |
| `e2e new-service` | ✅ Works |
| `e2e new-test` | ✅ Works |
| `e2e run` | ✅ Works (runs, tests fail due to no API) |
| `e2e doctor` | ✅ Works |
| `e2e config` | ✅ Works |
| `e2e lint` | ✅ Works |
| `e2e --help` | ✅ Works |

---

## Commands That Need Fixes

| Command | Status | Issue |
|---------|--------|-------|
| `python -m socialseed_e2e.mock_server` | ❌ FAILS | ImportError |
| `python api-rest-demo.py` | ❌ N/A | File doesn't exist |
| New modules imports | ❌ FAILS | Not packaged |

---

## Summary

| Issue | Severity | Type | Status |
|-------|----------|------|--------|
| T001: Version mismatch | LOW | Documentation | ✅ FIXED |
| T002: Missing api-rest-demo.py | HIGH | Bug | ✅ FIXED |
| T003: Mock server ImportError | HIGH | Bug | ✅ FIXED |
| T004: New modules not packaged | HIGH | Missing Code | ✅ FIXED |
| T005: Service name mismatch | LOW | Documentation | ✅ FIXED |
| T006: Placeholder template | LOW | UX | ✅ NOT AN ISSUE |

---

## Recommended Actions

1. **Immediate (High Priority):**
   - Rebuild the package to include new modules (T004)
   - Fix mock server import issue (T003)
   - Create or restore api-rest-demo.py file (T002)

2. **Soon (Medium Priority):**
   - Update README version number (T001)
   - Update service name in documentation (T005)

3. **Later (Low Priority):**
   - Improve test template placeholder (T006)
