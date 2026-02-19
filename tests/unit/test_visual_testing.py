"""Tests for Visual Testing Module.

This module tests the AI-powered visual regression testing features.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

# Check if numpy is available
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Check if scipy is available
try:
    import scipy

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from socialseed_e2e.visual_testing import (
    BaselineInfo,
    BaselineManager,
    BaselineReviewer,
    BaselineSnapshot,
    ComparisonConfig,
    ComparisonResult,
    ContentType,
    DiffSeverity,
    ResponsiveScreenshotter,
    ScreenshotCapture,
    ScreenshotConfig,
    ScreenshotFormat,
    Screenshotter,
    ViewportSize,
    VisualComparison,
    VisualDiff,
    VisualRegressionReport,
    VisualTestResult,
)

# Conditionally import components that require numpy/scipy
if NUMPY_AVAILABLE and SCIPY_AVAILABLE:
    from socialseed_e2e.visual_testing import (
        AIComparator,
        ImageComparator,
        PerceptualComparator,
    )

if NUMPY_AVAILABLE and SCIPY_AVAILABLE:
    from socialseed_e2e.visual_testing import VisualTestingOrchestrator


class TestViewportSize:
    """Tests for ViewportSize model."""

    def test_default_viewport(self):
        """Test default viewport creation."""
        vp = ViewportSize()
        assert vp.width == 1920
        assert vp.height == 1080
        assert vp.device_scale_factor == 1.0

    def test_custom_viewport(self):
        """Test custom viewport creation."""
        vp = ViewportSize(width=375, height=667, device_scale_factor=2.0)
        assert vp.width == 375
        assert vp.height == 667
        assert vp.device_scale_factor == 2.0

    def test_viewport_string_representation(self):
        """Test viewport string representation."""
        vp = ViewportSize(width=1920, height=1080, device_scale_factor=2.0)
        assert str(vp) == "1920x1080@2.0x"


class TestScreenshotConfig:
    """Tests for ScreenshotConfig model."""

    def test_default_config(self):
        """Test default screenshot configuration."""
        config = ScreenshotConfig()
        assert config.viewport.width == 1920
        assert config.full_page is True
        assert config.format == ScreenshotFormat.PNG
        assert config.quality == 90

    def test_custom_config(self):
        """Test custom screenshot configuration."""
        viewport = ViewportSize(width=375, height=667)
        config = ScreenshotConfig(
            viewport=viewport,
            full_page=False,
            format=ScreenshotFormat.JPEG,
            quality=80,
        )
        assert config.viewport == viewport
        assert config.full_page is False
        assert config.format == ScreenshotFormat.JPEG
        assert config.quality == 80


class TestVisualDiff:
    """Tests for VisualDiff model."""

    def test_diff_creation(self):
        """Test visual diff creation."""
        diff = VisualDiff(
            x=100,
            y=200,
            width=50,
            height=30,
            diff_percentage=15.5,
            severity=DiffSeverity.MEDIUM,
            description="Test difference",
        )
        assert diff.x == 100
        assert diff.y == 200
        assert diff.width == 50
        assert diff.height == 30
        assert diff.diff_percentage == 15.5
        assert diff.severity == DiffSeverity.MEDIUM
        assert diff.description == "Test difference"


class TestVisualComparison:
    """Tests for VisualComparison model."""

    def test_comparison_match(self):
        """Test comparison with match result."""
        comparison = VisualComparison(
            result=ComparisonResult.MATCH,
            current_path="/path/to/current.png",
            diff_percentage=0.0,
            pixel_diff_count=0,
            total_pixels=1000000,
            threshold=0.1,
        )
        assert comparison.result == ComparisonResult.MATCH
        assert comparison.has_significant_diff is False

    def test_comparison_mismatch(self):
        """Test comparison with mismatch result."""
        comparison = VisualComparison(
            result=ComparisonResult.MISMATCH,
            current_path="/path/to/current.png",
            diff_percentage=15.0,
            pixel_diff_count=150000,
            total_pixels=1000000,
            threshold=0.1,
        )
        assert comparison.result == ComparisonResult.MISMATCH
        assert comparison.has_significant_diff is True

    def test_comparison_with_differences(self):
        """Test comparison with differences list."""
        diff = VisualDiff(
            x=100,
            y=200,
            width=50,
            height=30,
            diff_percentage=15.5,
            severity=DiffSeverity.HIGH,
        )
        comparison = VisualComparison(
            result=ComparisonResult.MISMATCH,
            current_path="/path/to/current.png",
            diff_percentage=15.0,
            differences=[diff],
            threshold=0.1,
        )
        assert len(comparison.differences) == 1
        assert comparison.differences[0].severity == DiffSeverity.HIGH


class TestBaselineInfo:
    """Tests for BaselineInfo model."""

    def test_baseline_creation(self):
        """Test baseline info creation."""
        baseline = BaselineInfo(
            id="test_baseline_123",
            name="Test Baseline",
            test_name="test_homepage",
            content_type=ContentType.HTML,
            viewport=ViewportSize(width=1920, height=1080),
            file_path="/path/to/baseline.png",
            tags=["homepage", "desktop"],
            metadata={"version": "1.0"},
        )
        assert baseline.id == "test_baseline_123"
        assert baseline.name == "Test Baseline"
        assert baseline.test_name == "test_homepage"
        assert baseline.content_type == ContentType.HTML
        assert baseline.tags == ["homepage", "desktop"]


class TestVisualTestResult:
    """Tests for VisualTestResult model."""

    def test_passed_result(self):
        """Test passed test result."""
        result = VisualTestResult(
            test_name="test_homepage",
            passed=True,
            duration_ms=1500,
        )
        assert result.test_name == "test_homepage"
        assert result.passed is True
        assert result.duration_ms == 1500

    def test_failed_result(self):
        """Test failed test result."""
        result = VisualTestResult(
            test_name="test_homepage",
            passed=False,
            duration_ms=2000,
            error_message="Baseline not found",
        )
        assert result.passed is False
        assert result.error_message == "Baseline not found"


class TestVisualRegressionReport:
    """Tests for VisualRegressionReport model."""

    def test_report_creation(self):
        """Test report creation."""
        report = VisualRegressionReport(
            suite_name="visual_suite",
            total_tests=10,
            passed=8,
            failed=2,
            new_baselines=1,
            duration_ms=50000,
        )
        assert report.suite_name == "visual_suite"
        assert report.total_tests == 10
        assert report.passed == 8
        assert report.failed == 2
        assert report.new_baselines == 1

    def test_pass_rate_calculation(self):
        """Test pass rate calculation."""
        report = VisualRegressionReport(
            suite_name="visual_suite",
            total_tests=10,
            passed=7,
            failed=3,
            duration_ms=50000,
        )
        assert report.pass_rate == 0.7
        assert report.has_failures is True

    def test_zero_tests_pass_rate(self):
        """Test pass rate with zero tests."""
        report = VisualRegressionReport(
            suite_name="visual_suite",
            total_tests=0,
            passed=0,
            failed=0,
            duration_ms=0,
        )
        assert report.pass_rate == 0.0


@pytest.mark.skipif(
    not NUMPY_AVAILABLE or not SCIPY_AVAILABLE, reason="numpy/scipy not available"
)
class TestImageComparator:
    """Tests for ImageComparator."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def identical_images(self, temp_dir):
        """Create two identical images."""
        img1_path = temp_dir / "image1.png"
        img2_path = temp_dir / "image2.png"

        # Create identical images
        img = Image.new("RGB", (100, 100), color="red")
        img.save(img1_path)
        img.save(img2_path)

        return str(img1_path), str(img2_path)

    @pytest.fixture
    def different_images(self, temp_dir):
        """Create two different images."""
        img1_path = temp_dir / "baseline.png"
        img2_path = temp_dir / "current.png"

        # Create different images
        img1 = Image.new("RGB", (100, 100), color="red")
        img2 = Image.new("RGB", (100, 100), color="blue")
        img1.save(img1_path)
        img2.save(img2_path)

        return str(img1_path), str(img2_path)

    def test_compare_identical_images(self, identical_images):
        """Test comparing identical images."""
        baseline, current = identical_images
        comparator = ImageComparator()

        result = comparator.compare(baseline, current)

        assert result.result == ComparisonResult.MATCH
        assert result.diff_percentage == 0.0
        assert result.pixel_diff_count == 0

    def test_compare_different_images(self, different_images):
        """Test comparing different images."""
        baseline, current = different_images
        config = ComparisonConfig(threshold=0.5)  # High threshold to avoid match
        comparator = ImageComparator(config)

        result = comparator.compare(baseline, current)

        assert result.result == ComparisonResult.MISMATCH
        assert result.diff_percentage > 0.0
        assert result.pixel_diff_count > 0

    def test_compare_with_threshold(self, different_images):
        """Test comparison with threshold."""
        baseline, current = different_images
        config = ComparisonConfig(threshold=1.0)  # Very high threshold
        comparator = ImageComparator(config)

        result = comparator.compare(baseline, current)

        # With high threshold, even different images might match
        assert result.threshold == 1.0


@pytest.mark.skipif(
    not NUMPY_AVAILABLE or not SCIPY_AVAILABLE, reason="numpy/scipy not available"
)
class TestAIComparator:
    """Tests for AIComparator."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_ai_comparison_basic(self, temp_dir):
        """Test basic AI comparison."""
        # Create identical images
        baseline_path = temp_dir / "baseline.png"
        current_path = temp_dir / "current.png"

        img = Image.new("RGB", (100, 100), color="green")
        img.save(baseline_path)
        img.save(current_path)

        comparator = AIComparator()
        result = comparator.compare(str(baseline_path), str(current_path))

        assert result.result == ComparisonResult.MATCH

    def test_ai_comparison_detects_differences(self, temp_dir):
        """Test AI comparison detects differences."""
        baseline_path = temp_dir / "baseline.png"
        current_path = temp_dir / "current.png"

        img1 = Image.new("RGB", (100, 100), color="red")
        img2 = Image.new("RGB", (100, 100), color="blue")
        img1.save(baseline_path)
        img2.save(current_path)

        comparator = AIComparator()
        result = comparator.compare(str(baseline_path), str(current_path))

        assert result.result == ComparisonResult.MISMATCH
        assert len(result.differences) > 0

    def test_ai_comparison_with_dynamic_detection_disabled(self, temp_dir):
        """Test AI comparison with dynamic detection disabled."""
        baseline_path = temp_dir / "baseline.png"
        current_path = temp_dir / "current.png"

        img1 = Image.new("RGB", (100, 100), color="yellow")
        img2 = Image.new("RGB", (100, 100), color="orange")
        img1.save(baseline_path)
        img2.save(current_path)

        config = ComparisonConfig(use_ai_detection=False)
        comparator = AIComparator(config)
        result = comparator.compare(str(baseline_path), str(current_path))

        assert result.result == ComparisonResult.MISMATCH


@pytest.mark.skipif(
    not NUMPY_AVAILABLE or not SCIPY_AVAILABLE, reason="numpy/scipy not available"
)
class TestPerceptualComparator:
    """Tests for PerceptualComparator."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_perceptual_hash_identical(self, temp_dir):
        """Test perceptual hash comparison with identical images."""
        baseline_path = temp_dir / "baseline.png"
        current_path = temp_dir / "current.png"

        img = Image.new("RGB", (100, 100), color="purple")
        img.save(baseline_path)
        img.save(current_path)

        comparator = PerceptualComparator(threshold=0.1)
        result = comparator.compare(str(baseline_path), str(current_path))

        assert result.result == ComparisonResult.MATCH

    def test_perceptual_hash_different(self, temp_dir):
        """Test perceptual hash comparison with different images."""
        baseline_path = temp_dir / "baseline.png"
        current_path = temp_dir / "current.png"

        img1 = Image.new("RGB", (100, 100), color="red")
        img2 = Image.new("RGB", (100, 100), color="blue")
        img1.save(baseline_path)
        img2.save(current_path)

        comparator = PerceptualComparator(threshold=0.1)
        result = comparator.compare(str(baseline_path), str(current_path))

        assert result.result == ComparisonResult.MISMATCH


class TestBaselineManager:
    """Tests for BaselineManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_screenshot(self, temp_dir):
        """Create a sample screenshot."""
        screenshot_path = temp_dir / "screenshot.png"
        img = Image.new("RGB", (100, 100), color="white")
        img.save(screenshot_path)
        return str(screenshot_path)

    def test_create_baseline(self, temp_dir, sample_screenshot):
        """Test creating a baseline."""
        manager = BaselineManager(str(temp_dir))

        baseline = manager.create_baseline(
            test_name="test_homepage",
            screenshot_path=sample_screenshot,
            content_type=ContentType.HTML,
            viewport=ViewportSize(width=1920, height=1080),
            tags=["homepage", "desktop"],
        )

        assert baseline.test_name == "test_homepage"
        assert baseline.content_type == ContentType.HTML
        assert "homepage" in baseline.tags
        assert Path(baseline.file_path).exists()

    def test_get_baseline(self, temp_dir, sample_screenshot):
        """Test retrieving a baseline."""
        manager = BaselineManager(str(temp_dir))

        created = manager.create_baseline(
            test_name="test_homepage",
            screenshot_path=sample_screenshot,
        )

        retrieved = manager.get_baseline("test_homepage")

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_nonexistent_baseline(self, temp_dir):
        """Test retrieving a nonexistent baseline."""
        manager = BaselineManager(str(temp_dir))

        baseline = manager.get_baseline("nonexistent_test")

        assert baseline is None

    def test_list_baselines(self, temp_dir, sample_screenshot):
        """Test listing baselines."""
        manager = BaselineManager(str(temp_dir))

        manager.create_baseline(
            test_name="test_homepage",
            screenshot_path=sample_screenshot,
            tags=["homepage"],
        )
        manager.create_baseline(
            test_name="test_about",
            screenshot_path=sample_screenshot,
            tags=["about"],
        )

        all_baselines = manager.list_baselines()
        homepage_baselines = manager.list_baselines(tags=["homepage"])

        assert len(all_baselines) == 2
        assert len(homepage_baselines) == 1
        assert homepage_baselines[0].test_name == "test_homepage"

    def test_baseline_stats(self, temp_dir, sample_screenshot):
        """Test getting baseline statistics."""
        manager = BaselineManager(str(temp_dir))

        manager.create_baseline(
            test_name="test_homepage",
            screenshot_path=sample_screenshot,
            content_type=ContentType.HTML,
        )

        stats = manager.get_baseline_stats()

        assert stats["total_baselines"] == 1
        assert stats["content_type_breakdown"]["html"] == 1
        assert "storage_size_mb" in stats


class TestBaselineReviewer:
    """Tests for BaselineReviewer."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_review_failures_with_new_baselines(self, temp_dir):
        """Test reviewing failures with new baselines needed."""
        manager = BaselineManager(str(temp_dir))
        reviewer = BaselineReviewer(manager)

        # Create failed result without baseline
        result = VisualTestResult(
            test_name="test_new_feature",
            passed=False,
            baseline=None,
        )

        report = reviewer.review_failures([result])

        assert report["total_failures"] == 1
        assert len(report["new_baselines"]) == 1
        assert report["new_baselines"][0]["action"] == "create_baseline"

    def test_review_failures_with_dynamic_content(self, temp_dir):
        """Test reviewing failures with only dynamic content differences."""
        manager = BaselineManager(str(temp_dir))
        reviewer = BaselineReviewer(manager)

        # Create baseline
        baseline = BaselineInfo(
            id="test_baseline",
            name="Test",
            test_name="test_homepage",
            content_type=ContentType.HTML,
            viewport=ViewportSize(),
            file_path="/path/to/baseline.png",
        )

        # Create comparison with only dynamic differences
        comparison = VisualComparison(
            result=ComparisonResult.MISMATCH,
            current_path="/path/to/current.png",
            differences=[
                VisualDiff(
                    x=0,
                    y=0,
                    width=10,
                    height=10,
                    diff_percentage=50.0,
                    severity=DiffSeverity.LOW,
                    is_dynamic=True,
                )
            ],
            threshold=0.1,
        )

        result = VisualTestResult(
            test_name="test_homepage",
            passed=False,
            baseline=baseline,
            comparison=comparison,
        )

        report = reviewer.review_failures([result])

        assert len(report["suggested_updates"]) == 1
        assert (
            report["suggested_updates"][0]["reason"]
            == "All differences are dynamic content"
        )


class TestScreenshotter:
    """Tests for Screenshotter."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_capture_from_html_content(self, temp_dir):
        """Test capturing screenshot from HTML content.

        Note: This test is a placeholder. Full testing requires Playwright
        which is not available in the test environment.
        """
        screenshotter = Screenshotter(str(temp_dir))

        # Verify the screenshotter is initialized correctly
        assert screenshotter.output_dir == Path(temp_dir)

        # The actual capture_from_html_content method requires Playwright
        # which would need to be properly mocked in a full test environment
        assert hasattr(screenshotter, "capture_from_html_content")

    def test_screenshotter_output_dir_creation(self, temp_dir):
        """Test that screenshotter creates output directory."""
        output_path = temp_dir / "visual_output"
        assert not output_path.exists()

        screenshotter = Screenshotter(str(output_path))

        assert output_path.exists()
        assert screenshotter.output_dir == output_path


@pytest.mark.skipif(
    not NUMPY_AVAILABLE or not SCIPY_AVAILABLE, reason="numpy/scipy not available"
)
class TestVisualTestingOrchestrator:
    """Tests for VisualTestingOrchestrator."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_orchestrator_initialization(self, temp_dir):
        """Test orchestrator initialization."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        assert orchestrator.output_dir == Path(temp_dir)
        assert orchestrator.config is not None
        assert orchestrator.screenshotter is not None
        assert orchestrator.baseline_manager is not None
        assert orchestrator.ai_comparator is not None

    def test_resolve_viewport_by_name(self, temp_dir):
        """Test resolving viewport by device name."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        mobile_vp = orchestrator._resolve_viewport("mobile")
        assert mobile_vp.width == 375
        assert mobile_vp.height == 667

        desktop_vp = orchestrator._resolve_viewport("desktop")
        assert desktop_vp.width == 1920
        assert desktop_vp.height == 1080

    def test_resolve_viewport_with_orientation(self, temp_dir):
        """Test resolving viewport with orientation."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        landscape_vp = orchestrator._resolve_viewport("mobile", orientation="landscape")
        assert landscape_vp.width == 667  # Swapped from 375
        assert landscape_vp.height == 375  # Swapped from 667

    def test_resolve_custom_viewport(self, temp_dir):
        """Test resolving custom viewport."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        custom_vp = ViewportSize(width=800, height=600)
        resolved_vp = orchestrator._resolve_viewport(custom_vp)

        assert resolved_vp.width == 800
        assert resolved_vp.height == 600

    def test_detect_layout_shifts(self, temp_dir):
        """Test layout shift detection."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        # Create test images
        baseline_path = temp_dir / "baseline.png"
        current_path = temp_dir / "current.png"

        baseline = Image.new("RGB", (1920, 1080), color="white")
        current = Image.new("RGB", (1920, 1080), color="white")

        # Add a difference (layout shift)
        from PIL import ImageDraw

        draw = ImageDraw.Draw(current)
        draw.rectangle([100, 100, 200, 200], fill="red")

        baseline.save(baseline_path)
        current.save(current_path)

        result = orchestrator.detect_layout_shifts(
            str(baseline_path),
            str(current_path),
        )

        assert result["has_layout_shifts"] is True
        assert result["total_shifts"] > 0
        assert len(result["shifts"]) > 0

    def test_detect_layout_shifts_no_shifts(self, temp_dir):
        """Test layout shift detection with no shifts."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        # Create identical images
        baseline_path = temp_dir / "baseline.png"
        current_path = temp_dir / "current.png"

        img = Image.new("RGB", (100, 100), color="white")
        img.save(baseline_path)
        img.save(current_path)

        result = orchestrator.detect_layout_shifts(
            str(baseline_path),
            str(current_path),
        )

        assert result["has_layout_shifts"] is False
        assert result["total_shifts"] == 0

    def test_generate_approval_workflow(self, temp_dir):
        """Test generating approval workflow."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        # Create test results
        baseline = BaselineInfo(
            id="test_baseline",
            name="Test",
            test_name="test_homepage",
            content_type=ContentType.HTML,
            viewport=ViewportSize(),
            file_path="/path/to/baseline.png",
        )

        comparison = VisualComparison(
            result=ComparisonResult.MISMATCH,
            current_path="/path/to/current.png",
            differences=[
                VisualDiff(
                    x=0,
                    y=0,
                    width=10,
                    height=10,
                    diff_percentage=50.0,
                    severity=DiffSeverity.HIGH,
                    is_dynamic=False,
                )
            ],
            threshold=0.1,
        )

        failed_result = VisualTestResult(
            test_name="test_homepage",
            passed=False,
            baseline=baseline,
            comparison=comparison,
        )

        report = VisualRegressionReport(
            suite_name="test_suite",
            total_tests=1,
            passed=0,
            failed=1,
            results=[failed_result],
            duration_ms=1000,
        )

        workflow = orchestrator.generate_approval_workflow(report)

        assert workflow["total_failed"] == 1
        assert len(workflow["requires_review"]) == 1
        assert workflow["requires_review"][0]["action"] == "manual_review"

    def test_compare_semantically(self, temp_dir):
        """Test semantic comparison."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        # Create test images
        baseline_path = temp_dir / "baseline.png"
        current_path = temp_dir / "current.png"

        img = Image.new("RGB", (100, 100), color="white")
        img.save(baseline_path)
        img.save(current_path)

        result = orchestrator.compare_semantically(
            str(baseline_path),
            str(current_path),
        )

        assert isinstance(result, VisualComparison)

    def test_get_stats(self, temp_dir):
        """Test getting statistics."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        stats = orchestrator.get_stats()

        assert "total_baselines" in stats
        assert "total_snapshots" in stats
        assert "content_type_breakdown" in stats

    def test_orchestrator_devices_constant(self, temp_dir):
        """Test that orchestrator has predefined devices."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        assert "mobile" in orchestrator.DEVICES
        assert "tablet" in orchestrator.DEVICES
        assert "desktop" in orchestrator.DEVICES
        assert "mobile_small" in orchestrator.DEVICES

    def test_orchestrator_orientations_constant(self, temp_dir):
        """Test that orchestrator has orientation modes."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        assert "portrait" in orchestrator.ORIENTATIONS
        assert "landscape" in orchestrator.ORIENTATIONS

    def test_orchestrator_cleanup(self, temp_dir):
        """Test cleanup functionality."""
        orchestrator = VisualTestingOrchestrator(str(temp_dir))

        # Create a baseline first
        screenshot_path = temp_dir / "test_screenshot.png"
        img = Image.new("RGB", (100, 100), color="white")
        img.save(screenshot_path)

        orchestrator.baseline_manager.create_baseline(
            test_name="test_old",
            screenshot_path=str(screenshot_path),
        )

        # Test cleanup (should remove old baselines)
        removed = orchestrator.cleanup(days=0)  # 0 days to remove everything

        # Since we just created it, it shouldn't be removed with 90 days
        # But with 0 days, it might be
        assert isinstance(removed, int)
