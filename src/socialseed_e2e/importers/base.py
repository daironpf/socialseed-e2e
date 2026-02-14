"""Base importer class for all format importers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional


class ImportError(Exception):
    """Exception raised when import fails."""

    pass


class ImportResult:
    """Result of an import operation."""

    def __init__(
        self,
        success: bool,
        message: str,
        tests: Optional[List[Dict]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.success = success
        self.message = message
        self.tests = tests or []
        self.warnings = warnings or []

    def __repr__(self):
        return f"ImportResult(success={self.success}, tests={len(self.tests)}, warnings={len(self.warnings)})"


class BaseImporter(ABC):
    """Base class for all importers."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("services/imported")
        self.warnings: List[str] = []

    @abstractmethod
    def import_file(self, file_path: Path) -> ImportResult:
        """Import from a file and return ImportResult."""
        pass

    @abstractmethod
    def generate_code(self, data: Dict) -> str:
        """Generate Python test code from imported data."""
        pass

    def _sanitize_name(self, name: str) -> str:
        """Convert name to valid Python identifier."""
        import re

        # Remove invalid characters
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        # Ensure it starts with letter
        if sanitized and sanitized[0].isdigit():
            sanitized = f"test_{sanitized}"
        # Remove consecutive underscores
        sanitized = re.sub(r"_+", "_", sanitized)
        # Remove trailing underscore
        sanitized = sanitized.rstrip("_")
        return sanitized.lower() or "test_case"

    def _write_test_file(self, test_name: str, content: str) -> Path:
        """Write generated test to file."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.output_dir / f"{test_name}.py"
        file_path.write_text(content)
        return file_path

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
