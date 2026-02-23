"""Natural Language Translator for test code generation.

This module provides natural language parsing capabilities to understand
test descriptions in plain English, Spanish, and other languages.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from socialseed_e2e.nlp.models import (
    ActionType,
    AssertionType,
    EntityType,
    IntentType,
    Language,
    NaturalLanguageTest,
    ParsedAction,
    ParsedAssertion,
    ParsedEntity,
    TranslationContext,
)


class LanguagePatterns:
    """Language-specific patterns for different languages."""

    PATTERNS = {
        Language.ENGLISH: {
            "intents": {
                IntentType.VERIFY: [
                    r"verify",
                    r"check",
                    r"ensure",
                    r"validate",
                    r"confirm",
                ],
                IntentType.TEST: [
                    r"test",
                    r"validate",
                ],
                IntentType.ASSERT: [
                    r"assert",
                    r"should",
                    r"must",
                ],
            },
            "actions": {
                ActionType.LOGIN: [r"login", r"log in", r"sign in", r"authenticate"],
                ActionType.LOGOUT: [r"logout", r"log out", r"sign out"],
                ActionType.CREATE: [r"create", r"add", r"post", r"register"],
                ActionType.READ: [r"read", r"get", r"fetch", r"retrieve"],
                ActionType.UPDATE: [r"update", r"modify", r"edit", r"put", r"patch"],
                ActionType.DELETE: [r"delete", r"remove", r"destroy"],
                ActionType.SEND: [r"send", r"submit", r"post"],
                ActionType.RECEIVE: [r"receive", r"get back", r"return"],
                ActionType.SEARCH: [r"search", r"find", r"look for"],
                ActionType.FILTER: [r"filter", r"narrow"],
                ActionType.SORT: [r"sort", r"order"],
            },
            "entities": {
                EntityType.USER: [r"user", r"customer", r"client"],
                EntityType.ADMIN: [r"admin", r"administrator", r"moderator"],
                EntityType.ENDPOINT: [r"endpoint", r"url", r"route"],
                EntityType.API: [r"api", r"endpoint"],
                EntityType.TOKEN: [r"token", r"jwt", r"bearer token"],
                EntityType.CREDENTIALS: [r"credentials", r"username", r"password"],
                EntityType.REQUEST: [r"request", r"call"],
                EntityType.RESPONSE: [r"response", r"result"],
                EntityType.DATA: [r"data", r"payload", r"body"],
                EntityType.FIELD: [r"field", r"property", r"attribute"],
                EntityType.HEADER: [r"header", r"headers"],
                EntityType.PARAMETER: [r"parameter", r"param", r"argument"],
            },
            "assertions": {
                AssertionType.EQUALS: [r"equals", r"is equal to", r"should be"],
                AssertionType.CONTAINS: [r"contains", r"includes", r"has"],
                AssertionType.EXISTS: [r"exists", r"is present"],
                AssertionType.STATUS_CODE: [
                    r"status code",
                    r"http code",
                    r"response code",
                ],
                AssertionType.RESPONSE_TIME: [r"response time", r"takes less than"],
                AssertionType.FIELD_EXISTS: [r"field exists", r"has field"],
                AssertionType.FIELD_VALUE: [r"field value", r"field should be"],
                AssertionType.IS_EMPTY: [r"is empty", r"should be empty"],
                AssertionType.IS_NOT_EMPTY: [r"is not empty", r"should not be empty"],
            },
        },
        Language.SPANISH: {
            "intents": {
                IntentType.VERIFY: [
                    r"verificar",
                    r"comprobar",
                    r"asegurar",
                    r"validar",
                    r"confirmar",
                ],
                IntentType.TEST: [
                    r"probar",
                    r"testear",
                    r"validar",
                ],
                IntentType.ASSERT: [
                    r"asegurar",
                    r"debería",
                    r"debe",
                ],
            },
            "actions": {
                ActionType.LOGIN: [r"iniciar sesión", r"loguear", r"autenticar"],
                ActionType.LOGOUT: [r"cerrar sesión", r"desloguear"],
                ActionType.CREATE: [r"crear", r"agregar", r"añadir", r"registrar"],
                ActionType.READ: [r"leer", r"obtener", r"recuperar", r"consultar"],
                ActionType.UPDATE: [r"actualizar", r"modificar", r"editar"],
                ActionType.DELETE: [r"eliminar", r"borrar", r"remover"],
                ActionType.SEND: [r"enviar", r"mandar"],
                ActionType.RECEIVE: [r"recibir", r"obtener"],
                ActionType.SEARCH: [r"buscar", r"encontrar"],
                ActionType.FILTER: [r"filtrar"],
                ActionType.SORT: [r"ordenar", r"clasificar"],
            },
            "entities": {
                EntityType.USER: [r"usuario", r"cliente"],
                EntityType.ADMIN: [r"admin", r"administrador"],
                EntityType.ENDPOINT: [r"endpoint", r"url", r"ruta"],
                EntityType.API: [r"api", r"interfaz"],
                EntityType.TOKEN: [r"token", r"jwt"],
                EntityType.CREDENTIALS: [r"credenciales", r"usuario", r"contraseña"],
                EntityType.REQUEST: [r"petición", r"solicitud", r"llamada"],
                EntityType.RESPONSE: [r"respuesta", r"resultado"],
                EntityType.DATA: [r"datos", r"payload", r"cuerpo"],
                EntityType.FIELD: [r"campo", r"propiedad", r"atributo"],
                EntityType.HEADER: [r"cabecera", r"encabezado"],
                EntityType.PARAMETER: [r"parámetro", r"argumento"],
            },
            "assertions": {
                AssertionType.EQUALS: [r"igual a", r"sea igual", r"debería ser"],
                AssertionType.CONTAINS: [r"contiene", r"incluye", r"tiene"],
                AssertionType.EXISTS: [r"existe", r"está presente"],
                AssertionType.STATUS_CODE: [r"código de estado", r"código http"],
                AssertionType.RESPONSE_TIME: [
                    r"tiempo de respuesta",
                    r"tarde menos de",
                ],
                AssertionType.FIELD_EXISTS: [r"campo existe", r"tiene campo"],
                AssertionType.FIELD_VALUE: [r"valor del campo"],
                AssertionType.IS_EMPTY: [r"está vacío", r"sea vacío"],
                AssertionType.IS_NOT_EMPTY: [r"no está vacío", r"no sea vacío"],
            },
        },
    }

    @classmethod
    def get_patterns(cls, language: Language) -> Dict[str, Any]:
        """Get patterns for a specific language."""
        return cls.PATTERNS.get(language, cls.PATTERNS[Language.ENGLISH])


class NaturalLanguageParser:
    """Parse natural language test descriptions."""

    def __init__(self, language: Language = Language.ENGLISH):
        self.language = language
        self.patterns = LanguagePatterns.get_patterns(language)

    def parse(
        self, text: str, context: Optional[TranslationContext] = None
    ) -> NaturalLanguageTest:
        """Parse natural language text into structured test description.

        Args:
            text: Natural language description
            context: Optional translation context

        Returns:
            Parsed natural language test
        """
        context = context or TranslationContext()

        # Clean and normalize text
        cleaned_text = self._clean_text(text)

        # Extract intent
        intent = self._extract_intent(cleaned_text)

        # Extract entities
        entities = self._extract_entities(cleaned_text)

        # Extract actions
        actions = self._extract_actions(cleaned_text)

        # Extract assertions
        assertions = self._extract_assertions(cleaned_text)

        # Extract preconditions
        preconditions = self._extract_preconditions(cleaned_text)

        # Calculate confidence
        confidence = self._calculate_confidence(entities, actions, assertions)

        return NaturalLanguageTest(
            raw_text=text,
            language=self.language,
            intent=intent,
            description=cleaned_text,
            entities=entities,
            actions=actions,
            assertions=assertions,
            preconditions=preconditions,
            confidence_score=confidence,
        )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove common filler words based on language
        if self.language == Language.ENGLISH:
            filler_words = [
                "please",
                "kindly",
                "would you",
                "could you",
                "i want to",
                "we need to",
            ]
        elif self.language == Language.SPANISH:
            filler_words = [
                "por favor",
                "quisiera",
                "me gustaría",
                "necesito",
                "queremos",
            ]
        else:
            filler_words = []

        for filler in filler_words:
            text = re.sub(rf"\b{filler}\b", "", text, flags=re.IGNORECASE)

        return " ".join(text.split())

    def _extract_intent(self, text: str) -> IntentType:
        """Extract intent from text.

        Args:
            text: Cleaned text

        Returns:
            Detected intent
        """
        text_lower = text.lower()

        for intent, patterns in self.patterns["intents"].items():
            for pattern in patterns:
                if re.search(rf"\b{pattern}\b", text_lower):
                    return intent

        return IntentType.VERIFY

    def _extract_entities(self, text: str) -> List[ParsedEntity]:
        """Extract entities from text.

        Args:
            text: Cleaned text

        Returns:
            List of extracted entities
        """
        entities = []
        text_lower = text.lower()

        for entity_type, patterns in self.patterns["entities"].items():
            for pattern in patterns:
                matches = re.finditer(rf"\b({pattern})\b", text_lower)
                for match in matches:
                    # Try to find entity name/value after the entity type
                    name = self._extract_entity_name(text, match.end())

                    entity = ParsedEntity(
                        entity_type=entity_type,
                        name=name or match.group(1),
                        position=match.start(),
                        confidence=0.8,
                    )
                    entities.append(entity)

        # Sort by position
        entities.sort(key=lambda e: e.position)

        return entities

    def _extract_entity_name(self, text: str, start_pos: int) -> Optional[str]:
        """Extract entity name after position.

        Args:
            text: Full text
            start_pos: Position after entity type

        Returns:
            Entity name or None
        """
        # Look for patterns like "user named John" or "endpoint /api/users"
        remaining = text[start_pos:].strip()

        # Pattern: named/called X
        named_match = re.match(
            r"(?:named|called|with name|with username)\s+['\"]?([\w/\-@.]+)['\"]?",
            remaining,
            re.IGNORECASE,
        )
        if named_match:
            return named_match.group(1)

        # Pattern: with value X
        value_match = re.match(
            r"(?:with value|with|equals?|is)\s+['\"]?([\w/\-@.]+)['\"]?",
            remaining,
            re.IGNORECASE,
        )
        if value_match:
            return value_match.group(1)

        return None

    def _extract_actions(self, text: str) -> List[ParsedAction]:
        """Extract actions from text.

        Args:
            text: Cleaned text

        Returns:
            List of extracted actions
        """
        actions = []
        text_lower = text.lower()

        for action_type, patterns in self.patterns["actions"].items():
            for pattern in patterns:
                matches = re.finditer(rf"\b({pattern})\b", text_lower)
                for match in matches:
                    # Try to find target
                    target = self._extract_action_target(text, match.end())

                    # Extract parameters
                    parameters = self._extract_action_parameters(text, match.end())

                    action = ParsedAction(
                        action_type=action_type,
                        target=target,
                        parameters=parameters,
                        position=match.start(),
                        confidence=0.85,
                    )
                    actions.append(action)

        # Sort by position
        actions.sort(key=lambda a: a.position)

        return actions

    def _extract_action_target(self, text: str, start_pos: int) -> Optional[str]:
        """Extract action target after position.

        Args:
            text: Full text
            start_pos: Position after action

        Returns:
            Target or None
        """
        remaining = text[start_pos:].strip()

        # Look for "action [the] X" pattern
        target_match = re.match(
            r"(?:the|a|an)?\s+([\w\s/\-]+?)(?:\s+(?:with|to|from|in|on|at)\b|$)",
            remaining,
            re.IGNORECASE,
        )
        if target_match:
            return target_match.group(1).strip()

        return None

    def _extract_action_parameters(self, text: str, start_pos: int) -> Dict[str, Any]:
        """Extract action parameters.

        Args:
            text: Full text
            start_pos: Position after action

        Returns:
            Dictionary of parameters
        """
        parameters = {}
        remaining = text[start_pos:].strip()

        # Look for "with X = Y" or "with X: Y" patterns
        param_matches = re.finditer(
            r"with\s+(\w+)\s*(?:=|:)\s*['\"]?([\w/\-@.]+)['\"]?",
            remaining,
            re.IGNORECASE,
        )
        for match in param_matches:
            parameters[match.group(1)] = match.group(2)

        return parameters

    def _extract_assertions(self, text: str) -> List[ParsedAssertion]:
        """Extract assertions from text.

        Args:
            text: Cleaned text

        Returns:
            List of extracted assertions
        """
        assertions = []
        text_lower = text.lower()

        for assertion_type, patterns in self.patterns["assertions"].items():
            for pattern in patterns:
                matches = re.finditer(rf"\b({pattern})\b", text_lower)
                for match in matches:
                    # Extract field and expected value
                    field, expected_value = self._extract_assertion_details(
                        text, match.end()
                    )

                    assertion = ParsedAssertion(
                        assertion_type=assertion_type,
                        field=field,
                        expected_value=expected_value,
                        confidence=0.75,
                    )
                    assertions.append(assertion)

        return assertions

    def _extract_assertion_details(
        self, text: str, start_pos: int
    ) -> Tuple[Optional[str], Any]:
        """Extract assertion field and expected value.

        Args:
            text: Full text
            start_pos: Position after assertion pattern

        Returns:
            Tuple of (field, expected_value)
        """
        remaining = text[start_pos:].strip()

        # Look for "is/equals X" pattern
        value_match = re.match(
            r"(?:is|equals?|should be)?\s*['\"]?([\w/\-@.]+)['\"]?",
            remaining,
            re.IGNORECASE,
        )
        if value_match:
            value = value_match.group(1)
            # Try to convert to number if possible
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass
            return None, value

        return None, None

    def _extract_preconditions(self, text: str) -> List[str]:
        """Extract preconditions from text.

        Args:
            text: Cleaned text

        Returns:
            List of preconditions
        """
        preconditions = []
        text_lower = text.lower()

        # Look for "given/when X" patterns
        given_patterns = [
            r"given\s+(.*?)(?:when|then|$)",
            r"assuming\s+(.*?)(?:when|then|$)",
            r"if\s+(.*?)(?:then|$)",
        ]

        for pattern in given_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                preconditions.append(match.group(1).strip())

        return preconditions

    def _calculate_confidence(
        self,
        entities: List[ParsedEntity],
        actions: List[ParsedAction],
        assertions: List[ParsedAssertion],
    ) -> float:
        """Calculate overall parsing confidence.

        Args:
            entities: Extracted entities
            actions: Extracted actions
            assertions: Extracted assertions

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not entities and not actions and not assertions:
            return 0.0

        # Calculate based on what we found
        entity_conf = (
            sum(e.confidence for e in entities) / len(entities) if entities else 0
        )
        action_conf = (
            sum(a.confidence for a in actions) / len(actions) if actions else 0
        )
        assertion_conf = (
            sum(a.confidence for a in assertions) / len(assertions) if assertions else 0
        )

        # Weight factors
        weights = {"entities": 0.3, "actions": 0.4, "assertions": 0.3}

        confidence = (
            entity_conf * weights["entities"]
            + action_conf * weights["actions"]
            + assertion_conf * weights["assertions"]
        )

        return min(confidence, 1.0)


class MultiLanguageTranslator:
    """Translate natural language in multiple languages."""

    def __init__(self):
        self.parsers: Dict[Language, NaturalLanguageParser] = {}

    def detect_language(self, text: str) -> Language:
        """Detect language from text.

        Args:
            text: Natural language text

        Returns:
            Detected language
        """
        text_lower = text.lower()

        # Simple heuristic based on common words
        spanish_indicators = [
            "el",
            "la",
            "los",
            "las",
            "usuario",
            "iniciar",
            "sesión",
            "verificar",
            "cuando",
            "entonces",
        ]
        french_indicators = ["le", "la", "les", "utilisateur", "vérifier"]
        german_indicators = ["der", "die", "das", "benutzer", "überprüfen"]

        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
        french_count = sum(1 for word in french_indicators if word in text_lower)
        german_count = sum(1 for word in german_indicators if word in text_lower)

        counts = {
            Language.SPANISH: spanish_count,
            Language.FRENCH: french_count,
            Language.GERMAN: german_count,
        }

        best_match = max(counts, key=counts.get)

        if counts[best_match] > 0:
            return best_match

        return Language.ENGLISH

    def parse(
        self, text: str, language: Optional[Language] = None
    ) -> NaturalLanguageTest:
        """Parse text in specified or detected language.

        Args:
            text: Natural language text
            language: Optional specific language

        Returns:
            Parsed test description
        """
        if language is None:
            language = self.detect_language(text)

        if language not in self.parsers:
            self.parsers[language] = NaturalLanguageParser(language)

        return self.parsers[language].parse(text)


class TestDescriptionBuilder:
    """Build test descriptions from parsed components."""

    def __init__(self, parser: NaturalLanguageParser):
        self.parser = parser

    def from_description(
        self, description: str, context: Optional[TranslationContext] = None
    ) -> NaturalLanguageTest:
        """Build test from description.

        Args:
            description: Test description
            context: Optional context

        Returns:
            Parsed test
        """
        return self.parser.parse(description, context)

    def from_scenario(
        self,
        scenario: str,
        given: List[str],
        when: List[str],
        then: List[str],
        context: Optional[TranslationContext] = None,
    ) -> NaturalLanguageTest:
        """Build test from Gherkin-style scenario.

        Args:
            scenario: Scenario name
            given: Given steps
            when: When steps
            then: Then steps
            context: Optional context

        Returns:
            Parsed test
        """
        # Combine into description
        description_parts = [scenario]

        if given:
            description_parts.append("Given " + " and ".join(given))
        if when:
            description_parts.append("When " + " and ".join(when))
        if then:
            description_parts.append("Then " + " and ".join(then))

        description = ". ".join(description_parts)

        return self.parser.parse(description, context)
