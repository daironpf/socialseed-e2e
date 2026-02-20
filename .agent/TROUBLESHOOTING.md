# Troubleshooting Guide for AI Agents

This guide helps AI agents diagnose and resolve common issues when working with socialseed-e2e.

---

## Quick Diagnosis

Run this command to check the framework health:
```bash
e2e doctor
```

---

## Common Issues

### Issue: Command not found

**Problem:** `e2e: command not found`

**Solution:**
```bash
# Reinstall the package
pip install -e .

# Or use python module directly
python -m socialseed_e2e --help
```

---

### Issue: Tests fail with "No services configured"

**Problem:** `e2e run` returns empty results or error

**Solution:**
1. Check `e2e.conf` exists in project root
2. Verify services are defined:
```yaml
services:
  my_api:
    base_url: http://localhost:8080
    endpoints:
      - /api/users
```

---

### Issue: manifest-check fails

**Problem:** Cannot find manifest for service

**Solution:**
```bash
# Generate manifest first
e2e manifest ../services/my-service

# Then check
e2e manifest-check my-service
```

---

### Issue: Import errors with Playwright

**Problem:** `ModuleNotFoundError: No module named 'playwright'`

**Solution:**
```bash
pip install playwright
playwright install chromium
```

---

### Issue: Permission denied on test execution

**Problem:** Cannot run tests

**Solution:**
```bash
chmod +x <test_file>.py
# Or run with python
python <test_file>.py
```

---

### Issue: Timeout errors

**Problem:** Tests hang or timeout

**Solution:**
Add timeout configuration:
```yaml
services:
  my_api:
    base_url: http://localhost:8080
    timeout: 30  # seconds
```

---

### Issue: gRPC commands fail

**Problem:** `grpcio` module not found

**Solution:**
```bash
pip install socialseed-e2e[grpc]
```

---

### Issue: RAG/search commands fail

**Problem:** Semantic search not working

**Solution:**
```bash
pip install socialseed-e2e[rag]

# Build index
e2e build-index
```

---

## Debug Mode

Use verbose mode for detailed output:
```bash
e2e run --verbose
e2e --verbose doctor
```

---

## Getting Help

1. Run `e2e doctor` for health check
2. Check `e2e config` for configuration
3. Review logs in `.e2e/logs/`
