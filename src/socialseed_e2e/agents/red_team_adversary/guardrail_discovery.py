"""Guardrail Discovery Component.

Automatically identifies safety constraints and guardrails within
the system's prompts, documentation, and code.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from socialseed_e2e.agents.red_team_adversary.models import (
    GuardrailInfo,
    GuardrailType,
)


class GuardrailDiscovery:
    """Discovers and analyzes safety guardrails in the system."""

    # Patterns for detecting different types of guardrails
    GUARDRAIL_PATTERNS = {
        GuardrailType.INPUT_FILTER: [
            r"(?i)(filter|block|reject|sanitize|clean).*?(input|prompt|user|request)",
            r"(?i)(do not|don't|never|prohibit).*?(accept|process|allow)",
            r"(?i)if.*?(contains|has|matches).*?(reject|block|deny)",
        ],
        GuardrailType.OUTPUT_FILTER: [
            r"(?i)(filter|block|sanitize|clean).*?(output|response|result)",
            r"(?i)(do not|don't|never).*?(reveal|expose|leak|share)",
            r"(?i)if.*?(sensitive|private|confidential).*?(block|filter|remove)",
        ],
        GuardrailType.PROMPT_VALIDATION: [
            r"(?i)(validate|check|verify).*?(prompt|input|request)",
            r"(?i)(must|should|required).*?(format|structure|pattern)",
            r"(?i)(invalid|malformed|incorrect).*?(prompt|input)",
        ],
        GuardrailType.RATE_LIMITING: [
            r"(?i)(rate.?limit|throttle|quota|cooldown)",
            r"(?i)(max|maximum).*?(request|call|attempt).{0,20}(per|/|hour|minute|second)",
            r"(?i)(too many|excessive).*?(request|call|attempt)",
        ],
        GuardrailType.CONTENT_MODERATION: [
            r"(?i)(moderate|censor|flag|review).*?(content|text|message)",
            r"(?i)(inappropriate|offensive|harmful|toxic|unsafe)",
            r"(?i)(hate|violence|harassment|discrimination)",
        ],
        GuardrailType.AUTH_CHECK: [
            r"(?i)(authenticate|authorize|verify|check).*?(user|identity|permission|role)",
            r"(?i)(admin|root|privileged|authorized).{0,30}(only|required|necessary)",
            r"(?i)(unauthorized|unauthenticated|forbidden|denied)",
        ],
        GuardrailType.CONTEXT_ISOLATION: [
            r"(?i)(isolate|separate|sandbox|contain).*?(context|session|conversation)",
            r"(?i)(do not|don't|never).*?(access|read|use).*?(other|previous|external)",
            r"(?i)(context|session).{0,20}(isolated|separated|independent)",
        ],
    }

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.discovered_guardrails: List[GuardrailInfo] = []
        self.search_paths = [
            self.project_root / "docs",
            self.project_root / ".agent",
            self.project_root / "src",
            self.project_root / "services",
        ]

    def discover_all(self) -> List[GuardrailInfo]:
        """Discover all guardrails in the project."""
        self.discovered_guardrails = []

        # Search in documentation
        self._discover_in_documentation()

        # Search in code
        self._discover_in_code()

        # Search in prompts/templates
        self._discover_in_prompts()

        return self.discovered_guardrails

    def _discover_in_documentation(self) -> None:
        """Search for guardrails in documentation files."""
        doc_patterns = ["*.md", "*.txt", "*.rst"]

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            for pattern in doc_patterns:
                for doc_file in search_path.rglob(pattern):
                    content = doc_file.read_text(encoding="utf-8", errors="ignore")
                    self._analyze_content(
                        content, str(doc_file.relative_to(self.project_root))
                    )

    def _discover_in_code(self) -> None:
        """Search for guardrails in source code."""
        code_patterns = ["*.py", "*.js", "*.ts", "*.java", "*.go"]

        src_path = self.project_root / "src"
        if src_path.exists():
            for pattern in code_patterns:
                for code_file in src_path.rglob(pattern):
                    content = code_file.read_text(encoding="utf-8", errors="ignore")
                    self._analyze_content(
                        content, str(code_file.relative_to(self.project_root))
                    )

    def _discover_in_prompts(self) -> None:
        """Search for guardrails in prompt/template files."""
        prompt_paths = [
            self.project_root / "prompts",
            self.project_root / ".agent",
            self.project_root / "templates",
        ]

        for prompt_path in prompt_paths:
            if not prompt_path.exists():
                continue

            for prompt_file in prompt_path.rglob("*"):
                if prompt_file.is_file():
                    content = prompt_file.read_text(encoding="utf-8", errors="ignore")
                    self._analyze_content(
                        content, str(prompt_file.relative_to(self.project_root))
                    )

    def _analyze_content(self, content: str, location: str) -> None:
        """Analyze content for guardrail patterns."""
        for guardrail_type, patterns in self.GUARDRAIL_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    # Extract context around the match
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end].strip()

                    guardrail_id = (
                        f"gr_{guardrail_type.value}_{len(self.discovered_guardrails)}"
                    )

                    guardrail = GuardrailInfo(
                        guardrail_id=guardrail_id,
                        guardrail_type=guardrail_type,
                        description=self._extract_description(context),
                        location=location,
                        strength=self._estimate_strength(context),
                    )

                    # Avoid duplicates
                    if not self._is_duplicate(guardrail):
                        self.discovered_guardrails.append(guardrail)

    def _extract_description(self, context: str) -> str:
        """Extract a human-readable description from context."""
        # Clean up the context
        lines = context.split("\n")
        description = " ".join(line.strip() for line in lines if line.strip())

        # Limit length
        if len(description) > 200:
            description = description[:200] + "..."

        return description

    def _estimate_strength(self, context: str) -> int:
        """Estimate the strength of a guardrail based on context."""
        strength = 50  # Base strength

        # Increase strength for explicit validation
        if re.search(r"(?i)(strict|enforce|mandatory|required)", context):
            strength += 20

        # Increase for multiple checks
        if re.search(r"(?i)(and|&).*?(check|validate|verify)", context):
            strength += 15

        # Decrease for weak language
        if re.search(r"(?i)(try|attempt|should|might|optional)", context):
            strength -= 20

        # Increase for specific technical implementations
        if re.search(r"(?i)(regex|pattern|schema|validate)", context):
            strength += 10

        return max(0, min(100, strength))

    def _is_duplicate(self, guardrail: GuardrailInfo) -> bool:
        """Check if a similar guardrail already exists."""
        for existing in self.discovered_guardrails:
            if (
                existing.guardrail_type == guardrail.guardrail_type
                and existing.location == guardrail.location
                and self._similarity(existing.description, guardrail.description) > 0.8
            ):
                return True
        return False

    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def get_guardrails_by_type(
        self, guardrail_type: GuardrailType
    ) -> List[GuardrailInfo]:
        """Get all guardrails of a specific type."""
        return [
            g for g in self.discovered_guardrails if g.guardrail_type == guardrail_type
        ]

    def get_vulnerable_guardrails(self) -> List[GuardrailInfo]:
        """Get guardrails with low strength scores."""
        return [g for g in self.discovered_guardrails if g.strength < 50]

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of discovered guardrails."""
        by_type = {}
        for guardrail_type in GuardrailType:
            by_type[guardrail_type.value] = len(
                self.get_guardrails_by_type(guardrail_type)
            )

        return {
            "total_guardrails": len(self.discovered_guardrails),
            "by_type": by_type,
            "vulnerable_count": len(self.get_vulnerable_guardrails()),
            "average_strength": (
                sum(g.strength for g in self.discovered_guardrails)
                / len(self.discovered_guardrails)
                if self.discovered_guardrails
                else 0
            ),
        }
