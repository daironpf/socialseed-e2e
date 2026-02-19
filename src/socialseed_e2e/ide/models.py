"""Pydantic models for IDE integration."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class IDEType(str, Enum):
    """Supported IDE types."""

    VSCODE = "vscode"
    INTELLIJ = "intellij"
    PYCHARM = "pycharm"
    VIM = "vim"
    EMACS = "emacs"


class TestTemplate(BaseModel):
    """Test template for IDE."""

    id: str
    name: str
    description: str
    code: str
    language: str = "python"
    category: str = "general"


class DebugConfig(BaseModel):
    """Debug configuration."""

    name: str
    type: str
    request: str = "launch"
    module: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)


class LaunchConfig(BaseModel):
    """IDE launch configuration."""

    version: str = "0.2.0"
    configurations: List[DebugConfig] = Field(default_factory=list)


class CompletionItem(BaseModel):
    """Code completion item."""

    label: str
    kind: str
    detail: str
    insert_text: str
    documentation: Optional[str] = None


class TestWizardStep(BaseModel):
    """Test creation wizard step."""

    step_id: str
    title: str
    description: str
    options: List[Dict[str, Any]] = Field(default_factory=list)


class TestWizardConfig(BaseModel):
    """Configuration for test creation wizard."""

    wizard_id: str
    title: str
    steps: List[TestWizardStep] = Field(default_factory=list)
