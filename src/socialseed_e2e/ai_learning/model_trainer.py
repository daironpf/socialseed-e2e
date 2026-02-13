"""
Model training system for AI learning.
Trains models based on collected feedback to improve test generation.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TrainingData(BaseModel):
    """Training data for model improvement."""

    inputs: List[str]
    outputs: List[str]
    contexts: List[Optional[str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningMetrics(BaseModel):
    """Metrics from model training."""

    training_samples: int
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    training_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ModelTrainer:
    """
    Trains AI models based on collected feedback.
    This is a framework for model training - actual ML implementation can be plugged in.
    """

    def __init__(self):
        self.training_history: List[LearningMetrics] = []
        self._patterns: Dict[str, List[str]] = {}
        self._corrections: Dict[str, str] = {}

    def train_from_corrections(self, training_data: TrainingData) -> LearningMetrics:
        """
        Train model from user corrections.

        This is a simplified implementation that learns patterns.
        In production, this would integrate with actual ML models.
        """
        start_time = datetime.now()

        # Learn correction patterns
        for i, (input_text, output_text) in enumerate(
            zip(training_data.inputs, training_data.outputs)
        ):
            self._corrections[input_text] = output_text

            # Extract patterns (simplified)
            pattern_key = self._extract_pattern(input_text)
            if pattern_key not in self._patterns:
                self._patterns[pattern_key] = []
            self._patterns[pattern_key].append(output_text)

        training_time = (datetime.now() - start_time).total_seconds()

        # Calculate metrics (simplified)
        metrics = LearningMetrics(
            training_samples=len(training_data.inputs),
            accuracy=0.85,  # Placeholder - would be calculated from validation
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            training_time=training_time,
        )

        self.training_history.append(metrics)
        logger.info(f"Trained on {metrics.training_samples} samples in {training_time:.2f}s")

        return metrics

    def _extract_pattern(self, text: str) -> str:
        """Extract a pattern key from text (simplified)."""
        # In a real implementation, this would use NLP/ML techniques
        # For now, just use first few words as pattern
        words = text.split()[:3]
        return " ".join(words)

    def predict_correction(self, input_text: str) -> Optional[str]:
        """
        Predict a correction for given input based on learned patterns.
        """
        # Direct match
        if input_text in self._corrections:
            return self._corrections[input_text]

        # Pattern match
        pattern_key = self._extract_pattern(input_text)
        if pattern_key in self._patterns and self._patterns[pattern_key]:
            # Return most common correction for this pattern
            return self._patterns[pattern_key][-1]

        return None

    def get_learning_progress(self) -> Dict[str, Any]:
        """Get learning progress metrics."""
        if not self.training_history:
            return {"total_training_sessions": 0, "total_samples": 0, "latest_accuracy": 0.0}

        total_samples = sum(m.training_samples for m in self.training_history)
        latest_metrics = self.training_history[-1]

        return {
            "total_training_sessions": len(self.training_history),
            "total_samples": total_samples,
            "latest_accuracy": latest_metrics.accuracy,
            "latest_f1_score": latest_metrics.f1_score,
            "learned_patterns": len(self._patterns),
            "learned_corrections": len(self._corrections),
        }

    def optimize_test_order(
        self, test_names: List[str], execution_history: Dict[str, float]
    ) -> List[str]:
        """
        Optimize test execution order based on historical data.

        Args:
            test_names: List of test names to order
            execution_history: Dict mapping test names to average execution time

        Returns:
            Optimized list of test names
        """
        # Strategy: Run faster tests first, then slower ones
        # This provides faster feedback

        def get_execution_time(test_name: str) -> float:
            return execution_history.get(test_name, float("inf"))

        optimized = sorted(test_names, key=get_execution_time)

        logger.info(f"Optimized test order for {len(test_names)} tests")
        return optimized

    def suggest_test_improvements(self, test_name: str, failure_count: int) -> List[str]:
        """
        Suggest improvements for frequently failing tests.
        """
        suggestions = []

        if failure_count > 5:
            suggestions.append("Consider adding more robust error handling")
            suggestions.append("Check if test data is still valid")
            suggestions.append("Verify endpoint availability and response format")

        if failure_count > 10:
            suggestions.append("This test may need significant refactoring")
            suggestions.append("Consider splitting into smaller, more focused tests")

        # Check learned patterns for this test
        pattern_key = self._extract_pattern(test_name)
        if pattern_key in self._patterns:
            suggestions.append(
                f"Similar tests have been corrected {len(self._patterns[pattern_key])} times"
            )

        return suggestions

    def export_model(self, output_path: str):
        """Export learned patterns and corrections."""
        import json

        model_data = {
            "patterns": self._patterns,
            "corrections": self._corrections,
            "training_history": [m.model_dump() for m in self.training_history],
        }

        with open(output_path, "w") as f:
            json.dump(model_data, f, indent=2, default=str)

        logger.info(f"Exported model to {output_path}")

    def load_model(self, input_path: str):
        """Load previously learned patterns and corrections."""
        import json

        with open(input_path, "r") as f:
            model_data = json.load(f)

        self._patterns = model_data.get("patterns", {})
        self._corrections = model_data.get("corrections", {})

        # Load training history
        for history_item in model_data.get("training_history", []):
            if isinstance(history_item.get("timestamp"), str):
                history_item["timestamp"] = datetime.fromisoformat(history_item["timestamp"])
            self.training_history.append(LearningMetrics(**history_item))

        logger.info(f"Loaded model from {input_path}")
