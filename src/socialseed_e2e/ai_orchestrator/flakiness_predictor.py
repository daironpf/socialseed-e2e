"""
Flakiness Prediction System for socialseed-e2e.

This module provides predictive analysis of test flakiness before execution,
using AST analysis and historical data to identify potential flaky tests.

Features:
- AST-based test code analysis
- Pattern detection for common flakiness causes
- Risk scoring for new tests
- Recommendations for improving test stability
"""

import ast
import hashlib
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FlakinessRiskLevel(str, Enum):
    """Risk levels for test flakiness."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FlakinessFactor(str, Enum):
    """Common factors that cause test flakiness."""

    TIME_SENSITIVE = "time_sensitive"
    RANDOM_DATA = "random_data"
    EXTERNAL_DEPENDENCY = "external_dependency"
    TIMING_ISSUE = "timing_issue"
    STATE_LEAKAGE = "state_leakage"
    ASYNC_ISSUE = "async_issue"
    FLAKY_ASSERTION = "flaky_assertion"


class FlakinessPrediction(BaseModel):
    """Prediction result for test flakiness."""

    test_file: str
    test_name: Optional[str] = None

    risk_level: FlakinessRiskLevel
    risk_score: float = Field(..., ge=0, le=100)

    factors_detected: List[FlakinessFactor] = Field(default_factory=list)
    factor_details: Dict[str, Any] = Field(default_factory=dict)

    recommendations: List[str] = Field(default_factory=list)
    suggested_fixes: List[Dict[str, Any]] = Field(default_factory=list)

    analyzed_at: datetime = Field(default_factory=datetime.now)


class FlakinessAnalyzer:
    """
    Analyzes test code to predict flakiness before execution.
    """

    FLAKY_PATTERNS = {
        FlakinessFactor.TIME_SENSITIVE: [
            r"time\.sleep\(",
            r"asyncio\.sleep\(",
            r"threading\.sleep\(",
            r"delay\(",
        ],
        FlakinessFactor.RANDOM_DATA: [
            r"random\.",
            r"faker\.",
            r"uuid\.",
            r"\b\d+\.\d+\.\d+\.\d+",  # random IP
        ],
        FlakinessFactor.EXTERNAL_DEPENDENCY: [
            r"requests\.get\(",
            r"httpx\.",
            r"subprocess\.",
            r"os\.system\(",
        ],
        FlakinessFactor.TIMING_ISSUE: [
            r"wait_for\(",
            r"waitUntil\(",
            r"poll\(",
            r"retry\(",
        ],
        FlakinessFactor.STATE_LEAKAGE: [
            r"class.*Test.*:",
            r"setUp\(",
            r"tearDown\(",
            r"@pytest\.fixture.*scope=[\"']function",
        ],
        FlakinessFactor.ASYNC_ISSUE: [
            r"async def test",
            r"await ",
            r"Promise",
            r"concurrent\.futures",
        ],
    }

    def __init__(self):
        self.risk_weights = {
            FlakinessFactor.TIME_SENSITIVE: 25,
            FlakinessFactor.RANDOM_DATA: 20,
            FlakinessFactor.EXTERNAL_DEPENDENCY: 30,
            FlakinessFactor.TIMING_ISSUE: 20,
            FlakinessFactor.STATE_LEAKAGE: 15,
            FlakinessFactor.ASYNC_ISSUE: 15,
        }

    def analyze_file(self, file_path: str) -> List[FlakinessPrediction]:
        """Analyze a test file for potential flakiness."""
        predictions = []
        path = Path(file_path)

        if not path.exists():
            return predictions

        with open(path, "r") as f:
            source_code = f.read()

        ast_tree = None
        try:
            ast_tree = ast.parse(source_code)
        except SyntaxError:
            return predictions

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                pred = self._analyze_test_function(node, source_code, path.name)
                predictions.append(pred)

        return predictions

    def _analyze_test_function(
        self,
        func_node: ast.FunctionDef,
        source_code: str,
        file_name: str,
    ) -> FlakinessPrediction:
        """Analyze a single test function."""
        func_source = ast.get_source_segment(source_code, func_node)
        factors = []
        factor_details = {}
        recommendations = []
        suggested_fixes = []

        for factor, patterns in self.FLAKY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, func_source or ""):
                    factors.append(factor)
                    factor_details[factor.value] = self._get_factor_details(
                        factor, func_source
                    )

                    fix = self._suggest_fix(factor)
                    if fix:
                        suggested_fixes.append(fix)

                    rec = self._get_recommendation(factor)
                    if rec:
                        recommendations.append(rec)

        risk_score = sum(self.risk_weights.get(f, 0) for f in factors)
        risk_score = min(risk_score, 100)

        risk_level = self._calculate_risk_level(risk_score)

        return FlakinessPrediction(
            test_file=file_name,
            test_name=func_node.name,
            risk_level=risk_level,
            risk_score=risk_score,
            factors_detected=factors,
            factor_details=factor_details,
            recommendations=recommendations,
            suggested_fixes=suggested_fixes,
        )

    def _get_factor_details(
        self, factor: FlakinessFactor, source: str
    ) -> Dict[str, Any]:
        """Get detailed information about a detected factor."""
        matches = []
        patterns = self.FLAKY_PATTERNS.get(factor, [])

        for pattern in patterns:
            for match in re.finditer(pattern, source):
                matches.append(
                    {
                        "line": source[: match.start()].count("\n") + 1,
                        "match": match.group(0),
                    }
                )

        return {"matches": matches, "count": len(matches)}

    def _suggest_fix(self, factor: FlakinessFactor) -> Optional[Dict[str, Any]]:
        """Suggest a fix for a specific flakiness factor."""
        fixes = {
            FlakinessFactor.TIME_SENSITIVE: {
                "type": "replace_sleep",
                "description": "Replace sleep with dynamic waits",
                "example": "page.wait_for_selector('.element', state='visible')",
            },
            FlakinessFactor.RANDOM_DATA: {
                "type": "use_fixed_data",
                "description": "Use fixed test data instead of random",
                "example": "Use constants or fixtures",
            },
            FlakinessFactor.EXTERNAL_DEPENDENCY: {
                "type": "mock_dependency",
                "description": "Mock external API calls",
                "example": "Use responses library or unittest.mock",
            },
            FlakinessFactor.TIMING_ISSUE: {
                "type": "improve_wait",
                "description": "Use Playwright's auto-waiting capabilities",
                "example": "page.click('.button') instead of explicit waits",
            },
            FlakinessFactor.STATE_LEAKAGE: {
                "type": "isolation",
                "description": "Ensure test isolation with fresh state",
                "example": "Use test fixtures with proper cleanup",
            },
            FlakinessFactor.ASYNC_ISSUE: {
                "type": "proper_await",
                "description": "Ensure proper async handling",
                "example": "Use await for all async operations",
            },
        }
        return fixes.get(factor)

    def _get_recommendation(self, factor: FlakinessFactor) -> Optional[str]:
        """Get a recommendation for a specific factor."""
        recs = {
            FlakinessFactor.TIME_SENSITIVE: "Replace hardcoded sleep() with Playwright's auto-waiting or explicit waits",
            FlakinessFactor.RANDOM_DATA: "Use deterministic test data from fixtures instead of random values",
            FlakinessFactor.EXTERNAL_DEPENDENCY: "Mock external API calls to avoid network flakiness",
            FlakinessFactor.TIMING_ISSUE: "Use more robust wait conditions or increase test timeout",
            FlakinessFactor.STATE_LEAKAGE: "Ensure proper test isolation with fresh browser context per test",
            FlakinessFactor.ASYNC_ISSUE: "Ensure all async operations are properly awaited",
        }
        return recs.get(factor)

    def _calculate_risk_level(self, score: float) -> FlakinessRiskLevel:
        """Calculate risk level from score."""
        if score >= 70:
            return FlakinessRiskLevel.CRITICAL
        elif score >= 50:
            return FlakinessRiskLevel.HIGH
        elif score >= 25:
            return FlakinessRiskLevel.MEDIUM
        return FlakinessRiskLevel.LOW


class FlakinessPredictor:
    """
    High-level predictor that combines AST analysis with historical data.
    """

    def __init__(self):
        self.analyzer = FlakinessAnalyzer()
        self.history: Dict[str, List[FlakinessPrediction]] = {}

    def predict(
        self,
        test_file: str,
        test_name: Optional[str] = None,
    ) -> FlakinessPrediction:
        """Predict flakiness for a test."""
        predictions = self.analyzer.analyze_file(test_file)

        if test_name:
            for pred in predictions:
                if pred.test_name == test_name:
                    return pred

        return (
            predictions[0]
            if predictions
            else FlakinessPrediction(
                test_file=test_file,
                test_name=test_name,
                risk_level=FlakinessRiskLevel.LOW,
                risk_score=0,
            )
        )

    def predict_directory(self, directory: str) -> List[FlakinessPrediction]:
        """Predict flakiness for all tests in a directory."""
        predictions = []
        path = Path(directory)

        for test_file in path.rglob("test_*.py"):
            preds = self.analyzer.analyze_file(str(test_file))
            predictions.extend(preds)

        return predictions

    def generate_report(self, predictions: List[FlakinessPrediction]) -> Dict[str, Any]:
        """Generate a flakiness report."""
        total = len(predictions)
        by_risk = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for pred in predictions:
            by_risk[pred.risk_level.value] += 1

        avg_score = sum(p.risk_score for p in predictions) / total if total else 0

        high_risk_tests = [
            {
                "test": p.test_name or p.test_file,
                "risk_score": p.risk_score,
                "factors": [f.value for f in p.factors_detected],
            }
            for p in predictions
            if p.risk_level in (FlakinessRiskLevel.HIGH, FlakinessRiskLevel.CRITICAL)
        ]

        return {
            "total_tests": total,
            "risk_distribution": by_risk,
            "average_risk_score": avg_score,
            "high_risk_tests": high_risk_tests,
            "recommendations": self._consolidate_recommendations(predictions),
        }

    def _consolidate_recommendations(
        self, predictions: List[FlakinessPrediction]
    ) -> List[str]:
        """Consolidate recommendations from all predictions."""
        all_recs = set()
        for pred in predictions:
            all_recs.update(pred.recommendations)
        return list(all_recs)


__all__ = [
    "FlakinessAnalyzer",
    "FlakinessPredictor",
    "FlakinessPrediction",
    "FlakinessRiskLevel",
    "FlakinessFactor",
]
