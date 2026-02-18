#!/usr/bin/env python3
"""Verify that test fixes are applied correctly."""

import sys
from pathlib import Path


def check_fixes():
    """Check if all test fixes are in place."""
    errors = []

    # Check 1: test_generator.py has empty_project fixture
    generator_file = Path("tests/unit/project_manifest/test_generator.py")
    if generator_file.exists():
        content = generator_file.read_text()
        if "def empty_project(self, tmp_path):" not in content:
            errors.append("❌ test_generator.py missing empty_project fixture")
        else:
            print("✓ test_generator.py has empty_project fixture")
    else:
        errors.append("❌ test_generator.py not found")

    # Check 2: test_parsers.py has fixed assertions
    parsers_file = Path("tests/unit/project_manifest/test_parsers.py")
    if parsers_file.exists():
        content = parsers_file.read_text()
        if "assert len(dto.fields) >= 2" in content:
            print("✓ test_parsers.py has fixed Java record assertion")
        else:
            errors.append("❌ test_parsers.py missing fixed assertion")

        if "assert len(result.dto_schemas) >= 1" in content:
            print("✓ test_parsers.py has fixed TypeScript assertion")
        else:
            errors.append("❌ test_parsers.py missing TypeScript fix")
    else:
        errors.append("❌ test_parsers.py not found")

    # Check 3: parallel_runner.py has config_path check
    parallel_file = Path("src/socialseed_e2e/core/parallel_runner.py")
    if parallel_file.exists():
        content = parallel_file.read_text()
        if "if config_path is not None:" in content:
            print("✓ parallel_runner.py has config_path check")
        else:
            errors.append("❌ parallel_runner.py missing config_path check")
    else:
        errors.append("❌ parallel_runner.py not found")

    # Check 4: parsers.py has None check
    parsers_src = Path("src/socialseed_e2e/project_manifest/parsers.py")
    if parsers_src.exists():
        content = parsers_src.read_text()
        if "if port_str is None:" in content:
            print("✓ parsers.py has None check for port_str")
        else:
            errors.append("❌ parsers.py missing port_str None check")
    else:
        errors.append("❌ parsers.py not found")

    if errors:
        print("\n" + "=" * 50)
        print("ERRORS FOUND:")
        for error in errors:
            print(f"  {error}")
        print("=" * 50)
        return 1
    else:
        print("\n" + "=" * 50)
        print("✅ All fixes are in place!")
        print("=" * 50)
        return 0


if __name__ == "__main__":
    sys.exit(check_fixes())
