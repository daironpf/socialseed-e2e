"""Cost Efficiency Report Generator.

Generates COST_EFFICIENCY_REPORT.json with comprehensive
token usage, cost, and performance analysis.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.telemetry.models import (
    CostEfficiencyReport,
    CostRegression,
    LLMCall,
    OptimizationRecommendation,
    ReasoningLoop,
    TestCaseMetrics,
)


class ReportGenerator:
    """Generates cost efficiency reports."""

    def __init__(self, output_dir: str = "telemetry"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        calls: List[LLMCall],
        test_cases: List[TestCaseMetrics],
        reasoning_loops: List[ReasoningLoop],
        cost_regressions: List[CostRegression],
        recommendations: List[OptimizationRecommendation],
        budget_breaches: List[Dict[str, Any]],
    ) -> CostEfficiencyReport:
        """Generate comprehensive cost efficiency report."""
        report_id = str(uuid.uuid4())[:8]
        generated_at = datetime.now()

        # Calculate overall metrics
        total_calls = len(calls)
        total_input = sum(c.token_usage.input_tokens for c in calls)
        total_output = sum(c.token_usage.output_tokens for c in calls)
        total_tokens = total_input + total_output
        total_cost = sum(c.cost.total_cost_usd for c in calls)

        # Calculate latency metrics
        avg_latency = (
            sum(c.latency.total_latency_ms for c in calls) / len(calls) if calls else 0
        )
        total_time = (
            sum(c.latency.total_latency_ms for c in calls) / 1000 if calls else 0
        )

        # Calculate by model
        by_model = self._aggregate_by_model(calls)

        # Calculate by test case
        by_test_case = test_cases

        # Calculate by task
        by_task = self._aggregate_by_task(calls, test_cases)

        # Calculate health score
        health_score = self._calculate_health_score(
            calls, reasoning_loops, cost_regressions, budget_breaches
        )

        # Determine status
        status = self._determine_status(health_score, cost_regressions, budget_breaches)

        # Generate summary
        summary = self._generate_summary(
            total_cost,
            total_tokens,
            len(reasoning_loops),
            len(cost_regressions),
            health_score,
        )

        report = CostEfficiencyReport(
            report_id=report_id,
            generated_at=generated_at,
            total_llm_calls=total_calls,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            avg_latency_ms=avg_latency,
            total_execution_time_seconds=total_time,
            by_model=by_model,
            by_test_case=by_test_case,
            by_task=by_task,
            reasoning_loops=reasoning_loops,
            cost_regressions=cost_regressions,
            budget_breaches=budget_breaches,
            optimization_recommendations=recommendations,
            summary=summary,
            health_score=health_score,
            status=status,
        )

        return report

    def save_report(
        self, report: CostEfficiencyReport, filename: Optional[str] = None
    ) -> Path:
        """Save report to JSON file."""
        if filename is None:
            filename = f"COST_EFFICIENCY_REPORT_{report.report_id}.json"

        report_path = self.output_dir / filename

        # Convert to dict
        report_dict = report.model_dump()

        # Save
        with open(report_path, "w") as f:
            json.dump(report_dict, f, indent=2, default=str)

        return report_path

    def _aggregate_by_model(self, calls: List[LLMCall]) -> Dict[str, Dict[str, Any]]:
        """Aggregate metrics by model."""
        by_model: Dict[str, Dict[str, Any]] = {}

        for call in calls:
            model = call.model_name
            if model not in by_model:
                by_model[model] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "avg_latency_ms": 0.0,
                    "provider": call.provider,
                    "cost_tier": call.cost_tier.value,
                }

            by_model[model]["calls"] += 1
            by_model[model]["input_tokens"] += call.token_usage.input_tokens
            by_model[model]["output_tokens"] += call.token_usage.output_tokens
            by_model[model]["total_tokens"] += call.token_usage.total_tokens
            by_model[model]["cost_usd"] += call.cost.total_cost_usd

        # Calculate averages
        for model in by_model:
            model_calls = [c for c in calls if c.model_name == model]
            by_model[model]["avg_latency_ms"] = (
                sum(c.latency.total_latency_ms for c in model_calls) / len(model_calls)
                if model_calls
                else 0
            )

        return by_model

    def _aggregate_by_task(
        self,
        calls: List[LLMCall],
        test_cases: List[TestCaseMetrics],
    ) -> List["TaskMetrics"]:
        """Aggregate metrics by task."""
        # Group test cases by task
        task_map: Dict[str, List[TestCaseMetrics]] = {}
        for tc in test_cases:
            # Extract task from test_case_id or group by common prefix
            task_id = (
                tc.test_case_id.split("_")[0] if "_" in tc.test_case_id else "default"
            )
            if task_id not in task_map:
                task_map[task_id] = []
            task_map[task_id].append(tc)

        from socialseed_e2e.telemetry.models import TaskMetrics

        tasks = []
        for task_id, task_tests in task_map.items():
            total_cost = sum(t.total_cost_usd for t in task_tests)
            total_tokens = sum(t.total_tokens for t in task_tests)

            task_info = TaskMetrics(
                task_id=task_id,
                task_name=task_id,  # Use task_id as task_name
                test_cases=task_tests,
                total_cost_usd=total_cost,
                total_tokens=total_tokens,
            )
            tasks.append(task_info)

        return tasks

    def _calculate_health_score(
        self,
        calls: List[LLMCall],
        loops: List[ReasoningLoop],
        regressions: List[CostRegression],
        breaches: List[Dict[str, Any]],
    ) -> int:
        """Calculate overall health score (0-100)."""
        score = 100

        # Deduct for reasoning loops (wasted compute)
        loop_waste = sum(l.cost_incurred_usd for l in loops)
        total_cost = sum(c.cost.total_cost_usd for c in calls)
        if total_cost > 0:
            waste_percentage = (loop_waste / total_cost) * 100
            score -= int(waste_percentage * 2)  # 2 points per % waste

        # Deduct for cost regressions
        score -= len(regressions) * 10

        # Deduct for budget breaches
        score -= len(breaches) * 5

        # Deduct for cache misses (if tracked)
        cache_misses = sum(1 for c in calls if not c.cache_hit)
        if calls:
            cache_miss_rate = cache_misses / len(calls)
            score -= int(cache_miss_rate * 10)

        return max(0, min(100, score))

    def _determine_status(
        self,
        health_score: int,
        regressions: List[CostRegression],
        breaches: List[Dict[str, Any]],
    ) -> str:
        """Determine overall status."""
        if health_score >= 80 and not regressions and not breaches:
            return "healthy"
        elif health_score >= 50 and len(regressions) <= 1:
            return "warning"
        else:
            return "critical"

    def _generate_summary(
        self,
        total_cost: float,
        total_tokens: int,
        loops_count: int,
        regressions_count: int,
        health_score: int,
    ) -> str:
        """Generate human-readable summary."""
        parts = []

        parts.append(f"Total cost: ${total_cost:.4f}")
        parts.append(f"Total tokens: {total_tokens:,}")

        if loops_count > 0:
            parts.append(f"⚠️ {loops_count} reasoning loop(s) detected")

        if regressions_count > 0:
            parts.append(f"🚨 {regressions_count} cost regression(s) detected")

        parts.append(f"Health score: {health_score}/100")

        if health_score >= 80:
            parts.append("✅ System is performing efficiently")
        elif health_score >= 50:
            parts.append("⚠️ Some optimizations recommended")
        else:
            parts.append("🚨 Critical issues require attention")

        return "; ".join(parts)

    def generate_markdown_report(self, report: CostEfficiencyReport) -> str:
        """Generate markdown version of report."""
        lines = [
            "# Cost Efficiency Report",
            "",
            f"**Report ID:** {report.report_id}",
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Status:** {report.status.upper()}",
            f"**Health Score:** {report.health_score}/100",
            "",
            "## Summary",
            "",
            report.summary,
            "",
            "## Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total LLM Calls | {report.total_llm_calls} |",
            f"| Total Tokens | {report.total_tokens:,} |",
            f"| Total Cost | ${report.total_cost_usd:.4f} |",
            f"| Avg Latency | {report.avg_latency_ms:.0f}ms |",
            f"| Execution Time | {report.total_execution_time_seconds:.1f}s |",
            "",
            "## By Model",
            "",
            "| Model | Calls | Tokens | Cost |",
            "|-------|-------|--------|------|",
        ]

        for model, data in report.by_model.items():
            lines.append(
                f"| {model} | {data['calls']} | {data['total_tokens']:,} | ${data['cost_usd']:.4f} |"
            )

        lines.extend(
            [
                "",
                "## Issues Detected",
                "",
            ]
        )

        if report.reasoning_loops:
            lines.append(f"### Reasoning Loops: {len(report.reasoning_loops)}")
            for loop in report.reasoning_loops:
                lines.append(f"- {loop.loop_id}: {loop.tokens_consumed} tokens wasted")
            lines.append("")

        if report.cost_regressions:
            lines.append(f"### Cost Regressions: {len(report.cost_regressions)}")
            for reg in report.cost_regressions:
                lines.append(
                    f"- {reg.test_cases_affected[0] if reg.test_cases_affected else 'overall'}: "
                    f"+{reg.increase_percentage:.1f}%"
                )
            lines.append("")

        if report.optimization_recommendations:
            lines.extend(
                [
                    "## Optimization Recommendations",
                    "",
                ]
            )
            for i, rec in enumerate(report.optimization_recommendations[:10], 1):
                lines.append(f"{i}. **{rec.title}** ({rec.priority})")
                lines.append(f"   - {rec.description}")
                if rec.estimated_savings_usd:
                    lines.append(
                        f"   - Potential savings: ${rec.estimated_savings_usd:.4f}"
                    )
                lines.append("")

        return "\n".join(lines)
