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

```bash
# Generate manifest in current directory
e2e manifest

# Generate for a specific project
e2e manifest /path/to/project

# Force full re-scan (instead of smart sync)
e2e manifest --force
```

### 2. Query the Manifest

```bash
# Display project summary as JSON
e2e manifest-query

# Display as Markdown
e2e manifest-query -f markdown
```

### 3. Watch Files for Changes

```bash
# Start file watcher with auto-update
e2e watch

# Watch specific project
e2e watch /path/to/project
```

## Project Structure

After running `e2e manifest`, you'll have:

```
project-root/
├── project_knowledge.json     # Generated manifest
├── src/
│   └── ...                    # Your source files
└── ...
```

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

Generate the project manifest.

**Options:**
- `--force`: Force full scan instead of smart sync

**Examples:**
```bash
e2e manifest                    # Current directory
e2e manifest /path/to/project   # Specific project
e2e manifest --force            # Full re-scan
```

### `e2e manifest-query`

Query the generated manifest.

**Options:**
- `--format, -f`: Output format (`json` or `markdown`)

**Examples:**
```bash
e2e manifest-query                    # JSON output
e2e manifest-query -f markdown        # Markdown output
```

### `e2e watch`

Watch files and auto-update manifest.

**Examples:**
```bash
e2e watch                    # Watch current directory
e2e watch /path/to/project   # Watch specific project
```

## Best Practices

1. **Commit the Manifest**: Add `project_knowledge.json` to version control for team collaboration
2. **CI/CD Integration**: Generate manifest in CI to validate project structure
3. **Pre-commit Hook**: Auto-update manifest before commits
4. **AI Agent Integration**: Point AI agents to the manifest for context

### Pre-commit Hook Example

```bash
#!/bin/sh
# .git/hooks/pre-commit

e2e manifest
if [ $? -ne 0 ]; then
    echo "Failed to update manifest"
    exit 1
fi

git add project_knowledge.json
```

## Troubleshooting

### Manifest Not Generated

```bash
# Check if project has source files
find . -name "*.py" -o -name "*.java" -o -name "*.js" | head -10

# Force full scan
e2e manifest --force
```

### Services Not Detected

- Verify source files are in recognized languages
- Check exclude patterns aren't too broad
- Ensure files have proper framework imports

### Outdated Manifest

```bash
# Regenerate with force
e2e manifest --force

# Or use watch mode for automatic updates
e2e watch
```

## API Reference

See the [API Reference](api-reference.md) for detailed documentation of all classes and methods.

## Contributing

Contributions are welcome! See [Contributing Guide](../CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](../LICENSE) for details.
