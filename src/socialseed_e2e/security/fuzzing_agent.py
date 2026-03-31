"""
Zero-Day Vulnerability Predictive Fuzzing - EPIC-020
RAG-powered security testing agent for predictive fuzzing.
"""

import json
import random
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx


class VulnerabilityType(str, Enum):
    """Types of vulnerabilities to test."""
    BOLA = "bola"
    IDOR = "idor"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    JWT_MANIPULATION = "jwt_manipulation"
    PARAMETER_POLLUTION = "parameter_pollution"
    SSRF = "ssrf"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"


class Severity(str, Enum):
    """Vulnerability severity."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CVEEntry:
    """CVE entry for RAG."""
    cve_id: str
    description: str
    severity: Severity
    affected_components: List[str] = field(default_factory=list)
    published_date: Optional[datetime] = None


@dataclass
class FuzzPayload:
    """A fuzzing payload."""
    id: str
    vulnerability_type: VulnerabilityType
    payload: str
    description: str
    expected_impact: str


@dataclass
class VulnerabilityFinding:
    """A discovered vulnerability."""
    id: str
    vulnerability_type: VulnerabilityType
    endpoint: str
    severity: Severity
    description: str
    evidence: Dict[str, Any]
    discovered_at: datetime = field(default_factory=datetime.now)
    cve_references: List[str] = field(default_factory=list)


class CVEFeedConnector:
    """Connects to CVE feeds for RAG."""
    
    def __init__(self):
        self._cves: Dict[str, CVEEntry] = {}
        self._lock = threading.Lock()
    
    async def fetch_cves(
        self,
        year: Optional[int] = None,
        severity_filter: Optional[Severity] = None,
    ) -> List[CVEEntry]:
        """Fetch CVEs from NVD API."""
        if year is None:
            year = datetime.now().year
        
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0"
        
        params = {
            "pubStartDate": f"{year}-01-01T00:00:00.000Z",
            "pubEndDate": f"{year}-12-31T23:59:59.000Z",
            "resultsPerPage": 50,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("vulnerabilities", []):
                        cve = item.get("cve", {})
                        cve_id = cve.get("id", "")
                        
                        metrics = cve.get("metrics", {})
                        cvss = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
                        
                        base_score = cvss.get("baseScore", 0)
                        sev = Severity.CRITICAL if base_score >= 9 else Severity.HIGH if base_score >= 7 else Severity.MEDIUM if base_score >= 4 else Severity.LOW
                        
                        desc = cve.get("descriptions", [{}])[0].get("value", "")
                        
                        entry = CVEEntry(
                            cve_id=cve_id,
                            description=desc[:500],
                            severity=sev,
                            published_date=datetime.now(),
                        )
                        
                        with self._lock:
                            self._cves[cve_id] = entry
                            
        except Exception as e:
            print(f"Failed to fetch CVEs: {e}")
        
        cves = list(self._cves.values())
        
        if severity_filter:
            cves = [c for c in cves if c.severity == severity_filter]
        
        return cves
    
    def search_cves(self, query: str) -> List[CVEEntry]:
        """Search CVEs by keyword."""
        query_lower = query.lower()
        return [
            c for c in self._cves.values()
            if query_lower in c.description.lower()
        ][:10]
    
    def get_cve(self, cve_id: str) -> Optional[CVEEntry]:
        """Get a specific CVE."""
        return self._cves.get(cve_id)


class PayloadGenerator:
    """Generates fuzzing payloads for various vulnerability types."""
    
    def __init__(self):
        self._payloads: Dict[VulnerabilityType, List[FuzzPayload]] = {
            vt: [] for vt in VulnerabilityType
        }
        self._init_default_payloads()
    
    def _init_default_payloads(self) -> None:
        """Initialize default payloads."""
        self._payloads[VulnerabilityType.IDOR] = [
            FuzzPayload("idor-1", VulnerabilityType.IDOR, "?user_id=1", "Test access to user 1", "Unauthorized access"),
            FuzzPayload("idor-2", VulnerabilityType.IDOR, "?user_id=999999", "Test non-existent user", "Information disclosure"),
            FuzzPayload("idor-3", VulnerabilityType.IDOR, "../admin", "Path traversal attempt", "Admin access"),
        ]
        
        self._payloads[VulnerabilityType.JWT_MANIPULATION] = [
            FuzzPayload("jwt-1", VulnerabilityType.JWT_MANIPULATION, '{"alg":"none"}', "JWT algorithm manipulation", "Privilege escalation"),
            FuzzPayload("jwt-2", VulnerabilityType.JWT_MANIPULATION, '{"sub":"admin"}', "JWT subject manipulation", "Admin access"),
            FuzzPayload("jwt-3", VulnerabilityType.JWT_MANIPULATION, "", "Remove signature", "Bypass authentication"),
        ]
        
        self._payloads[VulnerabilityType.SQL_INJECTION] = [
            FuzzPayload("sql-1", VulnerabilityType.SQL_INJECTION, "' OR '1'='1", "Basic SQL injection", "Data exfiltration"),
            FuzzPayload("sql-2", VulnerabilityType.SQL_INJECTION, "'; DROP TABLE users; --", "SQL drop table", "Denial of service"),
            FuzzPayload("sql-3", VulnerabilityType.SQL_INJECTION, "UNION SELECT * FROM users", "SQL union injection", "Data exfiltration"),
        ]
        
        self._payloads[VulnerabilityType.XSS] = [
            FuzzPayload("xss-1", VulnerabilityType.XSS, "<script>alert(1)</script>", "Basic XSS", "Cookie theft"),
            FuzzPayload("xss-2", VulnerabilityType.XSS, "<img src=x onerror=alert(1)>", "Img onerror XSS", "Cookie theft"),
            FuzzPayload("xss-3", VulnerabilityType.XSS, "{{constructor.constructor('alert(1)')()}}", "Template injection", "Code execution"),
        ]
        
        self._payloads[VulnerabilityType.PARAMETER_POLLUTION] = [
            FuzzPayload("pp-1", VulnerabilityType.PARAMETER_POLLUTION, "?id=1&id=2", "Duplicate parameter", "Parameter override"),
            FuzzPayload("pp-2", VulnerabilityType.PARAMETER_POLLUTION, "?user_id=1&user_id=999", "Multi-user IDOR", "Unauthorized access"),
        ]
    
    def get_payloads(self, vuln_type: VulnerabilityType) -> List[FuzzPayload]:
        """Get payloads for a vulnerability type."""
        return self._payloads.get(vuln_type, [])
    
    def mutate_payload(self, payload: str, vuln_type: VulnerabilityType) -> List[str]:
        """Mutate a payload for more coverage."""
        mutations = [payload]
        
        if vuln_type == VulnerabilityType.SQL_INJECTION:
            mutations.extend([
                payload.replace("'", "\""),
                payload.replace("1", "1-1"),
                payload + "--",
                payload + "/*",
            ])
        elif vuln_type == VulnerabilityType.XSS:
            mutations.extend([
                payload.replace("<script>", "<ScRiPt>"),
                payload.replace("alert", "confirm"),
                payload.replace("1", "1"),
            ])
        
        return mutations[:5]


class SecurityFuzzingAgent:
    """Main security fuzzing agent."""
    
    def __init__(
        self,
        base_url: str,
        cve_feed: Optional[CVEFeedConnector] = None,
    ):
        self.base_url = base_url
        self.cve_feed = cve_feed or CVEFeedConnector()
        self.payload_gen = PayloadGenerator()
        self._findings: Dict[str, VulnerabilityFinding] = {}
        self._lock = threading.Lock()
    
    async def initialize(self) -> None:
        """Initialize the agent with CVE data."""
        await self.cve_feed.fetch_cves()
    
    async def fuzz_endpoint(
        self,
        endpoint: str,
        method: str,
        vulnerability_types: List[VulnerabilityType],
    ) -> List[VulnerabilityFinding]:
        """Fuzz an endpoint for vulnerabilities."""
        findings = []
        
        async with httpx.AsyncClient() as client:
            for vuln_type in vulnerability_types:
                payloads = self.payload_gen.get_payloads(vuln_type)
                
                for fuzz_payload in payloads:
                    try:
                        if method.upper() == "GET":
                            response = await client.get(
                                f"{self.base_url}{endpoint}{fuzz_payload.payload}",
                                timeout=10.0,
                            )
                        else:
                            response = await client.request(
                                method.upper(),
                                f"{self.base_url}{endpoint}",
                                data={"q": fuzz_payload.payload},
                                timeout=10.0,
                            )
                        
                        if self._analyze_response(response, fuzz_payload, vuln_type):
                            finding = VulnerabilityFinding(
                                id=f"vuln-{len(self._findings)}",
                                vulnerability_type=vuln_type,
                                endpoint=endpoint,
                                severity=self._determine_severity(vuln_type),
                                description=fuzz_payload.description,
                                evidence={
                                    "url": f"{self.base_url}{endpoint}{fuzz_payload.payload}",
                                    "status_code": response.status_code,
                                    "payload": fuzz_payload.payload,
                                    "response_preview": response.text[:200],
                                },
                            )
                            findings.append(finding)
                            
                            with self._lock:
                                self._findings[finding.id] = finding
                                
                    except Exception as e:
                        print(f"Fuzzing error: {e}")
        
        return findings
    
    def _analyze_response(
        self,
        response: httpx.Response,
        payload: FuzzPayload,
        vuln_type: VulnerabilityType,
    ) -> bool:
        """Analyze if a response indicates a vulnerability."""
        if vuln_type == VulnerabilityType.IDOR:
            return response.status_code == 200 and "id" in response.text.lower()
        
        if vuln_type == VulnerabilityType.SQL_INJECTION:
            return any(x in response.text.lower() for x in ["sql", "syntax", "mysql", "error"])
        
        if vuln_type == VulnerabilityType.XSS:
            return payload.payload in response.text
        
        if vuln_type == VulnerabilityType.JWT_MANIPULATION:
            return response.status_code in [200, 201] and "token" in response.text.lower()
        
        return False
    
    def _determine_severity(self, vuln_type: VulnerabilityType) -> Severity:
        """Determine severity based on vulnerability type."""
        severe_types = [
            VulnerabilityType.SQL_INJECTION,
            VulnerabilityType.COMMAND_INJECTION,
            VulnerabilityType.SSRF,
        ]
        
        if vuln_type in severe_types:
            return Severity.CRITICAL
        elif vuln_type in [VulnerabilityType.BOLA, VulnerabilityType.IDOR]:
            return Severity.HIGH
        else:
            return Severity.MEDIUM
    
    def get_findings(
        self,
        severity: Optional[Severity] = None,
    ) -> List[Dict[str, Any]]:
        """Get vulnerability findings."""
        findings = list(self._findings.values())
        
        if severity:
            findings = [f for f in findings if f.severity == severity]
        
        return [
            {
                "id": f.id,
                "type": f.vulnerability_type.value,
                "endpoint": f.endpoint,
                "severity": f.severity.value,
                "description": f.description,
                "evidence": f.evidence,
                "discovered_at": f.discovered_at.isoformat(),
                "cve_references": f.cve_references,
            }
            for f in findings
        ]
    
    def get_report(self) -> str:
        """Generate a markdown security report."""
        findings = list(self._findings.values())
        
        report = "# Security Fuzzing Report\n\n"
        report += f"**Generated:** {datetime.now().isoformat()}\n\n"
        report += f"**Total Findings:** {len(findings)}\n\n"
        
        by_severity = {}
        for f in findings:
            if f.severity not in by_severity:
                by_severity[f.severity] = []
            by_severity[f.severity].append(f)
        
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            if severity in by_severity:
                findings_list = by_severity[severity]
                report += f"## {severity.value.upper()} ({len(findings_list)})\n\n"
                
                for f in findings_list:
                    report += f"### {f.vulnerability_type.value} at {f.endpoint}\n\n"
                    report += f"**Description:** {f.description}\n\n"
                    report += f"**Evidence:**\n```\n{json.dumps(f.evidence, indent=2)}\n```\n\n"
        
        return report


_global_agent: Optional[SecurityFuzzingAgent] = None


def get_security_agent(
    base_url: str,
    cve_feed: Optional[CVEFeedConnector] = None,
) -> SecurityFuzzingAgent:
    """Get global security fuzzing agent."""
    global _global_agent
    if _global_agent is None:
        _global_agent = SecurityFuzzingAgent(base_url, cve_feed)
    return _global_agent
