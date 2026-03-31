"""
Autonomous Source Code Auto-Fixing - EPIC-018
AI-powered code fixes with GitHub/GitLab PR integration.
"""

from .source_fixer import (
    AutoFixOrchestrator,
    CodePatch,
    FixCategory,
    GitIntegration,
    PRCreator,
    SourceCodeAnalyzer,
    SourceCodeFix,
    VCSProvider,
    get_auto_fix_orchestrator,
)

__all__ = [
    "AutoFixOrchestrator",
    "CodePatch",
    "FixCategory",
    "GitIntegration",
    "PRCreator",
    "SourceCodeAnalyzer",
    "SourceCodeFix",
    "VCSProvider",
    "get_auto_fix_orchestrator",
]
