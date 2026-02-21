#!/usr/bin/env python3
"""Verify that key fixes are applied.

This script verifies that the critical fixes for the release are in place.
Used by the GitHub release workflow.
"""

import sys
from pathlib import Path


def verify_fixes():
    """Verify that fixes are applied."""
    errors = []

    # Check 1: Version is bumped
    version_file = Path("src/socialseed_e2e/__version__.py")
    if version_file.exists():
        content = version_file.read_text()
        if '"0.1.5"' in content or "'0.1.5'" in content:
            print("✓ Version bumped to 0.1.5")
        else:
            errors.append("Version not bumped to 0.1.5")
    else:
        errors.append("Version file not found")

    # Check 2: Test runner has kebab-case fix
    test_runner = Path("src/socialseed_e2e/core/test_runner.py")
    if test_runner.exists():
        content = test_runner.read_text()
        if "normalize_service_name" in content:
            print("✓ Service name normalization in test_runner.py")
        else:
            errors.append("Service name normalization not found")

    # Check 3: Commands module has lazy loading
    commands_init = Path("src/socialseed_e2e/commands/__init__.py")
    if commands_init.exists():
        content = commands_init.read_text()
        if "@register" in content:
            print("✓ Lazy loading with @register in commands/__init__.py")
        else:
            errors.append("Lazy loading not found")

    # Check 4: Project manifest API has unified location
    manifest_api = Path("src/socialseed_e2e/project_manifest/api.py")
    if manifest_api.exists():
        content = manifest_api.read_text()
        if ".e2e" in content and "manifests" in content:
            print("✓ Unified manifest location in project_manifest/api.py")
        else:
            errors.append("Unified manifest location not found")

    if errors:
        print("\n❌ Errors found:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\n✅ All fixes verified!")
    return 0


if __name__ == "__main__":
    sys.exit(verify_fixes())
