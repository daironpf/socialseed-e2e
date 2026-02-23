"""
ML Execution Orchestrator and Bin-Packing for socialseed-e2e.

This module provides intelligent test execution optimization using:
- Historical metrics collection (duration, CPU, memory)
- ML-based prediction of test duration
- Bin-packing algorithm for optimal test distribution
- Dynamic worker allocation based on resource usage

Features:
- First-fit decreasing bin-packing algorithm
- Test duration prediction using historical data
- Resource-aware worker allocation
- CI/CD pipeline optimization
"""

import json
import uuid
from dataclasses import field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestType(str, Enum):
    """Type of test for classification."""

    API_PURE = "api_pure"
    UI_BROWSER = "ui_browser"
    INTEGRATION = "integration"
    E2E = "e2e"


class WorkerResourceProfile(BaseModel):
    """Resource profile for a worker."""

    worker_id: str

    cpu_cores: int = 4
    memory_mb: int = 8192

    available_cpu_percent: float = 100.0
    available_memory_mb: int = 8192


class TestMetrics(BaseModel):
    """Historical metrics for a test."""

    test_id: str
    test_name: str
    test_file: str

    test_type: TestType

    avg_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0

    avg_memory_mb: float = 0.0
    max_memory_mb: float = 0.0

    execution_count: int = 0
    last_executed: Optional[datetime] = None

    success_rate: float = 1.0


class TestBin(BaseModel):
    """A bin (worker) containing tests to execute."""

    bin_id: str

    tests: List[str] = field(default_factory=list)

    total_duration_ms: float = 0.0
    total_memory_mb: float = 0.0

    estimated_completion_time_ms: float = 0.0


class BinPackingConfig(BaseModel):
    """Configuration for bin-packing algorithm."""

    num_workers: int = 4

    max_bin_duration_ms: float = 300000.0
    max_bin_memory_mb: float = 8192.0

    allow_overflow: bool = False

    prioritize_by: str = "duration"

    use_ml_prediction: bool = True


class ExecutionPlan(BaseModel):
    """Complete execution plan with bin allocation."""

    plan_id: str
    generated_at: datetime = Field(default_factory=datetime.now)

    bins: List[TestBin] = Field(default_factory=list)

    total_tests: int = 0
    estimated_duration_ms: float = 0.0

    worker_count: int = 0


class MetricsCollector:
    """
    Collects and stores historical test metrics.
    """

    def __init__(self, storage_path: str = ".e2e/test_metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.metrics: Dict[str, TestMetrics] = {}

    def record_execution(
        self,
        test_name: str,
        test_file: str,
        duration_ms: float,
        memory_mb: float,
        success: bool,
        test_type: TestType = TestType.API_PURE,
    ) -> None:
        """Record a test execution."""
        test_id = f"{test_file}::{test_name}"

        if test_id not in self.metrics:
            self.metrics[test_id] = TestMetrics(
                test_id=test_id,
                test_name=test_name,
                test_file=test_file,
                test_type=test_type,
            )

        metrics = self.metrics[test_id]

        metrics.execution_count += 1

        if metrics.execution_count == 1:
            metrics.avg_duration_ms = duration_ms
            metrics.min_duration_ms = duration_ms
            metrics.max_duration_ms = duration_ms
            metrics.avg_memory_mb = memory_mb
            metrics.max_memory_mb = memory_mb
        else:
            metrics.avg_duration_ms = (
                metrics.avg_duration_ms * (metrics.execution_count - 1) + duration_ms
            ) / metrics.execution_count
            metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
            metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)
            metrics.avg_memory_mb = (
                metrics.avg_memory_mb * (metrics.execution_count - 1) + memory_mb
            ) / metrics.execution_count
            metrics.max_memory_mb = max(metrics.max_memory_mb, memory_mb)

        if success:
            metrics.success_rate = (
                metrics.success_rate * (metrics.execution_count - 1) + 1.0
            ) / metrics.execution_count
        else:
            metrics.success_rate = (
                metrics.success_rate * (metrics.execution_count - 1) + 0.0
            ) / metrics.execution_count

        metrics.last_executed = datetime.now()

    def get_metrics(self, test_id: str) -> Optional[TestMetrics]:
        """Get metrics for a specific test."""
        return self.metrics.get(test_id)

    def get_all_metrics(self) -> List[TestMetrics]:
        """Get all collected metrics."""
        return list(self.metrics.values())

    def save_metrics(self) -> None:
        """Save metrics to disk."""
        data = {
            test_id: metrics.model_dump() for test_id, metrics in self.metrics.items()
        }

        with open(self.storage_path / "metrics.json", "w") as f:
            json.dump(data, f, default=str)

    def load_metrics(self) -> None:
        """Load metrics from disk."""
        metrics_file = self.storage_path / "metrics.json"
        if not metrics_file.exists():
            return

        with open(metrics_file, "r") as f:
            data = json.load(f)

        for test_id, metrics_data in data.items():
            self.metrics[test_id] = TestMetrics(**metrics_data)


class DurationPredictor:
    """
    ML-based predictor for test duration.
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.test_type_weights = {
            TestType.API_PURE: 1.0,
            TestType.INTEGRATION: 1.5,
            TestType.UI_BROWSER: 2.5,
            TestType.E2E: 3.0,
        }

    def predict_duration(
        self,
        test_name: str,
        test_file: str,
        test_type: TestType = TestType.API_PURE,
    ) -> float:
        """Predict test duration based on historical data."""
        test_id = f"{test_file}::{test_name}"

        metrics = self.metrics_collector.get_metrics(test_id)

        if metrics and metrics.execution_count >= 3:
            base_duration = metrics.avg_duration_ms

            weight = self.test_type_weights.get(test_type, 1.0)

            confidence = min(metrics.execution_count / 10.0, 1.0)

            return base_duration * weight * (1.0 + (1.0 - confidence) * 0.2)

        return self._estimate_default_duration(test_type)

    def _estimate_default_duration(self, test_type: TestType) -> float:
        """Estimate default duration based on test type."""
        defaults = {
            TestType.API_PURE: 5000,
            TestType.INTEGRATION: 15000,
            TestType.UI_BROWSER: 30000,
            TestType.E2E: 45000,
        }
        return defaults.get(test_type, 10000)


class BinPackingScheduler:
    """
    First-fit decreasing bin-packing algorithm for test distribution.
    """

    def __init__(self, config: BinPackingConfig):
        self.config = config
        self.predictor: Optional[DurationPredictor] = None

    def set_predictor(self, predictor: DurationPredictor) -> None:
        """Set the duration predictor."""
        self.predictor = predictor

    def create_execution_plan(
        self,
        tests: List[Dict[str, Any]],
    ) -> ExecutionPlan:
        """Create an optimal execution plan using bin-packing."""
        plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            bins=[],
        )

        test_items = []
        for test in tests:
            test_id = test.get("id", test.get("name", "unknown"))
            test_name = test.get("name", test_id)
            test_file = test.get("file", "")
            test_type = TestType(test.get("type", "api_pure"))

            if self.predictor:
                duration = self.predictor.predict_duration(
                    test_name, test_file, test_type
                )
            else:
                duration = test.get("duration_ms", 10000)

            memory = test.get("memory_mb", 512)

            test_items.append(
                {
                    "id": test_id,
                    "name": test_name,
                    "duration_ms": duration,
                    "memory_mb": memory,
                    "test_type": test_type,
                }
            )

        test_items.sort(key=lambda x: x["duration_ms"], reverse=True)

        bins = []
        for _ in range(self.config.num_workers):
            bins.append(TestBin(bin_id=str(uuid.uuid4())))

        for test in test_items:
            best_bin = None
            best_fit = float("inf")

            for bin_item in bins:
                if self._can_fit(bin_item, test):
                    fit = self._calculate_fit(bin_item, test)
                    if fit < best_fit:
                        best_fit = fit
                        best_bin = bin_item

            if best_bin is None:
                if self.config.allow_overflow:
                    best_bin = min(bins, key=lambda b: b.total_duration_ms)
                else:
                    continue

            best_bin.tests.append(test["id"])
            best_bin.total_duration_ms += test["duration_ms"]
            best_bin.total_memory_mb += test["memory_mb"]

        plan.bins = bins
        plan.total_tests = sum(len(b.tests) for b in bins)
        plan.estimated_duration_ms = max((b.total_duration_ms for b in bins), default=0)
        plan.worker_count = self.config.num_workers

        return plan

    def _can_fit(self, bin_item: TestBin, test: Dict[str, Any]) -> bool:
        """Check if a test can fit in a bin."""
        duration_fit = (
            bin_item.total_duration_ms + test["duration_ms"]
            <= self.config.max_bin_duration_ms
        )
        memory_fit = (
            bin_item.total_memory_mb + test["memory_mb"]
            <= self.config.max_bin_memory_mb
        )
        return duration_fit and memory_fit

    def _calculate_fit(self, bin_item: TestBin, test: Dict[str, Any]) -> float:
        """Calculate how well a test fits in a bin (lower is better)."""
        duration_ratio = (
            bin_item.total_duration_ms + test["duration_ms"]
        ) / self.config.max_bin_duration_ms
        memory_ratio = (
            bin_item.total_memory_mb + test["memory_mb"]
        ) / self.config.max_bin_memory_mb
        return max(duration_ratio, memory_ratio)


class MLExecutionOrchestrator:
    """
    ML-powered execution orchestrator that optimizes test distribution.
    """

    def __init__(
        self,
        bin_packing_config: Optional[BinPackingConfig] = None,
        metrics_storage_path: str = ".e2e/test_metrics",
    ):
        self.metrics_collector = MetricsCollector(metrics_storage_path)
        self.predictor = DurationPredictor(self.metrics_collector)

        self.bin_packing_config = bin_packing_config or BinPackingConfig()
        self.scheduler = BinPackingScheduler(self.bin_packing_config)
        self.scheduler.set_predictor(self.predictor)

    def optimize_execution(
        self,
        tests: List[Dict[str, Any]],
    ) -> ExecutionPlan:
        """Create an optimized execution plan."""
        self.metrics_collector.load_metrics()

        return self.scheduler.create_execution_plan(tests)

    def record_results(
        self,
        test_results: List[Dict[str, Any]],
    ) -> None:
        """Record test execution results for future optimization."""
        for result in test_results:
            self.metrics_collector.record_execution(
                test_name=result.get("name", "unknown"),
                test_file=result.get("file", ""),
                duration_ms=result.get("duration_ms", 0),
                memory_mb=result.get("memory_mb", 0),
                success=result.get("success", True),
                test_type=TestType(result.get("type", "api_pure")),
            )

        self.metrics_collector.save_metrics()

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate an optimization report."""
        metrics = self.metrics_collector.get_all_metrics()

        avg_duration = (
            sum(m.avg_duration_ms for m in metrics) / len(metrics) if metrics else 0
        )
        avg_success_rate = (
            sum(m.success_rate for m in metrics) / len(metrics) if metrics else 0
        )

        by_type = {}
        for m in metrics:
            t = m.test_type.value
            if t not in by_type:
                by_type[t] = {"count": 0, "avg_duration": 0}
            by_type[t]["count"] += 1
            by_type[t]["avg_duration"] += m.avg_duration_ms

        for t in by_type:
            if by_type[t]["count"] > 0:
                by_type[t]["avg_duration"] /= by_type[t]["count"]

        return {
            "total_tests_tracked": len(metrics),
            "average_duration_ms": avg_duration,
            "average_success_rate": avg_success_rate,
            "by_test_type": by_type,
        }


__all__ = [
    "BinPackingConfig",
    "BinPackingScheduler",
    "DurationPredictor",
    "ExecutionPlan",
    "MetricsCollector",
    "MLExecutionOrchestrator",
    "TestBin",
    "TestMetrics",
    "TestType",
    "WorkerResourceProfile",
]
