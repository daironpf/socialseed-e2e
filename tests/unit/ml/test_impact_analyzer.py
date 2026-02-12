"""Unit tests for ImpactAnalyzer.

Tests for the code impact analysis functionality.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from socialseed_e2e.ml.impact_analyzer import ImpactAnalyzer
from socialseed_e2e.ml.models import ChangeType, CodeChange, FileType, TestPriority


class TestImpactAnalyzerInit:
    """Test ImpactAnalyzer initialization."""

    def test_init_with_default_path(self):
        """Test initialization with default project root."""
        analyzer = ImpactAnalyzer()
        assert analyzer.project_root == Path.cwd()

    def test_init_with_custom_path(self):
        """Test initialization with custom project root."""
        custom_path = Path("/tmp/project")
        analyzer = ImpactAnalyzer(project_root=custom_path)
        assert analyzer.project_root == custom_path


class TestDetectFileType:
    """Test file type detection."""

    def test_detect_python_file(self):
        """Test detecting Python files."""
        analyzer = ImpactAnalyzer()
        assert analyzer._detect_file_type("test.py") == FileType.PYTHON
        assert analyzer._detect_file_type("src/app.py") == FileType.PYTHON

    def test_detect_javascript_file(self):
        """Test detecting JavaScript files."""
        analyzer = ImpactAnalyzer()
        assert analyzer._detect_file_type("app.js") == FileType.JAVASCRIPT

    def test_detect_typescript_file(self):
        """Test detecting TypeScript files."""
        analyzer = ImpactAnalyzer()
        assert analyzer._detect_file_type("app.ts") == FileType.TYPESCRIPT
        assert analyzer._detect_file_type("component.tsx") == FileType.TYPESCRIPT

    def test_detect_java_file(self):
        """Test detecting Java files."""
        analyzer = ImpactAnalyzer()
        assert analyzer._detect_file_type("Main.java") == FileType.JAVA

    def test_detect_config_file(self):
        """Test detecting config files."""
        analyzer = ImpactAnalyzer()
        assert analyzer._detect_file_type("config.json") == FileType.CONFIG
        assert analyzer._detect_file_type("settings.yaml") == FileType.CONFIG
        assert analyzer._detect_file_type("app.yml") == FileType.CONFIG

    def test_detect_test_file(self):
        """Test detecting test files."""
        analyzer = ImpactAnalyzer()
        assert analyzer._detect_file_type("test_app.py") == FileType.TEST

    def test_detect_other_file(self):
        """Test detecting other file types."""
        analyzer = ImpactAnalyzer()
        assert analyzer._detect_file_type("README.md") == FileType.OTHER
        assert analyzer._detect_file_type("Makefile") == FileType.OTHER


class TestParseChangeType:
    """Test git change type parsing."""

    def test_parse_added(self):
        """Test parsing added status."""
        analyzer = ImpactAnalyzer()
        assert analyzer._parse_change_type("A") == ChangeType.ADDED

    def test_parse_modified(self):
        """Test parsing modified status."""
        analyzer = ImpactAnalyzer()
        assert analyzer._parse_change_type("M") == ChangeType.MODIFIED

    def test_parse_deleted(self):
        """Test parsing deleted status."""
        analyzer = ImpactAnalyzer()
        assert analyzer._parse_change_type("D") == ChangeType.DELETED

    def test_parse_renamed(self):
        """Test parsing renamed status."""
        analyzer = ImpactAnalyzer()
        assert analyzer._parse_change_type("R100") == ChangeType.RENAMED
        assert analyzer._parse_change_type("R50") == ChangeType.RENAMED

    def test_parse_unknown_defaults_to_modified(self):
        """Test unknown status defaults to modified."""
        analyzer = ImpactAnalyzer()
        assert analyzer._parse_change_type("X") == ChangeType.MODIFIED
        assert analyzer._parse_change_type("") == ChangeType.MODIFIED


class TestIsTestFile:
    """Test test file detection."""

    def test_is_test_file_with_prefix(self):
        """Test detecting test files with prefix."""
        analyzer = ImpactAnalyzer()
        assert analyzer._is_test_file("test_app.py") is True

    def test_is_test_file_with_suffix(self):
        """Test detecting test files with suffix."""
        analyzer = ImpactAnalyzer()
        assert analyzer._is_test_file("app_test.py") is True

    def test_is_test_file_js_pattern(self):
        """Test detecting JS test files."""
        analyzer = ImpactAnalyzer()
        assert analyzer._is_test_file("app.test.js") is True
        assert analyzer._is_test_file("app.spec.js") is True

    def test_is_test_file_in_test_directory(self):
        """Test detecting test files in test directories."""
        analyzer = ImpactAnalyzer()
        assert analyzer._is_test_file("tests/test_app.py") is True
        assert analyzer._is_test_file("test/unit/app.py") is True

    def test_is_not_test_file(self):
        """Test non-test files."""
        analyzer = ImpactAnalyzer()
        assert analyzer._is_test_file("src/app.py") is False
        assert analyzer._is_test_file("main.py") is False


class TestCalculateImpactScore:
    """Test impact score calculation."""

    def test_empty_changes_zero_score(self):
        """Test empty changes result in zero score."""
        analyzer = ImpactAnalyzer()
        score = analyzer._calculate_impact_score([], [])
        assert score == 0.0

    def test_single_file_low_score(self):
        """Test single file change results in low score."""
        analyzer = ImpactAnalyzer()
        change = CodeChange(
            file_path="src/app.py",
            change_type=ChangeType.MODIFIED,
            lines_added=5,
            lines_deleted=2,
        )
        score = analyzer._calculate_impact_score([change], ["test_app.py"])
        assert 0.0 < score < 0.5

    def test_many_files_high_score(self):
        """Test many file changes result in higher score."""
        analyzer = ImpactAnalyzer()
        changes = [
            CodeChange(
                file_path=f"src/module{i}.py",
                change_type=ChangeType.MODIFIED,
                lines_added=20,
                lines_deleted=10,
            )
            for i in range(15)
        ]
        affected = [f"test_module{i}.py" for i in range(15)]
        score = analyzer._calculate_impact_score(changes, affected)
        assert score > 0.5

    def test_config_file_boosts_score(self):
        """Test config files boost impact score."""
        analyzer = ImpactAnalyzer()
        change = CodeChange(
            file_path="config.json",
            change_type=ChangeType.MODIFIED,
            file_type=FileType.CONFIG,
            lines_added=10,
        )
        score = analyzer._calculate_impact_score([change], [])
        assert score > 0.1  # Should be boosted by config file


class TestDetermineRiskLevel:
    """Test risk level determination."""

    def test_low_impact_low_risk(self):
        """Test low impact results in low risk."""
        analyzer = ImpactAnalyzer()
        change = CodeChange(
            file_path="docs/readme.md",
            change_type=ChangeType.MODIFIED,
        )
        risk = analyzer._determine_risk_level(0.1, [change])
        assert risk == TestPriority.LOW

    def test_medium_impact_medium_risk(self):
        """Test medium impact results in medium risk."""
        analyzer = ImpactAnalyzer()
        change = CodeChange(
            file_path="src/app.py",
            change_type=ChangeType.MODIFIED,
        )
        risk = analyzer._determine_risk_level(0.4, [change])
        assert risk == TestPriority.MEDIUM

    def test_high_impact_high_risk(self):
        """Test high impact results in high risk."""
        analyzer = ImpactAnalyzer()
        change = CodeChange(
            file_path="src/app.py",
            change_type=ChangeType.MODIFIED,
        )
        risk = analyzer._determine_risk_level(0.7, [change])
        assert risk == TestPriority.HIGH

    def test_critical_config_change(self):
        """Test config changes result in critical risk."""
        analyzer = ImpactAnalyzer()
        change = CodeChange(
            file_path="config.json",
            change_type=ChangeType.MODIFIED,
            file_type=FileType.CONFIG,
        )
        risk = analyzer._determine_risk_level(0.3, [change])
        assert risk == TestPriority.CRITICAL

    def test_deleted_file_critical(self):
        """Test deleted files result in critical risk."""
        analyzer = ImpactAnalyzer()
        change = CodeChange(
            file_path="src/app.py",
            change_type=ChangeType.DELETED,
        )
        risk = analyzer._determine_risk_level(0.3, [change])
        assert risk == TestPriority.CRITICAL


class TestAnalyzeGitDiff:
    """Test git diff analysis."""

    @patch("subprocess.run")
    def test_analyze_git_diff_success(self, mock_run):
        """Test successful git diff analysis."""
        # Mock git diff --name-status output
        mock_run.return_value = Mock(
            stdout="M\tsrc/app.py\nA\ttest_new.py",
            returncode=0,
        )

        analyzer = ImpactAnalyzer()

        # Mock _get_diff_stats to avoid additional subprocess calls
        with patch.object(analyzer, "_get_diff_stats", return_value=(10, 5)):
            with patch.object(analyzer, "_extract_changed_functions", return_value=[]):
                with patch.object(analyzer, "_extract_changed_classes", return_value=[]):
                    with patch.object(analyzer, "_extract_changed_imports", return_value=[]):
                        result = analyzer.analyze_git_diff()

        assert result.impact_score >= 0.0
        assert len(result.changed_files) == 2

    @patch("subprocess.run")
    def test_analyze_git_diff_no_changes(self, mock_run):
        """Test git diff with no changes."""
        mock_run.return_value = Mock(
            stdout="",
            returncode=0,
        )

        analyzer = ImpactAnalyzer()
        result = analyzer.analyze_git_diff()

        assert result.impact_score == 0.0
        assert len(result.changed_files) == 0

    @patch("subprocess.run")
    def test_analyze_git_diff_error(self, mock_run):
        """Test git diff with error."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        analyzer = ImpactAnalyzer()
        result = analyzer.analyze_git_diff()

        # Should return empty analysis on error
        assert result.impact_score == 0.0


class TestFindRelatedTests:
    """Test finding related tests."""

    def test_find_related_test_same_name(self, tmp_path):
        """Test finding test with same name pattern."""
        analyzer = ImpactAnalyzer(project_root=tmp_path)

        # Create test file
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_app.py").touch()

        change = CodeChange(
            file_path="src/app.py",
            change_type=ChangeType.MODIFIED,
        )

        related = analyzer._find_related_tests(change)
        assert "tests/test_app.py" in related

    def test_find_no_related_tests(self, tmp_path):
        """Test when no related tests exist."""
        analyzer = ImpactAnalyzer(project_root=tmp_path)

        change = CodeChange(
            file_path="src/unknown.py",
            change_type=ChangeType.MODIFIED,
        )

        related = analyzer._find_related_tests(change)
        assert len(related) == 0
