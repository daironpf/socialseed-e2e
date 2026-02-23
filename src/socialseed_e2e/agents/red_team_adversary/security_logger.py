"""Security Logger for Red Team Operations.

Logs all adversarial activities and successful attacks to security/red-team-logs.json
for analysis and remediation.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.agents.red_team_adversary.models import (
    AttackAttempt,
    GuardrailInfo,
    VulnerabilityReport,
)


class SecurityLogger:
    """Logs security testing activities and findings."""

    def __init__(self, output_dir: str = "security"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_file = self.output_dir / "red-team-logs.json"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs: List[Dict[str, Any]] = []

        # Load existing logs if present
        self._load_existing_logs()

    def _load_existing_logs(self) -> None:
        """Load existing logs from file."""
        if self.logs_file.exists():
            try:
                with open(self.logs_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.logs = data
                    elif isinstance(data, dict) and "logs" in data:
                        self.logs = data["logs"]
            except (json.JSONDecodeError, IOError):
                self.logs = []

    def log_attack_attempt(
        self,
        attempt: AttackAttempt,
        session_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a single attack attempt."""
        log_entry = {
            "timestamp": attempt.timestamp.isoformat(),
            "session_id": self.session_id,
            "type": "attack_attempt",
            "attempt_id": attempt.attempt_id,
            "attack_type": attempt.attack_type.value,
            "payload": {
                "payload_id": attempt.payload.payload_id,
                "name": attempt.payload.name,
                "description": attempt.payload.description,
                "payload_text": attempt.payload.payload_text,
                "target_component": attempt.payload.target_component,
            },
            "target_component": attempt.target_component,
            "result": attempt.result.value,
            "severity": attempt.severity.value,
            "success_indicators": attempt.success_indicators,
            "failure_indicators": attempt.failure_indicators,
            "response_snippet": attempt.response_snippet,
            "mitigation_suggestion": attempt.mitigation_suggestion,
            "session_context": session_context or {},
        }

        self.logs.append(log_entry)
        self._save_logs()

    def log_successful_attack(
        self,
        attempt: AttackAttempt,
        exploitation_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a successful attack with exploitation details."""
        log_entry = {
            "timestamp": attempt.timestamp.isoformat(),
            "session_id": self.session_id,
            "type": "successful_exploit",
            "attempt_id": attempt.attempt_id,
            "attack_type": attempt.attack_type.value,
            "payload": {
                "payload_id": attempt.payload.payload_id,
                "name": attempt.payload.name,
                "description": attempt.payload.description,
                "payload_text": attempt.payload.payload_text,
                "target_component": attempt.payload.target_component,
            },
            "target_component": attempt.target_component,
            "severity": attempt.severity.value,
            "success_indicators": attempt.success_indicators,
            "exploitation_details": exploitation_details or {},
            "mitigation_suggestion": attempt.mitigation_suggestion,
            "is_winning_payload": True,
        }

        self.logs.append(log_entry)
        self._save_logs()

    def log_guardrail_discovery(
        self,
        guardrail: GuardrailInfo,
        bypass_attempted: bool = False,
        bypass_successful: bool = False,
    ) -> None:
        """Log discovered guardrail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "type": "guardrail_discovery",
            "guardrail_id": guardrail.guardrail_id,
            "guardrail_type": guardrail.guardrail_type.value,
            "description": guardrail.description,
            "location": guardrail.location,
            "strength": guardrail.strength,
            "bypass_attempted": bypass_attempted,
            "bypass_successful": bypass_successful,
        }

        self.logs.append(log_entry)
        self._save_logs()

    def log_vulnerability_report(
        self,
        report: VulnerabilityReport,
    ) -> str:
        """Log complete vulnerability report."""
        report_file = self.output_dir / f"vulnerability-report-{report.report_id}.json"

        # Convert report to dict
        report_data = report.model_dump()

        # Save detailed report
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)

        # Log summary
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "type": "vulnerability_report",
            "report_id": report.report_id,
            "target_system": report.target_system,
            "total_attacks": report.total_attacks,
            "successful_attacks": report.successful_attacks,
            "partial_attacks": report.partial_attacks,
            "failed_attacks": report.failed_attacks,
            "resilience_score": report.resilience_score.overall_score,
            "report_file": str(report_file),
        }

        self.logs.append(log_entry)
        self._save_logs()

        return str(report_file)

    def log_session_start(
        self,
        target_system: str,
        attack_types: List[str],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log the start of a red team session."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "type": "session_start",
            "target_system": target_system,
            "attack_types": attack_types,
            "config": config or {},
        }

        self.logs.append(log_entry)
        self._save_logs()

    def log_session_end(
        self,
        total_attempts: int,
        successful_attacks: int,
        final_score: int,
    ) -> None:
        """Log the end of a red team session."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "type": "session_end",
            "total_attempts": total_attempts,
            "successful_attacks": successful_attacks,
            "final_resilience_score": final_score,
        }

        self.logs.append(log_entry)
        self._save_logs()

    def _save_logs(self) -> None:
        """Save logs to file."""
        # Ensure directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Save with metadata
        output_data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "total_entries": len(self.logs),
                "current_session": self.session_id,
            },
            "logs": self.logs,
        }

        with open(self.logs_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)

    def get_winning_payloads(self) -> List[Dict[str, Any]]:
        """Get all successfully exploited payloads."""
        return [
            log
            for log in self.logs
            if log.get("type") == "successful_exploit"
            or log.get("is_winning_payload") is True
        ]

    def get_logs_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific session."""
        return [log for log in self.logs if log.get("session_id") == session_id]

    def get_logs_by_attack_type(self, attack_type: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific attack type."""
        return [
            log
            for log in self.logs
            if log.get("attack_type") == attack_type
            or (log.get("payload") and log["payload"].get("attack_type") == attack_type)
        ]

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all logged activities."""
        total_attacks = len([l for l in self.logs if l.get("type") == "attack_attempt"])
        successful_exploits = len(self.get_winning_payloads())
        guardrails_found = len(
            [l for l in self.logs if l.get("type") == "guardrail_discovery"]
        )

        # Group by attack type
        attack_types: Dict[str, int] = {}
        for log in self.logs:
            if log.get("type") == "attack_attempt":
                atype = log.get("attack_type", "unknown")
                attack_types[atype] = attack_types.get(atype, 0) + 1

        return {
            "total_entries": len(self.logs),
            "total_attacks": total_attacks,
            "successful_exploits": successful_exploits,
            "guardrails_discovered": guardrails_found,
            "attack_types_breakdown": attack_types,
            "sessions": len(
                {l.get("session_id") for l in self.logs if l.get("session_id")}
            ),
        }

    def clear_logs(self) -> None:
        """Clear all logs (use with caution)."""
        self.logs = []
        if self.logs_file.exists():
            self.logs_file.unlink()
