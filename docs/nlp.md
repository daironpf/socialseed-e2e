# Natural Language to Test Code Translation Engine

## Overview

The Natural Language to Test Code Translation Engine enables users (especially non-technical stakeholders and AI agents) to write tests in plain English, Spanish, or other natural languages. The framework automatically converts these descriptions into executable test code.

## Key Features

### Multi-Language Support
- **English** (en) - Full support
- **Spanish** (es) - Full support
- **French** (fr) - Basic support
- **German** (de) - Basic support
- **Portuguese** (pt) - Basic support
- **Italian** (it) - Basic support

### Context-Aware Generation
The engine understands your existing API structure:
- Endpoints and their HTTP methods
- Request/Response DTOs
- Authentication requirements
- Service structure

### Gherkin/Cucumber Syntax Support
Write tests in BDD style:
```gherkin
Feature: User Login
  Scenario: Successful login
    Given a user with valid credentials
    When the user logs in
    Then they receive a JWT token
```

### Self-Documenting Tests
Generated tests include:
- Comprehensive docstrings
- Preconditions and postconditions
- Extracted entities and actions
- Source natural language reference

### Requirements Traceability
Link generated tests to requirements for full traceability.

## Quick Start

### Basic Translation

```python
from socialseed_e2e.nlp import NLToCodePipeline

# Create pipeline
pipeline = NLToCodePipeline("/path/to/project")

# Translate natural language
result = pipeline.translate(
    "Verify that when a user logs in with valid credentials, "
    "they receive a JWT token with 24h expiration"
)

# View generated code
if result.success:
    print(result.generated_code.code)
```

### Multi-Language Support

```python
from socialseed_e2e.nlp import NLToCodePipeline, Language

pipeline = NLToCodePipeline("/path/to/project")

# Spanish
result = pipeline.translate(
    "Verificar que el usuario puede iniciar sesión",
    language=Language.SPANISH
)

# French
result = pipeline.translate(
    "Vérifier que l'utilisateur peut se connecter",
    language=Language.FRENCH
)
```

### With Context

```python
from socialseed_e2e.nlp import NLToCodePipeline, TranslationContext

pipeline = NLToCodePipeline("/path/to/project")

# Provide context for better generation
context = TranslationContext(
    service="users-api",
    endpoint="/api/login",
    http_method="POST",
    auth_required=False
)

result = pipeline.translate(
    "Create a new user with valid data",
    context=context
)
```

## CLI Commands

### Translate Natural Language

```bash
# Basic translation
e2e translate --description "Verify user can login with valid credentials"

# With service context
e2e translate --description "Create a new order" --service orders-api

# Spanish
e2e translate --description "Verificar inicio de sesión" --language es

# Save to file
e2e translate --description "Test user creation" --output tests/test_user.py
```

### Convert Gherkin Features

```bash
# Convert single feature file
e2e gherkin-translate --feature-file features/login.feature

# Convert all features in directory
e2e gherkin-translate --feature-file features/ --output-dir tests/generated/
```

## Language Support Details

### Supported Intents
- **Verify** - Verify that something works
- **Check** - Check a condition
- **Test** - Test a functionality
- **Validate** - Validate data or behavior
- **Ensure** - Ensure requirements are met
- **Assert** - Make assertions

### Supported Actions
- **Login/Logout** - Authentication actions
- **Create** - POST operations
- **Read** - GET operations
- **Update** - PUT/PATCH operations
- **Delete** - DELETE operations
- **Send/Receive** - Data transfer
- **Search/Filter/Sort** - Query operations

### Supported Entities
- **User/Admin** - Personas
- **Endpoint/API** - API resources
- **Token/Credentials** - Authentication
- **Request/Response** - HTTP messages
- **Data/Field** - Data elements

## Gherkin Support

### Feature Files

Create `.feature` files with Gherkin syntax:

```gherkin
Feature: User Management
  As an admin
  I want to manage users
  So that I can control access

  Background:
    Given the database is initialized
    And an admin user exists

  @smoke @critical
  Scenario: Create new user
    Given a valid user registration request
    When I create a new user
    Then the user is created successfully
    And a welcome email is sent

  Scenario Outline: Login with different credentials
    Given a user with <username> and <password>
    When they attempt to login
    Then the response status should be <status>

    Examples:
      | username | password | status |
      | valid    | valid    | 200    |
      | valid    | invalid  | 401    |
      | invalid  | any      | 401    |
```

### Keywords by Language

| English | Spanish | French | German |
|---------|---------|--------|--------|
| Feature | Característica | Fonctionnalité | Funktionalität |
| Background | Antecedentes | Contexte | Grundlage |
| Scenario | Escenario | Scénario | Szenario |
| Given | Dado | Étant donné | Angenommen |
| When | Cuando | Quand | Wenn |
| Then | Entonces | Alors | Dann |
| And | Y | Et | Und |

## Examples

### Example 1: Simple Login Test

**Input:**
```
Verify that a user can login with valid credentials
```

**Output:**
```python
def test_login_user():
    """
    Verify that a user can login with valid credentials
    
    Entities:
        - user: user
        - credentials: credentials
    
    Actions:
        - login user
    
    Generated from: Verify that a user can login with valid credentials...
    """
    # Initialize page
    page = BasePage("http://localhost:8000")
    page.setup()
    
    # Perform login
    response = page.post("/api/auth/login", json={
        "username": "testuser",
        "password": "Test123!"
    })
    assert response.status == 200
    token = response.json().get("token")
    page.headers["Authorization"] = f"Bearer {token}"
    
    # Cleanup
    page.teardown()
```

### Example 2: Create Resource Test

**Input:**
```
Create a new user with name "John Doe" and email "john@example.com"
```

**Output:**
```python
def test_create_user():
    """
    Create a new user with name "John Doe" and email "john@example.com"
    
    Entities:
        - user: user
    
    Actions:
        - create user
    
    Generated from: Create a new user with name "John Doe"...
    """
    # Initialize page
    page = UsersPage("http://localhost:8000")
    page.setup()
    
    # Create/Send request
    response = page.post("/api/users", json={
        "name": "John Doe",
        "email": "john@example.com"
    })
    page.assert_ok(response)
    
    # Cleanup
    page.teardown()
```

### Example 3: Spanish Description

**Input:**
```
Verificar que el usuario puede crear un nuevo pedido
```

**Output:**
```python
def test_crear_pedido():
    """
    Verificar que el usuario puede crear un nuevo pedido
    
    Entidades:
        - usuario: usuario
        - pedido: order
    
    Acciones:
        - crear pedido
    """
    # Initialize page
    page = BasePage("http://localhost:8000")
    page.setup()
    
    # Crear/Send request
    response = page.post("/api/orders", json={"key": "value"})
    page.assert_ok(response)
    
    # Cleanup
    page.teardown()
```

## Advanced Usage

### Custom Language Patterns

```python
from socialseed_e2e.nlp import LanguagePatterns, Language

# Add custom patterns
patterns = LanguagePatterns.get_patterns(Language.ENGLISH)
patterns["actions"]["custom_action"] = ["custom", "special"]
```

### Context Enrichment

```python
from socialseed_e2e.nlp import ContextEnricher

enricher = ContextEnricher("/path/to/project")

# Enrich parsed test with context
enriched_test = enricher.enrich(parsed_test, context)
```

### Requirements Tracing

```python
from socialseed_e2e.nlp import RequirementsTracer

tracer = RequirementsTracer("/path/to/project")

# Link test to requirement
tracer.link_to_requirement(
    test_name="test_login",
    requirement_id="REQ-001",
    description="User must be able to login"
)

# Get traceability matrix
matrix = tracer.generate_traceability_matrix()
```

## Best Practices

### 1. Be Specific

**Good:**
```
Verify that an authenticated user can create a new order with valid items
```

**Less Good:**
```
Test the order functionality
```

### 2. Include Expected Results

**Good:**
```
Create a user and verify the response status is 201
```

**Less Good:**
```
Create a user
```

### 3. Use Active Voice

**Good:**
```
When the user submits the form, then a confirmation email is sent
```

**Less Good:**
```
The form being submitted by the user causes an email to be sent
```

### 4. Provide Context When Needed

Use the `--service` flag or `TranslationContext` to help the generator understand:
- Which service/endpoint you're testing
- Authentication requirements
- Existing API structure

## Troubleshooting

### Low Confidence Scores

If the translation confidence is low (< 0.6):
1. Be more specific in your description
2. Include expected outcomes
3. Use standard terminology (login, create, update, delete)
4. Provide context with `--service` flag

### Missing Entities

If entities aren't detected:
1. Use entity type keywords (user, endpoint, token, etc.)
2. Include specific names/values
3. Use quotes for string values

### Generated Code Review

Always review generated code before execution if:
- Confidence score is < 0.7
- Test requires authentication
- Complex assertions are needed
- Custom logic is involved

## Architecture

```
nlp/
├── models.py              # Data models
├── translator.py          # Natural language parser
├── context_awareness.py   # Project context understanding
├── code_generator.py      # Test code generation
├── gherkin_parser.py      # Gherkin/Cucumber support
└── __init__.py           # Public API
```

### Flow

1. **Parse** - Natural language → Structured test description
2. **Enrich** - Add project context (endpoints, DTOs)
3. **Generate** - Create executable test code
4. **Validate** - Check for completeness and accuracy

## API Reference

See docstrings in source files for detailed API documentation:
- `socialseed_e2e/nlp/translator.py`
- `socialseed_e2e/nlp/code_generator.py`
- `socialseed_e2e/nlp/context_awareness.py`
- `socialseed_e2e/nlp/gherkin_parser.py`

## Contributing

To add support for a new language:

1. Add language to `Language` enum in `models.py`
2. Add patterns to `LanguagePatterns.PATTERNS` in `translator.py`
3. Add Gherkin keywords to `GherkinParser.KEYWORDS` in `gherkin_parser.py`
4. Add tests in `tests/unit/test_nlp.py`
5. Update documentation
