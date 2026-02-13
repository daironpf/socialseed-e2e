"""
Adaptation engine for dynamic test improvement.
Adapts test generation and execution based on learned patterns and codebase changes.
"""
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AdaptationStrategy(str, Enum):
    """Strategies for test adaptation."""
    CONSERVATIVE = "conservative"  # Minimal changes, high confidence
    BALANCED = "balanced"  # Moderate changes based on patterns
    AGGRESSIVE = "aggressive"  # Rapid adaptation to changes


class CodebaseChange(BaseModel):
    """Represents a change in the codebase."""
    
    file_path: str
    change_type: str  # added, modified, deleted
    timestamp: datetime
    affected_tests: List[str] = []


class AdaptationEngine:
    """
    Adapts test generation and execution based on learning and codebase changes.
    """
    
    def __init__(self, strategy: AdaptationStrategy = AdaptationStrategy.BALANCED):
        self.strategy = strategy
        self._adaptation_history: List[Dict[str, Any]] = []
        self._codebase_changes: List[CodebaseChange] = []
        
        # Confidence thresholds based on strategy
        self._confidence_thresholds = {
            AdaptationStrategy.CONSERVATIVE: 0.9,
            AdaptationStrategy.BALANCED: 0.7,
            AdaptationStrategy.AGGRESSIVE: 0.5
        }
    
    def adapt_test_generation(
        self,
        test_template: str,
        learned_patterns: Dict[str, List[str]],
        confidence_scores: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Adapt test generation based on learned patterns.
        
        Args:
            test_template: Original test template
            learned_patterns: Patterns learned from feedback
            confidence_scores: Confidence scores for each pattern
        
        Returns:
            Adapted test template
        """
        threshold = self._confidence_thresholds[self.strategy]
        adapted_template = test_template
        
        for pattern_key, corrections in learned_patterns.items():
            # Check confidence
            confidence = confidence_scores.get(pattern_key, 0.0) if confidence_scores else 0.8
            
            if confidence >= threshold and corrections:
                # Apply the most recent correction
                most_recent_correction = corrections[-1]
                
                # Simple replacement (in production, would use more sophisticated NLP)
                if pattern_key in adapted_template:
                    adapted_template = adapted_template.replace(pattern_key, most_recent_correction)
                    
                    self._adaptation_history.append({
                        "timestamp": datetime.now(),
                        "pattern": pattern_key,
                        "correction": most_recent_correction,
                        "confidence": confidence,
                        "strategy": self.strategy.value
                    })
        
        logger.info(f"Adapted test template with {len(self._adaptation_history)} changes")
        return adapted_template
    
    def detect_codebase_changes(
        self,
        file_changes: List[Dict[str, str]],
        test_mapping: Dict[str, List[str]]
    ) -> List[CodebaseChange]:
        """
        Detect codebase changes and identify affected tests.
        
        Args:
            file_changes: List of file changes with 'path' and 'type'
            test_mapping: Mapping of file paths to test names
        
        Returns:
            List of CodebaseChange objects
        """
        changes = []
        
        for change in file_changes:
            file_path = change.get("path", "")
            change_type = change.get("type", "modified")
            
            # Find affected tests
            affected_tests = test_mapping.get(file_path, [])
            
            codebase_change = CodebaseChange(
                file_path=file_path,
                change_type=change_type,
                timestamp=datetime.now(),
                affected_tests=affected_tests
            )
            
            changes.append(codebase_change)
            self._codebase_changes.append(codebase_change)
        
        logger.info(f"Detected {len(changes)} codebase changes affecting {sum(len(c.affected_tests) for c in changes)} tests")
        return changes
    
    def prioritize_test_execution(
        self,
        all_tests: List[str],
        recent_failures: List[str],
        codebase_changes: Optional[List[CodebaseChange]] = None
    ) -> List[str]:
        """
        Prioritize test execution based on failures and codebase changes.
        
        Args:
            all_tests: All available tests
            recent_failures: Tests that failed recently
            codebase_changes: Recent codebase changes
        
        Returns:
            Prioritized list of tests
        """
        priority_scores: Dict[str, float] = {test: 0.0 for test in all_tests}
        
        # High priority for recent failures
        for test in recent_failures:
            if test in priority_scores:
                priority_scores[test] += 10.0
        
        # Priority for tests affected by codebase changes
        if codebase_changes:
            for change in codebase_changes:
                for test in change.affected_tests:
                    if test in priority_scores:
                        # Higher priority for recent changes
                        age_factor = 1.0  # Could calculate based on timestamp
                        priority_scores[test] += 5.0 * age_factor
        
        # Sort by priority (descending)
        prioritized = sorted(all_tests, key=lambda t: priority_scores[t], reverse=True)
        
        logger.info(f"Prioritized {len(prioritized)} tests for execution")
        return prioritized
    
    def suggest_test_updates(
        self,
        test_name: str,
        failure_patterns: List[str],
        learned_corrections: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """
        Suggest updates to a test based on failure patterns and learned corrections.
        
        Returns:
            List of suggestions with 'type', 'description', and 'code'
        """
        suggestions = []
        
        for pattern in failure_patterns:
            if pattern in learned_corrections:
                suggestions.append({
                    "type": "correction",
                    "description": f"Apply learned correction for pattern: {pattern}",
                    "code": learned_corrections[pattern],
                    "confidence": "high"
                })
        
        # Generic suggestions based on strategy
        if self.strategy == AdaptationStrategy.AGGRESSIVE:
            suggestions.append({
                "type": "refactor",
                "description": "Consider refactoring test for better resilience",
                "code": "# Add retry logic and better error handling",
                "confidence": "medium"
            })
        
        return suggestions
    
    def adapt_to_api_changes(
        self,
        endpoint: str,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapt test assertions to API schema changes.
        
        Returns:
            Adaptation recommendations
        """
        recommendations = {
            "endpoint": endpoint,
            "changes": [],
            "required_updates": []
        }
        
        # Detect added fields
        old_fields = set(old_schema.keys())
        new_fields = set(new_schema.keys())
        
        added = new_fields - old_fields
        removed = old_fields - new_fields
        
        for field in added:
            recommendations["changes"].append({
                "type": "field_added",
                "field": field,
                "suggestion": f"Consider adding assertion for new field: {field}"
            })
        
        for field in removed:
            recommendations["required_updates"].append({
                "type": "field_removed",
                "field": field,
                "action": f"Remove assertions for deleted field: {field}"
            })
        
        # Detect type changes
        for field in old_fields & new_fields:
            if old_schema[field] != new_schema[field]:
                recommendations["required_updates"].append({
                    "type": "type_changed",
                    "field": field,
                    "old_type": old_schema[field],
                    "new_type": new_schema[field],
                    "action": f"Update assertion for {field} type change"
                })
        
        logger.info(f"Generated {len(recommendations['changes']) + len(recommendations['required_updates'])} adaptation recommendations for {endpoint}")
        return recommendations
    
    def get_adaptation_metrics(self) -> Dict[str, Any]:
        """Get metrics about adaptations performed."""
        if not self._adaptation_history:
            return {
                "total_adaptations": 0,
                "strategy": self.strategy.value
            }
        
        return {
            "total_adaptations": len(self._adaptation_history),
            "strategy": self.strategy.value,
            "recent_adaptations": self._adaptation_history[-10:],
            "codebase_changes_tracked": len(self._codebase_changes),
            "confidence_threshold": self._confidence_thresholds[self.strategy]
        }
    
    def set_strategy(self, strategy: AdaptationStrategy):
        """Change the adaptation strategy."""
        old_strategy = self.strategy
        self.strategy = strategy
        logger.info(f"Changed adaptation strategy from {old_strategy.value} to {strategy.value}")
