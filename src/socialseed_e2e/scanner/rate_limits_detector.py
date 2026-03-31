"""Rate limits detector for identifying API rate limiting.

This module detects rate limits and generates test templates.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RateLimit:
    """Represents a rate limit configuration."""

    endpoint: str
    limit: int
    window: str  # "second", "minute", "hour"
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class RateLimitInfo:
    """Represents rate limit information."""

    limits: List[RateLimit] = field(default_factory=list)
    global_limits: Dict[str, Any] = field(default_factory=dict)


class RateLimitDetector:
    """Detects rate limits."""

    RATE_LIMIT_PATTERNS = [
        r"rate.limit",
        r"ratelimit",
        r"rate_limit",
        r"max.requests",
        r"throttle",
        r"@RateLimiter",
        r"@Throttle",
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def detect(self) -> RateLimitInfo:
        """Detect rate limits."""
        info = RateLimitInfo()

        self._scan_code_for_limits(info)
        self._scan_config_for_limits(info)

        return info

    def _scan_code_for_limits(self, info: RateLimitInfo) -> None:
        """Scan code for rate limit annotations."""
        for ext in [".py", ".js", ".ts", ".java"]:
            for file_path in self.project_root.rglob(f"*{ext}"):
                try:
                    content = file_path.read_text(errors="ignore")
                    
                    limit_patterns = [
                        r"@RateLimiter\(.*?value\s*=\s*(\d+)",
                        r"rate\s*limit\s*[:=]\s*(\d+)",
                        r"max.*?requests\s*[:=]\s*(\d+)",
                    ]
                    
                    for pattern in limit_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            try:
                                limit = int(match.group(1))
                                info.limits.append(RateLimit(
                                    endpoint="*",
                                    limit=limit,
                                    window="minute",
                                ))
                            except (ValueError, IndexError):
                                pass
                except Exception:
                    pass

    def _scan_config_for_limits(self, info: RateLimitInfo) -> None:
        """Scan config for rate limits."""
        conf_files = list(self.project_root.glob("*.conf")) + list(self.project_root.glob("*.yml"))
        
        for conf_file in conf_files:
            content = conf_file.read_text(errors="ignore")
            
            rate_pattern = r"rate.*?limit\s*[:=]\s*(\d+)"
            matches = re.finditer(rate_pattern, content, re.IGNORECASE)
            
            for match in matches:
                try:
                    limit = int(match.group(1))
                    info.limits.append(RateLimit(
                        endpoint="global",
                        limit=limit,
                        window="minute",
                    ))
                except (ValueError, IndexError):
                    pass


def generate_rate_limits_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate RATE_LIMITS.md document."""
    detector = RateLimitDetector(project_root)
    info = detector.detect()

    doc = "# Rate Limits\n\n"

    if info.limits:
        doc += "## Límites Detectados\n\n"
        doc += "| Endpoint | Límite | Ventana |\n"
        doc += "|----------|--------|---------|\n"
        for limit in info.limits:
            doc += f"| {limit.endpoint} | {limit.limit} | {limit.window} |\n"
        doc += "\n"
    else:
        doc += "No se detectaron rate limits específicos.\n\n"

    doc += "---\n\n"
    doc += "## Tests de Rate Limiting\n\n"
    doc += "```python\n"
    doc += "def test_rate_limit(page):\n"
    doc += "    \"\"\"Test: Verificar que se aplica el rate limit\"\"\"\n"
    doc += "    responses = []\n"
    doc += "    for _ in range(100):\n"
    doc += "        response = page.get(\"/api/data\")\n"
    doc += "        responses.append(response.status)\n"
    doc += "    \n"
    doc += "    # Verificar 429 Too Many Requests\n"
    doc += "    assert 429 in responses, \"Rate limit should be enforced\"\n"
    doc += "```\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_rate_limits_doc(project_root))
    else:
        print("Usage: python rate_limits_detector.py <project_root>")
