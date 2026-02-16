# How SocialSeed E2E Works

Understanding the core concepts and architecture of the SocialSeed E2E framework.

## Overview

SocialSeed E2E is a testing framework built around a **Service-Oriented Testing Model**. Instead of thinking in terms of individual test files, you organize tests around **Services** (the APIs you want to test), define **Endpoints** (the operations you can perform), and write **Scenarios** that exercise those endpoints with specific **Tests** and **Assertions**.

## Core Concepts

### 1. Service

A **Service** represents an API you want to test. Think of it as a logical grouping of related API functionality.

**Example Services:**
- `auth-service` - Authentication and authorization
- `users-api` - User management operations
- `payment-service` - Payment processing

**In Code:**
```python
# services/auth_service/auth_service_page.py
class AuthServicePage(BasePage):
    """Page object for auth-service API."""
    
    def do_login(self, email: str, password: str):
        return self.post("/auth/login", json={"email": email, "password": password})
```

**Configuration:**
```yaml
# e2e.conf
services:
  auth_service:
    base_url: http://localhost:8080
    health_endpoint: /health
```

**Key Points:**
- Each service has its own directory under `services/`
- Contains a `{service_name}_page.py` file with API methods
- Configured in `e2e.conf` with base URL and settings
- Tests are organized by service

---

### 2. Endpoint

An **Endpoint** is a specific API operation (HTTP method + path) within a Service. It's the building block of your API.

**Example Endpoints:**
- `POST /auth/login` - Authenticate a user
- `GET /users/{id}` - Retrieve user by ID
- `DELETE /posts/{id}` - Delete a post

**In Code:**
```python
# In your Page class
class UsersPage(BasePage):
    def get_user(self, user_id: int):
        """GET /users/{id}"""
        return self.get(f"/users/{user_id}")
    
    def create_user(self, name: str, email: str):
        """POST /users"""
        return self.post("/users", json={"name": name, "email": email})
```

**Key Points:**
- Endpoints are methods in your Page class
- They encapsulate the HTTP details (method, path, headers)
- Return `APIResponse` objects from Playwright
- Abstract away the API implementation from tests

---

### 3. Scenario

A **Scenario** is a sequence of API calls that represent a realistic user journey or business flow. It chains multiple endpoints together to test a complete workflow.

**Example Scenarios:**
- **User Registration Flow**: Create user → Login → Get profile
- **E-commerce Checkout**: Add to cart → Checkout → Payment → Order confirmation
- **Content Creation**: Login → Create post → Verify post exists

**In Code:**
```python
# services/users/modules/01_register_and_login.py
def run(users: 'UsersPage') -> APIResponse:
    """Scenario: Register new user and immediately log in."""
    
    # Step 1: Register new user
    response = users.create_user(
        name="John Doe",
        email="john@example.com"
    )
    assert response.status == 201
    user_id = response.json()["id"]
    
    # Step 2: Log in with new credentials
    login_response = users.login(
        email="john@example.com",
        password="secret123"
    )
    assert login_response.status == 200
    
    # Step 3: Verify user can access profile
    profile = users.get_user(user_id)
    assert profile.json()["name"] == "John Doe"
    
    return profile
```

**Key Points:**
- Scenarios are test modules (files in `modules/`)
- Each scenario defines a `run()` function
- They orchestrate multiple endpoint calls
- Can share state between steps
- Represent realistic API usage patterns

---

### 4. Test

A **Test** is a specific validation point within a Scenario. It's where you assert that the API behaves as expected.

**Types of Tests:**
- **Status Code Assertions**: Verify HTTP status (200, 201, 404, etc.)
- **Response Body Assertions**: Validate JSON structure and values
- **Header Assertions**: Check response headers
- **State Assertions**: Verify side effects (database changes, etc.)

**In Code:**
```python
# Status code assertion
assert response.status == 200, f"Expected 200, got {response.status}"

# Response body assertion
data = response.json()
assert "id" in data, "Response missing 'id' field"
assert data["id"] == 1, f"Expected id=1, got {data['id']}"

# Header assertion
assert response.headers["content-type"] == "application/json"

# Business logic assertion
assert data["status"] == "active", "User should be active after registration"
```

**Key Points:**
- Tests are Python `assert` statements
- Can check any aspect of the response
- Provide clear error messages
- Fail immediately on first assertion failure
- Framework catches failures and reports them

---

## How Assertions Are Evaluated

The assertion evaluation flow:

```
1. Execute API Call
   ↓
2. Get APIResponse Object
   ↓
3. Run Assertion (assert statement)
   ↓
   ├─ PASS → Continue to next assertion
   ↓
   └─ FAIL → Raise AssertionError
             ↓
4. Framework Catches AssertionError
   ↓
5. Marks Test as Failed
   ↓
6. Reports Failure with Details
```

**Example Flow:**
```python
def run(page: 'UsersPage') -> APIResponse:
    # 1. Execute API Call
    response = page.get_user(1)
    
    # 2. Get APIResponse (status=200, json={"id": 1, "name": "Alice"})
    
    # 3. Run Assertions
    assert response.status == 200  # PASS ✓
    
    data = response.json()
    assert "name" in data          # PASS ✓
    assert data["name"] == "Bob"   # FAIL ✗ (expected "Bob", got "Alice")
    
    # 4. AssertionError raised
    # 5. Framework catches it
    # 6. Test marked as FAILED
    #    Report: "Expected 'Bob', got 'Alice'"
```

---

## Conceptual Architecture Diagram

Here's how the pieces fit together:

```
┌─────────────────────────────────────────────────────────────┐
│                      Test Execution                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Configuration (e2e.conf)                                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Service: auth_service                                    ││
│  │   base_url: http://localhost:8080                       ││
│  │   health_endpoint: /health                              ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Service Layer                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Page Class (auth_service_page.py)                        ││
│  │   ┌─────────────────────────────────────────────────┐   ││
│  │   │ Endpoints                                        │   ││
│  │   │   • do_login()    → POST /auth/login           │   ││
│  │   │   • do_logout()   → POST /auth/logout          │   ││
│  │   │   • get_profile() → GET  /auth/profile         │   ││
│  │   └─────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Test Modules (modules/*.py)                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Scenario: 01_login_flow.py                               ││
│  │   ┌─────────────────────────────────────────────────┐   ││
│  │   │ Steps                                           │   ││
│  │   │   1. Call do_login()                           │   ││
│  │   │        ↓                                       │   ││
│  │   │   2. Assert status == 200                      │   ││
│  │   │        ↓                                       │   ││
│  │   │   3. Assert response has token                 │   ││
│  │   │        ↓                                       │   ││
│  │   │   4. Return response                           │   ││
│  │   └─────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Framework Execution                                         │
│  • Loads configuration                                      │
│  • Creates Page instances                                   │
│  • Discovers test modules                                   │
│  • Runs scenarios in order                                  │
│  • Captures assertions                                      │
│  • Generates reports                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Where AI Agents Fit

AI agents are **optional helpers** that accelerate test creation but are **not required** for framework operation.

### Without AI (Manual)

```
Developer → Writes Page Class → Writes Test Modules → Runs e2e run
```

**Pros:**
- Full control over code
- Deterministic, predictable
- No dependencies on AI services
- Works offline

**Cons:**
- Takes more time
- Requires understanding of framework
- Manual boilerplate writing

### With AI (Assisted)

```
Developer → Describes API → AI Generates → Developer Reviews → Runs e2e run
                                  ↑
                                  └── Uses AI Manifest (project_knowledge.json)
                                      └── Scans codebase automatically
```

**Pros:**
- Faster test creation
- Auto-generates boilerplate
- Understands API from code
- Suggests edge cases

**Cons:**
- Requires AI service
- May need manual review/tweaks
- Less predictable output

### AI Integration Points

1. **Manifest Generation** (`e2e manifest`)
   - Scans your API codebase
   - Extracts endpoints, DTOs, types
   - Creates `project_knowledge.json`

2. **Test Generation** (`e2e generate-tests`)
   - Reads manifest
   - Generates test modules
   - Creates Page classes

3. **Semantic Search** (`e2e search`)
   - Vector embeddings of your API
   - Natural language queries
   - Context-aware suggestions

4. **Execution Time**
   - **No AI involved during test execution**
   - Tests run deterministically
   - Pure Python code execution

**Bottom Line:**
- **Development:** AI can help write tests faster
- **Execution:** AI is never involved - tests run as pure Python
- **Your Choice:** Use AI or don't - both work perfectly

---

## Execution Flow Summary

When you run `e2e run`, here's what happens:

```
1. Load Configuration
   └─ Read e2e.conf → Build ServiceConfig objects

2. Discover Services
   └─ Scan services/ directory → Find all service folders

3. Initialize Pages
   └─ Create Page instances with configured base_url

4. Discover Tests
   └─ Scan modules/ directories → Find all test files

5. Execute Tests (in order)
   For each test module:
   a. Load module
   b. Call run(page) with Page instance
   c. Capture return value (APIResponse)
   d. Track any AssertionErrors
   e. Record execution time

6. Generate Reports
   └─ Summary of pass/fail
   └─ Timing information
   └─ Traceability (optional)

7. Exit
   └─ Return code 0 if all passed
   └─ Return code 1 if any failed
```

---

## Key Takeaways

1. **Service** = API you want to test (configured in e2e.conf)
2. **Endpoint** = Individual API operation (methods in Page class)
3. **Scenario** = Complete user journey (test module)
4. **Test** = Validation point (assert statement)
5. **AI is Optional** = Helps write tests, but never runs them
6. **Pure Python** = Tests are standard Python code with assertions

## Next Steps

- [Quick Start Guide](../quickstart.md) - Get up and running in 5 minutes
- [Writing Tests](../writing-tests.md) - Learn to write test modules
- [Configuration](../configuration.md) - Configure your services
- [AI Manifest](../project-manifest.md) - Use AI to accelerate development

## See Also

- [Architecture Deep Dive](../architecture.md) - Detailed framework internals
- [Best Practices](../best-practices.md) - Tips for effective testing
- [Examples](../tutorials/examples/) - More working examples
