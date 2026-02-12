"""Visual Regression Testing module for API testing framework.

This module provides visual testing support for APIs that return HTML, PDFs,
or images. Uses AI to detect visual regressions and manage baselines.

Example:
    >>> from socialseed_e2e.visual_testing import Screenshotter, AIComparator
    >>> screenshotter = Screenshotter()
    >>> comparator = AIComparator()
"""

from socialseed_e2e.visual_testing.models import (
    AIDiffAnalysis,
    BaselineInfo,
    BaselineSnapshot,
    ComparisonConfig,
    ComparisonResult,
    ContentType,
    DiffSeverity,
    ImageComparisonConfig,
    PDFRenderConfig,
    ScreenshotCapture,
    ScreenshotConfig,
    ScreenshotFormat,
    ViewportSize,
    VisualComparison,
    VisualDiff,
    VisualRegressionReport,
    VisualTestResult,
    VisualTestSuite,
)
from socialseed_e2e.visual_testing.screenshotter import (
    ResponsiveScreenshotter,
    Screenshotter,
)
from socialseed_e2e.visual_testing.ai_comparator import (
    AIComparator,
    ImageComparator,
    PerceptualComparator,
)
from socialseed_e2e.visual_testing.baseline_manager import (
    BaselineManager,
    BaselineReviewer,
)

__all__ = [
    # Models
    "AIDiffAnalysis",
    "BaselineInfo",
    "BaselineSnapshot",
    "ComparisonConfig",
    "ComparisonResult",
    "ContentType",
    "DiffSeverity",
    "ImageComparisonConfig",
    "PDFRenderConfig",
    "ScreenshotCapture",
    "ScreenshotConfig",
    "ScreenshotFormat",
    "ViewportSize",
    "VisualComparison",
    "VisualDiff",
    "VisualRegressionReport",
    "VisualTestResult",
    "VisualTestSuite",
    # Screenshotter
    "Screenshotter",
    "ResponsiveScreenshotter",
    # AI Comparator
    "AIComparator",
    "ImageComparator",
    "PerceptualComparator",
    # Baseline Manager
    "BaselineManager",
    "BaselineReviewer",
]
