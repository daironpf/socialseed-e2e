"""AI Agent Orchestration Layer for Autonomous Testing.

This module provides sophisticated orchestration capabilities that allow AI agents
to autonomously plan, execute, and report on comprehensive testing strategies.

Key Features:
- Test Strategy Planning: AI analyzes codebase and generates testing strategies
- Risk-Based Prioritization: AI prioritizes tests based on code changes and business impact
- Self-Healing Tests: AI automatically fixes flaky tests
- Intelligent Retry Logic: AI learns from failures and optimizes retry strategies
- Autonomous Debugging: AI analyzes logs and suggests fixes

Example:
    >>> from socialseed_e2e.ai_orchestrator import (
    ...     StrategyPlanner,
    ...     AutonomousRunner,
    ...     SelfHealer,
    ...     AIDebugger,
    ... )

    >>> # Plan a test strategy
    >>> planner = StrategyPlanner("/path/to/project")
    >>> strategy = planner.generate_strategy("API Testing Strategy", "Test all API endpoints")

    >>> # Run tests autonomously
    >>> runner = AutonomousRunner("/path/to/project")
    >>> execution = runner.run_strategy(strategy, context_factory)

    >>> # Debug failures
    >>> debugger = AIDebugger("/path/to/project")
    >>> for result in execution.results:
    ...     if result.status == TestStatus.FAILED:
    ...         analysis = debugger.debug(test_case, result, execution.id)
"""

from socialseed_e2e.ai_orchestrator.autonomous_runner import (
    AutonomousRunner,
    IntelligentRetryManager,
    TestExecutor,
)
from socialseed_e2e.ai_orchestrator.debugger import (
    AIDebugger,
    FixSuggester,
    LogAnalyzer,
    RootCauseAnalyzer,
)
from socialseed_e2e.ai_orchestrator.flakiness_predictor import (
    FlakinessAnalyzer,
    FlakinessPredictor,
    FlakinessPrediction,
    FlakinessRiskLevel,
    FlakinessFactor,
)
from socialseed_e2e.ai_orchestrator.models import (
    DebugAnalysis,
    FailurePattern,
    OrchestratorConfig,
    RetryStrategy,
    RiskFactor,
    TestCase,
    TestExecution,
    TestPriority,
    TestResult,
    TestStatus,
    TestStrategy,
    TestType,
)
from socialseed_e2e.ai_orchestrator.self_healer import (
    FlakyPatternDetector,
    SelfHealer,
    TestAnalyzer,
    TestHealer,
)
from socialseed_e2e.ai_orchestrator.strategy_planner import (
    CodeAnalyzer,
    StrategyPlanner,
)

__all__ = [
    # Models
    "DebugAnalysis",
    "FailurePattern",
    "OrchestratorConfig",
    "RetryStrategy",
    "RiskFactor",
    "TestCase",
    "TestExecution",
    "TestPriority",
    "TestResult",
    "TestStatus",
    "TestStrategy",
    "TestType",
    # Strategy Planner
    "StrategyPlanner",
    "CodeAnalyzer",
    # Autonomous Runner
    "AutonomousRunner",
    "IntelligentRetryManager",
    "TestExecutor",
    # Self Healer
    "SelfHealer",
    "TestHealer",
    "TestAnalyzer",
    "FlakyPatternDetector",
    # Debugger
    "AIDebugger",
    "LogAnalyzer",
    "RootCauseAnalyzer",
    "FixSuggester",
    # Flakiness Predictor (Issue #3)
    "FlakinessAnalyzer",
    "FlakinessPredictor",
    "FlakinessPrediction",
    "FlakinessRiskLevel",
    "FlakinessFactor",
]
