"""
Resource chaos injector for chaos engineering.

Provides resource-level chaos injection:
- CPU exhaustion
- Memory pressure
- Disk I/O saturation
- Disk space exhaustion
"""

import time
import uuid
import random
from typing import Any, Dict, List, Optional
from multiprocessing import Process, cpu_count

from ..models import (
    ChaosExperiment,
    ChaosResult,
    ChaosType,
    ExperimentStatus,
    ResourceChaosConfig,
)


class ResourceChaosInjector:
    """Resource-level chaos injector for resilience testing.

    Simulates resource exhaustion scenarios:
    - CPU overload
    - Memory pressure
    - Disk I/O saturation

    Example:
        injector = ResourceChaosInjector()

        config = ResourceChaosConfig(
            cpu_cores=2,
            cpu_load_percent=90.0,
            memory_mb=1024
        )

        result = injector.exhaust_cpu(
            experiment_id="res-001",
            config=config,
            duration_seconds=300
        )
    """

    def __init__(self):
        """Initialize resource chaos injector."""
        self.active_experiments: Dict[str, ChaosExperiment] = {}
        self.results: Dict[str, ChaosResult] = {}
        self._worker_processes: List[Process] = []

    def exhaust_cpu(
        self,
        experiment_id: str,
        config: ResourceChaosConfig,
        duration_seconds: int = 300,
    ) -> ChaosResult:
        """Simulate CPU exhaustion.

        Args:
            experiment_id: Unique experiment ID
            config: Resource chaos configuration
            duration_seconds: Duration of experiment

        Returns:
            ChaosResult with experiment results
        """
        experiment = ChaosExperiment(
            id=experiment_id,
            name=f"CPU Exhaustion - {config.cpu_cores} cores at {config.cpu_load_percent}%",
            description=f"Exhaust CPU with {config.cpu_cores} cores at {config.cpu_load_percent}% load",
            chaos_type=ChaosType.RESOURCE_CPU,
            resource_config=config,
            target_service="system",
            duration_seconds=duration_seconds,
        )

        self.active_experiments[experiment_id] = experiment

        result = ChaosResult(
            experiment_id=experiment_id,
            status=ExperimentStatus.RUNNING,
        )

        try:
            start_time = time.time()
            result.started_at = __import__("datetime").datetime.utcnow()

            # Start CPU workers
            workers = []
            for _ in range(config.cpu_cores):
                p = Process(
                    target=self._cpu_stress_worker,
                    args=(config.cpu_load_percent, duration_seconds),
                )
                p.start()
                workers.append(p)

            self._worker_processes.extend(workers)

            # Monitor
            elapsed = 0
            while elapsed < duration_seconds:
                time.sleep(1)
                elapsed = time.time() - start_time

            # Wait for workers to complete
            for p in workers:
                p.join(timeout=5)
                if p.is_alive():
                    p.terminate()

            result.completed_at = __import__("datetime").datetime.utcnow()
            result.duration_actual_seconds = elapsed
            result.success = True
            result.status = ExperimentStatus.COMPLETED

            result.observations.append(
                f"CPU exhaustion applied to {config.cpu_cores} cores"
            )
            result.observations.append(f"Target load: {config.cpu_load_percent}%")

        except Exception as e:
            result.status = ExperimentStatus.FAILED
            result.errors.append(str(e))

        self.results[experiment_id] = result
        return result

    def consume_memory(
        self,
        experiment_id: str,
        config: ResourceChaosConfig,
        duration_seconds: int = 300,
    ) -> ChaosResult:
        """Simulate memory pressure.

        Args:
            experiment_id: Unique experiment ID
            config: Resource chaos configuration
            duration_seconds: Duration of experiment

        Returns:
            ChaosResult with experiment results
        """
        experiment = ChaosExperiment(
            id=experiment_id,
            name=f"Memory Pressure - {config.memory_mb} MB",
            description=f"Apply {config.memory_mb} MB memory pressure",
            chaos_type=ChaosType.RESOURCE_MEMORY,
            resource_config=config,
            target_service="system",
            duration_seconds=duration_seconds,
        )

        self.active_experiments[experiment_id] = experiment

        result = ChaosResult(
            experiment_id=experiment_id,
            status=ExperimentStatus.RUNNING,
        )

        try:
            start_time = time.time()
            result.started_at = __import__("datetime").datetime.utcnow()

            # Consume memory
            memory_consumer = []
            chunk_size = 1024 * 1024  # 1 MB chunks
            target_chunks = config.memory_mb

            for _ in range(target_chunks):
                # Allocate memory
                memory_consumer.append(bytearray(chunk_size))

                # Check duration
                if time.time() - start_time >= duration_seconds:
                    break

                time.sleep(0.001)

            # Hold memory for remaining duration
            remaining = duration_seconds - (time.time() - start_time)
            if remaining > 0:
                time.sleep(remaining)

            # Release memory
            memory_consumer.clear()

            result.completed_at = __import__("datetime").datetime.utcnow()
            result.duration_actual_seconds = time.time() - start_time
            result.success = True
            result.status = ExperimentStatus.COMPLETED

            result.observations.append(
                f"Memory consumption: {len(memory_consumer)} MB allocated"
            )

        except Exception as e:
            result.status = ExperimentStatus.FAILED
            result.errors.append(str(e))

        self.results[experiment_id] = result
        return result

    def saturate_disk_io(
        self,
        experiment_id: str,
        config: ResourceChaosConfig,
        duration_seconds: int = 300,
    ) -> ChaosResult:
        """Simulate disk I/O saturation.

        Args:
            experiment_id: Unique experiment ID
            config: Resource chaos configuration
            duration_seconds: Duration of experiment

        Returns:
            ChaosResult with experiment results
        """
        experiment = ChaosExperiment(
            id=experiment_id,
            name=f"Disk I/O Saturation - {config.disk_io_mbps} MB/s",
            description=f"Saturate disk I/O at {config.disk_io_mbps} MB/s",
            chaos_type=ChaosType.RESOURCE_DISK,
            resource_config=config,
            target_service="system",
            duration_seconds=duration_seconds,
        )

        self.active_experiments[experiment_id] = experiment

        result = ChaosResult(
            experiment_id=experiment_id,
            status=ExperimentStatus.RUNNING,
        )

        try:
            import tempfile
            import os

            start_time = time.time()
            result.started_at = __import__("datetime").datetime.utcnow()

            # Create temp file for I/O operations
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_file = f.name
                chunk_size = 1024 * 1024  # 1 MB
                data = os.urandom(chunk_size)

                elapsed = 0
                total_written = 0

                while elapsed < duration_seconds:
                    # Write data
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                    total_written += chunk_size

                    # Control rate
                    target_time = total_written / (config.disk_io_mbps * 1024 * 1024)
                    actual_time = time.time() - start_time
                    if actual_time < target_time:
                        time.sleep(target_time - actual_time)

                    elapsed = time.time() - start_time

            # Cleanup
            os.unlink(temp_file)

            result.completed_at = __import__("datetime").datetime.utcnow()
            result.duration_actual_seconds = elapsed
            result.success = True
            result.status = ExperimentStatus.COMPLETED

            result.observations.append(
                f"Total data written: {total_written / (1024 * 1024):.2f} MB"
            )
            result.observations.append(f"Target rate: {config.disk_io_mbps} MB/s")

        except Exception as e:
            result.status = ExperimentStatus.FAILED
            result.errors.append(str(e))

        self.results[experiment_id] = result
        return result

    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop a running experiment.

        Args:
            experiment_id: Experiment ID to stop

        Returns:
            True if stopped successfully
        """
        if experiment_id in self.active_experiments:
            # Terminate worker processes
            for p in self._worker_processes:
                if p.is_alive():
                    p.terminate()
            self._worker_processes.clear()

            if experiment_id in self.results:
                self.results[experiment_id].status = ExperimentStatus.STOPPED
            return True
        return False

    def _cpu_stress_worker(self, load_percent: float, duration: int):
        """Worker process to consume CPU.

        Args:
            load_percent: Target CPU load percentage
            duration: Duration in seconds
        """
        start_time = time.time()

        while time.time() - start_time < duration:
            # Busy loop for load_percent of the time
            busy_time = load_percent / 100.0 * 0.1
            idle_time = 0.1 - busy_time

            end_busy = time.time() + busy_time
            while time.time() < end_busy:
                pass  # Busy work

            time.sleep(max(0, idle_time))
