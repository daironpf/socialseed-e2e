"""Tests for ModuleLoader.

This module contains unit tests for the ModuleLoader class which handles
dynamic loading of Python modules from file paths.
"""

import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from socialseed_e2e.core.loaders import ModuleLoader


class TestModuleLoaderInitialization:
    """Test cases for ModuleLoader initialization."""

    def test_loader_initialization(self):
        """Test that ModuleLoader can be instantiated."""
        loader = ModuleLoader()
        assert loader is not None
        assert isinstance(loader, ModuleLoader)


class TestLoadRunnableFromFile:
    """Test cases for load_runnable_from_file method."""

    def test_load_valid_runnable(self, tmp_path):
        """Test loading a valid runnable function from a file."""
        # Create a test module file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def run():
    return "Hello from test module"
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is not None
        assert callable(func)
        assert func() == "Hello from test module"

    def test_load_with_custom_function_name(self, tmp_path):
        """Test loading a function with custom name."""
        test_file = tmp_path / "custom_module.py"
        test_file.write_text("""
def custom_func():
    return "Custom function"
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file, function_name="custom_func")

        assert func is not None
        assert func() == "Custom function"

    def test_load_nonexistent_file_returns_none(self):
        """Test that loading a non-existent file returns None."""
        loader = ModuleLoader()
        func = loader.load_runnable_from_file(Path("/nonexistent/path/module.py"))

        assert func is None

    def test_load_non_python_file_returns_none(self, tmp_path):
        """Test that loading a non-Python file returns None."""
        text_file = tmp_path / "module.txt"
        text_file.write_text("This is not Python code")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(text_file)

        assert func is None

    def test_load_file_without_function_returns_none(self, tmp_path):
        """Test that loading a file without the target function returns None."""
        test_file = tmp_path / "no_run_module.py"
        test_file.write_text("""
def other_func():
    return "Not the run function"
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file, function_name="run")

        assert func is None

    def test_load_file_with_non_callable_run_returns_none(self, tmp_path):
        """Test that loading a file where 'run' is not callable returns None."""
        test_file = tmp_path / "non_callable_run.py"
        test_file.write_text("""
run = "This is a string, not a function"
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is None

    def test_load_module_with_imports(self, tmp_path):
        """Test loading a module that imports other modules."""
        test_file = tmp_path / "import_module.py"
        test_file.write_text("""
import os

def run():
    return f"Current directory: {os.getcwd()}"
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is not None
        assert callable(func)
        result = func()
        assert "Current directory:" in result

    def test_load_module_with_multiple_functions(self, tmp_path):
        """Test loading a module with multiple functions."""
        test_file = tmp_path / "multi_func_module.py"
        test_file.write_text("""
def helper():
    return "helper"

def run():
    return f"run with {helper()}"

def another():
    return "another"
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is not None
        assert func() == "run with helper"

    def test_load_module_with_classes(self, tmp_path):
        """Test loading a module that contains classes."""
        test_file = tmp_path / "class_module.py"
        test_file.write_text("""
class MyClass:
    def __init__(self):
        self.value = 42

    def get_value(self):
        return self.value

def run():
    obj = MyClass()
    return obj.get_value()
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is not None
        assert func() == 42


class TestLoadRunnableErrorHandling:
    """Test cases for error handling in load_runnable_from_file."""

    def test_load_corrupted_python_file(self, tmp_path, capsys):
        """Test handling of corrupted Python file with syntax errors."""
        test_file = tmp_path / "corrupted.py"
        test_file.write_text("""
def run(
    # Missing closing parenthesis and colon
    print("Broken")
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is None
        # Check that error was printed
        captured = capsys.readouterr()
        assert "Error loading" in captured.out or "Error loading" in captured.err

    def test_load_file_with_runtime_error_in_module(self, tmp_path, capsys):
        """Test handling of file with runtime errors during import."""
        test_file = tmp_path / "runtime_error.py"
        test_file.write_text("""
# This will raise an error during import
x = 1 / 0

def run():
    return "never reached"
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is None
        captured = capsys.readouterr()
        assert "Error loading" in captured.out or "Error loading" in captured.err

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty Python file."""
        test_file = tmp_path / "empty.py"
        test_file.write_text("")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is None

    def test_load_file_with_only_comments(self, tmp_path):
        """Test loading a file with only comments."""
        test_file = tmp_path / "comments_only.py"
        test_file.write_text("""
# This is a comment
# Another comment
# No actual code here
""")

        loader = ModuleLoader()
        func = loader.load_runnable_from_file(test_file)

        assert func is None


class TestDiscoverRunnables:
    """Test cases for discover_runnables method."""

    def test_discover_single_runnable(self, tmp_path):
        """Test discovering a single runnable in a directory."""
        test_file = tmp_path / "01_test.py"
        test_file.write_text("""
def run():
    return "test"
""")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        assert len(runnables) == 1
        assert runnables[0]() == "test"

    def test_discover_multiple_runnables(self, tmp_path):
        """Test discovering multiple runnables in a directory."""
        (tmp_path / "01_first.py").write_text("""
def run():
    return "first"
""")
        (tmp_path / "02_second.py").write_text("""
def run():
    return "second"
""")
        (tmp_path / "03_third.py").write_text("""
def run():
    return "third"
""")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        assert len(runnables) == 3
        assert runnables[0]() == "first"
        assert runnables[1]() == "second"
        assert runnables[2]() == "third"

    def test_discover_runnables_alphabetical_order(self, tmp_path):
        """Test that runnables are discovered in alphabetical order."""
        # Create files in non-alphabetical order
        (tmp_path / "z_last.py").write_text("""
def run():
    return "z"
""")
        (tmp_path / "a_first.py").write_text("""
def run():
    return "a"
""")
        (tmp_path / "m_middle.py").write_text("""
def run():
    return "m"
""")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        assert len(runnables) == 3
        assert runnables[0]() == "a"
        assert runnables[1]() == "m"
        assert runnables[2]() == "z"

    def test_discover_skips_init_files(self, tmp_path):
        """Test that __init__.py files are skipped during discovery."""
        (tmp_path / "__init__.py").write_text("""
def run():
    return "init"
""")
        (tmp_path / "01_module.py").write_text("""
def run():
    return "module"
""")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        assert len(runnables) == 1
        assert runnables[0]() == "module"

    def test_discover_ignores_non_runnable_files(self, tmp_path):
        """Test that files without run function are ignored."""
        (tmp_path / "01_runnable.py").write_text("""
def run():
    return "runnable"
""")
        (tmp_path / "02_no_run.py").write_text("""
def other():
    return "other"
""")
        (tmp_path / "03_runnable.py").write_text("""
def run():
    return "another"
""")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        assert len(runnables) == 2

    def test_discover_with_custom_pattern(self, tmp_path):
        """Test discovering with custom file pattern."""
        (tmp_path / "test_01.py").write_text("""
def run():
    return "test1"
""")
        (tmp_path / "other_01.py").write_text("""
def run():
    return "other"
""")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path, pattern="test_*.py")

        assert len(runnables) == 1
        assert runnables[0]() == "test1"

    def test_discover_empty_directory(self, tmp_path):
        """Test discovering in an empty directory."""
        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        assert runnables == []
        assert isinstance(runnables, list)

    def test_discover_nonexistent_directory(self):
        """Test discovering in a non-existent directory."""
        loader = ModuleLoader()
        runnables = loader.discover_runnables(Path("/nonexistent/directory"))

        assert runnables == []
        assert isinstance(runnables, list)

    def test_discover_file_instead_of_directory(self, tmp_path):
        """Test discovering when path is a file instead of directory."""
        test_file = tmp_path / "not_a_directory.py"
        test_file.write_text("""
def run():
    return "test"
""")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(test_file)

        assert runnables == []

    def test_discover_mixed_valid_invalid_files(self, tmp_path, capsys):
        """Test discovering with mix of valid, invalid, and corrupted files."""
        (tmp_path / "01_valid.py").write_text("""
def run():
    return "valid"
""")
        (tmp_path / "02_no_run.py").write_text("""
def other():
    return "no run"
""")
        (tmp_path / "03_corrupted.py").write_text("""
def run(
    # Syntax error
""")
        (tmp_path / "04_valid.py").write_text("""
def run():
    return "also valid"
""")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        assert len(runnables) == 2
        assert runnables[0]() == "valid"
        assert runnables[1]() == "also valid"

        # Verify error was printed for corrupted file
        captured = capsys.readouterr()
        assert "Error loading" in captured.out or "Error loading" in captured.err


class TestDiscoverRunnablesEdgeCases:
    """Test edge cases for discover_runnables."""

    def test_discover_with_numeric_prefix_ordering(self, tmp_path):
        """Test that files are sorted alphabetically (string sort, not numeric)."""
        (tmp_path / "10_ten.py").write_text("def run(): return 'ten'")
        (tmp_path / "01_one.py").write_text("def run(): return 'one'")
        (tmp_path / "02_two.py").write_text("def run(): return 'two'")
        (tmp_path / "100_hundred.py").write_text("def run(): return 'hundred'")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        results = [f() for f in runnables]
        # String sort: "01" < "02" < "100" < "10" (alphabetical, not numeric)
        assert results == ["one", "two", "hundred", "ten"]

    def test_discover_nested_directories_not_traversed(self, tmp_path):
        """Test that nested directories are not traversed."""
        # Create nested structure
        nested = tmp_path / "nested"
        nested.mkdir()

        (tmp_path / "01_parent.py").write_text("def run(): return 'parent'")
        (nested / "02_child.py").write_text("def run(): return 'child'")

        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        # Only parent should be found
        assert len(runnables) == 1
        assert runnables[0]() == "parent"


class TestModuleLoaderIntegration:
    """Integration tests for ModuleLoader."""

    def test_full_workflow_single_module(self, tmp_path):
        """Test complete workflow with a single module."""
        # Create a realistic test module
        test_file = tmp_path / "01_login_test.py"
        test_file.write_text("""
# Simulates a login test module

def setup():
    return "setup done"

def run():
    setup_result = setup()
    return f"Login test executed: {setup_result}"

def teardown():
    return "teardown done"
""")

        # Load the module
        loader = ModuleLoader()
        run_func = loader.load_runnable_from_file(test_file)

        assert run_func is not None
        result = run_func()
        assert "Login test executed" in result
        assert "setup done" in result

    def test_full_workflow_multiple_modules(self, tmp_path):
        """Test complete workflow with multiple modules simulating test suite."""
        # Create a suite of test modules
        modules = [
            ("01_setup.py", "def run(): return '01: Setup'"),
            ("02_auth.py", "def run(): return '02: Auth'"),
            ("03_test.py", "def run(): return '03: Test'"),
            ("04_cleanup.py", "def run(): return '04: Cleanup'"),
        ]

        for filename, content in modules:
            (tmp_path / filename).write_text(content)

        # Discover all modules
        loader = ModuleLoader()
        runnables = loader.discover_runnables(tmp_path)

        # Execute all in order
        results = [f() for f in runnables]

        assert len(results) == 4
        assert results[0] == "01: Setup"
        assert results[1] == "02: Auth"
        assert results[2] == "03: Test"
        assert results[3] == "04: Cleanup"

    def test_reload_same_module_different_instance(self, tmp_path):
        """Test that loading the same file creates a fresh module instance."""
        test_file = tmp_path / "stateful.py"
        test_file.write_text("""
counter = 0

def run():
    global counter
    counter += 1
    return counter
""")

        loader = ModuleLoader()

        # Load and call first time
        func1 = loader.load_runnable_from_file(test_file)
        result1 = func1()

        # Load again (should be fresh instance)
        func2 = loader.load_runnable_from_file(test_file)
        result2 = func2()

        # Both should return 1 because they're separate module instances
        assert result1 == 1
        assert result2 == 1
