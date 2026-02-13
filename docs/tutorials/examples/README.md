# Live Examples

Runnable code examples demonstrating SocialSeed-E2E features.

## 🎯 Quick Start Examples

### Example 1: Hello World Test

```python
"""
Hello World Example - Your first E2E test with SocialSeed-E2E
"""

from socialseed_e2e.core.base_page import BasePage

# Create a simple test page
class HelloWorldPage(BasePage):
    def __init__(self):
        super().__init__(base_url="https://httpbin.org")
    
    async def test_get_request(self):
        """Test a simple GET request"""
        response = await self.get("/get")
        return response.status == 200
    
    async def test_post_request(self):
        """Test a POST request with data"""
        data = {"message": "Hello, World!"}
        response = await self.post("/post", json=data)
        return response.status == 200

# Run the test
async def main():
    page = HelloWorldPage()
    
    print("🚀 Running Hello World tests...")
    
    # Test GET
    get_result = await page.test_get_request()
    print(f"GET Test: {'✅ PASS' if get_result else '❌ FAIL'}")
    
    # Test POST
    post_result = await page.test_post_request()
    print(f"POST Test: {'✅ PASS' if post_result else '❌ FAIL'}")
    
    await page.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

[📋 Copy Code](#) [▶️ Run in Playground](./playground)

---

### Example 2: API Authentication Flow

```python
"""
Authentication Flow Example - Testing login/logout
"""

from socialseed_e2e.core.base_page import BasePage

class AuthPage(BasePage):
    def __init__(self, base_url):
        super().__init__(base_url=base_url)
        self.token = None
    
    async def login(self, username, password):
        """Authenticate and store token"""
        response = await self.post(
            "/auth/login",
            json={"username": username, "password": password}
        )
        
        if response.status == 200:
            data = await response.json()
            self.token = data.get("token")
            return True
        return False
    
    async def access_protected_resource(self):
        """Access a resource requiring authentication"""
        if not self.token:
            raise Exception("Not authenticated")
        
        response = await self.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.status == 200
    
    async def logout(self):
        """Logout and invalidate token"""
        response = await self.post("/auth/logout")
        self.token = None
        return response.status == 200

# Complete authentication flow test
async def test_auth_flow():
    page = AuthPage("https://api.example.com")
    
    print("🔐 Testing Authentication Flow\n")
    
    # Step 1: Login
    print("Step 1: Login...")
    login_success = await page.login("user@example.com", "password123")
    print(f"  {'✅' if login_success else '❌'} Login")
    
    # Step 2: Access protected resource
    print("Step 2: Access protected resource...")
    try:
        access_success = await page.access_protected_resource()
        print(f"  {'✅' if access_success else '❌'} Access granted")
    except Exception as e:
        print(f"  ❌ Access denied: {e}")
    
    # Step 3: Logout
    print("Step 3: Logout...")
    logout_success = await page.logout()
    print(f"  {'✅' if logout_success else '❌'} Logout")
    
    await page.close()
    print("\n✨ Auth flow test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_auth_flow())
```

[📋 Copy Code](#) [▶️ Run in Playground](./playground)

---

### Example 3: CRUD Operations

```python
"""
CRUD Operations Example - Create, Read, Update, Delete
"""

from socialseed_e2e.core.base_page import BasePage

class CRUDPage(BasePage):
    def __init__(self, base_url):
        super().__init__(base_url=base_url)
        self.created_ids = []
    
    async def create_user(self, user_data):
        """Create a new user"""
        response = await self.post("/users", json=user_data)
        
        if response.status == 201:
            data = await response.json()
            user_id = data.get("id")
            self.created_ids.append(user_id)
            return user_id
        return None
    
    async def get_user(self, user_id):
        """Read user by ID"""
        response = await self.get(f"/users/{user_id}")
        
        if response.status == 200:
            return await response.json()
        return None
    
    async def update_user(self, user_id, updates):
        """Update user data"""
        response = await self.patch(f"/users/{user_id}", json=updates)
        return response.status == 200
    
    async def delete_user(self, user_id):
        """Delete user"""
        response = await self.delete(f"/users/{user_id}")
        
        if response.status == 204:
            if user_id in self.created_ids:
                self.created_ids.remove(user_id)
            return True
        return False
    
    async def cleanup(self):
        """Clean up all created users"""
        for user_id in self.created_ids[:]:
            await self.delete_user(user_id)

# Test CRUD operations
async def test_crud():
    page = CRUDPage("https://api.example.com")
    
    print("📝 Testing CRUD Operations\n")
    
    # CREATE
    print("1. CREATE user...")
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user"
    }
    user_id = await page.create_user(user_data)
    print(f"   ✅ Created user with ID: {user_id}")
    
    # READ
    print("2. READ user...")
    user = await page.get_user(user_id)
    print(f"   ✅ Retrieved: {user.get('name')}")
    
    # UPDATE
    print("3. UPDATE user...")
    updates = {"role": "admin"}
    update_success = await page.update_user(user_id, updates)
    print(f"   {'✅' if update_success else '❌'} Updated role to admin")
    
    # Verify update
    updated_user = await page.get_user(user_id)
    print(f"   Current role: {updated_user.get('role')}")
    
    # DELETE
    print("4. DELETE user...")
    delete_success = await page.delete_user(user_id)
    print(f"   {'✅' if delete_success else '❌'} Deleted user")
    
    # Verify deletion
    deleted_user = await page.get_user(user_id)
    print(f"   {'✅' if deleted_user is None else '❌'} User no longer exists")
    
    await page.close()
    print("\n✨ CRUD test complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_crud())
```

[📋 Copy Code](#) [▶️ Run in Playground](./playground)

---

## 🤖 AI-Powered Examples

### Example 4: Generate Tests with AI

```python
"""
AI Test Generation Example - Let AI understand your API
"""

from pathlib import Path
from socialseed_e2e.project_manifest import (
    ManifestGenerator,
    BusinessLogicInferenceEngine,
    FlowBasedTestSuiteGenerator
)

async def generate_tests_with_ai():
    print("🤖 AI-Powered Test Generation\n")
    
    # Step 1: Analyze codebase
    print("Step 1: Analyzing codebase...")
    project_path = Path("./my-api")
    generator = ManifestGenerator(project_path)
    manifest = generator.generate()
    
    print(f"   ✅ Found {len(manifest.services)} services")
    
    # Step 2: Infer business logic
    print("\nStep 2: Inferring business logic...")
    all_endpoints = []
    all_dtos = []
    
    for service in manifest.services:
        all_endpoints.extend(service.endpoints)
        all_dtos.extend(service.dto_schemas)
    
    inference = BusinessLogicInferenceEngine(all_endpoints, all_dtos)
    analysis = inference.analyze()
    
    print(f"   ✅ Detected {len(analysis['flows'])} business flows")
    print(f"   ✅ Found {len(analysis['relationships'])} endpoint relationships")
    
    # Show detected flows
    print("\n   Detected Flows:")
    for flow in analysis['flows'][:3]:
        print(f"     • {flow.name}: {len(flow.steps)} steps")
    
    # Step 3: Generate test suite
    print("\nStep 3: Generating test suite...")
    for service in manifest.services[:1]:
        suite_gen = FlowBasedTestSuiteGenerator(service)
        suite = suite_gen.generate_test_suite()
        
        print(f"   ✅ Generated {len(suite.test_files)} test files")
        print(f"   ✅ Covering {suite.total_scenarios} scenarios")
    
    print("\n✨ AI test generation complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(generate_tests_with_ai())
```

[📋 Copy Code](#) [▶️ Run in Playground](./playground)

---

### Example 5: Intent Recognition

```python
"""
Intent Recognition Example - Parse natural language commands
"""

from socialseed_e2e.ai_protocol import AIProtocolEngine

async def demonstrate_intent_recognition():
    print("🎯 Intent Recognition Demo\n")
    
    # Initialize AI protocol engine
    engine = AIProtocolEngine()
    
    # Test inputs
    test_inputs = [
        "Generate tests for the users API",
        "Run all tests in parallel",
        "Fix the failing login test",
        "Create a new service called 'payments'",
        "Analyze my codebase for security issues",
        "What's the status of test execution?",
    ]
    
    print("Parsing user inputs:\n")
    for user_input in test_inputs:
        intent = engine.parse_user_input(user_input)
        
        print(f"Input: \"{user_input}\"")
        print(f"  Intent: {intent.intent_type.value}")
        print(f"  Confidence: {intent.confidence:.1%}")
        
        if intent.entities:
            print(f"  Entities: {intent.entities}")
        
        if intent.alternative_intents:
            alt = intent.alternative_intents[0]
            print(f"  Alternative: {alt['intent_type']} ({alt['confidence']:.1%})")
        
        print()
    
    print("✨ Intent recognition demo complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(demonstrate_intent_recognition())
```

[📋 Copy Code](#) [▶️ Run in Playground](./playground)

---

## 🔧 Advanced Examples

### Example 6: Parallel Test Execution

```python
"""
Parallel Test Execution Example - Speed up your tests
"""

import asyncio
from socialseed_e2e.core.base_page import BasePage
from concurrent.futures import ThreadPoolExecutor

class ParallelTestPage(BasePage):
    def __init__(self, base_url, worker_id):
        super().__init__(base_url=base_url)
        self.worker_id = worker_id
    
    async def test_endpoint(self, endpoint):
        """Test a single endpoint"""
        print(f"  [Worker {self.worker_id}] Testing {endpoint}...")
        
        response = await self.get(endpoint)
        success = response.status == 200
        
        print(f"  [Worker {self.worker_id}] {endpoint}: {'✅' if success else '❌'}")
        return endpoint, success

async def run_parallel_tests():
    print("⚡ Parallel Test Execution\n")
    
    base_url = "https://api.example.com"
    endpoints = [
        "/users",
        "/products",
        "/orders",
        "/categories",
        "/inventory",
    ]
    
    # Create workers
    num_workers = 3
    pages = [ParallelTestPage(base_url, i) for i in range(num_workers)]
    
    # Distribute endpoints among workers
    print(f"Testing {len(endpoints)} endpoints with {num_workers} workers...\n")
    
    tasks = []
    for i, endpoint in enumerate(endpoints):
        worker = pages[i % num_workers]
        task = worker.test_endpoint(endpoint)
        tasks.append(task)
    
    # Run all tests concurrently
    results = await asyncio.gather(*tasks)
    
    # Close all pages
    for page in pages:
        await page.close()
    
    # Display results
    print("\n📊 Results:")
    passed = sum(1 for _, success in results if success)
    print(f"   Passed: {passed}/{len(endpoints)}")
    print(f"   Failed: {len(endpoints) - passed}/{len(endpoints)}")
    
    print("\n✨ Parallel execution complete!")

if __name__ == "__main__":
    asyncio.run(run_parallel_tests())
```

[📋 Copy Code](#) [▶️ Run in Playground](./playground)

---

### Example 7: Custom Assertions

```python
"""
Custom Assertions Example - Write your own validation logic
"""

from socialseed_e2e.core.base_page import BasePage
from socialseed_e2e.assertions import (
    assert_json_schema,
    assert_response_time,
    assert_header_contains
)

class CustomAssertionPage(BasePage):
    async def validate_api_response(self, response):
        """Apply multiple custom assertions"""
        
        # Assert JSON schema
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["id", "name", "email"]
        }
        assert_json_schema(response, schema)
        print("  ✅ JSON schema valid")
        
        # Assert response time
        assert_response_time(response, max_ms=500)
        print("  ✅ Response time < 500ms")
        
        # Assert headers
        assert_header_contains(response, "content-type", "application/json")
        print("  ✅ Content-Type header correct")
        
        return True
    
    async def test_user_api(self):
        """Test user API with custom assertions"""
        response = await self.get("/api/users/123")
        
        return await self.validate_api_response(response)

async def test_custom_assertions():
    print("🎨 Custom Assertions Demo\n")
    
    page = CustomAssertionPage("https://api.example.com")
    
    print("Testing user API with custom assertions:\n")
    
    try:
        success = await page.test_user_api()
        print(f"\n✅ All assertions passed!")
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
    finally:
        await page.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_custom_assertions())
```

[📋 Copy Code](#) [▶️ Run in Playground](./playground)

---

## 🎓 Try It Yourself

Modify the examples above and run them in the [Interactive Playground](./playground)!

### Next Steps

- 📚 [Read the full documentation](../README.md)
- 🎓 [Complete the tutorials](../notebooks/)
- 💬 [Join the community discussions](https://github.com/daironpf/socialseed-e2e/discussions)
