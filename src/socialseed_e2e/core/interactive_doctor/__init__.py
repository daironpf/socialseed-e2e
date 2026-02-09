"""Interactive Doctor module for socialseed-e2e.

This module provides AI-driven diagnosis and auto-fixing capabilities
for test failures.

Example:
    >>> from socialseed_e2e import InteractiveDoctor, ErrorContext
    >>>
    >>> doctor = InteractiveDoctor("/path/to/project")
    >>> session = doctor.start_session()
    >>>
    >>> context = ErrorContext(
    ...     test_name="test_login",
    ...     service_name="auth-service",
    ...     error_message="Validation error: age must be integer"
    ... )
    >>>
    >>> doctor.diagnose_and_fix(context, session)
    >>> doctor.end_session(session)
"""

from socialseed_e2e.core.interactive_doctor.analyzer import ErrorAnalyzer
from socialseed_e2e.core.interactive_doctor.doctor import (
    InteractiveDoctor,
    run_interactive_doctor,
)
from socialseed_e2e.core.interactive_doctor.fixer import AutoFixer
from socialseed_e2e.core.interactive_doctor.models import (
    AppliedFix,
    DiagnosisResult,
    DoctorSession,
    ErrorContext,
    ErrorType,
    FixStrategy,
    FixSuggestion,
    MissingFieldDetails,
    TypeMismatchDetails,
    ValidationErrorDetails,
)
from socialseed_e2e.core.interactive_doctor.suggester import FixSuggester

__all__ = [
    # Main classes
    "InteractiveDoctor",
    "ErrorAnalyzer",
    "FixSuggester",
    "AutoFixer",
    # Models
    "ErrorContext",
    "DiagnosisResult",
    "FixSuggestion",
    "AppliedFix",
    "DoctorSession",
    "ErrorType",
    "FixStrategy",
    "TypeMismatchDetails",
    "MissingFieldDetails",
    "ValidationErrorDetails",
    # Functions
    "run_interactive_doctor",
]
