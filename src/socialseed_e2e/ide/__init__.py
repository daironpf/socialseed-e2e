"""IDE Integration Module.

This module provides IDE integration support including:
- VS Code extension configuration
- Test generation from endpoints
- Debug configuration
- Code completion
- API client import/export (Postman, OpenAPI)

Usage:
    from socialseed_e2e.ide import VSCodeExtension, APIClientSync

    # Setup VS Code extension
    vscode = VSCodeExtension("/path/to/workspace")
    vscode.write_config_files(base_url="http://localhost:8080")

    # Import from Postman
    sync = APIClientSync()
    tests = sync.import_from_postman("collection.json")

    # Import from OpenAPI
    tests = sync.import_from_openapi("openapi.yaml")
"""

from .models import (
    IDEType,
    TestTemplate,
    DebugConfig,
    LaunchConfig,
    CompletionItem,
    TestWizardStep,
    TestWizardConfig,
)
from .vscode import VSCodeExtension, VSCodeCommands
from .api_client_sync import (
    PostmanImporter,
    PostmanExporter,
    OpenAPIImporter,
    APIClientSync,
)

__all__ = [
    "IDEType",
    "TestTemplate",
    "DebugConfig",
    "LaunchConfig",
    "CompletionItem",
    "TestWizardStep",
    "TestWizardConfig",
    "VSCodeExtension",
    "VSCodeCommands",
    "PostmanImporter",
    "PostmanExporter",
    "OpenAPIImporter",
    "APIClientSync",
]
