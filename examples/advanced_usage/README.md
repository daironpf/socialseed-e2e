# Advanced Usage Examples

This directory contains advanced examples demonstrating common testing scenarios with SocialSeed E2E.

## Examples Available

### 1. Authorization Headers (`auth_headers_example.py`)
Demonstrates different authentication methods:
- Basic Auth
- Bearer Token (JWT)
- API Key authentication
- Custom headers

### 2. Environment Variables (`env_variables_example.py`)
Shows how to:
- Load .env files
- Use environment variables in tests
- Configure services per environment
- Access secrets safely

### 3. Test Fixtures (`fixtures_example.py`)
Learn how to:
- Create setup/teardown logic
- Share state between tests
- Use page attributes for test data
- Clean up after tests

### 4. Parameterized Tests (`parameterized_tests_example.py`)
Explore:
- Running tests with multiple data sets
- Using test data from external files
- Dynamic test generation

## Quick Start

Run any example:

```bash
# Make sure dependencies are installed
pip install -r requirements.txt

# Run the example
python examples/advanced_usage/auth_headers_example.py
```

## Integration with e2e CLI

These patterns can be used with the e2e CLI:

```bash
# Initialize a project
e2e init my-project
cd my-project

# Add advanced patterns to your service
# Copy relevant examples to services/my-service/modules/
```

## Requirements

Each example may have specific requirements. Check the individual README in each example folder for details.

Common requirements:
- socialseed-e2e >= 0.1.0
- python-dotenv (for .env examples)
- pytest (for parameterized tests)
