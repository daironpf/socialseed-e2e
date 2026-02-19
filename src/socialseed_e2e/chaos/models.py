"""
Models for Chaos Engineering module.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChaosType(str, Enum):
    """Types of chaos experiments."""

    NETWORK_LATENCY = "network_latency"
    NETWORK_PACKET_LOSS = "network_packet_loss"
    NETWORK_DNS = "network_dns_manipulation"
    NETWORK_PARTITION = "network_partition"
    SERVICE_DOWNTIME = "service_downtime"
    SERVICE_DEGRADATION = "service_degradation"
    SERVICE_CASCADING = "service_cascading_failure"
    RESOURCE_CPU = "resource_cpu_exhaustion"
    RESOURCE_MEMORY = "resource_memory_pressure"
    RESOURCE_DISK = "resource_disk_io_saturation"


class ExperimentStatus(str, Enum):
    """Status of chaos experiment."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class NetworkChaosConfig(BaseModel):
    """Configuration for network chaos experiments."""

    latency_ms: int = Field(
        default=100, description="Latency to inject in milliseconds"
    )
    jitter_ms: int = Field(default=10, description="Jitter variation in milliseconds")
    packet_loss_percent: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Packet loss percentage"
    )
    packet_corruption_percent: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Packet corruption percentage"
    )
    bandwidth_limit_mbps: Optional[int] = Field(
        default=None, description="Bandwidth limit in Mbps"
    )
    dns_failure_rate: float = Field(
        default=0.0, ge=0.0, le=100.0, description="DNS failure rate percentage"
    )
    target_hosts: List[str] = Field(
        default_factory=list, description="Target hosts to affect"
    )
    ports: List[int] = Field(default_factory=list, description="Target ports")

    model_config = {"populate_by_name": True}


class ServiceChaosConfig(BaseModel):
    """Configuration for service chaos experiments."""

    service_name: str = Field(..., description="Name of service to target")
    duration_seconds: int = Field(
        default=60, description="Duration of chaos in seconds"
    )
    downtime_seconds: int = Field(default=10, description="Service downtime duration")
    error_rate_percent: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Error rate to inject"
    )
    latency_increase_ms: int = Field(
        default=0, description="Latency increase in milliseconds"
    )
    cpu_load_percent: int = Field(
        default=0, ge=0, le=100, description="CPU load to apply"
    )
    memory_pressure_mb: int = Field(default=0, description="Memory pressure in MB")
    downstream_services: List[str] = Field(
        default_factory=list, description="Downstream services for cascading failure"
    )

    model_config = {"populate_by_name": True}


class ResourceChaosConfig(BaseModel):
    """Configuration for resource chaos experiments."""

    cpu_cores: int = Field(default=1, description="Number of CPU cores to consume")
    cpu_load_percent: float = Field(
        default=80.0, ge=0.0, le=100.0, description="CPU load percentage per core"
    )
    memory_mb: int = Field(default=512, description="Memory to consume in MB")
    disk_io_mbps: int = Field(default=100, description="Disk I/O rate in MB/s")
    disk_fill_percent: Optional[float] = Field(
        default=None, ge=0.0, le=100.0, description="Disk fill percentage"
    )
    io_wait_percent: float = Field(
        default=50.0, ge=0.0, le=100.0, description="I/O wait percentage"
    )

    model_config = {"populate_by_name": True}


class HealthCheckConfig(BaseModel):
    """Configuration for health checks during chaos."""

    endpoint: str = Field(..., description="Health check endpoint")
    interval_seconds: int = Field(default=5, description="Check interval")
    timeout_seconds: int = Field(default=10, description="Request timeout")
    expected_status_code: int = Field(default=200, description="Expected HTTP status")
    success_rate_threshold: float = Field(
        default=95.0, ge=0.0, le=100.0, description="Minimum success rate %"
    )
    max_recovery_time_seconds: int = Field(
        default=60, description="Maximum acceptable recovery time"
    )

    model_config = {"populate_by_name": True}


class ChaosExperiment(BaseModel):
    """Defines a chaos experiment."""

    id: str = Field(..., description="Unique experiment ID")
    name: str = Field(..., description="Experiment name")
    description: str = Field(default="", description="Experiment description")
    chaos_type: ChaosType = Field(..., description="Type of chaos")

    # Configuration
    network_config: Optional[NetworkChaosConfig] = Field(default=None)
    service_config: Optional[ServiceChaosConfig] = Field(default=None)
    resource_config: Optional[ResourceChaosConfig] = Field(default=None)

    # Target
    target_service: str = Field(..., description="Target service name")
    target_environment: str = Field(default="staging", description="Target environment")

    # Health checks
    health_checks: List[HealthCheckConfig] = Field(default_factory=list)

    # Timing
    duration_seconds: int = Field(default=300, description="Experiment duration")
    ramp_up_seconds: int = Field(default=10, description="Ramp up time")
    ramp_down_seconds: int = Field(default=10, description="Ramp down time")

    # Safety
    auto_stop_on_critical: bool = Field(
        default=True, description="Auto-stop if system critical"
    )
    max_error_rate: float = Field(
        default=50.0, description="Max acceptable error rate %"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(default="system", description="Creator of experiment")
    tags: List[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ChaosResult(BaseModel):
    """Results from a chaos experiment."""

    experiment_id: str = Field(..., description="Experiment ID")
    status: ExperimentStatus = Field(default=ExperimentStatus.PENDING)

    # Timing
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    duration_actual_seconds: float = Field(default=0.0)

    # Metrics
    requests_total: int = Field(default=0)
    requests_success: int = Field(default=0)
    requests_failed: int = Field(default=0)
    error_rate_percent: float = Field(default=0.0)
    avg_latency_ms: float = Field(default=0.0)
    p95_latency_ms: float = Field(default=0.0)
    p99_latency_ms: float = Field(default=0.0)

    # Health check results
    health_check_success_rate: float = Field(default=0.0)
    recovery_time_seconds: Optional[float] = Field(default=None)

    # Observations
    observations: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Pass/Fail
    success: bool = Field(default=False)
    failed_assertions: List[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class GameDayScenario(BaseModel):
    """Defines a GameDay scenario."""

    id: str = Field(..., description="Scenario ID")
    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")
    objectives: List[str] = Field(
        default_factory=list, description="Learning objectives"
    )

    # Experiments to run
    experiments: List[ChaosExperiment] = Field(default_factory=list)

    # Execution
    parallel_execution: bool = Field(
        default=False, description="Run experiments in parallel"
    )
    stop_on_failure: bool = Field(default=True, description="Stop if experiment fails")

    # Success criteria
    success_criteria: List[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class GameDayResult(BaseModel):
    """Results from a GameDay."""

    scenario_id: str = Field(..., description="Scenario ID")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    experiment_results: List[ChaosResult] = Field(default_factory=list)

    overall_success: bool = Field(default=False)
    objectives_met: List[str] = Field(default_factory=list)
    lessons_learned: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
