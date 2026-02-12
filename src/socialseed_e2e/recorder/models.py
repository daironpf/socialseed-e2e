"""Models for recorded test sessions."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RecordedInteraction:
    """Represents a single recorded API interaction."""

    timestamp: datetime
    method: str
    url: str
    request_headers: Dict[str, str]
    request_body: Optional[Any] = None
    response_status: int = 200
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_body: Optional[Any] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert interaction to a dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "url": self.url,
            "request": {
                "headers": self.request_headers,
                "body": self.request_body,
            },
            "response": {
                "status": self.response_status,
                "headers": self.response_headers,
                "body": self.response_body,
            },
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecordedInteraction":
        """Create an interaction from a dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            method=data["method"],
            url=data["url"],
            request_headers=data["request"]["headers"],
            request_body=data["request"]["body"],
            response_status=data["response"]["status"],
            response_headers=data["response"]["headers"],
            response_body=data["response"]["body"],
            duration_ms=data.get("duration_ms", 0.0),
        )


@dataclass
class RecordedSession:
    """Represents a collection of recorded interactions."""

    name: str
    created_at: datetime = field(default_factory=datetime.now)
    interactions: List[RecordedInteraction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to a dictionary."""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "interactions": [i.to_dict() for i in self.interactions],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecordedSession":
        """Create a session from a dictionary."""
        return cls(
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            interactions=[RecordedInteraction.from_dict(i) for i in data["interactions"]],
            metadata=data.get("metadata", {}),
        )

    def save(self, path: str):
        """Save session to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "RecordedSession":
        """Load session from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
            return cls.from_dict(data)
