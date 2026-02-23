"""Natural Language to Test Code Translation Engine.

This module enables users to write tests in plain English, Spanish, or other
natural languages, which the framework automatically converts to executable
test code.

Key Features:
- Multi-language support (English, Spanish, French, German, Portuguese, Italian)
- Context-aware generation (understands existing API structure)
- Gherkin/Cucumber-style syntax support
- Self-documenting tests
- Requirements traceability

Example:
    >>> from socialseed_e2e.nlp import NLToCodePipeline

    >>> pipeline = NLToCodePipeline("/path/to/project")
    >>> result = pipeline.translate(
    ...     "Verify that when a user logs in with valid credentials, "
    ...     "they receive a JWT token with 24h expiration"
    ... )
    >>> print(result.generated_code.code)
"""

from socialseed_e2e.nlp.code_generator import (
    GherkinToCodeConverter,
    NLToCodePipeline,
    TestCodeGenerator,
)
from socialseed_e2e.nlp.context_awareness import (
    ContextEnricher,
    ProjectContextAnalyzer,
    RequirementsTracer,
    TestPatternMatcher,
)
from socialseed_e2e.nlp.gherkin_parser import (
    GherkinParser,
    GherkinWriter,
)
from socialseed_e2e.nlp.living_docs import (
    BusinessRule,
    BusinessRuleExtractor,
    CoverageTracker,
    DocFormat,
    LivingDocConfig,
    LivingDocumentationGenerator,
    SemanticDriftAlert,
    SemanticDriftDetector,
    TestCoverage,
)
from socialseed_e2e.nlp.models import (
    ActionType,
    AssertionType,
    EntityType,
    GeneratedCode,
    GherkinFeature,
    GherkinScenario,
    IntentType,
    Language,
    LanguagePattern,
    NaturalLanguageTest,
    ParsedAction,
    ParsedAssertion,
    ParsedEntity,
    TranslationContext,
    TranslationHistory,
    TranslationResult,
)
from socialseed_e2e.nlp.translator import (
    LanguagePatterns,
    MultiLanguageTranslator,
    NaturalLanguageParser,
    TestDescriptionBuilder,
)

__all__ = [
    # Models
    "ActionType",
    "AssertionType",
    "EntityType",
    "GeneratedCode",
    "GherkinFeature",
    "GherkinScenario",
    "IntentType",
    "Language",
    "LanguagePattern",
    "NaturalLanguageTest",
    "ParsedAction",
    "ParsedAssertion",
    "ParsedEntity",
    "TranslationContext",
    "TranslationHistory",
    "TranslationResult",
    # Translator
    "LanguagePatterns",
    "MultiLanguageTranslator",
    "NaturalLanguageParser",
    "TestDescriptionBuilder",
    # Context Awareness
    "ContextEnricher",
    "ProjectContextAnalyzer",
    "RequirementsTracer",
    "TestPatternMatcher",
    # Code Generator
    "GherkinToCodeConverter",
    "NLToCodePipeline",
    "TestCodeGenerator",
    # Gherkin Parser
    "GherkinParser",
    "GherkinWriter",
    # Living Documentation (Issue #4 - Phase 2)
    "BusinessRule",
    "BusinessRuleExtractor",
    "CoverageTracker",
    "DocFormat",
    "LivingDocConfig",
    "LivingDocumentationGenerator",
    "SemanticDriftAlert",
    "SemanticDriftDetector",
    "TestCoverage",
]
