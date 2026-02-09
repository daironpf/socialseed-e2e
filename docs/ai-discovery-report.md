# AI Discovery Report (Issue #187)

## Overview

The **AI Discovery Report** is a comprehensive summary automatically generated after scanning your project. It presents a "Mental Map" of what the AI understood about your codebase, including discovered endpoints, business flows, and generated test suites.

## What is a Discovery Report?

After running `e2e manifest` or `e2e generate-tests`, the AI analyzes your project and creates a detailed report that says something like:

> "I've analyzed your project. I found **15 REST endpoints** in **Java/Spring**. I've created **3 complex user flows** (Auth, Management, CRUD) in your `services/` folder. Ready to run?"

## Features

### 📊 Project Statistics
- Total services discovered
- REST endpoints count
- DTOs/Models identified
- Business flows detected
- Test files generated

### 🧠 Mental Map
The report includes:
- **Technology Stack**: Frameworks and languages detected
- **Service Architecture**: Microservices and their relationships
- **Business Flows**: Authentication, CRUD, Management, etc.
- **Endpoint Inventory**: All discovered API endpoints

### 🚀 Single Command Execution
The report provides a single command to run all tests:
```bash
e2e run
```

## Usage

### Automatic Generation

The Discovery Report is automatically generated after:

```bash
# After generating tests
e2e generate-tests

# Output:
# 📝 Generating AI Discovery Report...
#    ✓ Report saved: /project/.e2e/DISCOVERY_REPORT.md
```

### Manual Generation

Generate the report at any time:

```bash
# Generate for current project
e2e discover

# Generate for specific project
e2e discover /path/to/project

# Generate and open the report
e2e discover --open
```

### View the Report

The report is saved as a markdown file:

```bash
# Open the report
cat .e2e/DISCOVERY_REPORT.md

# Or use --open flag
e2e discover --open
```

## Report Structure

### 1. Header
```markdown
# 🔍 AI Discovery Report

**Project:** `my-api`
**Path:** `/home/user/my-api`
**Generated:** 2026-02-08 15:30:45
```

### 2. Technology Stack
```markdown
### 📦 Technology Stack

- **users-service**: Spring Boot (java)
- **payment-service**: FastAPI (python)
```

### 3. Statistics
```markdown
### 📊 Project Statistics

| Metric | Count |
|--------|-------|
| Services | 3 |
| REST Endpoints | 15 |
| DTOs/Models | 12 |
| Business Flows | 3 |
| Test Files Generated | 8 |
```

### 4. Discovered Flows
```markdown
### 🌊 Discovered Business Flows

#### 🔐 User Authentication Flow

- **Description:** Complete user registration and authentication flow
- **Type:** Authentication
- **Endpoints:** 3
- **Complexity:** 🟢 Simple

#### 📋 User CRUD Operations

- **Description:** Full CRUD lifecycle for user entities
- **Type:** Crud
- **Endpoints:** 4
- **Complexity:** 🟡 Moderate
```

### 5. Quick Start
```markdown
## 🚀 Ready to Run?

### Execute All Tests

```bash
cd /home/user/my-api
e2e run
```
```

### 6. Command Reference
```markdown
### 📖 Quick Reference

| Command | Description |
|---------|-------------|
| `e2e run` | Run all tests |
| `e2e run --service <name>` | Run tests for specific service |
| `e2e run --verbose` | Run with detailed output |
```

## Example Report

Here's a complete example:

```markdown
# 🔍 AI Discovery Report

**Project:** `ecommerce-api`
**Path:** `/home/user/ecommerce-api`
**Generated:** 2026-02-08 15:30:45

---

## 🧠 Mental Map of Your Project

### 📦 Technology Stack

- **users-service**: Spring Boot (java)
- **products-service**: FastAPI (python)
- **orders-service**: Express.js (javascript)

### 📊 Project Statistics

| Metric | Count |
|--------|-------|
| Services | 3 |
| REST Endpoints | 24 |
| DTOs/Models | 18 |
| Business Flows | 5 |
| Test Files Generated | 12 |

### 🌊 Discovered Business Flows

#### 🔐 User Authentication Flow
- **Description:** Registration → Login → Token refresh
- **Type:** Authentication
- **Endpoints:** 3
- **Complexity:** 🟢 Simple

#### 📋 Product Catalog Management
- **Description:** Create, list, update, delete products
- **Type:** Crud
- **Endpoints:** 5
- **Complexity:** 🟡 Moderate

#### 🛒 Complete Checkout Flow
- **Description:** Cart → Checkout → Payment → Order confirmation
- **Type:** Workflow
- **Endpoints:** 6
- **Complexity:** 🔴 Complex

---

## 🚀 Ready to Run?

I've analyzed your project and created comprehensive test suites.

### Execute All Tests

```bash
cd /home/user/ecommerce-api
e2e run
```

✅ **Ready to run?** Execute: `e2e run`
```

## API Usage

### Generate Report Programmatically

```python
from socialseed_e2e.project_manifest import generate_discovery_report
from pathlib import Path

# Generate report
report_path = generate_discovery_report(
    project_root=Path("/path/to/project"),
    manifest=manifest,  # Optional: ProjectKnowledge object
    flows=discovered_flows,  # Optional: List of flows
    tests_generated=8,  # Optional: Number of test files
)

print(f"Report generated: {report_path}")
```

### Using DiscoveryReportGenerator

```python
from socialseed_e2e.project_manifest import DiscoveryReportGenerator
from pathlib import Path

# Create generator
generator = DiscoveryReportGenerator(Path("/path/to/project"))

# Generate report
report_path = generator.generate_report(
    manifest=manifest,
    flows=flows,
    tests_generated=8,
    output_dir=Path("services")
)
```

## CLI Reference

### `e2e discover`

**Syntax:**
```bash
e2e discover [DIRECTORY] [OPTIONS]
```

**Arguments:**
- `DIRECTORY`: Project directory (default: current directory)

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output directory for report | `.e2e/` |
| `--open` | `--view` | Open the report after generation | Disabled |

**Examples:**

```bash
# Generate for current project
e2e discover

# Generate for specific project
e2e discover /path/to/project

# Generate and open
e2e discover --open

# Generate with custom output
e2e discover --output ./reports
```

## Integration with Other Commands

### After `e2e manifest`

```bash
e2e manifest
e2e discover  # Generate report from manifest
```

### After `e2e generate-tests`

The report is generated automatically:

```bash
e2e generate-tests

# Output includes:
# 📝 Generating AI Discovery Report...
#    ✓ Report saved: .e2e/DISCOVERY_REPORT.md
```

### After `e2e observe`

Combine with service detection:

```bash
e2e observe  # Detect running services
e2e discover  # Generate report
```

## Customization

### Report Location

By default, reports are saved to `.e2e/DISCOVERY_REPORT.md`:

```
project/
├── .e2e/
│   └── DISCOVERY_REPORT.md
├── services/
└── e2e.conf
```

### Report Content

The report automatically includes:
- ✅ Project metadata
- ✅ Technology stack
- ✅ Service statistics
- ✅ Business flows
- ✅ Execution commands
- ✅ Quick reference

## Troubleshooting

### "No project manifest found"

**Problem**: Report generation requires a manifest.

**Solution:**
```bash
# Generate manifest first
e2e manifest

# Then generate report
e2e discover
```

### Report not updating

**Problem**: Old report showing outdated information.

**Solution:**
```bash
# Force regeneration
e2e manifest --force
e2e generate-tests --force
e2e discover
```

### Missing flows in report

**Problem**: Business flows not appearing.

**Solution:**
Flows are detected during `e2e generate-tests`. Make sure to run that command first.

## Best Practices

### 1. Review After Generation

Always review the Discovery Report after generation:

```bash
e2e generate-tests
cat .e2e/DISCOVERY_REPORT.md
```

### 2. Share with Team

The report is a great way to onboard new developers:

```bash
# Commit the report
git add .e2e/DISCOVERY_REPORT.md
git commit -m "docs: Add AI Discovery Report"
```

### 3. Keep Updated

Regenerate when code changes:

```bash
# After major code changes
e2e manifest --force
e2e discover
```

## Comparison with Other Features

| Feature | Purpose | Output |
|---------|---------|--------|
| `e2e manifest` | Analyze code | `project_knowledge.json` |
| `e2e generate-tests` | Create tests | `services/` directory |
| `e2e observe` | Find running services | CLI output |
| `e2e discover` | **Generate report** | **`.e2e/DISCOVERY_REPORT.md`** |

## Future Enhancements

Planned improvements for Issue #187:

- [ ] Interactive HTML report
- [ ] Visual service dependency graph
- [ ] API diff reporting (what changed since last scan)
- [ ] Integration with CI/CD pipelines
- [ ] Export to PDF
- [ ] Custom report templates

## See Also

- [Autonomous Test Generation](autonomous-test-generation-guide.md) - How tests are generated
- [The Observer](the-observer.md) - Service detection
- [Project Manifest](project-manifest.md) - Underlying data structure
