"""Risk Scorer - Assigns risk scores to endpoints using AI analysis.

This module provides AI-powered risk scoring based on code changes,
historical failure data, and impact analysis.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from socialseed_e2e.risk_analyzer.change_analyzer import ChangedFile
from socialseed_e2e.risk_analyzer.impact_calculator import ImpactResult


@dataclass
class RiskResult:
    """Result of risk analysis for an endpoint."""

    endpoint_path: str
    http_method: str
    risk_score: int  # 0-100
    risk_level: str  # 'high', 'medium', 'low'
    factors: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    historical_failures: int = 0
    last_failure_date: Optional[datetime] = None


class RiskScorer:
    """Scores risk levels for endpoints using multiple factors."""

    # Risk thresholds
    HIGH_RISK_THRESHOLD = 70
    MEDIUM_RISK_THRESHOLD = 40

    def __init__(
        self,
        project_path: Optional[str] = None,
        history_file: Optional[str] = None,
    ):
        """Initialize the risk scorer.

        Args:
            project_path: Path to project root
            history_file: Path to test history file
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.history_file = (
            Path(history_file)
            if history_file
            else self.project_path / ".e2e/test_history.json"
        )
        self.test_history: Dict = {}
        self._load_history()

    def _load_history(self):
        """Load test execution history."""
        if self.history_file.exists():
            try:
                self.test_history = json.loads(self.history_file.read_text())
            except (json.JSONDecodeError, IOError):
                self.test_history = {}
        else:
            self.test_history = {}

    def calculate_risk_score(
        self,
        impact_result: ImpactResult,
        changed_files: List[ChangedFile],
        use_ai: bool = True,
    ) -> RiskResult:
        """Calculate comprehensive risk score for an endpoint.

        Args:
            impact_result: Impact analysis result
            changed_files: List of changed files
            use_ai: Whether to use AI-enhanced scoring

        Returns:
            Risk result with score and factors
        """
        factors = {}

        # Base score from impact
        base_score = impact_result.impact_score
        factors["impact_score"] = float(base_score)

        # Historical failure factor
        history_score = self._calculate_history_factor(
            impact_result.endpoint_path,
            impact_result.http_method,
        )
        factors["historical_failure"] = history_score

        # Complexity factor
        complexity_score = self._calculate_complexity_factor(
            impact_result.affected_files,
            changed_files,
        )
        factors["complexity"] = complexity_score

        # Change magnitude factor
        magnitude_score = self._calculate_magnitude_factor(
            impact_result.affected_files,
            changed_files,
        )
        factors["change_magnitude"] = magnitude_score

        # Critical path factor
        critical_score = self._calculate_critical_path_factor(
            impact_result.endpoint_path,
        )
        factors["critical_path"] = critical_score

        # Calculate weighted total
        if use_ai:
            total_score = self._ai_enhanced_scoring(factors)
        else:
            total_score = self._standard_scoring(factors)

        # Ensure score is within 0-100
        total_score = max(0, min(100, total_score))

        # Determine risk level
        risk_level = self._get_risk_level(total_score)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            total_score, factors, impact_result
        )

        # Get historical data
        historical_data = self._get_historical_data(
            impact_result.endpoint_path, impact_result.http_method
        )

        return RiskResult(
            endpoint_path=impact_result.endpoint_path,
            http_method=impact_result.http_method,
            risk_score=int(total_score),
            risk_level=risk_level,
            factors=factors,
            recommendations=recommendations,
            affected_files=impact_result.affected_files,
            historical_failures=historical_data["failure_count"],
            last_failure_date=historical_data["last_failure"],
        )

    def _calculate_history_factor(self, endpoint_path: str, http_method: str) -> float:
        """Calculate risk factor based on historical failures."""
        endpoint_key = f"{http_method} {endpoint_path}"

        if endpoint_key not in self.test_history:
            return 0.0

        history = self.test_history[endpoint_key]
        failures = history.get("failures", 0)
        total_runs = history.get("total_runs", 0)

        if total_runs == 0:
            return 0.0

        # Calculate failure rate
        failure_rate = failures / total_runs

        # Weight recent failures more heavily
        recent_failures = history.get("recent_failures", 0)
        recent_weight = min(recent_failures * 5, 20)  # Cap at 20

        # Combine factors
        score = (failure_rate * 30) + recent_weight

        return min(score, 40)  # Cap at 40

    def _calculate_complexity_factor(
        self,
        affected_files: List[str],
        changed_files: List[ChangedFile],
    ) -> float:
        """Calculate complexity factor based on code complexity."""
        score = 0.0

        for file_path in affected_files:
            # Find the corresponding changed file
            changed_file = next((f for f in changed_files if f.path == file_path), None)

            if changed_file:
                # Score based on number of affected functions
                func_count = len(changed_file.affected_functions)
                score += min(func_count * 2, 10)

                # Score based on lines changed
                total_lines = changed_file.lines_added + changed_file.lines_deleted
                if total_lines > 100:
                    score += 10
                elif total_lines > 50:
                    score += 7
                elif total_lines > 20:
                    score += 4

                # Check for complex patterns
                for change in changed_file.content_changes:
                    # Nested conditions increase complexity
                    if change.count("if ") > 2:
                        score += 3
                    # Database operations
                    if re.search(r"db\.|query|session", change, re.IGNORECASE):
                        score += 2
                    # External service calls
                    if re.search(r"requests\.|http|client", change, re.IGNORECASE):
                        score += 2

        return min(score, 30)  # Cap at 30

    def _calculate_magnitude_factor(
        self,
        affected_files: List[str],
        changed_files: List[ChangedFile],
    ) -> float:
        """Calculate factor based on change magnitude."""
        total_lines = 0

        for file_path in affected_files:
            changed_file = next((f for f in changed_files if f.path == file_path), None)
            if changed_file:
                total_lines += changed_file.lines_added
                total_lines += changed_file.lines_deleted

        # Score based on total lines changed
        if total_lines > 200:
            return 20.0
        elif total_lines > 100:
            return 15.0
        elif total_lines > 50:
            return 10.0
        elif total_lines > 20:
            return 5.0
        else:
            return 0.0

    def _calculate_critical_path_factor(self, endpoint_path: str) -> float:
        """Calculate factor based on endpoint criticality."""
        score = 0.0
        path_lower = endpoint_path.lower()

        # Critical paths
        critical_patterns = [
            r"auth",
            r"login",
            r"register",
            r"payment",
            r"checkout",
            r"order",
            r"user",
            r"admin",
        ]

        for pattern in critical_patterns:
            if re.search(pattern, path_lower):
                score += 5

        # API versioning - newer versions get slightly higher risk
        if "/v1/" in path_lower:
            score += 2

        return min(score, 20)  # Cap at 20

    def _ai_enhanced_scoring(self, factors: Dict[str, float]) -> float:
        """Apply AI-enhanced scoring algorithm.

        This uses weighted factors with machine learning-inspired adjustments.
        """
        # Base weights
        weights = {
            "impact_score": 0.35,
            "historical_failure": 0.25,
            "complexity": 0.20,
            "change_magnitude": 0.10,
            "critical_path": 0.10,
        }

        # Calculate weighted sum
        total = sum(factors.get(key, 0) * weight for key, weight in weights.items())

        # AI adjustment: Boost score if multiple high factors present
        high_factors = sum(1 for v in factors.values() if v > 15)
        if high_factors >= 3:
            total *= 1.15  # 15% boost

        # AI adjustment: Reduce score if all factors are low
        if all(v < 10 for v in factors.values()):
            total *= 0.85  # 15% reduction

        return total

    def _standard_scoring(self, factors: Dict[str, float]) -> float:
        """Apply standard scoring without AI enhancements."""
        weights = {
            "impact_score": 0.40,
            "historical_failure": 0.25,
            "complexity": 0.20,
            "change_magnitude": 0.10,
            "critical_path": 0.05,
        }

        return sum(factors.get(key, 0) * weight for key, weight in weights.items())

    def _get_risk_level(self, score: float) -> str:
        """Determine risk level from score."""
        if score >= self.HIGH_RISK_THRESHOLD:
            return "high"
        elif score >= self.MEDIUM_RISK_THRESHOLD:
            return "medium"
        else:
            return "low"

    def _generate_recommendations(
        self,
        risk_score: float,
        factors: Dict[str, float],
        impact_result: ImpactResult,
    ) -> List[str]:
        """Generate testing recommendations based on risk analysis."""
        recommendations = []

        # High impact recommendations
        if factors.get("impact_score", 0) > 50:
            recommendations.append(
                "Prioritize testing - endpoint directly affected by changes"
            )

        # Historical failure recommendations
        if factors.get("historical_failure", 0) > 20:
            recommendations.append(
                "Review historical failures - this endpoint has failed frequently"
            )

        # Complexity recommendations
        if factors.get("complexity", 0) > 15:
            recommendations.append("Test edge cases - complex changes detected")

        # Magnitude recommendations
        if factors.get("change_magnitude", 0) > 10:
            recommendations.append(
                "Comprehensive testing recommended - large changes detected"
            )

        # Critical path recommendations
        if factors.get("critical_path", 0) > 10:
            recommendations.append(
                "Critical endpoint - ensure all auth/business logic paths are tested"
            )

        # Risk level specific recommendations
        if risk_score >= self.HIGH_RISK_THRESHOLD:
            recommendations.append(
                "HIGH RISK: Run full regression suite before deployment"
            )
        elif risk_score >= self.MEDIUM_RISK_THRESHOLD:
            recommendations.append(
                "MEDIUM RISK: Test related functionality and integration points"
            )

        return recommendations

    def _get_historical_data(self, endpoint_path: str, http_method: str) -> Dict:
        """Get historical test data for an endpoint."""
        endpoint_key = f"{http_method} {endpoint_path}"

        if endpoint_key not in self.test_history:
            return {"failure_count": 0, "last_failure": None}

        history = self.test_history[endpoint_key]
        last_failure_str = history.get("last_failure")

        last_failure = None
        if last_failure_str:
            try:
                last_failure = datetime.fromisoformat(last_failure_str)
            except ValueError:
                pass

        return {
            "failure_count": history.get("failures", 0),
            "last_failure": last_failure,
        }

    def score_multiple_endpoints(
        self,
        impact_results: List[ImpactResult],
        changed_files: List[ChangedFile],
        use_ai: bool = True,
    ) -> List[RiskResult]:
        """Calculate risk scores for multiple endpoints.

        Args:
            impact_results: List of impact results
            changed_files: List of changed files
            use_ai: Whether to use AI-enhanced scoring

        Returns:
            List of risk results sorted by risk score (descending)
        """
        risk_results = []

        for impact in impact_results:
            risk = self.calculate_risk_score(impact, changed_files, use_ai)
            risk_results.append(risk)

        # Sort by risk score (descending)
        risk_results.sort(key=lambda x: x.risk_score, reverse=True)

        return risk_results

    def get_risk_summary(self, risk_results: List[RiskResult]) -> Dict:
        """Get summary statistics for risk analysis.

        Args:
            risk_results: List of risk results

        Returns:
            Summary dictionary
        """
        if not risk_results:
            return {
                "total_endpoints": 0,
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0,
                "average_score": 0,
                "max_score": 0,
                "min_score": 0,
            }

        scores = [r.risk_score for r in risk_results]
        high = sum(1 for r in risk_results if r.risk_level == "high")
        medium = sum(1 for r in risk_results if r.risk_level == "medium")
        low = sum(1 for r in risk_results if r.risk_level == "low")

        return {
            "total_endpoints": len(risk_results),
            "high_risk": high,
            "medium_risk": medium,
            "low_risk": low,
            "average_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
            "min_score": min(scores),
        }

    def save_test_result(
        self,
        endpoint_path: str,
        http_method: str,
        success: bool,
        timestamp: Optional[datetime] = None,
    ):
        """Save test execution result for future risk calculations.

        Args:
            endpoint_path: API endpoint path
            http_method: HTTP method
            success: Whether test passed
            timestamp: Test execution timestamp
        """
        endpoint_key = f"{http_method} {endpoint_path}"
        timestamp = timestamp or datetime.now()

        if endpoint_key not in self.test_history:
            self.test_history[endpoint_key] = {
                "total_runs": 0,
                "failures": 0,
                "recent_failures": 0,
                "last_failure": None,
                "last_success": None,
                "history": [],
            }

        history = self.test_history[endpoint_key]
        history["total_runs"] += 1

        if success:
            history["last_success"] = timestamp.isoformat()
            history["recent_failures"] = 0
        else:
            history["failures"] += 1
            history["recent_failures"] += 1
            history["last_failure"] = timestamp.isoformat()

        # Keep last 10 results
        history["history"].append(
            {
                "timestamp": timestamp.isoformat(),
                "success": success,
            }
        )
        history["history"] = history["history"][-10:]

        # Save to file
        self._save_history()

    def _save_history(self):
        """Save test history to file."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(json.dumps(self.test_history, indent=2))

    def get_prioritized_test_list(
        self, risk_results: List[RiskResult]
    ) -> List[Tuple[str, int, str]]:
        """Get prioritized list of tests to run.

        Returns:
            List of (endpoint, risk_score, priority) tuples
        """
        prioritized = []

        for result in risk_results:
            if result.risk_score >= self.HIGH_RISK_THRESHOLD:
                priority = "critical"
            elif result.risk_score >= self.MEDIUM_RISK_THRESHOLD:
                priority = "high"
            elif result.risk_score > 20:
                priority = "medium"
            else:
                priority = "low"

            endpoint = f"{result.http_method} {result.endpoint_path}"
            prioritized.append((endpoint, result.risk_score, priority))

        return prioritized
