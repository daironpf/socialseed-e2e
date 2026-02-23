"""Versioned contract management for APIs.

This module handles version-specific contracts and
tracks contract evolution across versions.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContractType(str, Enum):
    """Types of API contracts."""

    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    CUSTOM = "custom"


class VersionedContract:
    """Manage version-specific API contracts."""

    def __init__(self, base_path: Optional[str] = None):
        """Initialize versioned contract manager.

        Args:
            base_path: Base path for storing contract files
        """
        self.base_path = Path(base_path) if base_path else Path("contracts")
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.contracts: Dict[str, Dict[str, Any]] = {}
        self.contract_history: List[Dict[str, Any]] = []

    def add_contract(
        self,
        version: str,
        contract: Dict[str, Any],
        contract_type: ContractType = ContractType.OPENAPI,
    ):
        """Add a version-specific contract.

        Args:
            version: API version
            contract: Contract specification
            contract_type: Type of contract
        """
        self.contracts[version] = {
            "version": version,
            "type": contract_type,
            "spec": contract,
            "created_at": datetime.now().isoformat(),
        }

        self.contract_history.append(
            {
                "version": version,
                "action": "added",
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_contract(self, version: str) -> Optional[Dict[str, Any]]:
        """Get contract for a specific version.

        Args:
            version: API version

        Returns:
            Contract specification or None
        """
        if version in self.contracts:
            return self.contracts[version]["spec"]
        return None

    def compare_contracts(self, version1: str, version2: str) -> Dict[str, Any]:
        """Compare contracts between two versions.

        Args:
            version1: First version
            version2: Second version

        Returns:
            Comparison result with differences
        """
        contract1 = self.get_contract(version1)
        contract2 = self.get_contract(version2)

        if not contract1 or not contract2:
            return {"error": "One or both contracts not found"}

        differences = {
            "added_endpoints": [],
            "removed_endpoints": [],
            "modified_endpoints": [],
            "added_params": [],
            "removed_params": [],
            "breaking_changes": [],
        }

        paths1 = set(contract1.get("paths", {}).keys())
        paths2 = set(contract2.get("paths", {}).keys())

        differences["added_endpoints"] = list(paths2 - paths1)
        differences["removed_endpoints"] = list(paths1 - paths2)

        for path in paths1 & paths2:
            methods1 = set(contract1["paths"].get(path, {}).keys())
            methods2 = set(contract2["paths"].get(path, {}).keys())

            if methods1 != methods2:
                differences["modified_endpoints"].append(path)

        return differences

    def detect_breaking_changes(
        self, from_version: str, to_version: str
    ) -> List[Dict[str, Any]]:
        """Detect breaking changes between two contract versions.

        Args:
            from_version: Source version
            to_version: Target version

        Returns:
            List of breaking changes
        """
        comparison = self.compare_contracts(from_version, to_version)

        breaking_changes = []

        for endpoint in comparison.get("removed_endpoints", []):
            breaking_changes.append(
                {
                    "type": "endpoint_removed",
                    "severity": "critical",
                    "description": f"Endpoint {endpoint} was removed",
                    "from_version": from_version,
                    "to_version": to_version,
                }
            )

        for endpoint in comparison.get("modified_endpoints", []):
            breaking_changes.append(
                {
                    "type": "endpoint_modified",
                    "severity": "high",
                    "description": f"Endpoint {endpoint} was modified",
                    "from_version": from_version,
                    "to_version": to_version,
                }
            )

        return breaking_changes

    def generate_migration_guide(self, from_version: str, to_version: str) -> str:
        """Generate migration guide between versions.

        Args:
            from_version: Source version
            to_version: Target version

        Returns:
            Migration guide as Markdown string
        """
        breaking_changes = self.detect_breaking_changes(from_version, to_version)

        lines = [
            f"# Migration Guide: {from_version} → {to_version}",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## Overview",
            "",
            f"This guide helps migrate from API version **{from_version}** to **{to_version}**.",
            "",
        ]

        if breaking_changes:
            lines.extend(
                [
                    "## Breaking Changes",
                    "",
                    f"Found {len(breaking_changes)} breaking change(s):",
                    "",
                ]
            )

            for change in breaking_changes:
                lines.append(f"### {change['type'].replace('_', ' ').title()}")
                lines.append(f"- **Severity:** {change['severity']}")
                lines.append(f"- **Description:** {change['description']}")
                lines.append("")
        else:
            lines.extend(
                [
                    "## Breaking Changes",
                    "",
                    "No breaking changes detected between these versions.",
                    "",
                ]
            )

        lines.extend(
            [
                "## Recommended Migration Steps",
                "",
                "1. Review the breaking changes listed above",
                "2. Update your API client to handle new response formats",
                "3. Test your application against the new version",
                "4. Update any deprecated endpoint calls",
                "5. Deploy and monitor for errors",
                "",
            ]
        )

        return "\n".join(lines)

    def save_contract(self, version: str, file_path: Optional[str] = None):
        """Save contract to file.

        Args:
            version: API version
            file_path: Optional custom file path
        """
        contract = self.contracts.get(version)
        if not contract:
            return

        if file_path:
            path = Path(file_path)
        else:
            path = self.base_path / f"contract_{version}.json"

        path.write_text(json.dumps(contract["spec"], indent=2))

    def load_contract(self, version: str, file_path: str):
        """Load contract from file.

        Args:
            version: API version
            file_path: Path to contract file
        """
        path = Path(file_path)
        if path.exists():
            spec = json.loads(path.read_text())
            self.add_contract(version, spec)

    def get_contract_evolution(self) -> List[Dict[str, Any]]:
        """Get the evolution history of contracts.

        Returns:
            List of contract changes
        """
        return self.contract_history

    def get_latest_contract(self) -> Optional[Dict[str, Any]]:
        """Get the latest contract (highest version number).

        Returns:
            Latest contract specification or None
        """
        if not self.contracts:
            return None

        version_nums = []
        for version in self.contracts.keys():
            import re

            match = re.search(r"(\d+)", version)
            if match:
                version_nums.append((int(match.group(1)), version))

        if version_nums:
            latest = max(version_nums)[1]
            return self.contracts[latest]["spec"]

        return None
