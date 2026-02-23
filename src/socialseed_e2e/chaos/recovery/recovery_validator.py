"""
Recovery validation module for chaos engineering.

Validates system recovery after chaos experiments.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from ..models import (
    ChaosResult,
    ExperimentStatus,
    HealthCheckConfig,
)


class RecoveryValidator:
    """Validates system recovery after chaos experiments.

    Monitors system health during and after chaos:
    - Health endpoint monitoring
    - Success rate validation
    - Recovery time measurement
    - Automated rollback triggers

    Example:
        validator = RecoveryValidator()

        # Configure health check
        config = HealthCheckConfig(
            endpoint="https://api.example.com/health",
            interval_seconds=5,
            success_rate_threshold=95.0,
            max_recovery_time_seconds=60
        )

        # Validate recovery
        is_healthy = validator.validate_recovery(
            health_config=config,
            timeout_seconds=120
        )
    """

    def __init__(self):
        """Initialize recovery validator."""
        self.health_history: List[Dict[str, Any]] = []
        self.is_monitoring = False

    def validate_recovery(
        self,
        health_config: HealthCheckConfig,
        timeout_seconds: int = 120,
    ) -> Dict[str, Any]:
        """Validate system recovery after chaos.

        Args:
            health_config: Health check configuration
            timeout_seconds: Maximum time to wait for recovery

        Returns:
            Validation results dictionary
        """
        start_time = time.time()
        checks_passed = 0
        checks_failed = 0
        recovery_time = None

        while time.time() - start_time < timeout_seconds:
            check_result = self._perform_health_check(health_config)
            self.health_history.append(check_result)

            if check_result["success"]:
                checks_passed += 1
                if recovery_time is None:
                    recovery_time = time.time() - start_time
            else:
                checks_failed += 1

            # Calculate success rate
            total_checks = checks_passed + checks_failed
            success_rate = (
                (checks_passed / total_checks * 100) if total_checks > 0 else 0
            )

            # Check if recovery criteria met
            if (
                success_rate >= health_config.success_rate_threshold
                and recovery_time is not None
            ):
                return {
                    "recovered": True,
                    "recovery_time_seconds": recovery_time,
                    "success_rate": success_rate,
                    "total_checks": total_checks,
                    "checks_passed": checks_passed,
                    "checks_failed": checks_failed,
                    "message": f"System recovered in {recovery_time:.1f} seconds with {success_rate:.1f}% success rate",
                }

            time.sleep(health_config.interval_seconds)

        # Timeout reached
        total_checks = checks_passed + checks_failed
        success_rate = (checks_passed / total_checks * 100) if total_checks > 0 else 0

        return {
            "recovered": False,
            "recovery_time_seconds": None,
            "success_rate": success_rate,
            "total_checks": total_checks,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "message": f"System did not recover within {timeout_seconds} seconds. Success rate: {success_rate:.1f}%",
        }

    def monitor_during_chaos(
        self,
        health_config: HealthCheckConfig,
        chaos_result: ChaosResult,
    ) -> Dict[str, Any]:
        """Monitor system health during chaos experiment.

        Args:
            health_config: Health check configuration
            chaos_result: Chaos experiment result

        Returns:
            Monitoring results
        """
        self.is_monitoring = True
        checks = []

        start_time = time.time()

        while self.is_monitoring and chaos_result.status == ExperimentStatus.RUNNING:
            check_result = self._perform_health_check(health_config)
            checks.append(check_result)

            # Update chaos result with health check info
            if check_result["success"]:
                chaos_result.health_check_success_rate = (
                    (sum(1 for c in checks if c["success"]) / len(checks) * 100)
                    if checks
                    else 0
                )

            time.sleep(health_config.interval_seconds)

        elapsed = time.time() - start_time

        success_count = sum(1 for c in checks if c["success"])
        success_rate = (success_count / len(checks) * 100) if checks else 0

        return {
            "duration_seconds": elapsed,
            "total_checks": len(checks),
            "success_rate": success_rate,
            "avg_response_time_ms": sum(c["response_time_ms"] for c in checks)
            / len(checks)
            if checks
            else 0,
        }

    def stop_monitoring(self):
        """Stop ongoing health monitoring."""
        self.is_monitoring = False

    def validate_experiment_result(
        self,
        result: ChaosResult,
        max_error_rate: float = 50.0,
        max_recovery_time: Optional[int] = None,
    ) -> bool:
        """Validate if chaos experiment result is acceptable.

        Args:
            result: Chaos experiment result
            max_error_rate: Maximum acceptable error rate
            max_recovery_time: Maximum acceptable recovery time

        Returns:
            True if result is acceptable
        """
        # Check error rate
        if result.error_rate_percent > max_error_rate:
            result.failed_assertions.append(
                f"Error rate {result.error_rate_percent:.1f}% exceeds maximum {max_error_rate}%"
            )
            return False

        # Check recovery time
        if max_recovery_time and result.recovery_time_seconds:
            if result.recovery_time_seconds > max_recovery_time:
                result.failed_assertions.append(
                    f"Recovery time {result.recovery_time_seconds:.0f}s exceeds maximum {max_recovery_time}s"
                )
                return False

        # Check health check success rate
        if result.health_check_success_rate < 50.0:
            result.failed_assertions.append(
                f"Health check success rate {result.health_check_success_rate:.1f}% is too low"
            )
            return False

        return True

    def create_health_check(
        self,
        endpoint: str,
        interval_seconds: int = 5,
        timeout_seconds: int = 10,
        expected_status_code: int = 200,
        success_rate_threshold: float = 95.0,
        max_recovery_time_seconds: int = 60,
    ) -> HealthCheckConfig:
        """Create a health check configuration.

        Args:
            endpoint: Health check endpoint URL
            interval_seconds: Check interval
            timeout_seconds: Request timeout
            expected_status_code: Expected HTTP status code
            success_rate_threshold: Minimum success rate percentage
            max_recovery_time_seconds: Maximum acceptable recovery time

        Returns:
            HealthCheckConfig
        """
        return HealthCheckConfig(
            endpoint=endpoint,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            expected_status_code=expected_status_code,
            success_rate_threshold=success_rate_threshold,
            max_recovery_time_seconds=max_recovery_time_seconds,
        )

    def get_health_history(self) -> List[Dict[str, Any]]:
        """Get history of health checks.

        Returns:
            List of health check results
        """
        return self.health_history

    def clear_history(self):
        """Clear health check history."""
        self.health_history.clear()

    def _perform_health_check(self, config: HealthCheckConfig) -> Dict[str, Any]:
        """Perform a single health check.

        Args:
            config: Health check configuration

        Returns:
            Health check result
        """
        start_time = time.time()

        try:
            response = requests.get(
                config.endpoint,
                timeout=config.timeout_seconds,
            )

            response_time_ms = (time.time() - start_time) * 1000

            success = response.status_code == config.expected_status_code

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "endpoint": config.endpoint,
                "success": success,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "error": None,
            }

        except requests.Timeout:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "endpoint": config.endpoint,
                "success": False,
                "status_code": None,
                "response_time_ms": config.timeout_seconds * 1000,
                "error": "Timeout",
            }

        except Exception as e:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "endpoint": config.endpoint,
                "success": False,
                "status_code": None,
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
            }
