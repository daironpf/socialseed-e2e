# Installation Guide

## Requirements

- Python 3.9 or higher
- pip

## Installing with pip

```bash
pip install socialseed-e2e
```

## Installing Playwright Browsers

After installing the package, you need to install Playwright browsers:

```bash
playwright install chromium
```

## Verifying Installation

Run the doctor command to verify everything is set up correctly:

```bash
e2e doctor
```

## Development Installation

For development, install in editable mode:

```bash
git clone https://github.com/daironpf/socialseed-e2e.git
cd socialseed-e2e
pip install -e ".[dev]"
playwright install chromium
```

## Troubleshooting

### Common Issues

1. **Playwright not found**: Make sure to run `playwright install chromium`
2. **Permission errors**: Use `pip install --user` or a virtual environment
3. **Import errors**: Verify Python version is 3.9+
