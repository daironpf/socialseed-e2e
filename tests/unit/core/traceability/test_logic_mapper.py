"""Tests for logic mapper."""

from datetime import datetime

import pytest

from socialseed_e2e.core.traceability.logic_mapper import LogicMapper
from socialseed_e2e.core.traceability.models import LogicBranch, LogicBranchType, TestTrace


class TestLogicMapper:
    """Tests for LogicMapper class."""

    @pytest.fixture
    def mapper(self):
        """Create a mapper instance."""
        return LogicMapper()

    @pytest.fixture
    def sample_trace(self):
        """Create a sample test trace with logic branches."""
        trace = TestTrace(
            test_id="test-001",
            test_name="test_with_branches",
            service_name="test-service",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="passed",
        )

        # Add logic branches
        trace.logic_branches.append(
            LogicBranch(
                id="branch_0001",
                type=LogicBranchType.CONDITIONAL,
                condition="user.is_authenticated",
                decision="true",
                timestamp=datetime.now(),
                reason="User has valid token",
            )
        )

        trace.logic_branches.append(
            LogicBranch(
                id="branch_0002",
                type=LogicBranchType.ASSERTION,
                condition="assert response.status == 200",
                decision="passed",
                timestamp=datetime.now(),
                reason="Response is OK",
            )
        )

        trace.logic_branches.append(
            LogicBranch(
                id="branch_0003",
                type=LogicBranchType.VALIDATION,
                condition="validate email format",
                decision="passed",
                timestamp=datetime.now(),
            )
        )

        return trace

    def test_map_logic_flow_text(self, mapper, sample_trace):
        """Test mapping logic flow in text format."""
        flow = mapper.map_logic_flow(sample_trace, format_type="text")

        assert flow.title == "Logic Flow: test_with_branches"
        assert flow.decision_points == 3
        assert len(flow.branches) == 3
        assert "Logic Flow for:" in flow.flow_description

    def test_map_logic_flow_markdown(self, mapper, sample_trace):
        """Test mapping logic flow in markdown format."""
        flow = mapper.map_logic_flow(sample_trace, format_type="markdown")

        assert "## Logic Flow:" in flow.flow_description
        assert "**Condition:**" in flow.flow_description
        assert "**Decision:**" in flow.flow_description

    def test_map_logic_flow_html(self, mapper, sample_trace):
        """Test mapping logic flow in HTML format."""
        flow = mapper.map_logic_flow(sample_trace, format_type="html")

        assert '<div class="logic-flow">' in flow.flow_description
        assert 'class="branch"' in flow.flow_description
        assert "</div>" in flow.flow_description

    def test_map_logic_flow_empty(self, mapper):
        """Test mapping empty logic flow."""
        trace = TestTrace(
            test_id="test-002",
            test_name="empty_test",
            service_name="test-service",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        flow = mapper.map_logic_flow(trace)

        assert flow.decision_points == 0
        assert "No logical branches recorded" in flow.flow_description

    def test_generate_mermaid_flowchart(self, mapper, sample_trace):
        """Test generating Mermaid flowchart."""
        flowchart = mapper.generate_mermaid_flowchart(sample_trace)

        assert "flowchart TD" in flowchart or "flowchart LR" in flowchart
        assert "Start[" in flowchart
        assert "End[" in flowchart
        # Should have branch nodes
        assert "B1[" in flowchart or "branch" in flowchart

    def test_generate_mermaid_flowchart_left_right(self, mapper, sample_trace):
        """Test generating Mermaid flowchart in left-right direction."""
        flowchart = mapper.generate_mermaid_flowchart(sample_trace, direction="LR")

        assert "flowchart LR" in flowchart

    def test_generate_decision_tree_text(self, mapper, sample_trace):
        """Test generating text decision tree."""
        tree = mapper.generate_decision_tree(sample_trace, format_type="text")

        assert "Decision Tree:" in tree
        assert "├──" in tree  # Tree branch character

    def test_generate_decision_tree_markdown(self, mapper, sample_trace):
        """Test generating markdown decision tree."""
        tree = mapper.generate_decision_tree(sample_trace, format_type="markdown")

        assert "## Decision Tree:" in tree
        assert "- " in tree  # List item

    def test_generate_decision_tree_html(self, mapper, sample_trace):
        """Test generating HTML decision tree."""
        tree = mapper.generate_decision_tree(sample_trace, format_type="html")

        assert '<ul class="decision-tree">' in tree
        assert "<li>" in tree

    def test_analyze_branch_coverage(self, mapper):
        """Test analyzing branch coverage."""
        trace1 = TestTrace(
            test_id="test-001",
            test_name="test1",
            service_name="service1",
            start_time=datetime.now(),
        )
        trace1.logic_branches.append(
            LogicBranch(
                id="b1",
                type=LogicBranchType.CONDITIONAL,
                condition="x > 0",
                decision="true",
                timestamp=datetime.now(),
            )
        )
        trace1.logic_branches.append(
            LogicBranch(
                id="b2",
                type=LogicBranchType.ASSERTION,
                condition="status == 200",
                decision="passed",
                timestamp=datetime.now(),
            )
        )

        trace2 = TestTrace(
            test_id="test-002",
            test_name="test2",
            service_name="service1",
            start_time=datetime.now(),
        )
        trace2.logic_branches.append(
            LogicBranch(
                id="b3",
                type=LogicBranchType.CONDITIONAL,
                condition="x > 0",
                decision="false",
                timestamp=datetime.now(),
            )
        )

        coverage = mapper.analyze_branch_coverage([trace1, trace2])

        assert coverage["total_branches"] == 3
        assert coverage["average_branches_per_test"] == 1.5
        assert len(coverage["branch_types"]) > 0
        assert coverage["unique_decisions"] > 0

    def test_truncate_text(self, mapper):
        """Test text truncation."""
        short_text = "Short"
        long_text = "A" * 100

        assert mapper._truncate_text(short_text, 50) == short_text
        assert len(mapper._truncate_text(long_text, 50)) <= 50
        assert "..." in mapper._truncate_text(long_text, 50)

    def test_branch_icons(self, mapper):
        """Test branch icons are defined."""
        assert len(mapper.BRANCH_ICONS) > 0
        assert LogicBranchType.CONDITIONAL in mapper.BRANCH_ICONS
        assert LogicBranchType.ASSERTION in mapper.BRANCH_ICONS

    def test_branch_descriptions(self, mapper):
        """Test branch descriptions are defined."""
        assert len(mapper.BRANCH_DESCRIPTIONS) > 0
        assert LogicBranchType.CONDITIONAL in mapper.BRANCH_DESCRIPTIONS
        assert "Conditional" in mapper.BRANCH_DESCRIPTIONS[LogicBranchType.CONDITIONAL]
