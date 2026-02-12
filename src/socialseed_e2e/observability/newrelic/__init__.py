"""New Relic integration for socialseed-e2e."""

from typing import Any, Dict, Optional
from socialseed_e2e.observability import ObservabilityProvider

try:
    import newrelic.agent
    NEWRELIC_AVAILABLE = True
except ImportError:
    NEWRELIC_AVAILABLE = False


class NewRelicProvider(ObservabilityProvider):
    """New Relic observability provider."""

    def __init__(self, license_key: str, app_name: str = "SocialSeed-E2E"):
        if not NEWRELIC_AVAILABLE:
            raise ImportError("newrelic library is required. Install it with 'pip install newrelic'")
        
        # In a real scenario, we might need a config file, 
        # but we can also use environment variables.
        # This implementation assumes the agent is initialized via NEW_RELIC_LICENSE_KEY env var
        # or manual initialization if possible.
        self.app_name = app_name

    def record_test_result(self, test_name: str, status: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None):
        """Record test result as a custom event in New Relic."""
        event_data = {
            'testName': test_name,
            'status': status,
            'duration_ms': duration_ms,
            'appName': self.app_name
        }
        if metadata:
            event_data.update(metadata)
        
        newrelic.agent.record_custom_event('E2ETestResult', event_data)

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric in New Relic."""
        # New Relic typically uses hierarchical metric names
        metric_name = f"Custom/E2E/{name}"
        newrelic.agent.record_custom_metric(metric_name, value)
