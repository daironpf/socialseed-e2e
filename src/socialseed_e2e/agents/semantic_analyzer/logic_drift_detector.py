"""Logic Drift Detector.

Uses LLM-based reasoning to detect if changes in system behavior represent
semantic drift from the intended business logic.
"""

import json
import re
from typing import Any, Dict, List, Optional
import uuid

from models import (
    DriftSeverity,
    DriftType,
    IntentBaseline,
    LogicDrift,
    StateSnapshot,
)


class LogicDriftDetector:
    """Detects semantic logic drift using LLM-based reasoning."""

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
        self.detected_drifts: List[LogicDrift] = []

    def detect_drift(
        self,
        intent_baselines: List[IntentBaseline],
        before_state: StateSnapshot,
        after_state: StateSnapshot,
        code_diff: Optional[str] = None,
    ) -> List[LogicDrift]:
        """Detect logic drift by comparing states against intent baselines."""
        self.detected_drifts = []

        for intent in intent_baselines:
            # Check if this intent is affected by changes
            affected_endpoints = self._find_affected_endpoints(intent, before_state)

            if not affected_endpoints:
                continue

            # Analyze each affected endpoint
            for endpoint in affected_endpoints:
                before_api = before_state.get_api_snapshot(endpoint)
                after_api = after_state.get_api_snapshot(endpoint)

                if not before_api or not after_api:
                    continue

                # Detect drift for this intent and endpoint
                drift = self._analyze_drift(
                    intent=intent,
                    before_api=before_api,
                    after_api=after_api,
                    code_diff=code_diff,
                )

                if drift:
                    self.detected_drifts.append(drift)

        # Also check for structural changes in database
        db_drifts = self._detect_database_drifts(
            intent_baselines, before_state, after_state
        )
        self.detected_drifts.extend(db_drifts)

        return self.detected_drifts

    def _find_affected_endpoints(
        self, intent: IntentBaseline, state: StateSnapshot
    ) -> List[str]:
        """Find API endpoints potentially affected by this intent."""
        affected = []

        # Extract entity names from intent
        intent_text = (intent.description + " " + intent.expected_behavior).lower()

        for api_snapshot in state.api_snapshots:
            endpoint = api_snapshot.endpoint.lower()

            # Check if endpoint relates to intent
            # Simple keyword matching - can be enhanced with semantic similarity
            if any(entity.lower() in endpoint for entity in intent.related_entities):
                affected.append(api_snapshot.endpoint)
            elif any(keyword in endpoint for keyword in intent_text.split()):
                affected.append(api_snapshot.endpoint)

        return list(set(affected))

    def _analyze_drift(
        self,
        intent: IntentBaseline,
        before_api: Any,
        after_api: Any,
        code_diff: Optional[str],
    ) -> Optional[LogicDrift]:
        """Analyze if changes represent logic drift from intent."""
        # Check for obvious issues first

        # 1. Status code regression
        if before_api.response_status < 400 and after_api.response_status >= 400:
            return self._create_drift(
                intent=intent,
                drift_type=DriftType.BEHAVIORAL,
                severity=DriftSeverity.HIGH,
                description=f"Endpoint {after_api.endpoint} now returns error status {after_api.response_status}",
                affected_endpoints=[after_api.endpoint],
                reasoning="Previously working endpoint now returns error status",
                evidence=[
                    {"before_status": before_api.response_status},
                    {"after_status": after_api.response_status},
                ],
            )

        # 2. Response structure changes
        if type(before_api.response_body) != type(after_api.response_body):
            return self._create_drift(
                intent=intent,
                drift_type=DriftType.BEHAVIORAL,
                severity=DriftSeverity.HIGH,
                description=f"Response structure changed for {after_api.endpoint}",
                affected_endpoints=[after_api.endpoint],
                reasoning="Response type changed significantly",
                evidence=[
                    {"before_type": type(before_api.response_body).__name__},
                    {"after_type": type(after_api.response_body).__name__},
                ],
            )

        # 3. Check against success criteria
        for criterion in intent.success_criteria:
            if not self._verify_criterion(criterion, after_api.response_body):
                return self._create_drift(
                    intent=intent,
                    drift_type=DriftType.BUSINESS_RULE,
                    severity=DriftSeverity.CRITICAL,
                    description=f"Success criterion not met: {criterion}",
                    affected_endpoints=[after_api.endpoint],
                    reasoning=f"Expected behavior '{intent.expected_behavior}' not satisfied",
                    evidence=[
                        {"criterion": criterion},
                        {"response": after_api.response_body},
                    ],
                )

        # 4. Use LLM for semantic analysis if available
        if self.llm_client:
            llm_drift = self._llm_based_drift_analysis(
                intent, before_api, after_api, code_diff
            )
            if llm_drift:
                return llm_drift

        return None

    def _llm_based_drift_analysis(
        self,
        intent: IntentBaseline,
        before_api: Any,
        after_api: Any,
    ) -> Optional[LogicDrift]:
        """Use LLM to detect subtle semantic drift."""
        # This is a placeholder for LLM integration
        # In a real implementation, this would call an LLM API

        prompt = f"""
        Analyze whether the following API change represents a semantic drift from the intended behavior.
        
        Intent: {intent.description}
        Expected Behavior: {intent.expected_behavior}
        Success Criteria: {intent.success_criteria}
        
        Before:
        - Endpoint: {before_api.endpoint}
        - Status: {before_api.response_status}
        - Response: {json.dumps(before_api.response_body, indent=2)[:500]}
        
        After:
        - Endpoint: {after_api.endpoint}
        - Status: {after_api.response_status}
        - Response: {json.dumps(after_api.response_body, indent=2)[:500]}
        
        Does this change violate the intended behavior? If yes, explain why and classify the severity.
        """

        # Placeholder: In real implementation, call LLM
        # response = self.llm_client.complete(prompt)

        return None

    def _detect_database_drifts(
        self,
        intent_baselines: List[IntentBaseline],
        before_state: StateSnapshot,
        after_state: StateSnapshot,
    ) -> List[LogicDrift]:
        """Detect drift in database states."""
        drifts = []

        for before_db in before_state.database_snapshots:
            after_db = self._find_matching_db(after_state, before_db.database_type)

            if not after_db:
                continue

            # Check relationship integrity (especially for graph databases)
            if before_db.database_type == "neo4j":
                relationship_drifts = self._analyze_relationship_drifts(
                    intent_baselines, before_db, after_db
                )
                drifts.extend(relationship_drifts)

            # Check entity count changes
            for entity, before_data in before_db.entities.items():
                after_data = after_db.entities.get(entity, [])

                if len(before_data) != len(after_data):
                    # Check if this is expected based on intent
                    drift = self._check_entity_count_drift(
                        intent_baselines, entity, len(before_data), len(after_data)
                    )
                    if drift:
                        drifts.append(drift)

        return drifts

    def _analyze_relationship_drifts(
        self,
        intent_baselines: List[IntentBaseline],
        before_db: Any,
        after_db: Any,
    ) -> List[LogicDrift]:
        """Analyze relationship changes in graph databases."""
        drifts = []

        # Check for missing reciprocal relationships
        # Example: "follow" action should create reciprocal relationship
        before_rels = {
            (r["from"], r["relationship"], r["to"]) for r in before_db.relationships
        }
        after_rels = {
            (r["from"], r["relationship"], r["to"]) for r in after_db.relationships
        }

        missing_rels = before_rels - after_rels

        for rel in missing_rels:
            from_node, rel_type, to_node = rel

            # Check if this relates to any intent
            for intent in intent_baselines:
                if (
                    "follow" in intent.description.lower()
                    and rel_type.lower() == "follows"
                ):
                    drift = self._create_drift(
                        intent=intent,
                        drift_type=DriftType.RELATIONSHIP,
                        severity=DriftSeverity.CRITICAL,
                        description=f"Reciprocal relationship missing: {rel_type} from {from_node} to {to_node}",
                        affected_entities=[str(from_node), str(to_node)],
                        reasoning="Expected reciprocal relationship not created after follow action",
                        evidence=[
                            {"relationship_type": rel_type},
                            {"from": str(from_node)},
                            {"to": str(to_node)},
                        ],
                    )
                    drifts.append(drift)

        return drifts

    def _check_entity_count_drift(
        self,
        intent_baselines: List[IntentBaseline],
        entity: str,
        before_count: int,
        after_count: int,
    ) -> Optional[LogicDrift]:
        """Check if entity count change represents drift."""
        # Find relevant intent
        for intent in intent_baselines:
            if entity.lower() in [e.lower() for e in intent.related_entities]:
                # Check if count change violates intent
                # This is a simplified check
                if before_count > 0 and after_count == 0:
                    return self._create_drift(
                        intent=intent,
                        drift_type=DriftType.DATA_INTEGRITY,
                        severity=DriftSeverity.CRITICAL,
                        description=f"All {entity} entities were deleted",
                        affected_entities=[entity],
                        reasoning=f"Entity count dropped from {before_count} to {after_count}",
                        evidence=[
                            {"entity": entity},
                            {"before_count": before_count},
                            {"after_count": after_count},
                        ],
                    )

        return None

    def _verify_criterion(self, criterion: str, response: Dict[str, Any]) -> bool:
        """Verify if a success criterion is met in the response."""
        # Simple keyword matching - can be enhanced
        response_str = json.dumps(response).lower()

        # Extract key terms from criterion
        key_terms = re.findall(r"\b\w+\b", criterion.lower())

        # Check if key terms are present
        important_terms = [t for t in key_terms if len(t) > 3]

        if important_terms:
            return any(term in response_str for term in important_terms)

        return True

    def _find_matching_db(self, state: StateSnapshot, db_type: str) -> Optional[Any]:
        """Find matching database snapshot."""
        for db in state.database_snapshots:
            if db.database_type == db_type:
                return db
        return None

    def _create_drift(
        self,
        intent: IntentBaseline,
        drift_type: DriftType,
        severity: DriftSeverity,
        description: str,
        affected_endpoints: Optional[List[str]] = None,
        affected_entities: Optional[List[str]] = None,
        reasoning: str = "",
        recommendation: str = "",
        evidence: Optional[List[Dict]] = None,
    ) -> LogicDrift:
        """Create a LogicDrift instance."""
        drift_id = f"drift_{uuid.uuid4().hex[:8]}"

        return LogicDrift(
            drift_id=drift_id,
            drift_type=drift_type,
            severity=severity,
            intent=intent,
            description=description,
            affected_endpoints=affected_endpoints or [],
            affected_entities=affected_entities or [],
            reasoning=reasoning,
            recommendation=recommendation
            or self._generate_recommendation(drift_type, severity),
            confidence=0.85,
            evidence=evidence or [],
        )

    def _generate_recommendation(
        self, drift_type: DriftType, severity: DriftSeverity
    ) -> str:
        """Generate a recommendation based on drift type and severity."""
        recommendations = {
            DriftType.BEHAVIORAL: "Review the endpoint implementation to ensure it aligns with intended behavior",
            DriftType.RELATIONSHIP: "Check relationship creation logic in your data layer",
            DriftType.STATE_TRANSITION: "Verify state machine transitions and preconditions",
            DriftType.VALIDATION_LOGIC: "Review validation rules and error handling",
            DriftType.BUSINESS_RULE: "Ensure business logic implementation matches requirements",
            DriftType.DATA_INTEGRITY: "Check data migration scripts and database constraints",
            DriftType.SIDE_EFFECT: "Review side effect handling in your business logic",
            DriftType.MISSING_FUNCTIONALITY: "Implement missing functionality according to specifications",
        }

        base_rec = recommendations.get(
            drift_type, "Review the changes for semantic correctness"
        )

        if severity == DriftSeverity.CRITICAL:
            return f"URGENT: {base_rec}. This is a critical issue that should be fixed immediately."
        elif severity == DriftSeverity.HIGH:
            return f"{base_rec}. This should be addressed before deployment."
        else:
            return base_rec

    def get_drifts_by_severity(self, severity: DriftSeverity) -> List[LogicDrift]:
        """Get all drifts of a specific severity."""
        return [d for d in self.detected_drifts if d.severity == severity]

    def get_drifts_by_type(self, drift_type: DriftType) -> List[LogicDrift]:
        """Get all drifts of a specific type."""
        return [d for d in self.detected_drifts if d.drift_type == drift_type]

    def has_critical_drifts(self) -> bool:
        """Check if any critical drifts were detected."""
        return any(d.severity == DriftSeverity.CRITICAL for d in self.detected_drifts)
