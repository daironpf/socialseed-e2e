"""DataDog integration for socialseed-e2e."""

from typing import Any, Dict, Optional

from socialseed_e2e.observability import ObservabilityProvider

try:
    from datadog import api, initialize, statsd
    DATADOG_AVAILABLE = True
except ImportError:
    DATADOG_AVAILABLE = False


class DataDogProvider(ObservabilityProvider):
    """DataDog observability provider."""

    def __init__(self, api_key: str, app_key: Optional[str] = None, host_name: Optional[str] = None):
        if not DATADOG_AVAILABLE:
            raise ImportError("datadog library is required. Install it with 'pip install datadog'")

        options = {
            'api_key': api_key,
            'app_key': app_key,
            'api_host': 'https://api.datadoghq.com'
        }
        initialize(**options)
        self.host_name = host_name

    def record_test_result(self, test_name: str, status: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """Send test result to DataDog as a service check or event."""
        # Record duration as a metric
        statsd.timing('e2e.test.duration', duration_ms, tags=[f'test:{test_name}', f'status:{status}'])

        # Increment counter
        statsd.increment('e2e.test.count', tags=[f'test:{test_name}', f'status:{status}'])

        # Send an event for failures
        if status.lower() != 'passed' and status.lower() != 'ok':
            api.Event.create(
                title=f"E2E Test Failed: {test_name}",
                text=f"Test {test_name} failed with status {status}. Metadata: {metadata}",
                tags=[f'test:{test_name}', 'env:e2e', 'type:test_failure'],
                alert_type='error'
            )

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric in DataDog."""
        formatted_tags = []
        if tags:
            formatted_tags = [f"{k}:{v}" for k, v in tags.items()]

        statsd.gauge(f"e2e.custom.{name}", value, tags=formatted_tags)
