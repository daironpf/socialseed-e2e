#!/usr/bin/env python3
"""
Architecture Auto-Update Script

This script scans the src/socialseed_e2e directory and automatically
updates the ARCHITECTURE.md file with new modules.

Usage:
    python scripts/update_architecture.py
    python scripts/update_architecture.py --dry-run  # Preview changes only
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src" / "socialseed_e2e"
ARCHITECTURE_FILE = PROJECT_ROOT / "ARCHITECTURE.md"

# Module categorization (auto-detected but can be overridden)
MODULE_CATEGORIES = {
    "Core": ["core", "commands", "templates"],
    "AI & Agents": [
        "ai_orchestrator",
        "ai_protocol",
        "agent_orchestrator",
        "agents",
        "ai_learning",
        "ai_mocking",
        "ml",
        "nlp",
    ],
    "Testing Protocols": ["graphql", "grpc", "realtime", "auth"],
    "Quality Assurance": [
        "security",
        "chaos",
        "performance",
        "visual_testing",
        "contract_testing",
        "assertions",
    ],
    "Data & Infrastructure": [
        "database",
        "test_data",
        "test_data_advanced",
        "mocks",
        "distributed",
    ],
    "Observability": ["observability", "analytics", "telemetry", "reporting"],
    "Integration": [
        "ci_cd",
        "cloud",
        "docker",
        "importers",
        "recorder",
        "collaboration",
        "environments",
        "plugins",
    ],
    "Advanced Features": [
        "project_manifest",
        "shadow_runner",
        "traffic_sniffer",
        "traffic_vector_index",
        "semantic_fuzzing",
        "self_healing",
        "risk_analyzer",
        "time_travel",
        "pii_masking",
        "services",
        "reporting",
        "dashboard",
        "tui",
        "utils",
    ],
}

# Purpose mapping for known modules
MODULE_PURPOSES = {
    "core": "Base abstraction (BasePage, Orchestrator, Runner)",
    "commands": "CLI command implementation",
    "templates": "Test scaffolding templates",
    "graphql": "GraphQL testing",
    "grpc": "gRPC testing",
    "realtime": "WebSocket/SSE testing",
    "auth": "Authentication protocols",
    "security": "Security testing (OWASP, pentest)",
    "chaos": "Chaos engineering",
    "performance": "Load & performance testing",
    "visual_testing": "Visual regression testing",
    "contract_testing": "Contract testing (Pact)",
    "database": "Database testing",
    "test_data": "Test data generation",
    "test_data_advanced": "Advanced data generation",
    "mocks": "Mock server & simulation",
    "distributed": "Distributed test execution",
    "observability": "Metrics, tracing, logging",
    "analytics": "Test analytics & dashboards",
    "telemetry": "Token/cost tracking",
    "reporting": "Report generation",
    "ci_cd": "CI/CD pipeline templates",
    "cloud": "Cloud provider integrations",
    "docker": "Docker support",
    "importers": "Import from Postman/OpenAPI",
    "recorder": "Record & replay sessions",
    "project_manifest": "Project knowledge management",
    "shadow_runner": "Production traffic capture",
    "traffic_sniffer": "Network traffic analysis",
    "traffic_vector_index": "Vector-based traffic search",
    "semantic_fuzzing": "AI-powered fuzzing",
    "self_healing": "Self-repairing tests",
    "risk_analyzer": "Risk assessment",
    "ai_orchestrator": "AI-driven test orchestration",
    "ai_protocol": "Standardized agent communication",
    "agent_orchestrator": "Multi-agent coordination",
    "agents": "Specialized agent implementations",
    "ai_learning": "Learning from test feedback",
    "ai_mocking": "AI-powered mocking",
    "collaboration": "Team collaboration features",
    "environments": "Environment management",
    "plugins": "Plugin system",
    "ml": "Machine learning utilities",
    "nlp": "Natural language processing",
    "dashboard": "Web dashboard",
    "tui": "Terminal UI",
    "utils": "Utility functions",
    "time_travel": "Time-travel debugging",
    "pii_masking": "PII detection and masking",
    "services": "Built-in demo services",
}


def scan_modules() -> List[Dict]:
    """Scan src directory for modules."""
    modules = []

    if not SRC_DIR.exists():
        print(f"ERROR: Source directory not found: {SRC_DIR}")
        sys.exit(1)

    for item in SRC_DIR.iterdir():
        if (
            item.is_dir()
            and not item.name.startswith("_")
            and not item.name.startswith(".")
        ):
            modules.append(
                {
                    "name": item.name,
                    "path": str(item.relative_to(PROJECT_ROOT)),
                    "has_init": (item / "__init__.py").exists(),
                }
            )

    return sorted(modules, key=lambda x: x["name"].lower())


def detect_dependencies(module_path: Path) -> List[str]:
    """Detect module dependencies from imports."""
    deps: Set[str] = set()

    for py_file in module_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text(errors="ignore")
        except Exception:
            continue

        # Extract imports from socialseed_e2e
        import_pattern = r"from socialseed_e2e\.(\w+)"
        matches = re.findall(import_pattern, content)

        # Filter to actual module names (not submodules)
        for match in matches:
            if (SRC_DIR / match).exists():
                deps.add(match)

    return sorted(deps)


def categorize_module(module_name: str) -> str:
    """Categorize a module based on known categories."""
    for category, modules in MODULE_CATEGORIES.items():
        if module_name in modules:
            return category
    return "Other"


def get_module_purpose(module_name: str) -> str:
    """Get the purpose of a module."""
    return MODULE_PURPOSES.get(module_name, "Module purpose not defined")


def generate_module_registry_table(modules: List[Dict]) -> str:
    """Generate the module registry markdown table."""
    lines = [
        "### 6.1 Core Modules",
        "",
        "| Module | Purpose | Dependencies |",
        "|--------|---------|--------------|",
    ]

    # Group by category
    by_category: Dict[str, List[Dict]] = {}
    for module in modules:
        category = categorize_module(module["name"])
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(module)

    # Generate tables by category
    category_order = [
        "Core",
        "AI & Agents",
        "Testing Protocols",
        "Quality Assurance",
        "Data & Infrastructure",
        "Observability",
        "Integration",
        "Advanced Features",
        "Other",
    ]
    category_index = 1

    for category in category_order:
        if category not in by_category:
            continue

        header_level = 3 if category != "Core" else 3
        lines.append(f"\n### 6.{category_index} {category} Modules")
        lines.append(f"\n| Module | Purpose | Dependencies |")
        lines.append(f"|--------|---------|--------------|")

        for module in by_category[category]:
            deps = module.get("dependencies", [])
            deps_str = ", ".join(deps) if deps else "None"
            purpose = get_module_purpose(module["name"])
            lines.append(f"| `{module['name']}` | {purpose} | {deps_str} |")

        category_index += 1

    return "\n".join(lines)


def update_architecture_file(modules: List[Dict], dry_run: bool = False) -> bool:
    """Update the ARCHITECTURE.md file with current modules."""

    if not ARCHITECTURE_FILE.exists():
        print(f"ERROR: ARCHITECTURE.md not found: {ARCHITECTURE_FILE}")
        return False

    content = ARCHITECTURE_FILE.read_text()

    # Update the "Last Updated" date
    content = re.sub(
        r"\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}",
        f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}",
        content,
    )

    # Find and update the module registry section
    # Look for the pattern that indicates the start of module registry
    registry_pattern = r"(## 6\. Module Registry\n\nThis registry is auto-generated.*?)(### 6\.1 Core Modules\n\n\| Module \| Purpose \| Dependencies \|)"

    if not re.search(registry_pattern, content):
        print("WARNING: Could not find module registry section to update")
        return False

    # Generate new registry content
    new_registry = generate_module_registry_table(modules)

    # Replace old registry with new one
    # Find from "## 6. Module Registry" to "## 7. Auto-Update"
    old_section_pattern = r"## 6\. Module Registry.*?(?=## 7\. Auto-Update)"
    match = re.search(old_section_pattern, content, re.DOTALL)

    if match:
        new_section = f"## 6. Module Registry\n\nThis registry is auto-generated by scanning the `/src/socialseed_e2e` directory.\n\n{new_registry}\n\n"
        content = content[: match.start()] + new_section + content[match.end() :]

    if dry_run:
        print("=== DRY RUN: Changes that would be made ===")
        print(f"Would update {len(modules)} modules in registry")
        return True

    # Write updated content
    ARCHITECTURE_FILE.write_text(content)
    return True


def main():
    parser = argparse.ArgumentParser(description="Auto-update ARCHITECTURE.md")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    args = parser.parse_args()

    print("=" * 60)
    print("SocialSeed E2E - Architecture Auto-Update")
    print("=" * 60)
    print(f"\nScanning: {SRC_DIR}")

    # Scan for modules
    modules = scan_modules()
    print(f"Found {len(modules)} modules\n")

    # Detect dependencies for each module
    for module in modules:
        module_path = SRC_DIR / module["name"]
        deps = detect_dependencies(module_path)
        module["dependencies"] = deps
        module["category"] = categorize_module(module["name"])
        print(f"  - {module['name']}: {len(deps)} dependencies")

    # Update the architecture file
    print("\n" + "=" * 60)
    if update_architecture_file(modules, dry_run=args.dry_run):
        print("SUCCESS: Architecture documentation updated!")
    else:
        print("ERROR: Failed to update architecture documentation")
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
