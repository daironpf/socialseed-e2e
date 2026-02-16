"""Test module: Fetch and validate a post from JSONPlaceholder API.

This is a HUMAN-WRITTEN test module that demonstrates how to write standard,
deterministic API tests manually without relying on AI agents.

WHAT THIS TEST DOES:
-------------------
1. Makes a GET request to https://jsonplaceholder.typicode.com/posts/1
2. Validates the HTTP status code is 200 (OK)
3. Validates the response body contains expected data structure
4. Returns the response for the framework to track

WHY THIS IS USEFUL:
------------------
- Shows the "golden path" for writing basic API tests
- Demonstrates proper assertion patterns
- Can be run with: e2e run --service jsonplaceholder
- No AI involvement - 100% deterministic and predictable
"""

# Import the APIResponse type from Playwright
# This is the type returned by all HTTP methods (get, post, put, delete)
from playwright.sync_api import APIResponse

# Import TYPE_CHECKING to avoid circular imports at runtime
# This is a best practice for type hints with forward references
from typing import TYPE_CHECKING

# Use forward reference to import our Page class
# The TYPE_CHECKING block is only evaluated by type checkers, not at runtime
# This prevents circular import issues when the framework loads the module
if TYPE_CHECKING:
    # Import our JsonPlaceholderPage class using absolute import
    # The '..' goes up from modules/ to jsonplaceholder/ directory
    from ..jsonplaceholder_page import JsonPlaceholderPage


def run(page: "JsonPlaceholderPage") -> APIResponse:
    """Execute test: Fetch post #1 and validate response.

    This is the main test function that the framework will call.
    Every test module MUST define a run() function with this signature.

    Args:
        page: An instance of JsonPlaceholderPage initialized with base_url.
              The framework automatically creates and injects this object
              based on the service configuration in e2e.conf.

    Returns:
        APIResponse: The HTTP response object from the API call.
                    The framework uses this to track test results.

    Raises:
        AssertionError: If any validation fails (status code, response data).
                       The framework catches these and marks the test as failed.

    EXAMPLE USAGE:
    -------------
    From command line:
        $ e2e run --service jsonplaceholder

    The framework will:
        1. Read e2e.conf to find the jsonplaceholder service
        2. Create a JsonPlaceholderPage instance with the configured base_url
        3. Call this run() function with the page instance
        4. Track the result (pass/fail) based on assertions
    """

    # ========================================================================
    # STEP 1: Make the API call
    # ========================================================================

    # Print a message so we can see progress in the console output
    # This is optional but helpful for debugging
    print("Testing: Fetch post #1 from JSONPlaceholder API")

    # Call the get_post() method we defined in jsonplaceholder_page.py
    # This performs: GET https://jsonplaceholder.typicode.com/posts/1
    # The 'page' object was automatically injected by the framework
    response = page.get_post(1)

    # ========================================================================
    # STEP 2: Validate HTTP Status Code
    # ========================================================================

    # The most basic assertion: check that the request succeeded
    # HTTP 200 means "OK" - the request was successful
    #
    # We use response.ok which is a boolean property
    # It's True if status code is between 200-299
    assert response.ok, (
        f"Expected HTTP 200 OK, but got {response.status}. "
        f"Response body: {response.text()}"
    )

    # Alternative: You could also assert on the status code directly
    # assert response.status == 200, f"Expected 200, got {response.status}"

    # Print success message for the status code check
    print(f"✓ Status code is {response.status} (OK)")

    # ========================================================================
    # STEP 3: Validate Response Body
    # ========================================================================

    # Parse the JSON response body into a Python dictionary
    # This is a common pattern for REST APIs that return JSON
    data = response.json()

    # JSONPlaceholder returns a post object with this structure:
    # {
    #     "userId": 1,
    #     "id": 1,
    #     "title": "sunt aut facere repellat provident...",
    #     "body": "quia et suscipit\nsuscipit recusandae..."
    # }

    # Validate that the response contains the expected fields
    # These are our data quality assertions

    # Check that 'id' field exists in the response
    assert "id" in data, f"Response missing 'id' field. Got keys: {list(data.keys())}"

    # Check that the ID matches what we requested (post #1)
    assert data["id"] == 1, f"Expected post ID 1, but got {data.get('id')}"

    # Check that 'title' field exists
    assert "title" in data, (
        f"Response missing 'title' field. Got keys: {list(data.keys())}"
    )

    # Check that title is a non-empty string
    assert isinstance(data["title"], str), (
        f"Expected title to be a string, got {type(data['title'])}"
    )
    assert len(data["title"]) > 0, "Title should not be empty"

    # Check that 'userId' field exists
    assert "userId" in data, (
        f"Response missing 'userId' field. Got keys: {list(data.keys())}"
    )

    # Print success messages for data validation
    print(f"✓ Response contains 'id' field with value: {data['id']}")
    print(f"✓ Response contains 'title' field with value: '{data['title'][:50]}...'")
    print(f"✓ Response contains 'userId' field with value: {data['userId']}")

    # ========================================================================
    # STEP 4: Return the response
    # ========================================================================

    # Return the response object to the framework
    # This allows the framework to:
    #   - Track that the test completed
    #   - Record timing information
    #   - Generate reports
    #   - Handle any cleanup

    print("✓ Test completed successfully!")
    print(f"  Post title: {data['title'][:60]}...")

    return response


# ========================================================================
# ADDITIONAL NOTES FOR HUMAN TEST WRITERS:
# ========================================================================
#
# 1. TEST NAMING:
#    - File names should be descriptive: 01_get_post.py
#    - Use numeric prefixes (01_, 02_, etc.) to control execution order
#    - Tests run alphabetically, so 01 runs before 02
#
# 2. ERROR HANDLING:
#    - Use try/except if you need custom error handling
#    - Otherwise, let assertions raise - the framework catches them
#
# 3. STATE SHARING:
#    - You can store data on the page object for use in subsequent tests
#    - Example: page.post_id = data["id"]
#
# 4. MULTIPLE ASSERTIONS:
#    - Group related assertions together
#    - Provide clear error messages for each assertion
#
# 5. EXTERNAL APIs:
#    - This test uses a real external API (JSONPlaceholder)
#    - For production, you might want to use mocks or local test servers
#    - Consider rate limiting and API availability
#
# 6. DETERMINISM:
#    - This test is 100% deterministic - it always fetches post #1
#    - The JSONPlaceholder API always returns the same data for post #1
#    - This makes the test reliable and repeatable
#
# ========================================================================
