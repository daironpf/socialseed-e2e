"""Autonomous Test Runner for AI-driven test execution.

This module provides intelligent test execution with features like:
- Risk-based prioritization
- Intelligent retry logic with learning
- Parallel execution
- Real-time monitoring and reporting
"""

import hashlib
import json
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from socialseed_e2e.ai_orchestrator.models import (
    FailurePattern,
    OrchestratorConfig,
    RetryStrategy,
    TestCase,
    TestExecution,
    TestResult,
    TestStatus,
)
from socialseed_e2e.ai_orchestrator.self_healer import SelfHealer

logger = logging.getLogger(__name__)


class IntelligentRetryManager:
    """Manages retry strategies with learning capabilities."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(".e2e/retry_strategies.json")
        self.strategies: Dict[str, RetryStrategy] = {}
        self.patterns: Dict[str, FailurePattern] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load saved strategies and patterns."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for pattern_id, pattern_data in data.get("patterns", {}).items():
                        self.patterns[pattern_id] = FailurePattern.model_validate(pattern_data)
                    for pattern_id, strategy_data in data.get("strategies", {}).items():
                        self.strategies[pattern_id] = RetryStrategy.model_validate(strategy_data)
            except Exception as e:
                logger.warning(f"Failed to load retry data: {e}")

    def _save_data(self) -> None:
        """Save strategies and patterns."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "patterns": {k: p.model_dump() for k, p in self.patterns.items()},
            "strategies": {k: s.model_dump() for k, s in self.strategies.items()},
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def detect_pattern(self, error_message: str, stack_trace: str) -> Optional[FailurePattern]:
        """Detect a failure pattern from error information.

        Args:
            error_message: Error message
            stack_trace: Stack trace

        Returns:
            Detected pattern or None
        """
        # Generate pattern signature
        signature = self._generate_signature(error_message, stack_trace)

        # Check if pattern exists
        for pattern in self.patterns.values():
            if pattern.signature == signature:
                pattern.frequency += 1
                pattern.last_seen = datetime.utcnow()
                return pattern

        return None

    def record_failure(
        self,
        test_id: str,
        error_message: str,
        stack_trace: str,
        suggested_fix: Optional[str] = None,
    ) -> FailurePattern:
        """Record a new failure pattern.

        Args:
            test_id: Test that failed
            error_message: Error message
            stack_trace: Stack trace
            suggested_fix: Optional AI-suggested fix

        Returns:
            Recorded failure pattern
        """
        signature = self._generate_signature(error_message, stack_trace)

        # Check if pattern already exists
        for pattern in self.patterns.values():
            if pattern.signature == signature:
                pattern.frequency += 1
                pattern.last_seen = datetime.utcnow()
                if test_id not in pattern.affected_tests:
                    pattern.affected_tests.append(test_id)
                if suggested_fix:
                    pattern.suggested_fix = suggested_fix
                return pattern

        # Create new pattern
        pattern_id = hashlib.md5(signature.encode()).hexdigest()[:12]

        pattern_type = self._classify_failure_type(error_message, stack_trace)

        pattern = FailurePattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            signature=signature,
            frequency=1,
            affected_tests=[test_id],
            suggested_fix=suggested_fix,
        )

        self.patterns[pattern_id] = pattern

        # Create default strategy for this pattern
        self._create_default_strategy(pattern)

        return pattern

    def get_retry_strategy(self, pattern_id: str) -> RetryStrategy:
        """Get retry strategy for a pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Retry strategy
        """
        if pattern_id in self.strategies:
            return self.strategies[pattern_id]

        # Return default strategy
        return RetryStrategy(
            pattern_id=pattern_id,
            max_retries=3,
            backoff_type="exponential",
            base_delay_ms=1000,
            max_delay_ms=30000,
        )

    def update_strategy_success(self, pattern_id: str, success: bool) -> None:
        """Update strategy based on success/failure.

        Args:
            pattern_id: Pattern identifier
            success: Whether retry succeeded
        """
        if pattern_id not in self.strategies:
            return

        strategy = self.strategies[pattern_id]
        strategy.total_applied += 1

        # Update success rate
        current_rate = strategy.success_rate
        total = strategy.total_applied

        if success:
            strategy.success_rate = (current_rate * (total - 1) + 1.0) / total
        else:
            strategy.success_rate = (current_rate * (total - 1)) / total

        self._save_data()

    def _generate_signature(self, error_message: str, stack_trace: str) -> str:
        """Generate a unique signature for a failure pattern."""
        # Normalize the error for signature generation
        normalized = f"{error_message.lower()}::{stack_trace[:500].lower()}"

        # Remove variable parts (timestamps, IDs, etc.)
        import re

        normalized = re.sub(r"\d{4}-\d{2}-\d{2}", "[DATE]", normalized)
        normalized = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "[UUID]",
            normalized,
        )
        normalized = re.sub(r"\d+", "[NUM]", normalized)

        return hashlib.md5(normalized.encode()).hexdigest()

    def _classify_failure_type(self, error_message: str, stack_trace: str) -> str:
        """Classify the type of failure."""
        error_lower = error_message.lower()

        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "assertion" in error_lower:
            return "assertion_error"
        elif "connection" in error_lower or "network" in error_lower:
            return "network_error"
        elif "rate limit" in error_lower or "429" in error_lower:
            return "rate_limit"
        elif "5" in error_lower and "error" in error_lower:
            return "server_error"
        else:
            return "unknown"

    def _create_default_strategy(self, pattern: FailurePattern) -> None:
        """Create a default retry strategy for a pattern."""
        strategy = RetryStrategy(
            pattern_id=pattern.pattern_id,
            max_retries=3,
            backoff_type="exponential",
            base_delay_ms=1000,
            max_delay_ms=30000,
        )

        # Customize based on pattern type
        if pattern.pattern_type == "timeout":
            strategy.backoff_type = "linear"
            strategy.base_delay_ms = 2000
        elif pattern.pattern_type == "rate_limit":
            strategy.backoff_type = "exponential"
            strategy.base_delay_ms = 5000
            strategy.max_delay_ms = 60000
        elif pattern.pattern_type == "server_error":
            strategy.max_retries = 5
            strategy.base_delay_ms = 2000

        self.strategies[pattern.pattern_id] = strategy


class TestExecutor:
    """Executes individual test cases with retry and monitoring."""

    def __init__(
        self,
        retry_manager: IntelligentRetryManager,
        self_healer: Optional[SelfHealer] = None,
        config: Optional[OrchestratorConfig] = None,
    ):
        self.retry_manager = retry_manager
        self.self_healer = self_healer
        self.config = config or OrchestratorConfig()

    def execute(
        self,
        test_case: TestCase,
        context_factory: Callable[[], Any],
    ) -> TestResult:
        """Execute a single test case.

        Args:
            test_case: Test case to execute
            context_factory: Factory function to create test context

        Returns:
            Test execution result
        """
        started_at = datetime.utcnow()
        attempts = 0
        max_attempts = self.config.max_auto_fix_attempts if self.config.enable_self_healing else 1

        result = TestResult(
            test_id=test_case.id,
            status=TestStatus.PENDING,
            started_at=started_at,
            attempts=0,
        )

        while attempts < max_attempts:
            attempts += 1
            result.attempts = attempts

            try:
                # Create context for this attempt
                context = context_factory()

                # Execute the test
                self._run_test(test_case, context)

                # Success!
                result.status = TestStatus.PASSED
                result.completed_at = datetime.utcnow()
                result.duration_ms = int((result.completed_at - started_at).total_seconds() * 1000)

                # Cleanup
                if hasattr(context, "teardown"):
                    context.teardown()

                return result

            except Exception as e:
                error_message = str(e)
                stack_trace = traceback.format_exc()

                # Check for known failure patterns
                pattern = self.retry_manager.detect_pattern(error_message, stack_trace)

                if pattern:
                    # Use intelligent retry
                    strategy = self.retry_manager.get_retry_strategy(pattern.pattern_id)

                    if attempts <= strategy.max_retries:
                        delay = self._calculate_delay(strategy, attempts)
                        logger.info(f"Retry {attempts} for {test_case.id} after {delay}ms")
                        time.sleep(delay / 1000.0)
                        continue

                # Try self-healing if enabled
                if self.config.enable_self_healing and attempts < max_attempts and self.self_healer:
                    healed = self.self_healer.attempt_heal(test_case, error_message, stack_trace)

                    if healed:
                        result.healed = True
                        result.healing_applied = healed
                        logger.info(f"Test {test_case.id} was healed: {healed}")
                        continue

                # Final failure
                result.status = TestStatus.FAILED
                result.error_message = error_message
                result.stack_trace = stack_trace
                result.completed_at = datetime.utcnow()
                result.duration_ms = int((result.completed_at - started_at).total_seconds() * 1000)

                # Record failure pattern
                self.retry_manager.record_failure(
                    test_case.id,
                    error_message,
                    stack_trace,
                    suggested_fix=None,  # Could be populated by AI analysis
                )

                return result

        return result

    def _run_test(self, test_case: TestCase, context: Any) -> None:
        """Run the actual test.

        Args:
            test_case: Test case to run
            context: Test context
        """
        # Load and execute the test module
        import importlib.util

        module_path = Path(test_case.module)
        if not module_path.exists():
            raise FileNotFoundError(f"Test module not found: {module_path}")

        spec = importlib.util.spec_from_file_location("test_module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Call the run function
        if hasattr(module, "run"):
            module.run(context)
        else:
            raise AttributeError(f"Test module {module_path} has no 'run' function")

    def _calculate_delay(self, strategy: RetryStrategy, attempt: int) -> int:
        """Calculate retry delay based on strategy.

        Args:
            strategy: Retry strategy
            attempt: Current attempt number

        Returns:
            Delay in milliseconds
        """
        if strategy.backoff_type == "exponential":
            delay = strategy.base_delay_ms * (2 ** (attempt - 1))
        elif strategy.backoff_type == "linear":
            delay = strategy.base_delay_ms * attempt
        else:  # fixed
            delay = strategy.base_delay_ms

        return min(delay, strategy.max_delay_ms)


class AutonomousRunner:
    """Main autonomous test runner with orchestration capabilities."""

    def __init__(
        self,
        project_path: str,
        config: Optional[OrchestratorConfig] = None,
    ):
        self.project_path = Path(project_path)
        self.config = config or OrchestratorConfig()
        self.retry_manager = IntelligentRetryManager(
            storage_path=self.project_path / ".e2e/retry_strategies.json"
        )
        self.self_healer = SelfHealer(project_path) if self.config.enable_self_healing else None
        self.executor = TestExecutor(self.retry_manager, self.self_healer, self.config)
        self.execution_history: List[TestExecution] = []

    def run_strategy(
        self,
        strategy: Any,  # TestStrategy
        context_factory: Callable[[], Any],
        progress_callback: Optional[Callable[[TestResult], None]] = None,
    ) -> TestExecution:
        """Execute a test strategy autonomously.

        Args:
            strategy: Test strategy to execute
            context_factory: Factory to create test contexts
            progress_callback: Optional callback for progress updates

        Returns:
            Test execution results
        """
        logger.info(f"Starting autonomous execution of strategy: {strategy.name}")

        execution = TestExecution(
            id=self._generate_execution_id(),
            strategy_id=strategy.id,
            status=TestStatus.RUNNING,
        )

        # Execute test cases
        if self.config.parallel_workers > 1:
            results = self._run_parallel(strategy.test_cases, context_factory, progress_callback)
        else:
            results = self._run_sequential(strategy.test_cases, context_factory, progress_callback)

        execution.results = results
        execution.completed_at = datetime.utcnow()
        execution.status = self._determine_overall_status(results)
        execution.summary = self._calculate_summary(results)

        # Save execution
        self.execution_history.append(execution)
        self._save_execution(execution)

        logger.info(f"Strategy execution completed: {execution.status.value}")
        logger.info(f"Summary: {execution.summary}")

        return execution

    def _run_sequential(
        self,
        test_cases: List[TestCase],
        context_factory: Callable[[], Any],
        progress_callback: Optional[Callable[[TestResult], None]] = None,
    ) -> List[TestResult]:
        """Run tests sequentially.

        Args:
            test_cases: Test cases to run
            context_factory: Context factory
            progress_callback: Progress callback

        Returns:
            List of results
        """
        results: List[TestResult] = []

        for i, test_case in enumerate(test_cases):
            logger.info(f"Running test {i + 1}/{len(test_cases)}: {test_case.id}")

            result = self.executor.execute(test_case, context_factory)
            results.append(result)

            if progress_callback:
                progress_callback(result)

        return results

    def _run_parallel(
        self,
        test_cases: List[TestCase],
        context_factory: Callable[[], Any],
        progress_callback: Optional[Callable[[TestResult], None]] = None,
    ) -> List[TestResult]:
        """Run tests in parallel with dependency management.

        Args:
            test_cases: Test cases to run
            context_factory: Context factory
            progress_callback: Progress callback

        Returns:
            List of results
        """
        results: List[TestResult] = []
        completed_tests: Dict[str, TestResult] = {}

        # Group tests by parallelization groups
        # For simplicity, we'll run all tests from the same service sequentially
        # and different services in parallel
        service_tests: Dict[str, List[TestCase]] = {}
        for test in test_cases:
            if test.service not in service_tests:
                service_tests[test.service] = []
            service_tests[test.service].append(test)

        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            futures: Dict[Any, str] = {}

            for service, tests in service_tests.items():
                future = executor.submit(self._run_service_tests, tests, context_factory)
                futures[future] = service

            for future in as_completed(futures):
                service = futures[future]
                try:
                    service_results = future.result()
                    results.extend(service_results)

                    if progress_callback:
                        for result in service_results:
                            progress_callback(result)

                except Exception as e:
                    logger.error(f"Service {service} failed: {e}")

        return results

    def _run_service_tests(
        self,
        test_cases: List[TestCase],
        context_factory: Callable[[], Any],
    ) -> List[TestResult]:
        """Run tests for a single service.

        Args:
            test_cases: Test cases for the service
            context_factory: Context factory

        Returns:
            List of results
        """
        results: List[TestResult] = []

        for test_case in test_cases:
            result = self.executor.execute(test_case, context_factory)
            results.append(result)

        return results

    def _determine_overall_status(self, results: List[TestResult]) -> TestStatus:
        """Determine overall execution status.

        Args:
            results: All test results

        Returns:
            Overall status
        """
        if not results:
            return TestStatus.PASSED

        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        flaky = sum(1 for r in results if r.status == TestStatus.FLAKY)
        healed = sum(1 for r in results if r.healed)

        if failed > 0:
            return TestStatus.FAILED
        elif flaky > 0:
            return TestStatus.FLAKY
        elif healed > 0:
            return TestStatus.HEALED
        else:
            return TestStatus.PASSED

    def _calculate_summary(self, results: List[TestResult]) -> Dict[str, int]:
        """Calculate execution summary.

        Args:
            results: All test results

        Returns:
            Summary counts
        """
        summary = {
            "total": len(results),
            "passed": 0,
            "failed": 0,
            "flaky": 0,
            "skipped": 0,
            "healed": 0,
        }

        for result in results:
            status_key = result.status.value.lower()
            if status_key in summary:
                summary[status_key] += 1

            if result.healed:
                summary["healed"] += 1

        return summary

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
        return f"exec_{timestamp}_{random_suffix}"

    def _save_execution(self, execution: TestExecution) -> None:
        """Save execution to file.

        Args:
            execution: Execution to save
        """
        executions_path = self.project_path / ".e2e" / "executions"
        executions_path.mkdir(parents=True, exist_ok=True)

        file_path = executions_path / f"{execution.id}.json"

        with open(file_path, "w") as f:
            f.write(execution.model_dump_json(indent=2))

    def get_execution_history(
        self,
        limit: Optional[int] = None,
        strategy_id: Optional[str] = None,
    ) -> List[TestExecution]:
        """Get execution history.

        Args:
            limit: Maximum number of executions to return
            strategy_id: Filter by strategy ID

        Returns:
            List of executions
        """
        executions = self.execution_history

        if strategy_id:
            executions = [e for e in executions if e.strategy_id == strategy_id]

        # Sort by start time (newest first)
        executions = sorted(executions, key=lambda e: e.started_at, reverse=True)

        if limit:
            executions = executions[:limit]

        return executions

    def get_failure_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get failure statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Failure statistics
        """
        cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=days)

        stats = {
            "total_executions": 0,
            "total_failures": 0,
            "most_common_failures": [],
            "failure_rate_by_test": {},
            "retry_success_rate": 0.0,
        }

        recent_executions = [e for e in self.execution_history if e.started_at > cutoff]

        for execution in recent_executions:
            stats["total_executions"] += 1

            for result in execution.results:
                if result.status == TestStatus.FAILED:
                    stats["total_failures"] += 1

                    # Track failures by test
                    if result.test_id not in stats["failure_rate_by_test"]:
                        stats["failure_rate_by_test"][result.test_id] = {
                            "failures": 0,
                            "total": 0,
                        }
                    stats["failure_rate_by_test"][result.test_id]["failures"] += 1
                    stats["failure_rate_by_test"][result.test_id]["total"] += 1

        return stats
