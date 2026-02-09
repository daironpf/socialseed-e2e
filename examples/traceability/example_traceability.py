"""Example: Visual Traceability with Sequence Diagrams

This example demonstrates how to use the Visual Traceability features
of socialseed-e2e to generate sequence diagrams and logic flow maps
from test execution.

Requirements:
    - socialseed-e2e installed
    - A running API to test (the example uses a mock)
"""

from socialseed_e2e import BasePage, enable_traceability, TraceContext, TraceReporter


def example_1_basic_traceability():
    """Example 1: Basic traceability with automatic sequence diagrams."""
    print("=" * 60)
    print("Example 1: Basic Traceability")
    print("=" * 60)

    # Enable traceability
    collector = enable_traceability()

    # Create a test page
    page = BasePage("https://jsonplaceholder.typicode.com")
    page.setup()

    try:
        # Use TraceContext to automatically trace test execution
        with TraceContext("test_get_posts", "jsonplaceholder-api"):
            # Make API calls - they will be automatically traced
            response = page.get("/posts/1")
            page.assert_ok(response)

            data = page.assert_json(response)
            assert "id" in data
            assert data["id"] == 1

        print("✓ Test completed successfully")

    finally:
        page.teardown()

    # Generate report
    reporter = TraceReporter()
    report = reporter.generate_report()

    # Save reports
    reporter.save_html_report(report, "example1_report.html")
    reporter.save_markdown_report(report, "example1_report.md")

    print(f"\n📊 Report generated:")
    print(f"   - Tests: {report.summary['total_tests']}")
    print(f"   - Interactions: {report.summary['total_interactions']}")
    print(f"   - Components: {report.summary['total_components']}")

    # Print sequence diagram
    if report.sequence_diagrams:
        print(f"\n📈 Sequence Diagram (Mermaid):")
        print("-" * 40)
        print(report.sequence_diagrams[0].content)
        print("-" * 40)


def example_2_manual_tracing():
    """Example 2: Manual tracing with custom interactions."""
    print("\n" + "=" * 60)
    print("Example 2: Manual Tracing")
    print("=" * 60)

    from socialseed_e2e.core.traceability import (
        TraceCollector,
        TraceConfig,
        InteractionType,
        LogicBranchType,
    )

    # Create collector with custom config
    config = TraceConfig(
        enabled=True,
        capture_request_body=True,
        capture_response_body=True,
        track_logic_branches=True,
        output_format="mermaid",
    )
    collector = TraceCollector(config)

    # Start trace
    collector.start_trace("test_user_workflow", "user-service")

    # Register components
    collector.register_component("Client", "client")
    collector.register_component("Auth-Service", "service")
    collector.register_component("User-Database", "database")

    # Record interactions manually
    collector.record_interaction(
        from_component="Client",
        to_component="Auth-Service",
        action="POST /auth/login",
        interaction_type=InteractionType.HTTP_REQUEST,
        request_data={"username": "john.doe", "password": "***"},
        status="success",
        duration_ms=120.5,
    )

    # Record logic branch
    collector.record_logic_branch(
        condition="credentials_valid",
        decision="true",
        branch_type=LogicBranchType.CONDITIONAL,
        reason="Username and password match database records",
    )

    collector.record_interaction(
        from_component="Auth-Service",
        to_component="User-Database",
        action="SELECT user_permissions",
        interaction_type=InteractionType.DATABASE_QUERY,
        status="success",
        duration_ms=45.0,
    )

    # Record assertion
    collector.record_assertion(assertion="user.has_permission('read')", passed=True)

    collector.record_interaction(
        from_component="Auth-Service",
        to_component="Client",
        action="200 OK with JWT token",
        interaction_type=InteractionType.HTTP_RESPONSE,
        response_data={"token": "eyJhbGciOiJIUzI1NiIs...", "expires_in": 3600},
        status="success",
        duration_ms=5.0,
    )

    # End trace
    collector.end_trace("passed")

    # Generate and display report
    from socialseed_e2e.core.traceability import TraceReporter

    reporter = TraceReporter(collector)
    report = reporter.generate_report()

    print(f"\n📊 Trace Summary:")
    print(f"   - Interactions: {report.summary['total_interactions']}")
    print(f"   - Logic Branches: {report.summary['total_logic_branches']}")
    print(f"   - Components: {report.summary['total_components']}")

    if report.sequence_diagrams:
        print(f"\n📈 Sequence Diagram:")
        print("-" * 40)
        print(report.sequence_diagrams[0].content)
        print("-" * 40)

    if report.logic_flows:
        print(f"\n🔄 Logic Flow:")
        print("-" * 40)
        print(report.logic_flows[0].flow_description[:500])
        print("..." if len(report.logic_flows[0].flow_description) > 500 else "")
        print("-" * 40)


def example_3_cli_usage():
    """Example 3: Using traceability via CLI."""
    print("\n" + "=" * 60)
    print("Example 3: CLI Usage")
    print("=" * 60)

    print("""
To enable traceability when running tests via CLI, use the --trace flag:

    e2e run --trace

You can also customize the output:

    # Generate PlantUML diagrams instead of Mermaid
    e2e run --trace --trace-format plantuml

    # Specify output directory
    e2e run --trace --trace-output ./my-reports

    # Run specific service with traceability
    e2e run --service auth-service --trace

The following reports will be generated in e2e_reports/:
    - traceability_report.html (Interactive HTML report)
    - traceability_report.md (Markdown report)
    - traceability_report.json (JSON data)
""")


def example_4_integration_with_tests():
    """Example 4: Integration with existing test modules."""
    print("\n" + "=" * 60)
    print("Example 4: Integration with Test Modules")
    print("=" * 60)

    print("""
You can integrate traceability into your existing test modules:

    # In your test module (e.g., services/auth/modules/01_login.py)
    from socialseed_e2e import TraceContext, record_logic_branch

    def run(page):
        with TraceContext("test_login", "auth-service"):
            # Login request
            response = page.post("/login", json={
                "username": "test@example.com",
                "password": "password123"
            })

            # Record conditional logic
            if response.status == 200:
                record_logic_branch(
                    condition="response.status == 200",
                    decision="success_path",
                    reason="Valid credentials"
                )
                data = response.json()
                assert "token" in data
            else:
                record_logic_branch(
                    condition="response.status == 200",
                    decision="error_path",
                    reason="Invalid credentials"
                )
                assert False, "Login failed"

The trace will automatically capture:
- All HTTP requests/responses
- Logic branches and decisions
- Assertions and their results
- Timing information
""")


if __name__ == "__main__":
    print("\n" + "🚀 " * 30)
    print("Visual Traceability Examples for socialseed-e2e")
    print("🚀 " * 30 + "\n")

    # Run examples
    try:
        example_1_basic_traceability()
    except Exception as e:
        print(f"Example 1 error (expected if no API): {e}")

    example_2_manual_tracing()
    example_3_cli_usage()
    example_4_integration_with_tests()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("""
For more information:
    - Documentation: docs/traceability.md
    - API Reference: socialseed_e2e.core.traceability
    - CLI Help: e2e run --help
    """)
