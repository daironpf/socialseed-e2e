"""Tests for AI Discovery Report Generator (Issue #187)."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from socialseed_e2e.project_manifest.discovery_report import (
    DiscoveredFlow,
    DiscoveryReportGenerator,
    DiscoverySummary,
    generate_discovery_report,
)


class TestDiscoveredFlow:
    """Test DiscoveredFlow dataclass."""

    def test_flow_creation(self):
        """Test creating a DiscoveredFlow."""
        flow = DiscoveredFlow(
            name="User Authentication",
            description="Login and registration flow",
            endpoints_count=3,
            flow_type="authentication",
            complexity="simple",
        )

        assert flow.name == "User Authentication"
        assert flow.description == "Login and registration flow"
        assert flow.endpoints_count == 3
        assert flow.flow_type == "authentication"
        assert flow.complexity == "simple"


class TestDiscoverySummary:
    """Test DiscoverySummary dataclass."""

    def test_summary_creation(self):
        """Test creating a DiscoverySummary."""
        summary = DiscoverySummary(
            project_name="test-api",
            project_path=Path("/test/project"),
            analysis_timestamp=datetime(2026, 2, 8, 15, 30, 0),
            tech_stack={"users": {"framework": "Spring", "language": "java"}},
            services_count=2,
            endpoints_count=15,
            dtos_count=10,
            flows_discovered=[],
            tests_generated=5,
            output_directory=Path("/test/project/services"),
        )

        assert summary.project_name == "test-api"
        assert summary.services_count == 2
        assert summary.endpoints_count == 15


class TestDiscoveryReportGenerator:
    """Test DiscoveryReportGenerator."""

    @pytest.fixture
    def generator(self, tmp_path):
        return DiscoveryReportGenerator(tmp_path)

    def test_init(self, generator, tmp_path):
        """Test generator initialization."""
        assert generator.project_root == tmp_path
        assert generator.output_dir == tmp_path / ".e2e"
        assert generator.output_dir.exists()

    def test_calculate_complexity(self, generator):
        """Test complexity calculation."""
        # Simple flow (1-2 steps)
        simple = {"steps": [{}, {}]}
        assert generator._calculate_complexity(simple) == "simple"

        # Moderate flow (3-4 steps)
        moderate = {"steps": [{}, {}, {}]}
        assert generator._calculate_complexity(moderate) == "moderate"

        # Complex flow (5+ steps)
        complex_flow = {"steps": [{}, {}, {}, {}, {}]}
        assert generator._calculate_complexity(complex_flow) == "complex"

    def test_get_flow_emoji(self, generator):
        """Test flow emoji mapping."""
        assert generator._get_flow_emoji("authentication") == "🔐"
        assert generator._get_flow_emoji("crud") == "📋"
        assert generator._get_flow_emoji("management") == "⚙️"
        assert generator._get_flow_emoji("unknown") == "📌"

    def test_get_complexity_emoji(self, generator):
        """Test complexity emoji mapping."""
        assert generator._get_complexity_emoji("simple") == "🟢"
        assert generator._get_complexity_emoji("moderate") == "🟡"
        assert generator._get_complexity_emoji("complex") == "🔴"
        assert generator._get_complexity_emoji("unknown") == "⚪"

    def test_build_markdown_content(self, generator):
        """Test markdown content generation."""
        summary = DiscoverySummary(
            project_name="test-api",
            project_path=Path("/test/project"),
            analysis_timestamp=datetime(2026, 2, 8, 15, 30, 0),
            tech_stack={"users": {"framework": "Spring", "language": "java"}},
            services_count=2,
            endpoints_count=15,
            dtos_count=10,
            flows_discovered=[
                DiscoveredFlow(
                    name="Auth Flow",
                    description="Authentication",
                    endpoints_count=3,
                    flow_type="authentication",
                    complexity="simple",
                )
            ],
            tests_generated=5,
            output_directory=Path("/test/project/services"),
        )

        content = generator._build_markdown_content(summary)

        # Check key sections exist
        assert "# 🔍 AI Discovery Report" in content
        assert "test-api" in content
        assert "Spring" in content
        assert "Auth Flow" in content
        assert "e2e run" in content

    def test_get_single_command(self, generator, tmp_path):
        """Test single command generation."""
        command = generator.get_single_command()
        assert f"cd {tmp_path}" in command
        assert "e2e run" in command


class TestGenerateDiscoveryReport:
    """Test convenience function."""

    def test_generate_report_function(self, tmp_path):
        """Test the generate_discovery_report function."""
        with patch.object(DiscoveryReportGenerator, "generate_report") as mock_generate:
            mock_generate.return_value = tmp_path / ".e2e" / "DISCOVERY_REPORT.md"

            result = generate_discovery_report(project_root=tmp_path, tests_generated=3)

            assert mock_generate.called
            assert result == tmp_path / ".e2e" / "DISCOVERY_REPORT.md"


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_report_generation(self, tmp_path):
        """Test complete report generation flow."""
        generator = DiscoveryReportGenerator(tmp_path)

        # Create a mock summary
        summary = DiscoverySummary(
            project_name="integration-test",
            project_path=tmp_path,
            analysis_timestamp=datetime.now(),
            tech_stack={},
            services_count=1,
            endpoints_count=5,
            dtos_count=3,
            flows_discovered=[],
            tests_generated=2,
            output_directory=tmp_path / "services",
        )

        # Generate markdown
        content = generator._build_markdown_content(summary)

        # Verify content
        assert "integration-test" in content
        assert "1" in content  # services count
        assert "5" in content  # endpoints count
        assert "e2e run" in content
