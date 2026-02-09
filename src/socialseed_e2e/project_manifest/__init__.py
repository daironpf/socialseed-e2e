"""AI Project Manifest (JSON Knowledge Base) for token optimization.

This package provides functionality to generate, maintain, and query
a project knowledge manifest that stores:
- All detected endpoints and their HTTP methods
- DTO schemas and field validation rules
- Port configurations and environment variables
- Relationships between services

Example:
    >>> from socialseed_e2e.project_manifest import ManifestGenerator, ManifestAPI
    >>>
    >>> # Generate manifest
    >>> generator = ManifestGenerator("/path/to/project")
    >>> manifest = generator.generate()
    >>>
    >>> # Query manifest
    >>> api = ManifestAPI("/path/to/project")
    >>> endpoints = api.get_endpoints(method=HttpMethod.GET)
    >>> user_dto = api.get_dto("UserRequest")
"""

from socialseed_e2e.project_manifest.api import ManifestAPI, TokenOptimizedQuery

# Flow-based test generation (Issue #185)
from socialseed_e2e.project_manifest.business_logic_inference import (
    BusinessFlow,
    BusinessLogicInferenceEngine,
    EndpointRelationship,
    FlowStep,
    FlowType,
    RelationshipType,
    ValidationCriteria,
)
from socialseed_e2e.project_manifest.db_model_parsers import (
    BaseDBParser,
    ColumnInfo,
    DatabaseParserRegistry,
    DatabaseSchema,
    EntityInfo,
    EntityRelationship,
    HibernateParser,
    PrismaParser,
    SQLAlchemyParser,
    db_parser_registry,
)
from socialseed_e2e.project_manifest.deep_scanner import (
    DeepScanner,
    EnvironmentDetector,
    TechStackDetector,
)
from socialseed_e2e.project_manifest.dummy_data_generator import (
    DataGenerationContext,
    DataGenerationStrategy,
    DummyDataGenerator,
    GeneratedData,
)
from socialseed_e2e.project_manifest.file_watcher import FileWatcher, SmartSyncManager
from socialseed_e2e.project_manifest.flow_test_generator import (
    FlowBasedTestSuiteGenerator,
    GeneratedTestSuite,
)
from socialseed_e2e.project_manifest.generator import ManifestGenerator
from socialseed_e2e.project_manifest.models import (
    DtoField,
    DtoSchema,
    EndpointInfo,
    EndpointParameter,
    EnvironmentVariable,
    FileMetadata,
    HttpMethod,
    PortConfig,
    ProjectKnowledge,
    ServiceDependency,
    ServiceInfo,
    ValidationRule,
)
from socialseed_e2e.project_manifest.parsers import (
    BaseParser,
    JavaParser,
    NodeParser,
    ParseResult,
    PythonParser,
    parser_registry,
)
from socialseed_e2e.project_manifest.retrieval import (
    ContextChunk,
    RAGRetrievalEngine,
    TaskContextBuilder,
)
from socialseed_e2e.project_manifest.vector_store import ManifestVectorStore, SearchResult
from socialseed_e2e.project_manifest.vector_sync import (
    IntegratedSyncManager,
    VectorIndexSyncManager,
)

__all__ = [
    # Main classes
    "ManifestGenerator",
    "ManifestAPI",
    "TokenOptimizedQuery",
    "FileWatcher",
    "SmartSyncManager",
    # Models
    "ProjectKnowledge",
    "ServiceInfo",
    "EndpointInfo",
    "EndpointParameter",
    "DtoSchema",
    "DtoField",
    "ValidationRule",
    "PortConfig",
    "EnvironmentVariable",
    "ServiceDependency",
    "FileMetadata",
    "HttpMethod",
    # Parsers
    "BaseParser",
    "PythonParser",
    "JavaParser",
    "NodeParser",
    "ParseResult",
    "parser_registry",
    # Vector Store & RAG
    "ManifestVectorStore",
    "SearchResult",
    "RAGRetrievalEngine",
    "ContextChunk",
    "TaskContextBuilder",
    "VectorIndexSyncManager",
    "IntegratedSyncManager",
    # Deep Scanner
    "DeepScanner",
    "TechStackDetector",
    "EnvironmentDetector",
    # Business Logic Inference (Issue #185)
    "BusinessLogicInferenceEngine",
    "BusinessFlow",
    "FlowStep",
    "FlowType",
    "EndpointRelationship",
    "RelationshipType",
    "ValidationCriteria",
    # Database Model Parsers (Issue #185)
    "BaseDBParser",
    "SQLAlchemyParser",
    "PrismaParser",
    "HibernateParser",
    "DatabaseSchema",
    "EntityInfo",
    "EntityRelationship",
    "ColumnInfo",
    "DatabaseParserRegistry",
    "db_parser_registry",
    # Dummy Data Generator (Issue #185)
    "DummyDataGenerator",
    "DataGenerationStrategy",
    "GeneratedData",
    "DataGenerationContext",
    # Flow Test Generator (Issue #185)
    "FlowBasedTestSuiteGenerator",
    "GeneratedTestSuite",
]
