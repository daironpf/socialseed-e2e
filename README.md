# 🌱 socialseed-e2e

[![PyPI](https://img.shields.io/pypi/v/socialseed-e2e)](https://pypi.org/project/socialseed-e2e/)
[![Python](https://img.shields.io/pypi/pyversions/socialseed-e2e)](https://pypi.org/project/socialseed-e2e/)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://daironpf.github.io/socialseed-e2e/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/socialseed-e2e)](https://pypi.org/project/socialseed-e2e/)

> **The ultimate E2E testing framework for REST APIs - Built for developers and AI agents**

**One-liner:** Test your REST APIs with 10x less code using intelligent scaffolding, automatic test discovery, and stateful test chaining. Perfect for both manual testing and AI-generated test suites.

📚 **[Full Documentation](https://daironpf.github.io/socialseed-e2e/)**

---

## 🚀 Get Started in 30 Seconds

```bash
pip install socialseed-e2e
playwright install chromium

e2e init my-tests && cd my-tests
e2e new-service users-api
e2e new-test login --service users-api
e2e run
```

---

## 🤖 Built for AI Agents (Recommended)

**This framework was designed from the ground up for AI agents.**

While you can write tests manually, the true power comes from letting AI do the work:

```bash
# 1. Initialize
e2e init

# 2. Tell your AI agent:
# "Read the .agent/ folder and generate tests for my API"

# 3. The AI automatically:
# - Scans your API code
# - Generates complete test suites
# - Uses semantic search to understand your endpoints
# - Creates stateful test chains
```

**AI Features:**
- Auto-generates `project_knowledge.json` from your codebase
- Vector embeddings for semantic search over your API
- RAG-ready retrieval for context-aware test generation
- Structured protocols that AI agents understand

**Don't have an AI agent?** You can write tests manually too—it's still 10x faster than traditional frameworks.

---

## ✨ What You Get

- **CLI scaffolding** - `e2e new-service` and `e2e new-test` commands
- **Auto-discovery** - Tests run in order automatically
- **Stateful chaining** - Share data between tests
- **Built-in mocking** - Test without external dependencies
- **AI Manifest** - Auto-generate API knowledge from code
- **Vector search** - Semantic search over your API (RAG-ready)

---

## 📝 Example Test

```python
# services/users-api/modules/01_login.py

async def run(page):
    response = await page.do_login(
        email="test@example.com",
        password="secret"
    )
    assert response.status == 200
    assert "token" in response.json()
    return response
```

---

## 🎯 CLI Commands

```bash
e2e init [dir]              # Initialize project
e2e new-service <name>      # Create service structure
e2e new-test <name>         # Create test module
e2e run                     # Run all tests
e2e manifest                # Generate API knowledge
e2e search "auth"           # Semantic search (RAG)
e2e build-index             # Build vector index
e2e watch                   # Auto-update on changes
```

---

## 📚 Documentation

All guides at **[daironpf.github.io/socialseed-e2e](https://daironpf.github.io/socialseed-e2e/)**

- [Quick Start](https://daironpf.github.io/socialseed-e2e/quickstart.html)
- [Writing Tests](https://daironpf.github.io/socialseed-e2e/writing-tests.html)
- [CLI Reference](https://daironpf.github.io/socialseed-e2e/cli-reference.html)
- [AI Manifest](https://daironpf.github.io/socialseed-e2e/project-manifest.html)

---

## 📜 License

MIT - See [LICENSE](LICENSE)

<p align="center">
  <sub>Built with ❤️ by Dairon Pérez Frías and AI co-authors</sub>
</p>
