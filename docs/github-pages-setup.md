# GitHub Pages Configuration Guide

This document explains how to configure GitHub Pages for the socialseed-e2e documentation.

## Overview

Documentation is automatically built and deployed using GitHub Actions when:
- Changes are pushed to the `main` branch affecting the `docs/` directory
- Pull requests are opened against `main` with documentation changes
- Manually triggered via `workflow_dispatch`

## Configuration Steps

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under "Source", select **GitHub Actions**
4. Click **Save**

### 2. Verify Workflow File

The workflow file `.github/workflows/docs.yml` is already configured to:
- Build documentation with Sphinx
- Deploy to GitHub Pages using the official `actions/deploy-pages` action
- Run on Python 3.11
- Cache pip dependencies for faster builds

### 3. Required Permissions

The workflow uses the following permissions:
```yaml
permissions:
  pages: write
  id-token: write
```

These are automatically granted when using the `actions/deploy-pages` action.

### 4. Environment Configuration

The workflow creates a deployment environment called `github-pages`. You can view deployment status in:
- The **Actions** tab of your repository
- The **Environments** section in repository settings

## Workflow Triggers

The documentation workflow runs on:

1. **Push to main**: When files in `docs/`, `.github/workflows/docs.yml`, or `src/**/*.py` change
2. **Pull Requests**: To validate documentation builds before merging
3. **Manual trigger**: Via GitHub UI (Actions → Documentation → Run workflow)

## Build Process

The workflow performs these steps:

1. **Checkout**: Gets the repository code with full history
2. **Setup Python**: Installs Python 3.11 with pip caching
3. **Install Dependencies**: Installs package with docs extras
4. **Build Docs**: Runs `make html` in the docs directory
5. **Check Links**: Validates all documentation links (optional, non-blocking)
6. **Upload Artifact**: Stores the built HTML for deployment
7. **Deploy**: Publishes to GitHub Pages

## Local Testing

To test documentation builds locally:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build documentation
cd docs
make html

# View the built documentation
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
```

## Troubleshooting

### Build Failures

Check the Actions tab for detailed logs. Common issues:
- Missing Python dependencies → Ensure `pyproject.toml` has all docs dependencies
- Sphinx configuration errors → Check `docs/conf.py`
- Broken links → Review `docs/_build/linkcheck/output.txt`

### Deployment Issues

If deployment fails:
1. Verify GitHub Pages is enabled (Settings → Pages → Source: GitHub Actions)
2. Check that the workflow has the required permissions
3. Ensure the artifact is being created successfully in the build job

## URL Structure

Once deployed, documentation will be available at:
```
https://daironpf.github.io/socialseed-e2e/
```

## Alternative: Branch-based Deployment

If you prefer deploying from a branch instead of GitHub Actions:

1. Change workflow to push to `gh-pages` branch:
   ```yaml
   - name: Deploy
     uses: peaceiris/actions-gh-pages@v3
     with:
       github_token: ${{ secrets.GITHUB_TOKEN }}
       publish_dir: ./docs/_build/html
   ```

2. Set GitHub Pages source to `gh-pages` branch

## See Also

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
