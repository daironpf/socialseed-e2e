"""Visual Testing Orchestrator - Unified interface for visual regression testing.

This module provides a high-level orchestrator that combines all visual testing
features: AI-powered comparison, responsive testing, and baseline management.

Example:
    >>> from socialseed_e2e.visual_testing import VisualTestingOrchestrator
    >>> orchestrator = VisualTestingOrchestrator()
    >>> result = await orchestrator.run_visual_test(
    ...     page=page,
    ...     test_name="homepage",
    ...     viewport="desktop"
    ... )
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import Page as AsyncPage
from playwright.sync_api import Page as SyncPage

from socialseed_e2e.visual_testing.ai_comparator import (
    AIComparator,
    ImageComparator,
    PerceptualComparator,
)
from socialseed_e2e.visual_testing.baseline_manager import (
    BaselineManager,
    BaselineReviewer,
)
from socialseed_e2e.visual_testing.models import (
    BaselineInfo,
    ComparisonConfig,
    ComparisonResult,
    DiffSeverity,
    ScreenshotConfig,
    ViewportSize,
    VisualComparison,
    VisualRegressionReport,
    VisualTestResult,
)
from socialseed_e2e.visual_testing.screenshotter import (
    ResponsiveScreenshotter,
    Screenshotter,
)

logger = logging.getLogger(__name__)


class VisualTestingOrchestrator:
    """Orchestrates visual regression testing with AI-powered analysis.

    This class provides a unified interface for:
    - AI-powered visual comparison with semantic diff detection
    - Responsive testing across multiple viewports and devices
    - Visual regression tracking with approval workflows
    - Layout shift detection
    - Historical comparison

    Attributes:
        output_dir: Directory for storing screenshots and baselines
        config: Global comparison configuration
    """

    # Standard device viewports
    DEVICES = {
        "mobile_small": ViewportSize(width=320, height=568),  # iPhone SE
        "mobile": ViewportSize(width=375, height=667),  # iPhone 8
        "mobile_large": ViewportSize(width=414, height=896),  # iPhone 11 Pro Max
        "tablet": ViewportSize(width=768, height=1024),  # iPad
        "tablet_large": ViewportSize(width=1024, height=1366),  # iPad Pro
        "desktop": ViewportSize(width=1920, height=1080),  # Full HD
        "desktop_large": ViewportSize(width=2560, height=1440),  # 2K
        "ultrawide": ViewportSize(width=3440, height=1440),  # Ultrawide
    }

    # Orientation modes
    ORIENTATIONS = {
        "portrait": lambda vp: vp,
        "landscape": lambda vp: ViewportSize(
            width=vp.height, height=vp.width, device_scale_factor=vp.device_scale_factor
        ),
    }

    def __init__(
        self,
        output_dir: str = ".e2e/visual_baselines",
        config: Optional[ComparisonConfig] = None,
    ):
        """Initialize the visual testing orchestrator.

        Args:
            output_dir: Directory for screenshots and baselines
            config: Global comparison configuration
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or ComparisonConfig()

        # Initialize components
        self.screenshotter = Screenshotter(str(self.output_dir))
        self.responsive_screenshotter = ResponsiveScreenshotter(self.screenshotter)
        self.baseline_manager = BaselineManager(str(self.output_dir))
        self.baseline_reviewer = BaselineReviewer(self.baseline_manager)
        self.ai_comparator = AIComparator(self.config)
        self.image_comparator = ImageComparator(self.config)
        self.perceptual_comparator = PerceptualComparator(self.config.threshold)

        logger.info(f"VisualTestingOrchestrator initialized with output: {output_dir}")

    def run_visual_test(
        self,
        page: Union[SyncPage, AsyncPage],
        test_name: str,
        viewport: Union[str, ViewportSize] = "desktop",
        orientation: str = "portrait",
        use_ai: bool = True,
        create_baseline_if_missing: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VisualTestResult:
        """Run a single visual test.

        Captures screenshot, compares against baseline, and returns result.

        Args:
            page: Playwright page object
            test_name: Name of the test
            viewport: Viewport size (device name or ViewportSize)
            orientation: "portrait" or "landscape"
            use_ai: Whether to use AI-powered comparison
            create_baseline_if_missing: Create baseline if none exists
            metadata: Additional test metadata

        Returns:
            Visual test result
        """
        start_time = datetime.utcnow()
        metadata = metadata or {}

        try:
            # Resolve viewport
            viewport_size = self._resolve_viewport(viewport, orientation)

            # Create screenshot config
            screenshot_config = ScreenshotConfig(
                viewport=viewport_size,
                full_page=True,
            )

            # Capture screenshot
            logger.info(f"Capturing screenshot for {test_name} at {viewport_size}")
            screenshot = self.screenshotter.capture_html(
                page=page,
                test_name=f"{test_name}_{viewport}",
                config=screenshot_config,
                metadata={
                    **metadata,
                    "viewport_name": viewport
                    if isinstance(viewport, str)
                    else "custom",
                    "orientation": orientation,
                },
            )

            # Get baseline
            baseline = self.baseline_manager.get_baseline(
                test_name=test_name,
                viewport=viewport_size,
            )

            # Compare or create baseline
            if baseline:
                # Compare against baseline
                comparison = self._compare_images(
                    baseline.file_path,
                    screenshot.file_path,
                    use_ai=use_ai,
                )

                passed = comparison.result == ComparisonResult.MATCH

                result = VisualTestResult(
                    test_name=test_name,
                    passed=passed,
                    comparison=comparison,
                    baseline=baseline,
                    screenshot=screenshot,
                    duration_ms=int(
                        (datetime.utcnow() - start_time).total_seconds() * 1000
                    ),
                )

            elif create_baseline_if_missing:
                # Create new baseline
                baseline = self.baseline_manager.create_baseline(
                    test_name=test_name,
                    screenshot_path=screenshot.file_path,
                    viewport=viewport_size,
                    metadata=metadata,
                )

                result = VisualTestResult(
                    test_name=test_name,
                    passed=True,  # New baseline is considered passing
                    baseline=baseline,
                    screenshot=screenshot,
                    duration_ms=int(
                        (datetime.utcnow() - start_time).total_seconds() * 1000
                    ),
                )
                logger.info(f"Created new baseline for {test_name}")

            else:
                # No baseline and not creating one
                result = VisualTestResult(
                    test_name=test_name,
                    passed=False,
                    screenshot=screenshot,
                    duration_ms=int(
                        (datetime.utcnow() - start_time).total_seconds() * 1000
                    ),
                    error_message="No baseline exists and create_baseline_if_missing=False",
                )

            return result

        except Exception as e:
            logger.error(f"Visual test failed for {test_name}: {e}")
            return VisualTestResult(
                test_name=test_name,
                passed=False,
                duration_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
                error_message=str(e),
            )

    def run_responsive_test(
        self,
        page: Union[SyncPage, AsyncPage],
        test_name: str,
        devices: Optional[List[str]] = None,
        orientations: Optional[List[str]] = None,
        use_ai: bool = True,
        create_baseline_if_missing: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[VisualTestResult]:
        """Run visual tests across multiple devices and orientations.

        Args:
            page: Playwright page object
            test_name: Base name for the test
            devices: List of device names (default: all devices)
            orientations: List of orientations (default: portrait)
            use_ai: Whether to use AI-powered comparison
            create_baseline_if_missing: Create baselines if missing
            metadata: Additional test metadata

        Returns:
            List of visual test results for each device/orientation
        """
        devices = devices or ["mobile", "tablet", "desktop"]
        orientations = orientations or ["portrait"]
        results = []

        for device in devices:
            for orientation in orientations:
                device_test_name = f"{test_name}_{device}_{orientation}"
                result = self.run_visual_test(
                    page=page,
                    test_name=device_test_name,
                    viewport=device,
                    orientation=orientation,
                    use_ai=use_ai,
                    create_baseline_if_missing=create_baseline_if_missing,
                    metadata={
                        **(metadata or {}),
                        "device": device,
                        "orientation": orientation,
                    },
                )
                results.append(result)

        return results

    def run_test_suite(
        self,
        tests: List[Dict[str, Any]],
        use_ai: bool = True,
        parallel: bool = False,
    ) -> VisualRegressionReport:
        """Run a suite of visual tests.

        Args:
            tests: List of test configurations
            use_ai: Whether to use AI-powered comparison
            parallel: Whether to run tests in parallel (async)

        Returns:
            Visual regression report
        """
        start_time = datetime.utcnow()
        results = []

        if parallel:
            # Run tests asynchronously
            results = asyncio.run(self._run_tests_async(tests, use_ai))
        else:
            # Run tests sequentially
            for test_config in tests:
                result = self._run_single_test_config(test_config, use_ai)
                results.append(result)

        # Generate report
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        new_baselines = sum(1 for r in results if r.baseline and not r.comparison)

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        report = VisualRegressionReport(
            suite_name="visual_regression_suite",
            total_tests=len(results),
            passed=passed,
            failed=failed,
            new_baselines=new_baselines,
            results=results,
            duration_ms=duration_ms,
        )

        logger.info(
            f"Test suite complete: {passed} passed, {failed} failed, "
            f"{new_baselines} new baselines"
        )

        return report

    async def _run_tests_async(
        self,
        tests: List[Dict[str, Any]],
        use_ai: bool,
    ) -> List[VisualTestResult]:
        """Run tests asynchronously.

        Args:
            tests: List of test configurations
            use_ai: Whether to use AI-powered comparison

        Returns:
            List of test results
        """
        tasks = [
            asyncio.to_thread(self._run_single_test_config, test, use_ai)
            for test in tests
        ]
        return await asyncio.gather(*tasks)

    def _run_single_test_config(
        self,
        test_config: Dict[str, Any],
        use_ai: bool,
    ) -> VisualTestResult:
        """Run a single test from config.

        Args:
            test_config: Test configuration dictionary
            use_ai: Whether to use AI-powered comparison

        Returns:
            Visual test result
        """
        page = test_config["page"]
        test_name = test_config["test_name"]
        viewport = test_config.get("viewport", "desktop")
        orientation = test_config.get("orientation", "portrait")

        return self.run_visual_test(
            page=page,
            test_name=test_name,
            viewport=viewport,
            orientation=orientation,
            use_ai=use_ai,
            metadata=test_config.get("metadata"),
        )

    def detect_layout_shifts(
        self,
        baseline_path: str,
        current_path: str,
        threshold: float = 0.1,
    ) -> Dict[str, Any]:
        """Detect layout shifts between two screenshots.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            threshold: Sensitivity threshold for shift detection

        Returns:
            Layout shift analysis report
        """
        comparison = self.ai_comparator.compare(baseline_path, current_path)

        layout_shifts = []
        total_shift_score = 0.0

        for diff in comparison.differences:
            if not diff.is_dynamic and diff.severity in (
                DiffSeverity.MEDIUM,
                DiffSeverity.HIGH,
                DiffSeverity.CRITICAL,
            ):
                # Calculate layout shift score based on region size and position
                # Elements higher on the page and larger elements have higher impact
                image_height = 1080  # Approximate, would need actual dimensions
                position_weight = 1.0 - (
                    diff.y / image_height
                )  # Higher weight for top elements
                size_score = (diff.width * diff.height) / (
                    1920 * 1080
                )  # Relative to screen size

                shift_score = position_weight * size_score * 100
                total_shift_score += shift_score

                layout_shifts.append(
                    {
                        "region": {
                            "x": diff.x,
                            "y": diff.y,
                            "width": diff.width,
                            "height": diff.height,
                        },
                        "severity": diff.severity.value,
                        "shift_score": round(shift_score, 4),
                        "description": diff.description,
                    }
                )

        # Sort by shift score (highest impact first)
        layout_shifts.sort(key=lambda x: x["shift_score"], reverse=True)

        return {
            "has_layout_shifts": len(layout_shifts) > 0,
            "total_shifts": len(layout_shifts),
            "total_shift_score": round(total_shift_score, 4),
            "shifts": layout_shifts[:10],  # Top 10 shifts
            "requires_attention": total_shift_score > threshold,
        }

    def compare_semantically(
        self,
        baseline_path: str,
        current_path: str,
        ignore_regions: Optional[List[Dict[str, int]]] = None,
    ) -> VisualComparison:
        """Perform semantic visual comparison.

        Uses AI to understand the content and ignore unimportant changes.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            ignore_regions: Optional regions to ignore

        Returns:
            Semantic comparison result
        """
        # Configure comparison with AI enabled
        config = ComparisonConfig(
            threshold=self.config.threshold,
            ignore_regions=ignore_regions or self.config.ignore_regions,
            ignore_dynamic_content=True,
            use_ai_detection=True,
        )

        comparator = AIComparator(config)
        return comparator.compare(baseline_path, current_path)

    def approve_test_result(
        self,
        test_result: VisualTestResult,
        description: Optional[str] = None,
    ) -> BaselineInfo:
        """Approve a test result and update baseline.

        Args:
            test_result: Test result to approve
            description: Optional approval description

        Returns:
            Updated baseline info
        """
        if not test_result.screenshot:
            raise ValueError("Test result has no screenshot to approve")

        baseline = self.baseline_manager.approve_current_as_baseline(
            test_name=test_result.test_name,
            current_screenshot_path=test_result.screenshot.file_path,
        )

        logger.info(
            f"Approved baseline for {test_result.test_name}: {description or 'No description'}"
        )

        return baseline

    def batch_approve(
        self,
        test_results: List[VisualTestResult],
    ) -> List[BaselineInfo]:
        """Batch approve multiple test results.

        Args:
            test_results: List of test results to approve

        Returns:
            List of updated baselines
        """
        baselines = []

        for result in test_results:
            if result.screenshot:
                baseline = self.approve_test_result(result)
                baselines.append(baseline)

        logger.info(f"Batch approved {len(baselines)} baselines")

        return baselines

    def get_historical_comparison(
        self,
        test_name: str,
        current_screenshot_path: str,
        lookback_count: int = 5,
    ) -> List[VisualComparison]:
        """Compare current screenshot against historical baselines.

        Args:
            test_name: Name of the test
            current_screenshot_path: Path to current screenshot
            lookback_count: Number of historical versions to compare

        Returns:
            List of comparisons with historical baselines
        """
        baseline = self.baseline_manager.get_baseline(test_name)

        if not baseline:
            logger.warning(f"No baseline found for {test_name}")
            return []

        # Get snapshots (historical versions)
        snapshots = self.baseline_manager.get_snapshots(baseline.id)
        snapshots = sorted(snapshots, key=lambda s: s.created_at, reverse=True)
        snapshots = snapshots[:lookback_count]

        comparisons = []

        # Compare with current baseline
        current_comparison = self.ai_comparator.compare(
            baseline.file_path,
            current_screenshot_path,
        )
        current_comparison.baseline_path = f"{baseline.id} (current)"
        comparisons.append(current_comparison)

        # Compare with historical snapshots
        for snapshot in snapshots:
            comparison = self.ai_comparator.compare(
                snapshot.file_path,
                current_screenshot_path,
            )
            comparison.baseline_path = (
                f"{snapshot.id} ({snapshot.created_at.isoformat()})"
            )
            comparisons.append(comparison)

        return comparisons

    def generate_approval_workflow(
        self,
        report: VisualRegressionReport,
    ) -> Dict[str, Any]:
        """Generate approval workflow for failed tests.

        Args:
            report: Visual regression report

        Returns:
            Approval workflow with suggested actions
        """
        failed_results = [r for r in report.results if not r.passed]

        workflow = {
            "total_failed": len(failed_results),
            "auto_approvable": [],
            "requires_review": [],
            "new_baselines": [],
            "actions": [],
        }

        for result in failed_results:
            if not result.baseline:
                # No baseline exists - suggest creating one
                workflow["new_baselines"].append(
                    {
                        "test_name": result.test_name,
                        "screenshot_path": result.screenshot.file_path
                        if result.screenshot
                        else None,
                        "action": "create_baseline",
                        "reason": "No baseline exists",
                    }
                )
                workflow["actions"].append(f"Create baseline for {result.test_name}")

            elif result.comparison:
                # Check if all differences are dynamic
                non_dynamic_diffs = [
                    d for d in result.comparison.differences if not d.is_dynamic
                ]

                if not non_dynamic_diffs:
                    # All differences are dynamic - auto-approvable
                    workflow["auto_approvable"].append(
                        {
                            "test_name": result.test_name,
                            "baseline_id": result.baseline.id,
                            "differences_count": len(result.comparison.differences),
                            "action": "update_baseline",
                            "reason": "All differences are dynamic content",
                        }
                    )
                    workflow["actions"].append(
                        f"Auto-approve {result.test_name} (dynamic content only)"
                    )
                else:
                    # Has significant differences - requires manual review
                    workflow["requires_review"].append(
                        {
                            "test_name": result.test_name,
                            "baseline_id": result.baseline.id,
                            "significant_diffs": len(non_dynamic_diffs),
                            "total_diffs": len(result.comparison.differences),
                            "action": "manual_review",
                            "reason": f"{len(non_dynamic_diffs)} significant differences detected",
                        }
                    )
                    workflow["actions"].append(
                        f"Review {result.test_name} ({len(non_dynamic_diffs)} significant differences)"
                    )

        return workflow

    def _resolve_viewport(
        self,
        viewport: Union[str, ViewportSize],
        orientation: str = "portrait",
    ) -> ViewportSize:
        """Resolve viewport string to ViewportSize.

        Args:
            viewport: Viewport name or ViewportSize object
            orientation: Orientation mode

        Returns:
            Resolved viewport size
        """
        if isinstance(viewport, ViewportSize):
            vp = viewport
        elif viewport in self.DEVICES:
            vp = self.DEVICES[viewport]
        else:
            # Default to desktop
            vp = self.DEVICES["desktop"]

        # Apply orientation
        if orientation in self.ORIENTATIONS:
            vp = self.ORIENTATIONS[orientation](vp)

        return vp

    def _compare_images(
        self,
        baseline_path: str,
        current_path: str,
        use_ai: bool = True,
    ) -> VisualComparison:
        """Compare two images.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            use_ai: Whether to use AI-powered comparison

        Returns:
            Visual comparison result
        """
        if use_ai:
            return self.ai_comparator.compare(baseline_path, current_path)
        else:
            return self.image_comparator.compare(baseline_path, current_path)

    def get_stats(self) -> Dict[str, Any]:
        """Get visual testing statistics.

        Returns:
            Statistics dictionary
        """
        return self.baseline_manager.get_baseline_stats()

    def cleanup(self, days: int = 90) -> int:
        """Clean up old baselines.

        Args:
            days: Remove baselines older than this many days

        Returns:
            Number of baselines removed
        """
        return self.baseline_manager.cleanup_old_baselines(days)
