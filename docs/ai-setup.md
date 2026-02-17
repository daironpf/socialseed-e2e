# AI Features Setup Guide

This document explains how to configure and use AI-powered features in socialseed-e2e.

---

## AI Commands Overview

| Command | Description | Requirements |
|---------|-------------|---------------|
| `e2e translate` | Translate natural language to test code | Local NLP (no API key needed) |
| `e2e generate-tests` | Generate test suites from code analysis | Manifest (run `e2e manifest` first) |
| `e2e plan-strategy` | Create AI-driven test strategy | AI configuration |
| `e2e debug-execution` | Debug failed tests with AI | Execution ID from previous run |
| `e2e autonomous-run` | Run tests with AI orchestration | Strategy ID |
| `e2e security-test` | Run AI security fuzzing | Services configured |
| `e2e semantic-analyze` | Detect logic drift | gRPC server running |
| `e2e regression` | AI regression analysis | Git repository |

---

## Quick Setup

### 1. Generate Project Manifest

Most AI commands require a project manifest:

```bash
# Generate manifest for your project
e2e manifest

# Check manifest status
e2e manifest-query
```

### 2. Verify Configuration

Check if your environment is ready for AI features:

```bash
e2e doctor
```

### 3. Run AI Commands

```bash
# Generate tests
e2e generate-tests

# Create test strategy
e2e plan-strategy --name "My Strategy"

# Debug a failed execution
e2e run --report json  # First, run tests with report
# Then use the execution ID from the report
e2e debug-execution --execution-id <id>
```

---

## Common Issues and Solutions

### Issue: "No manifest found"

**Solution:**
```bash
e2e manifest
```

### Issue: "No execution IDs available"

**Solution:**
Run tests with reporting enabled to generate execution records:
```bash
e2e run --report json
```

### Issue: "Strategy ID required"

**Solution:**
First create a strategy:
```bash
e2e plan-strategy --name "My Test Strategy"
```
Then use the generated strategy ID.

### Issue: "Semantic analyzer server not running"

**Solution:**
Start the semantic analyzer:
```bash
e2e semantic-analyze server
```

---

## Environment Variables

Some AI features may require environment variables:

```bash
# Optional: For advanced NLP features
export OPENAI_API_KEY=sk-...

# Optional: For cloud-based semantic analysis
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Verbose Mode

For more details on what's happening:
```bash
e2e <command> --verbose
e2e <command> -v
```

---

## Getting Help

- Run `e2e <command> --help` for specific command help
- Run `e2e doctor` to check your setup
- Check the main README.md for general documentation
