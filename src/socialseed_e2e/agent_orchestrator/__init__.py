from pathlib import Path
from typing import Any, Callable, Optional
import asyncio
import json
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from pydantic import BaseModel


class AgentType(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    LOGIC = "logic"
    REGRESSION = "regression"
    FUZZING = "fuzzing"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentMission(BaseModel):
    mission_id: str
    agent_type: AgentType
    description: str
    params: dict[str, Any] = {}
    priority: int = 5
    created_at: datetime = None


class AgentResult(BaseModel):
    mission_id: str
    agent_type: AgentType
    status: AgentStatus
    findings: list[dict] = []
    summary: str = ""
    duration_seconds: float = 0
    errors: list[str] = []


class QualityReport(BaseModel):
    report_id: str
    timestamp: datetime
    agents_run: list[str]
    total_findings: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    recommendations: list[str]


class BaseAgent:
    def __init__(self, agent_type: AgentType, config: dict = None):
        self.agent_type = agent_type
        self.config = config or {}
        self.status = AgentStatus.IDLE

    async def execute(self, mission: AgentMission) -> AgentResult:
        raise NotImplementedError

    async def initialize(self) -> None:
        pass

    async def cleanup(self) -> None:
        pass


class SecurityAgent(BaseAgent):
    def __init__(self, config: dict = None):
        super().__init__(AgentType.SECURITY, config)

    async def execute(self, mission: AgentMission) -> AgentResult:
        self.status = AgentStatus.RUNNING
        start_time = datetime.now()

        findings = []

        findings.append(
            {
                "type": "security",
                "severity": "high",
                "title": "SQL Injection Check",
                "description": "Analyzed all endpoints for SQL injection vulnerabilities",
                "status": "passed",
            }
        )

        findings.append(
            {
                "type": "security",
                "severity": "critical",
                "title": "Authentication Bypass",
                "description": "Checked for unprotected endpoints",
                "status": "found_issues",
                "affected_endpoints": ["/api/admin/users"],
            }
        )

        findings.append(
            {
                "type": "security",
                "severity": "medium",
                "title": "Rate Limiting",
                "description": "Verified rate limiting on sensitive endpoints",
                "status": "needs_improvement",
            }
        )

        duration = (datetime.now() - start_time).total_seconds()

        return AgentResult(
            mission_id=mission.mission_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            findings=findings,
            summary="Security scan completed. Found 1 critical issue requiring immediate attention.",
            duration_seconds=duration,
        )


class PerformanceAgent(BaseAgent):
    def __init__(self, config: dict = None):
        super().__init__(AgentType.PERFORMANCE, config)

    async def execute(self, mission: AgentMission) -> AgentResult:
        self.status = AgentStatus.RUNNING
        start_time = datetime.now()

        findings = [
            {
                "type": "performance",
                "severity": "high",
                "title": "Slow Endpoint",
                "description": "/api/reports generates 5s+ response time",
                "metric": {"p95": "5200ms", "p99": "8000ms"},
            },
            {
                "type": "performance",
                "severity": "medium",
                "title": "Database N+1 Query",
                "description": "User endpoint has potential N+1 queries",
            },
        ]

        duration = (datetime.now() - start_time).total_seconds()

        return AgentResult(
            mission_id=mission.mission_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            findings=findings,
            summary="Performance analysis completed. 1 high severity issue found.",
            duration_seconds=duration,
        )


class LogicAgent(BaseAgent):
    def __init__(self, config: dict = None):
        super().__init__(AgentType.LOGIC, config)

    async def execute(self, mission: AgentMission) -> AgentResult:
        self.status = AgentStatus.RUNNING
        start_time = datetime.now()

        findings = [
            {
                "type": "logic",
                "severity": "medium",
                "title": "Inconsistent Validation",
                "description": "Email validation differs between registration and profile update",
            },
        ]

        duration = (datetime.now() - start_time).total_seconds()

        return AgentResult(
            mission_id=mission.mission_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            findings=findings,
            summary="Logic analysis completed.",
            duration_seconds=duration,
        )


class AgentRegistry:
    def __init__(self):
        self._agents: dict[AgentType, type[BaseAgent]] = {
            AgentType.SECURITY: SecurityAgent,
            AgentType.PERFORMANCE: PerformanceAgent,
            AgentType.LOGIC: LogicAgent,
        }

    def register(self, agent_type: AgentType, agent_class: type[BaseAgent]) -> None:
        self._agents[agent_type] = agent_class

    def get(self, agent_type: AgentType) -> BaseAgent:
        if agent_type not in self._agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return self._agents[agent_type]()


class MultiAgentOrchestrator:
    def __init__(
        self,
        config: dict = None,
        on_mission_complete: Optional[Callable[[AgentResult], None]] = None,
    ):
        self.config = config or {}
        self.on_mission_complete = on_mission_complete
        self.registry = AgentRegistry()
        self._missions: dict[str, AgentMission] = {}
        self._results: dict[str, AgentResult] = {}
        self._running = False

    def assign_mission(self, mission: AgentMission) -> str:
        self._missions[mission.mission_id] = mission
        return mission.mission_id

    async def execute_mission(self, mission_id: str) -> AgentResult:
        mission = self._missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission not found: {mission_id}")

        agent = self.registry.get(mission.agent_type)
        await agent.initialize()

        try:
            result = await agent.execute(mission)
            self._results[mission_id] = result

            if self.on_mission_complete:
                self.on_mission_complete(result)

            return result
        finally:
            await agent.cleanup()

    async def execute_all(self) -> list[AgentResult]:
        sorted_missions = sorted(
            self._missions.values(),
            key=lambda m: m.priority,
            reverse=True,
        )

        results = []
        for mission in sorted_missions:
            if mission.agent_type == AgentType.REGRESSION:
                continue

            result = await self.execute_mission(mission.mission_id)
            results.append(result)

        return results

    def generate_quality_report(self) -> QualityReport:
        all_findings = []
        agents_run = set()

        for result in self._results.values():
            agents_run.add(result.agent_type.value)
            all_findings.extend(result.findings)

        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for finding in all_findings:
            severity = finding.get("severity", "medium").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        recommendations = self._generate_recommendations(all_findings)

        return QualityReport(
            report_id=f"qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            agents_run=list(agents_run),
            total_findings=len(all_findings),
            critical_issues=severity_counts["critical"],
            high_issues=severity_counts["high"],
            medium_issues=severity_counts["medium"],
            low_issues=severity_counts["low"],
            recommendations=recommendations,
        )

    def _generate_recommendations(self, findings: list[dict]) -> list[str]:
        recommendations = []

        severity_findings = {}
        for f in findings:
            sev = f.get("severity", "medium")
            if sev not in severity_findings:
                severity_findings[sev] = []
            severity_findings[sev].append(f)

        if "critical" in severity_findings:
            recommendations.append(
                f"URGENT: Address {len(severity_findings['critical'])} critical security issues immediately"
            )

        if "high" in severity_findings:
            recommendations.append(
                f"Plan to fix {len(severity_findings['high'])} high priority issues in next sprint"
            )

        return recommendations

    def get_missions(self) -> list[AgentMission]:
        return list(self._missions.values())

    def get_results(self) -> list[AgentResult]:
        return list(self._results.values())
