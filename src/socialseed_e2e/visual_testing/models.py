"""Models for Visual Regression Testing.

This module defines the data models used by the visual testing system
for capturing, comparing, and managing visual baselines.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    """Types of content that can be visually tested."""

    HTML = "html"
    PDF = "pdf"
    IMAGE = "image"
    SVG = "svg"


class ScreenshotFormat(str, Enum):
    """Supported screenshot formats."""

    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


class ComparisonResult(str, Enum):
    """Results of visual comparison."""

    MATCH = "match"
    MISMATCH = "mismatch"
    NO_BASELINE = "no_baseline"
    ERROR = "error"


class DiffSeverity(str, Enum):
    """Severity levels for visual differences."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViewportSize(BaseModel):
    """Viewport dimensions for screenshots."""

    width: int = Field(default=1920, description="Viewport width in pixels")
    height: int = Field(default=1080, description="Viewport height in pixels")
    device_scale_factor: float = Field(
        default=1.0, description="Device scale factor (retina=2.0)"
    )

    def __str__(self) -> str:
        return f"{self.width}x{self.height}@{self.device_scale_factor}x"


class ScreenshotConfig(BaseModel):
    """Configuration for screenshot capture."""

    viewport: ViewportSize = Field(
        default_factory=ViewportSize, description="Viewport size"
    )
    full_page: bool = Field(
        default=True, description="Capture full page or viewport only"
    )
    format: ScreenshotFormat = Field(
        default=ScreenshotFormat.PNG, description="Image format"
    )
    quality: int = Field(default=90, ge=1, le=100, description="JPEG quality (1-100)")
    timeout: int = Field(default=30000, description="Wait timeout in milliseconds")
    wait_for_network_idle: bool = Field(
        default=True, description="Wait for network to be idle"
    )
    wait_for_selector: Optional[str] = Field(
        default=None, description="Wait for selector to be visible"
    )
    hide_selectors: List[str] = Field(
        default_factory=list, description="CSS selectors to hide"
    )
    clip: Optional[Dict[str, int]] = Field(
        default=None, description="Clip region {x, y, width, height}"
    )


class VisualDiff(BaseModel):
    """Represents a visual difference between two images."""

    x: int = Field(..., description="X coordinate of diff")
    y: int = Field(..., description="Y coordinate of diff")
    width: int = Field(..., description="Width of diff region")
    height: int = Field(..., description="Height of diff region")
    diff_percentage: float = Field(
        ..., description="Percentage of difference in region"
    )
    severity: DiffSeverity = Field(..., description="Severity of the difference")
    description: str = Field(default="", description="Description of the difference")
    is_dynamic: bool = Field(
        default=False, description="Whether diff is in dynamic content"
    )


class VisualComparison(BaseModel):
    """Result of visual comparison between two screenshots."""

    result: ComparisonResult = Field(..., description="Comparison result")
    baseline_path: Optional[str] = Field(None, description="Path to baseline image")
    current_path: str = Field(..., description="Path to current image")
    diff_path: Optional[str] = Field(None, description="Path to diff image")
    diff_percentage: float = Field(
        default=0.0, description="Overall difference percentage"
    )
    pixel_diff_count: int = Field(default=0, description="Number of different pixels")
    total_pixels: int = Field(default=0, description="Total pixels compared")
    differences: List[VisualDiff] = Field(
        default_factory=list, description="List of visual differences"
    )
    ignored_regions: List[Dict[str, int]] = Field(
        default_factory=list, description="Regions ignored in comparison"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    threshold: float = Field(default=0.1, description="Threshold used for comparison")

    @property
    def has_significant_diff(self) -> bool:
        """Check if there are significant differences."""
        return self.diff_percentage > self.threshold


class BaselineInfo(BaseModel):
    """Information about a visual baseline."""

    id: str = Field(..., description="Baseline identifier")
    name: str = Field(..., description="Baseline name")
    test_name: str = Field(..., description="Associated test name")
    content_type: ContentType = Field(..., description="Type of content")
    viewport: ViewportSize = Field(..., description="Viewport used")
    file_path: str = Field(..., description="Path to baseline file")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(default="", description="Who created the baseline")
    tags: List[str] = Field(default_factory=list, description="Baseline tags")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    checksum: str = Field(default="", description="File checksum")


class BaselineSnapshot(BaseModel):
    """A snapshot of a baseline at a point in time."""

    id: str = Field(..., description="Snapshot identifier")
    baseline_id: str = Field(..., description="Parent baseline ID")
    file_path: str = Field(..., description="Path to snapshot file")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    description: str = Field(default="", description="Snapshot description")


class ScreenshotCapture(BaseModel):
    """Represents a captured screenshot."""

    id: str = Field(..., description="Capture identifier")
    test_name: str = Field(..., description="Test name")
    url: Optional[str] = Field(None, description="URL captured")
    content_type: ContentType = Field(..., description="Type of content")
    file_path: str = Field(..., description="Path to screenshot file")
    viewport: ViewportSize = Field(..., description="Viewport used")
    config: ScreenshotConfig = Field(..., description="Screenshot configuration")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class VisualTestResult(BaseModel):
    """Complete result of a visual test."""

    test_name: str = Field(..., description="Test name")
    passed: bool = Field(..., description="Whether test passed")
    comparison: Optional[VisualComparison] = Field(
        None, description="Comparison result"
    )
    baseline: Optional[BaselineInfo] = Field(None, description="Baseline used")
    screenshot: Optional[ScreenshotCapture] = Field(
        None, description="Screenshot captured"
    )
    duration_ms: int = Field(default=0, description="Test duration in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = Field(None, description="Error if any")


class ComparisonConfig(BaseModel):
    """Configuration for visual comparison."""

    threshold: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Difference threshold (0-1)"
    )
    ignore_regions: List[Dict[str, int]] = Field(
        default_factory=list, description="Regions to ignore"
    )
    ignore_dynamic_content: bool = Field(
        default=True, description="Ignore known dynamic content"
    )
    use_ai_detection: bool = Field(
        default=True, description="Use AI for diff detection"
    )
    antialiasing_tolerance: int = Field(
        default=2, description="Tolerance for antialiasing"
    )
    color_threshold: int = Field(
        default=10, ge=0, le=255, description="Color difference threshold"
    )
    pixel_threshold: float = Field(
        default=0.01, description="Minimum pixel difference to consider"
    )


class VisualTestSuite(BaseModel):
    """A suite of visual tests."""

    name: str = Field(..., description="Suite name")
    tests: List[str] = Field(default_factory=list, description="Test names")
    baselines: List[str] = Field(default_factory=list, description="Baseline IDs")
    config: ComparisonConfig = Field(
        default_factory=ComparisonConfig, description="Suite configuration"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AIDiffAnalysis(BaseModel):
    """AI analysis of visual differences."""

    diff_id: str = Field(..., description="Diff identifier")
    severity: DiffSeverity = Field(..., description="AI-assessed severity")
    is_regression: bool = Field(..., description="Whether it's a regression")
    is_dynamic_content: bool = Field(
        default=False, description="Whether it's dynamic content"
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="AI confidence")
    description: str = Field(default="", description="AI description")
    suggested_action: str = Field(
        default="", description="Suggested action (approve/update baseline)"
    )
    similar_baseline_changes: List[str] = Field(
        default_factory=list, description="Similar historical changes"
    )


class PDFRenderConfig(BaseModel):
    """Configuration for PDF rendering."""

    scale: float = Field(default=1.0, description="Rendering scale")
    page_ranges: Optional[List[int]] = Field(
        default=None, description="Pages to render (None = all)"
    )
    width: Optional[int] = Field(None, description="Output width in pixels")
    height: Optional[int] = Field(None, description="Output height in pixels")
    format: ScreenshotFormat = Field(default=ScreenshotFormat.PNG)


class ImageComparisonConfig(BaseModel):
    """Configuration for image comparison."""

    tolerance: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Pixel difference tolerance"
    )
    ignore_color: bool = Field(default=False, description="Ignore color differences")
    ignore_antialiasing: bool = Field(default=True, description="Ignore antialiasing")
    crop_regions: Optional[List[Dict[str, int]]] = Field(
        default=None, description="Regions to compare"
    )


class VisualRegressionReport(BaseModel):
    """Report of visual regression test run."""

    suite_name: str = Field(..., description="Test suite name")
    total_tests: int = Field(..., description="Total tests run")
    passed: int = Field(..., description="Tests passed")
    failed: int = Field(..., description="Tests failed")
    new_baselines: int = Field(default=0, description="New baselines created")
    updated_baselines: int = Field(default=0, description="Baselines updated")
    results: List[VisualTestResult] = Field(
        default_factory=list, description="Individual test results"
    )
    duration_ms: int = Field(..., description="Total duration")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests

    @property
    def has_failures(self) -> bool:
        """Check if there are failures."""
        return self.failed > 0
