"""
Explainable AI (XAI) Error Tracing System for socialseed-e2e.

This module provides transparent AI decision-making by:
- Recording thought processes and reasoning chains
- Injecting explanations into reports
- Providing interactive feedback loops
- Integrating with ai_learning module

Features:
- Standardized Agent Protocol with reasoning chains
- Interactive AI thought visualization
- Human feedback integration
- Explanation-based reporting
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of AI agents in the framework."""

    HEALER = "healer"
    GENERATOR = "generator"
    PLANNER = "planner"
    EXPLORER = "explorer"
    ORCHESTRATOR = "orchestrator"


class ReasoningStep(BaseModel):
    """A single step in the reasoning chain."""

    step_id: str

    thought: str
    action: str
    result: str

    confidence: float = Field(..., ge=0, le=1)

    alternatives_considered: List[str] = Field(default_factory=list)
    rejected_reasons: Dict[str, str] = Field(default_factory=dict)

    timestamp: datetime = Field(default_factory=datetime.now)


class AgentDecision(BaseModel):
    """A complete decision made by an AI agent."""

    decision_id: str

    agent_type: AgentType
    task_id: str

    reasoning_chain: List[ReasoningStep] = Field(default_factory=list)

    final_decision: str
    decision_rationale: str

    confidence_score: float = Field(..., ge=0, le=1)

    metadata: Dict[str, Any] = {}

    created_at: datetime = Field(default_factory=datetime.now)


class HumanFeedback(BaseModel):
    """Human feedback on AI decision."""

    feedback_id: str

    decision_id: str
    agent_type: AgentType

    rating: str
    comment: Optional[str] = None

    is_correct: bool
    suggested_correction: Optional[str] = None

    timestamp: datetime = Field(default_factory=datetime.now)


class XAIReport(BaseModel):
    """Complete XAI report for a test execution."""

    report_id: str
    generated_at: datetime = Field(default_factory=datetime.now)

    test_name: str
    test_file: str

    agent_decisions: List[AgentDecision] = Field(default_factory=list)

    total_decisions: int = 0
    average_confidence: float = 0.0

    human_feedback: List[HumanFeedback] = Field(default_factory=list)


class ThoughtChainRecorder:
    """
    Records thought chains for AI agent decisions.
    """

    def __init__(self):
        self.decisions: List[AgentDecision] = []
        self.current_decision: Optional[AgentDecision] = None

    def start_decision(
        self,
        agent_type: AgentType,
        task_id: str,
        final_decision: str,
    ) -> str:
        """Start recording a new decision."""
        decision = AgentDecision(
            decision_id=str(uuid.uuid4()),
            agent_type=agent_type,
            task_id=task_id,
            final_decision=final_decision,
            decision_rationale="",
        )
        self.current_decision = decision
        return decision.decision_id

    def add_reasoning_step(
        self,
        thought: str,
        action: str,
        result: str,
        confidence: float = 0.8,
        alternatives: Optional[List[str]] = None,
    ) -> None:
        """Add a reasoning step to the current decision."""
        if not self.current_decision:
            return

        step = ReasoningStep(
            step_id=str(uuid.uuid4()),
            thought=thought,
            action=action,
            result=result,
            confidence=confidence,
            alternatives_considered=alternatives or [],
        )

        self.current_decision.reasoning_chain.append(step)

    def complete_decision(
        self,
        rationale: str,
        confidence: float,
    ) -> AgentDecision:
        """Complete and store the decision."""
        if not self.current_decision:
            raise ValueError("No active decision to complete")

        self.current_decision.decision_rationale = rationale
        self.current_decision.confidence_score = confidence

        self.decisions.append(self.current_decision)
        completed = self.current_decision
        self.current_decision = None

        return completed

    def get_decisions(self) -> List[AgentDecision]:
        """Get all recorded decisions."""
        return self.decisions

    def get_decision(self, decision_id: str) -> Optional[AgentDecision]:
        """Get a specific decision by ID."""
        return next((d for d in self.decisions if d.decision_id == decision_id), None)


class HumanFeedbackCollector:
    """
    Collects and processes human feedback on AI decisions.
    """

    def __init__(self):
        self.feedback_list: List[HumanFeedback] = []

    def add_feedback(
        self,
        decision_id: str,
        agent_type: AgentType,
        rating: str,
        is_correct: bool,
        comment: Optional[str] = None,
        correction: Optional[str] = None,
    ) -> HumanFeedback:
        """Add human feedback for a decision."""
        feedback = HumanFeedback(
            feedback_id=str(uuid.uuid4()),
            decision_id=decision_id,
            agent_type=agent_type,
            rating=rating,
            is_correct=is_correct,
            comment=comment,
            suggested_correction=correction,
        )

        self.feedback_list.append(feedback)
        return feedback

    def get_feedback(self) -> List[HumanFeedback]:
        """Get all feedback."""
        return self.feedback_list

    def get_incorrect_decisions(self) -> List[HumanFeedback]:
        """Get feedback where AI was incorrect."""
        return [f for f in self.feedback_list if not f.is_correct]


class ExplainableAIReporter:
    """
    Generates XAI reports with thought chains and explanations.
    """

    def __init__(self):
        self.recorder = ThoughtChainRecorder()
        self.feedback_collector = HumanFeedbackCollector()

    def generate_report(
        self,
        test_name: str,
        test_file: str,
    ) -> XAIReport:
        """Generate an XAI report for a test."""
        decisions = self.recorder.get_decisions()
        feedback = self.feedback_collector.get_feedback()

        avg_confidence = (
            sum(d.confidence_score for d in decisions) / len(decisions)
            if decisions
            else 0.0
        )

        report = XAIReport(
            report_id=str(uuid.uuid4()),
            test_name=test_name,
            test_file=test_file,
            agent_decisions=decisions,
            total_decisions=len(decisions),
            average_confidence=avg_confidence,
            human_feedback=feedback,
        )

        return report

    def generate_html_report(self, report: XAIReport) -> str:
        """Generate HTML report with expandable thought chains."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>XAI Report - {report.test_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .decision {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .agent-type {{ color: #666; font-size: 0.9em; }}
        .confidence {{ color: #2196F3; font-weight: bold; }}
        .reasoning-step {{ margin: 10px 0; padding-left: 20px; border-left: 2px solid #eee; }}
        .thought {{ font-style: italic; color: #555; }}
        .action {{ color: #4CAF50; }}
        .result {{ color: #FF9800; }}
        .alternatives {{ color: #9E9E9E; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>Explainable AI Report</h1>
    <p>Test: {report.test_name}</p>
    <p>Generated: {report.generated_at}</p>
    <p>Total Decisions: {report.total_decisions}</p>
    <p>Average Confidence: {report.average_confidence:.2%}</p>
"""

        for decision in report.agent_decisions:
            html += f"""
    <div class="decision">
        <h2>Agent: {decision.agent_type.value}</h2>
        <p class="confidence">Confidence: {decision.confidence_score:.2%}</p>
        <p><strong>Decision:</strong> {decision.final_decision}</p>
        <p><strong>Rationale:</strong> {decision.decision_rationale}</p>
"""

            for step in decision.reasoning_chain:
                html += f"""
        <div class="reasoning-step">
            <p class="thought">"{step.thought}"</p>
            <p class="action">→ Action: {step.action}</p>
            <p class="result">← Result: {step.result}</p>
"""
                if step.alternatives_considered:
                    html += f"""
            <p class="alternatives">Alternatives considered: {", ".join(step.alternatives_considered)}</p>
"""
                html += "</div>"

            html += "</div>"

        html += """
</body>
</html>
"""
        return html


class XAIMiddleware:
    """
    Middleware for automatically recording agent decisions.
    """

    def __init__(self, reporter: ExplainableAIReporter):
        self.reporter = reporter
        self.recorder = reporter.recorder

    def record_healer_decision(
        self,
        task_id: str,
        fix_applied: str,
        rationale: str,
        confidence: float,
    ) -> str:
        """Record a HealerAgent decision."""
        decision_id = self.recorder.start_decision(
            AgentType.HEALER, task_id, fix_applied
        )
        self.recorder.add_reasoning_step(
            thought="Analyzing test failure",
            action="Applying fix",
            result=fix_applied,
            confidence=confidence,
        )
        self.recorder.complete_decision(rationale, confidence)
        return decision_id

    def record_generator_decision(
        self,
        task_id: str,
        test_generated: str,
        rationale: str,
        confidence: float,
    ) -> str:
        """Record a GeneratorAgent decision."""
        decision_id = self.recorder.start_decision(
            AgentType.GENERATOR, task_id, test_generated
        )
        self.recorder.add_reasoning_step(
            thought="Analyzing API endpoints",
            action="Generating test",
            result=test_generated,
            confidence=confidence,
        )
        self.recorder.complete_decision(rationale, confidence)
        return decision_id


__all__ = [
    "AgentDecision",
    "AgentType",
    "ExplainableAIReporter",
    "HumanFeedback",
    "HumanFeedbackCollector",
    "ReasoningStep",
    "ThoughtChainRecorder",
    "XAIMiddleware",
    "XAIReport",
]
