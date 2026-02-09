# AI Regression Agents for Differential Testing (Issue #84)

## Overview

The **AI Regression Agent** provides intelligent differential testing by analyzing git diffs, determining impact on existing tests, and executing only the tests affected by code changes. This provides instant feedback to developers during the development cycle.

## Features

### 🔍 Git Integration
- Analyzes git diffs between any two references (commits, branches, tags)
- Identifies modified functions, classes, controllers, and models
- Extracts changed endpoints and API routes
- Tracks line-by-line changes

### 🎯 Impact Analysis
- Determines which services are affected by changes
- Identifies affected endpoints and API routes
- Maps changes to existing test cases
- Recommends new tests for new functionality
- Calculates risk level (low, medium, high, critical)

### ⚡ Targeted Execution
- Runs only tests related to changes
- Skips unaffected tests for faster feedback
- Parallel execution support
- Integration with CI/CD pipelines

## Usage

### Quick Start

```bash
# Analyze last commit
e2e regression

# Compare against main branch
e2e regression --base-ref main

# Analyze and run affected tests
e2e regression --run-tests

# Compare specific tags
e2e regression -b v1.0 -t v2.0

# Custom output report
e2e regression --output my-report.md
```

### CLI Options

```bash
e2e regression [DIRECTORY] [OPTIONS]
```

**Arguments:**
- `DIRECTORY`: Project directory (default: current directory)

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--base-ref` | `-b` | Base git reference | `HEAD~1` |
| `--target-ref` | `-t` | Target git reference | `HEAD` |
| `--run-tests` | | Execute affected tests | `False` |
| `--output` | `-o` | Report filename | `REGRESSION_REPORT.md` |

## How It Works

### 1. Git Diff Analysis

```python
from socialseed_e2e.project_manifest import GitDiffAnalyzer

analyzer = GitDiffAnalyzer("/path/to/project")

# Get changed files
changed_files = analyzer.get_changed_files("HEAD~1", "HEAD")

# Analyze changes in detail
changes = analyzer.analyze_changes("main", "feature-branch")

for change in changes:
    print(f"File: {change.file_path}")
    print(f"Type: {change.change_type}")
    print(f"Function: {change.function_name}")
    print(f"Lines: +{change.lines_added}/-{change.lines_deleted}")
```

### 2. Impact Analysis

```python
from socialseed_e2e.project_manifest import ImpactAnalyzer

analyzer = ImpactAnalyzer(project_root, manifest)
impact = analyzer.analyze_impact(changes)

print(f"Affected services: {impact.affected_services}")
print(f"Affected endpoints: {impact.affected_endpoints}")
print(f"Tests to run: {impact.affected_tests}")
print(f"Risk level: {impact.risk_level}")
```

### 3. Targeted Test Execution

```python
from socialseed_e2e.project_manifest import RegressionAgent

agent = RegressionAgent("/path/to/project", "HEAD~1", "HEAD")
impact = agent.run_analysis()

# Get tests to run by service
tests_by_service = agent.get_tests_to_run(impact)

for service, tests in tests_by_service.items():
    print(f"Service: {service}")
    print(f"Tests: {tests}")
```

## Example Output

```
🤖 AI Regression Agent
   Project: /home/user/my-api
   Comparing: HEAD~1 → HEAD

📊 Analysis Complete

   Files changed: 3
   Services affected: 2
   Endpoints affected: 1
   Tests to run: 5
   Risk level: MEDIUM

📝 Changed Files:
   ~ UserController.java (45+/12-)
   ~ UserService.java (23+/5-)
   + UserRepository.java (67+/0-)

🎯 Affected Services:
   • users-service
   • auth-service

🧪 Tests to Execute:
   users-service:
     - *UserController*
     - *createUser*
     - *updateUser*
     ... and 2 more

✨ New Tests Recommended:
   • Test for new function: findByEmail
   • Test for new endpoint: /users/search

📝 Generating report...
   ✓ Report saved: .e2e/REGRESSION_REPORT.md

============================================================
🤖 Regression Analysis Complete
============================================================

   ✅ Analysis complete - 5 tests identified

   Tip: Use --run-tests to execute affected tests automatically
```

## Report Format

### Executive Summary

```markdown
# 🤖 AI Regression Analysis Report

**Base Reference:** `HEAD~1`
**Target Reference:** `HEAD`
**Risk Level:** MEDIUM

---

## 📊 Summary

- **Files Changed:** 3
- **Services Affected:** 2
- **Endpoints Affected:** 1
- **Tests to Run:** 5
- **New Tests Needed:** 2
```

### Changed Files

```markdown
## 📝 Changed Files

### UserController.java
- **Type:** modified
- **Lines:** +45/-12
- **Function:** `createUser`
- **Class:** `UserController`
- **Endpoints:** /api/users

### UserService.java
- **Type:** modified
- **Lines:** +23/-5
- **Function:** `validateEmail`
```

### Affected Services

```markdown
## 🎯 Affected Services

- users-service
- auth-service
```

### Tests to Execute

```markdown
## 🧪 Tests to Execute

Run these tests to verify the changes:

```bash
e2e run --service users-service
e2e run --service auth-service
```
```

### New Tests Recommended

```markdown
## ✨ New Tests Recommended

- [ ] Test for new function: findByEmail
- [ ] Test for new endpoint: /users/search
```

## Risk Levels

The AI Regression Agent calculates risk based on:

| Risk Level | Criteria | Action Required |
|------------|----------|----------------|
| **Critical** | >2 services OR >500 lines | Full regression testing |
| **High** | >1 service OR >200 lines | Careful review + targeted tests |
| **Medium** | >50 lines OR deletions | Standard targeted testing |
| **Low** | Simple changes | Quick targeted tests |

## CI/CD Integration

### GitHub Actions

```yaml
name: Regression Tests

on:
  pull_request:
    branches: [ main ]

jobs:
  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Need full history for diff

      - name: Install socialseed-e2e
        run: pip install socialseed-e2e

      - name: Analyze Changes
        run: e2e regression --base-ref origin/main --target-ref HEAD

      - name: Run Affected Tests
        run: e2e regression --base-ref origin/main --target-ref HEAD --run-tests
```

### GitLab CI

```yaml
regression_tests:
  script:
    - pip install socialseed-e2e
    - e2e regression --base-ref $CI_MERGE_REQUEST_TARGET_BRANCH_NAME --run-tests
  only:
    - merge_requests
```

## Programmatic Usage

### Basic Usage

```python
from socialseed_e2e.project_manifest import run_regression_analysis

impact, report = run_regression_analysis(
    project_root="/path/to/project",
    base_ref="main",
    target_ref="feature-branch"
)

print(f"Found {len(impact.affected_tests)} tests to run")
print(f"Risk level: {impact.risk_level}")
```

### Advanced Usage

```python
from socialseed_e2e.project_manifest import (
    RegressionAgent,
    GitDiffAnalyzer,
    ImpactAnalyzer,
)

# Create agent
agent = RegressionAgent(
    project_root="/path/to/project",
    base_ref="v1.0",
    target_ref="v2.0"
)

# Run analysis
impact = agent.run_analysis()

# Access detailed information
for change in impact.changed_files:
    print(f"Changed: {change.file_path}")
    print(f"  Function: {change.function_name}")
    print(f"  Lines: +{change.lines_added}/-{change.lines_deleted}")

# Get tests to run
tests_by_service = agent.get_tests_to_run(impact)
for service, tests in tests_by_service.items():
    print(f"{service}: {len(tests)} tests")

# Generate report
report = agent.generate_report(impact)
with open("regression-report.md", "w") as f:
    f.write(report)
```

### Custom Analysis

```python
from socialseed_e2e.project_manifest import GitDiffAnalyzer

analyzer = GitDiffAnalyzer("/path/to/project")

# Get specific file diff
diff = analyzer.get_detailed_diff(
    file_path=Path("src/controllers/UserController.java"),
    base_ref="HEAD~1",
    target_ref="HEAD"
)

# Parse the diff
change = analyzer._parse_diff(
    file_path=Path("src/controllers/UserController.java"),
    diff_content=diff
)

print(f"Function changed: {change.function_name}")
print(f"Endpoints affected: {change.affected_endpoints}")
```

## Best Practices

### 1. Run on Every PR

```bash
# In your pre-commit or CI

e2e regression --base-ref main --run-tests
```

### 2. Compare Before Merge

```bash
# Before merging feature branch
e2e regression -b main -t feature-branch --run-tests
```

### 3. Review Reports

Always review the regression report before merging:

```bash
e2e regression
cat .e2e/REGRESSION_REPORT.md
```

### 4. Address New Test Recommendations

The agent identifies new tests needed. Create them before merging:

```bash
e2e regression
# Review "New Tests Recommended" section
# Create missing tests
e2e new-test <test-name> --service <service>
```

## Supported Languages

The GitDiffAnalyzer supports extracting code elements from:

- **Python** (.py) - Functions, classes
- **Java** (.java) - Methods, classes, Spring endpoints
- **JavaScript/TypeScript** (.js, .ts) - Functions, classes, Express endpoints
- **Go** (.go) - Functions
- **Ruby** (.rb) - Methods, classes
- **PHP** (.php) - Functions, classes

## Troubleshooting

### "No changes detected"

Ensure you're in a git repository and the references exist:

```bash
# Verify refs exist
git log --oneline HEAD~5..HEAD

# Run with explicit refs
e2e regression -b main -t HEAD
```

### "No project manifest found"

Run `e2e manifest` first to create the project knowledge base:

```bash
e2e manifest
e2e regression
```

### Git not found

Ensure git is installed and in your PATH:

```bash
which git
git --version
```

## API Reference

### RegressionAgent

```python
class RegressionAgent:
    def __init__(self, project_root: Path, base_ref: str, target_ref: str)
    def load_manifest(self) -> Optional[ProjectKnowledge]
    def run_analysis(self) -> ImpactAnalysis
    def get_tests_to_run(self, impact: ImpactAnalysis) -> Dict[str, List[str]]
    def generate_report(self, impact: ImpactAnalysis) -> str
```

### GitDiffAnalyzer

```python
class GitDiffAnalyzer:
    def __init__(self, project_root: Path)
    def get_changed_files(self, base_ref: str, target_ref: str) -> List[Path]
    def get_detailed_diff(self, file_path: Path, base_ref: str, target_ref: str) -> str
    def analyze_changes(self, base_ref: str, target_ref: str) -> List[CodeChange]
```

### ImpactAnalyzer

```python
class ImpactAnalyzer:
    def __init__(self, project_root: Path, manifest: ProjectKnowledge)
    def analyze_impact(self, changes: List[CodeChange]) -> ImpactAnalysis
```

## Comparison with Other Commands

| Command | Purpose | Use Case |
|---------|---------|----------|
| `e2e run` | Run all tests | Full regression suite |
| `e2e run --service X` | Run service tests | Testing specific service |
| `e2e regression` | **Analyze + targeted tests** | **PR validation, CI/CD** |
| `e2e security-test` | Security testing | Security audits |

## Future Enhancements

Planned improvements for Issue #84:

- [ ] ML-based test selection (predict which tests will fail)
- [ ] Historical failure correlation
- [ ] Automatic test generation for new code
- [ ] Parallel test execution
- [ ] Integration with test impact analysis tools
- [ ] Visual diff reporting

## See Also

- [Autonomous Test Generation](autonomous-test-generation-guide.md)
- [AI Discovery Report](ai-discovery-report.md)
- [Security Fuzzing](security-fuzzing.md)
