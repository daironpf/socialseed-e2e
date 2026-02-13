"""
AI Learning and Feedback Loop module for socialseed-e2e.
Enables AI agents to learn from test execution results and improve over time.
"""

from .adaptation_engine import AdaptationEngine, AdaptationStrategy
from .feedback_collector import FeedbackCollector, FeedbackType, TestFeedback
from .model_trainer import LearningMetrics, ModelTrainer, TrainingData

__all__ = [
    "FeedbackCollector",
    "TestFeedback",
    "FeedbackType",
    "ModelTrainer",
    "TrainingData",
    "LearningMetrics",
    "AdaptationEngine",
    "AdaptationStrategy",
]
