"""Consumer-side contract definition for socialseed-e2e."""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Interaction:
    description: str
    provider_state: str
    request: Dict[str, Any]
    response: Dict[str, Any]


@dataclass
class Contract:
    consumer: str
    provider: str
    interactions: List[Interaction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat()
    })


class ConsumerContract:
    """DSL for defining consumer contracts."""

    def __init__(self, consumer_name: str, provider_name: str):
        self.contract = Contract(consumer=consumer_name, provider=provider_name)
        self._current_interaction: Optional[Interaction] = None

    def given(self, provider_state: str):
        """Define the state the provider should be in."""
        self._temp_state = provider_state
        return self

    def upon_receiving(self, description: str):
        """Description of the request being made."""
        self._temp_description = description
        return self

    def with_request(self, method: str, path: str, headers: Optional[Dict] = None, body: Any = None):
        """Define the expected request."""
        self._temp_request = {
            "method": method.upper(),
            "path": path,
            "headers": headers or {},
            "body": body
        }
        return self

    def will_respond_with(self, status: int, headers: Optional[Dict] = None, body: Any = None):
        """Define the expected response."""
        interaction = Interaction(
            description=self._temp_description,
            provider_state=self._temp_state,
            request=self._temp_request,
            response={
                "status": status,
                "headers": headers or {},
                "body": body
            }
        )
        self.contract.interactions.append(interaction)
        return self

    def to_json(self) -> str:
        """Export contract to JSON string."""
        return json.dumps(asdict(self.contract), indent=4)

    def save(self, directory: str = ".e2e/contracts"):
        """Save contract to a file."""
        import os
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        filename = f"{self.contract.consumer}-{self.contract.provider}.json"
        path = os.path.join(directory, filename)
        with open(path, "w") as f:
            f.write(self.to_json())
        print(f"Contract saved to {path}")
