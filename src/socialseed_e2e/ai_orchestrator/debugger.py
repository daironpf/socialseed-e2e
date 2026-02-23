"""AI-Powered Debugger for autonomous test debugging.

This module provides intelligent debugging capabilities that analyze test
failures, identify root causes, and suggest or apply fixes automatically.
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from socialseed_e2e.ai_orchestrator.models import DebugAnalysis, TestCase, TestResult

logger = logging.getLogger(__name__)


class LogAnalyzer:
    """Analyzes logs to extract relevant information."""

    ERROR_PATTERNS = {
        "assertion_error": [
            r"AssertionError",
            r"assert.*failed",
            r"expected.*but got",
        ],
        "timeout_error": [
            r"TimeoutError",
            r"timed out",
            r"deadline exceeded",
        ],
        "network_error": [
            r"ConnectionError",
            r"Connection refused",
            r"Network is unreachable",
            r"No route to host",
        ],
        "authentication_error": [
            r"401",
            r"Unauthorized",
            r"Authentication failed",
            r"Invalid token",
        ],
        "authorization_error": [
            r"403",
            r"Forbidden",
            r"Access denied",
            r"Insufficient permissions",
        ],
        "not_found_error": [
            r"404",
            r"Not found",
            r"Does not exist",
        ],
        "validation_error": [
            r"ValidationError",
            r"Invalid input",
            r"Bad request",
            r"422",
        ],
        "server_error": [
            r"500",
            r"502",
            r"503",
            r"504",
            r"Internal server error",
        ],
        "database_error": [
            r"DatabaseError",
            r"IntegrityError",
            r"OperationalError",
        ],
    }

    def classify_error(self, error_message: str, stack_trace: str) -> str:
        """Classify error type from message and stack trace.

        Args:
            error_message: Error message
            stack_trace: Stack trace

        Returns:
            Error classification
        """
        combined = f"{error_message}\n{stack_trace}".lower()

        for error_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    return error_type

        return "unknown_error"

    def extract_relevant_logs(self, logs: List[str], error_time: datetime) -> List[str]:
        """Extract logs relevant to the error.

        Args:
            logs: All logs
            error_time: Time of error

        Returns:
            Relevant logs
        """
        # For now, return last 50 log lines
        return logs[-50:] if len(logs) > 50 else logs

    def extract_request_info(self, logs: List[str]) -> Optional[Dict[str, Any]]:
        """Extract HTTP request information from logs.

        Args:
            logs: Log lines

        Returns:
            Request info or None
        """
        request_info = None

        for log in logs:
            # Look for HTTP request patterns
            match = re.search(r"(GET|POST|PUT|DELETE|PATCH)\s+(\S+)\s+-\s+(\d+)", log)
            if match:
                request_info = {
                    "method": match.group(1),
                    "url": match.group(2),
                    "status": int(match.group(3)),
                }

        return request_info


class RootCauseAnalyzer:
    """Analyzes root causes of test failures."""

    COMMON_CAUSES = {
        "assertion_error": [
            "Data mismatch between expected and actual values",
            "Race condition causing intermittent data differences",
            "Schema changes not reflected in test expectations",
            "Test data corruption or staleness",
        ],
        "timeout_error": [
            "Service degradation or high latency",
            "Missing or incorrect timeout configuration",
            "Resource contention or deadlock",
            "External dependency slowness",
        ],
        "network_error": [
            "Service not started or crashed",
            "Network connectivity issues",
            "DNS resolution failures",
            "Firewall or security group blocking",
        ],
        "authentication_error": [
            "Expired or invalid authentication token",
            "Missing authentication headers",
            "Test user credentials changed",
            "Authentication service unavailable",
        ],
        "authorization_error": [
            "Test user lacks required permissions",
            "Role-based access control misconfiguration",
            "Missing authorization headers",
        ],
        "not_found_error": [
            "Resource was deleted before test accessed it",
            "Incorrect resource identifier in test",
            "Race condition in resource creation",
        ],
        "validation_error": [
            "Invalid test data format",
            "Missing required fields",
            "Constraint violations",
        ],
        "server_error": [
            "Application bug causing internal error",
            "Database connection issues",
            "Memory or resource exhaustion",
            "Unhandled exception in application",
        ],
        "database_error": [
            "Database constraint violations",
            "Connection pool exhaustion",
            "Lock contention or deadlock",
            "Schema migration not applied",
        ],
    }

    def analyze(
        self,
        test_case: TestCase,
        error_message: str,
        stack_trace: str,
        logs: List[str],
    ) -> Tuple[str, float]:
        """Analyze root cause of failure.

        Args:
            test_case: Test case that failed
            error_message: Error message
            stack_trace: Stack trace
            logs: Execution logs

        Returns:
            Tuple of (root_cause, confidence_score)
        """
        # Classify error type
        log_analyzer = LogAnalyzer()
        error_type = log_analyzer.classify_error(error_message, stack_trace)

        # Get potential causes
        potential_causes = self.COMMON_CAUSES.get(error_type, ["Unknown error"])

        # Score each potential cause based on evidence
        cause_scores = []
        for cause in potential_causes:
            score = self._score_cause(cause, test_case, error_message, stack_trace, logs)
            cause_scores.append((cause, score))

        # Return highest scoring cause
        if cause_scores:
            best_cause, best_score = max(cause_scores, key=lambda x: x[1])
            return best_cause, best_score

        return "Unable to determine root cause", 0.0

    def _score_cause(
        self,
        cause: str,
        test_case: TestCase,
        error_message: str,
        stack_trace: str,
        logs: List[str],
    ) -> float:
        """Score a potential cause based on evidence.

        Args:
            cause: Potential cause
            test_case: Test case
            error_message: Error message
            stack_trace: Stack trace
            logs: Logs

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        combined_text = f"{error_message} {stack_trace} {' '.join(logs)}".lower()

        # Score based on keyword matches
        if "race" in cause.lower() and ("concurrent" in combined_text or "thread" in combined_text):
            score += 0.2

        if "timeout" in cause.lower() and "timeout" in combined_text:
            score += 0.2

        if "token" in cause.lower() and "token" in combined_text:
            score += 0.2

        if "database" in cause.lower() and any(
            word in combined_text for word in ["db", "sql", "query", "database"]
        ):
            score += 0.2

        if "service" in cause.lower() and "unavailable" in combined_text:
            score += 0.2

        return min(score, 1.0)


class FixSuggester:
    """Suggests fixes for identified issues."""

    FIX_TEMPLATES = {
        "assertion_error": [
            {
                "description": "Add tolerance to numeric assertions",
                "code_changes": [
                    {
                        "pattern": r"assertEqual\(([^,]+),\s*([^)]+)\)",
                        "replacement": r"assertAlmostEqual(\1, \2, delta=0.01)",
                    }
                ],
            },
            {
                "description": "Update expected values to match actual response",
                "action": "manual_review",
            },
        ],
        "timeout_error": [
            {
                "description": "Increase timeout configuration",
                "code_changes": [
                    {
                        "pattern": r"timeout\s*=\s*(\d+)",
                        "replacement": r"timeout=\1 * 2",
                    }
                ],
            },
            {
                "description": "Add retry logic for transient failures",
                "code_changes": [
                    {
                        "pattern": r"def (\w+)\(",
                        "replacement": r"@retry(stop=stop_after_attempt(3))\ndef \1(",
                    }
                ],
            },
        ],
        "network_error": [
            {
                "description": "Add wait for service to be ready",
                "code_changes": [
                    {
                        "pattern": r"(setup|setUp)",
                        "replacement": r"\1 with wait_for_healthy",
                    }
                ],
            },
            {
                "description": "Verify service is running before test",
                "action": "add_health_check",
            },
        ],
        "authentication_error": [
            {
                "description": "Refresh authentication token before test",
                "code_changes": [
                    {
                        "pattern": r"headers\s*=\s*",
                        "replacement": r"headers = get_fresh_token(); ",
                    }
                ],
            },
        ],
        "authorization_error": [
            {
                "description": "Update test user permissions",
                "action": "update_permissions",
            },
        ],
    }

    def suggest_fixes(
        self,
        error_type: str,
        root_cause: str,
        test_case: TestCase,
    ) -> List[Dict[str, Any]]:
        """Suggest fixes for the identified issue.

        Args:
            error_type: Classified error type
            root_cause: Identified root cause
            test_case: Test case

        Returns:
            List of suggested fixes
        """
        fixes = self.FIX_TEMPLATES.get(error_type, [])

        # Add generic fallback fix
        if not fixes:
            fixes = [
                {
                    "description": "Review test for flakiness patterns",
                    "action": "run_self_healer",
                }
            ]

        # Enhance suggestions with context
        enhanced_fixes = []
        for fix in fixes:
            enhanced_fix = {
                **fix,
                "applicability_score": self._score_applicability(fix, test_case),
                "risk_level": self._assess_risk(fix),
            }
            enhanced_fixes.append(enhanced_fix)

        # Sort by applicability
        enhanced_fixes.sort(key=lambda x: x["applicability_score"], reverse=True)

        return enhanced_fixes

    def _score_applicability(self, fix: Dict[str, Any], test_case: TestCase) -> float:
        """Score how applicable a fix is.

        Args:
            fix: Fix suggestion
            test_case: Test case

        Returns:
            Applicability score
        """
        score = 0.7  # Base score

        if "code_changes" in fix:
            score += 0.2

        if fix.get("action") == "manual_review":
            score -= 0.1  # Prefer automated fixes

        return score

    def _assess_risk(self, fix: Dict[str, Any]) -> str:
        """Assess the risk level of applying a fix.

        Args:
            fix: Fix suggestion

        Returns:
            Risk level: low, medium, high
        """
        if "code_changes" not in fix:
            return "low"

        # Simple heuristic: more changes = higher risk
        num_changes = len(fix.get("code_changes", []))
        if num_changes > 2:
            return "high"
        elif num_changes > 1:
            return "medium"
        else:
            return "low"


class AIDebugger:
    """AI-powered debugging system."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.log_analyzer = LogAnalyzer()
        self.root_cause_analyzer = RootCauseAnalyzer()
        self.fix_suggester = FixSuggester()
        self.analysis_history: List[DebugAnalysis] = []
        self.history_path = self.project_path / ".e2e" / "debug_analysis.json"
        self._load_history()

    def _load_history(self) -> None:
        """Load analysis history."""
        if self.history_path.exists():
            try:
                with open(self.history_path, "r") as f:
                    data = json.load(f)
                    self.analysis_history = [DebugAnalysis.model_validate(a) for a in data]
            except Exception as e:
                logger.warning(f"Failed to load analysis history: {e}")

    def _save_history(self) -> None:
        """Save analysis history."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.history_path, "w") as f:
            json.dump(
                [a.model_dump() for a in self.analysis_history],
                f,
                indent=2,
                default=str,
            )

    def debug(
        self,
        test_case: TestCase,
        test_result: TestResult,
        execution_id: str,
    ) -> DebugAnalysis:
        """Debug a failed test.

        Args:
            test_case: Test case that failed
            test_result: Test execution result
            execution_id: Execution ID

        Returns:
            Debug analysis result
        """
        logger.info(f"Debugging test: {test_case.id}")

        # Classify error
        error_type = self.log_analyzer.classify_error(
            test_result.error_message or "", test_result.stack_trace or ""
        )

        # Analyze root cause
        root_cause, confidence = self.root_cause_analyzer.analyze(
            test_case,
            test_result.error_message or "",
            test_result.stack_trace or "",
            test_result.logs,
        )

        # Suggest fixes
        suggested_fixes = self.fix_suggester.suggest_fixes(
            error_type,
            root_cause,
            test_case,
        )

        # Generate code changes from suggestions
        code_changes = self._generate_code_changes(test_case, suggested_fixes)

        # Determine if human review is needed
        requires_review = confidence < 0.7 or any(
            f.get("risk_level") == "high" for f in suggested_fixes
        )

        # Create analysis
        analysis = DebugAnalysis(
            analysis_id=self._generate_analysis_id(),
            test_id=test_case.id,
            execution_id=execution_id,
            failure_type=error_type,
            root_cause=root_cause,
            confidence_score=confidence,
            suggested_fixes=suggested_fixes,
            code_changes=code_changes,
            requires_human_review=requires_review,
        )

        # Save analysis
        self.analysis_history.append(analysis)
        self._save_history()

        logger.info(f"Debug analysis complete: {error_type} - Confidence: {confidence:.2f}")

        return analysis

    def _generate_code_changes(
        self,
        test_case: TestCase,
        suggested_fixes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate specific code changes from suggestions.

        Args:
            test_case: Test case
            suggested_fixes: Suggested fixes

        Returns:
            List of code changes
        """
        code_changes = []

        test_file = self.project_path / test_case.module
        if not test_file.exists():
            return code_changes

        try:
            with open(test_file, "r") as f:
                source_code = f.read()

            for fix in suggested_fixes:
                for change in fix.get("code_changes", []):
                    pattern = change.get("pattern", "")
                    replacement = change.get("replacement", "")

                    if pattern and replacement:
                        # Check if pattern exists in code
                        if re.search(pattern, source_code):
                            code_changes.append(
                                {
                                    "file": str(test_file),
                                    "pattern": pattern,
                                    "replacement": replacement,
                                    "description": fix.get("description", ""),
                                }
                            )

        except Exception as e:
            logger.warning(f"Failed to generate code changes: {e}")

        return code_changes

    def apply_fix(self, analysis_id: str, fix_index: int = 0) -> bool:
        """Apply a suggested fix.

        Args:
            analysis_id: Analysis ID
            fix_index: Index of fix to apply

        Returns:
            True if fix was applied
        """
        # Find analysis
        analysis = None
        for a in self.analysis_history:
            if a.analysis_id == analysis_id:
                analysis = a
                break

        if not analysis:
            logger.error(f"Analysis not found: {analysis_id}")
            return False

        if analysis.requires_human_review:
            logger.warning("Fix requires human review, not applying automatically")
            return False

        # Apply code changes
        for change in analysis.code_changes:
            try:
                file_path = Path(change["file"])

                with open(file_path, "r") as f:
                    content = f.read()

                # Apply replacement
                new_content = re.sub(change["pattern"], change["replacement"], content)

                if new_content != content:
                    with open(file_path, "w") as f:
                        f.write(new_content)

                    logger.info(f"Applied fix to {file_path}")

            except Exception as e:
                logger.error(f"Failed to apply fix: {e}")
                return False

        return True

    def get_debug_report(self, execution_id: str) -> Dict[str, Any]:
        """Get comprehensive debug report for an execution.

        Args:
            execution_id: Execution ID

        Returns:
            Debug report
        """
        analyses = [a for a in self.analysis_history if a.execution_id == execution_id]

        if not analyses:
            return {"error": "No analyses found for execution"}

        # Group by failure type
        failures_by_type: Dict[str, List[DebugAnalysis]] = {}
        for analysis in analyses:
            error_type = analysis.failure_type
            if error_type not in failures_by_type:
                failures_by_type[error_type] = []
            failures_by_type[error_type].append(analysis)

        return {
            "execution_id": execution_id,
            "total_failures": len(analyses),
            "failures_by_type": {
                error_type: len(items) for error_type, items in failures_by_type.items()
            },
            "average_confidence": sum(a.confidence_score for a in analyses) / len(analyses),
            "requiring_human_review": sum(1 for a in analyses if a.requires_human_review),
            "analyses": [a.model_dump() for a in analyses],
        }

    def find_similar_failures(self, test_id: str, limit: int = 5) -> List[DebugAnalysis]:
        """Find similar previous failures.

        Args:
            test_id: Test ID
            limit: Maximum number to return

        Returns:
            List of similar failure analyses
        """
        # Get recent analyses for this test
        test_analyses = [a for a in self.analysis_history if a.test_id == test_id]

        if not test_analyses:
            return []

        # Get the most recent
        latest = max(test_analyses, key=lambda a: a.created_at)

        # Find similar failures (same error type)
        similar = [
            a
            for a in self.analysis_history
            if a.failure_type == latest.failure_type and a.test_id != test_id
        ]

        # Sort by date
        similar.sort(key=lambda a: a.created_at, reverse=True)

        return similar[:limit]

    def _generate_analysis_id(self) -> str:
        """Generate unique analysis ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:6]
        return f"dbg_{timestamp}_{random_suffix}"
