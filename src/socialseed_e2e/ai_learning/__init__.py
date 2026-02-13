"""
AI Learning and Feedback Loop module for socialseed-e2e.
Enables AI agents to learn from test execution results and improve over time.
"""

from .feedback_collector import FeedbackCollector, TestFeedback, FeedbackType
from .model_trainer import ModelTrainer, TrainingData, LearningMetrics
from .adaptation_engine import AdaptationEngine, AdaptationStrategy

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
