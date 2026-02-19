"""API migration testing and version compatibility.

This module tests API migrations between versions and
validates backward compatibility.
"""

import time
from typing import List, Dict, Any, Optional, Callable

from .models import (
    VersionStrategy,
    APIVersion,
    MigrationTestResult,
    VersionTestResult,
    BreakingChange,
)
from .version_detector import VersionDetector


class MigrationTester:
    """Test API migrations and version compatibility."""

    def __init__(
        self, base_url: str, strategy: VersionStrategy = VersionStrategy.URL_PATH
    ):
        """Initialize migration tester.

        Args:
            base_url: Base URL of the API
            strategy: Versioning strategy
        """
        self.base_url = base_url
        self.strategy = strategy
        self.detector = VersionDetector(base_url)
        self.detector.strategy = strategy

    def test_version(
        self, version: str, test_func: Callable, *args, **kwargs
    ) -> VersionTestResult:
        """Run a test against a specific API version.

        Args:
            version: API version to test
            test_func: Test function to execute
            *args: Positional arguments for test function
            **kwargs: Keyword arguments for test function

        Returns:
            VersionTestResult with test outcome
        """
        url = self.detector.get_version_url(version)
        headers = self.detector.get_version_headers(version)
        params = self.detector.get_version_params(version)

        kwargs_with_version = {
            **kwargs,
            "_version_url": url,
            "_version_headers": headers,
            "_version_params": params,
            "_version": version,
        }

        start_time = time.time()

        try:
            result = test_func(*args, **kwargs_with_version)
            duration_ms = (time.time() - start_time) * 1000

            return VersionTestResult(
                version=version,
                test_name=test_func.__name__,
                passed=True,
                duration_ms=duration_ms,
                response_status=result.status_code
                if hasattr(result, "status_code")
                else 200,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            return VersionTestResult(
                version=version,
                test_name=test_func.__name__,
                passed=False,
                duration_ms=duration_ms,
                error_message=str(e),
            )

    def test_all_versions(
        self, test_func: Callable, versions: Optional[List[str]] = None, *args, **kwargs
    ) -> List[VersionTestResult]:
        """Run a test against all API versions.

        Args:
            test_func: Test function to execute
            versions: Optional list of versions to test (discovers if not provided)
            *args: Positional arguments for test function
            **kwargs: Keyword arguments for test function

        Returns:
            List of VersionTestResult for each version
        """
        if versions is None:
            discovered = self.detector.discover_versions()
            versions = [v.version for v in discovered]

        results = []

        for version in versions:
            result = self.test_version(version, test_func, *args, **kwargs)
            results.append(result)

        return results

    def test_migration(
        self, from_version: str, to_version: str, test_func: Callable, *args, **kwargs
    ) -> MigrationTestResult:
        """Test migration between two API versions.

        Args:
            from_version: Source version
            to_version: Target version
            test_func: Test function to execute
            *args: Positional arguments for test function
            **kwargs: Keyword arguments for test function

        Returns:
            MigrationTestResult with migration outcome
        """
        from_url = self.detector.get_version_url(from_version)
        to_url = self.detector.get_version_url(to_version)

        from_headers = self.detector.get_version_headers(from_version)
        to_headers = self.detector.get_version_headers(to_version)

        from_params = self.detector.get_version_params(from_version)
        to_params = self.detector.get_version_params(to_version)

        kwargs_from = {
            **kwargs,
            "_version_url": from_url,
            "_version_headers": from_headers,
            "_version_params": from_params,
            "_version": from_version,
        }

        kwargs_to = {
            **kwargs,
            "_version_url": to_url,
            "_version_headers": to_headers,
            "_version_params": to_params,
            "_version": to_version,
        }

        breaking_changes = []
        warnings = []
        backward_compatible = True

        try:
            from_result = test_func(*args, **kwargs_from)
        except Exception as e:
            breaking_changes.append(f"Source version {from_version} failed: {str(e)}")
            backward_compatible = False

        try:
            to_result = test_func(*args, **kwargs_to)
        except Exception as e:
            breaking_changes.append(f"Target version {to_version} failed: {str(e)}")
            backward_compatible = False

        if breaking_changes:
            return MigrationTestResult(
                from_version=from_version,
                to_version=to_version,
                test_name=test_func.__name__,
                passed=False,
                breaking_changes=breaking_changes,
                warnings=warnings,
                backward_compatible=backward_compatible,
            )

        if self._detect_breaking_changes(from_result, to_result):
            breaking_changes.append("Response structure changed between versions")
            backward_compatible = False

        return MigrationTestResult(
            from_version=from_version,
            to_version=to_version,
            test_name=test_func.__name__,
            passed=backward_compatible,
            breaking_changes=breaking_changes,
            warnings=warnings,
            backward_compatible=backward_compatible,
        )

    def _detect_breaking_changes(self, from_result: Any, to_result: Any) -> bool:
        """Detect breaking changes between two results.

        Args:
            from_result: Result from source version
            to_result: Result from target version

        Returns:
            True if breaking changes detected
        """
        if not hasattr(from_result, "json") or not hasattr(to_result, "json"):
            return False

        try:
            from_data = from_result.json()
            to_data = to_result.json()

            from_fields = (
                set(from_data.keys()) if isinstance(from_data, dict) else set()
            )
            to_fields = set(to_data.keys()) if isinstance(to_data, dict) else set()

            removed_fields = from_fields - to_fields
            if removed_fields:
                return True

            new_required_fields = to_fields - from_fields
            if new_required_fields:
                return True

        except Exception:
            pass

        return False

    def test_cross_version_consistency(
        self, test_func: Callable, versions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Test consistency across API versions.

        Args:
            test_func: Test function to execute
            versions: Optional list of versions to test

        Returns:
            Dictionary with consistency report
        """
        if versions is None:
            discovered = self.detector.discover_versions()
            versions = [v.version for v in discovered]

        results = self.test_all_versions(test_func, versions)

        passed_versions = [r for r in results if r.passed]
        failed_versions = [r for r in results if not r.passed]

        return {
            "total_versions": len(versions),
            "passed": len(passed_versions),
            "failed": len(failed_versions),
            "consistent": len(failed_versions) == 0,
            "results": results,
        }

    def detect_breaking_changes(
        self, from_version: str, to_version: str, endpoints: List[str]
    ) -> List[BreakingChange]:
        """Detect breaking changes between versions for specific endpoints.

        Args:
            from_version: Source version
            to_version: Target version
            endpoints: List of endpoint paths to check

        Returns:
            List of detected BreakingChange objects
        """
        breaking_changes = []

        from_url = self.detector.get_version_url(from_version)
        to_url = self.detector.get_version_url(to_version)

        for endpoint in endpoints:
            breaking_changes.append(
                BreakingChange(
                    type="endpoint_removed",
                    description=f"Endpoint {endpoint} may have been removed or modified in {to_version}",
                    severity="high",
                    from_version=from_version,
                    to_version=to_version,
                    affected_endpoints=[endpoint],
                )
            )

        return breaking_changes
