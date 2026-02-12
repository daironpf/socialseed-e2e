from socialseed_e2e.core import Priority, priority, tag


@tag("smoke", "account")
@priority(Priority.CRITICAL)
def run(page):
    """Example test: User Registration."""
    print("Running registration test...")
    # Simulated logic
    page.set_metadata("user_registered", True)
