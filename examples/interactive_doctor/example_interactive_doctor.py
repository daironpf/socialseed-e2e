"""Example: Interactive Doctor for Test Failures

This example demonstrates how to use the AI-Driven Interactive Doctor
to diagnose and fix test failures automatically.

Example Scenarios:
    1. Type mismatch errors (String vs Integer)
    2. Missing required fields
    3. Validation errors
"""

from socialseed_e2e import (
    ErrorContext,
    InteractiveDoctor,
    run_interactive_doctor,
)


def example_1_basic_diagnosis():
    """Example 1: Basic error diagnosis and fix."""
    print("=" * 60)
    print("Example 1: Basic Error Diagnosis")
    print("=" * 60)

    # Create doctor instance
    doctor = InteractiveDoctor(
        project_root=".",
        interactive=False,  # Set to True for interactive mode
    )

    # Start session
    session = doctor.start_session()

    # Simulate a type mismatch error
    context = ErrorContext(
        test_name="test_create_user",
        service_name="user-service",
        endpoint_path="/users",
        http_method="POST",
        error_message="Validation error: 'age' expected Integer but got String",
        request_data={
            "name": "John Doe",
            "email": "john@example.com",
            "age": "25",  # String instead of Integer
        },
        response_data={
            "error": "Validation failed",
            "field": "age",
            "expected": "integer",
            "got": "string",
        },
        response_status=400,
    )

    # Diagnose and fix
    result = doctor.diagnose_and_fix(context, session)

    # End session and get summary
    summary = doctor.end_session(session)

    print("\n📊 Session Summary:")
    print(f"   Duration: {summary['duration_seconds']:.1f}s")
    print(f"   Errors Analyzed: {summary['total_errors']}")
    print(f"   Fixes Applied: {summary['applied_fixes']}")
    print(f"   Success Rate: {summary['fix_success_rate']:.0f}%")


def example_2_missing_field():
    """Example 2: Missing required field error."""
    print("\n" + "=" * 60)
    print("Example 2: Missing Required Field")
    print("=" * 60)

    doctor = InteractiveDoctor(".", interactive=False)
    session = doctor.start_session()

    # Simulate missing field error
    context = ErrorContext(
        test_name="test_update_profile",
        service_name="profile-service",
        endpoint_path="/profile",
        http_method="PUT",
        error_message="Missing required field: 'user_id' is required",
        request_data={
            "name": "Updated Name",
            "bio": "New bio",
            # Missing: user_id
        },
        response_status=422,
    )

    result = doctor.diagnose_and_fix(context, session)
    summary = doctor.end_session(session)

    print(f"\n✓ Fix applied: {result is not None}")


def example_3_validation_error():
    """Example 3: Validation constraint error."""
    print("\n" + "=" * 60)
    print("Example 3: Validation Error")
    print("=" * 60)

    doctor = InteractiveDoctor(".", interactive=False)
    session = doctor.start_session()

    # Simulate validation error
    context = ErrorContext(
        test_name="test_create_product",
        service_name="product-service",
        endpoint_path="/products",
        http_method="POST",
        error_message="Validation error: 'price' must be greater than 0",
        request_data={
            "name": "Test Product",
            "price": -10,  # Invalid: negative price
        },
        response_status=400,
    )

    result = doctor.diagnose_and_fix(context, session)
    summary = doctor.end_session(session)

    print(f"\n✓ Session completed with {summary['applied_fixes']} fixes applied")


def example_4_cli_usage():
    """Example 4: Using Interactive Doctor via CLI."""
    print("\n" + "=" * 60)
    print("Example 4: CLI Usage")
    print("=" * 60)

    print("""
To use the Interactive Doctor from CLI:

    # Run doctor in interactive mode
    e2e doctor
    
    # Run doctor for a specific test
    e2e doctor --test test_create_user
    
    # Run doctor with specific error
    e2e doctor --test test_login --error "Validation error"
    
    # Run in automatic mode (non-interactive)
    e2e doctor --auto
    
    # Run after test execution with failures
    e2e run --doctor

The doctor will:
    1. Analyze the error message
    2. Query the Project Manifest
    3. Suggest appropriate fixes
    4. Apply fixes automatically or guide you
""")


def example_5_programmatic_usage():
    """Example 5: Advanced programmatic usage."""
    print("\n" + "=" * 60)
    print("Example 5: Advanced Programmatic Usage")
    print("=" * 60)

    print("""
from socialseed_e2e import (
    InteractiveDoctor,
    ErrorContext,
    ErrorAnalyzer,
    FixSuggester,
    AutoFixer,
)

# Step 1: Analyze error
analyzer = ErrorAnalyzer("/path/to/project")
context = ErrorContext(
    test_name="test_api",
    service_name="my-service",
    error_message="Validation error"
)
diagnosis = analyzer.analyze(context)

print(f"Error Type: {diagnosis.error_type}")
print(f"Confidence: {diagnosis.confidence:.0%}")
print(f"Description: {diagnosis.description}")

# Step 2: Get fix suggestions
suggester = FixSuggester()
suggestions = suggester.suggest_fixes(diagnosis)

for i, suggestion in enumerate(suggestions, 1):
    print(f"{i}. {suggestion.title}")
    print(f"   Strategy: {suggestion.strategy}")
    print(f"   Automatic: {suggestion.automatic}")
    print(f"   Description: {suggestion.description}")

# Step 3: Apply fix automatically
fixer = AutoFixer("/path/to/project")
if suggestions and suggestions[0].automatic:
    result = fixer.apply_fix(diagnosis, suggestions[0])
    if result.success:
        print(f"✓ Fix applied to: {result.files_modified}")
    else:
        print(f"✗ Fix failed: {result.error_message}")
""")


if __name__ == "__main__":
    print("\n" + "🔧 " * 30)
    print("Interactive Doctor Examples for socialseed-e2e")
    print("🔧 " * 30 + "\n")

    # Run examples
    print("NOTE: These examples use non-interactive mode for demonstration.")
    print("Set interactive=True to use the interactive CLI prompts.\n")

    try:
        example_1_basic_diagnosis()
    except Exception as e:
        print(f"Example 1 error (expected if no manifest): {e}")

    try:
        example_2_missing_field()
    except Exception as e:
        print(f"Example 2 error: {e}")

    try:
        example_3_validation_error()
    except Exception as e:
        print(f"Example 3 error: {e}")

    example_4_cli_usage()
    example_5_programmatic_usage()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("""
For more information:
    - Documentation: docs/interactive-doctor.md
    - API Reference: socialseed_e2e.core.interactive_doctor
    - CLI Help: e2e doctor --help
    """)
