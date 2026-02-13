import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from socialseed_e2e.collaboration.sharing import TestRepository, TestMetadata, TestPackage
from socialseed_e2e.collaboration.permissions import PermissionManager, Permission, Role
from socialseed_e2e.collaboration.review import ReviewWorkflow, ReviewStatus


class TestSharing:
    """Tests for test sharing and repository."""
    
    @pytest.fixture
    def temp_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def repository(self, temp_repo):
        return TestRepository(temp_repo)
    
    @pytest.fixture
    def sample_package(self):
        metadata = TestMetadata(
            name="test_login",
            version="1.0.0",
            description="Login test",
            author="test_user",
            tags=["auth", "login"],
            category="authentication"
        )
        return TestPackage(
            metadata=metadata,
            test_content="def test_login(): pass",
            documentation="# Login Test\nTests user login functionality"
        )
    
    def test_publish_and_get(self, repository, sample_package):
        # Publish
        package_id = repository.publish(sample_package)
        assert package_id == "test_login@1.0.0"
        
        # Retrieve
        retrieved = repository.get("test_login", "1.0.0")
        assert retrieved is not None
        assert retrieved.metadata.name == "test_login"
        assert retrieved.test_content == "def test_login(): pass"
    
    def test_get_latest_version(self, repository, sample_package):
        # Publish v1.0.0
        repository.publish(sample_package)
        
        # Publish v2.0.0
        sample_package.metadata.version = "2.0.0"
        repository.publish(sample_package)
        
        # Get latest (should be 2.0.0)
        latest = repository.get("test_login")
        assert latest is not None
        assert latest.metadata.version == "2.0.0"
    
    def test_list_tests(self, repository, sample_package):
        repository.publish(sample_package)
        
        # List all
        tests = repository.list_tests()
        assert len(tests) == 1
        assert tests[0]["name"] == "test_login"
        
        # Filter by category
        auth_tests = repository.list_tests(category="authentication")
        assert len(auth_tests) == 1
        
        # Filter by tags
        login_tests = repository.list_tests(tags=["login"])
        assert len(login_tests) == 1
    
    def test_delete(self, repository, sample_package):
        repository.publish(sample_package)
        
        # Delete
        result = repository.delete("test_login", "1.0.0")
        assert result is True
        
        # Verify deleted
        retrieved = repository.get("test_login", "1.0.0")
        assert retrieved is None


class TestPermissions:
    """Tests for permissions and access control."""
    
    @pytest.fixture
    def perm_manager(self):
        return PermissionManager()
    
    def test_owner_permissions(self, perm_manager):
        perm_manager.set_owner("test_1", "user_1")
        
        # Owner should have all permissions
        assert perm_manager.has_permission("test_1", "user_1", Permission.READ)
        assert perm_manager.has_permission("test_1", "user_1", Permission.WRITE)
        assert perm_manager.has_permission("test_1", "user_1", Permission.DELETE)
        assert perm_manager.has_permission("test_1", "user_1", Permission.ADMIN)
    
    def test_grant_role(self, perm_manager):
        perm_manager.grant_role("test_1", "user_2", Role.CONTRIBUTOR)
        
        # Contributor should have read, write, review
        assert perm_manager.has_permission("test_1", "user_2", Permission.READ)
        assert perm_manager.has_permission("test_1", "user_2", Permission.WRITE)
        assert perm_manager.has_permission("test_1", "user_2", Permission.REVIEW)
        
        # But not delete or admin
        assert not perm_manager.has_permission("test_1", "user_2", Permission.DELETE)
        assert not perm_manager.has_permission("test_1", "user_2", Permission.ADMIN)
    
    def test_grant_and_revoke_permission(self, perm_manager):
        perm_manager.grant_permission("test_1", "user_3", Permission.READ)
        assert perm_manager.has_permission("test_1", "user_3", Permission.READ)
        
        perm_manager.revoke_permission("test_1", "user_3", Permission.READ)
        assert not perm_manager.has_permission("test_1", "user_3", Permission.READ)
    
    def test_list_users(self, perm_manager):
        perm_manager.set_owner("test_1", "owner")
        perm_manager.grant_role("test_1", "contributor", Role.CONTRIBUTOR)
        
        users = perm_manager.list_users("test_1")
        assert len(users) == 2
        
        owner_entry = next(u for u in users if u["user_id"] == "owner")
        assert owner_entry["is_owner"] is True


class TestReview:
    """Tests for review workflows."""
    
    @pytest.fixture
    def workflow(self):
        return ReviewWorkflow()
    
    def test_create_review(self, workflow):
        review = workflow.create_review("test_1", "reviewer_1")
        
        assert review.resource_id == "test_1"
        assert review.reviewer == "reviewer_1"
        assert review.status == ReviewStatus.PENDING
    
    def test_add_comment(self, workflow):
        review = workflow.create_review("test_1", "reviewer_1")
        
        workflow.add_comment(review.review_id, "commenter", "Looks good!")
        
        updated_review = workflow.get_review(review.review_id)
        assert len(updated_review.comments) == 1
        assert updated_review.comments[0].content == "Looks good!"
    
    def test_approve_review(self, workflow):
        review = workflow.create_review("test_1", "reviewer_1")
        
        review.approve()
        assert review.status == ReviewStatus.APPROVED
    
    def test_is_approved(self, workflow):
        # Create 2 reviews
        review1 = workflow.create_review("test_1", "reviewer_1")
        review2 = workflow.create_review("test_1", "reviewer_2")
        
        # Not approved yet
        assert not workflow.is_approved("test_1", min_approvals=2)
        
        # Approve one
        review1.approve()
        assert not workflow.is_approved("test_1", min_approvals=2)
        
        # Approve second
        review2.approve()
        assert workflow.is_approved("test_1", min_approvals=2)
    
    def test_review_summary(self, workflow):
        review1 = workflow.create_review("test_1", "reviewer_1")
        review2 = workflow.create_review("test_1", "reviewer_2")
        
        review1.approve()
        review2.request_changes()
        workflow.add_comment(review1.review_id, "author", "Thanks!")
        
        summary = workflow.get_review_summary("test_1")
        
        assert summary["total_reviews"] == 2
        assert summary["status_counts"]["approved"] == 1
        assert summary["status_counts"]["changes_requested"] == 1
        assert summary["total_comments"] == 1
