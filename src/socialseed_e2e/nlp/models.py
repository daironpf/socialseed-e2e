"""Models for Natural Language to Test Code Translation.

This module defines the data models used by the NLP translation engine
to convert natural language descriptions into executable test code.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class Language(str, Enum):
    """Supported natural languages."""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    PORTUGUESE = "pt"
    ITALIAN = "it"


class IntentType(str, Enum):
    """Types of test intents that can be recognized."""

    VERIFY = "verify"
    CHECK = "check"
    TEST = "test"
    VALIDATE = "validate"
    ENSURE = "ensure"
    ASSERT = "assert"


class ActionType(str, Enum):
    """Types of actions in test descriptions."""

    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SEND = "send"
    RECEIVE = "receive"
    NAVIGATE = "navigate"
    SEARCH = "search"
    FILTER = "filter"
    SORT = "sort"
    UPLOAD = "upload"
    DOWNLOAD = "download"


class EntityType(str, Enum):
    """Types of entities that can be recognized in test descriptions."""

    USER = "user"
    ADMIN = "admin"
    ENDPOINT = "endpoint"
    API = "api"
    DATABASE = "database"
    SERVICE = "service"
    TOKEN = "token"
    CREDENTIALS = "credentials"
    REQUEST = "request"
    RESPONSE = "response"
    DATA = "data"
    FIELD = "field"
    HEADER = "header"
    PARAMETER = "parameter"


class AssertionType(str, Enum):
    """Types of assertions that can be generated."""

    EQUALS = "equals"
    CONTAINS = "contains"
    EXISTS = "exists"
    STATUS_CODE = "status_code"
    RESPONSE_TIME = "response_time"
    FIELD_EXISTS = "field_exists"
    FIELD_VALUE = "field_value"
    LIST_LENGTH = "list_length"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    MATCHES_PATTERN = "matches_pattern"
    IS_TYPE = "is_type"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


class ParsedEntity(BaseModel):
    """Entity extracted from natural language text."""

    entity_type: EntityType = Field(..., description="Type of entity")
    name: str = Field(..., description="Entity name or identifier")
    value: Optional[str] = Field(None, description="Entity value if specified")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Additional entity attributes"
    )
    position: int = Field(0, description="Position in text")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Extraction confidence")


class ParsedAction(BaseModel):
    """Action extracted from natural language text."""

    action_type: ActionType = Field(..., description="Type of action")
    target: Optional[str] = Field(None, description="Target of the action")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )
    preconditions: List[str] = Field(
        default_factory=list, description="Required preconditions"
    )
    position: int = Field(0, description="Position in text")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Extraction confidence")


class ParsedAssertion(BaseModel):
    """Assertion extracted from natural language text."""

    assertion_type: AssertionType = Field(..., description="Type of assertion")
    field: Optional[str] = Field(None, description="Field being asserted")
    expected_value: Any = Field(None, description="Expected value")
    operator: str = Field("equals", description="Comparison operator")
    negated: bool = Field(False, description="Whether assertion is negated")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Extraction confidence")


class TranslationContext(BaseModel):
    """Context information for translation."""

    language: Language = Field(default=Language.ENGLISH, description="Source language")
    service: Optional[str] = Field(None, description="Target service")
    endpoint: Optional[str] = Field(None, description="Target endpoint")
    http_method: Optional[str] = Field(None, description="HTTP method")
    auth_required: bool = Field(False, description="Whether authentication is required")
    existing_tests: List[str] = Field(
        default_factory=list, description="Existing test names for context"
    )
    project_structure: Dict[str, Any] = Field(
        default_factory=dict, description="Project structure information"
    )


class NaturalLanguageTest(BaseModel):
    """Parsed natural language test description."""

    raw_text: str = Field(..., description="Original natural language text")
    language: Language = Field(
        default=Language.ENGLISH, description="Detected language"
    )
    intent: IntentType = Field(default=IntentType.VERIFY, description="Test intent")
    description: str = Field("", description="Clean description")
    entities: List[ParsedEntity] = Field(
        default_factory=list, description="Extracted entities"
    )
    actions: List[ParsedAction] = Field(
        default_factory=list, description="Extracted actions"
    )
    assertions: List[ParsedAssertion] = Field(
        default_factory=list, description="Extracted assertions"
    )
    preconditions: List[str] = Field(
        default_factory=list, description="Test preconditions"
    )
    postconditions: List[str] = Field(
        default_factory=list, description="Test postconditions"
    )
    tags: List[str] = Field(default_factory=list, description="Test tags")
    confidence_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Overall confidence"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GeneratedCode(BaseModel):
    """Generated test code."""

    test_name: str = Field(..., description="Generated test function name")
    module_name: str = Field(..., description="Suggested module name")
    code: str = Field(..., description="Generated Python code")
    imports: List[str] = Field(default_factory=list, description="Required imports")
    docstring: str = Field("", description="Generated docstring")
    assertions_count: int = Field(0, description="Number of assertions")
    lines_of_code: int = Field(0, description="Lines of generated code")
    source_nl: str = Field("", description="Source natural language")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Generation confidence")
    requires_review: bool = Field(False, description="Whether manual review is needed")
    suggestions: List[str] = Field(
        default_factory=list, description="Improvement suggestions"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class GherkinFeature(BaseModel):
    """Gherkin/Cucumber style feature."""

    name: str = Field(..., description="Feature name")
    description: str = Field("", description="Feature description")
    background: Optional[str] = Field(None, description="Background steps")
    scenarios: List["GherkinScenario"] = Field(
        default_factory=list, description="Feature scenarios"
    )
    tags: List[str] = Field(default_factory=list, description="Feature tags")


class GherkinScenario(BaseModel):
    """Gherkin/Cucumber style scenario."""

    name: str = Field(..., description="Scenario name")
    description: str = Field("", description="Scenario description")
    given_steps: List[str] = Field(default_factory=list, description="Given steps")
    when_steps: List[str] = Field(default_factory=list, description="When steps")
    then_steps: List[str] = Field(default_factory=list, description="Then steps")
    and_steps: List[str] = Field(default_factory=list, description="And/But steps")
    examples: List[Dict[str, str]] = Field(
        default_factory=list, description="Scenario outline examples"
    )
    tags: List[str] = Field(default_factory=list, description="Scenario tags")


class TranslationResult(BaseModel):
    """Complete result of natural language to code translation."""

    success: bool = Field(True, description="Whether translation succeeded")
    parsed_test: Optional[NaturalLanguageTest] = Field(None, description="Parsed test")
    generated_code: Optional[GeneratedCode] = Field(None, description="Generated code")
    gherkin_feature: Optional[GherkinFeature] = Field(
        None, description="Gherkin feature"
    )
    errors: List[str] = Field(default_factory=list, description="Translation errors")
    warnings: List[str] = Field(
        default_factory=list, description="Translation warnings"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class TranslationHistory(BaseModel):
    """History of translations for learning and improvement."""

    translations: List[TranslationResult] = Field(default_factory=list)
    most_common_patterns: Dict[str, int] = Field(default_factory=dict)
    success_rate: float = Field(0.0, ge=0.0, le=1.0)
    average_confidence: float = Field(0.0, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class LanguagePattern(BaseModel):
    """Recognized language pattern for a specific language."""

    language: Language = Field(..., description="Language")
    pattern_type: str = Field(..., description="Type of pattern")
    pattern: str = Field(..., description="Regex or pattern string")
    example: str = Field("", description="Example phrase")
    confidence_boost: float = Field(0.1, ge=0.0, le=1.0)


# Update forward references
GherkinFeature.model_rebuild()
