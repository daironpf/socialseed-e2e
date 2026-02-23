"""Reasoning Loop Detector.

Identifies 'zombie agents' that enter infinite loops of thought
without reaching a conclusion, wasting budget.
"""

import re
from datetime import datetime
from typing import Dict, List

from socialseed_e2e.telemetry.models import LLMCall, ReasoningLoop


class ReasoningLoopDetector:
    """Detects agents stuck in reasoning loops."""

    # Patterns indicating potential loops
    LOOP_INDICATORS = [
        r"let me think about this",
        r"i need to reconsider",
        r"on second thought",
        r"actually, let me",
        r"wait, that's not right",
        r"hmm, let me analyze",
        r"i should think about",
        r"let's reconsider",
        r"going back to",
        r"revisiting my previous",
        r"i'm not sure",
        r"this is confusing",
        r"maybe i should",
        r"alternatively",
        r"on the other hand",
        r"but then again",
        r"however",
        r"although",
        r"conversely",
        r"nevertheless",
    ]

    # Phrases that indicate progress
    PROGRESS_INDICATORS = [
        r"conclusion",
        r"therefore",
        r"final answer",
        r"in summary",
        r"to conclude",
        r"the solution is",
        r"answer is",
        r"result is",
        r"completed",
        r"finished",
        r"done",
        r"success",
    ]

    def __init__(
        self,
        max_reasoning_steps: int = 10,
        max_reasoning_time_seconds: float = 30.0,
    ):
        self.max_reasoning_steps = max_reasoning_steps
        self.max_reasoning_time_seconds = max_reasoning_time_seconds
        self.agent_states: Dict[str, Dict] = {}
        self.detected_loops: List[ReasoningLoop] = []

    def track_call(self, call: LLMCall):
        """Track an LLM call for potential loops."""
        agent_key = self._get_agent_key(call)

        if agent_key not in self.agent_states:
            self.agent_states[agent_key] = {
                "calls": [],
                "start_time": call.timestamp,
                "reasoning_steps": 0,
                "repeated_phrases": [],
                "no_progress_count": 0,
            }

        state = self.agent_states[agent_key]
        state["calls"].append(call)

        # Check for reasoning indicators
        response_preview = call.response_preview or ""
        prompt_preview = call.prompt_preview or ""
        combined_text = (response_preview + " " + prompt_preview).lower()

        # Check for loop indicators
        loop_score = self._calculate_loop_score(combined_text)
        progress_score = self._calculate_progress_score(combined_text)

        if loop_score > progress_score:
            state["reasoning_steps"] += 1
            state["no_progress_count"] += 1
        elif progress_score > 0:
            state["no_progress_count"] = 0

        # Check for repeated phrases
        repeated = self._find_repeated_phrases(state["calls"])
        state["repeated_phrases"] = repeated

        # Check if loop detected
        if self._is_in_loop(state, call):
            loop = self._create_loop_record(agent_key, state, call)
            self.detected_loops.append(loop)
            # Reset state after detection
            self.agent_states[agent_key] = {
                "calls": [],
                "start_time": call.timestamp,
                "reasoning_steps": 0,
                "repeated_phrases": [],
                "no_progress_count": 0,
            }

    def _get_agent_key(self, call: LLMCall) -> str:
        """Get unique key for agent/task combination."""
        parts = []
        if call.agent_name:
            parts.append(call.agent_name)
        if call.task_id:
            parts.append(call.task_id)
        if call.test_case_id:
            parts.append(call.test_case_id)

        return "_".join(parts) if parts else "unknown"

    def _calculate_loop_score(self, text: str) -> int:
        """Calculate score for loop indicators in text."""
        score = 0
        for pattern in self.LOOP_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1
        return score

    def _calculate_progress_score(self, text: str) -> int:
        """Calculate score for progress indicators in text."""
        score = 0
        for pattern in self.PROGRESS_INDICATORS:
            if re.search(pattern, text, re.IGNORECASE):
                score += 2  # Progress indicators weighted higher
        return score

    def _find_repeated_phrases(self, calls: List[LLMCall]) -> List[str]:
        """Find phrases repeated across multiple calls."""
        if len(calls) < 3:
            return []

        # Get last 3 responses
        recent_texts = []
        for call in calls[-3:]:
            text = (call.response_preview or "") + " " + (call.prompt_preview or "")
            recent_texts.append(text.lower())

        # Find common phrases (3+ words)
        repeated = []
        for i, text1 in enumerate(recent_texts):
            for j, text2 in enumerate(recent_texts):
                if i < j:
                    common = self._extract_common_phrases(text1, text2)
                    repeated.extend(common)

        return list(set(repeated))[:5]  # Return unique phrases, max 5

    def _extract_common_phrases(self, text1: str, text2: str) -> List[str]:
        """Extract common 3-word phrases between two texts."""
        words1 = text1.split()
        words2 = text2.split()

        phrases1 = set()
        for i in range(len(words1) - 2):
            phrase = " ".join(words1[i : i + 3])
            phrases1.add(phrase)

        phrases2 = set()
        for i in range(len(words2) - 2):
            phrase = " ".join(words2[i : i + 3])
            phrases2.add(phrase)

        common = phrases1 & phrases2
        return list(common)[:3]  # Max 3 phrases

    def _is_in_loop(self, state: Dict, current_call: LLMCall) -> bool:
        """Check if agent is stuck in a reasoning loop."""
        # Check reasoning steps limit
        if state["reasoning_steps"] >= self.max_reasoning_steps:
            return True

        # Check time limit
        start_time = state["start_time"]
        elapsed = (current_call.timestamp - start_time).total_seconds()
        if elapsed > self.max_reasoning_time_seconds:
            return True

        # Check for repeated phrases
        if len(state["repeated_phrases"]) >= 3:
            return True

        # Check for no progress
        if state["no_progress_count"] >= 5:
            return True

        return False

    def _create_loop_record(
        self,
        agent_key: str,
        state: Dict,
        current_call: LLMCall,
    ) -> ReasoningLoop:
        """Create a ReasoningLoop record."""
        loop_id = f"loop_{len(self.detected_loops)}_{agent_key[:20]}"

        start_time = state["start_time"]
        elapsed = (current_call.timestamp - start_time).total_seconds()

        # Calculate total tokens and cost
        total_tokens = sum(c.token_usage.total_tokens for c in state["calls"])
        total_cost = sum(c.cost.total_cost_usd for c in state["calls"])

        # Check if reached conclusion in last call
        last_response = current_call.response_preview or ""
        reached_conclusion = self._calculate_progress_score(last_response.lower()) > 0

        # Determine conclusion quality
        conclusion_quality = None
        if reached_conclusion:
            if total_tokens < 1000:
                conclusion_quality = "high"
            elif total_tokens < 3000:
                conclusion_quality = "medium"
            else:
                conclusion_quality = "low"
        else:
            conclusion_quality = "none"

        # Parse agent key
        parts = agent_key.split("_")
        agent_name = parts[0] if parts else None
        task_id = "_".join(parts[1:]) if len(parts) > 1 else None

        return ReasoningLoop(
            loop_id=loop_id,
            detected_at=datetime.now(),
            agent_name=agent_name,
            task_id=task_id,
            reasoning_steps=state["reasoning_steps"],
            time_spent_seconds=elapsed,
            tokens_consumed=total_tokens,
            cost_incurred_usd=total_cost,
            repeated_phrases=state["repeated_phrases"],
            circular_references=[],  # Could be enhanced with more analysis
            no_progress_indicators=[
                "Multiple reconsiderations detected",
                f"{state['no_progress_count']} steps without progress",
            ],
            reached_conclusion=reached_conclusion,
            conclusion_quality=conclusion_quality,
        )

    def get_detected_loops(self) -> List[ReasoningLoop]:
        """Get all detected reasoning loops."""
        return self.detected_loops

    def get_total_wasted_cost(self) -> float:
        """Get total cost wasted in loops."""
        return sum(loop.cost_incurred_usd for loop in self.detected_loops)

    def get_total_wasted_tokens(self) -> int:
        """Get total tokens wasted in loops."""
        return sum(loop.tokens_consumed for loop in self.detected_loops)

    def reset(self):
        """Reset detector state."""
        self.agent_states = {}
        self.detected_loops = []

    def generate_summary(self) -> Dict:
        """Generate summary of loop detection."""
        return {
            "loops_detected": len(self.detected_loops),
            "total_wasted_tokens": self.get_total_wasted_tokens(),
            "total_wasted_cost_usd": self.get_total_wasted_cost(),
            "agents_affected": len(
                {loop.agent_name for loop in self.detected_loops if loop.agent_name}
            ),
            "tasks_affected": len(
                {loop.task_id for loop in self.detected_loops if loop.task_id}
            ),
        }
