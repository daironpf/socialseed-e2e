"""
Data models for Shadow Runner and Semantic Fuzzing.

This module provides Pydantic models for:
- Captured traffic data
- Fuzzing configuration
- Mutation strategies
- Test generation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class MutationType(str, Enum):
    """Types of semantic mutations for fuzzing."""

    STRING_BOUNDARY = "string_boundary"
    NUMBER_BOUNDARY = "number_boundary"
    INJECT_SQL = "inject_sql"
    INJECT_XSS = "inject_xss"
    INJECT_PATH_TRAVERSAL = "inject_path_traversal"
    INJECT_COMMAND = "inject_command"
    NULL_INJECTION = "null_injection"
    TYPE_MISMATCH = "type_mismatch"
    ENUM_EXHAUSTION = "enum_exhaustion"
    LENGTH_EXTREME = "length_extreme"
    UNICODE_FUZZING = "unicode_fuzzing"
    JSON_STRUCTURE = "json_structure"
    HEADER_INJECTION = "header_injection"
    SCHEMA_VIOLATION = "schema_violation"


class FuzzingStrategy(str, Enum):
    """Strategy for selecting mutations."""

    RANDOM = "random"
    INTELLIGENT = "intelligent"
    COVERAGE_GUIDED = "coverage_guided"
    AI_POWERED = "ai_powered"


class CaptureConfig(BaseModel):
    """Configuration for traffic capture."""

    target_url: str
    output_path: str
    filter_health_checks: bool = False
    filter_static_assets: bool = False
    sanitize_pii: bool = False
    max_requests: Optional[int] = None
    capture_duration: Optional[int] = None


class TestGenerationConfig(BaseModel):
    """Configuration for test generation from captured traffic."""

    service_name: Optional[str] = None
    group_by: str = "service"
    include_auth: bool = False
    generate_assertions: bool = True
    generate_negative_tests: bool = True


class ReplayConfig(BaseModel):
    """Configuration for traffic replay."""

    target_url: Optional[str] = None
    speed: str = "realtime"
    stop_on_error: bool = False
    iterations: int = 1


class FuzzingConfig(BaseModel):
    """Configuration for semantic fuzzing."""

    enabled: bool = True
    strategy: FuzzingStrategy = FuzzingStrategy.INTELLIGENT
    mutations_per_request: int = 5
    max_payload_size: int = 10000
    timeout: int = 30
    include_mutation_types: Optional[List[MutationType]] = None
    exclude_mutation_types: Optional[List[MutationType]] = None
    ai_model: Optional[str] = None
    semantic_understanding: bool = True

    @field_validator("include_mutation_types", "exclude_mutation_types", mode="before")
    @classmethod
    def validate_mutation_lists(cls, v):
        if v is None:
            return v
        return [MutationType(m) if isinstance(m, str) else m for m in v]


class CapturedRequest(BaseModel):
    """A single captured HTTP request."""

    id: str
    timestamp: datetime
    method: HttpMethod
    url: str
    path: str
    headers: Dict[str, str] = {}
    query_params: Dict[str, str] = {}
    body: Optional[Dict[str, Any]] = None
    form_data: Optional[Dict[str, str]] = None
    matched_service: Optional[str] = None
    status_code: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None

    model_config = {"populate_by_name": True}


class CapturedTraffic(BaseModel):
    """Container for captured traffic data."""

    capture_id: str
    capture_time: datetime
    source_url: str
    requests: List[CapturedRequest] = []
    metadata: Dict[str, Any] = {}

    model_config = {"populate_by_name": True}


class MutatedRequest(BaseModel):
    """A request after mutation/fuzzing."""

    original_request: CapturedRequest
    mutation_type: MutationType
    mutated_field: str
    original_value: Any
    mutated_value: Any
    fuzzing_strategy: FuzzingStrategy
    generation_timestamp: datetime = Field(default_factory=datetime.now)


class FuzzingResult(BaseModel):
    """Result of a fuzzing campaign."""

    campaign_id: str
    original_request: CapturedRequest
    mutated_requests: List[MutatedRequest]
    execution_results: List[Dict[str, Any]] = []
    vulnerabilities_found: List[Dict[str, Any]] = []
    errors_detected: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"populate_by_name": True}


class TestGenerationResult(BaseModel):
    """Result of test generation from captured traffic."""

    generated_tests: List[Dict[str, Any]]
    test_count: int
    service_name: Optional[str]
    generation_time: datetime = Field(default_factory=datetime.now)
    coverage_report: Optional[Dict[str, Any]] = None


class TrafficAnalysis(BaseModel):
    """Analysis results from captured traffic."""

    total_requests: int = 0
    unique_endpoints: int = 0
    methods: Dict[str, int] = {}
    status_codes: Dict[str, int] = {}
    endpoints_by_service: Dict[str, List[str]] = {}
    auth_required_endpoints: List[str] = []
    pii_detected: bool = False
    potential_security_issues: List[Dict[str, Any]] = []

    model_config = {"populate_by_name": True}


class SemanticMutation(BaseModel):
    """A semantic-aware mutation generated by AI."""

    mutation_id: str
    request_id: str
    field_path: str
    original_value: Any
    mutated_value: Any
    mutation_reason: str
    expected_impact: str
    severity: str = "medium"


class FuzzingCampaign(BaseModel):
    """A complete fuzzing campaign configuration and results."""

    campaign_id: str
    name: str
    description: str
    source_capture: Optional[str] = None
    target_url: str
    fuzzing_config: FuzzingConfig
    status: str = "pending"
    results: List[FuzzingResult] = []
    total_mutations: int = 0
    successful_mutations: int = 0
    failed_mutations: int = 0
    vulnerabilities_found: List[Dict[str, Any]] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    model_config = {"populate_by_name": True}


__all__ = [
    "HttpMethod",
    "MutationType",
    "FuzzingStrategy",
    "CaptureConfig",
    "TestGenerationConfig",
    "ReplayConfig",
    "FuzzingConfig",
    "CapturedRequest",
    "CapturedTraffic",
    "MutatedRequest",
    "FuzzingResult",
    "TestGenerationResult",
    "TrafficAnalysis",
    "SemanticMutation",
    "FuzzingCampaign",
]
