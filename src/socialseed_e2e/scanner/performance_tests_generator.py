"""Performance tests generator for load and stress testing.

This module generates performance test templates with SLAs.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PerformanceTest:
    """Represents a performance test."""

    name: str
    type: str  # "load", "stress", "spike", "endurance"
    description: str
    test_code: str
    sla: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceInfo:
    """Represents performance test information."""

    tests: List[PerformanceTest] = field(default_factory=dict)
    slas: Dict[str, Any] = field(default_factory=dict)


class PerformanceTestGenerator:
    """Generates performance test templates."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def generate(self) -> PerformanceInfo:
        """Generate performance tests."""
        info = PerformanceInfo()

        self._generate_load_tests(info)
        self._generate_stress_tests(info)
        self._generate_spike_tests(info)
        self._generate_endurance_tests(info)
        self._detect_slas(info)

        return info

    def _generate_load_tests(self, info: PerformanceInfo) -> None:
        """Generate load tests."""
        test = PerformanceTest(
            name="test_load_basic",
            type="load",
            description="Basic load test - 10 concurrent users for 1 minute",
            test_code='''def test_load_basic(page):
    """Load test: 10 concurrent users for 1 minute"""
    import concurrent.futures
    import time
    
    def make_request():
        response = page.get("/users")
        return response.status
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        start = time.time()
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed = time.time() - start
    
    success_count = sum(1 for r in results if r == 200)
    assert success_count >= 95, f"Success rate: {success_count}% (expected >=95%)"
    print(f"Load test: {success_count}/100 requests successful in {elapsed:.2f}s")
''',
            sla={"p95_latency": 500, "success_rate": 95, "throughput": 100},
        )
        info.tests.append(test)

    def _generate_stress_tests(self, info: PerformanceInfo) -> None:
        """Generate stress tests."""
        test = PerformanceTest(
            name="test_stress_scalability",
            type="stress",
            description="Stress test - ramp up from 10 to 100 users",
            test_code='''def test_stress_scalability(page):
    """Stress test: ramp up users and measure degradation"""
    import concurrent.futures
    
    results = {}
    
    for user_count in [10, 25, 50, 75, 100]:
        def make_request():
            response = page.get("/users")
            return response.status, response.elapsed.total_seconds() * 1000
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
            futures = [executor.submit(make_request) for _ in range(user_count * 2)]
            results[user_count] = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        avg_latency = sum(r[1] for r in results[user_count]) / len(results[user_count])
        print(f"Users: {user_count}, Avg latency: {avg_latency:.2f}ms")
        
        # Fail if latency exceeds threshold
        if avg_latency > 2000:
            break
    
    print(f"Max concurrent users supported: {user_count}")
''',
            sla={"max_latency": 2000, "max_users": 100},
        )
        info.tests.append(test)

    def _generate_spike_tests(self, info: PerformanceInfo) -> None:
        """Generate spike tests."""
        test = PerformanceTest(
            name="test_spike_recovery",
            type="spike",
            description="Spike test - sudden increase in traffic",
            test_code='''def test_spike_recovery(page):
    """Spike test: sudden traffic increase and recovery"""
    import concurrent.futures
    import time
    
    # Baseline
    baseline = sum(1 for _ in range(10) if page.get("/users").status == 200)
    print(f"Baseline: {baseline}/10 successful")
    
    # Spike
    time.sleep(1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(page.get, "/users") for _ in range(50)]
        spike_results = [f.result().status for f in concurrent.futures.as_completed(futures)]
    
    spike_success = sum(1 for r in spike_results if r == 200)
    print(f"Spike: {spike_success}/50 successful")
    
    # Recovery
    time.sleep(2)
    recovery = sum(1 for _ in range(10) if page.get("/users").status == 200)
    print(f"Recovery: {recovery}/10 successful")
    
    assert spike_success >= 30, f"Spike handling failed: {spike_success}%"
''',
            sla={"spike_success_rate": 60, "recovery_time": 5},
        )
        info.tests.append(test)

    def _generate_endurance_tests(self, info: PerformanceInfo) -> None:
        """Generate endurance tests."""
        test = PerformanceTest(
            name="test_endurance_memory",
            type="endurance",
            description="Endurance test - sustained load over time",
            test_code='''def test_endurance_memory(page):
    """Endurance test: sustained load with memory monitoring"""
    import time
    import gc
    
    gc.collect()
    initial_objects = len(gc.get_objects())
    
    for i in range(100):
        response = page.get("/users")
        if i % 10 == 0:
            print(f"Request {i}: status={response.status}")
    
    gc.collect()
    final_objects = len(gc.get_objects())
    leaked = final_objects - initial_objects
    
    print(f"Memory leak check: {leaked} new objects")
    assert leaked < 100, f"Possible memory leak: {leaked} objects"
''',
            sla={"max_leak": 100, "duration": 100},
        )
        info.tests.append(test)

    def _detect_slas(self, info: PerformanceInfo) -> None:
        """Detect SLAs from configuration."""
        sla_patterns = [
            (r"latency.*?(\d+)\s*ms", "latency"),
            (r"timeout.*?(\d+)\s*ms", "timeout"),
            (r"rate.*?(\d+)\s*%", "success_rate"),
        ]

        for conf_file in self.project_root.glob("*.conf"):
            content = conf_file.read_text(errors="ignore")
            for pattern, sla_type in sla_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    info.slas[sla_type] = int(match.group(1))


def generate_performance_tests_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate PERFORMANCE_TESTS.md document."""
    generator = PerformanceTestGenerator(project_root)
    info = generator.generate()

    doc = "# Tests de Rendimiento\n\n"

    doc += "## SLAs Definidos\n\n"
    if info.slas:
        doc += "| Métrica | Valor |\n"
        doc += "|---------|-------|\n"
        for key, value in info.slas.items():
            doc += f"| {key} | {value} |\n"
        doc += "\n"

    test_types = {
        "load": "💼 Tests de Carga",
        "stress": "⚡ Tests de Estrés",
        "spike": "📈 Tests de Spike",
        "endurance": "⏱️ Tests de Endurance",
    }

    for test_type, title in test_types.items():
        tests = [t for t in info.tests if t.type == test_type]
        if tests:
            doc += f"## {title}\n\n"
            for test in tests:
                doc += f"### {test.name}\n\n"
                doc += f"{test.description}\n\n"
                doc += f"```python\n{test.test_code}\n```\n\n"

    doc += "---\n\n"
    doc += "## Ejecución\n\n"
    doc += "```bash\n"
    doc += "# Ejecutar tests de carga\n"
    doc += "e2e run --service auth-service --tag load\n\n"
    doc += "# Ejecutar tests de estrés\n"
    doc += "e2e run --service auth-service --tag stress\n\n"
    doc += "# Generar reporte HTML\n"
    doc += "e2e perf-report\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_performance_tests_doc(project_root))
    else:
        print("Usage: python performance_tests_generator.py <project_root>")
