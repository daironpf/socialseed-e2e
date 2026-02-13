# API Explorer

Interactive API documentation for SocialSeed-E2E.

## Quick Search

Use the search below to find specific APIs:

```
🔍 Search: ____________________________ [Search]

Filter by:
[ ] Core      [ ] Manifest    [ ] AI Protocol
[ ] Testing   [ ] Reporting   [ ] Utils
```

## Core Classes

### ManifestGenerator

Generate project knowledge manifest from codebase.

```python
from socialseed_e2e.project_manifest import ManifestGenerator

generator = ManifestGenerator("/path/to/project")
manifest = generator.generate()
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_root` | `str` or `Path` | Root directory of the project |
| `config` | `Optional[Dict]` | Configuration options |

**Returns:**

- `ProjectKnowledge` - Generated manifest

**Example:**

```python
from pathlib import Path
from socialseed_e2e.project_manifest import ManifestGenerator

# Create generator
project_path = Path("./my-api")
generator = ManifestGenerator(project_path)

# Generate manifest
manifest = generator.generate()

# Access data
print(f"Services: {len(manifest.services)}")
for service in manifest.services:
    print(f"  - {service.name}: {len(service.endpoints)} endpoints")
```

**See also:**
- [ProjectKnowledge](#projectknowledge)
- [ManifestAPI](#manifestapi)

---

### ManifestAPI

Query and interact with the generated manifest.

```python
from socialseed_e2e.project_manifest import ManifestAPI

api = ManifestAPI("/path/to/project")
endpoints = api.get_all_endpoints()
```

**Methods:**

#### `get_all_endpoints()`

Get all endpoints from all services.

```python
endpoints = api.get_all_endpoints()
for ep in endpoints:
    print(f"{ep.method.value} {ep.path}")
```

**Returns:** `List[EndpointInfo]`

---

#### `get_endpoint(path, method=None)`

Get a specific endpoint by path.

```python
endpoint = api.get_endpoint("/api/users", HttpMethod.GET)
if endpoint:
    print(f"Found: {endpoint.name}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` | Endpoint path |
| `method` | `Optional[HttpMethod]` | HTTP method filter |

**Returns:** `Optional[EndpointInfo]`

---

#### `get_dto(name)`

Get a DTO by name.

```python
dto = api.get_dto("UserRequest")
if dto:
    for field in dto.fields:
        print(f"  {field.name}: {field.type}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | DTO name |

**Returns:** `Optional[DtoSchema]`

---

## AI Protocol

### AIProtocolEngine

Main engine for AI Agent Communication Protocol.

```python
from socialseed_e2e.ai_protocol import AIProtocolEngine

engine = AIProtocolEngine()
session_id = engine.initialize_session()
```

**Methods:**

#### `initialize_session(agent_capabilities, agent_requirements)`

Initialize a new communication session.

```python
session_id = engine.initialize_session(
    agent_capabilities=["test_generation", "test_execution"],
    agent_requirements=[]
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_capabilities` | `List[str]` | Capabilities agent supports |
| `agent_requirements` | `List[Requirement]` | Agent requirements |

**Returns:** `str` - Session ID

---

#### `parse_user_input(user_input, session_id)`

Parse natural language input and recognize intent.

```python
intent = engine.parse_user_input("Generate tests for users service")
print(f"Intent: {intent.intent_type.value}")
print(f"Confidence: {intent.confidence}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | Natural language input |
| `session_id` | `Optional[str]` | Session context |

**Returns:** `Intent`

---

#### `process_message(message)`

Process a protocol message.

```python
from socialseed_e2e.ai_protocol.message_formats import ProtocolMessage

# Create request
message = engine.create_request_message("Generate tests", session_id)

# Process
response = engine.process_message(message)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `message` | `ProtocolMessage` | Message to process |

**Returns:** `ProtocolMessage`

---

## Test Runner

### run_all_tests

Run all tests in the project.

```python
from socialseed_e2e.core.test_runner import run_all_tests

results = run_all_tests()
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parallel` | `bool` | `False` | Run tests in parallel |
| `verbose` | `bool` | `False` | Verbose output |
| `filter_tags` | `Optional[List[str]]` | `None` | Filter by tags |

**Returns:** `TestSuiteResult`

**Example:**

```python
from socialseed_e2e.core.test_runner import run_all_tests

# Run all tests
results = run_all_tests(parallel=True, verbose=True)

# Check results
print(f"Total: {results.total}")
print(f"Passed: {results.passed}")
print(f"Failed: {results.failed}")
print(f"Duration: {results.duration:.2f}s")
```

---

## Interactive Examples

Try these live code examples:

### Example 1: Generate Manifest

```python
from socialseed_e2e.project_manifest import ManifestGenerator
from pathlib import Path

# Set your project path
project_path = Path(".")  # Current directory

# Create generator
generator = ManifestGenerator(project_path)

# Generate manifest
manifest = generator.generate()

# Display results
print(f"✅ Manifest generated!")
print(f"   Project: {manifest.project_name}")
print(f"   Services: {len(manifest.services)}")
```

[▶️ Run this example](#)

---

### Example 2: Query Endpoints

```python
from socialseed_e2e.project_manifest import ManifestAPI

api = ManifestAPI(".")
endpoints = api.get_all_endpoints()

print(f"Found {len(endpoints)} endpoints:\n")
for ep in endpoints[:5]:  # Show first 5
    print(f"  {ep.method.value:7} {ep.path}")
```

[▶️ Run this example](#)

---

### Example 3: Parse Intent

```python
from socialseed_e2e.ai_protocol import AIProtocolEngine

engine = AIProtocolEngine()

# Parse user input
intent = engine.parse_user_input("Create tests for auth service")

print(f"Intent: {intent.intent_type.value}")
print(f"Confidence: {intent.confidence:.2%}")
print(f"Entities: {intent.entities}")
```

[▶️ Run this example](#)

---

## Type Reference

### ProjectKnowledge

Root model containing all project information.

```python
class ProjectKnowledge(BaseModel):
    version: str
    project_name: str
    project_root: str
    generated_at: datetime
    last_updated: datetime
    services: List[ServiceInfo]
    file_metadata: Dict[str, FileMetadata]
    global_env_vars: List[EnvironmentVariable]
    metadata: Dict[str, Any]
```

**Methods:**

- `get_service(name)` - Get service by name
- `get_endpoint(path, method)` - Get endpoint by path
- `get_dto(name)` - Get DTO by name

---

### EndpointInfo

REST endpoint information.

```python
class EndpointInfo(BaseModel):
    name: str
    method: HttpMethod
    path: str
    full_path: str
    parameters: List[EndpointParameter]
    request_dto: Optional[str]
    response_dto: Optional[str]
    requires_auth: bool
    auth_roles: List[str]
    file_path: str
    line_number: Optional[int]
    description: Optional[str]
    tags: List[str]
```

---

### Intent

Recognized intent from user input.

```python
@dataclass
class Intent:
    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]
    raw_input: str
    alternative_intents: List[Dict[str, Any]]
```

**Intent Types:**

- `GENERATE_TESTS`
- `EXECUTE_TESTS`
- `ANALYZE_CODE`
- `FIX_TEST`
- `CREATE_SERVICE`
- `CONFIGURE`
- `QUERY`
- `VALIDATE`
- `REFACTOR`
- `DOCUMENT`
- `UNKNOWN`

---

## Search Results

```
Showing 1-10 of 156 results

[Previous] 1 2 3 4 5 ... 16 [Next]
```

---

**💡 Tip:** Use the search box at the top to find specific APIs quickly!
