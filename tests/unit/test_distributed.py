"""Tests for Test Distribution Module.

This module tests the test parallelization and distribution features.
"""

import pytest
import time

from socialseed_e2e.distributed import (
    DistributedTestRunner,
    DistributionStrategy,
    ImpactAnalyzer,
    ParallelExecutor,
    TestCase,
    TestDistributor,
    TestPrioritizer,
    TestPriority,
    TestResult,
)


class TestTestCase:
    """Tests for TestCase."""

    def test_initialization(self):
        """Test test case initialization."""
        test = TestCase(id="test_1", name="Test 1", module="test_module")
        assert test.id == "test_1"
        assert test.name == "Test 1"
        assert test.priority == TestPriority.MEDIUM

    def test_is_critical(self):
        """Test critical status check."""
        test = TestCase(
            id="test_1",
            name="Test 1",
            module="test_module",
            priority=TestPriority.CRITICAL,
        )
        assert test.is_critical is True


class TestTestResult:
    """Tests for TestResult."""

    def test_initialization(self):
        """Test result initialization."""
        result = TestResult(test_id="test_1", status="passed")
        assert result.test_id == "test_1"
        assert result.status == "passed"


class TestImpactAnalyzer:
    """Tests for ImpactAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = ImpactAnalyzer()
        assert analyzer is not None

    def test_register_test(self):
        """Test registering test."""
        analyzer = ImpactAnalyzer()
        test = TestCase(id="test_1", name="Test 1", module="test_module")
        analyzer.register_test(test, ["src/api/users.py"])

        assert "test_1" in analyzer.test_map

    def test_analyze_impact(self):
        """Test impact analysis."""
        analyzer = ImpactAnalyzer()
        test = TestCase(id="test_1", name="Test 1", module="test_module")
        analyzer.register_test(test, ["src/api/users.py"])

        impacted = analyzer.analyze_impact(["src/api/users.py"])
        assert "test_1" in impacted

    def test_coverage_report(self):
        """Test coverage report."""
        analyzer = ImpactAnalyzer()
        test = TestCase(id="test_1", name="Test 1", module="test_module")
        analyzer.register_test(test, ["src/api/users.py", "src/api/auth.py"])

        report = analyzer.get_coverage_report([test])
        assert report["total_tests"] == 1
        assert report["files_covered"] == 2


class TestTestPrioritizer:
    """Tests for TestPrioritizer."""

    def test_initialization(self):
        """Test prioritizer initialization."""
        prioritizer = TestPrioritizer()
        assert prioritizer is not None

    def test_prioritize_by_priority(self):
        """Test prioritization by priority level."""
        prioritizer = TestPrioritizer()
        tests = [
            TestCase(
                id="test_1",
                name="Test 1",
                module="test_module",
                priority=TestPriority.LOW,
            ),
            TestCase(
                id="test_2",
                name="Test 2",
                module="test_module",
                priority=TestPriority.CRITICAL,
            ),
            TestCase(
                id="test_3",
                name="Test 3",
                module="test_module",
                priority=TestPriority.HIGH,
            ),
        ]

        prioritized = prioritizer.prioritize_by_priority(tests)
        assert prioritized[0].id == "test_2"

    def test_prioritize_by_duration(self):
        """Test prioritization by duration."""
        prioritizer = TestPrioritizer()
        tests = [
            TestCase(
                id="test_1",
                name="Test 1",
                module="test_module",
                estimated_duration_ms=3000,
            ),
            TestCase(
                id="test_2",
                name="Test 2",
                module="test_module",
                estimated_duration_ms=1000,
            ),
            TestCase(
                id="test_3",
                name="Test 3",
                module="test_module",
                estimated_duration_ms=2000,
            ),
        ]

        prioritized = prioritizer.prioritize_by_duration(tests)
        assert prioritized[0].id == "test_2"


class TestParallelExecutor:
    """Tests for ParallelExecutor."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = ParallelExecutor(workers=4)
        assert executor.workers == 4

    def test_run_tests(self):
        """Test running tests."""
        executor = ParallelExecutor(workers=2)
        tests = [
            TestCase(id="test_1", name="Test 1", module="test_module"),
            TestCase(id="test_2", name="Test 2", module="test_module"),
        ]

        def execute_fn(test):
            time.sleep(0.1)
            return TestResult(test_id=test.id, status="passed")

        results = executor.run_tests(tests, execute_fn)
        assert len(results) == 2

    def test_get_statistics(self):
        """Test getting statistics."""
        executor = ParallelExecutor(workers=2)
        tests = [TestCase(id="test_1", name="Test 1", module="test_module")]

        def execute_fn(test):
            return TestResult(test_id=test.id, status="passed", duration_ms=100)

        executor.run_tests(tests, execute_fn)
        stats = executor.get_statistics()

        assert stats["total"] == 1
        assert stats["passed"] == 1


class TestTestDistributor:
    """Tests for TestDistributor."""

    def test_initialization(self):
        """Test distributor initialization."""
        distributor = TestDistributor(workers=4)
        assert distributor.workers == 4

    def test_distribute_round_robin(self):
        """Test round-robin distribution."""
        distributor = TestDistributor(
            workers=2, strategy=DistributionStrategy.ROUND_ROBIN
        )
        tests = [
            TestCase(id="test_1", name="Test 1", module="test_module"),
            TestCase(id="test_2", name="Test 2", module="test_module"),
            TestCase(id="test_3", name="Test 3", module="test_module"),
            TestCase(id="test_4", name="Test 4", module="test_module"),
        ]

        distribution = distributor.distribute(tests)
        assert len(distribution[0]) == 2
        assert len(distribution[1]) == 2

    def test_distribute_by_duration(self):
        """Test distribution by duration."""
        distributor = TestDistributor(
            workers=2, strategy=DistributionStrategy.BY_DURATION
        )
        tests = [
            TestCase(
                id="test_1",
                name="Test 1",
                module="test_module",
                estimated_duration_ms=3000,
            ),
            TestCase(
                id="test_2",
                name="Test 2",
                module="test_module",
                estimated_duration_ms=2000,
            ),
            TestCase(
                id="test_3",
                name="Test 3",
                module="test_module",
                estimated_duration_ms=1000,
            ),
        ]

        distribution = distributor.distribute(tests)
        assert len(distribution) == 2


class TestDistributedTestRunner:
    """Tests for DistributedTestRunner."""

    def test_initialization(self):
        """Test runner initialization."""
        runner = DistributedTestRunner(workers=4)
        assert runner.workers == 4

    def test_run_distributed(self):
        """Test distributed test execution."""
        runner = DistributedTestRunner(workers=2)
        tests = [
            TestCase(id="test_1", name="Test 1", module="test_module"),
            TestCase(id="test_2", name="Test 2", module="test_module"),
        ]

        def execute_fn(test):
            return TestResult(test_id=test.id, status="passed")

        results = runner.run_distributed(tests, execute_fn)
        assert len(results) == 2

    def test_get_report(self):
        """Test getting report."""
        runner = DistributedTestRunner(workers=2)
        report = runner.get_report()
        assert "workers" in report
        assert report["workers"] == 2


class TestDistributionStrategy:
    """Tests for DistributionStrategy enum."""

    def test_strategies(self):
        """Test distribution strategies."""
        assert DistributionStrategy.ROUND_ROBIN.value == "round_robin"
        assert DistributionStrategy.RANDOM.value == "random"
        assert DistributionStrategy.BY_PRIORITY.value == "by_priority"
        assert DistributionStrategy.BY_DURATION.value == "by_duration"


class TestTestPriority:
    """Tests for TestPriority enum."""

    def test_priorities(self):
        """Test test priorities."""
        assert TestPriority.CRITICAL.value == "critical"
        assert TestPriority.HIGH.value == "high"
        assert TestPriority.MEDIUM.value == "medium"
        assert TestPriority.LOW.value == "low"
