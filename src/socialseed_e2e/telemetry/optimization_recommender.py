"""Optimization Recommender.

Analyzes telemetry logs and suggests optimizations:
- Prompt truncations
- Context-caching strategies
- Model downgrades
- Batching opportunities
"""

from typing import Any, Dict, List, Optional

from socialseed_e2e.telemetry.models import (
    LLMCall,
    OptimizationRecommendation,
    TestCaseMetrics,
)


class OptimizationRecommender:
    """Generates cost and performance optimization recommendations."""

    # Thresholds for recommendations
    LONG_PROMPT_THRESHOLD = 3000  # tokens
    VERY_LONG_PROMPT_THRESHOLD = 8000  # tokens
    HIGH_COST_THRESHOLD = 0.10  # USD per call
    REPEATED_CONTEXT_THRESHOLD = 0.8  # 80% similarity

    def __init__(self):
        self.recommendations: List[OptimizationRecommendation] = []

    def analyze_and_recommend(
        self,
        calls: List[LLMCall],
        test_cases: List[TestCaseMetrics],
    ) -> List[OptimizationRecommendation]:
        """Analyze usage and generate recommendations."""
        self.recommendations = []

        # Analyze for truncation opportunities
        self._analyze_prompt_truncation(calls)

        # Analyze for caching opportunities
        self._analyze_context_caching(calls)

        # Analyze for model downgrade opportunities
        self._analyze_model_downgrade(calls)

        # Analyze for batching opportunities
        self._analyze_batching(calls)

        # Analyze for repeated patterns
        self._analyze_repeated_patterns(calls)

        # Sort by priority and estimated savings
        self.recommendations.sort(
            key=lambda r: (
                {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(r.priority, 4),
                -(r.estimated_savings_usd or 0),
            )
        )

        return self.recommendations

    def _analyze_prompt_truncation(self, calls: List[LLMCall]):
        """Analyze for prompt truncation opportunities."""
        long_prompt_calls = [
            c for c in calls if c.token_usage.input_tokens > self.LONG_PROMPT_THRESHOLD
        ]

        if not long_prompt_calls:
            return

        # Group by test case
        by_test: Dict[str, List[LLMCall]] = {}
        for call in long_prompt_calls:
            test_id = call.test_case_id or "unknown"
            if test_id not in by_test:
                by_test[test_id] = []
            by_test[test_id].append(call)

        for test_id, test_calls in by_test.items():
            avg_input = sum(c.token_usage.input_tokens for c in test_calls) / len(
                test_calls
            )

            if avg_input > self.VERY_LONG_PROMPT_THRESHOLD:
                # Very long prompts - critical
                potential_savings = sum(
                    (c.token_usage.input_tokens - self.LONG_PROMPT_THRESHOLD)
                    / 1000
                    * c.cost.cost_per_1k_input_tokens
                    for c in test_calls
                )

                rec = OptimizationRecommendation(
                    recommendation_id=f"trunc_{test_id}",
                    category="truncation",
                    priority="critical",
                    title=f"Critical: Reduce prompt size for {test_id}",
                    description=f"Average prompt size is {avg_input:.0f} tokens. Consider removing unnecessary context or splitting into smaller prompts.",
                    estimated_savings_usd=potential_savings,
                    estimated_savings_percentage=30.0,
                    implementation_effort="medium",
                    risk_level="low",
                    code_example=self._generate_truncation_example(),
                )
                self.recommendations.append(rec)

            elif avg_input > self.LONG_PROMPT_THRESHOLD:
                # Long prompts - high priority
                potential_savings = (
                    sum(
                        (c.token_usage.input_tokens - 2000)
                        / 1000
                        * c.cost.cost_per_1k_input_tokens
                        for c in test_calls
                    )
                    * 0.5
                )  # Assume 50% reduction possible

                rec = OptimizationRecommendation(
                    recommendation_id=f"trunc_{test_id}",
                    category="truncation",
                    priority="high",
                    title=f"Reduce prompt size for {test_id}",
                    description=f"Average prompt size is {avg_input:.0f} tokens. Consider summarizing or removing redundant information.",
                    estimated_savings_usd=potential_savings,
                    estimated_savings_percentage=20.0,
                    implementation_effort="low",
                    risk_level="low",
                    code_example=self._generate_truncation_example(),
                )
                self.recommendations.append(rec)

    def _analyze_context_caching(self, calls: List[LLMCall]):
        """Analyze for context caching opportunities."""
        # Find calls with similar prompts (potential for caching)
        prompt_similarities = self._find_similar_prompts(calls)

        for group_id, similar_calls in prompt_similarities.items():
            if len(similar_calls) >= 3:  # At least 3 similar calls
                total_calls = len(similar_calls)
                avg_input = (
                    sum(c.token_usage.input_tokens for c in similar_calls) / total_calls
                )
                avg_cost = (
                    sum(c.cost.total_cost_usd for c in similar_calls) / total_calls
                )

                # Estimate savings (assuming 70% of prompt could be cached)
                potential_savings = (
                    total_calls * avg_cost * 0.7 * 0.5
                )  # 50% of 70% cached

                rec = OptimizationRecommendation(
                    recommendation_id=f"cache_{group_id}",
                    category="caching",
                    priority="high" if total_calls > 5 else "medium",
                    title=f"Implement context caching for repeated patterns",
                    description=f"Found {total_calls} similar prompts (avg {avg_input:.0f} tokens). Caching common context could save significant costs.",
                    estimated_savings_usd=potential_savings,
                    estimated_savings_percentage=35.0,
                    implementation_effort="medium",
                    risk_level="low",
                    code_example=self._generate_caching_example(),
                )
                self.recommendations.append(rec)

    def _analyze_model_downgrade(self, calls: List[LLMCall]):
        """Analyze for model downgrade opportunities."""
        # Group by model
        by_model: Dict[str, List[LLMCall]] = {}
        for call in calls:
            model = call.model_name
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(call)

        # Check for expensive models that might be overkill
        expensive_models = ["gpt-4", "claude-3-opus"]

        for model in expensive_models:
            if model in by_model:
                model_calls = by_model[model]

                # Check if calls are simple (short output, no complex reasoning)
                simple_calls = [
                    c
                    for c in model_calls
                    if c.token_usage.output_tokens < 500 and c.reasoning_steps < 3
                ]

                if len(simple_calls) > len(model_calls) * 0.7:  # 70% are simple
                    # Could downgrade
                    potential_savings = sum(
                        c.cost.total_cost_usd * 0.8  # 80% cost reduction
                        for c in simple_calls
                    )

                    cheaper_alternative = (
                        "gpt-3.5-turbo" if "gpt" in model else "claude-3-haiku"
                    )

                    rec = OptimizationRecommendation(
                        recommendation_id=f"downgrade_{model}",
                        category="model_downgrade",
                        priority="medium",
                        title=f"Consider {cheaper_alternative} for simple tasks",
                        description=f"{len(simple_calls)} calls to {model} are simple (<500 output tokens, <3 reasoning steps). Consider using {cheaper_alternative} for these.",
                        estimated_savings_usd=potential_savings,
                        estimated_savings_percentage=60.0,
                        implementation_effort="low",
                        risk_level="medium",
                        code_example=self._generate_model_selection_example(
                            cheaper_alternative
                        ),
                    )
                    self.recommendations.append(rec)

    def _analyze_batching(self, calls: List[LLMCall]):
        """Analyze for batching opportunities."""
        # Group by test case and check for rapid sequential calls
        by_test: Dict[str, List[LLMCall]] = {}
        for call in calls:
            test_id = call.test_case_id or "unknown"
            if test_id not in by_test:
                by_test[test_id] = []
            by_test[test_id].append(call)

        for test_id, test_calls in by_test.items():
            if len(test_calls) < 3:
                continue

            # Sort by timestamp
            sorted_calls = sorted(test_calls, key=lambda c: c.timestamp)

            # Check for rapid consecutive calls
            rapid_sequences = []
            current_sequence = [sorted_calls[0]]

            for i in range(1, len(sorted_calls)):
                time_diff = (
                    sorted_calls[i].timestamp - sorted_calls[i - 1].timestamp
                ).total_seconds()
                if time_diff < 5:  # Less than 5 seconds apart
                    current_sequence.append(sorted_calls[i])
                else:
                    if len(current_sequence) >= 3:
                        rapid_sequences.append(current_sequence)
                    current_sequence = [sorted_calls[i]]

            if len(current_sequence) >= 3:
                rapid_sequences.append(current_sequence)

            for seq_idx, sequence in enumerate(rapid_sequences):
                total_cost = sum(c.cost.total_cost_usd for c in sequence)

                rec = OptimizationRecommendation(
                    recommendation_id=f"batch_{test_id}_{seq_idx}",
                    category="batching",
                    priority="medium",
                    title=f"Batch API calls in {test_id}",
                    description=f"Found {len(sequence)} rapid consecutive calls that could be batched to reduce overhead.",
                    estimated_savings_usd=total_cost * 0.2,  # 20% overhead reduction
                    estimated_savings_percentage=20.0,
                    implementation_effort="high",
                    risk_level="medium",
                    code_example=self._generate_batching_example(),
                )
                self.recommendations.append(rec)

    def _analyze_repeated_patterns(self, calls: List[LLMCall]):
        """Analyze for repeated patterns that could be templated."""
        # This would require more sophisticated text analysis
        # For now, provide a general recommendation if many calls
        if len(calls) > 20:
            total_cost = sum(c.cost.total_cost_usd for c in calls)

            rec = OptimizationRecommendation(
                recommendation_id="patterns_general",
                category="other",
                priority="low",
                title="Review for prompt templating opportunities",
                description="High volume of calls detected. Review prompts for repeated patterns that could be converted to templates with variable substitution.",
                estimated_savings_usd=total_cost * 0.15,
                estimated_savings_percentage=15.0,
                implementation_effort="medium",
                risk_level="low",
                code_example=self._generate_templating_example(),
            )
            self.recommendations.append(rec)

    def _find_similar_prompts(self, calls: List[LLMCall]) -> Dict[str, List[LLMCall]]:
        """Find groups of similar prompts."""
        # Simplified similarity detection based on length and first 100 chars
        groups: Dict[str, List[LLMCall]] = {}

        for call in calls:
            preview = call.prompt_preview or ""
            # Create a simple hash based on length bucket and first 100 chars
            length_bucket = call.token_usage.input_tokens // 500  # 500 token buckets
            content_hash = preview[:100] if len(preview) >= 100 else preview
            group_key = f"{length_bucket}_{hash(content_hash) % 1000}"

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(call)

        # Only return groups with multiple calls
        return {k: v for k, v in groups.items() if len(v) >= 3}

    def _generate_truncation_example(self) -> str:
        """Generate code example for prompt truncation."""
        return """
# Before: Sending full context
response = llm.generate(large_context + user_query)

# After: Summarize context first
summary = summarize(large_context, max_tokens=500)
response = llm.generate(summary + user_query)
"""

    def _generate_caching_example(self) -> str:
        """Generate code example for context caching."""
        return """
# Before: Re-sending same context
for query in queries:
    response = llm.generate(system_prompt + context + query)

# After: Cache context
cached_context = llm.cache_context(system_prompt + context)
for query in queries:
    response = llm.generate(cached_context + query)  # Cheaper!
"""

    def _generate_model_selection_example(self, cheaper_model: str) -> str:
        """Generate code example for model selection."""
        return f'''
# Before: Always using expensive model
response = llm.generate(prompt, model="gpt-4")

# After: Select model based on complexity
if is_simple_task(prompt):
    response = llm.generate(prompt, model="{cheaper_model}")
else:
    response = llm.generate(prompt, model="gpt-4")
'''

    def _generate_batching_example(self) -> str:
        """Generate code example for batching."""
        return """
# Before: Individual calls
results = []
for item in items:
    result = llm.generate(process(item))
    results.append(result)

# After: Batched call
results = llm.generate_batch([process(item) for item in items])
"""

    def _generate_templating_example(self) -> str:
        """Generate code example for templating."""
        return """
# Before: Dynamic prompt construction
prompt = f"Analyze {data} and provide {format} output"

# After: Template with variable substitution
template = load_template("analysis_template")
prompt = template.format(data=data, format=format)
"""

    def get_total_estimated_savings(self) -> float:
        """Get total estimated savings from all recommendations."""
        return sum(r.estimated_savings_usd or 0 for r in self.recommendations)

    def get_recommendations_by_category(
        self, category: str
    ) -> List[OptimizationRecommendation]:
        """Get recommendations by category."""
        return [r for r in self.recommendations if r.category == category]

    def get_recommendations_by_priority(
        self, priority: str
    ) -> List[OptimizationRecommendation]:
        """Get recommendations by priority."""
        return [r for r in self.recommendations if r.priority == priority]
