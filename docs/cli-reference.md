# CLI Reference

## Global Options

```bash
e2e [command] [options]
```

- `--version`: Show version
- `--help`: Show help

## Commands

### init

Initialize a new E2E project:

```bash
e2e init [directory]
```

Creates:
- `e2e.conf`
- `services/`
- `tests/`

### run

Run tests:

```bash
e2e run [options]
  --service <name>     Run tests for specific service
  --module <name>      Run specific test module
  --verbose            Enable verbose output
  --output <format>    Output format (text, json)
```

### new-service

Create a new service:

```bash
e2e new-service <name> [options]
```

### new-test

Create a new test:

```bash
e2e new-test <name> --service <svc> [options]
```

### doctor

Verify installation:

```bash
e2e doctor
```

Checks:
- Playwright installation
- Browser availability
- Configuration file
- Directory structure

### config

Show configuration:

```bash
e2e config
```

## Examples

```bash
# Initialize project
e2e init

# Create service
e2e new-service users

# Create test
e2e new-test login --service users

# Run all tests
e2e run

# Run specific service
e2e run --service users

# Check installation
e2e doctor
```
