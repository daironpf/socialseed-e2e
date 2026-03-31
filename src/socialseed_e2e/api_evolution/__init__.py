"""
API Evolution & Auto-Contract Versioning - EPIC-021
Automatically detects API changes and updates contracts.
"""

from .contract_versioning import (
    APIChange,
    APIContract,
    BreakingChangeAlert,
    ChangeSeverity,
    ChangeType,
    ContractAutoUpdater,
    SemanticDiffEngine,
    get_diff_engine,
)

__all__ = [
    "APIChange",
    "APIContract",
    "BreakingChangeAlert",
    "ChangeSeverity",
    "ChangeType",
    "ContractAutoUpdater",
    "SemanticDiffEngine",
    "get_diff_engine",
]
