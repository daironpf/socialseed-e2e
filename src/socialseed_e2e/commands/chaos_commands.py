"""
CLI commands for chaos engineering.
"""

import time

import click

from ...chaos import (
    ChaosExperiment,
    ChaosType,
    GameDayOrchestrator,
    NetworkChaosConfig,
    NetworkChaosInjector,
    RecoveryValidator,
    ResourceChaosConfig,
    ResourceChaosInjector,
    ServiceChaosConfig,
    ServiceChaosInjector,
)


@click.group(name="chaos")
def chaos_group():
    """Chaos engineering commands."""
    pass


@chaos_group.command(name="network")
@click.option("--target", "-t", required=True, help="Target service name")
@click.option("--latency", "-l", default=100, help="Latency in milliseconds")
@click.option("--jitter", "-j", default=10, help="Jitter in milliseconds")
@click.option("--packet-loss", "-p", default=0.0, help="Packet loss percentage")
@click.option("--duration", "-d", default=300, help="Duration in seconds")
@click.option("--dns-failure", default=0.0, help="DNS failure rate percentage")
def network(target, latency, jitter, packet_loss, duration, dns_failure):
    """Run network chaos experiments."""
    click.echo(f"🌐 Running network chaos on {target}...")
    click.echo(f"   Latency: {latency}ms (+/- {jitter}ms)")
    click.echo(f"   Packet Loss: {packet_loss}%")
    click.echo(f"   DNS Failure Rate: {dns_failure}%")
    click.echo(f"   Duration: {duration}s")

    injector = NetworkChaosInjector()
    config = NetworkChaosConfig(
        latency_ms=latency,
        jitter_ms=jitter,
        packet_loss_percent=packet_loss,
        dns_failure_rate=dns_failure,
    )

    result = injector.run_experiment(
        experiment_id=f"net-{int(time.time())}",
        config=config,
        target_service=target,
        duration_seconds=duration,
    )

    _display_result(result)


@chaos_group.command(name="service")
@click.option("--service", "-s", required=True, help="Target service name")
@click.option("--downtime", "-d", default=30, help="Downtime duration in seconds")
@click.option("--error-rate", "-e", default=0.0, help="Error rate percentage")
@click.option("--duration", "-t", default=300, help="Experiment duration in seconds")
def service(service, downtime, error_rate, duration):
    """Run service chaos experiments."""
    click.echo(f"🔧 Running service chaos on {service}...")
    click.echo(f"   Downtime: {downtime}s")
    click.echo(f"   Error Rate: {error_rate}%")
    click.echo(f"   Duration: {duration}s")

    injector = ServiceChaosInjector()
    config = ServiceChaosConfig(
        service_name=service,
        downtime_seconds=downtime,
        error_rate_percent=error_rate,
    )

    result = injector.simulate_downtime(
        experiment_id=f"svc-{int(time.time())}",
        config=config,
        duration_seconds=duration,
    )

    _display_result(result)


@chaos_group.command(name="resource")
@click.option("--cpu-cores", "-c", default=1, help="Number of CPU cores")
@click.option("--cpu-load", default=80.0, help="CPU load percentage")
@click.option("--memory", "-m", default=512, help="Memory to consume in MB")
@click.option("--duration", "-d", default=300, help="Duration in seconds")
def resource(cpu_cores, cpu_load, memory, duration):
    """Run resource chaos experiments."""
    click.echo("💾 Running resource chaos...")
    click.echo(f"   CPU: {cpu_cores} cores at {cpu_load}%")
    click.echo(f"   Memory: {memory} MB")
    click.echo(f"   Duration: {duration}s")

    injector = ResourceChaosInjector()
    config = ResourceChaosConfig(
        cpu_cores=cpu_cores,
        cpu_load_percent=cpu_load,
        memory_mb=memory,
    )

    result = injector.exhaust_cpu(
        experiment_id=f"res-{int(time.time())}",
        config=config,
        duration_seconds=duration,
    )

    _display_result(result)


@chaos_group.command(name="gameday")
@click.option("--name", "-n", required=True, help="GameDay scenario name")
@click.option("--service", "-s", required=True, help="Target service")
@click.option(
    "--parallel/--sequential", default=False, help="Run experiments in parallel"
)
def gameday(name, service, parallel):
    """Run a GameDay chaos scenario."""
    click.echo(f"🎮 Running GameDay: {name}")
    click.echo(f"   Target: {service}")
    click.echo(f"   Mode: {'Parallel' if parallel else 'Sequential'}")

    orchestrator = GameDayOrchestrator()

    # Create experiments
    experiments = [
        ChaosExperiment(
            id="net-latency",
            name="Network Latency",
            chaos_type=ChaosType.NETWORK_LATENCY,
            network_config=NetworkChaosConfig(latency_ms=200),
            target_service=service,
        ),
        ChaosExperiment(
            id="svc-downtime",
            name="Service Downtime",
            chaos_type=ChaosType.SERVICE_DOWNTIME,
            service_config=ServiceChaosConfig(
                service_name=service, downtime_seconds=30
            ),
            target_service=service,
        ),
    ]

    scenario = orchestrator.create_scenario(
        name=name,
        description=f"GameDay scenario for {service}",
        objectives=["Test system resilience", "Validate recovery procedures"],
        experiments=experiments,
        parallel=parallel,
    )

    result = orchestrator.run_gameday(scenario)

    click.echo("\n📊 GameDay Results:")
    click.echo(f"   Overall Success: {'✅' if result.overall_success else '❌'}")
    click.echo(f"   Experiments Run: {len(result.experiment_results)}")
    click.echo(
        f"   Objectives Met: {len(result.objectives_met)}/{len(scenario.objectives)}"
    )

    if result.lessons_learned:
        click.echo("\n📚 Lessons Learned:")
        for lesson in result.lessons_learned[:5]:
            click.echo(f"   • {lesson}")

    if result.action_items:
        click.echo("\n✅ Action Items:")
        for item in result.action_items[:5]:
            click.echo(f"   • {item}")


@chaos_group.command(name="validate")
@click.option("--endpoint", "-e", required=True, help="Health check endpoint")
@click.option("--interval", "-i", default=5, help="Check interval in seconds")
@click.option("--timeout", "-t", default=60, help="Timeout in seconds")
@click.option("--threshold", default=95.0, help="Success rate threshold")
def validate(endpoint, interval, timeout, threshold):
    """Validate system recovery after chaos."""
    click.echo(f"🔄 Validating recovery at {endpoint}...")
    click.echo(f"   Interval: {interval}s")
    click.echo(f"   Timeout: {timeout}s")
    click.echo(f"   Threshold: {threshold}%")

    validator = RecoveryValidator()
    config = validator.create_health_check(
        endpoint=endpoint,
        interval_seconds=interval,
        success_rate_threshold=threshold,
    )

    result = validator.validate_recovery(config, timeout_seconds=timeout)

    if result["recovered"]:
        click.echo("\n✅ System recovered successfully!")
        click.echo(f"   Recovery Time: {result['recovery_time_seconds']:.1f}s")
        click.echo(f"   Success Rate: {result['success_rate']:.1f}%")
    else:
        click.echo("\n❌ System did not recover within timeout")
        click.echo(f"   Success Rate: {result['success_rate']:.1f}%")
        click.echo(f"   Total Checks: {result['total_checks']}")


def _display_result(result):
    """Display chaos experiment result."""
    click.echo("\n📊 Experiment Results:")
    click.echo(f"   Status: {result.status.value}")
    click.echo(f"   Success: {'✅' if result.success else '❌'}")
    click.echo(f"   Total Requests: {result.requests_total}")
    click.echo(f"   Successful: {result.requests_success}")
    click.echo(f"   Failed: {result.requests_failed}")
    click.echo(f"   Error Rate: {result.error_rate_percent:.2f}%")

    if result.avg_latency_ms > 0:
        click.echo(f"   Avg Latency: {result.avg_latency_ms:.1f}ms")
        click.echo(f"   P95 Latency: {result.p95_latency_ms:.1f}ms")
        click.echo(f"   P99 Latency: {result.p99_latency_ms:.1f}ms")

    if result.observations:
        click.echo("\n🔍 Observations:")
        for obs in result.observations[:3]:
            click.echo(f"   • {obs}")

    if result.errors:
        click.echo("\n⚠️  Errors:")
        for error in result.errors[:3]:
            click.echo(f"   • {error}")


def get_chaos_group():
    """Return chaos command group."""
    return chaos_group


def register_chaos_commands(cli):
    """Legacy registration function."""
    cli.add_command(chaos_group)
