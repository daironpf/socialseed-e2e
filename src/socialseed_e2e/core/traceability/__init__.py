"""Visual Traceability module for socialseed-e2e.

This module provides comprehensive traceability features including:
- Sequence diagram generation (Mermaid.js and PlantUML)
- Logic flow mapping and visualization
- Test execution tracing and reporting
- Integration with BasePage and TestRunner

Example:
    >>> from socialseed_e2e import enable_traceability, TraceContext
    >>>
    >>> # Enable traceability
    >>> collector = enable_traceability()
    >>>
    >>> # Run tests with tracing
    >>> with TraceContext("test_login", "auth-service"):
    ...     response = page.post("/login", json=credentials)
    ...     assert response.status == 200
    >>>
    >>> # Generate report
    >>> from socialseed_e2e import TraceReporter
    >>> reporter = TraceReporter()
    >>> report = reporter.generate_report()
    >>> reporter.save_html_report(report, "trace_report.html")
"""

from socialseed_e2e.core.traceability.collector import (
    TraceCollector,
    create_collector,
    get_global_collector,
    set_global_collector,
)
from socialseed_e2e.core.traceability.integration import (
    TraceContext,
    deinstrument_base_page,
    disable_traceability,
    enable_traceability,
    end_test_trace,
    instrument_base_page,
    record_interaction,
    record_logic_branch,
    start_test_trace,
    trace_assertion,
    trace_http_request,
)
from socialseed_e2e.core.traceability.logic_mapper import LogicMapper
from socialseed_e2e.core.traceability.models import (
    Component,
    Interaction,
    InteractionType,
    LogicBranch,
    LogicBranchType,
    LogicFlow,
    SequenceDiagram,
    TestTrace,
    TraceConfig,
    TraceReport,
)
from socialseed_e2e.core.traceability.reporter import TraceReporter
from socialseed_e2e.core.traceability.sequence_diagram import SequenceDiagramGenerator

__all__ = [
    # Core classes
    "TraceCollector",
    "TraceReporter",
    "SequenceDiagramGenerator",
    "LogicMapper",
    # Models
    "TestTrace",
    "TraceConfig",
    "TraceReport",
    "Component",
    "Interaction",
    "InteractionType",
    "LogicBranch",
    "LogicBranchType",
    "LogicFlow",
    "SequenceDiagram",
    # Integration
    "enable_traceability",
    "disable_traceability",
    "instrument_base_page",
    "deinstrument_base_page",
    "TraceContext",
    "start_test_trace",
    "end_test_trace",
    "record_interaction",
    "record_logic_branch",
    "trace_http_request",
    "trace_assertion",
    # Utilities
    "get_global_collector",
    "set_global_collector",
    "create_collector",
]
