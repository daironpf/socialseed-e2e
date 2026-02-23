"""PII detection and data privacy management.

This module handles PII detection, masking, and privacy compliance
for test data.
"""

import re
from typing import Any, Dict, List, Optional

from .models import (
    DataClassification,
    DataMaskingRule,
    GDPRCompliance,
    PIIType,
    SensitivityLevel,
)


class PIIDetector:
    """Detect personally identifiable information in test data."""

    def __init__(self):
        """Initialize PII detector with default patterns."""
        self.patterns: Dict[PIIType, str] = {
            PIIType.EMAIL: r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            PIIType.PHONE: r"(\+?1?[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
            PIIType.SSN: r"\b(?!000|666|9\d{2})[0-9]{3}[-\s]?(?!00)[0-9]{2}[-\s]?(?!0000)[0-9]{4}\b",
            PIIType.CREDIT_CARD: r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
            PIIType.IP_ADDRESS: r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
            PIIType.DATE_OF_BIRTH: r"\b(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/(19|20)[0-9]{2}\b",
        }

    def detect_pii(
        self, data: Any, fields: Optional[List[str]] = None
    ) -> Dict[str, List[PIIType]]:
        """Detect PII in data.

        Args:
            data: Data to scan (dict, list, or string)
            fields: Optional list of field names to scan

        Returns:
            Dictionary mapping field names to detected PII types
        """
        detected: Dict[str, List[PIIType]] = {}

        if isinstance(data, dict):
            for key, value in data.items():
                if fields and key not in fields:
                    continue

                pii_types = self._scan_value(value)
                if pii_types:
                    detected[key] = pii_types

        elif isinstance(data, str):
            pii_types = self._scan_value(data)
            if pii_types:
                detected["value"] = pii_types

        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    for key, value in item.items():
                        pii_types = self._scan_value(value)
                        if pii_types:
                            detected[f"{i}.{key}"] = pii_types

        return detected

    def _scan_value(self, value: Any) -> List[PIIType]:
        """Scan a single value for PII patterns."""
        pii_types = []

        value_str = str(value)

        for pii_type, pattern in self.patterns.items():
            if re.search(pattern, value_str):
                pii_types.append(pii_type)

        if self._looks_like_name(value_str):
            pii_types.append(PIIType.NAME)

        if self._looks_like_address(value_str):
            pii_types.append(PIIType.ADDRESS)

        return list(set(pii_types))

    def _looks_like_name(self, value: str) -> bool:
        """Check if value looks like a person's name."""
        name_pattern = r"^[A-Z][a-z]+(\s[A-Z][a-z]+)+$"
        return bool(re.match(name_pattern, value))

    def _looks_like_address(self, value: str) -> bool:
        """Check if value looks like an address."""
        address_indicators = [
            "street",
            "avenue",
            "road",
            "blvd",
            "suite",
            "apt",
            "floor",
        ]
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in address_indicators)

    def classify_field(
        self, field_name: str, detected_pii: List[PIIType]
    ) -> DataClassification:
        """Classify a field based on detected PII.

        Args:
            field_name: Name of the field
            detected_pii: List of PII types detected

        Returns:
            DataClassification object
        """
        if not detected_pii:
            return DataClassification(
                field_name=field_name,
                sensitivity_level=SensitivityLevel.PUBLIC,
            )

        pii_to_sensitivity = {
            PIIType.SSN: SensitivityLevel.RESTRICTED,
            PIIType.CREDIT_CARD: SensitivityLevel.RESTRICTED,
            PIIType.PASSPORT: SensitivityLevel.RESTRICTED,
            PIIType.DRIVER_LICENSE: SensitivityLevel.RESTRICTED,
            PIIType.DATE_OF_BIRTH: SensitivityLevel.CONFIDENTIAL,
            PIIType.NAME: SensitivityLevel.CONFIDENTIAL,
            PIIType.ADDRESS: SensitivityLevel.CONFIDENTIAL,
            PIIType.EMAIL: SensitivityLevel.INTERNAL,
            PIIType.PHONE: SensitivityLevel.INTERNAL,
            PIIType.IP_ADDRESS: SensitivityLevel.INTERNAL,
        }

        max_sensitivity = SensitivityLevel.PUBLIC
        for pii_type in detected_pii:
            sensitivity = pii_to_sensitivity.get(pii_type, SensitivityLevel.PUBLIC)
            if sensitivity.value > max_sensitivity.value:
                max_sensitivity = sensitivity

        requires_encryption = max_sensitivity in [
            SensitivityLevel.CONFIDENTIAL,
            SensitivityLevel.RESTRICTED,
        ]

        return DataClassification(
            field_name=field_name,
            sensitivity_level=max_sensitivity,
            pii_types=detected_pii,
            requires_encryption=requires_encryption,
        )


class DataMasker:
    """Mask sensitive data in test datasets."""

    def __init__(self):
        """Initialize data masker."""
        self.default_rules: List[DataMaskingRule] = [
            DataMaskingRule(
                field_pattern=".*email.*",
                masking_strategy="email",
                replacement="***@****.***",
            ),
            DataMaskingRule(
                field_pattern=".*password.*",
                masking_strategy="fixed",
                replacement="********",
            ),
            DataMaskingRule(
                field_pattern=".*ssn.*",
                masking_strategy="partial",
                replacement="***-**-****",
            ),
            DataMaskingRule(
                field_pattern=".*credit.*",
                masking_strategy="partial",
                replacement="****-****-****-****",
            ),
            DataMaskingRule(
                field_pattern=".*phone.*",
                masking_strategy="partial",
                replacement="(***) ***-****",
            ),
        ]
        self.custom_rules: List[DataMaskingRule] = []

    def add_rule(self, rule: DataMaskingRule):
        """Add a custom masking rule."""
        self.custom_rules.append(rule)

    def mask_data(
        self, data: Any, fields: Optional[Dict[str, List[PIIType]]] = None
    ) -> Any:
        """Mask sensitive data.

        Args:
            data: Data to mask
            fields: Optional mapping of fields to PII types

        Returns:
            Masked data
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = self._mask_field(
                    key, value, fields.get(key) if fields else None
                )
            return result

        elif isinstance(data, list):
            return [self.mask_data(item, fields) for item in data]

        return data

    def _mask_field(
        self, field_name: str, value: Any, pii_types: Optional[List[PIIType]] = None
    ) -> Any:
        """Mask a single field."""
        all_rules = self.custom_rules + self.default_rules

        for rule in all_rules:
            if re.match(rule.field_pattern, field_name, re.IGNORECASE):
                return self._apply_masking(value, rule)

        if pii_types:
            return self._mask_by_pii_types(value, pii_types)

        return value

    def _apply_masking(self, value: Any, rule: DataMaskingRule) -> Any:
        """Apply a masking rule to a value."""
        if not isinstance(value, str):
            return rule.replacement

        if rule.masking_strategy == "fixed":
            return rule.replacement

        elif rule.masking_strategy == "email":
            return "user@example.com"

        elif rule.masking_strategy == "partial":
            if len(value) > 4:
                return rule.replacement
            return value

        elif rule.masking_strategy == "hash":
            import hashlib

            return hashlib.sha256(value.encode()).hexdigest()[:16]

        return rule.replacement

    def _mask_by_pii_types(self, value: Any, pii_types: List[PIIType]) -> Any:
        """Mask based on PII type."""
        if not isinstance(value, str):
            return "***"

        for pii_type in pii_types:
            if pii_type == PIIType.EMAIL:
                return "user@example.com"
            elif pii_type == PIIType.PHONE:
                return "(555) 123-4567"
            elif pii_type == PIIType.SSN:
                return "***-**-****"
            elif pii_type == PIIType.CREDIT_CARD:
                return "****-****-****-****"
            elif pii_type == PIIType.IP_ADDRESS:
                return "192.168.0.1"

        return "***"


class GDPRManager:
    """Manage GDPR compliance for test data."""

    def __init__(self):
        """Initialize GDPR manager."""
        self.compliance_rules: List[str] = []

    def check_compliance(self, data: Any) -> GDPRCompliance:
        """Check GDPR compliance for data.

        Args:
            data: Data to check

        Returns:
            GDPRCompliance result
        """
        violations = []

        pii_detector = PIIDetector()
        detected_pii = pii_detector.detect_pii(data)

        if detected_pii:
            violations.append(f"Contains PII: {', '.join(detected_pii.keys())}")

        return GDPRCompliance(
            is_compliant=len(violations) == 0,
            violations=violations,
        )

    def apply_data_subject_rights(self, data: Any, action: str) -> Any:
        """Apply data subject rights (erasure, portability).

        Args:
            data: Data to process
            action: Right to apply ('erasure', 'portability')

        Returns:
            Processed data
        """
        if action == "erasion":
            return None

        elif action == "portability":
            import json

            if isinstance(data, dict):
                return json.dumps(data, indent=2)

        return data
