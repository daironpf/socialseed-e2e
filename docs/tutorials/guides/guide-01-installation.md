# Guide 1: Installation

> ⏱️ **Time:** 5 minutes | **Difficulty:** ⭐ Easy

Welcome! This guide will help you install SocialSeed-E2E and get it running.

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.8 or higher
- ✅ pip (Python package installer)
- ✅ Git (for cloning examples)

## Step 1: Install via pip

The easiest way to install SocialSeed-E2E is through pip:

```bash
pip install socialseed-e2e
```

<details>
<summary>💡 Alternative: Install from source</summary>

If you want the latest development version:

```bash
git clone https://github.com/daironpf/socialseed-e2e.git
cd socialseed-e2e
pip install -e .
```
</details>

## Step 2: Verify Installation

Let's verify that the installation was successful:

```bash
# Check version
e2e --version

# Expected output:
# socialseed-e2e version 0.1.3
```

## Step 3: Run Doctor

The built-in doctor command checks your installation:

```bash
e2e doctor
```

You should see something like:

```
🔍 Running E2E Doctor...

✓ Python version: 3.9.7
✓ Playwright: Installed
✓ Configuration: Valid
✓ Services: Ready

✅ All checks passed!
```

## Step 4: Initialize a Test Project

Create your first test project:

```bash
# Create a new directory
mkdir my-first-tests
cd my-first-tests

# Initialize the project
e2e init
```

This will create:

```
my-first-tests/
├── e2e.conf          # Main configuration file
├── services/         # Service test modules
│   └── __init__.py
└── reports/          # Test reports directory
```

## Step 5: Explore the CLI

Let's explore the available commands:

```bash
# Show help
e2e --help

# Show specific command help
e2e init --help
e2e run --help
```

## 🎯 Quick Test

Let's make sure everything works:

```bash
# Create a simple test service
e2e new-service demo-api

# Check what was created
ls -la services/demo-api/
```

You should see:

```
services/demo-api/
├── __init__.py
├── demo_api_page.py
├── data_schema.py
└── modules/
    └── __init__.py
```

## ✅ Success!

You've successfully installed SocialSeed-E2E! 🎉

### What You Learned

- ✅ How to install the framework
- ✅ How to verify the installation
- ✅ How to initialize a project
- ✅ How to create a new service

### Next Steps

→ Continue to [Guide 2: First Test Project](guide-02-first-project.md)

---

## Troubleshooting

<details>
<summary>❌ "Command not found: e2e"</summary>

**Solution:** The script directory is not in your PATH.

```bash
# Find where pip installs scripts
pip show socialseed-e2e

# Or use Python module syntax
python -m socialseed_e2e --version
```
</details>

<details>
<summary>❌ "ImportError: No module named 'socialseed_e2e'"</summary>

**Solution:** The package isn't installed in your current Python environment.

```bash
# Check which Python you're using
which python

# Install in the correct environment
/path/to/your/python -m pip install socialseed-e2e
```
</details>

<details>
<summary>❌ Permission denied errors</summary>

**Solution:** Use the --user flag

```bash
pip install --user socialseed-e2e
```
</details>

---

**Need more help?** Check the [FAQ](../faq.md) or [open an issue](https://github.com/daironpf/socialseed-e2e/issues).
