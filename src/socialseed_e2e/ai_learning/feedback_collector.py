"""
Feedback collection system for AI learning.
Collects test execution results, user corrections, and patterns for learning.
"""
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of feedback that can be collected."""

    TEST_SUCCESS = "test_success"
    TEST_FAILURE = "test_failure"
    USER_CORRECTION = "user_correction"
    PATTERN_DETECTED = "pattern_detected"
    PERFORMANCE_ISSUE = "performance_issue"
    CODE_CHANGE = "code_change"


class TestFeedback(BaseModel):
    """Feedback from a test execution."""

    feedback_id: str
    feedback_type: FeedbackType
    test_name: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # Test execution details
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

    # Context
    test_code: Optional[str] = None
    endpoint: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    response_data: Optional[Dict[str, Any]] = None

    # User corrections
    original_assertion: Optional[str] = None
    corrected_assertion: Optional[str] = None
    user_comment: Optional[str] = None

    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class FeedbackCollector:
    """
    Collects and stores feedback from test executions for AI learning.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./ai_feedback")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.storage_path / "feedback.jsonl"

        # In-memory cache for recent feedback
        self._feedback_cache: List[TestFeedback] = []
        self._max_cache_size = 1000

    def collect(self, feedback: TestFeedback):
        """Collect a piece of feedback."""
        # Add to cache
        self._feedback_cache.append(feedback)
        if len(self._feedback_cache) > self._max_cache_size:
            self._feedback_cache.pop(0)

        # Persist to disk (JSONL format for streaming)
        with open(self.feedback_file, "a") as f:
            feedback_dict = feedback.model_dump()
            # Convert datetime to ISO format
            if isinstance(feedback_dict.get("timestamp"), datetime):
                feedback_dict["timestamp"] = feedback_dict["timestamp"].isoformat()
            f.write(json.dumps(feedback_dict) + "\n")

        logger.info(f"Collected feedback: {feedback.feedback_type} for {feedback.test_name}")

    def collect_test_result(
        self,
        test_name: str,
        success: bool,
        execution_time: float,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None,
        **kwargs,
    ):
        """Convenience method to collect test execution results."""
        feedback = TestFeedback(
            feedback_id=f"{test_name}_{datetime.now().timestamp()}",
            feedback_type=FeedbackType.TEST_SUCCESS if success else FeedbackType.TEST_FAILURE,
            test_name=test_name,
            execution_time=execution_time,
            error_message=error_message,
            stack_trace=stack_trace,
            **kwargs,
        )
        self.collect(feedback)

    def collect_user_correction(
        self,
        test_name: str,
        original_assertion: str,
        corrected_assertion: str,
        user_comment: Optional[str] = None,
        **kwargs,
    ):
        """Collect user corrections to tests."""
        feedback = TestFeedback(
            feedback_id=f"{test_name}_correction_{datetime.now().timestamp()}",
            feedback_type=FeedbackType.USER_CORRECTION,
            test_name=test_name,
            original_assertion=original_assertion,
            corrected_assertion=corrected_assertion,
            user_comment=user_comment,
            **kwargs,
        )
        self.collect(feedback)

    def get_recent_feedback(self, limit: int = 100) -> List[TestFeedback]:
        """Get recent feedback from cache."""
        return self._feedback_cache[-limit:]

    def get_feedback_by_type(self, feedback_type: FeedbackType) -> List[TestFeedback]:
        """Get all feedback of a specific type from cache."""
        return [f for f in self._feedback_cache if f.feedback_type == feedback_type]

    def get_feedback_by_test(self, test_name: str) -> List[TestFeedback]:
        """Get all feedback for a specific test from cache."""
        return [f for f in self._feedback_cache if f.test_name == test_name]

    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in collected feedback."""
        if not self._feedback_cache:
            return {"total": 0}

        total = len(self._feedback_cache)
        type_counts = {}
        for feedback in self._feedback_cache:
            type_counts[feedback.feedback_type.value] = (
                type_counts.get(feedback.feedback_type.value, 0) + 1
            )

        # Calculate success rate
        successes = type_counts.get(FeedbackType.TEST_SUCCESS.value, 0)
        failures = type_counts.get(FeedbackType.TEST_FAILURE.value, 0)
        success_rate = successes / (successes + failures) if (successes + failures) > 0 else 0

        # Average execution time
        execution_times = [
            f.execution_time for f in self._feedback_cache if f.execution_time is not None
        ]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        # Most common errors
        error_counts: Dict[str, int] = {}
        for feedback in self._feedback_cache:
            if feedback.error_message:
                error_counts[feedback.error_message] = (
                    error_counts.get(feedback.error_message, 0) + 1
                )

        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total": total,
            "type_counts": type_counts,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "top_errors": [{"error": err, "count": count} for err, count in top_errors],
            "user_corrections": type_counts.get(FeedbackType.USER_CORRECTION.value, 0),
        }

    def load_all_feedback(self) -> List[TestFeedback]:
        """Load all feedback from disk."""
        if not self.feedback_file.exists():
            return []

        feedback_list = []
        with open(self.feedback_file, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                # Parse datetime
                if isinstance(data.get("timestamp"), str):
                    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
                feedback_list.append(TestFeedback(**data))

        return feedback_list

    def export_for_training(self, output_path: Path):
        """Export feedback in a format suitable for model training."""
        all_feedback = self.load_all_feedback()

        training_data = []
        for feedback in all_feedback:
            if feedback.feedback_type == FeedbackType.USER_CORRECTION:
                training_data.append(
                    {
                        "input": feedback.original_assertion,
                        "output": feedback.corrected_assertion,
                        "context": feedback.user_comment,
                        "test_name": feedback.test_name,
                    }
                )

        with open(output_path, "w") as f:
            json.dump(training_data, f, indent=2)

        logger.info(f"Exported {len(training_data)} training examples to {output_path}")
        return len(training_data)
