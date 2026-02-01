# Installation Guide

Complete guide for installing and setting up socialseed-e2e on your system.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Install](#quick-install)
- [Step-by-Step Installation](#step-by-step-installation)
- [Virtual Environment Setup](#virtual-environment-setup)
- [Development Installation](#development-installation)
- [Playwright Browser Installation](#playwright-browser-installation)
- [Verification](#verification)
- [Platform-Specific Notes](#platform-specific-notes)
- [Troubleshooting](#troubleshooting)
- [Common Issues](#common-issues)
- [Next Steps](#next-steps)

## System Requirements

### Minimum Requirements

- **Python**: 3.9 or higher (3.9, 3.10, 3.11, 3.12 supported)
- **pip**: 21.0 or higher
- **Operating System**: 
  - Linux (Ubuntu 20.04+, CentOS 8+, Debian 10+)
  - macOS (10.15 Catalina or higher)
  - Windows (Windows 10 or higher)
- **Memory**: 2 GB RAM minimum (4 GB recommended)
- **Disk Space**: 500 MB for installation + 200 MB for Playwright browsers

### Optional Requirements

- **Git**: For development installation
- **Virtual Environment Tool**: `venv` (included in Python 3.3+) or `virtualenv`
- **Node.js**: 16+ (required for some Playwright features)

### Check Your Python Version

```bash
python --version
# or
python3 --version
```

Expected output: `Python 3.9.x` or higher

If you don't have Python 3.9+, download it from [python.org](https://www.python.org/downloads/).

## Quick Install

For experienced users who want to get started immediately:

```bash
# Install the package
pip install socialseed-e2e

# Install Playwright browsers
playwright install chromium

# Verify installation
e2e doctor
```

## Step-by-Step Installation

### 1. Create a Virtual Environment (Recommended)

Using a virtual environment keeps your project dependencies isolated.

#### Linux/macOS

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

#### Windows

```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment (Command Prompt)
venv\Scripts\activate.bat

# Or PowerShell
venv\Scripts\Activate.ps1
```

### 2. Install socialseed-e2e

With your virtual environment activated:

```bash
pip install socialseed-e2e
```

This will install:
- socialseed-e2e framework
- Playwright for HTTP testing
- Pydantic for data validation
- PyYAML for configuration
- Rich for terminal output
- Click for CLI
- All other dependencies

### 3. Install Playwright Browsers

Playwright requires browser binaries to perform HTTP testing:

```bash
# Install Chromium (recommended, smaller footprint)
playwright install chromium

# Or install all browsers (Chromium, Firefox, WebKit)
playwright install
```

**Download Size:**
- Chromium only: ~150 MB
- All browsers: ~400 MB

**Installation Time:** 1-3 minutes depending on your connection

### 4. Verify Installation

Run the built-in doctor command to check your setup:

```bash
e2e doctor
```

Expected output:
```
🔍 Running system checks...

✓ Python version: 3.12.0
✓ socialseed-e2e: 0.1.0
✓ Playwright: 1.40.0
✓ Chromium browser: Installed
✓ Configuration: Ready

🎉 All checks passed! Your system is ready.
```

## Virtual Environment Setup

### Why Use Virtual Environments?

- **Isolation**: Dependencies don't conflict with other projects
- **Reproducibility**: Easy to recreate the same environment
- **Clean System**: No global package pollution
- **Version Control**: `requirements.txt` or `pyproject.toml` tracks dependencies

### Creating Virtual Environments

#### Using venv (Built-in)

```bash
# Create
python -m venv myproject-env

# Activate
source myproject-env/bin/activate  # Linux/macOS
myproject-env\Scripts\activate     # Windows

# Deactivate
deactivate
```

#### Using virtualenv

```bash
# Install virtualenv
pip install virtualenv

# Create
virtualenv myproject-env

# Activate
source myproject-env/bin/activate  # Linux/macOS
myproject-env\Scripts\activate     # Windows
```

#### Using conda

```bash
# Create
conda create -n socialseed-e2e python=3.11

# Activate
conda activate socialseed-e2e

# Install package
pip install socialseed-e2e
```

### Best Practices

1. **Name your environment**: Use descriptive names like `my-api-tests`
2. **Add to .gitignore**: Don't commit virtual environment folders
3. **Document dependencies**: Keep a `requirements.txt` or use `pyproject.toml`
4. **Pin versions**: Specify versions for reproducibility

## Development Installation

If you want to contribute to socialseed-e2e or modify the source code:

### 1. Clone the Repository

```bash
git clone https://github.com/daironpf/socialseed-e2e.git
cd socialseed-e2e
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 3. Install in Editable Mode

```bash
pip install -e ".[dev]"
```

This installs:
- Package in editable mode (changes reflect immediately)
- Development dependencies (pytest, black, flake8, mypy, etc.)
- All runtime dependencies

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

### 5. Run Tests

```bash
pytest
```

### 6. Verify Development Setup

```bash
e2e doctor
e2e --version
```

## Playwright Browser Installation

Playwright browsers are essential for HTTP testing. Here's how to manage them:

### Install Specific Browsers

```bash
# Chromium only (recommended for API testing)
playwright install chromium

# Firefox
playwright install firefox

# WebKit
playwright install webkit

# All browsers
playwright install
```

### Update Browsers

```bash
# Update all installed browsers to latest versions
playwright install --with-deps chromium
```

### Uninstall Browsers

```bash
# Remove all browsers
playwright uninstall

# Remove specific browser
playwright uninstall chromium
```

### Check Browser Versions

```bash
# List installed browsers
playwright show-browsers
```

### System Dependencies

Playwright may require system dependencies on Linux:

#### Ubuntu/Debian

```bash
playwright install-deps chromium
```

Or manually:

```bash
sudo apt-get update
sudo apt-get install -y libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2
```

#### CentOS/RHEL/Fedora

```bash
sudo yum install -y alsa-lib \
    atk \
    cups-libs \
    dbus-libs \
    expat \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXtst \
    libdrm \
    libxcb \
    libxkbcommon \
    mesa-libgbm \
    nss \
    pango
```

## Verification

### Using e2e doctor

The `e2e doctor` command checks your entire setup:

```bash
e2e doctor
```

Checks performed:
- Python version compatibility
- socialseed-e2e installation
- Playwright installation
- Browser binaries
- CLI functionality

### Manual Verification

```bash
# Check Python version
python --version

# Check package installation
pip show socialseed-e2e

# Check Playwright
playwright --version

# Check CLI
which e2e
e2e --help

# Test basic functionality
e2e init test-project
cd test-project
e2e config
```

### Expected Output

```
$ python --version
Python 3.12.0

$ pip show socialseed-e2e
Name: socialseed-e2e
Version: 0.1.0
Summary: Framework E2E para testing de APIs REST con Playwright
...

$ playwright --version
Version 1.40.0

$ e2e doctor
🔍 Running system checks...
✓ Python version: 3.12.0
✓ socialseed-e2e: 0.1.0
✓ Playwright: 1.40.0
✓ Chromium browser: Installed
✓ Configuration: Ready
🎉 All checks passed! Your system is ready.
```

## Platform-Specific Notes

### Linux

#### Ubuntu/Debian

```bash
# Install system dependencies for Playwright
sudo apt-get update
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libxcomposite1

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install socialseed-e2e
playwright install chromium
```

#### CentOS/RHEL/Fedora

```bash
# Install system dependencies
sudo yum install -y atk cups-libs libXcomposite libXcursor

# Install Python 3.9+ if not available
sudo yum install -y python39 python39-pip

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install
pip install socialseed-e2e
playwright install chromium
```

### macOS

#### Using Homebrew

```bash
# Install Python if needed
brew install python@3.11

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install socialseed-e2e
playwright install chromium
```

#### Manual Installation

```bash
# Download Python from python.org
# Install normally

# Open Terminal
python3 -m venv venv
source venv/bin/activate
pip install socialseed-e2e
playwright install chromium
```

### Windows

#### Using Command Prompt

```cmd
:: Create virtual environment
python -m venv venv

:: Activate
venv\Scripts\activate.bat

:: Install
pip install socialseed-e2e
playwright install chromium
```

#### Using PowerShell

```powershell
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\Activate.ps1

# Install
pip install socialseed-e2e
playwright install chromium
```

#### Windows-Specific Issues

If you see execution policy errors in PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Troubleshooting

### Installation Failures

#### Permission Denied

**Problem**: `Permission denied` when installing

**Solution 1**: Use `--user` flag
```bash
pip install --user socialseed-e2e
```

**Solution 2**: Use virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate
pip install socialseed-e2e
```

**Solution 3**: Use sudo (not recommended)
```bash
sudo pip install socialseed-e2e  # Linux/macOS only
```

#### Network Issues

**Problem**: `Connection timeout` or `SSL certificate verify failed`

**Solution 1**: Use trusted host
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org socialseed-e2e
```

**Solution 2**: Configure proxy
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
pip install socialseed-e2e
```

**Solution 3**: Use mirror (China users)
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple socialseed-e2e
```

### Playwright Issues

#### Browser Installation Fails

**Problem**: `playwright install` fails with download errors

**Solution 1**: Check internet connection
```bash
ping playwright.azureedge.net
```

**Solution 2**: Set download host (China users)
```bash
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

**Solution 3**: Manual download
```bash
# Download browser manually and place in correct location
# Location: ~/.cache/ms-playwright/ on Linux/macOS
# Location: %USERPROFILE%\AppData\Local\ms-playwright\ on Windows
```

#### Missing System Dependencies

**Problem**: Chromium fails to launch with missing library errors

**Solution**: Install system dependencies
```bash
# Ubuntu/Debian
sudo apt-get install -y libnss3 libatk-bridge2.0-0 libxcomposite1 libxdamage1

# Or use Playwright's automatic installer
playwright install-deps chromium
```

### Python Version Issues

#### Python Not Found

**Problem**: `python: command not found`

**Solution 1**: Use python3
```bash
python3 -m pip install socialseed-e2e
```

**Solution 2**: Create alias
```bash
alias python=python3
python -m pip install socialseed-e2e
```

#### Wrong Python Version

**Problem**: Package requires Python 3.9+, you have 3.8

**Solution**: Install Python 3.9+
```bash
# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv python3.11-pip

# macOS
brew install python@3.11

# Windows
# Download from python.org
```

### Virtual Environment Issues

#### Cannot Activate

**Problem**: `source venv/bin/activate` doesn't work

**Solution 1**: Check if venv exists
```bash
ls -la venv/bin/activate
```

**Solution 2**: Use absolute path
```bash
source /full/path/to/venv/bin/activate
```

**Solution 3**: Check permissions
```bash
chmod +x venv/bin/activate
```

#### Wrong Python in venv

**Problem**: Virtual environment uses system Python

**Solution**: Recreate with correct Python
```bash
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
```

## Common Issues

### ImportError: No module named 'socialseed_e2e'

**Cause**: Package not installed or installed in wrong environment

**Solution**:
```bash
# Check which Python you're using
which python

# Check if package is installed
pip list | grep socialseed

# Install in current environment
pip install socialseed-e2e
```

### e2e command not found

**Cause**: CLI not in PATH

**Solution 1**: Activate virtual environment
```bash
source venv/bin/activate
```

**Solution 2**: Use full path
```bash
/path/to/venv/bin/e2e
```

**Solution 3**: Reinstall with --force-reinstall
```bash
pip install --force-reinstall socialseed-e2e
```

### Playwright browser not found

**Cause**: Browsers not installed or wrong location

**Solution**:
```bash
# Reinstall browsers
playwright uninstall
playwright install chromium

# Check location
playwright show-browsers

# Verify e2e doctor output
e2e doctor
```

### SSL Certificate Errors

**Cause**: Outdated certificates or corporate proxy

**Solution 1**: Update certificates
```bash
# macOS
brew install ca-certificates

# Ubuntu/Debian
sudo update-ca-certificates
```

**Solution 2**: Disable SSL verification (temporary, not recommended for production)
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org socialseed-e2e
```

### ModuleNotFoundError on Import

**Cause**: Missing dependencies or circular import

**Solution**:
```bash
# Reinstall with all dependencies
pip install --force-reinstall --no-cache-dir socialseed-e2e

# Or in development mode
git clone https://github.com/daironpf/socialseed-e2e.git
cd socialseed-e2e
pip install -e ".[dev]"
```

### Tests Fail After Installation

**Cause**: Incomplete setup or missing browsers

**Solution**:
```bash
# Full reinstall
pip uninstall socialseed-e2e -y
pip cache purge
pip install socialseed-e2e
playwright install chromium

# Verify
e2e doctor
pytest --version
```

## Next Steps

After successful installation:

1. **[Quick Start Guide](quickstart.md)** - Create your first test in 5 minutes
2. **[Configuration](configuration.md)** - Learn about e2e.conf options
3. **[Writing Tests](writing-tests.md)** - Test writing patterns and best practices
4. **[CLI Reference](cli-reference.md)** - Complete CLI command reference

### Quick Test

```bash
# Initialize a test project
e2e init my-first-test
cd my-first-test

# Check configuration
e2e config

# Run tests (if you have any)
e2e run
```

### Getting Help

- **Documentation**: [Full Documentation](https://github.com/daironpf/socialseed-e2e/tree/main/docs)
- **Issues**: [GitHub Issues](https://github.com/daironpf/socialseed-e2e/issues)
- **Discussions**: [GitHub Discussions](https://github.com/daironpf/socialseed-e2e/discussions)

---

**Still having issues?** 

Run `e2e doctor` and share the output when [opening an issue](https://github.com/daironpf/socialseed-e2e/issues/new).
