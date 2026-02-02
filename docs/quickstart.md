# Quick Start Guide

Get started with socialseed-e2e in 15 minutes! This guide will walk you through creating your first API testing project from scratch.

**⏱️ Time Required:** 15 minutes
**📋 Prerequisites:** socialseed-e2e installed (see [Installation Guide](installation.md))

## Table of Contents

- [Overview](#overview)
- [What You'll Build](#what-youll-build)
- [Step 1: Project Initialization](#step-1-project-initialization)
- [Step 2: Understanding the Project Structure](#step-2-understanding-the-project-structure)
- [Step 3: Configure Your API](#step-3-configure-your-api)
- [Step 4: Create Your First Service](#step-4-create-your-first-service)
- [Step 5: Create Your First Test](#step-5-create-your-first-test)
- [Step 6: Run Your Tests](#step-6-run-your-tests)
- [Step 7: Add More Tests](#step-7-add-more-tests)
- [Next Steps](#next-steps)
- [Troubleshooting](#troubleshooting)

## Overview

In this quick start guide, you'll:

1. ✅ Initialize a new testing project
2. ✅ Configure API endpoints
3. ✅ Create a service test suite
4. ✅ Write your first API test
5. ✅ Run tests and see results
6. ✅ Chain multiple tests together

## What You'll Build

You'll create a simple test suite for a Users API with these endpoints:
- `POST /auth/login` - User authentication
- `GET /users/me` - Get current user profile

**Final Result:** A working test suite that logs in a user and retrieves their profile.

---

## Step 1: Project Initialization

Let's create your first testing project!

### Command

```bash
# Create a new directory for your project
mkdir my-api-tests
cd my-api-tests

# Initialize the project
e2e init
```

### What Happens

```
🚀 Initializing socialseed-e2e project...

📁 Creating directory structure...
   ✓ services/
   ✓ tests/
   ✓ .github/workflows/

📄 Creating configuration files...
   ✓ e2e.conf
   ✓ .gitignore
   ✓ README.md

🎉 Project initialized successfully!

Next steps:
   1. Edit e2e.conf to configure your API
   2. Run 'e2e new-service <name>' to create a service
   3. Run 'e2e new-test <name> --service <service>' to create tests
   4. Run 'e2e run' to execute your tests
```

### Files Created

```
my-api-tests/
├── e2e.conf              # Main configuration file
├── .gitignore            # Git ignore rules
├── README.md             # Project readme
├── services/             # Your service test implementations
│   └── __init__.py
└── .github/
    └── workflows/        # CI/CD templates
        └── e2e-tests.yml
```

**⏱️ Time elapsed:** ~30 seconds

---

## Step 2: Understanding the Project Structure

Before continuing, let's understand what each component does:

### Configuration File (`e2e.conf`)

This is the heart of your testing project. It defines:
- General settings (environment, timeouts)
- Service endpoints to test
- Test execution parameters

### Services Directory (`services/`)

Each subdirectory here represents an API service you want to test:
```
services/
├── users-api/           # Tests for Users API
│   ├── __init__.py
│   ├── users_api_page.py    # Service page class
│   ├── data_schema.py       # DTOs and constants
│   └── modules/             # Test modules
│       ├── 01_login.py
│       └── 02_get_profile.py
└── __init__.py
```

### The Service Page Pattern

- **Service Page**: Python class that extends `BasePage`
- **Encapsulates**: HTTP methods, authentication, base URL
- **Benefit**: Reusable across all tests for that service

---

## Step 3: Configure Your API

Now let's configure your API endpoints in `e2e.conf`.

### Open e2e.conf

```bash
# Using your favorite editor
code e2e.conf    # VS Code
# or
vim e2e.conf     # Vim
# or
nano e2e.conf    # Nano
```

### Edit the Configuration

Replace the default configuration with this:

```yaml
general:
  environment: dev
  timeout: 30000
  verbose: true

services:
  users-api:
    name: users-api
    base_url: http://localhost:8080
    health_endpoint: /health
    timeout: 5000
    required: true

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Configuration Explained

| Setting | Description | Value |
|---------|-------------|-------|
| `environment` | Current environment | `dev` |
| `timeout` | Default request timeout (ms) | `30000` (30s) |
| `verbose` | Show detailed output | `true` |
| `base_url` | API base URL | `http://localhost:8080` |
| `health_endpoint` | Health check endpoint | `/health` |
| `required` | Fail if service is unavailable | `true` |

### Verify Configuration

```bash
e2e config
```

**Expected Output:**
```
📋 Configuration Summary
═══════════════════════════════════════════════════

Environment: dev
Timeout: 30000ms
Verbose: true

Services:
───────────────────────────────────────────────────
users-api (required)
  Base URL: http://localhost:8080
  Health: /health
  Timeout: 5000ms

✓ Configuration is valid
```

**⏱️ Time elapsed:** ~2 minutes

---

## Step 4: Create Your First Service

A "service" in socialseed-e2e represents an API you want to test.

### Command

```bash
e2e new-service users-api
```

### What Happens

```
🆕 Creating new service: users-api

📁 Creating directory structure...
   ✓ services/users-api/
   ✓ services/users-api/modules/

📄 Creating service files...
   ✓ services/users-api/__init__.py
   ✓ services/users-api/users_api_page.py
   ✓ services/users-api/data_schema.py
   ✓ services/users-api/modules/__init__.py

🎨 Generating from templates...
   ✓ Service page class
   ✓ Data schema definitions
   ✓ Module structure

✅ Service 'users-api' created successfully!

Next steps:
   1. Review and customize users_api_page.py
   2. Add constants to data_schema.py
   3. Run 'e2e new-test <name> --service users-api' to create tests
```

### Files Created

```
services/users-api/
├── __init__.py              # Makes it a Python package
├── users_api_page.py        # Service page class (main file)
├── data_schema.py           # Constants and DTOs
└── modules/                 # Test modules go here
    └── __init__.py
```

### Review the Service Page

Open `services/users-api/users_api_page.py`:

```python
"""Users API Service Page.

This module provides a service page for testing the Users API.
"""

from typing import TYPE_CHECKING

from socialseed_e2e import BasePage

if TYPE_CHECKING:
    from playwright.sync_api import APIResponse


class UsersApiPage(BasePage):
    """Service page for Users API testing.

    This class provides methods for interacting with the Users API,
    including authentication, user management, and profile operations.

    Usage:
        page = UsersApiPage(config)
        response = page.post("/auth/login", json=credentials)
    """

    def __init__(self, config: dict):
        """Initialize the Users API page.

        Args:
            config: Service configuration from e2e.conf
        """
        super().__init__(config)
        self.auth_token: str = None
        self.current_user: dict = None
```

**Key Points:**
- Extends `BasePage` (provides HTTP methods, retry logic, etc.)
- Has access to service configuration from `e2e.conf`
- Can store state (like `auth_token`) between tests

**⏱️ Time elapsed:** ~4 minutes

---

## Step 5: Create Your First Test

Now let's create a test that checks if the API is healthy.

### Command

```bash
e2e new-test health_check --service users-api
```

### What Happens

```
🆕 Creating new test: health_check

📄 Generating test module...
   ✓ services/users-api/modules/01_health_check.py

🎨 Applying template...
   ✓ Test structure
   ✓ Docstrings
   ✓ Type hints

✅ Test 'health_check' created successfully!

The test has been added to the execution queue.
Run 'e2e run --service users-api' to execute it.
```

### File Created

`services/users-api/modules/01_health_check.py`:

```python
"""Health Check Test for Users API.

This test verifies that the Users API is running and accessible.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import APIResponse
    from ..users_api_page import UsersApiPage


def run(users_api: 'UsersApiPage') -> 'APIResponse':
    """Test that the Users API health endpoint returns 200.

    This test checks if the API is running and responding correctly.

    Args:
        users_api: Instance of UsersApiPage with service configuration

    Returns:
        APIResponse: The HTTP response from the health endpoint
    """
    print("🔍 Checking API health...")

    # Make the HTTP request
    response = users_api.get("/health")

    # Assert the response is successful
    if response.status == 200:
        print("✅ API is healthy!")
    else:
        print(f"❌ API health check failed: {response.status}")
        raise AssertionError(f"Expected 200, got {response.status}")

    return response
```

### Understanding the Test Structure

```python
def run(users_api: 'UsersApiPage') -> 'APIResponse':
```

- **Function name**: Must be `run`
- **Parameter**: Service page instance (injected by framework)
- **Return type**: `APIResponse` from Playwright
- **State**: Can store data in `users_api` for next test

### Customize the Test

Let's make it more interesting. Edit the file:

```python
"""Health Check Test for Users API.

This test verifies that the Users API is running and accessible.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import APIResponse
    from ..users_api_page import UsersApiPage


def run(users_api: 'UsersApiPage') -> 'APIResponse':
    """Test that the Users API health endpoint returns 200.

    Args:
        users_api: Instance of UsersApiPage

    Returns:
        APIResponse: The HTTP response
    """
    print("🏥 Checking Users API health...")

    # Test the health endpoint
    response = users_api.get("/health")

    # Verify response
    if response.status == 200:
        data = response.json()
        print(f"✅ API Status: {data.get('status', 'OK')}")
        print(f"✅ Service: {data.get('service', 'unknown')}")
        print(f"✅ Version: {data.get('version', 'unknown')}")
    else:
        print(f"❌ Health check failed with status: {response.status}")
        print(f"Response: {response.text()}")
        raise AssertionError(f"Health check failed: {response.status}")

    return response
```

**⏱️ Time elapsed:** ~8 minutes

---

## Step 6: Run Your Tests

Time to see your test in action!

### Command

```bash
e2e run
```

### Expected Output (Success)

```
🚀 socialseed-e2e v0.1.0
═══════════════════════════════════════════════════

📋 Configuration: e2e.conf
🌍 Environment: dev
⏱️  Timeout: 30000ms

🔍 Discovering services...
   ✓ Found 1 service: users-api

📦 Service: users-api
───────────────────────────────────────────────────
🔗 Base URL: http://localhost:8080
🏥 Health Check: /health

🧪 Running 1 test module(s)

[1/1] 01_health_check.py
🏥 Checking Users API health...
✅ API Status: healthy
✅ Service: users-api
✅ Version: 1.0.0
✅ PASSED (0.42s)

───────────────────────────────────────────────────
✅ All tests passed! (1/1)
⏱️  Total Duration: 0.45s

═══════════════════════════════════════════════════
🎉 Test run completed successfully!
```

### Expected Output (API Not Running)

```
🚀 socialseed-e2e v0.1.0
═══════════════════════════════════════════════════

📋 Configuration: e2e.conf
🌍 Environment: dev

🔍 Discovering services...
   ✓ Found 1 service: users-api

📦 Service: users-api
───────────────────────────────────────────────────
⚠️  Service health check failed
   URL: http://localhost:8080/health
   Error: Connection refused

❌ Required service 'users-api' is not available
   Set 'required: false' in e2e.conf to skip this check

═══════════════════════════════════════════════════
💥 Test run failed: Service unavailable
```

### Using the Mock API

If you don't have a real API running, use the built-in Mock API:

**Terminal 1:**
```bash
python tests/fixtures/mock_api.py
```

**Terminal 2:**
```bash
cd my-api-tests
e2e run
```

Update `e2e.conf` to use mock API:
```yaml
services:
  users-api:
    name: users-api
    base_url: http://localhost:8765  # Mock API port
    health_endpoint: /health
    timeout: 5000
    required: true
```

**⏱️ Time elapsed:** ~10 minutes

---

## Step 7: Add More Tests

Let's create a more complex test that chains with the first one.

### Create Login Test

```bash
e2e new-test login --service users-api
```

This creates `services/users-api/modules/02_login.py`:

Edit it to:

```python
"""Login Test for Users API.

This test authenticates a user and stores the token for subsequent tests.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import APIResponse
    from ..users_api_page import UsersApiPage


def run(users_api: 'UsersApiPage') -> 'APIResponse':
    """Test user login and store authentication token.

    This test:
    1. Sends login credentials to /auth/login
    2. Extracts the auth token from response
    3. Stores token in users_api for other tests to use

    Args:
        users_api: Instance of UsersApiPage

    Returns:
        APIResponse: The login response
    """
    print("🔐 Attempting user login...")

    # Prepare credentials
    credentials = {
        "email": "test@example.com",
        "password": "secret123"
    }

    # Make login request
    response = users_api.post("/auth/login", json=credentials)

    # Verify and extract token
    if response.status == 200:
        data = response.json()
        users_api.auth_token = data["token"]
        users_api.current_user = data["user"]

        print(f"✅ Login successful!")
        print(f"   Token: {users_api.auth_token[:20]}...")
        print(f"   User: {users_api.current_user['email']}")
    else:
        print(f"❌ Login failed: {response.status}")
        print(f"   Response: {response.text()}")
        raise AssertionError(f"Login failed: {response.status}")

    return response
```

### Create Profile Test

```bash
e2e new-test get_profile --service users-api
```

Edit `services/users-api/modules/03_get_profile.py`:

```python
"""Get Profile Test for Users API.

This test retrieves the current user's profile using the auth token
from the previous login test.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import APIResponse
    from ..users_api_page import UsersApiPage


def run(users_api: 'UsersApiPage') -> 'APIResponse':
    """Test retrieving user profile with authentication.

    This test uses the auth_token stored by the login test to
    make an authenticated request to /users/me.

    Args:
        users_api: Instance of UsersApiPage (with auth_token from login)

    Returns:
        APIResponse: The profile response
    """
    print("👤 Retrieving user profile...")

    # Check if we have auth token from previous test
    if not users_api.auth_token:
        raise AssertionError("No auth token found. Run login test first.")

    # Set authorization header
    headers = {
        "Authorization": f"Bearer {users_api.auth_token}"
    }

    # Make authenticated request
    response = users_api.get("/users/me", headers=headers)

    # Verify response
    if response.status == 200:
        profile = response.json()
        print(f"✅ Profile retrieved!")
        print(f"   Name: {profile.get('name', 'N/A')}")
        print(f"   Email: {profile.get('email', 'N/A')}")
        print(f"   Role: {profile.get('role', 'N/A')}")
    else:
        print(f"❌ Failed to get profile: {response.status}")
        raise AssertionError(f"Profile retrieval failed: {response.status}")

    return response
```

### Run All Tests

```bash
e2e run --service users-api
```

**Expected Output:**
```
🚀 socialseed-e2e v0.1.0
═══════════════════════════════════════════════════

📦 Service: users-api
───────────────────────────────────────────────────
🧪 Running 3 test module(s)

[1/3] 01_health_check.py
🏥 Checking Users API health...
✅ API Status: healthy
✅ PASSED (0.42s)

[2/3] 02_login.py
🔐 Attempting user login...
✅ Login successful!
   Token: eyJhbGciOiJIUzI1Ni...
   User: test@example.com
✅ PASSED (0.38s)

[3/3] 03_get_profile.py
👤 Retrieving user profile...
✅ Profile retrieved!
   Name: Test User
   Email: test@example.com
   Role: user
✅ PASSED (0.35s)

───────────────────────────────────────────────────
✅ All tests passed! (3/3)
⏱️  Total Duration: 1.15s
```

**Key Concept:** Tests run in alphabetical order (01_, 02_, 03_) and share state through the `users_api` object!

**⏱️ Time elapsed:** ~15 minutes ✅

---

## Next Steps

Congratulations! You've successfully:
- ✅ Created a testing project
- ✅ Configured an API service
- ✅ Written 3 different tests
- ✅ Ran tests and saw results
- ✅ Learned about test chaining

### Continue Learning

1. **[Writing Tests](writing-tests.md)** - Learn advanced test patterns
2. **[Configuration](configuration.md)** - Deep dive into e2e.conf options
3. **[CLI Reference](cli-reference.md)** - All available commands
4. **[Mock API](mock-api.md)** - Test without a real API

### Practice Exercises

Try these challenges to reinforce your learning:

**Exercise 1: Add Error Handling Test**
Create a test that checks what happens with invalid credentials.

**Exercise 2: Add Data Validation Test**
Create a test that verifies the response JSON structure.

**Exercise 3: Test Multiple Services**
Add another service to your e2e.conf and create tests for it.

### Example Solutions

<details>
<summary>Click to see Exercise 1 solution</summary>

```bash
e2e new-test login_error --service users-api
```

```python
def run(users_api: 'UsersApiPage') -> 'APIResponse':
    """Test login with invalid credentials."""
    print("🔐 Testing login with invalid credentials...")

    credentials = {
        "email": "invalid@example.com",
        "password": "wrongpassword"
    }

    response = users_api.post("/auth/login", json=credentials)

    if response.status == 401:
        print("✅ Correctly rejected invalid credentials")
    else:
        raise AssertionError(f"Expected 401, got {response.status}")

    return response
```
</details>

---

## Troubleshooting

### "e2e command not found"

**Problem:** After installation, the `e2e` command is not recognized.

**Solution:**
```bash
# Make sure you're in a virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Or use the full path
/path/to/venv/bin/e2e
```

### "Connection refused" Error

**Problem:** Tests fail with "Connection refused" to localhost:8080.

**Solution:**
1. Check if your API is running on port 8080
2. Update `e2e.conf` with the correct base_url
3. Or use the Mock API: `python tests/fixtures/mock_api.py`

### Tests Not Found

**Problem:** `e2e run` says "No tests found".

**Solution:**
```bash
# Check test file naming (must start with numbers: 01_, 02_, etc.)
ls services/users-api/modules/

# Check for syntax errors in test files
python -m py_compile services/users-api/modules/*.py
```

### Import Errors

**Problem:** `ModuleNotFoundError` when running tests.

**Solution:**
```bash
# Reinstall in editable mode
pip install -e ".[dev]"

# Check that you're in the right directory
pwd  # Should be in project root or my-api-tests/
```

---

## Summary

**What You Learned:**

1. **Project Structure**: `e2e.conf` + `services/` + `tests/`
2. **Service Pages**: Classes that extend `BasePage`
3. **Test Modules**: Files in `services/<name>/modules/`
4. **Test Chaining**: Tests share state through service page
5. **Running Tests**: `e2e run` with beautiful output

**Commands Reference:**

```bash
e2e init                    # Initialize project
e2e new-service <name>      # Create service
e2e new-test <name> --service <svc>  # Create test
e2e run                     # Run all tests
e2e run --service <name>    # Run specific service
e2e config                  # Show configuration
e2e doctor                  # Verify installation
```

---

<p align="center">
  <b>🎉 You're now ready to test APIs like a pro!</b>
</p>

<p align="center">
  Next: <a href="writing-tests.md">Writing Tests</a> →
  <a href="configuration.md">Configuration</a> →
  <a href="cli-reference.md">CLI Reference</a>
</p>
