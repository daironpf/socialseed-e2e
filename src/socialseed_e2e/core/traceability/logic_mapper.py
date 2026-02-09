"""Logic mapper for visual representation of test execution branches.

This module provides functionality to map and visualize the logical
decisions and branches taken during test execution.
"""

from datetime import datetime
from typing import Dict, List, Optional

from socialseed_e2e.core.traceability.models import (
    LogicBranch,
    LogicBranchType,
    LogicFlow,
    TestTrace,
)


class LogicMapper:
    """Maps and visualizes logical branches in test execution.

    This class creates visual representations of the logical decisions
    made during test execution, showing why certain branches were taken.

    Example:
        >>> mapper = LogicMapper()
        >>> trace = collector.get_current_trace()
        >>> flow = mapper.map_logic_flow(trace)
        >>> print(flow.flow_description)
    """

    # Icons for different branch types
    BRANCH_ICONS = {
        LogicBranchType.CONDITIONAL: "◆",
        LogicBranchType.LOOP: "⟳",
        LogicBranchType.TRY_CATCH: "⚡",
        LogicBranchType.ASSERTION: "✓",
        LogicBranchType.VALIDATION: "🔍",
        LogicBranchType.ERROR_HANDLING: "⚠",
    }

    # Descriptions for branch types
    BRANCH_DESCRIPTIONS = {
        LogicBranchType.CONDITIONAL: "Conditional check",
        LogicBranchType.LOOP: "Loop iteration",
        LogicBranchType.TRY_CATCH: "Exception handling",
        LogicBranchType.ASSERTION: "Assertion check",
        LogicBranchType.VALIDATION: "Validation",
        LogicBranchType.ERROR_HANDLING: "Error handling",
    }

    def __init__(self):
        """Initialize the logic mapper."""
        self._branch_counter = 0

    def map_logic_flow(
        self, trace: TestTrace, include_details: bool = True, format_type: str = "text"
    ) -> LogicFlow:
        """Map the logical flow of a test execution.

        Args:
            trace: The test trace to analyze
            include_details: Whether to include detailed descriptions
            format_type: Output format (text, markdown, html)

        Returns:
            LogicFlow with mapped branches and description
        """
        self._branch_counter = 0

        if not trace.logic_branches:
            return LogicFlow(
                title=f"Logic Flow: {trace.test_name}",
                branches=[],
                flow_description="No logical branches recorded",
                decision_points=0,
            )

        # Sort branches by timestamp
        sorted_branches = sorted(trace.logic_branches, key=lambda x: x.timestamp)

        # Generate flow description
        if format_type == "markdown":
            flow_description = self._generate_markdown_flow(sorted_branches, trace, include_details)
        elif format_type == "html":
            flow_description = self._generate_html_flow(sorted_branches, trace, include_details)
        else:
            flow_description = self._generate_text_flow(sorted_branches, trace, include_details)

        return LogicFlow(
            title=f"Logic Flow: {trace.test_name}",
            branches=sorted_branches,
            flow_description=flow_description,
            decision_points=len(sorted_branches),
        )

    def generate_mermaid_flowchart(
        self,
        trace: TestTrace,
        direction: str = "TD",  # TD (top-down) or LR (left-right)
    ) -> str:
        """Generate a Mermaid.js flowchart of the logic flow.

        Args:
            trace: The test trace to visualize
            direction: Flowchart direction (TD or LR)

        Returns:
            Mermaid flowchart definition
        """
        if not trace.logic_branches:
            return f"""flowchart {direction}
    Start["{trace.test_name}"]
    End["End"]
    Start --> End"""

        lines = [f"flowchart {direction}"]

        # Add start node
        lines.append(f'    Start["▶ {trace.test_name}"]')

        prev_node = "Start"

        # Add branch nodes
        for i, branch in enumerate(trace.logic_branches):
            node_id = f"B{i + 1}"
            icon = self.BRANCH_ICONS.get(branch.type, "•")

            # Create node label
            label = f"{icon} {self._truncate_text(branch.condition, 30)}"
            lines.append(f'    {node_id}["{label}"]')

            # Add connection from previous node
            lines.append(f"    {prev_node} --> {node_id}")

            # Add decision node
            decision_id = f"D{i + 1}"
            decision_label = f"{branch.decision}"
            if branch.reason:
                decision_label += f"<br/><small>{self._truncate_text(branch.reason, 40)}</small>"

            lines.append(f'    {decision_id}["{decision_label}"]')
            lines.append(f"    {node_id} --> {decision_id}")

            prev_node = decision_id

        # Add end node
        status_icon = "✓" if trace.status == "passed" else "✗"
        lines.append(f'    End["{status_icon} {trace.status.upper()}"]')
        lines.append(f"    {prev_node} --> End")

        return "\n".join(lines)

    def generate_decision_tree(self, trace: TestTrace, format_type: str = "text") -> str:
        """Generate a decision tree representation.

        Args:
            trace: The test trace to visualize
            format_type: Output format (text, markdown, html)

        Returns:
            Decision tree representation
        """
        if not trace.logic_branches:
            return "No decisions recorded"

        if format_type == "markdown":
            return self._generate_markdown_tree(trace)
        elif format_type == "html":
            return self._generate_html_tree(trace)
        else:
            return self._generate_text_tree(trace)

    def analyze_branch_coverage(self, traces: List[TestTrace]) -> Dict:
        """Analyze branch coverage across multiple test traces.

        Args:
            traces: List of test traces to analyze

        Returns:
            Dictionary with coverage statistics
        """
        branch_types: Dict[LogicBranchType, int] = {}
        decisions: Dict[str, int] = {}
        total_branches = 0

        for trace in traces:
            for branch in trace.logic_branches:
                total_branches += 1

                # Count by type
                branch_types[branch.type] = branch_types.get(branch.type, 0) + 1

                # Count decisions
                decision_key = f"{branch.condition} -> {branch.decision}"
                decisions[decision_key] = decisions.get(decision_key, 0) + 1

        return {
            "total_branches": total_branches,
            "branch_types": {k.value: v for k, v in branch_types.items()},
            "unique_decisions": len(decisions),
            "decision_frequency": decisions,
            "average_branches_per_test": total_branches / len(traces) if traces else 0,
        }

    def _generate_text_flow(
        self, branches: List[LogicBranch], trace: TestTrace, include_details: bool
    ) -> str:
        """Generate text-based flow description.

        Args:
            branches: List of logic branches
            trace: Test trace
            include_details: Whether to include details

        Returns:
            Text flow description
        """
        lines = [f"Logic Flow for: {trace.test_name}", "=" * 50, ""]

        for i, branch in enumerate(branches, 1):
            icon = self.BRANCH_ICONS.get(branch.type, "•")
            desc = self.BRANCH_DESCRIPTIONS.get(branch.type, "Decision")

            lines.append(f"{i}. {icon} {desc}")
            lines.append(f"   Condition: {branch.condition}")
            lines.append(f"   Decision: {branch.decision}")

            if include_details and branch.reason:
                lines.append(f"   Reason: {branch.reason}")

            lines.append("")

        lines.append(f"Result: {trace.status.upper()}")

        return "\n".join(lines)

    def _generate_markdown_flow(
        self, branches: List[LogicBranch], trace: TestTrace, include_details: bool
    ) -> str:
        """Generate Markdown flow description.

        Args:
            branches: List of logic branches
            trace: Test trace
            include_details: Whether to include details

        Returns:
            Markdown flow description
        """
        lines = [f"## Logic Flow: {trace.test_name}", ""]

        for i, branch in enumerate(branches, 1):
            icon = self.BRANCH_ICONS.get(branch.type, "•")
            desc = self.BRANCH_DESCRIPTIONS.get(branch.type, "Decision")

            lines.append(f"### {i}. {icon} {desc}")
            lines.append("")
            lines.append(f"**Condition:** `{branch.condition}`")
            lines.append("")
            lines.append(f"**Decision:** `{branch.decision}`")

            if include_details and branch.reason:
                lines.append("")
                lines.append(f"**Reason:** {branch.reason}")

            lines.append("")

        status_emoji = "✅" if trace.status == "passed" else "❌"
        lines.append(f"**Result:** {status_emoji} {trace.status.upper()}")

        return "\n".join(lines)

    def _generate_html_flow(
        self, branches: List[LogicBranch], trace: TestTrace, include_details: bool
    ) -> str:
        """Generate HTML flow description.

        Args:
            branches: List of logic branches
            trace: Test trace
            include_details: Whether to include details

        Returns:
            HTML flow description
        """
        html = [f'<div class="logic-flow">']
        html.append(f"<h3>Logic Flow: {trace.test_name}</h3>")
        html.append('<div class="branches">')

        for i, branch in enumerate(branches, 1):
            icon = self.BRANCH_ICONS.get(branch.type, "•")
            desc = self.BRANCH_DESCRIPTIONS.get(branch.type, "Decision")

            html.append(f'<div class="branch" id="branch-{i}">')
            html.append(f'<div class="branch-header">{icon} {desc}</div>')
            html.append(f'<div class="condition"><code>{branch.condition}</code></div>')
            html.append(f'<div class="decision">→ {branch.decision}</div>')

            if include_details and branch.reason:
                html.append(f'<div class="reason">{branch.reason}</div>')

            html.append("</div>")

        status_class = "success" if trace.status == "passed" else "failure"
        html.append(f'<div class="result {status_class}">{trace.status.upper()}</div>')
        html.append("</div>")
        html.append("</div>")

        return "\n".join(html)

    def _generate_text_tree(self, trace: TestTrace) -> str:
        """Generate text-based decision tree.

        Args:
            trace: Test trace

        Returns:
            Text tree representation
        """
        lines = [f"Decision Tree: {trace.test_name}", ""]

        for branch in trace.logic_branches:
            icon = self.BRANCH_ICONS.get(branch.type, "•")
            lines.append(f"├── {icon} {branch.condition}")
            lines.append(f"│   └── {branch.decision}")
            if branch.reason:
                lines.append(f"│       └── {branch.reason}")

        return "\n".join(lines)

    def _generate_markdown_tree(self, trace: TestTrace) -> str:
        """Generate Markdown decision tree.

        Args:
            trace: Test trace

        Returns:
            Markdown tree representation
        """
        lines = [f"## Decision Tree: {trace.test_name}", ""]

        for i, branch in enumerate(trace.logic_branches):
            indent = "  " * i
            icon = self.BRANCH_ICONS.get(branch.type, "•")
            lines.append(f"{indent}- {icon} `{branch.condition}` → **{branch.decision}**")
            if branch.reason:
                lines.append(f"{indent}  - _{branch.reason}_")

        return "\n".join(lines)

    def _generate_html_tree(self, trace: TestTrace) -> str:
        """Generate HTML decision tree.

        Args:
            trace: Test trace

        Returns:
            HTML tree representation
        """
        html = ['<ul class="decision-tree">']

        for branch in trace.logic_branches:
            icon = self.BRANCH_ICONS.get(branch.type, "•")
            html.append("<li>")
            html.append(f'<span class="condition">{icon} {branch.condition}</span>')
            html.append(f'<span class="decision">→ {branch.decision}</span>')
            if branch.reason:
                html.append(f'<span class="reason">{branch.reason}</span>')
            html.append("</li>")

        html.append("</ul>")

        return "\n".join(html)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."
