"""Jaeger distributed tracing for socialseed-e2e."""

from typing import Any, Dict, Optional
from socialseed_e2e.observability import TracingProvider

try:
    from jaeger_client import Config
    import opentracing
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False


class JaegerProvider(TracingProvider):
    """Jaeger tracing provider."""

    def __init__(self, service_name: str = "socialseed-e2e", agent_host: str = "localhost"):
        if not JAEGER_AVAILABLE:
            raise ImportError("jaeger-client library is required. Install it with 'pip install jaeger-client'")
        
        config = Config(
            config={
                'sampler': {'type': 'const', 'param': 1},
                'local_agent': {'reporting_host': agent_host},
                'logging': True,
            },
            service_name=service_name,
            validate=True,
        )
        
        # this initializes the global tracer
        self.tracer = config.initialize_tracer()

    def start_span(self, name: str, tags: Optional[Dict[str, str]] = None) -> Any:
        """Start a Jaeger span."""
        return self.tracer.start_span(name, tags=tags)

    def end_span(self, span: Any):
        """Finish a Jaeger span."""
        if span:
            span.finish()

    def close(self):
        """Close the tracer."""
        if self.tracer:
            self.tracer.close()
