"""
Security reporting module.

Generates comprehensive security reports with findings, risk scores, and recommendations.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import (
    SecurityVulnerability,
    SecretFinding,
    ComplianceViolation,
    SecurityReport,
    SecurityScanResult,
    VulnerabilitySeverity,
    VulnerabilityCategory,
    SecretType,
    ComplianceStandard,
)


class SecurityReporter:
    """Generates security reports from scan results."""

    def __init__(self, project_name: str = "Untitled Project"):
        self.project_name = project_name
        self.scan_results = []
        self.vulnerabilities = []
        self.secrets = []
        self.compliance_violations = []

    def add_scan_result(self, result):
        self.scan_results.append(result)
        self.vulnerabilities.extend(result.vulnerabilities)
        self.secrets.extend(result.secrets)
        self.compliance_violations.extend(result.compliance_violations)

    def generate_report(self) -> SecurityReport:
        risk_score = self._calculate_risk_score()
        risk_level = self._get_risk_level(risk_score)
        recommendations = self._generate_recommendations()

        return SecurityReport(
            report_id=self._generate_report_id(),
            project_name=self.project_name,
            total_scans=len(self.scan_results),
            total_vulnerabilities=len(self.vulnerabilities),
            total_secrets=len(self.secrets),
            total_compliance_violations=len(self.compliance_violations),
            risk_score=risk_score,
            risk_level=risk_level,
            scan_results=self.scan_results,
            top_recommendations=recommendations,
        )

    def export_json(self, filepath: str) -> str:
        report = self.generate_report()
        with open(filepath, "w") as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
        return filepath

    def _calculate_risk_score(self) -> float:
        if not self.vulnerabilities and not self.secrets:
            return 0.0

        weights = {
            VulnerabilitySeverity.CRITICAL: 10,
            VulnerabilitySeverity.HIGH: 5,
            VulnerabilitySeverity.MEDIUM: 2,
            VulnerabilitySeverity.LOW: 0.5,
        }

        total_score = 0
        for vuln in self.vulnerabilities:
            total_score += weights.get(vuln.severity, 1)
        for secret in self.secrets:
            total_score += weights.get(secret.severity, 1) * 1.5
        for violation in self.compliance_violations:
            total_score += weights.get(violation.severity, 1) * 1.2

        return min(total_score, 100.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        return "minimal"

    def _generate_recommendations(self) -> List[str]:
        recommendations = []

        critical_count = sum(
            1
            for v in self.vulnerabilities
            if v.severity == VulnerabilitySeverity.CRITICAL
        )
        if critical_count > 0:
            recommendations.append(
                f"URGENT: Address {critical_count} critical vulnerabilities immediately"
            )

        if self.secrets:
            recommendations.append(
                f"Rotate {len(self.secrets)} exposed secrets immediately"
            )

        if not recommendations:
            recommendations.append("Continue regular security testing and monitoring")

        return recommendations[:5]

    def _generate_report_id(self) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"SEC_{timestamp}_{self.project_name.replace(' ', '_')[:20]}"
