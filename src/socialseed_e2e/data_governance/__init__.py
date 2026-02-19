"""Test Data Governance Module.

This module provides comprehensive test data governance including:
- PII detection and masking
- GDPR compliance management
- Data lifecycle and refresh automation
- Data subset generation
- Data quality validation

Usage:
    from socialseed_e2e.data_governance import (
        PIIDetector, DataMasker, GDPRManager,
        DataLifecycleManager, DataSubsetGenerator,
        DataQualityValidator, DataGovernanceOrchestrator
    )

    # Detect PII
    detector = PIIDetector()
    pii = detector.detect_pii(user_data)

    # Mask sensitive data
    masker = DataMasker()
    masked = masker.mask_data(user_data, pii)

    # Manage lifecycle
    lifecycle = DataLifecycleManager()
    lifecycle.snapshot_data("users", users)

    # Validate quality
    validator = DataQualityValidator()
    validator.add_rule(DataQualityRule(...))
    results = validator.validate_data(users)
"""

from .models import (
    SensitivityLevel,
    PIIType,
    DataClassification,
    DataMaskingRule,
    GDPRCompliance,
    DataRefreshPolicy,
    DataQualityRule,
    DataQualityResult,
    DataGovernanceReport,
)
from .privacy import PIIDetector, DataMasker, GDPRManager
from .data_manager import (
    DataLifecycleManager,
    DataSubsetGenerator,
    DataQualityValidator,
    DataGovernanceOrchestrator,
)

__all__ = [
    "SensitivityLevel",
    "PIIType",
    "DataClassification",
    "DataMaskingRule",
    "GDPRCompliance",
    "DataRefreshPolicy",
    "DataQualityRule",
    "DataQualityResult",
    "DataGovernanceReport",
    "PIIDetector",
    "DataMasker",
    "GDPRManager",
    "DataLifecycleManager",
    "DataSubsetGenerator",
    "DataQualityValidator",
    "DataGovernanceOrchestrator",
]
