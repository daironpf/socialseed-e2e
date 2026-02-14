# Migration Assistant - Importers Module

This module provides import functionality for migrating from other tools and formats into SocialSeed E2E.

## Supported Formats

### 1. Postman Collections (v2.1)
Import Postman collections and convert them to SocialSeed E2E test modules.

```bash
e2e import postman ./my-collection.json --output ./services/api --service-name user-api
```

**Features:**
- Converts requests to async test functions
- Extracts headers, query params, and body
- Handles Postman variables (`{{variable}}`)
- Generates Page Objects automatically
- Preserves folder structure in comments

**Output:**
- Test files in `services/<name>/modules/`
- Page Object: `<name>_page.py`
- Config file with base URL

### 2. Postman Environments
Import Postman environment files into framework configuration.

```bash
e2e import environment ./environment.json --output ./config --service-name production
```

**Output:**
- `imported_config.yaml` with variables

### 3. OpenAPI / Swagger (3.0+)
Import OpenAPI specifications to generate test skeletons.

```bash
e2e import openapi ./swagger.yaml --output ./services/api --service-name payment-api --generate-scenarios
```

**Features:**
- Supports OpenAPI 3.0, 3.1, and Swagger 2.0
- Generates tests for all endpoints
- Extracts request/response schemas
- Creates example data from schemas
- Generates service configuration

**Output:**
- Test files for each endpoint
- Page Object with typed methods
- Complete service configuration

### 4. Curl Commands
Import curl commands to generate test cases.

```bash
# Single command
e2e import curl "curl -X POST https://api.example.com/users -d '{name:John}'"

# From file
e2e import curl @commands.txt --output ./services/imported
```

**Features:**
- Parses headers (-H)
- Handles methods (-X)
- Extracts data (-d)
- Supports authentication (-u)

## Usage Examples

### Complete Migration Workflow

```bash
# 1. Import Postman collection
e2e import postman ./postman/MyAPI.postman_collection.json \
    --output ./services/myapi \
    --service-name myapi

# 2. Import environment
e2e import environment ./postman/MyAPI.postman_environment.json \
    --output ./services/myapi \
    --service-name myapi

# 3. Review and customize generated files
ls ./services/myapi/
# myapi_page.py
# test_*.py
# imported_config.yaml

# 4. Run imported tests
e2e run --service myapi
```

### Importing OpenAPI with Scenarios

```bash
# Import with scenario generation
e2e import openapi ./swagger.json \
    --output ./services/payments \
    --service-name payment-service \
    --generate-scenarios

# Review generated scenarios
cat ./services/payments/scenarios.md

# Run specific scenario
e2e run --service payment-service --scenario checkout-flow
```

## API Usage

```python
from socialseed_e2e.importers import (
    PostmanImporter,
    OpenAPIImporter,
    CurlImporter,
    PostmanEnvironmentImporter
)
from pathlib import Path

# Postman
importer = PostmanImporter(
    output_dir=Path("./services/imported"),
    service_name="my-service"
)
result = importer.import_file(Path("./collection.json"))

if result.success:
    print(f"Imported {len(result.tests)} tests")
    for warning in result.warnings:
        print(f"Warning: {warning}")

# OpenAPI
importer = OpenAPIImporter(
    output_dir=Path("./services/api"),
    service_name="api-service"
)
result = importer.import_file(Path("./swagger.yaml"))

# Curl
importer = CurlImporter(output_dir=Path("./services/imported"))
result = importer.import_command('curl -X GET https://api.example.com/users')
```

## Architecture

```
importers/
├── __init__.py              # Exports all importers
├── base.py                  # BaseImporter class
├── postman_importer.py      # Postman Collection & Environment
├── openapi_importer.py      # OpenAPI/Swagger specs
└── curl_importer.py         # Curl commands
```

### BaseImporter

All importers extend `BaseImporter` which provides:
- File output management
- Name sanitization
- Warning collection
- Result tracking

### ImportResult

```python
result = ImportResult(
    success=True,
    message="Imported 5 tests",
    tests=[...],
    warnings=["Deprecated header detected"]
)
```

## Limitations

### Postman
- Scripts (pre-request, tests) are extracted but may need manual conversion
- Binary file uploads are not supported
- OAuth flows require manual configuration

### OpenAPI
- Complex authentication schemes need manual setup
- Callbacks and webhooks are not imported
- Some vendor extensions are ignored

### Curl
- Multi-part form data is simplified
- Complex redirects may not be preserved
- File uploads need manual configuration

## Extending

To add a new importer:

1. Create a new file: `my_importer.py`
2. Extend `BaseImporter`
3. Implement `import_file()` and `generate_code()`
4. Add CLI command in `cli.py`
5. Export in `__init__.py`

Example:

```python
from socialseed_e2e.importers.base import BaseImporter, ImportResult

class MyImporter(BaseImporter):
    def import_file(self, file_path: Path) -> ImportResult:
        # Parse your format
        tests = self._parse(file_path)
        
        # Generate code
        for test in tests:
            code = self.generate_code(test)
            self._write_test_file(test["name"], code)
        
        return ImportResult(
            success=True,
            message=f"Imported {len(tests)} tests",
            tests=tests
        )
    
    def generate_code(self, data: Dict) -> str:
        return f"async def run(page): ..."
```

## Troubleshooting

### Import fails with "Invalid JSON"
- Check file encoding (should be UTF-8)
- Validate JSON syntax
- For YAML, ensure PyYAML is installed: `pip install pyyaml`

### Tests don't run
- Check if `async def run(page)` is properly defined
- Verify imports in generated files
- Ensure Page Object extends BasePage

### Variables not replaced
- Postman variables `{{var}}` should be defined in collection or environment
- Check that environment was imported correctly
- Review generated code for `f-strings` with variables

## See Also

- [Main Documentation](../../docs/)
- [CLI Import Commands](../../docs/cli-import.md)
- [Migration Guide](../../docs/migration.md)
