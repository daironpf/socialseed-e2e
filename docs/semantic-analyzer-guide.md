# Semantic Analyzer - User Guide

Complete guide for using the Autonomous Semantic Regression & Logic Drift Detection Agent (Issue #163).

## Table of Contents

1. [Quick Start](#quick-start)
2. [For Human Developers](#for-human-developers)
3. [For AI Agents](#for-ai-agents)
4. [Understanding Drift Reports](#understanding-drift-reports)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

The semantic analyzer is included with socialseed-e2e:

```bash
pip install socialseed-e2e
```

Optional dependencies for enhanced functionality:

```bash
# For LLM-based semantic analysis
pip install openai  # or anthropic, etc.

# For database snapshots
pip install neo4j    # Neo4j graph database
pip install pymongo  # MongoDB
pip install sqlalchemy  # PostgreSQL, MySQL, SQLite
```

### Basic Usage

```bash
# Run semantic analysis on current project
e2e semantic-analyze run

# Extract intent baselines only
e2e semantic-analyze intents

# Compare specific commits
e2e semantic-analyze run -b HEAD~1 -t HEAD

# Analyze with API testing
e2e semantic-analyze run -u http://localhost:8080
```

---

## For Human Developers

### What is Semantic Analysis?

Traditional E2E tests answer: "Does the API return 200 OK?"

Semantic Analysis answers: **"Does the system behavior match the intended business logic?"**

Example scenarios it detects:
- A "follow" action that no longer creates the reciprocal relationship
- Validation rules that were accidentally bypassed
- Business logic changes that violate documented requirements
- State transitions that skip required steps

### CLI Commands

#### 1. Run Analysis

```bash
# Basic analysis
e2e semantic-analyze run

# Compare two commits
e2e semantic-analyze run -b v1.0.0 -t v1.1.0

# Include API endpoints
e2e semantic-analyze run \
  -u http://localhost:8080 \
  --baseline-commit HEAD~5 \
  --target-commit HEAD

# Include database snapshots
e2e semantic-analyze run \
  -d neo4j \
  --db-uri bolt://localhost:7687 \
  --db-user neo4j \
  --db-password password

# Skip state capture (faster)
e2e semantic-analyze run --no-state-capture
```

**Options:**
- `-u, --base-url`: API base URL for testing
- `-b, --baseline-commit`: Starting commit for comparison
- `-t, --target-commit`: Ending commit for comparison
- `-d, --database-type`: Database type (neo4j, postgresql, mongodb)
- `--db-uri`: Database connection URI
- `--db-user`: Database username
- `--db-password`: Database password
- `-o, --output`: Output directory for reports
- `--no-state-capture`: Skip state capture (intent extraction only)

#### 2. Extract Intents

View extracted intent baselines without running full analysis:

```bash
# Show all intents
e2e semantic-analyze intents

# Filter by category
e2e semantic-analyze intents -c user_management -c auth

# Output as JSON
e2e semantic-analyze intents --json-output > intents.json
```

#### 3. Start gRPC Server

For integration with CI/CD or other tools:

```bash
# Start server on default port (50051)
e2e semantic-analyze server

# Use custom port
e2e semantic-analyze server -p 50052

# Bind to specific host
e2e semantic-analyze server -h 0.0.0.0 -p 50051
```

### Python API

```python
from socialseed_e2e.agents import SemanticAnalyzerAgent

# Create agent
agent = SemanticAnalyzerAgent(
    project_root="/path/to/project",
    project_name="My API",
    base_url="http://localhost:8080",
)

# Run full analysis
report = agent.analyze(
    baseline_commit="abc123",
    target_commit="def456",
    api_endpoints=[
        {"endpoint": "/api/users", "method": "GET"},
        {"endpoint": "/api/follow", "method": "POST"},
    ],
    database_configs=[
        {"type": "neo4j", "uri": "bolt://localhost:7687"},
    ],
)

# Check for critical issues
if report.has_critical_drifts():
    print("🚨 Critical semantic drifts detected!")
    for drift in report.get_drifts_by_severity("critical"):
        print(f"  - {drift.description}")
        print(f"    Recommendation: {drift.recommendation}")

    # Exit with error code in CI/CD
    import sys
    sys.exit(1)

# Get summary
summary = report.generate_summary()
print(f"Total drifts: {summary['total_drifts']}")
print(f"Critical: {summary['severity_distribution']['critical']}")
print(f"High: {summary['severity_distribution']['high']}")
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: Semantic Regression Check

on: [pull_request]

jobs:
  semantic-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install socialseed-e2e
        run: pip install socialseed-e2e

      - name: Run Semantic Analysis
        run: |
          e2e semantic-analyze run \
            --baseline-commit ${{ github.event.pull_request.base.sha }} \
            --target-commit ${{ github.event.pull_request.head.sha }} \
            --output .e2e/reports/

      - name: Check for Critical Drifts
        run: |
          if grep -q "🚨 CRITICAL" .e2e/reports/SEMANTIC_DRIFT_REPORT_*.md; then
            echo "🚨 Critical semantic drifts detected!"
            exit 1
          fi

      - name: Upload Report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: semantic-drift-report
          path: .e2e/reports/
```

#### GitLab CI

```yaml
semantic-analysis:
  stage: test
  script:
    - pip install socialseed-e2e
    - e2e semantic-analyze run --baseline-commit $CI_MERGE_REQUEST_DIFF_BASE_SHA --target-commit $CI_COMMIT_SHA
  artifacts:
    paths:
      - .e2e/reports/
    expire_in: 1 week
  rules:
    - if: $CI_MERGE_REQUEST_IID
```

### Writing Documentation for Better Analysis

The semantic analyzer extracts intents from your documentation. Write clear documentation for better results:

```markdown
## Feature: User Following

### Description
When a user follows another user, the system should create a bidirectional
relationship in the graph database and send a notification.

### Expected Behavior
1. User A clicks "Follow" on User B's profile
2. System creates FOLLOW relationship: User A → User B
3. System creates reciprocal FOLLOW relationship: User B → User A
4. System sends notification to User B
5. System increments follower count for User B
6. System increments following count for User A

### Success Criteria
- ✅ Both FOLLOW relationships are created in Neo4j
- ✅ Notification is sent to the followed user
- ✅ Follower/following counts are updated
- ❌ Cannot follow yourself
- ❌ Cannot follow the same user twice

### API Endpoints
- `POST /api/users/{id}/follow` - Create follow relationship
- `DELETE /api/users/{id}/follow` - Remove follow relationship
- `GET /api/users/{id}/followers` - Get followers list
- `GET /api/users/{id}/following` - Get following list
```

---

## For AI Agents

### Understanding Your Role

As an AI agent, you can use the semantic analyzer to:
1. **Verify changes** - Ensure code modifications preserve business logic
2. **Detect regressions** - Find semantic drift before deployment
3. **Generate insights** - Provide actionable recommendations to developers
4. **Maintain consistency** - Validate that implementation matches documentation

### Key Concepts

#### Intent Baselines
Intent baselines represent the expected behavior extracted from:
- Documentation files (`docs/*.md`)
- GitHub issues (`issues.json`)
- Code comments and docstrings
- Test case descriptions

Each baseline includes:
- `intent_id`: Unique identifier
- `description`: Human-readable description
- `category`: Classification (user_management, payment, etc.)
- `expected_behavior`: What should happen
- `success_criteria`: Conditions that must be met

#### State Snapshots
Captures the complete system state at a point in time:
- API responses (status, body, headers, timing)
- Database state (entities, relationships, constraints)
- Commit hash and branch information

#### Logic Drift
A detected deviation from expected behavior:
- **BEHAVIORAL**: API behavior changed
- **RELATIONSHIP**: Entity relationships modified
- **STATE_TRANSITION**: Invalid state transitions
- **VALIDATION_LOGIC**: Validation rules changed
- **BUSINESS_RULE**: Core business logic violated
- **DATA_INTEGRITY**: Data consistency issues
- **SIDE_EFFECT**: Unexpected side effects
- **MISSING_FUNCTIONALITY**: Expected behavior not present

### API Reference for Agents

#### SemanticAnalyzerAgent

```python
from socialseed_e2e.agents import SemanticAnalyzerAgent

agent = SemanticAnalyzerAgent(
    project_root: Path,
    project_name: Optional[str] = None,
    base_url: Optional[str] = None,
    llm_client: Optional[Any] = None,  # For enhanced analysis
)

# Methods
report = agent.analyze(
    baseline_commit: Optional[str] = None,
    target_commit: Optional[str] = None,
    api_endpoints: Optional[List[Dict]] = None,
    database_configs: Optional[List[Dict]] = None,
    capture_states: bool = True,
    output_path: Optional[Path] = None,
) -> SemanticDriftReport

summary = agent.get_intent_summary() -> Dict[str, Any]
```

#### IntentBaselineExtractor

```python
from socialseed_e2e.agents import IntentBaselineExtractor

extractor = IntentBaselineExtractor(project_root: Path)

# Methods
baselines = extractor.extract_all() -> List[IntentBaseline]
baselines = extractor.get_baselines_by_category(category: str) -> List[IntentBaseline]
baselines = extractor.get_baselines_by_entity(entity: str) -> List[IntentBaseline]
```

#### Working with Reports

```python
from socialseed_e2e.agents import (
    SemanticDriftReport,
    DriftSeverity,
    DriftType,
)

# Report methods
summary = report.generate_summary() -> Dict[str, Any]
critical_drifts = report.get_drifts_by_severity(DriftSeverity.CRITICAL)
behavioral_drifts = report.get_drifts_by_type(DriftType.BEHAVIORAL)
has_critical = report.has_critical_drifts() -> bool

# Drift properties
drift.drift_id: str
drift.drift_type: DriftType
drift.severity: DriftSeverity
drift.description: str
drift.reasoning: str
drift.recommendation: str
drift.confidence: float
drift.affected_endpoints: List[str]
drift.affected_entities: List[str]
```

### Best Practices for AI Agents

1. **Always run analysis before suggesting changes**
   ```python
   agent = SemanticAnalyzerAgent(project_root)
   report = agent.analyze()
   if report.has_critical_drifts():
       # Alert about critical issues
       pass
   ```

2. **Extract intents before implementing features**
   ```python
   extractor = IntentBaselineExtractor(project_root)
   baselines = extractor.extract_all()
   # Use baselines to understand requirements
   ```

3. **Check specific categories for targeted changes**
   ```python
   auth_baselines = extractor.get_baselines_by_category("user_management")
   ```

4. **Validate state changes in databases**
   ```python
   report = agent.analyze(
       database_configs=[{
           "type": "neo4j",
           "uri": "bolt://localhost:7687",
       }]
   )
   ```

### Prompts for Common Tasks

**Task: Analyze a Pull Request**
```
Analyze PR #123 for semantic drift:
1. Extract intent baselines from docs and issues
2. Capture baseline state at PR base commit
3. Capture current state at PR head commit
4. Detect any logic drift
5. Generate report with recommendations

Focus on user_management and auth categories.
```

**Task: Verify Database Migration**
```
Verify that the database migration maintains business logic:
1. Extract intents related to data integrity
2. Capture Neo4j state before migration
3. Run migration
4. Capture Neo4j state after migration
5. Check for relationship or entity count drifts
6. Report any data integrity issues
```

**Task: Check API Changes**
```
Analyze API changes between v1.0 and v1.1:
1. Extract intents related to API behavior
2. Test endpoints /api/users and /api/follow
3. Compare responses between versions
4. Detect any behavioral drift
5. Report breaking changes
```

---

## Understanding Drift Reports

### SEMANTIC_DRIFT_REPORT.md Structure

```markdown
# Semantic Drift Analysis Report

## Executive Summary
- Total intents analyzed
- Total drifts detected
- Severity distribution
- Status indicator (✅/⚠️/🚨)

## Intent Baselines
- List of extracted intents
- Categories and confidence levels
- Source locations

## State Snapshots
- API snapshots (endpoints tested, responses)
- Database snapshots (entities, relationships)

## Detected Semantic Drifts
### Critical Issues
- High severity drifts requiring immediate attention

### High Priority
- Significant deviations to review

### Medium/Low
- Minor deviations or informational items

## Detailed Analysis
- Behavioral analysis
- Relationship analysis
- Business rule analysis

## Recommendations
- Specific actions to take
- Next steps

## Appendix
- Metadata
- Severity level definitions
- Drift type definitions
```

### Interpreting Results

**No Drifts Detected:**
```
✅ NO DRIFT DETECTED
System behavior aligns with intended business logic.
```
Action: Safe to deploy.

**Drifts Detected:**
```
⚠️  DRIFTS DETECTED - Review Recommended
Semantic drifts detected that may indicate deviations from intended business logic.
```
Action: Review the detailed drifts in the report.

**Critical Issues:**
```
🚨 CRITICAL ISSUES FOUND - Immediate action required!
```
Action: Fix before deployment.

### Severity Levels

| Level | Action Required | Example |
|-------|-----------------|---------|
| 🚨 CRITICAL | Fix immediately | Missing reciprocal relationship |
| ⚠️ HIGH | Fix before deploy | Business rule bypassed |
| 🔍 MEDIUM | Review and decide | Minor validation change |
| ℹ️ LOW | Optional review | Cosmetic change |
| 💡 INFO | Documentation only | Note for future reference |

---

## Advanced Usage

### Custom Intent Extraction

```python
from socialseed_e2e.agents import IntentBaselineExtractor

extractor = IntentBaselineExtractor(project_root)

# Extract from specific sources only
extractor._extract_from_docs()
extractor._extract_from_github_issues()

# Get baselines for specific category
auth_baselines = extractor.get_baselines_by_category("user_management")
```

### State Capture Without Analysis

```python
from socialseed_e2e.agents import StatefulAnalyzer

analyzer = StatefulAnalyzer(project_root, base_url="http://localhost:8080")

# Capture baseline
baseline = analyzer.capture_baseline_state(
    api_endpoints=[
        {"endpoint": "/api/users", "method": "GET"},
    ],
    database_configs=[
        {"type": "neo4j", "uri": "bolt://localhost:7687"},
    ],
)

# Save for later
analyzer.save_snapshot(baseline, "baseline.json")

# Load and compare
loaded = analyzer.load_snapshot("baseline.json")
differences = analyzer.compare_states(baseline, loaded)
```

### gRPC Integration

**Server:**
```python
from socialseed_e2e.agents.semantic_analyzer.grpc_server import serve

# Start gRPC server
serve(port=50051)
```

**Client:**
```python
from socialseed_e2e.agents.semantic_analyzer.grpc_client import (
    SemanticAnalyzerClient
)

with SemanticAnalyzerClient("localhost", 50051) as client:
    response = client.analyze(
        project_root="/path/to/project",
        baseline_commit="abc123",
        target_commit="def456",
    )
    print(f"Report: {response.report_path}")
    print(f"Drifts: {response.summary.total_drifts}")
```

### LLM Integration

For enhanced semantic analysis:

```python
from openai import OpenAI
from socialseed_e2e.agents import SemanticAnalyzerAgent

# Create LLM client
llm_client = OpenAI()

# Create agent with LLM
agent = SemanticAnalyzerAgent(
    project_root="/path/to/project",
    llm_client=llm_client,
)

# Run analysis with LLM-based reasoning
report = agent.analyze()
```

---

## Troubleshooting

### Common Issues

**Issue: No intent baselines extracted**
```
⚠️ No intent baselines were extracted. Please ensure documentation exists
in the `docs/` folder or GitHub issues are available.
```
Solution:
- Create documentation in `docs/` folder
- Add GitHub issues with expected behavior
- Write docstrings in your code

**Issue: Cannot connect to database**
```
Warning: Could not capture Neo4j state: [Errno 111] Connection refused
```
Solution:
- Verify database is running
- Check connection URI
- Ensure credentials are correct
- Install required drivers (`pip install neo4j`)

**Issue: API endpoints return errors**
```
Warning: Could not capture API state: 500 Server Error
```
Solution:
- Verify API is running
- Check base URL is correct
- Ensure endpoints exist and are accessible

**Issue: Report shows false positives**
```
Detected drifts that are actually intentional changes
```
Solution:
- Update documentation to reflect new behavior
- Add success criteria to intent baselines
- Use `--no-state-capture` for intent-only analysis

### Debug Mode

Enable verbose output:

```bash
# CLI
e2e semantic-analyze run --verbose

# Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

- Check the report's Appendix section for definitions
- Review the examples in this documentation
- Look at test cases in `tests/test_semantic_analyzer.py`
- Open an issue on GitHub

---

## Examples

### Example 1: Detect Missing Reciprocal Relationship

```python
# Before code change
# User A follows User B → creates A→B relationship

# After code change (bug introduced)
# User A follows User B → relationship not created

# Analysis will detect:
drift = {
    "type": "RELATIONSHIP",
    "severity": "CRITICAL",
    "description": "Reciprocal relationship missing after follow action",
    "reasoning": "Expected FOLLOW relationship not created in Neo4j",
}
```

### Example 2: Validation Bypass

```python
# Intent: "Only premium users can create groups"

# Before: Premium users → 200 OK, Free users → 403 Forbidden ✓
# After:  All users → 200 OK ✗

# Analysis will detect:
drift = {
    "type": "BUSINESS_RULE",
    "severity": "HIGH",
    "description": "Premium-only validation bypassed",
    "reasoning": "All users can now create groups, violating business rule",
}
```

### Example 3: State Transition Error

```python
# Intent: "Order status: pending → confirmed → shipped → delivered"

# Before: Correct transitions ✓
# After:  pending → shipped (skipping confirmed) ✗

# Analysis will detect:
drift = {
    "type": "STATE_TRANSITION",
    "severity": "HIGH",
    "description": "Invalid order state transition",
    "reasoning": "Order transitioned from pending to shipped without confirmation",
}
```

---

## Next Steps

- [ ] Review your SEMANTIC_DRIFT_REPORT.md
- [ ] Set up CI/CD integration
- [ ] Update documentation to reduce false positives
- [ ] Configure LLM for enhanced analysis
- [ ] Customize severity thresholds

---

**Need more help?** Open an issue at https://github.com/daironpf/socialseed-e2e/issues
