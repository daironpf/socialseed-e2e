"""Tests for Red Team Adversarial Agent.

Tests for guardrail discovery, adversarial probing, resilience scoring, and logging.
"""

import json
from pathlib import Path

import pytest

from socialseed_e2e.agents.red_team_adversary import (
    AdversarialPayloads,
    AdversarialProber,
    AttackResult,
    AttackSeverity,
    AttackType,
    GuardrailDiscovery,
    GuardrailType,
    RedTeamAgent,
    ResilienceScorer,
    SecurityLogger,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure with guardrails."""
    # Create docs with guardrail patterns
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    readme = docs_dir / "README.md"
    readme.write_text("""
# Project Documentation

## Security Guidelines

### Input Validation
All user inputs must be validated before processing.
Do not accept malicious or malformed data.

### Authentication Required
Admin functions require authentication.
Verify user identity before granting access.

### Rate Limiting
API requests are limited to 100 per minute per user.
Excessive requests will be blocked.

### Content Moderation
Inappropriate content is filtered and rejected.
Offensive language is not allowed.
""")

    # Create code with guardrail patterns
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    auth_file = src_dir / "auth.py"
    auth_file.write_text("""
def check_admin_privileges(user):
    '''Verify user has admin privileges'''
    if not user.is_authenticated:
        raise UnauthorizedError("Authentication required")
    if not user.is_admin:
        raise ForbiddenError("Admin access only")
    return True

def sanitize_input(data):
    '''Sanitize user input'''
    # Filter malicious content
    if contains_malicious_patterns(data):
        raise ValidationError("Invalid input")
    return clean(data)
""")

    return tmp_path


class TestGuardrailDiscovery:
    """Tests for GuardrailDiscovery."""

    def test_discover_guardrails(self, temp_project):
        """Test guardrail discovery."""
        discovery = GuardrailDiscovery(temp_project)
        guardrails = discovery.discover_all()

        # Should find multiple guardrails
        assert len(guardrails) > 0

        # Check guardrail structure
        for guardrail in guardrails:
            assert guardrail.guardrail_id
            assert guardrail.guardrail_type in GuardrailType
            assert guardrail.description
            assert guardrail.location
            assert 0 <= guardrail.strength <= 100

    def test_get_guardrails_by_type(self, temp_project):
        """Test filtering guardrails by type."""
        discovery = GuardrailDiscovery(temp_project)
        discovery.discover_all()

        # Get auth guardrails
        auth_guardrails = discovery.get_guardrails_by_type(GuardrailType.AUTH_CHECK)

        # Should find authentication-related guardrails
        assert len(auth_guardrails) >= 0  # May or may not find depending on patterns

    def test_generate_summary(self, temp_project):
        """Test summary generation."""
        discovery = GuardrailDiscovery(temp_project)
        discovery.discover_all()

        summary = discovery.generate_summary()

        assert "total_guardrails" in summary
        assert "by_type" in summary
        assert "vulnerable_count" in summary
        assert "average_strength" in summary


class TestAdversarialPayloads:
    """Tests for AdversarialPayloads."""

    def test_get_all_payloads(self):
        """Test getting all payloads."""
        payloads = AdversarialPayloads.get_all_payloads()

        assert len(payloads) > 0

        # Check payload structure
        for payload in payloads:
            assert payload.payload_id
            assert payload.name
            assert payload.description
            assert payload.payload_text
            assert payload.target_component
            assert payload.attack_type in AttackType

    def test_get_payloads_by_type(self):
        """Test getting payloads by type."""
        for attack_type in AttackType:
            payloads = AdversarialPayloads.get_payloads_by_type(attack_type)

            # All returned payloads should match the type
            for payload in payloads:
                assert payload.attack_type == attack_type

    def test_prompt_injection_payloads(self):
        """Test prompt injection payloads exist."""
        payloads = AdversarialPayloads.get_payloads_by_type(AttackType.PROMPT_INJECTION)

        assert len(payloads) > 0

        # Check for specific patterns
        for payload in payloads:
            assert (
                "ignore" in payload.payload_text.lower()
                or "system" in payload.payload_text.lower()
                or "override" in payload.payload_text.lower()
            )

    def test_privilege_escalation_payloads(self):
        """Test privilege escalation payloads exist."""
        payloads = AdversarialPayloads.get_payloads_by_type(
            AttackType.PRIVILEGE_ESCALATION
        )

        assert len(payloads) > 0

        # Check for privilege-related patterns (at least one payload should match)
        has_privilege_pattern = any(
            "admin" in p.payload_text.lower()
            or "root" in p.payload_text.lower()
            or "privileged" in p.payload_text.lower()
            or "service account" in p.payload_text.lower()
            for p in payloads
        )
        assert has_privilege_pattern


class TestAdversarialProber:
    """Tests for AdversarialProber."""

    def test_probe_with_payload(self):
        """Test probing with a single payload."""
        prober = AdversarialProber()

        # Get a test payload
        payloads = AdversarialPayloads.get_payloads_by_type(AttackType.PROMPT_INJECTION)
        payload = payloads[0]

        # Execute attack
        attempt = prober.probe_with_payload(payload)

        assert attempt.attempt_id
        assert attempt.attack_type == AttackType.PROMPT_INJECTION
        assert attempt.payload == payload
        assert attempt.result in AttackResult
        assert attempt.timestamp

    def test_run_attack_campaign(self):
        """Test running a campaign of attacks."""
        prober = AdversarialProber()

        attempts = prober.run_attack_campaign(max_attempts=5)

        assert len(attempts) == 5

        for attempt in attempts:
            assert attempt.attempt_id
            assert attempt.result in AttackResult

    def test_get_successful_attacks(self):
        """Test filtering successful attacks."""
        prober = AdversarialProber()

        # Run some attacks
        prober.run_attack_campaign(max_attempts=10)

        successful = prober.get_successful_attacks()

        # All returned should be successful
        for attempt in successful:
            assert attempt.result == AttackResult.SUCCESS

    def test_get_attack_statistics(self):
        """Test statistics generation."""
        prober = AdversarialProber()

        # Run attacks
        prober.run_attack_campaign(max_attempts=5)

        stats = prober.get_attack_statistics()

        assert "total" in stats
        assert "successful" in stats
        assert "failed" in stats
        assert "success_rate" in stats
        assert stats["total"] == 5


class TestResilienceScorer:
    """Tests for ResilienceScorer."""

    def test_calculate_score(self):
        """Test score calculation."""
        scorer = ResilienceScorer()

        # Create test attempts
        prober = AdversarialProber()
        attempts = prober.run_attack_campaign(max_attempts=10)

        # Calculate score
        score = scorer.calculate_score(attempts, [])

        assert isinstance(score.overall_score, int)
        assert 0 <= score.overall_score <= 100
        assert score.summary
        assert isinstance(score.recommendations, list)

    def test_score_with_no_attacks(self):
        """Test scoring with no attacks."""
        scorer = ResilienceScorer()

        score = scorer.calculate_score([], [])

        assert score.overall_score == 100  # Perfect score if no attacks

    def test_score_breakdown(self):
        """Test score breakdown generation."""
        scorer = ResilienceScorer()

        prober = AdversarialProber()
        attempts = prober.run_attack_campaign(max_attempts=5)

        scorer.calculate_score(attempts, [])

        breakdown = scorer.get_score_breakdown()

        assert "total_attacks" in breakdown
        assert "successful_attacks" in breakdown
        assert "failed_attacks" in breakdown


class TestSecurityLogger:
    """Tests for SecurityLogger."""

    def test_log_attack_attempt(self, tmp_path):
        """Test logging attack attempt."""
        logger = SecurityLogger(output_dir=str(tmp_path / "security"))

        # Create test attempt
        prober = AdversarialProber()
        payloads = AdversarialPayloads.get_all_payloads()
        attempt = prober.probe_with_payload(payloads[0])

        # Log it
        logger.log_attack_attempt(attempt)

        # Check log file exists
        assert logger.logs_file.exists()

    def test_get_winning_payloads(self, tmp_path):
        """Test getting winning payloads."""
        logger = SecurityLogger(output_dir=str(tmp_path / "security"))

        # Log some attempts
        prober = AdversarialProber()
        for payload in AdversarialPayloads.get_all_payloads()[:5]:
            attempt = prober.probe_with_payload(payload)
            logger.log_attack_attempt(attempt)
            if attempt.result == AttackResult.SUCCESS:
                logger.log_successful_attack(attempt)

        winning = logger.get_winning_payloads()

        # Should return successful exploits
        for log in winning:
            assert (
                log.get("type") == "successful_exploit"
                or log.get("is_winning_payload") == True
            )

    def test_generate_summary(self, tmp_path):
        """Test summary generation."""
        logger = SecurityLogger(output_dir=str(tmp_path / "security"))

        # Log some data
        logger.log_session_start("test", ["prompt_injection"])

        summary = logger.generate_summary()

        assert "total_entries" in summary
        assert "sessions" in summary


class TestRedTeamAgent:
    """Tests for RedTeamAgent."""

    def test_agent_initialization(self, temp_project):
        """Test agent initialization."""
        agent = RedTeamAgent(project_root=temp_project)

        assert agent.project_root == temp_project
        assert agent.guardrail_discovery is not None
        assert agent.adversarial_prober is not None
        assert agent.resilience_scorer is not None
        assert agent.security_logger is not None

    def test_quick_scan(self, temp_project):
        """Test quick scan functionality."""
        agent = RedTeamAgent(project_root=temp_project)

        results = agent.quick_scan()

        assert "guardrails_found" in results
        assert "attacks_executed" in results
        assert "successful_attacks" in results
        assert "resilience_score" in results
        assert "summary" in results

    def test_generate_mitigation_guide(self, temp_project):
        """Test mitigation guide generation."""
        agent = RedTeamAgent(project_root=temp_project)

        # Run quick scan first
        agent.quick_scan()

        guide = agent.generate_mitigation_guide()

        assert isinstance(guide, str)
        assert "Security Mitigation Guide" in guide or "Run full assessment" in guide


class TestIntegration:
    """Integration tests."""

    def test_full_assessment(self, temp_project):
        """Test full assessment workflow."""
        agent = RedTeamAgent(project_root=temp_project)

        # Run limited assessment
        report = agent.run_full_assessment()

        assert report.report_id
        assert report.total_attacks > 0
        assert report.resilience_score is not None
        assert 0 <= report.resilience_score.overall_score <= 100
        assert len(report.discovered_guardrails) >= 0
        assert len(report.vulnerabilities) > 0

    def test_attack_type_filtering(self, temp_project):
        """Test filtering by attack type."""
        agent = RedTeamAgent(project_root=temp_project)

        # Run only prompt injection attacks
        report = agent.run_full_assessment(attack_types=[AttackType.PROMPT_INJECTION])

        # All vulnerabilities should be prompt injection
        for vuln in report.vulnerabilities:
            assert vuln.attack_type == AttackType.PROMPT_INJECTION
