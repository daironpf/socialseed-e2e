"""Installation verification script for socialseed-e2e framework.

This script verifies that the framework is properly installed and configured,
and that all components work correctly.

Usage:
    python verify_installation.py

Or after e2e init:
    python verify_setup.py
"""

import importlib
import sys
from pathlib import Path


def check_color(text: str, color: str) -> str:
    """Add color to text for terminal output."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_check(name: str, status: bool, message: str = ""):
    """Print a check result."""
    symbol = "✓" if status else "✗"
    color = "green" if status else "red"
    msg = f" - {message}" if message else ""
    print(f"  {check_color(symbol, color)} {name}{msg}")


def verify_installation():
    """Run all verification checks."""
    all_passed = True

    print("\n" + "=" * 60)
    print("  SocialSeed E2E Framework - Installation Verification")
    print("=" * 60)

    # 1. Check Python version
    print_section("Python Environment")
    version = sys.version_info
    python_ok = version.major == 3 and version.minor >= 10
    print_check(f"Python {version.major}.{version.minor}.{version.micro}", python_ok)
    all_passed = all_passed and python_ok

    # 2. Check required packages
    print_section("Required Packages")
    required_packages = [
        ("pydantic", "Pydantic v2"),
        ("email_validator", "Email Validator"),
    ]

    for package, display_name in required_packages:
        try:
            importlib.import_module(package)
            print_check(f"{display_name}", True)
        except ImportError:
            print_check(f"{display_name}", False, f"Not installed. Run: pip install {package}")
            all_passed = False

    # 3. Check framework packages
    print_section("Framework Packages")
    try:
        importlib.import_module("socialseed_e2e")
        print_check("socialseed_e2e (framework)", True)
    except ImportError:
        print_check("socialseed_e2e", False, "Framework not installed")
        print("  → Install with: pip install socialseed-e2e")
        all_passed = False

    # 4. Check project structure
    print_section("Project Structure")

    project_root = Path(".").resolve()
    required_paths = [
        ("e2e.conf", "Configuration file"),
        ("services/", "Services directory"),
        ("requirements.txt", "Dependencies file"),
        (".agent/AGENT_GUIDE.md", "AI Agent guide"),
        (".agent/EXAMPLE_TEST.md", "Example documentation"),
    ]

    for path, description in required_paths:
        full_path = project_root / path
        exists = full_path.exists()
        print_check(f"{path} ({description})", exists)
        if not exists:
            all_passed = False

    # 5. Test Pydantic alias serialization
    print_section("Pydantic Alias Serialization Test")
    try:
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            model_config = {"populate_by_name": True}
            field_name: str = Field(alias="fieldName", serialization_alias="fieldName")

        # Test serialization
        instance = TestModel(field_name="test")
        data = instance.model_dump(by_alias=True)

        if "fieldName" in data and data["fieldName"] == "test":
            print_check("CamelCase serialization", True)
        else:
            print_check("CamelCase serialization", False, "alias not working correctly")
            all_passed = False

        # Test deserialization
        instance2 = TestModel(fieldName="test2")
        if instance2.field_name == "test2":
            print_check("Field population by name", True)
        else:
            print_check("Field population by name", False, "populate_by_name not working")
            all_passed = False

    except Exception as e:
        print_check("Pydantic configuration", False, str(e))
        all_passed = False

    # 6. Check for common issues
    print_section("Common Issues Check")

    # Check for relative imports in services
    services_dir = project_root / "services"
    if services_dir.exists():
        has_relative_imports = False
        for py_file in services_dir.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                content = py_file.read_text()
                if "from .." in content or "from . import" in content:
                    if py_file.name != "__init__.py":
                        has_relative_imports = True
                        print_check(
                            f"Relative imports in {py_file}",
                            False,
                            "Use absolute imports",
                        )
            except Exception:
                pass

        if not has_relative_imports:
            print_check("No relative imports found", True)

    # 7. Services check
    print_section("Configured Services")
    if services_dir.exists():
        services = [d.name for d in services_dir.iterdir() if d.is_dir()]
        if services:
            for service in services:
                print_check(f"Service: {service}", True)
        else:
            print("  ℹ No services configured yet")
            print("  → Create with: e2e new-service <name>")

    # Final summary
    print("\n" + "=" * 60)
    if all_passed:
        print(check_color("  ✓ All checks passed! Installation is ready.", "green"))
        print("\n  🎉 You can now:")
        print("     • Run: e2e new-service <name> to create a service")
        print("     • Ask your AI agent to generate tests")
        print("     • Read .agent/AGENT_GUIDE.md for patterns")
    else:
        print(check_color("  ✗ Some checks failed. Please review issues above.", "red"))
        print("\n  🔧 To fix:")
        print("     • Install dependencies: pip install -r requirements.txt")
        print("     • Review .agent/AGENT_GUIDE.md for correct patterns")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)
