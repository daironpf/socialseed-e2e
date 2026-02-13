# Team Collaboration and Test Sharing

The collaboration module provides enterprise-grade features for teams to work together on E2E tests, including test sharing, access control, and review workflows.

## Overview

The collaboration system consists of three main components:

1. **Test Repository**: Share and version tests across teams
2. **Permission Manager**: Control access with role-based permissions
3. **Review Workflow**: Implement code review processes for tests

## Installation

The collaboration features are included in the core package:

```bash
pip install socialseed-e2e
```

## Quick Start

### 1. Test Sharing and Reusability

Share tests with your team using the `TestRepository`:

```python
from pathlib import Path
from socialseed_e2e.collaboration import TestRepository, TestMetadata, TestPackage

# Initialize repository
repo = TestRepository(Path("./shared_tests"))

# Create a test package
metadata = TestMetadata(
    name="test_user_login",
    version="1.0.0",
    description="Comprehensive user login test",
    author="john.doe@company.com",
    tags=["auth", "critical", "smoke"],
    category="authentication"
)

test_code = '''
def test_user_login(auth_page):
    """Test user login with valid credentials."""
    response = auth_page.login(username="testuser", password="secret")
    auth_page.assert_ok(response)
    assert response.json()["token"] is not None
'''

package = TestPackage(
    metadata=metadata,
    test_content=test_code,
    fixtures={
        "auth_page": "# Auth page fixture code..."
    },
    documentation="# User Login Test\n\nTests the authentication flow..."
)

# Publish to repository
package_id = repo.publish(package)
print(f"Published: {package_id}")  # test_user_login@1.0.0
```

### 2. Retrieving Shared Tests

```python
# Get latest version
test = repo.get("test_user_login")

# Get specific version
test = repo.get("test_user_login", version="1.0.0")

# List all tests
all_tests = repo.list_tests()

# Filter by category
auth_tests = repo.list_tests(category="authentication")

# Filter by tags
critical_tests = repo.list_tests(tags=["critical"])
```

### 3. Access Control and Permissions

Control who can access and modify tests:

```python
from socialseed_e2e.collaboration import PermissionManager, Role, Permission

# Initialize permission manager
perm = PermissionManager()

# Set test owner
perm.set_owner("test_user_login", "john.doe@company.com")

# Grant roles to team members
perm.grant_role("test_user_login", "jane.smith@company.com", Role.CONTRIBUTOR)
perm.grant_role("test_user_login", "bob.jones@company.com", Role.VIEWER)

# Grant specific permissions
perm.grant_permission("test_user_login", "alice@company.com", Permission.READ)
perm.grant_permission("test_user_login", "alice@company.com", Permission.REVIEW)

# Check permissions
can_write = perm.has_permission("test_user_login", "jane.smith@company.com", Permission.WRITE)
print(f"Jane can write: {can_write}")  # True (CONTRIBUTOR role)

# List all users with access
users = perm.list_users("test_user_login")
for user in users:
    print(f"{user['user_id']}: {user['role']} - {user['permissions']}")
```

### 4. Review Workflows

Implement code review processes for test changes:

```python
from socialseed_e2e.collaboration import ReviewWorkflow, ReviewStatus

# Initialize workflow
workflow = ReviewWorkflow()

# Create a review
review = workflow.create_review(
    resource_id="test_user_login",
    reviewer="jane.smith@company.com"
)

# Add comments
workflow.add_comment(
    review.review_id,
    author="jane.smith@company.com",
    content="Consider adding edge cases for invalid credentials"
)

workflow.add_comment(
    review.review_id,
    author="jane.smith@company.com",
    content="This assertion could be more specific",
    line_number=5  # Inline comment
)

# Request changes
review.request_changes()

# After changes are made, approve
review.approve()

# Check if test is approved
if workflow.is_approved("test_user_login", min_approvals=2):
    print("Test is ready to merge!")

# Get review summary
summary = workflow.get_review_summary("test_user_login")
print(f"Total reviews: {summary['total_reviews']}")
print(f"Approved: {summary['status_counts']['approved']}")
print(f"Comments: {summary['total_comments']}")
```

## Roles and Permissions

### Predefined Roles

| Role | Permissions | Description |
|------|------------|-------------|
| `VIEWER` | READ | Can view tests |
| `CONTRIBUTOR` | READ, WRITE, REVIEW | Can modify and review tests |
| `MAINTAINER` | READ, WRITE, DELETE, REVIEW | Full control except admin |
| `OWNER` | All permissions | Complete control including admin |

### Individual Permissions

- `READ`: View test content
- `WRITE`: Modify tests
- `DELETE`: Remove tests
- `REVIEW`: Review and approve changes
- `ADMIN`: Manage permissions and settings

## Complete Workflow Example

Here's a complete example showing a typical team workflow:

```python
from pathlib import Path
from socialseed_e2e.collaboration import (
    TestRepository, TestMetadata, TestPackage,
    PermissionManager, Role,
    ReviewWorkflow
)

# 1. Setup
repo = TestRepository(Path("./team_tests"))
perm = PermissionManager()
workflow = ReviewWorkflow()

# 2. Author creates and publishes a test
metadata = TestMetadata(
    name="test_checkout_flow",
    version="1.0.0",
    author="developer@company.com",
    tags=["e2e", "checkout"],
    category="commerce"
)

package = TestPackage(
    metadata=metadata,
    test_content="def test_checkout(): ...",
    documentation="# Checkout Flow Test"
)

test_id = repo.publish(package)

# 3. Set permissions
perm.set_owner(test_id, "developer@company.com")
perm.grant_role(test_id, "reviewer@company.com", Role.CONTRIBUTOR)
perm.grant_role(test_id, "qa-lead@company.com", Role.MAINTAINER)

# 4. Create review
review = workflow.create_review(test_id, "reviewer@company.com")
workflow.add_comment(review.review_id, "reviewer@company.com", "LGTM!")
review.approve()

# 5. Check approval status
if workflow.is_approved(test_id):
    print("✅ Test approved and ready for use")

    # Team members can now retrieve and use the test
    shared_test = repo.get("test_checkout_flow")
    print(f"Retrieved: {shared_test.metadata.name}")
```

## Version Management

The repository supports versioning for test evolution:

```python
# Publish version 1.0.0
metadata_v1 = TestMetadata(name="test_api", version="1.0.0", author="dev")
package_v1 = TestPackage(metadata=metadata_v1, test_content="# v1 code")
repo.publish(package_v1)

# Publish version 2.0.0 with improvements
metadata_v2 = TestMetadata(name="test_api", version="2.0.0", author="dev")
package_v2 = TestPackage(metadata=metadata_v2, test_content="# v2 code")
repo.publish(package_v2)

# Get latest (v2.0.0)
latest = repo.get("test_api")

# Get specific version (v1.0.0)
v1 = repo.get("test_api", version="1.0.0")
```

## Best Practices

### 1. Test Metadata
- Use descriptive names and clear descriptions
- Tag tests appropriately for easy discovery
- Categorize tests by functional area
- Include comprehensive documentation

### 2. Access Control
- Always set an owner for tests
- Use roles for common permission sets
- Grant individual permissions only when needed
- Review permissions regularly

### 3. Review Process
- Require reviews for critical tests
- Use inline comments for specific feedback
- Set minimum approval requirements
- Document review decisions

### 4. Version Management
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Document changes between versions
- Keep backward compatibility when possible
- Archive deprecated versions

## Integration with CI/CD

```python
# Example: CI/CD pipeline integration
def deploy_approved_tests():
    """Deploy only approved tests to production."""
    repo = TestRepository(Path("./tests"))
    workflow = ReviewWorkflow()

    tests = repo.list_tests(tags=["production"])

    for test_info in tests:
        test_id = f"{test_info['name']}@{test_info['version']}"

        if workflow.is_approved(test_id, min_approvals=2):
            test = repo.get(test_info['name'], test_info['version'])
            # Deploy test to production environment
            deploy_to_prod(test)
        else:
            print(f"⚠️  {test_id} not approved, skipping deployment")
```

## API Reference

### TestRepository

- `publish(package: TestPackage) -> str`: Publish a test package
- `get(name: str, version: Optional[str] = None) -> Optional[TestPackage]`: Retrieve a test
- `list_tests(category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict]`: List tests
- `delete(name: str, version: str) -> bool`: Delete a test version

### PermissionManager

- `set_owner(resource_id: str, user_id: str)`: Set resource owner
- `grant_role(resource_id: str, user_id: str, role: Role)`: Grant a role
- `grant_permission(resource_id: str, user_id: str, permission: Permission)`: Grant permission
- `has_permission(resource_id: str, user_id: str, permission: Permission) -> bool`: Check permission
- `list_users(resource_id: str) -> List[Dict]`: List users with access

### ReviewWorkflow

- `create_review(resource_id: str, reviewer: str) -> Review`: Create a review
- `add_comment(review_id: str, author: str, content: str, line_number: Optional[int])`: Add comment
- `update_status(review_id: str, status: ReviewStatus) -> bool`: Update review status
- `is_approved(resource_id: str, min_approvals: int = 1) -> bool`: Check approval status
- `get_review_summary(resource_id: str) -> Dict`: Get review summary

## See Also

- [Test Organization](test-organization.md)
- [CI/CD Integration](ci-cd.md)
- [Plugin Development](plugin-development.md)
