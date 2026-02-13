"""Deep Context Awareness for AI Agents.

This module integrates all deep context awareness capabilities:
- Semantic Codebase Understanding
- Business Logic Inference
- User Behavior Pattern Learning
- API Relationship Mapping
- Domain Model Understanding
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from socialseed_e2e.project_manifest.behavior_learner import UserBehaviorLearner
from socialseed_e2e.project_manifest.business_logic_inference import (
    BusinessLogicInferenceEngine,
)
from socialseed_e2e.project_manifest.domain_understanding import (
    DomainModelUnderstanding,
)
from socialseed_e2e.project_manifest.models import ProjectKnowledge, ServiceInfo
from socialseed_e2e.project_manifest.relationship_mapper import APIRelationshipMapper
from socialseed_e2e.project_manifest.semantic_analyzer import SemanticCodebaseAnalyzer


@dataclass
class DeepContext:
    """Complete deep context understanding."""

    project_root: Path
    manifest: Optional[ProjectKnowledge] = None
    semantic_context: Optional[Any] = None
    business_logic: Optional[Any] = None
    behavior_profile: Optional[Any] = None
    api_relationships: Optional[Any] = None
    domain_model: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeepContextAwarenessEngine:
    """Engine for deep context awareness.

    This engine integrates multiple analyzers to provide comprehensive
    understanding of the project context beyond the basic manifest.
    """

    def __init__(self, project_root: Path, manifest: Optional[ProjectKnowledge] = None):
        """Initialize the deep context awareness engine.

        Args:
            project_root: Root directory of the project
            manifest: Optional existing project manifest
        """
        self.project_root = Path(project_root)
        self.manifest = manifest
        self.context = DeepContext(project_root=project_root, manifest=manifest)

        # Initialize analyzers
        self.semantic_analyzer = SemanticCodebaseAnalyzer(project_root)
        self.behavior_learner = UserBehaviorLearner()
        self.domain_understanding = DomainModelUnderstanding(project_root)

    def analyze(self, include_behavior: bool = True) -> DeepContext:
        """Run complete deep context analysis.

        Args:
            include_behavior: Whether to include behavior learning

        Returns:
            DeepContext with all analysis results
        """
        # 1. Semantic Analysis
        self.context.semantic_context = self.semantic_analyzer.analyze()

        # 2. Business Logic Inference
        if self.manifest:
            self.context.business_logic = self._analyze_business_logic()

        # 3. API Relationship Mapping
        if self.manifest:
            self.context.api_relationships = self._map_api_relationships()

        # 4. Domain Model Understanding
        self.context.domain_model = self.domain_understanding.analyze()

        # 5. Behavior Learning (if enabled)
        if include_behavior:
            self.context.behavior_profile = (
                self.behavior_learner.get_learned_preferences()
            )

        # 6. Build comprehensive metadata
        self.context.metadata = self._build_metadata()

        return self.context

    def _analyze_business_logic(self) -> Any:
        """Analyze business logic using the manifest."""
        all_endpoints = []
        all_dtos = []

        for service in self.manifest.services:
            all_endpoints.extend(service.endpoints)
            all_dtos.extend(service.dto_schemas)

        if all_endpoints:
            engine = BusinessLogicInferenceEngine(all_endpoints, all_dtos)
            return engine.analyze()

        return None

    def _map_api_relationships(self) -> Any:
        """Map API relationships."""
        if self.manifest.services:
            mapper = APIRelationshipMapper(self.manifest.services)
            return mapper.map_relationships()

        return None

    def _build_metadata(self) -> Dict[str, Any]:
        """Build comprehensive metadata about the context."""
        metadata = {
            "analysis_timestamp": str(Path(__file__).stat().st_mtime),
            "project_root": str(self.project_root),
            "has_manifest": self.manifest is not None,
        }

        # Add semantic analysis summary
        if self.context.semantic_context:
            metadata["semantic_summary"] = self.semantic_analyzer.get_domain_summary()

        # Add domain model summary
        if self.context.domain_model:
            metadata["domain_summary"] = self.domain_understanding.get_domain_summary()

        # Add relationship summary
        if self.context.api_relationships:
            metadata["relationship_summary"] = self.context.api_relationships.get(
                "summary", {}
            )

        # Add behavior summary
        if self.context.behavior_profile:
            metadata["behavior_summary"] = {
                "preferred_test_types": self.context.behavior_profile.get(
                    "preferred_test_types", []
                ),
                "focus_areas": self.context.behavior_profile.get("focus_areas", []),
            }

        return metadata

    def get_context_for_generation(self) -> Dict[str, Any]:
        """Get context optimized for test generation.

        Returns:
            Dictionary with generation context
        """
        context = {
            "project_root": str(self.project_root),
            "semantic_understanding": {},
            "business_flows": [],
            "api_dependencies": [],
            "domain_elements": [],
            "behavior_hints": {},
        }

        # Add semantic understanding
        if self.context.semantic_context:
            context["semantic_understanding"] = {
                "domain_concepts": [
                    {"name": c.name, "type": c.concept_type}
                    for c in self.context.semantic_context.domain_concepts[:10]
                ],
                "business_rules": [
                    {"description": r.description, "type": r.rule_type}
                    for r in self.context.semantic_context.business_rules[:10]
                ],
                "patterns": [
                    {"type": p.pattern_type.value, "description": p.description}
                    for p in self.context.semantic_context.patterns
                ],
            }

        # Add business flows
        if self.context.business_logic:
            context["business_flows"] = [
                {
                    "name": flow.name,
                    "type": flow.flow_type.value,
                    "steps": [step.endpoint.name for step in flow.steps],
                }
                for flow in self.context.business_logic.get("flows", [])[:5]
            ]

        # Add API dependencies
        if self.context.api_relationships:
            deps = self.context.api_relationships.get("dependencies", [])
            context["api_dependencies"] = [
                {
                    "source": d.source_endpoint,
                    "target": d.target_endpoint,
                    "type": d.category.value,
                    "strength": d.strength.value,
                }
                for d in deps[:10]
            ]

        # Add domain elements
        if self.context.domain_model:
            context["domain_elements"] = [
                {"name": e.name, "type": e.element_type.value}
                for e in self.context.domain_model.elements[:10]
            ]

        # Add behavior hints
        if self.context.behavior_profile:
            context["behavior_hints"] = (
                self.behavior_learner.get_test_generation_hints()
            )

        return context

    def get_recommendations(self) -> List[Dict[str, str]]:
        """Get recommendations based on deep context.

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        # Semantic recommendations
        if self.context.semantic_context:
            patterns = self.context.semantic_context.patterns
            if patterns:
                recommendations.append(
                    {
                        "category": "architecture",
                        "message": f"Detected {len(patterns)} architectural patterns - consider pattern-based test generation",
                    }
                )

        # Business logic recommendations
        if self.context.business_logic:
            flows = self.context.business_logic.get("flows", [])
            if flows:
                recommendations.append(
                    {
                        "category": "testing",
                        "message": f"Detected {len(flows)} business flows - prioritize flow-based testing",
                    }
                )

        # Domain model recommendations
        if self.context.domain_model:
            aggregates = self.domain_understanding.get_aggregate_roots()
            if aggregates:
                recommendations.append(
                    {
                        "category": "domain",
                        "message": f"Found {len(aggregates)} aggregate roots - test transactional boundaries",
                    }
                )

        # Behavior recommendations
        if self.context.behavior_profile:
            prefs = self.context.behavior_profile.get("preferred_test_types", [])
            if prefs:
                recommendations.append(
                    {
                        "category": "preferences",
                        "message": f"User prefers {', '.join(prefs[:3])} tests - align generation accordingly",
                    }
                )

        return recommendations

    def export_context_report(self, output_path: Path) -> None:
        """Export a comprehensive context report.

        Args:
            output_path: Path to save the report
        """
        report = {
            "project_root": str(self.project_root),
            "analysis_summary": self.context.metadata,
            "generation_context": self.get_context_for_generation(),
            "recommendations": self.get_recommendations(),
        }

        with open(output_path, "w") as f:
            import json

            json.dump(report, f, indent=2, default=str)

    def save(self) -> None:
        """Save all learned data."""
        self.behavior_learner.save()
