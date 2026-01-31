# Quick Start Guide

Get started with socialseed-e2e in 15 minutes!

## Step 1: Initialize Your Project

```bash
e2e init
```

This creates:
- `e2e.conf` - Configuration file
- `services/` - Directory for service tests
- `tests/` - Directory for test modules

## Step 2: Configure Your API

Edit `e2e.conf`:

```yaml
general:
  environment: dev
  timeout: 30000

services:
  myapi:
    name: my-api
    base_url: http://localhost:8080
    health_endpoint: /health
```

## Step 3: Create a Service

```bash
e2e new-service myapi
```

## Step 4: Create a Test

```bash
e2e new-test login --service myapi
```

## Step 5: Run Tests

```bash
e2e run
```

That's it! See [Writing Tests](writing-tests.md) for more details.
