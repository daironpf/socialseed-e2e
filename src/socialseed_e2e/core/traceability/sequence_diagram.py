"""Sequence diagram generator for test execution traces.

This module generates Mermaid.js and PlantUML sequence diagrams
from test execution traces.
"""

from datetime import datetime
from typing import List, Optional

from socialseed_e2e.core.traceability.models import (
    Component,
    Interaction,
    InteractionType,
    SequenceDiagram,
    TestTrace,
)


class SequenceDiagramGenerator:
    """Generator for sequence diagrams from test traces.

    This class generates Mermaid.js and PlantUML sequence diagrams
    that visualize the interactions between components during test execution.

    Example:
        >>> generator = SequenceDiagramGenerator()
        >>> trace = collector.get_current_trace()
        >>> diagram = generator.generate_mermaid(trace, title="Login Flow")
        >>> print(diagram.content)
    """

    # Default component type mappings for styling
    COMPONENT_STYLES = {
        "client": {"shape": "Actor", "color": "#e1f5fe"},
        "gateway": {"shape": "participant", "color": "#fff3e0"},
        "service": {"shape": "participant", "color": "#e8f5e9"},
        "database": {"shape": "database", "color": "#fce4ec"},
        "cache": {"shape": "participant", "color": "#f3e5f5"},
        "external": {"shape": "participant", "color": "#e0e0e0"},
        "auth": {"shape": "participant", "color": "#fff9c4"},
    }

    def __init__(self):
        """Initialize the sequence diagram generator."""
        self._participant_aliases: dict = {}

    def generate_mermaid(
        self,
        trace: TestTrace,
        title: Optional[str] = None,
        include_timestamps: bool = True,
        include_duration: bool = True,
        group_by_service: bool = False,
    ) -> SequenceDiagram:
        """Generate a Mermaid.js sequence diagram.

        Args:
            trace: The test trace to visualize
            title: Optional diagram title
            include_timestamps: Whether to include timestamps
            include_duration: Whether to include duration
            group_by_service: Whether to group interactions by service

        Returns:
            SequenceDiagram with Mermaid.js content
        """
        lines = ["sequenceDiagram"]

        diagram_title = title or f"{trace.test_name} - {trace.service_name}"

        # Reset aliases for this diagram
        self._participant_aliases = {}

        # Get unique components in order of appearance
        components = self._get_ordered_components(trace)

        # Handle empty trace - add a default participant
        if not components:
            from socialseed_e2e.core.traceability.models import Component

            components = [Component(name="Test", type="client")]

        # Add participant declarations with styling
        for component in components:
            participant_line = self._create_participant_declaration(component)
            lines.append(f"    {participant_line}")

        # Add title if provided
        if diagram_title:
            lines.append(f"    Note over {components[0].name}: {diagram_title}")

        # Add test start note
        start_time_str = trace.start_time.strftime("%H:%M:%S.%f")[:-3]
        lines.append(f"    Note right of {components[0].name}: Test started at {start_time_str}")

        # Group interactions if requested
        if group_by_service and trace.interactions:
            current_service = None
            for interaction in trace.interactions:
                if interaction.to_component != current_service:
                    if current_service:
                        lines.append("    end")
                    current_service = interaction.to_component
                    lines.append("    rect rgb(230, 245, 255)")
                    lines.append(
                        f"    Note over {interaction.from_component},{interaction.to_component}: {current_service}"
                    )
                lines.extend(
                    self._create_interaction_lines(
                        interaction, include_timestamps, include_duration
                    )
                )
            if current_service:
                lines.append("    end")
        else:
            # Add interactions
            for interaction in trace.interactions:
                lines.extend(
                    self._create_interaction_lines(
                        interaction, include_timestamps, include_duration
                    )
                )

        # Add test end note
        if trace.end_time:
            end_time_str = trace.end_time.strftime("%H:%M:%S.%f")[:-3]
            status_emoji = "✓" if trace.status == "passed" else "✗"
            lines.append(
                f"    Note right of {components[0].name}: {status_emoji} Test {trace.status} at {end_time_str}"
            )

        # Add component list
        component_names = [c.name for c in components]

        content = "\n".join(lines)

        return SequenceDiagram(
            title=diagram_title,
            format="mermaid",
            content=content,
            components=component_names,
            interactions_count=len(trace.interactions),
            generated_at=datetime.now(),
        )

    def generate_plantuml(
        self,
        trace: TestTrace,
        title: Optional[str] = None,
        include_timestamps: bool = True,
        include_duration: bool = True,
    ) -> SequenceDiagram:
        """Generate a PlantUML sequence diagram.

        Args:
            trace: The test trace to visualize
            title: Optional diagram title
            include_timestamps: Whether to include timestamps
            include_duration: Whether to include duration

        Returns:
            SequenceDiagram with PlantUML content
        """
        lines = ["@startuml"]

        diagram_title = title or f"{trace.test_name} - {trace.service_name}"
        lines.append(f"title {diagram_title}")

        # Reset aliases for this diagram
        self._participant_aliases = {}

        # Get unique components in order of appearance
        components = self._get_ordered_components(trace)

        # Add participant declarations
        for component in components:
            participant_line = self._create_plantuml_participant(component)
            lines.append(participant_line)

        # Add test start
        start_time_str = trace.start_time.strftime("%H:%M:%S.%f")[:-3]
        lines.append(f"note right: Test started at {start_time_str}")

        # Add interactions
        for interaction in trace.interactions:
            lines.extend(
                self._create_plantuml_interaction_lines(
                    interaction, include_timestamps, include_duration
                )
            )

        # Add test end
        if trace.end_time:
            end_time_str = trace.end_time.strftime("%H:%M:%S.%f")[:-3]
            status = "PASSED" if trace.status == "passed" else "FAILED"
            lines.append(f"note right: Test {status} at {end_time_str}")

        lines.append("@enduml")

        # Add component list
        component_names = [c.name for c in components]

        content = "\n".join(lines)

        return SequenceDiagram(
            title=diagram_title,
            format="plantuml",
            content=content,
            components=component_names,
            interactions_count=len(trace.interactions),
            generated_at=datetime.now(),
        )

    def generate_both(
        self,
        trace: TestTrace,
        title: Optional[str] = None,
        include_timestamps: bool = True,
        include_duration: bool = True,
    ) -> List[SequenceDiagram]:
        """Generate both Mermaid.js and PlantUML diagrams.

        Args:
            trace: The test trace to visualize
            title: Optional diagram title
            include_timestamps: Whether to include timestamps
            include_duration: Whether to include duration

        Returns:
            List containing both SequenceDiagram instances
        """
        return [
            self.generate_mermaid(trace, title, include_timestamps, include_duration),
            self.generate_plantuml(trace, title, include_timestamps, include_duration),
        ]

    def _get_ordered_components(self, trace: TestTrace) -> List[Component]:
        """Get components in order of first appearance.

        Args:
            trace: Test trace

        Returns:
            List of components ordered by first appearance
        """
        seen = set()
        ordered = []

        # First, add components from interactions in order
        for interaction in trace.interactions:
            for component_name in [
                interaction.from_component,
                interaction.to_component,
            ]:
                if component_name not in seen:
                    seen.add(component_name)
                    # Find component in trace components or create default
                    component = next(
                        (c for c in trace.components if c.name == component_name),
                        Component(name=component_name, type="service"),
                    )
                    ordered.append(component)

        # Add any remaining components from trace.components
        for component in trace.components:
            if component.name not in seen:
                ordered.append(component)

        return ordered

    def _create_participant_declaration(self, component: Component) -> str:
        """Create a Mermaid participant declaration with appropriate styling.

        Args:
            component: Component to declare

        Returns:
            Mermaid participant declaration
        """
        style = self.COMPONENT_STYLES.get(
            component.type.lower(), {"shape": "participant", "color": "#ffffff"}
        )

        # Create safe alias for component name
        alias = self._get_safe_alias(component.name)

        shape = style["shape"]
        if shape == "Actor":
            return f"actor {component.name} as {alias}"
        elif shape == "database":
            return f"database {component.name} as {alias}"
        else:
            return f"participant {component.name} as {alias}"

    def _create_plantuml_participant(self, component: Component) -> str:
        """Create a PlantUML participant declaration.

        Args:
            component: Component to declare

        Returns:
            PlantUML participant declaration
        """
        alias = self._get_safe_alias(component.name)

        if component.type.lower() == "database":
            return f'database "{component.name}" as {alias}'
        elif component.type.lower() == "actor":
            return f'actor "{component.name}" as {alias}'
        else:
            return f'participant "{component.name}" as {alias}'

    def _get_safe_alias(self, name: str) -> str:
        """Create a safe alias for component names.

        Args:
            name: Original component name

        Returns:
            Safe alias for use in diagrams
        """
        if name not in self._participant_aliases:
            # Replace spaces and special characters
            safe_name = name.replace(" ", "_").replace("-", "_")
            self._participant_aliases[name] = safe_name
        return self._participant_aliases[name]

    def _create_interaction_lines(
        self, interaction: Interaction, include_timestamps: bool, include_duration: bool
    ) -> List[str]:
        """Create Mermaid lines for an interaction.

        Args:
            interaction: Interaction to visualize
            include_timestamps: Whether to include timestamps
            include_duration: Whether to include duration

        Returns:
            List of Mermaid lines
        """
        lines = []

        from_alias = self._get_safe_alias(interaction.from_component)
        to_alias = self._get_safe_alias(interaction.to_component)

        # Create arrow based on status
        if interaction.status == "error":
            arrow = "--x"  # X for error
        elif interaction.status == "warning":
            arrow = "-->>"  # Dashed for warning
        else:
            arrow = "->>"  # Solid for success

        # Build action label
        action_label = interaction.action

        # Add duration if requested
        if include_duration and interaction.duration_ms > 0:
            action_label += f" ({interaction.duration_ms:.0f}ms)"

        # Add main interaction line
        lines.append(f"    {from_alias}{arrow}{to_alias}: {action_label}")

        # Add activation if it's a request-response
        if interaction.type == InteractionType.HTTP_REQUEST:
            lines.append(f"    activate {to_alias}")

        # Add note with details if there's data or errors
        if interaction.error_message:
            lines.append(f"    Note right of {to_alias}: Error: {interaction.error_message}")
        elif interaction.response_data and "status" in str(interaction.response_data):
            status = interaction.response_data.get("status", "?")
            lines.append(f"    Note right of {to_alias}: Status: {status}")

        # Add timestamp note if requested
        if include_timestamps:
            time_str = interaction.timestamp.strftime("%H:%M:%S.%f")[:-3]
            lines.append(f"    Note left of {from_alias}: {time_str}")

        # Deactivate after response
        if interaction.type == InteractionType.HTTP_REQUEST:
            lines.append(f"    deactivate {to_alias}")

        return lines

    def _create_plantuml_interaction_lines(
        self, interaction: Interaction, include_timestamps: bool, include_duration: bool
    ) -> List[str]:
        """Create PlantUML lines for an interaction.

        Args:
            interaction: Interaction to visualize
            include_timestamps: Whether to include timestamps
            include_duration: Whether to include duration

        Returns:
            List of PlantUML lines
        """
        lines = []

        from_alias = self._get_safe_alias(interaction.from_component)
        to_alias = self._get_safe_alias(interaction.to_component)

        # Build action label
        action_label = interaction.action

        # Add duration if requested
        if include_duration and interaction.duration_ms > 0:
            action_label += f"\\n({interaction.duration_ms:.0f}ms)"

        # Add main interaction line
        lines.append(f"{from_alias} -> {to_alias}: {action_label}")

        # Add activation
        lines.append(f"activate {to_alias}")

        # Add response line for HTTP interactions
        if interaction.type == InteractionType.HTTP_REQUEST:
            status = "OK"
            if interaction.response_data and isinstance(interaction.response_data, dict):
                status = interaction.response_data.get("status", "OK")
            lines.append(f"{to_alias} --> {from_alias}: {status}")

        # Add note with error if present
        if interaction.error_message:
            lines.append(f"note right: Error: {interaction.error_message}")

        # Deactivate
        lines.append(f"deactivate {to_alias}")

        return lines
