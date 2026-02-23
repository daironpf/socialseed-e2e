"""
GameDay orchestrator for chaos engineering.

Automates GameDay scenarios for team learning and resilience validation.
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import (
    ChaosExperiment,
    ChaosResult,
    ExperimentStatus,
    GameDayResult,
    GameDayScenario,
)
from ..network.network_chaos import NetworkChaosInjector
from ..resource.resource_chaos import ResourceChaosInjector
from ..service.service_chaos import ServiceChaosInjector


class GameDayOrchestrator:
    """Orchestrates GameDay chaos engineering scenarios.

    Coordinates multiple chaos experiments for team learning:
    - Sequential or parallel experiment execution
    - Real-time monitoring and observations
    - Success criteria validation
    - Automated reporting

    Example:
        orchestrator = GameDayOrchestrator()

        # Create scenario
        scenario = GameDayScenario(
            id="gameday-001",
            name="Payment System Resilience",
            description="Test payment system under various failure modes",
            objectives=["Validate retry logic", "Test circuit breakers"],
            experiments=[exp1, exp2, exp3]
        )

        # Run GameDay
        result = orchestrator.run_gameday(scenario)
    """

    def __init__(self):
        """Initialize GameDay orchestrator."""
        self.network_injector = NetworkChaosInjector()
        self.service_injector = ServiceChaosInjector()
        self.resource_injector = ResourceChaosInjector()
        self.active_scenarios: Dict[str, GameDayScenario] = {}
        self.results: Dict[str, GameDayResult] = {}

    def run_gameday(self, scenario: GameDayScenario) -> GameDayResult:
        """Run a complete GameDay scenario.

        Args:
            scenario: GameDay scenario to execute

        Returns:
            GameDayResult with complete results
        """
        result = GameDayResult(
            scenario_id=scenario.id,
            started_at=datetime.utcnow(),
        )

        self.active_scenarios[scenario.id] = scenario

        try:
            # Execute experiments
            if scenario.parallel_execution:
                # Run in parallel (simplified - in real implementation use asyncio/multiprocessing)
                for experiment in scenario.experiments:
                    exp_result = self._run_experiment(experiment)
                    result.experiment_results.append(exp_result)

                    if not exp_result.success and scenario.stop_on_failure:
                        result.lessons_learned.append(
                            f"Experiment {experiment.id} failed - stopping GameDay"
                        )
                        break
            else:
                # Run sequentially
                for experiment in scenario.experiments:
                    exp_result = self._run_experiment(experiment)
                    result.experiment_results.append(exp_result)

                    if not exp_result.success and scenario.stop_on_failure:
                        result.lessons_learned.append(
                            f"Experiment {experiment.id} failed - stopping GameDay"
                        )
                        break

                    # Small delay between experiments
                    time.sleep(5)

            # Evaluate success criteria
            result.objectives_met = self._evaluate_objectives(scenario, result)
            result.overall_success = all(r.success for r in result.experiment_results)

            # Generate lessons learned
            result.lessons_learned.extend(self._generate_lessons_learned(result))

            # Generate action items
            result.action_items = self._generate_action_items(result)

            result.completed_at = datetime.utcnow()

        except Exception as e:
            result.lessons_learned.append(f"GameDay failed with error: {str(e)}")

        self.results[scenario.id] = result
        return result

    def create_scenario(
        self,
        name: str,
        description: str,
        objectives: List[str],
        experiments: List[ChaosExperiment],
        parallel: bool = False,
        stop_on_failure: bool = True,
    ) -> GameDayScenario:
        """Create a new GameDay scenario.

        Args:
            name: Scenario name
            description: Scenario description
            objectives: Learning objectives
            experiments: List of experiments to run
            parallel: Run experiments in parallel
            stop_on_failure: Stop if any experiment fails

        Returns:
            GameDayScenario
        """
        return GameDayScenario(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            objectives=objectives,
            experiments=experiments,
            parallel_execution=parallel,
            stop_on_failure=stop_on_failure,
        )

    def get_scenario_status(self, scenario_id: str) -> Optional[GameDayResult]:
        """Get status of a GameDay scenario.

        Args:
            scenario_id: Scenario ID

        Returns:
            GameDayResult or None
        """
        return self.results.get(scenario_id)

    def generate_report(self, scenario_id: str) -> Dict[str, Any]:
        """Generate a comprehensive GameDay report.

        Args:
            scenario_id: Scenario ID

        Returns:
            Report dictionary
        """
        result = self.results.get(scenario_id)
        scenario = self.active_scenarios.get(scenario_id)

        if not result or not scenario:
            return {"error": "Scenario not found"}

        return {
            "scenario": {
                "id": scenario.id,
                "name": scenario.name,
                "description": scenario.description,
                "objectives": scenario.objectives,
            },
            "execution": {
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat()
                if result.completed_at
                else None,
                "duration_minutes": (
                    result.completed_at - result.started_at
                ).total_seconds()
                / 60
                if result.completed_at
                else None,
            },
            "results": {
                "overall_success": result.overall_success,
                "experiments_run": len(result.experiment_results),
                "experiments_passed": sum(
                    1 for r in result.experiment_results if r.success
                ),
                "experiments_failed": sum(
                    1 for r in result.experiment_results if not r.success
                ),
            },
            "objectives": {
                "total": len(scenario.objectives),
                "met": len(result.objectives_met),
                "list": result.objectives_met,
            },
            "lessons_learned": result.lessons_learned,
            "action_items": result.action_items,
        }

    def _run_experiment(self, experiment: ChaosExperiment) -> ChaosResult:
        """Run a single chaos experiment.

        Args:
            experiment: Experiment to run

        Returns:
            ChaosResult
        """
        # Route to appropriate injector based on chaos type
        if experiment.chaos_type.value.startswith("network"):
            if experiment.network_config:
                return self.network_injector.run_experiment(
                    experiment_id=experiment.id,
                    config=experiment.network_config,
                    target_service=experiment.target_service,
                    duration_seconds=experiment.duration_seconds,
                )

        elif experiment.chaos_type.value.startswith("service"):
            if experiment.service_config:
                if experiment.chaos_type.value == "service_downtime":
                    return self.service_injector.simulate_downtime(
                        experiment_id=experiment.id,
                        config=experiment.service_config,
                        duration_seconds=experiment.duration_seconds,
                    )
                elif experiment.chaos_type.value == "service_cascading":
                    return self.service_injector.simulate_cascading_failure(
                        experiment_id=experiment.id,
                        primary_service=experiment.target_service,
                        downstream_services=experiment.service_config.downstream_services,
                    )

        elif experiment.chaos_type.value.startswith("resource"):
            if experiment.resource_config:
                if experiment.chaos_type.value == "resource_cpu":
                    return self.resource_injector.exhaust_cpu(
                        experiment_id=experiment.id,
                        config=experiment.resource_config,
                        duration_seconds=experiment.duration_seconds,
                    )
                elif experiment.chaos_type.value == "resource_memory":
                    return self.resource_injector.consume_memory(
                        experiment_id=experiment.id,
                        config=experiment.resource_config,
                        duration_seconds=experiment.duration_seconds,
                    )

        # Default error result
        return ChaosResult(
            experiment_id=experiment.id,
            status=ExperimentStatus.FAILED,
            errors=["Unknown chaos type or missing configuration"],
        )

    def _evaluate_objectives(
        self, scenario: GameDayScenario, result: GameDayResult
    ) -> List[str]:
        """Evaluate if learning objectives were met.

        Args:
            scenario: GameDay scenario
            result: GameDay result

        Returns:
            List of met objectives
        """
        met = []

        for objective in scenario.objectives:
            # Simple heuristic: if experiments passed, objectives likely met
            # In real implementation, use more sophisticated evaluation
            if result.overall_success:
                met.append(objective)

        return met

    def _generate_lessons_learned(self, result: GameDayResult) -> List[str]:
        """Generate lessons learned from GameDay.

        Args:
            result: GameDay result

        Returns:
            List of lessons
        """
        lessons = []

        # Analyze experiment results
        for exp_result in result.experiment_results:
            if exp_result.success:
                lessons.append(
                    f"System handled {exp_result.experiment_id} successfully"
                )
            else:
                lessons.append(
                    f"System struggled with {exp_result.experiment_id}: {', '.join(exp_result.errors)}"
                )

            # Add specific observations
            for obs in exp_result.observations:
                lessons.append(f"Observation: {obs}")

        return lessons

    def _generate_action_items(self, result: GameDayResult) -> List[str]:
        """Generate action items from GameDay results.

        Args:
            result: GameDay result

        Returns:
            List of action items
        """
        actions = []

        for exp_result in result.experiment_results:
            if not exp_result.success:
                actions.append(
                    f"Investigate and fix issues with {exp_result.experiment_id}"
                )

            if exp_result.error_rate_percent > 10:
                actions.append(
                    f"Improve error handling (current error rate: {exp_result.error_rate_percent:.1f}%)"
                )

            if (
                exp_result.recovery_time_seconds
                and exp_result.recovery_time_seconds > 30
            ):
                actions.append(
                    f"Reduce recovery time (currently {exp_result.recovery_time_seconds:.0f}s)"
                )

        if not actions:
            actions.append("Continue monitoring system resilience")

        return actions
