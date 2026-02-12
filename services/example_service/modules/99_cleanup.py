"""Example test module for system cleanup."""
from socialseed_e2e.core import Priority, priority, tag


@tag("cleanup")
@priority(Priority.LOW)
def run(page):
    """Run system cleanup test."""
    print("Running cleanup test...")
    # Simulated cleanup logic
    pass
