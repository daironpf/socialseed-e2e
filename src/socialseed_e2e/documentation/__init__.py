"""Test Documentation Generator Module.

This module provides automatic test documentation generation including:
- Test case documentation with step-by-step descriptions
- API documentation from test analysis
- Coverage reports with gap analysis
- Export to multiple formats (Markdown, HTML, OpenAPI)

Usage:
    from socialseed_e2e.documentation import TestDocGenerator, APIDocGenerator, CoverageAnalyzer

    # Generate test documentation
    generator = TestDocGenerator("/path/to/project")
    test_cases = generator.generate_docs()

    # Generate API docs from tests
    api_gen = APIDocGenerator(base_url="http://localhost:8080")
    api_docs = api_gen.generate_from_tests(test_cases)

    # Analyze coverage
    analyzer = CoverageAnalyzer()
    coverage = analyzer.analyze_coverage(test_cases, api_docs.endpoints)

    # Export documentation
    exporter = DocumentationExporter(output_dir="docs")
    exporter.export_test_cases(test_cases)
    exporter.export_api_docs(api_docs)
    exporter.export_coverage_report(coverage)
"""

from .api_doc_generator import APIDocGenerator
from .coverage_analyzer import CoverageAnalyzer
from .doc_exporter import DocumentationExporter
from .models import (
    APIDocumentation,
    CoverageReport,
    DocFormat,
    DocumentationProject,
    EndpointDoc,
    ErrorCodeDoc,
    TestCaseDoc,
    TestStepDoc,
)
from .test_doc_generator import TestDocGenerator

__all__ = [
    "DocFormat",
    "TestStepDoc",
    "TestCaseDoc",
    "EndpointDoc",
    "ErrorCodeDoc",
    "APIDocumentation",
    "CoverageReport",
    "DocumentationProject",
    "TestDocGenerator",
    "APIDocGenerator",
    "CoverageAnalyzer",
    "DocumentationExporter",
]
