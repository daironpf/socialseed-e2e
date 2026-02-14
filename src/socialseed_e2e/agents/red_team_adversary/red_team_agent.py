"""Red Team Adversarial Agent.

Main orchestrator for adversarial AI security testing.
Coordinates guardrail discovery, attack execution, and resilience scoring.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.agents.red_team_adversary.adversarial_prober import (
    AdversarialPayloads,
    AdversarialProber,
)
from socialseed_e2e.agents.red_team_adversary.guardrail_discovery import (
    GuardrailDiscovery,
)
from socialseed_e2e.agents.red_team_adversary.models import (
    AttackAttempt,
    AttackType,
    GuardrailInfo,
    RedTeamConfig,
    ResilienceScore,
    VulnerabilityReport,
)
from socialseed_e2e.agents.red_team_adversary.resilience_scorer import ResilienceScorer
from socialseed_e2e.agents.red_team_adversary.security_logger import SecurityLogger


class RedTeamAgent:
    """Main Red Team agent for adversarial security testing."""

    def __init__(
        self,
        project_root: Path,
        config: Optional[RedTeamConfig] = None,
    ):
        self.project_root = Path(project_root)
        self.config = config or RedTeamConfig(target_system=str(project_root))

        # Initialize components
        self.guardrail_discovery = GuardrailDiscovery(project_root)
        self.adversarial_prober = AdversarialProber()
        self.resilience_scorer = ResilienceScorer()
        self.security_logger = SecurityLogger(self.config.output_dir)

        # State
        self.discovered_guardrails: List[GuardrailInfo] = []
        self.attack_attempts: List[AttackAttempt] = []
        self.resilience_score: Optional[ResilienceScore] = None

    def run_full_assessment(
        self,
        attack_types: Optional[List[AttackType]] = None,
    ) -> VulnerabilityReport:
        """Run complete security assessment."""
        report_id = str(uuid.uuid4())[:8]

        # Log session start
        self.security_logger.log_session_start(
            target_system=self.config.target_system,
            attack_types=[
                at.value for at in (attack_types or self.config.attack_types)
            ],
            config=self.config.model_dump(),
        )

        # Step 1: Discover guardrails
        print("🔍 Discovering guardrails...")
        self._discover_guardrails()

        # Step 2: Execute adversarial attacks
        print("⚔️  Executing adversarial attacks...")
        self._execute_attacks(attack_types)

        # Step 3: Calculate resilience score
        print("📊 Calculating resilience score...")
        self._calculate_resilience()

        # Step 4: Generate report
        print("📝 Generating vulnerability report...")
        report = self._generate_report(report_id)

        # Log session end
        self.security_logger.log_session_end(
            total_attempts=len(self.attack_attempts),
            successful_attacks=len(
                [a for a in self.attack_attempts if a.result.value == "success"]
            ),
            final_score=self.resilience_score.overall_score
            if self.resilience_score
            else 0,
        )

        return report

    def _discover_guardrails(self) -> None:
        """Discover and log all guardrails."""
        self.discovered_guardrails = self.guardrail_discovery.discover_all()

        # Log discovered guardrails
        for guardrail in self.discovered_guardrails:
            self.security_logger.log_guardrail_discovery(guardrail)

        print(f"   ✓ Discovered {len(self.discovered_guardrails)} guardrails")

    def _execute_attacks(
        self,
        attack_types: Optional[List[AttackType]] = None,
    ) -> None:
        """Execute adversarial attacks."""
        if attack_types is None:
            attack_types = self.config.attack_types

        # Run attack campaign
        attempts = self.adversarial_prober.run_attack_campaign(
            attack_types=attack_types,
            max_attempts=self.config.max_iterations,
        )

        self.attack_attempts = attempts

        # Log all attempts
        for attempt in attempts:
            self.security_logger.log_attack_attempt(attempt)

            # Log successful exploits separately
            if attempt.result.value == "success":
                self.security_logger.log_successful_attack(attempt)

        successful = len([a for a in attempts if a.result.value == "success"])
        print(f"   ✓ Executed {len(attempts)} attacks ({successful} successful)")

    def _calculate_resilience(self) -> None:
        """Calculate overall resilience score."""
        self.resilience_score = self.resilience_scorer.calculate_score(
            attempts=self.attack_attempts,
            guardrails=self.discovered_guardrails,
        )

        print(f"   ✓ Resilience Score: {self.resilience_score.overall_score}/100")

    def _generate_report(self, report_id: str) -> VulnerabilityReport:
        """Generate complete vulnerability report."""
        successful = len(
            [a for a in self.attack_attempts if a.result.value == "success"]
        )
        partial = len([a for a in self.attack_attempts if a.result.value == "partial"])
        failed = len([a for a in self.attack_attempts if a.result.value == "failure"])

        report = VulnerabilityReport(
            report_id=report_id,
            generated_at=datetime.now(),
            target_system=self.config.target_system,
            total_attacks=len(self.attack_attempts),
            successful_attacks=successful,
            partial_attacks=partial,
            failed_attacks=failed,
            resilience_score=self.resilience_score,
            discovered_guardrails=self.discovered_guardrails,
            vulnerabilities=self.attack_attempts,
        )

        # Log report
        report_file = self.security_logger.log_vulnerability_report(report)
        print(f"   ✓ Report saved: {report_file}")

        return report

    def quick_scan(self) -> Dict[str, Any]:
        """Run quick security scan."""
        print("🚀 Running quick security scan...")

        # Discover guardrails
        guardrails = self.guardrail_discovery.discover_all()

        # Run limited attacks
        attempts = self.adversarial_prober.run_attack_campaign(
            max_attempts=10,
        )

        # Calculate score
        score = self.resilience_scorer.calculate_score(
            attempts=attempts,
            guardrails=guardrails,
        )

        return {
            "guardrails_found": len(guardrails),
            "attacks_executed": len(attempts),
            "successful_attacks": len(
                [a for a in attempts if a.result.value == "success"]
            ),
            "resilience_score": score.overall_score,
            "summary": score.summary,
        }

    def get_winning_payloads(self) -> List[Dict[str, Any]]:
        """Get all successfully exploited payloads."""
        return self.security_logger.get_winning_payloads()

    def test_specific_attack(
        self,
        attack_type: AttackType,
        payload_id: Optional[str] = None,
    ) -> AttackAttempt:
        """Test a specific attack type or payload."""
        # Get payloads for attack type
        payloads = AdversarialPayloads.get_payloads_by_type(attack_type)

        if not payloads:
            raise ValueError(f"No payloads found for attack type: {attack_type}")

        # Select payload
        if payload_id:
            payload = next((p for p in payloads if p.payload_id == payload_id), None)
            if not payload:
                raise ValueError(f"Payload not found: {payload_id}")
        else:
            payload = payloads[0]

        # Execute attack
        attempt = self.adversarial_prober.probe_with_payload(payload)

        # Log
        self.security_logger.log_attack_attempt(attempt)
        if attempt.result.value == "success":
            self.security_logger.log_successful_attack(attempt)

        return attempt

    def generate_mitigation_guide(self) -> str:
        """Generate mitigation guide based on findings."""
        if not self.resilience_score:
            return "Run full assessment first."

        lines = [
            "# Security Mitigation Guide\n",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Resilience Score:** {self.resilience_score.overall_score}/100\n",
            "## Executive Summary\n",
            self.resilience_score.summary,
            "\n## Recommendations\n",
        ]

        for i, rec in enumerate(self.resilience_score.recommendations, 1):
            lines.append(f"{i}. {rec}")

        lines.extend(
            [
                "\n## Component Scores\n",
                "| Component | Score |",
                "|-----------|-------|",
            ]
        )

        for component, score in self.resilience_score.component_scores.items():
            lines.append(f"| {component} | {score}/100 |")

        lines.extend(
            [
                "\n## Attack Type Resilience\n",
                "| Attack Type | Score |",
                "|-------------|-------|",
            ]
        )

        for attack_type, score in self.resilience_score.attack_type_scores.items():
            lines.append(f"| {attack_type.value} | {score}/100 |")

        return "\n".join(lines)
