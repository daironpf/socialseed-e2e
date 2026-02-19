"""
Locator repair engine for self-healing tests.

Repairs broken element locators by finding alternative selectors.
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from difflib import SequenceMatcher

from ..models import (
    LocatorRepair,
    TestFailure,
    HealingSuggestion,
    HealingType,
    ChangeType,
)


class LocatorRepairEngine:
    """Engine for repairing broken element locators.

    Uses multiple strategies to find alternative locators when elements change:
    - Attribute-based matching
    - Structural matching
    - Text content matching
    - Visual similarity (if available)

    Example:
        engine = LocatorRepairEngine()

        repair = engine.repair_locator(
            broken_locator="#submit-btn",
            locator_type="css",
            page_content=html_content
        )

        if repair.confidence > 0.8:
            print(f"Found new locator: {repair.new_locator}")
    """

    # Common locator patterns
    LOCATOR_PATTERNS = {
        "css": {
            "id": r"#([a-zA-Z][a-zA-Z0-9_-]*)",
            "class": r"\.([a-zA-Z][a-zA-Z0-9_-]*)",
            "attribute": r"\[([^=\]]+)(?:=([^\]]*))?\]",
            "tag": r"^([a-zA-Z]+)",
        },
        "xpath": {
            "id": r"@id=['\"]([^'\"]+)['\"]",
            "class": r"@class=['\"]([^'\"]+)['\"]",
            "attribute": r"@([^=\]]+)(?:=([^\]]*))?",
            "tag": r"//([a-zA-Z]+)",
        },
    }

    def __init__(self):
        """Initialize locator repair engine."""
        self.repair_history: List[LocatorRepair] = []

    def repair_locator(
        self,
        broken_locator: str,
        locator_type: str,
        page_content: str,
        element_attributes: Optional[Dict[str, Any]] = None,
    ) -> LocatorRepair:
        """Attempt to repair a broken locator.

        Args:
            broken_locator: The original broken locator
            locator_type: Type of locator (css, xpath, etc.)
            page_content: Current page HTML/content
            element_attributes: Known attributes of the element

        Returns:
            LocatorRepair with new locator and confidence score
        """
        # Try different repair strategies
        strategies = [
            self._repair_by_id,
            self._repair_by_class,
            self._repair_by_attributes,
            self._repair_by_text,
            self._repair_by_structure,
        ]

        best_repair = None
        best_confidence = 0.0

        for strategy in strategies:
            try:
                repair = strategy(
                    broken_locator=broken_locator,
                    locator_type=locator_type,
                    page_content=page_content,
                    element_attributes=element_attributes or {},
                )

                if repair and repair.confidence > best_confidence:
                    best_repair = repair
                    best_confidence = repair.confidence

            except Exception:
                continue

        if best_repair is None:
            # Fallback: return original with low confidence
            best_repair = LocatorRepair(
                id=str(uuid.uuid4()),
                old_locator=broken_locator,
                new_locator=broken_locator,
                locator_type=locator_type,
                confidence=0.1,
                repair_strategy="fallback_original",
            )

        self.repair_history.append(best_repair)
        return best_repair

    def analyze_locator_failure(
        self,
        failure: TestFailure,
        page_source: Optional[str] = None,
    ) -> List[HealingSuggestion]:
        """Analyze a test failure and suggest locator repairs.

        Args:
            failure: Test failure information
            page_source: Current page source if available

        Returns:
            List of healing suggestions
        """
        suggestions = []

        # Extract locator from error message
        locator_match = self._extract_locator_from_error(failure.error_message)

        if locator_match and page_source:
            locator, loc_type = locator_match

            repair = self.repair_locator(
                broken_locator=locator,
                locator_type=loc_type,
                page_content=page_source,
            )

            if repair.confidence > 0.5:
                suggestion = HealingSuggestion(
                    id=str(uuid.uuid4()),
                    healing_type=HealingType.LOCATOR_REPAIR,
                    change_type=ChangeType.LOCATOR_CHANGED,
                    description=f"Replace broken locator '{locator}' with '{repair.new_locator}'",
                    code_patch=self._generate_locator_patch(
                        old_locator=locator,
                        new_locator=repair.new_locator,
                        locator_type=loc_type,
                    ),
                    confidence=repair.confidence,
                    affected_files=[failure.test_file],
                    auto_applicable=repair.confidence > 0.8,
                )
                suggestions.append(suggestion)

        return suggestions

    def _extract_locator_from_error(
        self, error_message: str
    ) -> Optional[Tuple[str, str]]:
        """Extract locator information from error message.

        Args:
            error_message: Error message to parse

        Returns:
            Tuple of (locator, type) or None
        """
        # CSS selector patterns
        css_patterns = [
            r"selector ['\"]([^'\"]+)['\"]",
            r"css ['\"]([^'\"]+)['\"]",
            r"element ['\"]([^'\"]+)['\"]",
            r"locator ['\"]([^'\"]+)['\"]",
        ]

        for pattern in css_patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return (match.group(1), "css")

        # XPath patterns
        xpath_patterns = [
            r"xpath ['\"]([^'\"]+)['\"]",
            r"//[^/\s]+(?:\[[^\]]*\])?",
        ]

        for pattern in xpath_patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return (match.group(0), "xpath")

        return None

    def _repair_by_id(
        self,
        broken_locator: str,
        locator_type: str,
        page_content: str,
        element_attributes: Dict[str, Any],
    ) -> Optional[LocatorRepair]:
        """Try to repair by finding element with similar ID."""
        # Extract ID from broken locator
        id_match = re.search(self.LOCATOR_PATTERNS[locator_type]["id"], broken_locator)

        if not id_match:
            return None

        old_id = id_match.group(1)

        # Search for similar IDs in page content
        all_ids = re.findall(r'id=["\']([^"\']+)["\']', page_content)

        if old_id in all_ids:
            # ID still exists, locator might be correct but element not loaded
            return LocatorRepair(
                id=str(uuid.uuid4()),
                old_locator=broken_locator,
                new_locator=broken_locator,
                locator_type=locator_type,
                confidence=0.3,
                repair_strategy="id_still_exists",
            )

        # Find most similar ID
        best_match = None
        best_similarity = 0.0

        for page_id in all_ids:
            similarity = SequenceMatcher(None, old_id, page_id).ratio()
            if similarity > best_similarity and similarity > 0.6:
                best_similarity = similarity
                best_match = page_id

        if best_match:
            if locator_type == "css":
                new_locator = broken_locator.replace(f"#{old_id}", f"#{best_match}")
            else:
                new_locator = broken_locator.replace(old_id, best_match)

            return LocatorRepair(
                id=str(uuid.uuid4()),
                old_locator=broken_locator,
                new_locator=new_locator,
                locator_type=locator_type,
                confidence=best_similarity * 0.9,
                repair_strategy="similar_id_match",
            )

        return None

    def _repair_by_class(
        self,
        broken_locator: str,
        locator_type: str,
        page_content: str,
        element_attributes: Dict[str, Any],
    ) -> Optional[LocatorRepair]:
        """Try to repair by finding element with similar class."""
        class_match = re.search(
            self.LOCATOR_PATTERNS[locator_type]["class"], broken_locator
        )

        if not class_match:
            return None

        old_class = class_match.group(1)
        all_classes = re.findall(r'class=["\']([^"\']+)["\']', page_content)

        # Check if class still exists
        for class_attr in all_classes:
            if old_class in class_attr.split():
                return LocatorRepair(
                    id=str(uuid.uuid4()),
                    old_locator=broken_locator,
                    new_locator=broken_locator,
                    locator_type=locator_type,
                    confidence=0.3,
                    repair_strategy="class_still_exists",
                )

        return None

    def _repair_by_attributes(
        self,
        broken_locator: str,
        locator_type: str,
        page_content: str,
        element_attributes: Dict[str, Any],
    ) -> Optional[LocatorRepair]:
        """Try to repair by finding element with similar attributes."""
        if not element_attributes:
            return None

        # Use provided attributes to find matching element
        if "data-testid" in element_attributes:
            testid = element_attributes["data-testid"]
            if (
                f'data-testid="{testid}"' in page_content
                or f"data-testid='{testid}'" in page_content
            ):
                new_locator = (
                    f'[data-testid="{testid}"]'
                    if locator_type == "css"
                    else f"//*[@data-testid='{testid}']"
                )
                return LocatorRepair(
                    id=str(uuid.uuid4()),
                    old_locator=broken_locator,
                    new_locator=new_locator,
                    locator_type=locator_type,
                    confidence=0.95,
                    repair_strategy="data_testid_match",
                    element_attributes=element_attributes,
                )

        if "name" in element_attributes:
            name = element_attributes["name"]
            if f'name="{name}"' in page_content or f"name='{name}'" in page_content:
                new_locator = (
                    f'[name="{name}"]'
                    if locator_type == "css"
                    else f"//*[@name='{name}']"
                )
                return LocatorRepair(
                    id=str(uuid.uuid4()),
                    old_locator=broken_locator,
                    new_locator=new_locator,
                    locator_type=locator_type,
                    confidence=0.85,
                    repair_strategy="name_attribute_match",
                    element_attributes=element_attributes,
                )

        return None

    def _repair_by_text(
        self,
        broken_locator: str,
        locator_type: str,
        page_content: str,
        element_attributes: Dict[str, Any],
    ) -> Optional[LocatorRepair]:
        """Try to repair by finding element with similar text content."""
        if "text" not in element_attributes:
            return None

        old_text = element_attributes["text"]

        # Look for similar text in page
        # This is a simplified version - real implementation would use more sophisticated matching
        if locator_type == "css":
            new_locator = f':contains("{old_text}")'
        else:
            new_locator = f"//*[contains(text(), '{old_text}')]"

        return LocatorRepair(
            id=str(uuid.uuid4()),
            old_locator=broken_locator,
            new_locator=new_locator,
            locator_type=locator_type,
            confidence=0.6,
            repair_strategy="text_content_match",
            element_attributes=element_attributes,
        )

    def _repair_by_structure(
        self,
        broken_locator: str,
        locator_type: str,
        page_content: str,
        element_attributes: Dict[str, Any],
    ) -> Optional[LocatorRepair]:
        """Try to repair by finding element with similar DOM structure."""
        # This would require more sophisticated DOM parsing
        # For now, return None
        return None

    def _generate_locator_patch(
        self,
        old_locator: str,
        new_locator: str,
        locator_type: str,
    ) -> str:
        """Generate a code patch for locator replacement.

        Args:
            old_locator: Original locator
            new_locator: New locator
            locator_type: Type of locator

        Returns:
            Code patch string
        """
        return f"""# Locator Repair Patch
# Old: {old_locator}
# New: {new_locator}
# Type: {locator_type}

# Replace this:
# element = page.locator("{old_locator}")

# With this:
element = page.locator("{new_locator}")
"""

    def get_repair_history(self) -> List[LocatorRepair]:
        """Get history of all repairs performed.

        Returns:
            List of LocatorRepair objects
        """
        return self.repair_history
