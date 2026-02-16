# Basic API Test Example - Human Written (Non-AI)

This example demonstrates how to write a simple, deterministic API test manually
without relying on AI agents. It uses JSONPlaceholder (https://jsonplaceholder.typicode.com/),
a free fake REST API for testing and prototyping.

## What This Example Shows

- **Manual Test Writing**: How to write tests by hand using the framework
- **Real API Testing**: Makes actual HTTP calls to a public API
- **Simple Assertions**: Validates status codes and response data
- **Heavily Commented**: Every step is explained for learning purposes

## Running This Example

```bash
# From the examples/basic_api_test directory
e2e run
```

## Structure

```
basic_api_test/
├── README.md                    # This file
├── e2e.conf                     # Framework configuration
└── services/
    └── jsonplaceholder/         # Service directory
        ├── __init__.py
        ├── jsonplaceholder_page.py  # Page class for API calls
        └── modules/
            └── 01_get_post.py       # Test module
```

## Key Concepts Demonstrated

1. **Page Object Pattern**: The `JsonPlaceholderPage` class encapsulates API interactions
2. **Test Module Structure**: Uses the standard `run()` function pattern
3. **Assertions**: Validates both HTTP status codes and JSON response bodies
4. **Documentation**: Extensive comments explaining every step

## Notes

- This test makes real HTTP calls to https://jsonplaceholder.typicode.com/
- No AI agents are involved in this test - it's 100% human-written
- The API is free and requires no authentication for GET requests
- The test is deterministic - it always fetches the same post (ID: 1)
