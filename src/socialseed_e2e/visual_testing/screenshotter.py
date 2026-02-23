"""Screenshot capture for visual regression testing.

This module provides screenshot capture capabilities for HTML responses,
PDFs, and images for visual regression testing.
"""

import io
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from socialseed_e2e.visual_testing.models import (
    ContentType,
    ScreenshotCapture,
    ScreenshotConfig,
    ScreenshotFormat,
    ViewportSize,
)

try:
    from PIL import Image

    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

logger = logging.getLogger(__name__)


class Screenshotter:
    """Capture screenshots of HTML, PDF, and images."""

    def __init__(self, output_dir: str = ".e2e/visual_baselines"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture_html(
        self,
        page: Page,
        test_name: str,
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScreenshotCapture:
        """Capture screenshot of HTML page.

        Args:
            page: Playwright page object
            test_name: Test name for identification
            config: Screenshot configuration
            metadata: Additional metadata

        Returns:
            Screenshot capture info
        """
        config = config or ScreenshotConfig()
        metadata = metadata or {}

        # Set viewport
        page.set_viewport_size(
            {
                "width": config.viewport.width,
                "height": config.viewport.height,
            }
        )

        # Wait for network idle if configured
        if config.wait_for_network_idle:
            try:
                page.wait_for_load_state("networkidle", timeout=config.timeout)
            except PlaywrightTimeout:
                logger.warning("Timeout waiting for network idle")

        # Wait for selector if specified
        if config.wait_for_selector:
            try:
                page.wait_for_selector(config.wait_for_selector, timeout=config.timeout)
            except PlaywrightTimeout:
                logger.warning(
                    f"Timeout waiting for selector: {config.wait_for_selector}"
                )

        # Hide elements if configured
        for selector in config.hide_selectors:
            try:
                page.evaluate(
                    f'document.querySelectorAll("{selector}").forEach(el => el.style.display = "none")'
                )
            except Exception as e:
                logger.warning(f"Failed to hide selector {selector}: {e}")

        # Generate file path
        file_path = self._generate_path(test_name, config.format)

        # Capture screenshot
        screenshot_options = {
            "path": str(file_path),
            "full_page": config.full_page,
            "type": config.format.value,
        }

        if config.format == ScreenshotFormat.JPEG:
            screenshot_options["quality"] = config.quality

        if config.clip:
            screenshot_options["clip"] = config.clip

        page.screenshot(**screenshot_options)

        logger.info(f"Captured screenshot: {file_path}")

        return ScreenshotCapture(
            id=str(uuid.uuid4()),
            test_name=test_name,
            url=page.url,
            content_type=ContentType.HTML,
            file_path=str(file_path),
            viewport=config.viewport,
            config=config,
            metadata=metadata,
        )

    def capture_from_html_content(
        self,
        html_content: str,
        test_name: str,
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScreenshotCapture:
        """Capture screenshot from HTML content string.

        Args:
            html_content: HTML content string
            test_name: Test name
            config: Screenshot configuration
            metadata: Additional metadata

        Returns:
            Screenshot capture info
        """
        # Create temporary file for HTML
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(html_content)
            temp_path = f.name

        try:
            # Use Playwright to capture
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(f"file://{temp_path}")

                capture = self.capture_html(page, test_name, config, metadata)

                browser.close()
                return capture

        finally:
            # Cleanup temp file
            Path(temp_path).unlink(missing_ok=True)

    def capture_pdf(
        self,
        pdf_content: bytes,
        test_name: str,
        page_number: int = 1,
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScreenshotCapture:
        """Render PDF page as screenshot.

        Args:
            pdf_content: PDF file content (bytes)
            test_name: Test name
            page_number: Page number to render (1-indexed)
            config: Screenshot configuration
            metadata: Additional metadata

        Returns:
            Screenshot capture info
        """
        try:
            from pdf2image import convert_from_bytes

            config = config or ScreenshotConfig()

            # Convert PDF page to image
            images = convert_from_bytes(
                pdf_content,
                first_page=page_number,
                last_page=page_number,
                dpi=150,
            )

            if not images:
                raise ValueError(f"Could not render PDF page {page_number}")

            # Save image
            file_path = self._generate_path(test_name, config.format)
            images[0].save(file_path, format=config.format.value.upper())

            logger.info(f"Captured PDF screenshot: {file_path}")

            return ScreenshotCapture(
                id=str(uuid.uuid4()),
                test_name=test_name,
                url=None,
                content_type=ContentType.PDF,
                file_path=str(file_path),
                viewport=config.viewport,
                config=config,
                metadata={
                    **metadata,
                    "page_number": page_number,
                    "pdf_pages": len(images),
                },
            )

        except ImportError:
            logger.error(
                "pdf2image library not installed. Install with: pip install pdf2image"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to capture PDF: {e}")
            raise

    def capture_image(
        self,
        image_content: bytes,
        test_name: str,
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScreenshotCapture:
        """Process and save image for comparison.

        Args:
            image_content: Image file content (bytes)
            test_name: Test name
            config: Screenshot configuration
            metadata: Additional metadata

        Returns:
            Screenshot capture info
        """
        if not HAS_PIL:
            raise ImportError(
                "PIL/Pillow is required for image capture. Install with: pip install Pillow"
            )

        config = config or ScreenshotConfig()

        # Open image with PIL
        image = Image.open(io.BytesIO(image_content))

        # Convert to RGB if necessary (for consistency)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # Resize if viewport specified and different
        if config.viewport:
            current_size = image.size
            target_size = (config.viewport.width, config.viewport.height)
            if current_size != target_size:
                image = image.resize(target_size, Image.Resampling.LANCZOS)

        # Save image
        file_path = self._generate_path(test_name, config.format)

        save_kwargs = {}
        if config.format == ScreenshotFormat.JPEG:
            save_kwargs["quality"] = config.quality
            save_kwargs["optimize"] = True

        image.save(file_path, format=config.format.value.upper(), **save_kwargs)

        logger.info(f"Captured image: {file_path}")

        return ScreenshotCapture(
            id=str(uuid.uuid4()),
            test_name=test_name,
            url=None,
            content_type=ContentType.IMAGE,
            file_path=str(file_path),
            viewport=ViewportSize(width=image.width, height=image.height),
            config=config,
            metadata=metadata,
        )

    def capture_from_response(
        self,
        response: Any,
        test_name: str,
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScreenshotCapture:
        """Capture screenshot from API response.

        Automatically detects content type and captures appropriately.

        Args:
            response: API response (with content-type header and body)
            test_name: Test name
            config: Screenshot configuration
            metadata: Additional metadata

        Returns:
            Screenshot capture info
        """
        config = config or ScreenshotConfig()
        metadata = metadata or {}

        # Get content type from response
        content_type = self._detect_content_type(response)

        if content_type == ContentType.HTML:
            # HTML response - render it
            return self.capture_from_html_content(
                response.body(), test_name, config, metadata
            )

        elif content_type == ContentType.PDF:
            # PDF response
            return self.capture_pdf(
                response.body(), test_name, config=config, metadata=metadata
            )

        elif content_type == ContentType.IMAGE:
            # Image response
            return self.capture_image(
                response.body(), test_name, config=config, metadata=metadata
            )

        else:
            raise ValueError(f"Unsupported content type: {content_type}")

    def capture_multiple_viewports(
        self,
        page: Page,
        test_name: str,
        viewports: List[ViewportSize],
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ScreenshotCapture]:
        """Capture screenshots at multiple viewport sizes.

        Args:
            page: Playwright page
            test_name: Test name
            viewports: List of viewport sizes
            config: Base screenshot configuration
            metadata: Additional metadata

        Returns:
            List of screenshot captures
        """
        captures = []

        for i, viewport in enumerate(viewports):
            # Create config for this viewport
            vp_config = config.copy() if config else ScreenshotConfig()
            vp_config.viewport = viewport

            # Capture
            capture = self.capture_html(
                page,
                f"{test_name}_{viewport}",
                vp_config,
                {**metadata, "viewport_index": i},
            )
            captures.append(capture)

        return captures

    def _generate_path(self, test_name: str, format: ScreenshotFormat) -> Path:
        """Generate file path for screenshot.

        Args:
            test_name: Test name
            format: Image format

        Returns:
            File path
        """
        # Clean test name for filename
        clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in test_name)

        # Add timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{clean_name}_{timestamp}.{format.value}"
        return self.output_dir / filename

    def _detect_content_type(self, response: Any) -> ContentType:
        """Detect content type from response.

        Args:
            response: API response

        Returns:
            Detected content type
        """
        # Try to get content-type header
        headers = getattr(response, "headers", {})
        content_type_header = headers.get("content-type", "").lower()

        if "text/html" in content_type_header:
            return ContentType.HTML
        elif "application/pdf" in content_type_header:
            return ContentType.PDF
        elif any(
            img_type in content_type_header
            for img_type in ["image/png", "image/jpeg", "image/webp", "image/gif"]
        ):
            return ContentType.IMAGE
        elif "image/svg" in content_type_header:
            return ContentType.SVG

        # Try to detect from content
        body = response.body() if hasattr(response, "body") else b""

        if body.startswith(b"%PDF"):
            return ContentType.PDF
        elif body.startswith(b"<svg") or body.startswith(b"<?xml"):
            return ContentType.SVG
        elif body.startswith(b"<!DOCTYPE html") or body.startswith(b"<html"):
            return ContentType.HTML
        elif body[:4] in (b"\x89PNG", b"\xff\xd8\xff", b"GIF8"):
            return ContentType.IMAGE

        # Default to HTML
        return ContentType.HTML


class ResponsiveScreenshotter:
    """Capture responsive screenshots at multiple breakpoints."""

    # Standard responsive breakpoints
    BREAKPOINTS = {
        "mobile": ViewportSize(width=375, height=667),  # iPhone SE
        "tablet": ViewportSize(width=768, height=1024),  # iPad
        "desktop": ViewportSize(width=1920, height=1080),  # Full HD
        "large": ViewportSize(width=2560, height=1440),  # 2K
    }

    def __init__(self, screenshotter: Screenshotter):
        self.screenshotter = screenshotter

    def capture_all_breakpoints(
        self,
        page: Page,
        test_name: str,
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ScreenshotCapture]:
        """Capture screenshots at all standard breakpoints.

        Args:
            page: Playwright page
            test_name: Test name
            config: Base screenshot configuration
            metadata: Additional metadata

        Returns:
            Dictionary of breakpoint name to capture
        """
        captures = {}

        for breakpoint_name, viewport in self.BREAKPOINTS.items():
            bp_config = config.copy() if config else ScreenshotConfig()
            bp_config.viewport = viewport

            capture = self.screenshotter.capture_html(
                page,
                f"{test_name}_{breakpoint_name}",
                bp_config,
                {**metadata, "breakpoint": breakpoint_name},
            )
            captures[breakpoint_name] = capture

        return captures

    def capture_custom_breakpoints(
        self,
        page: Page,
        test_name: str,
        breakpoints: Dict[str, ViewportSize],
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ScreenshotCapture]:
        """Capture at custom breakpoints.

        Args:
            page: Playwright page
            test_name: Test name
            breakpoints: Custom breakpoints dict
            config: Base screenshot configuration
            metadata: Additional metadata

        Returns:
            Dictionary of breakpoint name to capture
        """
        captures = {}

        for breakpoint_name, viewport in breakpoints.items():
            bp_config = config.copy() if config else ScreenshotConfig()
            bp_config.viewport = viewport

            capture = self.screenshotter.capture_html(
                page,
                f"{test_name}_{breakpoint_name}",
                bp_config,
                {**metadata, "breakpoint": breakpoint_name},
            )
            captures[breakpoint_name] = capture

        return captures
