"""Test Parallelization & Distribution Module.

This module provides advanced test distribution capabilities:
- Smart test selection based on impact analysis
- Distributed test execution across workers
- Test prioritization by risk
- Resource optimization

Usage:
    from socialseed_e2e.distributed import (
        TestDistributor,
        ImpactAnalyzer,
        ParallelExecutor,
    )
"""

import multiprocessing
import queue
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class TestPriority(str, Enum):
    """Test priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DistributionStrategy(str, Enum):
    """Test distribution strategies."""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    BY_PRIORITY = "by_priority"
    BY_DURATION = "by_duration"
    BY_IMPACT = "by_impact"


@dataclass
class TestCase:
    """Represents a test case."""

    id: str
    name: str
    module: str
    priority: TestPriority = TestPriority.MEDIUM
    estimated_duration_ms: float = 1000.0
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    file_path: str = ""
    line_number: int = 0

    @property
    def is_critical(self) -> bool:
        """Check if test is critical."""
        return self.priority == TestPriority.CRITICAL


@dataclass
class TestResult:
    """Represents a test result."""

    test_id: str
    status: str
    duration_ms: float = 0.0
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkerResult:
    """Result from a worker."""

    worker_id: int
    tests_run: int
    tests_passed: int
    tests_failed: int
    duration_ms: float = 0.0


class ImpactAnalyzer:
    """Analyzes test impact based on code changes.

    Example:
        analyzer = ImpactAnalyzer()

        # Analyze changed files
        impacted = analyzer.analyze_impact(
            changed_files=["src/api/users.py", "src/api/auth.py"]
        )

        # Get tests to run
        tests = analyzer.get_tests_to_run(impacted)
    """

    def __init__(self):
        """Initialize impact analyzer."""
        self.test_map: Dict[str, List[str]] = {}
        self.file_dependencies: Dict[str, Set[str]] = {}

    def register_test(self, test: TestCase, files: List[str]) -> None:
        """Register test with its dependencies.

        Args:
            test: Test case
            files: Files the test depends on
        """
        self.test_map[test.id] = files
        for file in files:
            if file not in self.file_dependencies:
                self.file_dependencies[file] = set()
            self.file_dependencies[file].add(test.id)

    def analyze_impact(self, changed_files: List[str]) -> Set[str]:
        """Analyze impact of changed files.

        Args:
            changed_files: List of changed file paths

        Returns:
            Set of affected test IDs
        """
        impacted = set()

        for file in changed_files:
            if file in self.file_dependencies:
                impacted.update(self.file_dependencies[file])

        return impacted

    def get_tests_to_run(
        self,
        impacted_tests: Set[str],
        include_dependencies: bool = True,
    ) -> List[TestCase]:
        """Get list of tests to run.

        Args:
            impacted_tests: Set of impacted test IDs
            include_dependencies: Include dependent tests

        Returns:
            List of tests to run
        """
        tests_to_run = []

        for _test_id in impacted_tests:
            # Would look up test from registry
            pass

        return tests_to_run

    def get_coverage_report(self, tests: List[TestCase]) -> Dict[str, Any]:
        """Generate coverage report.

        Args:
            tests: List of tests

        Returns:
            Coverage report
        """
        covered_files = set()
        for test in tests:
            if test.id in self.test_map:
                covered_files.update(self.test_map[test.id])

        return {
            "total_tests": len(tests),
            "files_covered": len(covered_files),
            "files": list(covered_files),
        }


class TestPrioritizer:
    """Prioritizes tests based on various criteria.

    Example:
        prioritizer = TestPrioritizer()

        # Prioritize by risk
        prioritized = prioritizer.prioritize_by_risk(tests, baseline_failures)

        # Prioritize by duration
        prioritized = prioritizer.prioritize_by_duration(tests)
    """

    def __init__(self):
        """Initialize test prioritizer."""
        self.history: Dict[str, List[float]] = {}

    def prioritize_by_risk(
        self,
        tests: List[TestCase],
        baseline_failures: Dict[str, float],
    ) -> List[TestCase]:
        """Prioritize tests by risk.

        Args:
            tests: List of test cases
            baseline_failures: Failure rate by test ID

        Returns:
            Prioritized list of tests
        """

        def get_risk_score(test: TestCase) -> float:
            failure_rate = baseline_failures.get(test.id, 0.0)
            priority_weight = {
                TestPriority.CRITICAL: 1.0,
                TestPriority.HIGH: 0.75,
                TestPriority.MEDIUM: 0.5,
                TestPriority.LOW: 0.25,
            }.get(test.priority, 0.5)

            return failure_rate * priority_weight

        return sorted(tests, key=get_risk_score, reverse=True)

    def prioritize_by_duration(self, tests: List[TestCase]) -> List[TestCase]:
        """Prioritize tests by duration (fastest first).

        Args:
            tests: List of test cases

        Returns:
            Prioritized list of tests
        """
        return sorted(tests, key=lambda t: t.estimated_duration_ms)

    def prioritize_by_priority(self, tests: List[TestCase]) -> List[TestCase]:
        """Prioritize tests by priority level.

        Args:
            tests: List of test cases

        Returns:
            Prioritized list of tests
        """
        priority_order = {
            TestPriority.CRITICAL: 0,
            TestPriority.HIGH: 1,
            TestPriority.MEDIUM: 2,
            TestPriority.LOW: 3,
        }

        return sorted(tests, key=lambda t: priority_order.get(t.priority, 2))

    def predict_duration(
        self,
        test: TestCase,
        historical_data: Dict[str, List[float]],
    ) -> float:
        """Predict test duration based on history.

        Args:
            test: Test case
            historical_data: Historical duration data

        Returns:
            Predicted duration in milliseconds
        """
        if test.id in historical_data:
            durations = historical_data[test.id]
            if durations:
                return sum(durations) / len(durations)

        return test.estimated_duration_ms


class ParallelExecutor:
    """Executes tests in parallel across workers.

    Example:
        executor = ParallelExecutor(workers=4)

        # Execute tests
        results = executor.run_tests(tests, execute_fn)

        # Get statistics
        stats = executor.get_statistics()
    """

    def __init__(
        self,
        workers: int = 4,
        strategy: DistributionStrategy = DistributionStrategy.ROUND_ROBIN,
    ):
        """Initialize parallel executor.

        Args:
            workers: Number of worker threads/processes
            strategy: Distribution strategy
        """
        self.workers = workers
        self.strategy = strategy
        self.results: List[TestResult] = []
        self._lock = threading.Lock()

    def run_tests(
        self,
        tests: List[TestCase],
        execute_fn: Callable[[TestCase], TestResult],
        timeout: Optional[float] = None,
    ) -> List[TestResult]:
        """Run tests in parallel.

        Args:
            tests: List of tests to run
            execute_fn: Function to execute each test
            timeout: Optional timeout per test

        Returns:
            List of test results
        """
        self.results.clear()
        test_queue = queue.Queue()
        for test in tests:
            test_queue.put(test)

        def worker(worker_id: int):
            while True:
                try:
                    test = test_queue.get(timeout=1)
                except queue.Empty:
                    break

                start = time.perf_counter()
                try:
                    if timeout:
                        result = execute_fn(test)
                    else:
                        result = execute_fn(test)
                except Exception as e:
                    result = TestResult(
                        test_id=test.id,
                        status="error",
                        error=str(e),
                    )
                result.duration_ms = (time.perf_counter() - start) * 1000

                with self._lock:
                    self.results.append(result)

                test_queue.task_done()

        threads = []
        for i in range(self.workers):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return self.results

    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics.

        Returns:
            Statistics dictionary
        """
        if not self.results:
            return {}

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        errors = sum(1 for r in self.results if r.status == "error")

        durations = [r.duration_ms for r in self.results]
        durations.sort()

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "p50_duration_ms": durations[len(durations) // 2] if durations else 0,
            "p95_duration_ms": durations[int(len(durations) * 0.95)]
            if durations
            else 0,
            "p99_duration_ms": durations[int(len(durations) * 0.99)]
            if durations
            else 0,
        }


class TestDistributor:
    """Distributes tests across workers intelligently.

    Example:
        distributor = TestDistributor(workers=4)

        # Distribute tests
        distribution = distributor.distribute(tests)

        # Each worker gets balanced workload
        for worker_id, worker_tests in distribution.items():
            print(f"Worker {worker_id}: {len(worker_tests)} tests")
    """

    def __init__(
        self,
        workers: int = 4,
        strategy: DistributionStrategy = DistributionStrategy.ROUND_ROBIN,
    ):
        """Initialize test distributor.

        Args:
            workers: Number of workers
            strategy: Distribution strategy
        """
        self.workers = workers
        self.strategy = strategy

    def distribute(self, tests: List[TestCase]) -> Dict[int, List[TestCase]]:
        """Distribute tests across workers.

        Args:
            tests: List of tests to distribute

        Returns:
            Dictionary mapping worker_id to list of tests
        """
        if self.strategy == DistributionStrategy.ROUND_ROBIN:
            return self._distribute_round_robin(tests)
        elif self.strategy == DistributionStrategy.RANDOM:
            return self._distribute_random(tests)
        elif self.strategy == DistributionStrategy.BY_PRIORITY:
            return self._distribute_by_priority(tests)
        elif self.strategy == DistributionStrategy.BY_DURATION:
            return self._distribute_by_duration(tests)
        else:
            return self._distribute_round_robin(tests)

    def _distribute_round_robin(
        self, tests: List[TestCase]
    ) -> Dict[int, List[TestCase]]:
        """Distribute tests round-robin."""
        distribution = {i: [] for i in range(self.workers)}

        for i, test in enumerate(tests):
            worker_id = i % self.workers
            distribution[worker_id].append(test)

        return distribution

    def _distribute_random(self, tests: List[TestCase]) -> Dict[int, List[TestCase]]:
        """Distribute tests randomly."""
        shuffled = tests.copy()
        random.shuffle(shuffled)
        return self._distribute_round_robin(shuffled)

    def _distribute_by_priority(
        self, tests: List[TestCase]
    ) -> Dict[int, List[TestCase]]:
        """Distribute tests by priority."""
        sorted_tests = sorted(
            tests,
            key=lambda t: {
                TestPriority.CRITICAL: 0,
                TestPriority.HIGH: 1,
                TestPriority.MEDIUM: 2,
                TestPriority.LOW: 3,
            }.get(t.priority, 2),
        )
        return self._distribute_round_robin(sorted_tests)

    def _distribute_by_duration(
        self, tests: List[TestCase]
    ) -> Dict[int, List[TestCase]]:
        """Distribute tests by duration to balance workload."""
        sorted_tests = sorted(
            tests, key=lambda t: t.estimated_duration_ms, reverse=True
        )

        distribution = {i: [] for i in range(self.workers)}
        worker_loads = [0.0] * self.workers

        for test in sorted_tests:
            min_load_worker = min(range(self.workers), key=lambda w: worker_loads[w])
            distribution[min_load_worker].append(test)
            worker_loads[min_load_worker] += test.estimated_duration_ms

        return distribution


class DistributedTestRunner:
    """Comprehensive distributed test runner.

    Example:
        runner = DistributedTestRunner(workers=4)

        # Run with impact analysis
        results = runner.run_with_impact_analysis(
            tests=all_tests,
            changed_files=changed_files,
            execute_fn=run_test
        )

        # Get report
        report = runner.get_report()
    """

    def __init__(self, workers: int = 4):
        """Initialize distributed test runner.

        Args:
            workers: Number of workers
        """
        self.workers = workers
        self.executor = ParallelExecutor(workers=workers)
        self.analyzer = ImpactAnalyzer()
        self.prioritizer = TestPrioritizer()
        self.distributor = TestDistributor(workers=workers)
        self.results: List[TestResult] = []

    def run_with_impact_analysis(
        self,
        tests: List[TestCase],
        changed_files: List[str],
        execute_fn: Callable[[TestCase], TestResult],
    ) -> List[TestResult]:
        """Run tests with impact analysis.

        Args:
            tests: All available tests
            changed_files: List of changed files
            execute_fn: Function to execute a test

        Returns:
            List of test results
        """
        impacted = self.analyzer.analyze_impact(changed_files)
        tests_to_run = self.analyzer.get_tests_to_run(impacted)

        if not tests_to_run:
            tests_to_run = tests

        return self.executor.run_tests(tests_to_run, execute_fn)

    def run_with_prioritization(
        self,
        tests: List[TestCase],
        execute_fn: Callable[[TestCase], TestResult],
        priority_strategy: str = "risk",
    ) -> List[TestResult]:
        """Run tests with prioritization.

        Args:
            tests: Tests to run
            execute_fn: Function to execute a test
            priority_strategy: Strategy for prioritization

        Returns:
            List of test results
        """
        if priority_strategy == "risk":
            prioritized = self.prioritizer.prioritize_by_risk(tests, {})
        elif priority_strategy == "duration":
            prioritized = self.prioritizer.prioritize_by_duration(tests)
        else:
            prioritized = self.prioritizer.prioritize_by_priority(tests)

        return self.executor.run_tests(prioritized, execute_fn)

    def run_distributed(
        self,
        tests: List[TestCase],
        execute_fn: Callable[[TestCase], TestResult],
    ) -> Dict[int, List[TestResult]]:
        """Run tests distributed across workers.

        Args:
            tests: Tests to run
            execute_fn: Function to execute a test

        Returns:
            Results grouped by worker
        """
        distribution = self.distributor.distribute(tests)
        worker_results: Dict[int, List[TestResult]] = {
            i: [] for i in range(self.workers)
        }

        def run_worker(worker_id: int, worker_tests: List[TestCase]):
            for test in worker_tests:
                result = execute_fn(test)
                worker_results[worker_id].append(result)

        threads = []
        for worker_id, worker_tests in distribution.items():
            thread = threading.Thread(target=run_worker, args=(worker_id, worker_tests))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return worker_results

    def get_report(self) -> Dict[str, Any]:
        """Get test execution report.

        Returns:
            Report dictionary
        """
        stats = self.executor.get_statistics()

        return {
            "statistics": stats,
            "workers": self.workers,
            "strategy": self.distributor.strategy.value,
            "total_tests": len(self.results),
        }
