# Autonomous Test Generation (Issue #185)

## Overview

The **Autonomous Test Generation** feature enables socialseed-e2e to automatically generate complete end-to-end test suites by analyzing your codebase's business logic, database models, and validation rules.

## Features

### 1. Business Logic Inference
The system analyzes your API endpoints to understand business flows:

- **Authentication Flows**: Detects register → login → authenticated operations
- **CRUD Lifecycle**: Creates tests for Create → Read → Update → Delete patterns
- **Entity Relationships**: Understands how entities relate to each other
- **Sequential Dependencies**: Identifies endpoints that must be called in order

### 2. Database Model Parsing
Supports multiple ORM frameworks:

- **SQLAlchemy** (Python): Parses declarative models and mapped columns
- **Prisma**: Reads schema.prisma files
- **Hibernate/JPA** (Java): Extracts entity annotations

### 3. Intelligent Dummy Data Generation
Generates realistic test data based on:

- Database constraints (type, length, nullable, unique)
- Validation rules (min/max length, regex patterns, ranges)
- Field name semantics (email, username, phone, etc.)
- Foreign key relationships

### 4. Multi-Strategy Testing
Creates tests for different scenarios:

- **Valid Data**: Tests that should succeed
- **Invalid Data**: Tests that should fail validation
- **Edge Cases**: Boundary value testing (min, max, empty)
- **Chaos Tests**: Random/fuzzy data testing

## Usage

### Basic Usage

Generate tests for all services in your project:

```bash
e2e generate-tests
```

### Generate for Specific Service

```bash
e2e generate-tests --service users-api
```

### Dry Run (Preview)

See what would be generated without creating files:

```bash
e2e generate-tests --dry-run
```

### Strategy Selection

Generate only specific test types:

```bash
# Only chaos tests
e2e generate-tests --strategy chaos

# Only validation edge cases
e2e generate-tests --strategy edge
```

### Custom Output Directory

```bash
e2e generate-tests --output ./custom-tests
```

## How It Works

### Step 1: Database Model Parsing

The system scans your project for database models:

```python
# Example: SQLAlchemy model
def parse_sqlalchemy_models(project_path):
    parser = SQLAlchemyParser(project_path)
    schema = parser.parse_project()

    for entity in schema.entities:
        print(f"Found entity: {entity.name}")
        for column in entity.columns:
            print(f"  - {column.name}: {column.data_type}")
```

### Step 2: Business Logic Analysis

Detects relationships and flows:

```python
from socialseed_e2e.project_manifest import BusinessLogicInferenceEngine

# Analyze endpoints
engine = BusinessLogicInferenceEngine(endpoints, dtos)
analysis = engine.analyze()

# Access detected flows
for flow in analysis["flows"]:
    print(f"Flow: {flow.name}")
    for step in flow.steps:
        print(f"  Step {step.step_number}: {step.endpoint.name}")
```

### Step 3: Data Generation

Generates context-aware test data:

```python
from socialseed_e2e.project_manifest import DummyDataGenerator

generator = DummyDataGenerator(db_schema=schema)

# Generate valid data for a DTO
dto = service.get_dto("UserRequest")
data = generator.generate_for_dto(dto, DataGenerationStrategy.VALID)

# Generate multiple test scenarios
scenarios = generator.generate_test_scenarios(dto, num_valid=3, num_invalid=2)
```

### Step 4: Test Generation

Creates complete test suites:

```python
from socialseed_e2e.project_manifest import FlowBasedTestSuiteGenerator

# Create generator
generator = FlowBasedTestSuiteGenerator(service_info, db_schema)

# Generate suite
suite = generator.generate_test_suite()

# Write to files
generator.write_to_files(Path("./services"))
```

## Generated Files

For each service, the following files are created:

```
services/{service_name}/
├── __init__.py
├── data_schema.py          # DTOs and test data
├── {service_name}_page.py  # Page object with flow methods
└── modules/
    ├── _01_auth_flow.py    # Authentication flow tests
    ├── _02_crud_flow.py    # CRUD lifecycle tests
    └── _99_validation_tests.py  # Edge case tests
```

### data_schema.py

Contains:
- Pydantic models for all DTOs
- Endpoint constants
- Test data dictionaries
- Validation rules

### {service}_page.py

Contains:
- Page class extending BasePage
- Individual endpoint methods (`do_create_user`, `do_login`, etc.)
- Flow execution methods (`run_auth_flow`, etc.)
- State management between steps

### Test Modules

Each flow gets its own test module:

```python
def run(page: UsersApiPage) -> APIResponse:
    """Execute User Authentication Flow test."""
    results = page.run_user_authentication_flow_flow()

    assert results["success"], "Flow failed"

    return page.do_login(...)
```

## Configuration

### Validation Rules Detection

The system automatically detects validation rules from:

**SQLAlchemy:**
```python
username = Column(String(50), nullable=False, unique=True)
email = Column(String(100), nullable=False)
age = Column(Integer, nullable=False)
```

**Pydantic:**
```python
class UserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: int = Field(..., ge=18, le=120)
```

**Java/Hibernate:**
```java
@NotNull
@Size(min=3, max=50)
private String username;

@Email
@NotBlank
private String email;
```

### Generated Test Scenarios

For each validation rule, the system generates:

```python
# Success scenario
{
    "name": "Valid UserRequest",
    "data": {"username": "john_doe", "email": "john@example.com", "age": 25},
    "expected": "success"
}

# Failure scenarios
{
    "name": "username - Below Minimum Length",
    "data": {"username": "ab", "email": "john@example.com", "age": 25},
    "expected": "validation_error"
}

# Edge cases
{
    "name": "username - At Minimum Boundary (3)",
    "data": {"username": "abc", "email": "john@example.com", "age": 25},
    "expected": "success"
}
```

## Examples

### Example 1: Simple CRUD API

Given a User API with endpoints:
- `POST /users` - Create user
- `GET /users/{id}` - Get user
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

The generator creates:
1. A flow that tests: Create → Get → Update → Delete
2. Validation tests for each field
3. Edge case tests for boundaries

### Example 2: Authentication Flow

Given endpoints:
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me` (requires auth)

The generator creates:
1. Registration → Login → Get Profile flow
2. Tests for invalid credentials
3. Tests for token expiration

### Example 3: E-commerce Checkout

Given endpoints:
- `POST /cart/items`
- `POST /checkout`
- `POST /payment`
- `POST /orders/confirm`

The generator creates:
1. Complete checkout workflow test
2. Tests for each step in isolation
3. Failure scenarios (insufficient stock, invalid payment)

## Best Practices

### 1. Review Generated Tests

Always review generated tests before running them:

```bash
# Generate in dry-run mode first
e2e generate-tests --dry-run

# Then generate for real
e2e generate-tests

# Review the files
vim services/users-api/modules/_01_auth_flow.py
```

### 2. Customize Test Data

Edit `data_schema.py` to customize test values:

```python
TEST_DATA = {
    "auth_flow": {
        "register": {
            "email": "your-test-email@example.com",
            "password": "YourTestPassword123!"
        }
    }
}
```

### 3. Run Generated Tests

```bash
# Run all tests
e2e run

# Run specific service
e2e run --service users-api

# Run specific flow
e2e run --service users-api --module _01_auth_flow
```

### 4. Update Tests When API Changes

When your API changes, regenerate tests:

```bash
# Update the manifest first
e2e manifest --force

# Regenerate tests
e2e generate-tests --force
```

## API Reference

### BusinessLogicInferenceEngine

```python
class BusinessLogicInferenceEngine:
    def __init__(self, endpoints: List[EndpointInfo], dtos: List[DtoSchema])
    def analyze(self) -> Dict[str, Any]
    def get_flow_for_entity(self, entity_name: str) -> Optional[BusinessFlow]
    def suggest_test_scenarios(self) -> List[Dict[str, Any]]
```

### DummyDataGenerator

```python
class DummyDataGenerator:
    def __init__(self, db_schema: Optional[DatabaseSchema] = None)
    def generate_for_dto(self, dto: DtoSchema, strategy: DataGenerationStrategy) -> Dict[str, GeneratedData]
    def generate_for_entity(self, entity: EntityInfo, strategy: DataGenerationStrategy) -> Dict[str, GeneratedData]
    def generate_test_scenarios(self, dto: DtoSchema, num_valid: int, num_invalid: int) -> List[Dict[str, Any]]
```

### FlowBasedTestSuiteGenerator

```python
class FlowBasedTestSuiteGenerator:
    def __init__(self, service_info: ServiceInfo, db_schema: Optional[DatabaseSchema] = None)
    def generate_test_suite(self) -> GeneratedTestSuite
    def write_to_files(self, output_dir: Path) -> None
```

## Troubleshooting

### Issue: No flows detected

**Solution**: Ensure your endpoints have descriptive names:
- Good: `createUser`, `loginUser`, `getUserById`
- Bad: `handler1`, `process`, `action`

### Issue: No database models found

**Solution**: Check file locations:
- SQLAlchemy: `models.py`, `db.py`, `database.py`
- Prisma: `schema.prisma`
- Hibernate: `*.java` files with `@Entity`

### Issue: Invalid data generation

**Solution**: Manually specify test data in `data_schema.py`:

```python
TEST_DATA = {
    "custom_values": {
        "email": "specific@example.com"
    }
}
```

## Integration with CI/CD

Add to your GitHub Actions workflow:

```yaml
- name: Generate E2E Tests
  run: |
    pip install socialseed-e2e
    e2e manifest
    e2e generate-tests

- name: Run E2E Tests
  run: |
    e2e run --output json > test-results.json
```

## Future Enhancements

Planned improvements for Issue #185:

- [ ] Support for GraphQL APIs
- [ ] AI-powered test scenario generation using LLMs
- [ ] Visual flow diagram generation
- [ ] Integration with OpenAPI/Swagger specs
- [ ] Smart test data persistence across runs
- [ ] Custom rule definition via configuration files
