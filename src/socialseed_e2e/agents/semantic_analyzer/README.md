# Autonomous Semantic Regression & Logic Drift Detection Agent

**Issue #163 Implementation**

This agent answers the question: **"Is the system's behavior still aligned with the original business intent?"**

Unlike traditional E2E tests that check "is the button clickable?", this agent performs deep semantic analysis to detect when code changes introduce logic drift that violates business requirements, even when all tests pass.

## Overview

The Semantic Regression Agent provides:

- **Intent Baseline Extraction**: Crawls docs/, GitHub issues, code comments, and test cases
- **Stateful Analysis**: Captures API responses and database states before/after changes
- **Logic Drift Detection**: Uses LLM-based reasoning to detect semantic violations
- **Comprehensive Reports**: Generates SEMANTIC_DRIFT_REPORT.md with actionable insights

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              SemanticAnalyzerAgent (Orchestrator)           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐                                       │
│  │ IntentBaseline   │  Crawl docs/, issues, comments        │
│  │ Extractor        │  → Extract expected behavior           │
│  └────────┬─────────┘                                       │
│           ↓                                                 │
│  ┌──────────────────┐                                       │
│  │ StatefulAnalyzer │  Capture API + DB snapshots           │
│  │                  │  → Before & after code changes         │
│  └────────┬─────────┘                                       │
│           ↓                                                 │
│  ┌──────────────────┐                                       │
│  │ LogicDrift       │  LLM-based semantic comparison        │
│  │ Detector         │  → Detect business logic violations    │
│  └────────┬─────────┘                                       │
│           ↓                                                 │
│  ┌──────────────────┐                                       │
│  │ ReportGenerator  │  Generate SEMANTIC_DRIFT_REPORT.md    │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# The semantic analyzer is included with socialseed-e2e
pip install socialseed-e2e

# Optional: For LLM-based analysis (recommended)
pip install openai  # or your preferred LLM client

# Optional: For database snapshots
pip install neo4j   # For Neo4j graph databases
pip install pymongo # For MongoDB
pip install sqlalchemy  # For SQL databases
```

## Quick Start

### Command Line Usage

```bash
# Run complete semantic analysis
e2e semantic-analyze

# Compare specific commits
e2e semantic-analyze --baseline-commit HEAD~1 --target-commit HEAD

# Analyze a PR
e2e semantic-analyze --pr 123

# Specify API endpoints to test
e2e semantic-analyze \
  --api-endpoint "GET /api/users" \
  --api-endpoint "POST /api/follow"

# Include database snapshots
e2e semantic-analyze \
  --database neo4j \
  --db-uri bolt://localhost:7687 \
  --db-user neo4j \
  --db-password password

# Quick check without state capture
e2e semantic-analyze --quick-check
```

### Python API Usage

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
        {"endpoint": "/api/follow", "method": "POST", "body": {"user_id": "123"}},
    ],
    database_configs=[
        {"type": "neo4j", "uri": "bolt://localhost:7687"},
    ],
)

# Check results
if report.has_critical_drifts():
    print("🚨 Critical issues found!")
    for drift in report.get_drifts_by_severity("critical"):
        print(f"  - {drift.description}")
        print(f"    Recommendation: {drift.recommendation}")

# Get summary
summary = report.generate_summary()
print(f"Total drifts: {summary['total_drifts']}")
print(f"Critical: {summary['severity_distribution']['critical']}")
```

## How It Works

### 1. Intent Baseline Extraction

The agent crawls multiple sources to understand expected behavior:

**From Documentation (docs/*.md):**
```markdown
## Feature: User Following

When a user follows another user, the system should:
- Create a FOLLOW relationship in Neo4j
- Send a notification to the followed user
- Update follower/following counts
```

**From GitHub Issues (issues.json):**
```json
{
  "title": "Implement reciprocal following",
  "body": "When user A follows user B, they should appear in each other's lists",
  "labels": ["feature", "social"]
}
```

**From Code Comments:**
```python
def follow_user(user_id: str, target_id: str):
    """
    Creates a FOLLOW relationship between users.
    
    Preconditions:
    - User must be authenticated
    - Cannot follow yourself
    
    Postconditions:
    - FOLLOW relationship created in Neo4j
    - Notification sent to target user
    """
```

### 2. Stateful Analysis

Captures complete system state:

**API Snapshots:**
```python
api_snapshot = {
    "endpoint": "/api/follow",
    "method": "POST",
    "request_body": {"user_id": "123", "target_id": "456"},
    "response_body": {"success": True, "relationship_id": "789"},
    "response_status": 200,
    "timestamp": "2026-02-13T10:30:00",
}
```

**Database Snapshots:**
```python
# Neo4j example
neo4j_snapshot = {
    "entities": {
        "User": [{"id": "123", "name": "Alice"}, {"id": "456", "name": "Bob"}],
    },
    "relationships": [
        {"from": {"id": "123"}, "relationship": "FOLLOWS", "to": {"id": "456"}},
    ],
}
```

### 3. Logic Drift Detection

Detects semantic violations:

**Example 1: Missing Reciprocal Relationship**
```
Intent: "When user A follows user B, they should appear in each other's lists"

Before: User A FOLLOWS User B ✓
After:  Relationship not created ✗

Drift: RELATIONSHIP (Critical)
Reasoning: Expected reciprocal relationship not created after follow action
```

**Example 2: Business Logic Change**
```
Intent: "Only premium users can create groups"

Before: Premium users: 200 OK, Free users: 403 Forbidden ✓
After:  All users: 200 OK ✗

Drift: BUSINESS_RULE (High)
Reasoning: Validation logic bypassed - all users can now create groups
```

**Example 3: State Transition Error**
```
Intent: "Order status transitions: pending → confirmed → shipped → delivered"

Before: Correct transitions ✓
After:  pending → shipped (skipping confirmed) ✗

Drift: STATE_TRANSITION (High)
Reasoning: Invalid state transition detected
```

## Drift Types

| Type | Description | Example |
|------|-------------|---------|
| **BEHAVIORAL** | Behavior differs from intent | API returns different response structure |
| **RELATIONSHIP** | Entity relationships changed | Missing reciprocal relationship in graph |
| **STATE_TRANSITION** | State machine transitions incorrect | Order skips "confirmed" status |
| **VALIDATION_LOGIC** | Validation rules changed | Previously rejected inputs now accepted |
| **BUSINESS_RULE** | Core business logic changed | All users can access premium features |
| **DATA_INTEGRITY** | Data consistency issues | Orphaned records after deletion |
| **SIDE_EFFECT** | Unexpected side effects | Action creates wrong type of notification |
| **MISSING_FUNCTIONALITY** | Expected behavior not present | Feature described in docs not implemented |

## Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| **CRITICAL** | Breaks core business functionality | Fix immediately before deployment |
| **HIGH** | Significant deviation from intent | Address before deployment |
| **MEDIUM** | Moderate deviation, may be intentional | Review and decide |
| **LOW** | Minor deviation or cosmetic change | Optional review |
| **INFO** | Informational, no action required | Documentation only |

## Report Format

The agent generates a comprehensive `SEMANTIC_DRIFT_REPORT.md`:

```markdown
# Semantic Drift Analysis Report

**Project:** My API
**Report ID:** sdr_a1b2c3d4e5f6
**Generated:** 2026-02-13 10:30:00

## Executive Summary

⚠️ **3 semantic drift(s) detected** across 15 intent(s).

🚨 **1 CRITICAL** issue(s) require immediate attention.

### Severity Distribution

| Severity | Count | Status |
|----------|-------|--------|
| 🚨 CRITICAL | 1 | Action Required |
| ⚠️ HIGH | 1 | Action Required |
| ⚡ MEDIUM | 1 | Review |

## Detected Semantic Drifts

### 🚨 CRITICAL Severity

#### 🚨 drift_a1b2c3 (Relationship)

**Description:** Reciprocal relationship missing after follow action

**Related Intent:** User Following Feature
- Expected Behavior: When user A follows user B, create bidirectional relationship

**Reasoning:** Expected reciprocal relationship not created after follow action

**Recommendation:** URGENT: Check relationship creation logic in your data layer. This is a critical issue that should be fixed immediately.

**Confidence:** 95%

<details>
<summary>Evidence</summary>

```json
[{"from": "user_123"}, {"relationship_type": "FOLLOWS"}, {"to": "user_456"}]
```

</details>
```

## gRPC Integration

The agent exposes a gRPC service for inter-agent communication:

```protobuf
service SemanticAnalyzer {
  rpc Analyze(AnalyzeRequest) returns (AnalyzeResponse);
  rpc ExtractIntents(ExtractIntentsRequest) returns (ExtractIntentsResponse);
  rpc CaptureState(CaptureStateRequest) returns (CaptureStateResponse);
  rpc DetectDrift(DetectDriftRequest) returns (DetectDriftResponse);
  rpc StreamAnalysisProgress(StreamRequest) returns (stream ProgressUpdate);
}
```

**Python Client Example:**
```python
import grpc
from socialseed_e2e.agents.semantic_analyzer.proto import semantic_analyzer_pb2
from socialseed_e2e.agents.semantic_analyzer.proto import semantic_analyzer_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = semantic_analyzer_pb2_grpc.SemanticAnalyzerStub(channel)

request = semantic_analyzer_pb2.AnalyzeRequest(
    project_root="/path/to/project",
    baseline_commit="abc123",
    target_commit="def456",
)

response = stub.Analyze(request)
print(f"Report: {response.report_path}")
print(f"Total drifts: {response.summary.total_drifts}")
```

## Configuration

Create `.e2e/semantic_analyzer.yaml`:

```yaml
semantic_analyzer:
  project_name: "My API"
  base_url: "http://localhost:8080"
  
  # Intent extraction settings
  intent_sources:
    - docs
    - github_issues
    - code_comments
    - test_cases
  
  # API endpoints to monitor
  api_endpoints:
    - endpoint: /api/users
      method: GET
    - endpoint: /api/follow
      method: POST
      body:
        user_id: "{{test_user_id}}"
        target_id: "{{target_user_id}}"
  
  # Database configurations
  databases:
    - type: neo4j
      uri: bolt://localhost:7687
      user: neo4j
      password: "${NEO4J_PASSWORD}"
    
    - type: postgresql
      connection: postgresql://user:pass@localhost/dbname
  
  # LLM configuration (for enhanced analysis)
  llm:
    provider: openai
    model: gpt-4
    api_key: "${OPENAI_API_KEY}"
  
  # Drift detection thresholds
  thresholds:
    confidence_threshold: 0.7
    severity_overrides:
      - pattern: "relationship.*missing"
        severity: critical
```

## CI/CD Integration

### GitHub Actions

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
      
      - name: Run Semantic Analysis
        run: |
          e2e semantic-analyze \
            --baseline-commit ${{ github.event.pull_request.base.sha }} \
            --target-commit ${{ github.event.pull_request.head.sha }} \
            --output .e2e/reports/
      
      - name: Check for Critical Drifts
        run: |
          if grep -q "CRITICAL" .e2e/reports/SEMANTIC_DRIFT_REPORT.md; then
            echo "🚨 Critical semantic drifts detected!"
            exit 1
          fi
      
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: semantic-drift-report
          path: .e2e/reports/SEMANTIC_DRIFT_REPORT.md
```

## Use Cases

### 1. PR Review Automation
Automatically check PRs for semantic regressions before merging.

### 2. Legacy Code Refactoring
Ensure behavior preservation when refactoring old code.

### 3. Database Migrations
Validate that data migrations maintain business logic integrity.

### 4. API Versioning
Detect breaking semantic changes in API updates.

### 5. Microservice Communication
Verify that service changes don't break cross-service contracts.

## Limitations

- **LLM Dependency**: Best results require LLM integration for nuanced semantic analysis
- **Database Coverage**: Currently supports Neo4j, PostgreSQL, MySQL, MongoDB (extensible)
- **Documentation Quality**: Intent extraction quality depends on documentation completeness
- **Performance**: Full analysis with state capture can be slow for large APIs

## Roadmap

- [ ] Support for more database types (Redis, Elasticsearch)
- [ ] Integration with OpenTelemetry for distributed tracing
- [ ] Machine learning for drift pattern recognition
- [ ] Automated fix suggestions via LLM
- [ ] Integration with existing regression test suites

## Contributing

See the main project documentation for contribution guidelines.

## License

MIT License - see LICENSE file for details.
