"""Pydantic models for test documentation generation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocFormat(str, Enum):
    """Supported documentation export formats."""

    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    OPENAPI = "openapi"


class TestStepDoc(BaseModel):
    """Documentation for a single test step."""

    step_number: int
    description: str
    action: str
    expected_result: str
    request: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None


class TestCaseDoc(BaseModel):
    """Documentation for a test case."""

    test_id: str
    test_name: str
    description: str
    module: str
    service: str
    steps: List[TestStepDoc] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    expected_outcome: str
    tags: List[str] = Field(default_factory=list)
    severity: str = "medium"
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class EndpointDoc(BaseModel):
    """Documentation for an API endpoint."""

    path: str
    method: str
    summary: str
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    security: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    test_count: int = 0


class ErrorCodeDoc(BaseModel):
    """Documentation for an error code."""

    code: str
    message: str
    description: str
    possible_causes: List[str] = Field(default_factory=list)
    resolution: Optional[str] = None


class APIDocumentation(BaseModel):
    """Complete API documentation."""

    title: str
    version: str
    description: Optional[str] = None
    base_url: str
    endpoints: List[EndpointDoc] = Field(default_factory=list)
    error_codes: List[ErrorCodeDoc] = Field(default_factory=list)
    schemas: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)


class CoverageReport(BaseModel):
    """Test coverage report."""

    total_endpoints: int = 0
    covered_endpoints: int = 0
    uncovered_endpoints: List[str] = Field(default_factory=list)
    endpoint_coverage_percent: float = 0.0
    total_scenarios: int = 0
    covered_scenarios: List[str] = Field(default_factory=list)
    gap_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)


class DocumentationProject(BaseModel):
    """Complete documentation project."""

    project_name: str
    project_path: str
    test_cases: List[TestCaseDoc] = Field(default_factory=list)
    api_docs: Optional[APIDocumentation] = None
    coverage_report: Optional[CoverageReport] = None
    generated_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
