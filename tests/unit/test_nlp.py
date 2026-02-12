"""Unit tests for Natural Language Processing module.

This module contains tests for the NLP-based test code generation system.
"""

import pytest
from datetime import datetime

from socialseed_e2e.nlp.models import (
    ActionType,
    AssertionType,
    EntityType,
    GeneratedCode,
    GherkinFeature,
    GherkinScenario,
    IntentType,
    Language,
    NaturalLanguageTest,
    ParsedAction,
    ParsedAssertion,
    ParsedEntity,
    TranslationContext,
    TranslationResult,
)
from socialseed_e2e.nlp.translator import (
    LanguagePatterns,
    MultiLanguageTranslator,
    NaturalLanguageParser,
)
from socialseed_e2e.nlp.gherkin_parser import GherkinParser, GherkinWriter


class TestNLPModels:
    """Tests for NLP models."""

    def test_language_enum(self):
        """Test Language enum values."""
        assert Language.ENGLISH.value == "en"
        assert Language.SPANISH.value == "es"
        assert Language.FRENCH.value == "fr"

    def test_intent_type_enum(self):
        """Test IntentType enum values."""
        assert IntentType.VERIFY.value == "verify"
        assert IntentType.TEST.value == "test"
        assert IntentType.ASSERT.value == "assert"

    def test_action_type_enum(self):
        """Test ActionType enum values."""
        assert ActionType.LOGIN.value == "login"
        assert ActionType.CREATE.value == "create"
        assert ActionType.READ.value == "read"
        assert ActionType.UPDATE.value == "update"
        assert ActionType.DELETE.value == "delete"

    def test_entity_type_enum(self):
        """Test EntityType enum values."""
        assert EntityType.USER.value == "user"
        assert EntityType.API.value == "api"
        assert EntityType.TOKEN.value == "token"

    def test_assertion_type_enum(self):
        """Test AssertionType enum values."""
        assert AssertionType.EQUALS.value == "equals"
        assert AssertionType.CONTAINS.value == "contains"
        assert AssertionType.STATUS_CODE.value == "status_code"

    def test_parsed_entity_creation(self):
        """Test ParsedEntity creation."""
        entity = ParsedEntity(
            entity_type=EntityType.USER,
            name="testuser",
            confidence=0.9,
        )
        assert entity.entity_type == EntityType.USER
        assert entity.name == "testuser"
        assert entity.confidence == 0.9

    def test_parsed_action_creation(self):
        """Test ParsedAction creation."""
        action = ParsedAction(
            action_type=ActionType.LOGIN,
            target="/api/login",
            confidence=0.85,
        )
        assert action.action_type == ActionType.LOGIN
        assert action.target == "/api/login"

    def test_parsed_assertion_creation(self):
        """Test ParsedAssertion creation."""
        assertion = ParsedAssertion(
            assertion_type=AssertionType.STATUS_CODE,
            expected_value=200,
            confidence=0.75,
        )
        assert assertion.assertion_type == AssertionType.STATUS_CODE
        assert assertion.expected_value == 200

    def test_translation_context_creation(self):
        """Test TranslationContext creation."""
        context = TranslationContext(
            language=Language.ENGLISH,
            service="users-api",
            endpoint="/api/login",
        )
        assert context.language == Language.ENGLISH
        assert context.service == "users-api"
        assert context.endpoint == "/api/login"

    def test_natural_language_test_creation(self):
        """Test NaturalLanguageTest creation."""
        test = NaturalLanguageTest(
            raw_text="Verify user can login",
            language=Language.ENGLISH,
            intent=IntentType.VERIFY,
        )
        assert test.raw_text == "Verify user can login"
        assert test.language == Language.ENGLISH
        assert test.intent == IntentType.VERIFY

    def test_generated_code_creation(self):
        """Test GeneratedCode creation."""
        code = GeneratedCode(
            test_name="test_login",
            module_name="test_login.py",
            code="def test_login(): pass",
            confidence=0.8,
        )
        assert code.test_name == "test_login"
        assert code.confidence == 0.8


class TestNaturalLanguageParser:
    """Tests for NaturalLanguageParser."""

    def test_parse_simple_login(self):
        """Test parsing simple login description."""
        parser = NaturalLanguageParser(Language.ENGLISH)
        result = parser.parse("Verify that a user can login with valid credentials")

        assert result.intent == IntentType.VERIFY
        assert len(result.actions) > 0
        assert any(a.action_type == ActionType.LOGIN for a in result.actions)

    def test_parse_create_action(self):
        """Test parsing create action."""
        parser = NaturalLanguageParser(Language.ENGLISH)
        result = parser.parse("Create a new user with name John")

        assert len(result.actions) > 0
        assert any(a.action_type == ActionType.CREATE for a in result.actions)
        assert len(result.entities) > 0

    def test_parse_with_assertions(self):
        """Test parsing with assertions."""
        parser = NaturalLanguageParser(Language.ENGLISH)
        result = parser.parse("Verify the response status code is 200")

        assert len(result.assertions) > 0
        assert any(
            a.assertion_type == AssertionType.STATUS_CODE for a in result.assertions
        )

    def test_parse_spanish(self):
        """Test parsing Spanish text."""
        parser = NaturalLanguageParser(Language.SPANISH)
        result = parser.parse("Verificar que el usuario puede iniciar sesión")

        assert result.intent == IntentType.VERIFY
        assert len(result.actions) > 0

    def test_extract_entities(self):
        """Test entity extraction."""
        parser = NaturalLanguageParser(Language.ENGLISH)
        entities = parser._extract_entities("When a user named John logs in")

        assert len(entities) > 0
        assert any(e.entity_type == EntityType.USER for e in entities)

    def test_clean_text(self):
        """Test text cleaning."""
        parser = NaturalLanguageParser(Language.ENGLISH)
        cleaned = parser._clean_text("Please verify that the user can login")

        assert "please" not in cleaned.lower()


class TestMultiLanguageTranslator:
    """Tests for MultiLanguageTranslator."""

    def test_detect_language_english(self):
        """Test English language detection."""
        translator = MultiLanguageTranslator()
        detected = translator.detect_language("Verify user can login")

        assert detected == Language.ENGLISH

    def test_detect_language_spanish(self):
        """Test Spanish language detection."""
        translator = MultiLanguageTranslator()
        detected = translator.detect_language(
            "Verificar que el usuario puede iniciar sesión"
        )

        assert detected == Language.SPANISH

    def test_parse_with_auto_detection(self):
        """Test parsing with automatic language detection."""
        translator = MultiLanguageTranslator()
        result = translator.parse("Verify user can login")

        assert result.language == Language.ENGLISH


class TestGherkinParser:
    """Tests for GherkinParser."""

    def test_parse_simple_feature(self):
        """Test parsing simple feature."""
        feature_text = """
Feature: User Login
  As a user
  I want to login
  So that I can access my account

  Scenario: Successful login
    Given a user with valid credentials
    When the user logs in
    Then the user receives a token
"""
        parser = GherkinParser(Language.ENGLISH)
        feature = parser.parse(feature_text)

        assert feature.name == "User Login"
        assert len(feature.scenarios) == 1

    def test_parse_scenario_with_all_steps(self):
        """Test parsing scenario with all step types."""
        feature_text = """
Feature: Test Feature
  Scenario: Test Scenario
    Given a precondition
    When an action is performed
    Then an expectation is met
    And another expectation
"""
        parser = GherkinParser(Language.ENGLISH)
        feature = parser.parse(feature_text)

        assert len(feature.scenarios) == 1
        scenario = feature.scenarios[0]
        assert len(scenario.given_steps) == 1
        assert len(scenario.when_steps) == 1
        assert len(scenario.then_steps) >= 1

    def test_parse_background(self):
        """Test parsing feature with background."""
        feature_text = """
Feature: Test Feature
  Background:
    Given the system is initialized

  Scenario: Test Scenario
    When something happens
    Then something is expected
"""
        parser = GherkinParser(Language.ENGLISH)
        feature = parser.parse(feature_text)

        assert feature.background is not None

    def test_parse_tags(self):
        """Test parsing feature with tags."""
        feature_text = """
@smoke @critical
Feature: Critical Feature
  @positive
  Scenario: Positive test
    Given something
    When action
    Then result
"""
        parser = GherkinParser(Language.ENGLISH)
        feature = parser.parse(feature_text)

        assert len(feature.tags) == 2
        assert "smoke" in feature.tags
        assert "critical" in feature.tags

    def test_parse_spanish_gherkin(self):
        """Test parsing Spanish Gherkin."""
        feature_text = """
Característica: Inicio de Sesión
  Escenario: Inicio exitoso
    Dado un usuario válido
    Cuando inicia sesión
    Entonces recibe un token
"""
        parser = GherkinParser(Language.SPANISH)
        feature = parser.parse(feature_text)

        assert feature.name == "Inicio de Sesión"
        assert len(feature.scenarios) == 1


class TestGherkinWriter:
    """Tests for GherkinWriter."""

    def test_write_simple_feature(self):
        """Test writing simple feature."""
        feature = GherkinFeature(
            name="Test Feature",
            description="A test feature",
            scenarios=[
                GherkinScenario(
                    name="Test Scenario",
                    given_steps=["a precondition"],
                    when_steps=["an action"],
                    then_steps=["an expectation"],
                )
            ],
        )

        writer = GherkinWriter(Language.ENGLISH)
        text = writer.write(feature)

        assert "Feature: Test Feature" in text
        assert "Scenario: Test Scenario" in text
        assert "Given a precondition" in text

    def test_write_with_tags(self):
        """Test writing feature with tags."""
        feature = GherkinFeature(
            name="Tagged Feature",
            tags=["smoke", "critical"],
            scenarios=[
                GherkinScenario(
                    name="Test Scenario",
                    tags=["positive"],
                    given_steps=["step"],
                    when_steps=["action"],
                    then_steps=["result"],
                )
            ],
        )

        writer = GherkinWriter(Language.ENGLISH)
        text = writer.write(feature)

        assert "@smoke @critical" in text
        assert "@positive" in text


class TestLanguagePatterns:
    """Tests for LanguagePatterns."""

    def test_get_english_patterns(self):
        """Test getting English patterns."""
        patterns = LanguagePatterns.get_patterns(Language.ENGLISH)

        assert "intents" in patterns
        assert "actions" in patterns
        assert "entities" in patterns
        assert "assertions" in patterns

    def test_get_spanish_patterns(self):
        """Test getting Spanish patterns."""
        patterns = LanguagePatterns.get_patterns(Language.SPANISH)

        assert "intents" in patterns
        assert len(patterns["actions"]) > 0

    def test_english_login_patterns(self):
        """Test English login action patterns."""
        patterns = LanguagePatterns.get_patterns(Language.ENGLISH)
        login_patterns = patterns["actions"][ActionType.LOGIN]

        assert "login" in login_patterns
        assert "log in" in login_patterns


@pytest.mark.unit
class TestTranslationIntegration:
    """Integration tests for NLP translation."""

    def test_end_to_end_translation(self):
        """Test complete translation flow."""
        # Parse
        parser = NaturalLanguageParser(Language.ENGLISH)
        parsed = parser.parse("Verify user can login and receives a token")

        # Verify parsed content
        assert parsed.intent == IntentType.VERIFY
        assert len(parsed.actions) > 0
        assert any(a.action_type == ActionType.LOGIN for a in parsed.actions)

    def test_complex_scenario(self):
        """Test complex scenario parsing."""
        description = """Verify that when a registered user logs in with valid credentials,
        they receive a JWT token with 24 hour expiration"""

        parser = NaturalLanguageParser(Language.ENGLISH)
        result = parser.parse(description)

        assert result.intent == IntentType.VERIFY
        assert len(result.actions) > 0
        assert len(result.entities) >= 3  # user, credentials, token

    def test_multiple_actions(self):
        """Test parsing multiple actions."""
        description = "Create a user, then login and verify the token"

        parser = NaturalLanguageParser(Language.ENGLISH)
        result = parser.parse(description)

        assert len(result.actions) >= 2
        action_types = [a.action_type for a in result.actions]
        assert ActionType.CREATE in action_types or ActionType.LOGIN in action_types
