"""Pydantic models for test data governance."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SensitivityLevel(str, Enum):
    """Data sensitivity levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class PIIType(str, Enum):
    """Types of Personally Identifiable Information."""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"


class DataClassification(BaseModel):
    """Classification of test data."""

    field_name: str
    sensitivity_level: SensitivityLevel
    pii_types: List[PIIType] = Field(default_factory=list)
    requires_encryption: bool = False
    retention_days: Optional[int] = None


class DataMaskingRule(BaseModel):
    """Rule for masking sensitive data."""

    field_pattern: str
    masking_strategy: str
    replacement: str = "***"
    preserve_length: bool = False


class GDPRCompliance(BaseModel):
    """GDPR compliance status for test data."""

    is_compliant: bool = True
    data_subject_consent: bool = True
    right_to_erasure: bool = True
    data_portability: bool = True
    processing_legitimacy: str = "legitimate_interest"
    violations: List[str] = Field(default_factory=list)


class DataRefreshPolicy(BaseModel):
    """Policy for refreshing test data."""

    frequency: str
    retention_days: int
    cleanup_strategy: str
    last_refresh: Optional[datetime] = None
    next_refresh: Optional[datetime] = None


class DataQualityRule(BaseModel):
    """Rule for validating data quality."""

    rule_name: str
    field_name: str
    rule_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_critical: bool = False


class DataQualityResult(BaseModel):
    """Result of data quality validation."""

    rule_name: str
    passed: bool
    message: str
    affected_records: int = 0


class DataGovernanceReport(BaseModel):
    """Complete data governance report."""

    total_records: int = 0
    pii_records: int = 0
    encrypted_records: int = 0
    compliant_records: int = 0
    violations: List[str] = Field(default_factory=list)
    quality_score: float = 100.0
    generated_at: datetime = Field(default_factory=datetime.now)
