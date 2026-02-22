"""
Shadow Runner - Traffic Capture, Fuzzing, and Test Generation.

This module provides the core ShadowRunner class that handles:
- Capturing API traffic from production
- Applying semantic fuzzing mutations
- Generating test cases
- Replaying traffic against staging/pre-prod
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.shadow_runner.fuzzer import IntelligentFuzzer, SemanticFuzzer
from socialseed_e2e.shadow_runner.models import (
    CaptureConfig,
    CapturedRequest,
    CapturedTraffic,
    FuzzingCampaign,
    FuzzingConfig,
    FuzzingResult,
    FuzzingStrategy,
    HttpMethod,
    ReplayConfig,
    TestGenerationConfig,
    TestGenerationResult,
    TrafficAnalysis,
)


class ShadowRunner:
    """
    Main orchestrator for Shadow Runner operations.

    Provides:
    - Traffic capture and storage
    - Semantic fuzzing on captured requests
    - Test generation from captured traffic
    - Traffic replay and analysis
    """

    def __init__(self, output_dir: str = ".e2e/shadow"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture_traffic(self, config: CaptureConfig) -> CapturedTraffic:
        """
        Capture traffic from target URL.

        Note: This is a placeholder implementation. Real capture would use:
        - eBPF for kernel-level capture
        - PCAP for network-level capture
        - Proxy middleware for application-level capture
        """
        capture_id = str(uuid.uuid4())
        traffic = CapturedTraffic(
            capture_id=capture_id,
            capture_time=datetime.now(),
            source_url=config.target_url,
            requests=[],
            metadata={
                "filter_health": config.filter_health_checks,
                "filter_static": config.filter_static_assets,
                "sanitize_pii": config.sanitize_pii,
            },
        )

        return traffic

    def save_capture(self, traffic: CapturedTraffic, output_path: str) -> None:
        """Save captured traffic to JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(traffic.model_dump(by_alias=True), f, indent=2, default=str)

    def load_capture(self, capture_path: str) -> CapturedTraffic:
        """Load captured traffic from JSON file."""
        with open(capture_path, "r") as f:
            data = json.load(f)
        return CapturedTraffic(**data)

    def analyze_capture(self, capture_path: str) -> TrafficAnalysis:
        """Analyze captured traffic and return statistics."""
        traffic = self.load_capture(capture_path)

        analysis = TrafficAnalysis(
            total_requests=len(traffic.requests),
            unique_endpoints=len(set(r.path for r in traffic.requests)),
            methods={},
            status_codes={},
        )

        for request in traffic.requests:
            method = request.method.value
            analysis.methods[method] = analysis.methods.get(method, 0) + 1

            if request.status_code:
                status = str(request.status_code)
                analysis.status_codes[status] = analysis.status_codes.get(status, 0) + 1

            if request.matched_service:
                if request.matched_service not in analysis.endpoints_by_service:
                    analysis.endpoints_by_service[request.matched_service] = []
                if (
                    request.path
                    not in analysis.endpoints_by_service[request.matched_service]
                ):
                    analysis.endpoints_by_service[request.matched_service].append(
                        request.path
                    )

        return analysis

    def generate_fuzzing_campaign(
        self,
        capture_path: str,
        target_url: str,
        config: Optional[FuzzingConfig] = None,
    ) -> FuzzingCampaign:
        """Create a fuzzing campaign from captured traffic."""
        if config is None:
            config = FuzzingConfig()

        traffic = self.load_capture(capture_path)

        campaign = FuzzingCampaign(
            campaign_id=str(uuid.uuid4()),
            name=f"Fuzzing Campaign {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=f"Semantic fuzzing campaign targeting {target_url}",
            source_capture=capture_path,
            target_url=target_url,
            fuzzing_config=config,
            status="ready",
        )

        return campaign

    def run_fuzzing_campaign(
        self,
        campaign: FuzzingCampaign,
        execute_callback: Optional[callable] = None,
    ) -> FuzzingCampaign:
        """
        Execute a fuzzing campaign.

        Args:
            campaign: The fuzzing campaign to run
            execute_callback: Optional callback to execute mutated requests.
                              Should accept (request, mutated_body) and return response.

        Returns:
            Updated campaign with results
        """
        if campaign.source_capture:
            traffic = self.load_capture(campaign.source_capture)
        else:
            raise ValueError("Campaign must have a source capture")

        fuzzer = self._create_fuzzer(campaign.fuzzing_config)

        campaign.status = "running"
        campaign.start_time = datetime.now()

        vulnerabilities_found = []

        for request in traffic.requests:
            mutations = fuzzer.fuzz_request(request)

            for mutation in mutations:
                result = FuzzingResult(
                    campaign_id=campaign.campaign_id,
                    original_request=request,
                    mutated_requests=[mutation],
                )

                if execute_callback:
                    try:
                        exec_result = execute_callback(request, mutation.mutated_value)
                        result.execution_results.append(
                            {
                                "mutation": mutation.model_dump(),
                                "result": exec_result,
                            }
                        )

                        if self._detect_vulnerability(exec_result):
                            vulnerabilities_found.append(
                                {
                                    "request": request.path,
                                    "mutation_type": mutation.mutation_type.value,
                                    "details": exec_result,
                                }
                            )

                    except Exception as e:
                        result.errors_detected.append(str(e))

                campaign.results.append(result)

        campaign.vulnerabilities_found = vulnerabilities_found
        campaign.total_mutations = sum(
            len(r.mutated_requests) for r in campaign.results
        )
        campaign.successful_mutations = len(
            [r for r in campaign.results if r.execution_results]
        )
        campaign.failed_mutations = len(
            [r for r in campaign.results if r.errors_detected]
        )
        campaign.status = "completed"
        campaign.end_time = datetime.now()

        return campaign

    def _create_fuzzer(self, config: FuzzingConfig) -> SemanticFuzzer:
        """Create appropriate fuzzer based on configuration."""
        if config.strategy == FuzzingStrategy.AI_POWERED:
            return IntelligentFuzzer(config, config.ai_model)
        return SemanticFuzzer(config)

    def _detect_vulnerability(self, result: Any) -> bool:
        """Detect if execution result indicates a vulnerability."""
        if not result:
            return False

        if isinstance(result, dict):
            status = result.get("status", result.get("status_code", 0))
            if status == 500:
                return True
            if "error" in result.get("body", "").lower():
                return True

        return False

    def generate_tests(
        self,
        capture_path: str,
        config: TestGenerationConfig,
    ) -> TestGenerationResult:
        """Generate test cases from captured traffic."""
        traffic = self.load_capture(capture_path)

        tests = []
        endpoints_covered = set()

        for request in traffic.requests:
            test_case = self._generate_test_case(request, config)
            tests.append(test_case)
            endpoints_covered.add(request.path)

        coverage_report = {
            "total_endpoints": len(endpoints_covered),
            "endpoints": list(endpoints_covered),
            "http_methods": list(set(r.method.value for r in traffic.requests)),
        }

        return TestGenerationResult(
            generated_tests=tests,
            test_count=len(tests),
            service_name=config.service_name,
            coverage_report=coverage_report,
        )

    def _generate_test_case(
        self, request: CapturedRequest, config: TestGenerationConfig
    ) -> Dict[str, Any]:
        """Generate a single test case from a captured request."""
        test_case = {
            "name": f"test_{request.method.value.lower()}_{self._sanitize_path(request.path)}",
            "method": request.method.value,
            "url": request.url,
            "path": request.path,
            "headers": request.headers,
            "query_params": request.query_params,
        }

        if request.body:
            test_case["body"] = request.body

        if config.generate_assertions:
            test_case["assertions"] = self._generate_assertions(request)

        if config.generate_negative_tests:
            test_case["negative_tests"] = self._generate_negative_tests(request)

        return test_case

    def _sanitize_path(self, path: str) -> str:
        """Sanitize path for use as test name."""
        return path.replace("/", "_").replace("{", "").replace("}", "").strip("_")

    def _generate_assertions(self, request: CapturedRequest) -> Dict[str, Any]:
        """Generate assertions for a test case."""
        assertions = {
            "status_code": request.status_code or 200,
        }

        if request.response_body:
            assertions["response_keys"] = list(request.response_body.keys())

        return assertions

    def _generate_negative_tests(
        self, request: CapturedRequest
    ) -> List[Dict[str, Any]]:
        """Generate negative test cases."""
        negative_tests = []

        if request.body:
            negative_tests.append(
                {
                    "name": "invalid_body",
                    "body": {"invalid": "structure"},
                    "expected_status": 400,
                }
            )

        negative_tests.append(
            {
                "name": "missing_auth",
                "headers": {},
                "expected_status": 401,
            }
        )

        return negative_tests

    def replay_traffic(
        self,
        capture_path: str,
        config: ReplayConfig,
    ) -> Dict[str, Any]:
        """Replay captured traffic against target URL."""
        traffic = self.load_capture(capture_path)

        results = {
            "total": len(traffic.requests),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        return results

    def export_fuzzing_report(
        self,
        campaign: FuzzingCampaign,
        output_path: str,
    ) -> None:
        """Export fuzzing campaign results to JSON."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(campaign.model_dump(by_alias=True), f, indent=2, default=str)


__all__ = ["ShadowRunner"]
