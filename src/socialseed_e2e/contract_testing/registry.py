"""Contract registry and versioning system for socialseed-e2e."""

import json
from pathlib import Path
from typing import List, Optional


class LocalContractRegistry:
    """Local storage and versioning for API contracts."""

    def __init__(self, root_dir: str = ".e2e/contracts"):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, contract_content: str, consumer: str, provider: str, version: str = "latest"):
        """Publish a contract to the registry."""
        provider_dir = self.root_dir / provider / consumer
        provider_dir.mkdir(parents=True, exist_ok=True)

        target_file = provider_dir / f"{version}.json"
        with open(target_file, "w") as f:
            f.write(contract_content)

        print(f"Contract {consumer}->{provider} ({version}) published to registry.")

    def get_contract(self, consumer: str, provider: str, version: str = "latest") -> Optional[str]:
        """Retrieve a contract from the registry."""
        path = self.root_dir / provider / consumer / f"{version}.json"
        if path.exists():
            return path.read_text()
        return None

    def detect_breaking_changes(self, new_contract_content: str, consumer: str, provider: str) -> List[str]:
        """Compare a new contract with the latest version in the registry."""
        old_json = self.get_contract(consumer, provider, "latest")
        if not old_json:
            return []

        old = json.loads(old_json)
        new = json.loads(new_contract_content)

        changes = []

        # Simple comparison: check if any existing interaction was removed or changed
        old_interactions = {i["description"]: i for i in old["interactions"]}
        new_interactions = {i["description"]: i for i in new["interactions"]}

        for desc, old_int in old_interactions.items():
            if desc not in new_interactions:
                changes.append(f"Breaking change: Interaction '{desc}' was removed.")
                continue

            new_int = new_interactions[desc]
            # Check if expected status changed
            if old_int["response"]["status"] != new_int["response"]["status"]:
                 changes.append(f"Breaking change in '{desc}': Expected status changed from {old_int['response']['status']} to {new_int['response']['status']}")

        return changes
