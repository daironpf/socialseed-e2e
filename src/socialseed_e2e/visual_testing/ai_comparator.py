"""AI-powered visual comparison for detecting regressions.

This module provides intelligent visual comparison that can detect meaningful
differences while ignoring dynamic content like timestamps, ads, etc.
"""

import logging
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

from socialseed_e2e.visual_testing.models import (
    ComparisonConfig,
    ComparisonResult,
    DiffSeverity,
    VisualComparison,
    VisualDiff,
)

logger = logging.getLogger(__name__)


class ImageComparator:
    """Compare two images and detect differences."""

    def __init__(self, config: Optional[ComparisonConfig] = None):
        self.config = config or ComparisonConfig()

    def compare(
        self,
        baseline_path: str,
        current_path: str,
        diff_output_path: Optional[str] = None,
    ) -> VisualComparison:
        """Compare two images and return differences.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            diff_output_path: Optional path to save diff visualization

        Returns:
            Visual comparison result
        """
        # Load images
        baseline_img = Image.open(baseline_path).convert("RGB")
        current_img = Image.open(current_path).convert("RGB")

        # Ensure same size
        if baseline_img.size != current_img.size:
            logger.warning(
                f"Image sizes differ: {baseline_img.size} vs {current_img.size}. "
                "Resizing current to match baseline."
            )
            current_img = current_img.resize(
                baseline_img.size, Image.Resampling.LANCZOS
            )

        # Apply ignore regions
        baseline_img = self._apply_ignore_regions(baseline_img)
        current_img = self._apply_ignore_regions(current_img)

        # Calculate diff
        diff_data = self._calculate_pixel_diff(baseline_img, current_img)

        # Find diff regions
        differences = self._find_diff_regions(diff_data, baseline_img.size)

        # Calculate overall stats
        total_pixels = baseline_img.width * baseline_img.height
        pixel_diff_count = np.count_nonzero(diff_data)
        diff_percentage = (pixel_diff_count / total_pixels) * 100

        # Generate diff visualization
        if diff_output_path and pixel_diff_count > 0:
            self._create_diff_visualization(
                baseline_img, current_img, diff_data, differences, diff_output_path
            )

        # Determine result
        if pixel_diff_count == 0:
            result = ComparisonResult.MATCH
        elif diff_percentage <= self.config.threshold * 100:
            result = ComparisonResult.MATCH  # Within tolerance
        else:
            result = ComparisonResult.MISMATCH

        return VisualComparison(
            result=result,
            baseline_path=baseline_path,
            current_path=current_path,
            diff_path=diff_output_path,
            diff_percentage=diff_percentage,
            pixel_diff_count=int(pixel_diff_count),
            total_pixels=total_pixels,
            differences=differences,
            ignored_regions=self.config.ignore_regions,
            threshold=self.config.threshold,
        )

    def _apply_ignore_regions(self, image: Image.Image) -> Image.Image:
        """Apply ignore regions to image.

        Args:
            image: Input image

        Returns:
            Image with regions ignored (blacked out)
        """
        if not self.config.ignore_regions:
            return image

        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)

        for region in self.config.ignore_regions:
            x, y, w, h = region["x"], region["y"], region["width"], region["height"]
            draw.rectangle([x, y, x + w, y + h], fill=(0, 0, 0))

        return img_copy

    def _calculate_pixel_diff(
        self, baseline: Image.Image, current: Image.Image
    ) -> np.ndarray:
        """Calculate pixel-level differences.

        Args:
            baseline: Baseline image
            current: Current image

        Returns:
            Boolean array of differences
        """
        # Convert to numpy arrays
        baseline_arr = np.array(baseline)
        current_arr = np.array(current)

        # Calculate absolute difference
        diff = np.abs(baseline_arr.astype(float) - current_arr.astype(float))

        # Apply color threshold
        color_threshold = self.config.color_threshold

        # Check if difference exceeds threshold for any channel
        significant_diff = np.any(diff > color_threshold, axis=2)

        # Apply antialiasing tolerance if enabled
        if self.config.ignore_antialiasing:
            significant_diff = self._apply_antialiasing_mask(
                baseline_arr, current_arr, significant_diff
            )

        return significant_diff

    def _apply_antialiasing_mask(
        self,
        baseline_arr: np.ndarray,
        current_arr: np.ndarray,
        diff_mask: np.ndarray,
    ) -> np.ndarray:
        """Apply antialiasing tolerance to diff mask.

        Args:
            baseline_arr: Baseline image array
            current_arr: Current image array
            diff_mask: Current diff mask

        Returns:
            Updated diff mask
        """
        tolerance = self.config.antialiasing_tolerance

        # For pixels marked as different, check if they're just antialiased edges
        diff_indices = np.where(diff_mask)

        for y, x in zip(diff_indices[0], diff_indices[1]):
            # Get neighborhood
            y_min = max(0, y - tolerance)
            y_max = min(baseline_arr.shape[0], y + tolerance + 1)
            x_min = max(0, x - tolerance)
            x_max = min(baseline_arr.shape[1], x + tolerance + 1)

            baseline_neighbor = baseline_arr[y_min:y_max, x_min:x_max]
            current_neighbor = current_arr[y_min:y_max, x_min:x_max]

            # If colors are similar within neighborhood, it's likely antialiasing
            if np.allclose(
                np.mean(baseline_neighbor, axis=(0, 1)),
                np.mean(current_neighbor, axis=(0, 1)),
                atol=self.config.color_threshold,
            ):
                diff_mask[y, x] = False

        return diff_mask

    def _find_diff_regions(
        self, diff_data: np.ndarray, image_size: Tuple[int, int]
    ) -> List[VisualDiff]:
        """Find contiguous regions of differences.

        Args:
            diff_data: Boolean diff array
            image_size: Image dimensions

        Returns:
            List of diff regions
        """
        from scipy import ndimage

        # Label connected components
        labeled_array, num_features = ndimage.label(diff_data)

        differences = []

        for i in range(1, num_features + 1):
            # Get coordinates of this region
            coords = np.where(labeled_array == i)

            if len(coords[0]) == 0:
                continue

            # Calculate bounding box
            y_min, y_max = coords[0].min(), coords[0].max()
            x_min, x_max = coords[1].min(), coords[1].max()

            width = x_max - x_min + 1
            height = y_max - y_min + 1

            # Calculate diff percentage for this region
            region_size = width * height
            diff_pixels = len(coords[0])
            diff_percentage = (diff_pixels / region_size) * 100

            # Determine severity
            severity = self._calculate_severity(
                diff_percentage, region_size, image_size
            )

            diff = VisualDiff(
                x=int(x_min),
                y=int(y_min),
                width=int(width),
                height=int(height),
                diff_percentage=diff_percentage,
                severity=severity,
                description=f"Diff region with {diff_pixels} changed pixels",
            )
            differences.append(diff)

        # Sort by severity (high to low)
        severity_order = {
            DiffSeverity.CRITICAL: 4,
            DiffSeverity.HIGH: 3,
            DiffSeverity.MEDIUM: 2,
            DiffSeverity.LOW: 1,
            DiffSeverity.NONE: 0,
        }
        differences.sort(key=lambda d: severity_order.get(d.severity, 0), reverse=True)

        return differences

    def _calculate_severity(
        self,
        diff_percentage: float,
        region_size: int,
        image_size: Tuple[int, int],
    ) -> DiffSeverity:
        """Calculate severity of a diff region.

        Args:
            diff_percentage: Percentage of pixels changed
            region_size: Size of region
            image_size: Total image size

        Returns:
            Severity level
        """
        image_area = image_size[0] * image_size[1]
        region_coverage = (region_size / image_area) * 100

        if diff_percentage > 90 and region_coverage > 10:
            return DiffSeverity.CRITICAL
        elif diff_percentage > 50 or region_coverage > 5:
            return DiffSeverity.HIGH
        elif diff_percentage > 20 or region_coverage > 1:
            return DiffSeverity.MEDIUM
        elif diff_percentage > 5:
            return DiffSeverity.LOW
        else:
            return DiffSeverity.NONE

    def _create_diff_visualization(
        self,
        baseline: Image.Image,
        current: Image.Image,
        diff_data: np.ndarray,
        differences: List[VisualDiff],
        output_path: str,
    ) -> None:
        """Create visual diff image.

        Args:
            baseline: Baseline image
            current: Current image
            diff_data: Boolean diff array
            differences: List of diff regions
            output_path: Path to save visualization
        """
        # Create side-by-side comparison
        width = baseline.width * 3  # baseline, current, diff
        height = baseline.height

        result = Image.new("RGB", (width, height), (255, 255, 255))

        # Paste baseline and current
        result.paste(baseline, (0, 0))
        result.paste(current, (baseline.width, 0))

        # Create diff view
        diff_view = baseline.copy()
        diff_pixels = np.where(diff_data)

        # Highlight differences in red
        diff_arr = np.array(diff_view)
        diff_arr[diff_pixels[0], diff_pixels[1]] = [255, 0, 0]
        diff_view = Image.fromarray(diff_arr)

        # Draw rectangles around diff regions
        draw = ImageDraw.Draw(diff_view)
        for diff in differences:
            if diff.severity in (DiffSeverity.HIGH, DiffSeverity.CRITICAL):
                color = (255, 0, 0)  # Red for high severity
            elif diff.severity == DiffSeverity.MEDIUM:
                color = (255, 165, 0)  # Orange for medium
            else:
                color = (255, 255, 0)  # Yellow for low

            draw.rectangle(
                [diff.x, diff.y, diff.x + diff.width, diff.y + diff.height],
                outline=color,
                width=2,
            )

        result.paste(diff_view, (baseline.width * 2, 0))

        # Save
        result.save(output_path)


class AIComparator:
    """AI-powered visual comparison with intelligent diff detection."""

    # Known dynamic content patterns
    DYNAMIC_PATTERNS = {
        "timestamp": [
            r"\d{1,2}:\d{2}(:\d{2})?\s*(AM|PM|am|pm)?",
            r"\d{4}-\d{2}-\d{2}",
            r"\d{2}/\d{2}/\d{4}",
        ],
        "counters": [
            r"\d+\s*(views|likes|comments|shares)",
            r"\d+\s*(seconds?|minutes?|hours?|days?)\s*ago",
        ],
        "ads": [
            r"advertisement",
            r"sponsored",
            r"promoted",
        ],
    }

    def __init__(self, config: Optional[ComparisonConfig] = None):
        self.config = config or ComparisonConfig()
        self.base_comparator = ImageComparator(config)

    def compare(
        self,
        baseline_path: str,
        current_path: str,
        diff_output_path: Optional[str] = None,
    ) -> VisualComparison:
        """Compare images with AI-powered analysis.

        Args:
            baseline_path: Path to baseline image
            current_path: Path to current image
            diff_output_path: Optional path to save diff

        Returns:
            Visual comparison with AI analysis
        """
        # Perform base comparison
        comparison = self.base_comparator.compare(
            baseline_path, current_path, diff_output_path
        )

        if not self.config.use_ai_detection:
            return comparison

        # Apply AI analysis to differences
        if comparison.differences:
            comparison.differences = self._analyze_with_ai(
                baseline_path, current_path, comparison.differences
            )

            # Recalculate result based on AI analysis
            significant_diffs = [
                d
                for d in comparison.differences
                if not d.is_dynamic
                and d.severity in (DiffSeverity.HIGH, DiffSeverity.CRITICAL)
            ]

            if not significant_diffs and comparison.result == ComparisonResult.MISMATCH:
                comparison.result = ComparisonResult.MATCH
                logger.info(
                    "AI analysis: All differences are dynamic content, considering as match"
                )

        return comparison

    def _analyze_with_ai(
        self,
        baseline_path: str,
        current_path: str,
        differences: List[VisualDiff],
    ) -> List[VisualDiff]:
        """Analyze differences with AI to identify dynamic content.

        Args:
            baseline_path: Baseline image path
            current_path: Current image path
            differences: List of differences

        Returns:
            Updated differences with AI analysis
        """
        # Load images
        baseline_img = Image.open(baseline_path)
        current_img = Image.open(current_path)

        analyzed_diffs = []

        for diff in differences:
            # Extract region from both images
            baseline_region = baseline_img.crop(
                (diff.x, diff.y, diff.x + diff.width, diff.y + diff.height)
            )
            current_region = current_img.crop(
                (diff.x, diff.y, diff.x + diff.width, diff.y + diff.height)
            )

            # Analyze region
            is_dynamic = self._is_dynamic_content(baseline_region, current_region)

            if is_dynamic:
                diff.is_dynamic = True
                diff.severity = DiffSeverity.NONE
                diff.description = f"[Dynamic Content] {diff.description}"

            analyzed_diffs.append(diff)

        return analyzed_diffs

    def _is_dynamic_content(
        self,
        baseline_region: Image.Image,
        current_region: Image.Image,
    ) -> bool:
        """Check if difference is likely dynamic content.

        Args:
            baseline_region: Region from baseline
            current_region: Region from current

        Returns:
            True if likely dynamic content
        """
        # Try OCR if available
        try:
            import pytesseract

            baseline_text = pytesseract.image_to_string(baseline_region).lower()
            current_text = pytesseract.image_to_string(current_region).lower()

            # Check for known dynamic patterns
            for _pattern_name, patterns in self.DYNAMIC_PATTERNS.items():
                for pattern in patterns:
                    import re

                    if re.search(pattern, baseline_text) or re.search(
                        pattern, current_text
                    ):
                        return True

        except ImportError:
            logger.debug("pytesseract not available for OCR")
        except Exception as e:
            logger.debug(f"OCR failed: {e}")

        # Fallback: Check if regions have similar structure
        baseline_hist = self._get_color_histogram(baseline_region)
        current_hist = self._get_color_histogram(current_region)

        # If color distribution is similar but pixels differ, might be text/numbers
        hist_similarity = self._calculate_histogram_similarity(
            baseline_hist, current_hist
        )

        # High histogram similarity but pixel differences suggests text changes
        if hist_similarity > 0.9:
            return True

        return False

    def _get_color_histogram(self, image: Image.Image) -> np.ndarray:
        """Get color histogram of image.

        Args:
            image: Input image

        Returns:
            Histogram array
        """
        # Convert to small size for faster processing
        small = image.resize((50, 50))
        arr = np.array(small)

        # Calculate histogram for each channel
        histograms = []
        for i in range(3):  # RGB
            hist, _ = np.histogram(arr[:, :, i], bins=16, range=(0, 256))
            histograms.append(hist)

        return np.concatenate(histograms)

    def _calculate_histogram_similarity(
        self, hist1: np.ndarray, hist2: np.ndarray
    ) -> float:
        """Calculate similarity between two histograms.

        Args:
            hist1: First histogram
            hist2: Second histogram

        Returns:
            Similarity score (0-1)
        """
        # Normalize histograms
        hist1 = hist1.astype(float) / (hist1.sum() + 1e-10)
        hist2 = hist2.astype(float) / (hist2.sum() + 1e-10)

        # Calculate correlation
        correlation = np.corrcoef(hist1, hist2)[0, 1]

        return float(correlation) if not np.isnan(correlation) else 0.0


class PerceptualComparator:
    """Perceptual comparison using perceptual hashing."""

    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold

    def compare(
        self,
        baseline_path: str,
        current_path: str,
    ) -> VisualComparison:
        """Compare images using perceptual hashing.

        Args:
            baseline_path: Baseline image path
            current_path: Current image path

        Returns:
            Visual comparison result
        """
        # Calculate perceptual hashes
        baseline_hash = self._calculate_phash(baseline_path)
        current_hash = self._calculate_phash(current_path)

        # Calculate hamming distance
        distance = self._hamming_distance(baseline_hash, current_hash)
        max_distance = len(baseline_hash) * 4  # 4 bits per hex char
        similarity = 1 - (distance / max_distance)

        # Determine result
        if similarity >= (1 - self.threshold):
            result = ComparisonResult.MATCH
        else:
            result = ComparisonResult.MISMATCH

        return VisualComparison(
            result=result,
            baseline_path=baseline_path,
            current_path=current_path,
            diff_percentage=(1 - similarity) * 100,
            threshold=self.threshold,
        )

    def _calculate_phash(self, image_path: str) -> str:
        """Calculate perceptual hash (pHash) of image.

        Args:
            image_path: Path to image

        Returns:
            Hex hash string
        """
        from scipy import fftpack

        # Load and resize image
        img = Image.open(image_path).convert("L")  # Grayscale
        img = img.resize((32, 32), Image.Resampling.LANCZOS)

        # Apply DCT
        dct = fftpack.dct(fftpack.dct(np.array(img), axis=0), axis=1)

        # Use low frequencies
        dct_low = dct[:8, :8]

        # Calculate mean (excluding DC component)
        avg = (dct_low.sum() - dct_low[0, 0]) / 63

        # Generate hash
        diff = dct_low > avg
        hash_bits = diff.flatten()

        # Convert to hex
        hash_hex = ""
        for i in range(0, 64, 4):
            nibble = int("".join(str(int(b)) for b in hash_bits[i : i + 4]), 2)
            hash_hex += format(nibble, "x")

        return hash_hex

    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate hamming distance between two hashes.

        Args:
            hash1: First hash
            hash2: Second hash

        Returns:
            Hamming distance
        """
        if len(hash1) != len(hash2):
            raise ValueError("Hashes must be same length")

        distance = 0
        for c1, c2 in zip(hash1, hash2):
            # XOR the nibbles and count bits
            xor = int(c1, 16) ^ int(c2, 16)
            distance += bin(xor).count("1")

        return distance
