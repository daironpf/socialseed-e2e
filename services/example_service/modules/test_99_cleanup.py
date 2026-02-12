from socialseed_e2e.core import Priority, priority, tag


@tag("cleanup")
@priority(Priority.LOW)
def run(page):
    """Example test: System Cleanup."""
    print("Running cleanup test...")
    # Simulated cleanup logic
    pass
