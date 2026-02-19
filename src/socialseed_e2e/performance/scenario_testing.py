"""Scenario-Based Performance Testing.

This module provides tools for testing complex user journeys and workflows:
- User journey simulation
- Complex workflow testing
- Data-dependent scenarios
- Session management
- Think time modeling

Example:
    >>> from socialseed_e2e.performance import ScenarioBuilder, UserJourney
    >>> builder = ScenarioBuilder()
    >>> journey = builder.create_user_journey("e-commerce-checkout")
    >>> result = await journey.execute(users=100)
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Types of scenario steps."""

    REQUEST = "request"  # API request
    THINK = "think"  # Think time
    VALIDATION = "validation"  # Data validation
    DECISION = "decision"  # Conditional branch
    LOOP = "loop"  # Repeat steps
    SETUP = "setup"  # Initial setup
    TEARDOWN = "teardown"  # Cleanup
    DATA_GENERATION = "data_gen"  # Generate test data


@dataclass
class ScenarioStep:
    """A single step in a performance scenario.

    Attributes:
        name: Step name
        step_type: Type of step
        action: Function to execute
        weight: Probability weight for random selection
        think_time_ms: Think time after this step
        validation: Optional validation function
        on_error: Error handling strategy
        retry_count: Number of retries on failure
        timeout_seconds: Step timeout
    """

    name: str
    step_type: StepType
    action: Optional[Callable] = None
    weight: float = 1.0
    think_time_ms: Tuple[int, int] = (100, 500)
    validation: Optional[Callable] = None
    on_error: str = "continue"  # continue, abort, retry
    retry_count: int = 0
    timeout_seconds: int = 30

    async def execute(self, context: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute the step.

        Args:
            context: Execution context with shared data

        Returns:
            Tuple of (success, result)
        """
        if self.action is None:
            return True, None

        retries = 0
        max_retries = self.retry_count if self.on_error == "retry" else 0

        while retries <= max_retries:
            try:
                start_time = time.perf_counter()

                # Execute action
                if asyncio.iscoroutinefunction(self.action):
                    result = await asyncio.wait_for(
                        self.action(context), timeout=self.timeout_seconds
                    )
                else:
                    result = self.action(context)

                latency_ms = (time.perf_counter() - start_time) * 1000

                # Run validation if provided
                if self.validation:
                    valid = self.validation(result)
                    if not valid:
                        return False, {"error": "Validation failed", "result": result}

                return True, {
                    "result": result,
                    "latency_ms": latency_ms,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            except asyncio.TimeoutError:
                if retries >= max_retries:
                    return False, {"error": "Timeout", "timeout": self.timeout_seconds}
                retries += 1
                await asyncio.sleep(0.1 * retries)  # Exponential backoff

            except Exception as e:
                if retries >= max_retries:
                    return False, {"error": str(e), "exception_type": type(e).__name__}
                retries += 1
                await asyncio.sleep(0.1 * retries)

        return False, {"error": "Max retries exceeded"}


@dataclass
class ScenarioTransition:
    """Transition between steps in a scenario."""

    from_step: str
    to_step: str
    probability: float = 1.0
    condition: Optional[Callable] = None


@dataclass
class UserJourneyMetrics:
    """Metrics for a user journey execution."""

    journey_name: str
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    steps_completed: int = 0
    steps_failed: int = 0
    total_latency_ms: float = 0.0
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.steps_completed + self.steps_failed
        return (self.steps_completed / total * 100) if total > 0 else 0.0

    @property
    def duration_seconds(self) -> float:
        """Get journey duration."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


@dataclass
class ScenarioResult:
    """Results from scenario execution."""

    scenario_name: str
    start_time: datetime
    end_time: datetime
    concurrent_users: int
    total_journeys: int = 0
    successful_journeys: int = 0
    failed_journeys: int = 0

    # Aggregate metrics
    avg_journey_duration_ms: float = 0.0
    min_journey_duration_ms: float = 0.0
    max_journey_duration_ms: float = 0.0

    # Step-level metrics
    step_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # User journey details
    journey_metrics: List[UserJourneyMetrics] = field(default_factory=list)

    # Errors
    errors_by_step: Dict[str, int] = field(default_factory=dict)
    total_errors: int = 0

    def calculate_statistics(self) -> None:
        """Calculate aggregate statistics."""
        if not self.journey_metrics:
            return

        durations = [jm.duration_seconds * 1000 for jm in self.journey_metrics]
        self.avg_journey_duration_ms = sum(durations) / len(durations)
        self.min_journey_duration_ms = min(durations)
        self.max_journey_duration_ms = max(durations)

        # Calculate step statistics
        for journey in self.journey_metrics:
            for step_result in journey.step_results:
                step_name = step_result.get("step_name", "unknown")
                if step_name not in self.step_stats:
                    self.step_stats[step_name] = {
                        "count": 0,
                        "success_count": 0,
                        "fail_count": 0,
                        "total_latency_ms": 0.0,
                        "latencies": [],
                    }

                stats = self.step_stats[step_name]
                stats["count"] += 1

                if step_result.get("success", False):
                    stats["success_count"] += 1
                    latency = step_result.get("latency_ms", 0)
                    stats["total_latency_ms"] += latency
                    stats["latencies"].append(latency)
                else:
                    stats["fail_count"] += 1
                    error = step_result.get("error", "Unknown")
                    self.errors_by_step[step_name] = (
                        self.errors_by_step.get(step_name, 0) + 1
                    )
                    self.total_errors += 1

        # Calculate averages
        for stats in self.step_stats.values():
            if stats["success_count"] > 0:
                stats["avg_latency_ms"] = (
                    stats["total_latency_ms"] / stats["success_count"]
                )
                if stats["latencies"]:
                    sorted_latencies = sorted(stats["latencies"])
                    stats["p95_latency_ms"] = sorted_latencies[
                        int(len(sorted_latencies) * 0.95)
                    ]
                    stats["p99_latency_ms"] = sorted_latencies[
                        int(len(sorted_latencies) * 0.99)
                    ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "scenario_name": self.scenario_name,
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "concurrent_users": self.concurrent_users,
            "journeys": {
                "total": self.total_journeys,
                "successful": self.successful_journeys,
                "failed": self.failed_journeys,
                "success_rate_pct": round(
                    (self.successful_journeys / max(self.total_journeys, 1) * 100), 2
                ),
            },
            "journey_duration": {
                "avg_ms": round(self.avg_journey_duration_ms, 2),
                "min_ms": round(self.min_journey_duration_ms, 2),
                "max_ms": round(self.max_journey_duration_ms, 2),
            },
            "steps": {
                name: {
                    "count": stats["count"],
                    "success_rate_pct": round(
                        (stats["success_count"] / max(stats["count"], 1) * 100), 2
                    ),
                    "avg_latency_ms": round(stats.get("avg_latency_ms", 0), 2),
                    "p95_latency_ms": round(stats.get("p95_latency_ms", 0), 2),
                }
                for name, stats in self.step_stats.items()
            },
            "errors": {
                "total": self.total_errors,
                "by_step": self.errors_by_step,
            },
        }


class UserJourney:
    """Represents a user journey through a sequence of steps.

    A user journey simulates a realistic user flow through multiple
    API calls with think times between steps.

    Example:
        >>> journey = UserJourney("checkout")
        >>> journey.add_step(ScenarioStep(
        ...     name="login",
        ...     step_type=StepType.REQUEST,
        ...     action=login_func
        ... ))
        >>> journey.add_step(ScenarioStep(
        ...     name="add_to_cart",
        ...     step_type=StepType.REQUEST,
        ...     action=add_to_cart_func
        ... ))
        >>> result = await journey.execute_single_user(user_id=1)
    """

    def __init__(self, name: str, description: str = ""):
        """Initialize a user journey.

        Args:
            name: Journey name
            description: Journey description
        """
        self.name = name
        self.description = description
        self.steps: List[ScenarioStep] = []
        self.transitions: List[ScenarioTransition] = []
        self.setup_step: Optional[ScenarioStep] = None
        self.teardown_step: Optional[ScenarioStep] = None

    def add_step(self, step: ScenarioStep) -> "UserJourney":
        """Add a step to the journey.

        Args:
            step: ScenarioStep to add

        Returns:
            Self for chaining
        """
        self.steps.append(step)
        return self

    def add_transition(self, transition: ScenarioTransition) -> "UserJourney":
        """Add a transition between steps.

        Args:
            transition: ScenarioTransition to add

        Returns:
            Self for chaining
        """
        self.transitions.append(transition)
        return self

    def set_setup(self, step: ScenarioStep) -> "UserJourney":
        """Set the setup step.

        Args:
            step: Setup ScenarioStep

        Returns:
            Self for chaining
        """
        self.setup_step = step
        return self

    def set_teardown(self, step: ScenarioStep) -> "UserJourney":
        """Set the teardown step.

        Args:
            step: Teardown ScenarioStep

        Returns:
            Self for chaining
        """
        self.teardown_step = step
        return self

    async def execute_single_user(
        self, user_id: int, context: Optional[Dict[str, Any]] = None
    ) -> UserJourneyMetrics:
        """Execute the journey for a single user.

        Args:
            user_id: Unique user identifier
            context: Optional shared context

        Returns:
            UserJourneyMetrics with execution details
        """
        metrics = UserJourneyMetrics(
            journey_name=self.name, user_id=user_id, start_time=datetime.utcnow()
        )

        context = context or {}
        context["user_id"] = user_id
        context["journey_name"] = self.name

        try:
            # Run setup
            if self.setup_step:
                success, result = await self.setup_step.execute(context)
                if not success:
                    metrics.errors.append(f"Setup failed: {result}")
                    metrics.end_time = datetime.utcnow()
                    return metrics
                context["setup_result"] = result

            # Execute steps
            for step in self.steps:
                success, result = await step.execute(context)

                step_result = {
                    "step_name": step.name,
                    "step_type": step.step_type.value,
                    "success": success,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                if success:
                    metrics.steps_completed += 1
                    metrics.total_latency_ms += result.get("latency_ms", 0)
                    step_result.update(result)
                    context[f"step_{step.name}_result"] = result
                else:
                    metrics.steps_failed += 1
                    metrics.errors.append(
                        f"{step.name}: {result.get('error', 'Unknown')}"
                    )
                    step_result.update(result)

                    if step.on_error == "abort":
                        break

                metrics.step_results.append(step_result)

                # Add think time
                if step.think_time_ms[1] > 0:
                    think_ms = random.randint(
                        step.think_time_ms[0], step.think_time_ms[1]
                    )
                    await asyncio.sleep(think_ms / 1000)

            # Run teardown
            if self.teardown_step:
                await self.teardown_step.execute(context)

        except Exception as e:
            metrics.errors.append(f"Journey exception: {str(e)}")

        finally:
            metrics.end_time = datetime.utcnow()

        return metrics

    async def execute(
        self, concurrent_users: int, duration_seconds: int, ramp_up_seconds: int = 10
    ) -> ScenarioResult:
        """Execute journey with multiple concurrent users.

        Args:
            concurrent_users: Number of concurrent users
            duration_seconds: Test duration
            ramp_up_seconds: Ramp up time

        Returns:
            ScenarioResult with aggregate metrics
        """
        logger.info(
            f"Starting scenario '{self.name}' with {concurrent_users} users "
            f"for {duration_seconds}s"
        )

        start_time = datetime.utcnow()
        all_metrics: List[UserJourneyMetrics] = []
        stop_event = asyncio.Event()

        async def user_worker(user_id: int):
            """Worker for a single user."""
            while not stop_event.is_set():
                metrics = await self.execute_single_user(user_id)
                all_metrics.append(metrics)

                # Small delay before next iteration
                await asyncio.sleep(random.uniform(0.5, 2.0))

        # Start users with ramp-up
        tasks = []
        for i in range(concurrent_users):
            task = asyncio.create_task(user_worker(i))
            tasks.append(task)

            # Ramp up delay
            if ramp_up_seconds > 0 and i < concurrent_users - 1:
                await asyncio.sleep(ramp_up_seconds / concurrent_users)

        # Run for duration
        await asyncio.sleep(duration_seconds)
        stop_event.set()

        # Wait for completion
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.utcnow()

        # Build result
        result = ScenarioResult(
            scenario_name=self.name,
            start_time=start_time,
            end_time=end_time,
            concurrent_users=concurrent_users,
            total_journeys=len(all_metrics),
            successful_journeys=len([m for m in all_metrics if m.steps_failed == 0]),
            failed_journeys=len([m for m in all_metrics if m.steps_failed > 0]),
            journey_metrics=all_metrics,
        )

        result.calculate_statistics()

        logger.info(
            f"Scenario '{self.name}' complete: {result.successful_journeys}/"
            f"{result.total_journeys} successful journeys"
        )

        return result


class ScenarioBuilder:
    """Builder for creating complex performance scenarios.

    Provides a fluent API for building user journeys and scenarios
    with multiple steps, transitions, and validations.

    Example:
        >>> builder = ScenarioBuilder()
        >>>
        >>> # Create e-commerce checkout journey
        >>> checkout = builder.create_user_journey("checkout")
        >>> checkout.add_step(builder.request_step("login", login_api))
        >>> checkout.add_step(builder.request_step("browse", browse_api))
        >>> checkout.add_step(builder.request_step("add_cart", add_cart_api))
        >>> checkout.add_step(builder.request_step("checkout", checkout_api))
        >>>
        >>> # Execute the scenario
        >>> result = await checkout.execute(users=100, duration=300)
    """

    def __init__(self):
        """Initialize the scenario builder."""
        self.journeys: Dict[str, UserJourney] = {}

    def create_user_journey(self, name: str, description: str = "") -> UserJourney:
        """Create a new user journey.

        Args:
            name: Journey name
            description: Journey description

        Returns:
            New UserJourney instance
        """
        journey = UserJourney(name, description)
        self.journeys[name] = journey
        return journey

    def request_step(
        self,
        name: str,
        action: Callable,
        think_time_ms: Tuple[int, int] = (100, 500),
        validation: Optional[Callable] = None,
        retry_count: int = 0,
    ) -> ScenarioStep:
        """Create a request step.

        Args:
            name: Step name
            action: Request function
            think_time_ms: Think time range
            validation: Optional validation function
            retry_count: Number of retries

        Returns:
            ScenarioStep configured for requests
        """
        return ScenarioStep(
            name=name,
            step_type=StepType.REQUEST,
            action=action,
            think_time_ms=think_time_ms,
            validation=validation,
            retry_count=retry_count,
        )

    def think_step(self, duration_ms: Tuple[int, int]) -> ScenarioStep:
        """Create a think time step.

        Args:
            duration_ms: Think time range in milliseconds

        Returns:
            ScenarioStep configured for think time
        """

        async def think_action(context):
            await asyncio.sleep(random.randint(duration_ms[0], duration_ms[1]) / 1000)
            return {"think_time": "completed"}

        return ScenarioStep(
            name="think",
            step_type=StepType.THINK,
            action=think_action,
            think_time_ms=(0, 0),
        )

    def validation_step(
        self, name: str, validation_func: Callable, on_error: str = "abort"
    ) -> ScenarioStep:
        """Create a validation step.

        Args:
            name: Step name
            validation_func: Validation function
            on_error: Error handling strategy

        Returns:
            ScenarioStep configured for validation
        """
        return ScenarioStep(
            name=name,
            step_type=StepType.VALIDATION,
            action=validation_func,
            on_error=on_error,
            think_time_ms=(0, 0),
        )

    def conditional_step(
        self,
        name: str,
        condition: Callable,
        true_branch: List[ScenarioStep],
        false_branch: Optional[List[ScenarioStep]] = None,
    ) -> ScenarioStep:
        """Create a conditional step with branches.

        Args:
            name: Step name
            condition: Condition function
            true_branch: Steps to execute if true
            false_branch: Steps to execute if false

        Returns:
            ScenarioStep configured for conditional execution
        """

        async def conditional_action(context):
            result = condition(context)
            if asyncio.iscoroutinefunction(condition):
                result = await result

            branch = true_branch if result else (false_branch or [])
            results = []
            for step in branch:
                success, step_result = await step.execute(context)
                results.append(
                    {"step": step.name, "success": success, "result": step_result}
                )

            return {"branches_executed": len(results), "results": results}

        return ScenarioStep(
            name=name, step_type=StepType.DECISION, action=conditional_action
        )

    def data_generation_step(
        self, name: str, generator_func: Callable, output_key: str
    ) -> ScenarioStep:
        """Create a data generation step.

        Args:
            name: Step name
            generator_func: Function to generate data
            output_key: Key to store generated data in context

        Returns:
            ScenarioStep configured for data generation
        """

        async def data_action(context):
            if asyncio.iscoroutinefunction(generator_func):
                data = await generator_func(context)
            else:
                data = generator_func(context)

            context[output_key] = data
            return {
                "generated": True,
                "key": output_key,
                "data_preview": str(data)[:100],
            }

        return ScenarioStep(
            name=name,
            step_type=StepType.DATA_GENERATION,
            action=data_action,
            think_time_ms=(0, 0),
        )

    def get_journey(self, name: str) -> Optional[UserJourney]:
        """Get a journey by name.

        Args:
            name: Journey name

        Returns:
            UserJourney or None
        """
        return self.journeys.get(name)

    def list_journeys(self) -> List[str]:
        """List all journey names.

        Returns:
            List of journey names
        """
        return list(self.journeys.keys())


class WorkflowSimulator:
    """Simulates complex business workflows with multiple user journeys.

    Combines multiple user journeys to simulate realistic system usage
    with different user types and behaviors.

    Example:
        >>> simulator = WorkflowSimulator()
        >>>
        >>> # Add different user journeys
        >>> simulator.add_journey(browse_journey, weight=70)
        >>> simulator.add_journey(purchase_journey, weight=20)
        >>> simulator.add_journey(admin_journey, weight=10)
        >>>
        >>> # Run simulation
        >>> result = await simulator.run(users=100, duration=300)
    """

    def __init__(self):
        """Initialize the workflow simulator."""
        self.journeys: List[Tuple[UserJourney, float]] = []  # (journey, weight)
        self.results: List[ScenarioResult] = []

    def add_journey(
        self, journey: UserJourney, weight: float = 1.0
    ) -> "WorkflowSimulator":
        """Add a journey to the simulation.

        Args:
            journey: UserJourney to add
            weight: Probability weight for selection

        Returns:
            Self for chaining
        """
        self.journeys.append((journey, weight))
        return self

    def _select_journey(self) -> UserJourney:
        """Select a journey based on weights."""
        total_weight = sum(w for _, w in self.journeys)
        r = random.uniform(0, total_weight)

        cumulative = 0
        for journey, weight in self.journeys:
            cumulative += weight
            if r <= cumulative:
                return journey

        return self.journeys[-1][0]

    async def run(
        self, users: int, duration_seconds: int, ramp_up_seconds: int = 10
    ) -> Dict[str, Any]:
        """Run the workflow simulation.

        Args:
            users: Total concurrent users
            duration_seconds: Test duration
            ramp_up_seconds: Ramp up time

        Returns:
            Dictionary with combined results
        """
        logger.info(
            f"Starting workflow simulation with {len(self.journeys)} journey types, "
            f"{users} users"
        )

        start_time = datetime.utcnow()
        all_results: List[ScenarioResult] = []
        stop_event = asyncio.Event()

        async def user_worker(user_id: int):
            """Worker for a single user."""
            while not stop_event.is_set():
                journey = self._select_journey()
                metrics = await journey.execute_single_user(user_id)

                # Small delay before next journey
                await asyncio.sleep(random.uniform(1.0, 5.0))

        # Start all users
        tasks = []
        for i in range(users):
            task = asyncio.create_task(user_worker(i))
            tasks.append(task)

            if ramp_up_seconds > 0 and i < users - 1:
                await asyncio.sleep(ramp_up_seconds / users)

        # Run for duration
        await asyncio.sleep(duration_seconds)
        stop_event.set()

        # Wait for completion
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.utcnow()

        # Aggregate results
        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "concurrent_users": users,
            "journey_types": len(self.journeys),
            "journeys": [{"name": j.name, "weight": w} for j, w in self.journeys],
        }
