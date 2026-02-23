"""Intent Parser for AI Agent Communication Protocol.

This module provides intent recognition and parsing capabilities
for understanding AI agent requests.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from socialseed_e2e.ai_protocol.message_formats import Intent, IntentType


@dataclass
class IntentPattern:
    """Pattern for recognizing an intent."""

    intent_type: IntentType
    patterns: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    required_entities: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.6


class IntentParser:
    """Parser for recognizing intents from user input."""

    # Define intent patterns
    INTENT_PATTERNS = [
        IntentPattern(
            intent_type=IntentType.GENERATE_TESTS,
            patterns=[
                r"generate.*test",
                r"create.*test",
                r"write.*test",
                r"make.*test",
                r"build.*test",
                r"produce.*test",
            ],
            keywords=["generate", "create", "write", "test", "tests", "testing"],
            required_entities=["target"],
        ),
        IntentPattern(
            intent_type=IntentType.EXECUTE_TESTS,
            patterns=[
                r"run.*test",
                r"execute.*test",
                r"perform.*test",
                r"start.*test",
                r"launch.*test",
            ],
            keywords=["run", "execute", "perform", "test", "tests"],
        ),
        IntentPattern(
            intent_type=IntentType.ANALYZE_CODE,
            patterns=[
                r"analyze.*code",
                r"scan.*code",
                r"review.*code",
                r"examine.*code",
                r"inspect.*code",
            ],
            keywords=["analyze", "scan", "review", "code", "analyze"],
        ),
        IntentPattern(
            intent_type=IntentType.FIX_TEST,
            patterns=[
                r"fix.*test",
                r"repair.*test",
                r"correct.*test",
                r"debug.*test",
                r"resolve.*test",
            ],
            keywords=["fix", "repair", "correct", "debug", "test"],
        ),
        IntentPattern(
            intent_type=IntentType.CREATE_SERVICE,
            patterns=[
                r"create.*service",
                r"new.*service",
                r"add.*service",
                r"setup.*service",
                r"initialize.*service",
            ],
            keywords=["create", "new", "add", "service"],
            required_entities=["service_name"],
        ),
        IntentPattern(
            intent_type=IntentType.CONFIGURE,
            patterns=[
                r"config",
                r"setup",
                r"setting",
                r"configure",
                r"adjust",
            ],
            keywords=["config", "setup", "setting", "configure"],
        ),
        IntentPattern(
            intent_type=IntentType.QUERY,
            patterns=[
                r"what.*is",
                r"how.*to",
                r"show.*me",
                r"get.*info",
                r"query",
                r"find",
                r"search",
            ],
            keywords=["what", "how", "show", "get", "query", "find"],
        ),
        IntentPattern(
            intent_type=IntentType.VALIDATE,
            patterns=[
                r"validate",
                r"verify",
                r"check",
                r"confirm",
                r"ensure",
            ],
            keywords=["validate", "verify", "check", "confirm"],
        ),
        IntentPattern(
            intent_type=IntentType.REFACTOR,
            patterns=[
                r"refactor",
                r"restructure",
                r"rewrite",
                r"improve",
                r"optimize",
            ],
            keywords=["refactor", "restructure", "rewrite", "improve"],
        ),
        IntentPattern(
            intent_type=IntentType.DOCUMENT,
            patterns=[
                r"document",
                r"doc",
                r"explain",
                r"describe",
                r"document",
            ],
            keywords=["document", "doc", "explain", "describe"],
        ),
    ]

    # Entity extractors
    ENTITY_EXTRACTORS = {
        "service_name": [
            r"service[s]?\s+(?:called\s+)?['\"]?([\w-]+)['\"]?",
            r"for\s+(?:the\s+)?([\w-]+)\s+service",
            r"(?:new|create)\s+([\w-]+)\s+service",
        ],
        "target": [
            r"for\s+(?:the\s+)?([\w-]+)",
            r"target[s]?\s+['\"]?([\w-]+)['\"]?",
            r"on\s+([\w-]+)",
        ],
        "module": [
            r"module[s]?\s+['\"]?([\w-]+)['\"]?",
            r"in\s+(?:the\s+)?([\w-]+)\s+module",
        ],
        "endpoint": [
            r"endpoint[s]?\s+['\"]?([\w/-]+)['\"]?",
            r"path[s]?\s+['\"]?([\w/-]+)['\"]?",
        ],
        "language": [
            r"(?:in|for)\s+(?:the\s+)?([\w]+)\s+(?:language|project)",
            r"([\w]+)\s+(?:code|project|app)",
        ],
    }

    def __init__(self):
        """Initialize the intent parser."""
        self.patterns = self.INTENT_PATTERNS

    def parse(self, user_input: str) -> Intent:
        """Parse user input and recognize intent.

        Args:
            user_input: The user input string

        Returns:
            Recognized Intent with confidence and entities
        """
        input_lower = user_input.lower()

        # Score each intent pattern
        scored_intents = []
        for pattern in self.patterns:
            score = self._calculate_score(input_lower, pattern)
            scored_intents.append((pattern, score))

        # Sort by score
        scored_intents.sort(key=lambda x: x[1], reverse=True)

        # Get best match
        best_pattern, best_score = scored_intents[0]

        # Extract entities
        entities = self._extract_entities(user_input)

        # Build alternative intents
        alternatives = []
        for pattern, score in scored_intents[1:4]:  # Top 3 alternatives
            if score > 0.3:
                alternatives.append(
                    {
                        "intent_type": pattern.intent_type.value,
                        "confidence": score,
                    }
                )

        # Check if confidence is too low
        if best_score < best_pattern.confidence_threshold:
            return Intent(
                intent_type=IntentType.UNKNOWN,
                confidence=best_score,
                entities=entities,
                raw_input=user_input,
                alternative_intents=alternatives,
            )

        return Intent(
            intent_type=best_pattern.intent_type,
            confidence=best_score,
            entities=entities,
            raw_input=user_input,
            alternative_intents=alternatives,
        )

    def _calculate_score(self, user_input: str, pattern: IntentPattern) -> float:
        """Calculate confidence score for a pattern.

        Args:
            user_input: Lowercase user input
            pattern: Intent pattern to match

        Returns:
            Confidence score between 0 and 1
        """
        scores = []

        # Check regex patterns
        pattern_score = 0.0
        for regex_pattern in pattern.patterns:
            if re.search(regex_pattern, user_input, re.IGNORECASE):
                pattern_score = max(pattern_score, 0.8)
        scores.append(pattern_score)

        # Check keywords
        keyword_score = 0.0
        matched_keywords = 0
        for keyword in pattern.keywords:
            if keyword.lower() in user_input:
                matched_keywords += 1
        if pattern.keywords:
            keyword_score = (matched_keywords / len(pattern.keywords)) * 0.6
        scores.append(keyword_score)

        # Calculate final score
        final_score = max(scores) if scores else 0.0

        # Boost score if required entities are present
        if pattern.required_entities:
            entities = self._extract_entities(user_input)
            required_found = sum(
                1 for req in pattern.required_entities if req in entities
            )
            if required_found == len(pattern.required_entities):
                final_score = min(1.0, final_score + 0.1)

        return final_score

    def _extract_entities(self, user_input: str) -> Dict[str, Any]:
        """Extract entities from user input.

        Args:
            user_input: The user input string

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        for entity_type, patterns in self.ENTITY_EXTRACTORS.items():
            for pattern in patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                    entities[entity_type] = match.group(1)
                    break

        # Extract additional context
        entities["_raw_input"] = user_input
        entities["_word_count"] = len(user_input.split())

        return entities

    def add_custom_pattern(
        self,
        intent_type: IntentType,
        patterns: List[str],
        keywords: List[str],
        confidence_threshold: float = 0.6,
    ) -> None:
        """Add a custom intent pattern.

        Args:
            intent_type: Type of intent
            patterns: List of regex patterns
            keywords: List of keywords
            confidence_threshold: Minimum confidence threshold
        """
        custom_pattern = IntentPattern(
            intent_type=intent_type,
            patterns=patterns,
            keywords=keywords,
            confidence_threshold=confidence_threshold,
        )
        self.patterns.append(custom_pattern)

    def get_supported_intents(self) -> List[Dict[str, Any]]:
        """Get list of supported intents.

        Returns:
            List of intent information
        """
        return [
            {
                "intent_type": pattern.intent_type.value,
                "keywords": pattern.keywords,
                "required_entities": pattern.required_entities,
            }
            for pattern in self.patterns
        ]

    def validate_intent(self, intent: Intent) -> Tuple[bool, List[str]]:
        """Validate that an intent has all required entities.

        Args:
            intent: The intent to validate

        Returns:
            Tuple of (is_valid, missing_entities)
        """
        # Find the pattern for this intent
        pattern = None
        for p in self.patterns:
            if p.intent_type == intent.intent_type:
                pattern = p
                break

        if not pattern:
            return True, []

        # Check required entities
        missing = []
        for required in pattern.required_entities:
            if required not in intent.entities:
                missing.append(required)

        return len(missing) == 0, missing


class ContextualIntentParser(IntentParser):
    """Intent parser with context awareness."""

    def __init__(self):
        """Initialize the contextual parser."""
        super().__init__()
        self.context_history: List[Intent] = []
        self.max_history = 5

    def parse_with_context(
        self, user_input: str, context: Dict[str, Any] = None
    ) -> Intent:
        """Parse intent with context awareness.

        Args:
            user_input: User input string
            context: Additional context information

        Returns:
            Recognized Intent
        """
        # Get base intent
        intent = self.parse(user_input)

        # Enhance with context
        if context:
            intent.context.update(context)

        # Use history for disambiguation
        if intent.confidence < 0.7 and self.context_history:
            # Check if similar to previous intent
            last_intent = self.context_history[-1]
            if self._is_similar(intent, last_intent):
                intent.confidence = min(1.0, intent.confidence + 0.1)
                intent.context["inferred_from_history"] = True

        # Add to history
        self.context_history.append(intent)
        if len(self.context_history) > self.max_history:
            self.context_history.pop(0)

        return intent

    def _is_similar(self, intent1: Intent, intent2: Intent) -> bool:
        """Check if two intents are similar.

        Args:
            intent1: First intent
            intent2: Second intent

        Returns:
            True if intents are similar
        """
        # Same intent type
        if intent1.intent_type == intent2.intent_type:
            return True

        # Similar entities
        entities1 = set(intent1.entities.keys())
        entities2 = set(intent2.entities.keys())
        if entities1 & entities2:
            return True

        return False

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of conversation context.

        Returns:
            Context summary
        """
        if not self.context_history:
            return {"empty": True}

        intent_counts = {}
        for intent in self.context_history:
            key = intent.intent_type.value
            intent_counts[key] = intent_counts.get(key, 0) + 1

        return {
            "total_interactions": len(self.context_history),
            "intent_distribution": intent_counts,
            "last_intent": self.context_history[-1].intent_type.value,
            "common_entities": self._extract_common_entities(),
        }

    def _extract_common_entities(self) -> Dict[str, Any]:
        """Extract commonly mentioned entities."""
        entity_counts: Dict[str, Dict[str, int]] = {}

        for intent in self.context_history:
            for key, value in intent.entities.items():
                if key.startswith("_"):
                    continue
                if key not in entity_counts:
                    entity_counts[key] = {}
                value_str = str(value)
                entity_counts[key][value_str] = entity_counts[key].get(value_str, 0) + 1

        # Get most common for each entity type
        common = {}
        for entity_type, values in entity_counts.items():
            if values:
                most_common = max(values.items(), key=lambda x: x[1])
                common[entity_type] = most_common[0]

        return common
