# AI Project Manifest (JSON Knowledge Base)

The AI Project Manifest is a powerful feature that generates a `project_knowledge.json` file containing structured information about your project's APIs, DTOs, configuration, and service relationships. This enables AI agents to work with your project using significantly fewer tokens.

## Overview

### What is the Project Manifest?

The Project Manifest is a JSON-based knowledge base that stores:

- **Endpoints**: All HTTP endpoints with methods, paths, and parameters
- **DTO Schemas**: Data transfer objects with field types and validation rules
- **Configuration**: Port configurations and environment variables
- **Service Relationships**: Dependencies between microservices

### Why Use It?

1. **Token Optimization**: AI agents can query the JSON manifest instead of parsing raw source code
2. **Fast Analysis**: Pre-computed project structure enables instant insights
3. **Smart Sync**: Only changed files are re-scanned, saving time
4. **Multi-Language Support**: Works with Python, Java, JavaScript/TypeScript, and more

## Installation

The project manifest is included in `socialseed-e2e` by default. No additional installation required.

## Quick Start

### 1. Generate the Manifest

The manifest is generated for a microservice and stored in a centralized folder within the framework (NOT in the microservice directory).

```bash
# Generate manifest for a microservice
# The manifest is saved at: <framework_root>/manifests/<service_name>/project_knowledge.json
e2e manifest ../services/auth-service

# Force full re-scan (instead of smart sync)
e2e manifest ../services/auth-service --force
```

### 2. Query the Manifest

Use the service name to query the manifest:

```bash
# Display project summary as JSON
e2e manifest-query auth-service

# Display as Markdown
e2e manifest-query auth-service -f markdown
```

### 3. Watch Files for Changes

```bash
# Start file watcher with auto-update for a specific service
e2e watch auth-service
```

## Project Structure

After running `e2e manifest`, the manifest is stored in the framework's manifests folder:

```
socialseed-e2e/                          # Framework root
├── manifests/                            # Centralized manifests folder
│   ├── auth-service/                   # Manifest for auth service
│   │   └── project_knowledge.json
│   ├── user-service/                    # Manifest for user service
│   │   └── project_knowledge.json
│   └── payment-service/                 # Manifest for payment service
│       └── project_knowledge.json
└── src/
    └── socialseed_e2e/                  # Framework source code
```

This approach keeps the microservice code clean while providing a centralized location for AI agents to query project knowledge.

## Manifest Schema

### ProjectKnowledge

Root object containing all project information:

```json
{
  "version": "1.0.0",
  "project_name": "my-api",
  "project_root": "/path/to/project",
  "generated_at": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-15T10:30:00Z",
  "services": [...],
  "file_metadata": {...},
  "global_env_vars": [...]
}
```

### ServiceInfo

Each detected service:

```json
{
  "name": "users-api",
  "language": "python",
  "framework": "fastapi",
  "root_path": "/services/users",
  "endpoints": [...],
  "dto_schemas": [...],
  "ports": [...],
  "environment_vars": [...],
  "dependencies": [...]
}
```

### EndpointInfo

REST endpoint details:

```json
{
  "name": "create_user",
  "method": "POST",
  "path": "/users",
  "full_path": "/api/v1/users",
  "parameters": [...],
  "request_dto": "UserRequest",
  "response_dto": "UserResponse",
  "requires_auth": true,
  "file_path": "/routes.py",
  "line_number": 25
}
```

### DtoSchema

DTO definition:

```json
{
  "name": "UserRequest",
  "fields": [
    {
      "name": "username",
      "type": "str",
      "required": true,
      "validations": [
        {"rule_type": "min_length", "value": 3},
        {"rule_type": "max_length", "value": 50}
      ]
    }
  ],
  "file_path": "/dtos.py",
  "line_number": 10
}
```

## Supported Languages and Frameworks

### Python
- **FastAPI**: Detects `@app.get()`, `@app.post()`, etc.
- **Flask**: Detects `@app.route()` decorators
- **Django**: Basic detection (limited)
- **Pydantic**: Extracts models with validation rules

### Java
- **Spring Boot**: Detects `@RestController`, `@GetMapping`, etc.
- **Records**: Extracts Java record definitions
- **Validation annotations**: `@NotNull`, `@Size`, `@Email`, etc.

### JavaScript/TypeScript
- **Express.js**: Detects `app.get()`, `app.post()`, etc.
- **TypeScript**: Extracts interfaces and types
- **NestJS**: Basic detection

## Smart Sync

The smart sync feature detects file changes and only re-scans modified files:

```python
from socialseed_e2e.project_manifest import ManifestGenerator

generator = ManifestGenerator("/path/to/project")
manifest = generator.generate()  # Automatically uses smart sync
```

### How It Works

1. **First Run**: Performs full project scan
2. **Subsequent Runs**: Compares file checksums
3. **Incremental Update**: Only scans changed/new files
4. **Deleted Files**: Removes entries for deleted files

## Internal API

Query the manifest programmatically:

```python
from socialseed_e2e.project_manifest import ManifestAPI, HttpMethod

# Initialize API
api = ManifestAPI("/path/to/project")

# Get all services
services = api.get_services()

# Get specific endpoint
endpoint = api.get_endpoint("/api/users", HttpMethod.POST)

# Search endpoints
results = api.search_endpoints(tags=["auth"])

# Get DTO fields
fields = api.get_dto_fields("UserRequest")

# Get project summary
summary = api.get_summary()
```

### Token-Optimized Queries

For minimal token usage:

```python
from socialseed_e2e.project_manifest import ManifestAPI, TokenOptimizedQuery

api = ManifestAPI("/path/to/project")
query = TokenOptimizedQuery(api)

# Compact signatures
endpoint_sig = query.get_endpoint_signature("/api/users", HttpMethod.POST)
dto_sig = query.get_dto_signature("UserRequest")

# Compact lists
all_endpoints = query.list_all_endpoints_compact()
all_dtos = query.list_all_dtos_compact()
```

## File Watcher

Monitor files for changes:

```python
from socialseed_e2e.project_manifest import ManifestGenerator, SmartSyncManager

generator = ManifestGenerator("/path/to/project")
manager = SmartSyncManager(generator)

# Start watching
manager.start_watching(blocking=True)  # Blocks until interrupted
```

### With Debouncing

```python
# Wait 5 seconds after last change before updating
manager = SmartSyncManager(generator, debounce_seconds=5.0)
```

## Configuration

### Exclude Patterns

Exclude files from scanning:

```python
generator = ManifestGenerator(
    project_root="/path/to/project",
    exclude_patterns=[
        "**/node_modules/**",
        "**/__pycache__/**",
        "**/tests/**",
        "**/*.test.py",
    ]
)
```

### Custom Manifest Path

```python
generator = ManifestGenerator(
    project_root="/path/to/project",
    manifest_path=Path("/custom/path/manifest.json")
)
```

## CLI Commands

### `e2e manifest`

Generate the project manifest for a microservice. The manifest is stored in the framework's manifests folder.

**Arguments:**
- `directory`: Path to the microservice directory (e.g., `../services/auth-service`)

**Options:**
- `--force`: Force full scan instead of smart sync

**Examples:**
```bash
e2e manifest ../services/auth-service   # Generate for auth service
e2e manifest ../services/user-service    # Generate for user service
e2e manifest ../services/auth-service --force  # Force full re-scan
```

### `e2e manifest-query`

Query the generated manifest using the service name.

**Arguments:**
- `directory`: Service name (e.g., `auth-service`)

**Options:**
- `--format, -f`: Output format (`json` or `markdown`)

**Examples:**
```bash
e2e manifest-query auth-service           # JSON output
e2e manifest-query auth-service -f markdown  # Markdown output
```

### `e2e manifest-check`

Validate manifest freshness using source code hashes.

**Arguments:**
- `directory`: Service name (e.g., `auth-service`)

**Examples:**
```bash
e2e manifest-check auth-service
```

### `e2e build-index`

Build vector index for semantic search.

**Arguments:**
- `directory`: Service name (e.g., `auth-service`)

**Examples:**
```bash
e2e build-index auth-service
```

### `e2e search`

Semantic search on project manifest.

**Arguments:**
- `query`: Search query

**Options:**
- `--service, -s`: Service name (required)
- `--top-k, -k`: Number of results (default: 5)
- `--type, -t`: Filter by type (`endpoint`, `dto`, `service`)

**Examples:**
```bash
e2e search "authentication endpoints" -s auth-service
e2e search "user DTO" -s user-service --type dto
```

### `e2e retrieve`

Retrieve context for a specific task.

**Arguments:**
- `task`: Task description

**Options:**
- `--service, -s`: Service name (required)
- `--max-chunks, -c`: Maximum chunks (default: 5)

**Examples:**
```bash
e2e retrieve "create auth tests" -s auth-service
e2e retrieve "test payment flow" -s payment-service --max-chunks 3
```

### `e2e watch`

Watch files and auto-update manifest for a specific service.

**Arguments:**
- `directory`: Service name (e.g., `auth-service`)

**Examples:**
```bash
e2e watch auth-service
```

## Best Practices

1. **Centralized Manifest Location**: The manifest is stored in `<framework_root>/manifests/<service_name>/` - this keeps microservices clean
2. **AI Agent Usage**: Point AI agents to the manifest location for context instead of parsing source code
3. **CI/CD Integration**: Generate manifest in CI to validate project structure
4. **Use Smart Sync**: Let the system detect changes automatically instead of full rescans

### Workflow for AI Agents

```bash
# 1. Generate manifest for the microservice
e2e manifest ../services/auth-service

# 2. Query to understand the service
e2e manifest-query auth-service

# 3. Build index for semantic search (requires rag extras)
e2e build-index auth-service

# 4. Use search/retrieve for context
e2e search "login endpoint" -s auth-service
e2e retrieve "write tests" -s auth-service
```

### Pre-commit Hook Example

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Update manifest for known services
for service in auth-service user-service payment-service; do
    e2e manifest ../services/$service
    if [ $? -ne 0 ]; then
        echo "Failed to update manifest for $service"
        exit 1
    fi
done
```

## Troubleshooting

### Manifest Not Found

```bash
# Check if manifest exists in the framework
ls -la src/manifests/<service_name>/

# Generate manifest
e2e manifest ../services/<service_name>
```

### Services Not Detected

- Verify source files are in recognized languages
- Check exclude patterns aren't too broad
- Ensure files have proper framework imports

### Outdated Manifest

```bash
# Check freshness
e2e manifest-check auth-service

# Regenerate with force
e2e manifest ../services/auth-service --force

# Or use watch mode for automatic updates
e2e watch auth-service
```

## API Reference

See the [API Reference](api-reference.md) for detailed documentation of all classes and methods.

## Contributing

Contributions are welcome! See [Contributing Guide](../CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](../LICENSE) for details.
