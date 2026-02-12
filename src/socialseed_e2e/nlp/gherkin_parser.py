"""Gherkin/Cucumber syntax parser for BDD-style test descriptions.

This module parses Gherkin feature files and converts them to test code.
"""

import re
from typing import List, Optional, Tuple

from socialseed_e2e.nlp.models import (
    GherkinFeature,
    GherkinScenario,
    Language,
)


class GherkinParser:
    """Parse Gherkin/Cucumber feature files."""

    KEYWORDS = {
        Language.ENGLISH: {
            "feature": "Feature:",
            "background": "Background:",
            "scenario": "Scenario:",
            "scenario_outline": "Scenario Outline:",
            "given": "Given",
            "when": "When",
            "then": "Then",
            "and": "And",
            "but": "But",
            "examples": "Examples:",
        },
        Language.SPANISH: {
            "feature": "Característica:",
            "background": "Antecedentes:",
            "scenario": "Escenario:",
            "scenario_outline": "Esquema del Escenario:",
            "given": "Dado",
            "when": "Cuando",
            "then": "Entonces",
            "and": "Y",
            "but": "Pero",
            "examples": "Ejemplos:",
        },
    }

    def __init__(self, language: Language = Language.ENGLISH):
        self.language = language
        self.keywords = self.KEYWORDS.get(language, self.KEYWORDS[Language.ENGLISH])

    def parse(self, feature_text: str) -> GherkinFeature:
        """Parse Gherkin feature text.

        Args:
            feature_text: Raw Gherkin feature text

        Returns:
            Parsed feature
        """
        lines = feature_text.strip().split("\n")

        # Parse feature header
        name, description, line_idx = self._parse_feature_header(lines)

        # Parse tags
        tags = self._parse_tags(lines, 0)

        # Parse background if present
        background, line_idx = self._parse_background(lines, line_idx)

        # Parse scenarios
        scenarios = []
        while line_idx < len(lines):
            scenario, line_idx = self._parse_scenario(lines, line_idx)
            if scenario:
                scenarios.append(scenario)
            else:
                line_idx += 1

        return GherkinFeature(
            name=name,
            description=description,
            background=background,
            scenarios=scenarios,
            tags=tags,
        )

    def _parse_feature_header(self, lines: List[str]) -> Tuple[str, str, int]:
        """Parse feature name and description.

        Args:
            lines: All lines

        Returns:
            Tuple of (name, description, next_line_index)
        """
        name = ""
        description = ""
        line_idx = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Check for feature keyword
            if stripped.startswith(self.keywords["feature"]):
                name = stripped[len(self.keywords["feature"]) :].strip()
                line_idx = i + 1

                # Collect description lines
                description_lines = []
                while line_idx < len(lines):
                    desc_line = lines[line_idx].strip()
                    if not desc_line or desc_line.startswith("#"):
                        line_idx += 1
                        continue
                    # Stop at next keyword
                    if any(
                        desc_line.startswith(kw)
                        for kw in [
                            self.keywords["background"],
                            self.keywords["scenario"],
                            self.keywords["scenario_outline"],
                        ]
                    ):
                        break
                    description_lines.append(desc_line)
                    line_idx += 1

                description = " ".join(description_lines)
                break

        return name, description, line_idx

    def _parse_tags(self, lines: List[str], start_idx: int) -> List[str]:
        """Parse tags from lines.

        Args:
            lines: All lines
            start_idx: Starting index

        Returns:
            List of tags
        """
        tags = []

        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if line.startswith("@"):
                tags.extend(tag.strip() for tag in line.split() if tag.startswith("@"))
            elif line and not line.startswith("#"):
                break

        return [tag[1:] for tag in tags]  # Remove @ prefix

    def _parse_background(
        self, lines: List[str], start_idx: int
    ) -> Tuple[Optional[str], int]:
        """Parse background section.

        Args:
            lines: All lines
            start_idx: Starting index

        Returns:
            Tuple of (background_steps, next_line_index)
        """
        line_idx = start_idx

        while line_idx < len(lines):
            line = lines[line_idx].strip()

            if line.startswith(self.keywords["background"]):
                line_idx += 1
                steps = []

                while line_idx < len(lines):
                    step_line = lines[line_idx].strip()
                    if not step_line or step_line.startswith("#"):
                        line_idx += 1
                        continue
                    # Stop at next section
                    if any(
                        step_line.startswith(kw)
                        for kw in [
                            self.keywords["scenario"],
                            self.keywords["scenario_outline"],
                        ]
                    ):
                        break
                    steps.append(step_line)
                    line_idx += 1

                return "\n".join(steps), line_idx

            line_idx += 1

        return None, start_idx

    def _parse_scenario(
        self, lines: List[str], start_idx: int
    ) -> Tuple[Optional[GherkinScenario], int]:
        """Parse a scenario.

        Args:
            lines: All lines
            start_idx: Starting index

        Returns:
            Tuple of (scenario, next_line_index)
        """
        line_idx = start_idx

        # Parse tags before scenario
        tags = self._parse_tags(lines, line_idx)

        while line_idx < len(lines):
            line = lines[line_idx].strip()

            if line.startswith(
                (self.keywords["scenario"], self.keywords["scenario_outline"])
            ):
                is_outline = line.startswith(self.keywords["scenario_outline"])
                name = line.split(":", 1)[1].strip() if ":" in line else line

                line_idx += 1
                given_steps = []
                when_steps = []
                then_steps = []
                and_steps = []
                examples = []
                current_section = None

                while line_idx < len(lines):
                    step_line = lines[line_idx].strip()

                    if not step_line or step_line.startswith("#"):
                        line_idx += 1
                        continue

                    # Check for next scenario or end
                    if step_line.startswith(
                        (self.keywords["scenario"], self.keywords["scenario_outline"])
                    ):
                        break

                    # Parse examples for scenario outline
                    if step_line.startswith(self.keywords["examples"]):
                        examples, line_idx = self._parse_examples(lines, line_idx + 1)
                        continue

                    # Parse steps
                    if step_line.startswith(self.keywords["given"]):
                        given_steps.append(
                            step_line[len(self.keywords["given"]) :].strip()
                        )
                        current_section = "given"
                    elif step_line.startswith(self.keywords["when"]):
                        when_steps.append(
                            step_line[len(self.keywords["when"]) :].strip()
                        )
                        current_section = "when"
                    elif step_line.startswith(self.keywords["then"]):
                        then_steps.append(
                            step_line[len(self.keywords["then"]) :].strip()
                        )
                        current_section = "then"
                    elif step_line.startswith(
                        (self.keywords["and"], self.keywords["but"])
                    ):
                        step_text = (
                            step_line[len(self.keywords["and"]) :].strip()
                            if step_line.startswith(self.keywords["and"])
                            else step_line[len(self.keywords["but"]) :].strip()
                        )
                        and_steps.append(step_text)

                        # Add to current section
                        if current_section == "given":
                            given_steps.append(step_text)
                        elif current_section == "when":
                            when_steps.append(step_text)
                        elif current_section == "then":
                            then_steps.append(step_text)
                    else:
                        # Unknown line, might be end of scenario
                        break

                    line_idx += 1

                scenario = GherkinScenario(
                    name=name,
                    given_steps=given_steps,
                    when_steps=when_steps,
                    then_steps=then_steps,
                    and_steps=and_steps,
                    examples=examples,
                    tags=tags,
                )
                return scenario, line_idx

            line_idx += 1

        return None, start_idx

    def _parse_examples(
        self, lines: List[str], start_idx: int
    ) -> Tuple[List[dict], int]:
        """Parse examples table.

        Args:
            lines: All lines
            start_idx: Starting index

        Returns:
            Tuple of (examples, next_line_index)
        """
        examples = []
        line_idx = start_idx
        headers = []

        while line_idx < len(lines):
            line = lines[line_idx].strip()

            if not line or line.startswith("#"):
                line_idx += 1
                continue

            # Parse header row
            if line.startswith("|") and not headers:
                headers = [h.strip() for h in line.split("|")[1:-1]]
                line_idx += 1
                continue

            # Parse data rows
            if line.startswith("|"):
                values = [v.strip() for v in line.split("|")[1:-1]]
                if len(values) == len(headers):
                    example = dict(zip(headers, values))
                    examples.append(example)
                line_idx += 1
            else:
                break

        return examples, line_idx


class GherkinWriter:
    """Write Gherkin feature files."""

    def __init__(self, language: Language = Language.ENGLISH):
        self.language = language
        self.parser = GherkinParser(language)
        self.keywords = self.parser.keywords

    def write(self, feature: GherkinFeature) -> str:
        """Write feature to Gherkin text.

        Args:
            feature: Feature to write

        Returns:
            Gherkin text
        """
        lines = []

        # Write tags
        if feature.tags:
            lines.append(" ".join(f"@{tag}" for tag in feature.tags))

        # Write feature header
        lines.append(f"{self.keywords['feature']} {feature.name}")
        if feature.description:
            lines.append("")
            for desc_line in feature.description.split("\n"):
                lines.append(f"  {desc_line}")

        lines.append("")

        # Write background
        if feature.background:
            lines.append(f"{self.keywords['background']}")
            for line in feature.background.split("\n"):
                lines.append(f"    {line}")
            lines.append("")

        # Write scenarios
        for scenario in feature.scenarios:
            lines.extend(self._write_scenario(scenario))
            lines.append("")

        return "\n".join(lines)

    def _write_scenario(self, scenario: GherkinScenario) -> List[str]:
        """Write a scenario.

        Args:
            scenario: Scenario to write

        Returns:
            List of lines
        """
        lines = []

        # Write tags
        if scenario.tags:
            lines.append("  " + " ".join(f"@{tag}" for tag in scenario.tags))

        # Write scenario header
        keyword = (
            self.keywords["scenario_outline"]
            if scenario.examples
            else self.keywords["scenario"]
        )
        lines.append(f"  {keyword} {scenario.name}")

        # Write steps
        for step in scenario.given_steps:
            lines.append(f"    {self.keywords['given']} {step}")

        for step in scenario.when_steps:
            lines.append(f"    {self.keywords['when']} {step}")

        for step in scenario.then_steps:
            lines.append(f"    {self.keywords['then']} {step}")

        # Write examples
        if scenario.examples:
            lines.append(f"    {self.keywords['examples']}")
            if scenario.examples:
                # Write header
                headers = list(scenario.examples[0].keys())
                lines.append("      | " + " | ".join(headers) + " |")

                # Write rows
                for example in scenario.examples:
                    values = [str(example.get(h, "")) for h in headers]
                    lines.append("      | " + " | ".join(values) + " |")

        return lines
