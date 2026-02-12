from socialseed_e2e.core import Priority, depends_on, priority, tag


@tag("smoke", "auth")
@priority(Priority.HIGH)
@depends_on("test_01_registration")
def run(page):
    """Example test: User Login."""
    print("Running login test...")
    # Verify dependency state if needed
    if not page.get_metadata("user_registered"):
        print("Warning: Registration state not found, but dependency should have ensured it ran.")

    page.set_metadata("logged_in", True)
