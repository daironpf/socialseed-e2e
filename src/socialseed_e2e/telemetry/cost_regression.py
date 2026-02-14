"""Cost Regression Detector.

Detects when code changes increase token costs beyond acceptable thresholds.
Fails CI/CD pipeline if regression exceeds 15%.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from socialseed_e2e.telemetry.models import CostRegression, TestCaseMetrics


class CostRegressionDetector:
    """Detects cost regressions by comparing with baseline."""

    def __init__(
        self,
        baseline_file: Optional[str] = None,
        threshold_percentage: float = 15.0,
        output_dir: str = "telemetry",
    ):
        self.threshold_percentage = threshold_percentage
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Baseline file
        if baseline_file:
            self.baseline_file = Path(baseline_file)
        else:
            self.baseline_file = self.output_dir / "cost_baseline.json"

        self.baseline_data: Optional[Dict] = None
        self.detected_regressions: List[CostRegression] = []

        # Load baseline if exists
        self._load_baseline()

    def _load_baseline(self):
        """Load baseline data from file."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r") as f:
                    self.baseline_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.baseline_data = None

    def save_baseline(self, test_cases: List[TestCaseMetrics]):
        """Save current metrics as baseline."""
        baseline = {
            "created_at": datetime.now().isoformat(),
            "test_cases": {},
            "total_cost": 0.0,
        }

        total_cost = 0.0
        for tc in test_cases:
            baseline["test_cases"][tc.test_case_id] = {
                "cost_usd": tc.total_cost_usd,
                "input_tokens": tc.total_input_tokens,
                "output_tokens": tc.total_output_tokens,
                "latency_ms": tc.avg_latency_ms,
            }
            total_cost += tc.total_cost_usd

        baseline["total_cost"] = total_cost

        with open(self.baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)

        self.baseline_data = baseline

    def detect_regression(
        self,
        test_cases: List[TestCaseMetrics],
    ) -> List[CostRegression]:
        """Detect cost regressions compared to baseline."""
        self.detected_regressions = []

        if not self.baseline_data:
            # No baseline, create one
            self.save_baseline(test_cases)
            return []

        baseline_tests = self.baseline_data.get("test_cases", {})
        baseline_total = self.baseline_data.get("total_cost", 0.0)

        current_total = sum(tc.total_cost_usd for tc in test_cases)

        # Check overall regression
        if baseline_total > 0:
            increase_pct = ((current_total - baseline_total) / baseline_total) * 100

            if increase_pct > self.threshold_percentage:
                # Overall regression detected
                regression = CostRegression(
                    regression_id=f"reg_overall_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    detected_at=datetime.now(),
                    baseline_cost_usd=baseline_total,
                    current_cost_usd=current_total,
                    increase_percentage=increase_pct,
                    increase_absolute_usd=current_total - baseline_total,
                    threshold_percentage=self.threshold_percentage,
                    exceeded=True,
                    affected_flows=["overall"],
                    test_cases_affected=[tc.test_case_id for tc in test_cases],
                )
                self.detected_regressions.append(regression)

        # Check individual test case regressions
        for tc in test_cases:
            baseline_tc = baseline_tests.get(tc.test_case_id)

            if baseline_tc:
                baseline_cost = baseline_tc.get("cost_usd", 0)

                if baseline_cost > 0:
                    increase_pct = (
                        (tc.total_cost_usd - baseline_cost) / baseline_cost
                    ) * 100

                    if increase_pct > self.threshold_percentage:
                        regression = CostRegression(
                            regression_id=f"reg_{tc.test_case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            detected_at=datetime.now(),
                            baseline_cost_usd=baseline_cost,
                            current_cost_usd=tc.total_cost_usd,
                            increase_percentage=increase_pct,
                            increase_absolute_usd=tc.total_cost_usd - baseline_cost,
                            threshold_percentage=self.threshold_percentage,
                            exceeded=True,
                            affected_flows=[tc.test_name],
                            test_cases_affected=[tc.test_case_id],
                        )
                        self.detected_regressions.append(regression)

        return self.detected_regressions

    def has_regression(self) -> bool:
        """Check if any regression was detected."""
        return len(self.detected_regressions) > 0

    def get_regression_summary(self) -> Dict:
        """Get summary of detected regressions."""
        if not self.detected_regressions:
            return {
                "has_regression": False,
                "total_regressions": 0,
                "total_increase_usd": 0.0,
                "max_increase_percentage": 0.0,
            }

        total_increase = sum(r.increase_absolute_usd for r in self.detected_regressions)
        max_increase_pct = max(r.increase_percentage for r in self.detected_regressions)

        return {
            "has_regression": True,
            "total_regressions": len(self.detected_regressions),
            "total_increase_usd": total_increase,
            "max_increase_percentage": max_increase_pct,
            "threshold_percentage": self.threshold_percentage,
            "regressions": [
                {
                    "id": r.regression_id,
                    "test_case": r.test_cases_affected[0]
                    if r.test_cases_affected
                    else "unknown",
                    "increase_percentage": r.increase_percentage,
                    "increase_usd": r.increase_absolute_usd,
                }
                for r in self.detected_regressions
            ],
        }

    def generate_ci_message(self) -> str:
        """Generate CI/CD failure message."""
        if not self.detected_regressions:
            return "✅ No cost regression detected."

        lines = [
            "🚨 COST REGRESSION DETECTED",
            "",
            f"Threshold: {self.threshold_percentage}%",
            f"Regressions found: {len(self.detected_regressions)}",
            "",
            "Details:",
        ]

        for reg in self.detected_regressions:
            lines.append(
                f"  - {reg.test_cases_affected[0] if reg.test_cases_affected else 'overall'}: "
                f"+{reg.increase_percentage:.1f}% (${reg.increase_absolute_usd:.4f})"
            )

        lines.extend(
            [
                "",
                "Action required:",
                "  1. Review the cost increase in COST_EFFICIENCY_REPORT.json",
                "  2. Apply optimization recommendations",
                "  3. Update baseline if increase is intentional: e2e telemetry baseline",
            ]
        )

        return "\n".join(lines)

    def reset_baseline(self):
        """Reset/delete baseline file."""
        if self.baseline_file.exists():
            self.baseline_file.unlink()
        self.baseline_data = None

    def get_baseline_info(self) -> Optional[Dict]:
        """Get information about current baseline."""
        if not self.baseline_data:
            return None

        return {
            "file": str(self.baseline_file),
            "created_at": self.baseline_data.get("created_at"),
            "test_cases": len(self.baseline_data.get("test_cases", {})),
            "total_cost_usd": self.baseline_data.get("total_cost", 0),
        }
