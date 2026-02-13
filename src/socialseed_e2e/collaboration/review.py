"""
Review workflows for test collaboration.
Supports code review, comments, and approval processes.
"""
import logging
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ReviewStatus(str, Enum):
    """Status of a review."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class Comment(BaseModel):
    """A comment on a review."""
    author: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    line_number: Optional[int] = None  # For inline comments
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Review(BaseModel):
    """A review of a test or change."""
    review_id: str
    resource_id: str  # ID of the test being reviewed
    reviewer: str
    status: ReviewStatus = ReviewStatus.PENDING
    comments: List[Comment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def add_comment(self, author: str, content: str, line_number: Optional[int] = None):
        """Add a comment to the review."""
        comment = Comment(author=author, content=content, line_number=line_number)
        self.comments.append(comment)
        self.updated_at = datetime.now()
    
    def approve(self):
        """Approve the review."""
        self.status = ReviewStatus.APPROVED
        self.updated_at = datetime.now()
    
    def reject(self):
        """Reject the review."""
        self.status = ReviewStatus.REJECTED
        self.updated_at = datetime.now()
    
    def request_changes(self):
        """Request changes."""
        self.status = ReviewStatus.CHANGES_REQUESTED
        self.updated_at = datetime.now()


class ReviewWorkflow:
    """
    Manages review workflows for tests.
    """
    
    def __init__(self):
        # review_id -> Review
        self._reviews: Dict[str, Review] = {}
        # resource_id -> list of review_ids
        self._resource_reviews: Dict[str, List[str]] = {}
    
    def create_review(self, resource_id: str, reviewer: str) -> Review:
        """Create a new review for a resource."""
        review_id = f"{resource_id}_{reviewer}_{datetime.now().timestamp()}"
        review = Review(
            review_id=review_id,
            resource_id=resource_id,
            reviewer=reviewer
        )
        
        self._reviews[review_id] = review
        
        if resource_id not in self._resource_reviews:
            self._resource_reviews[resource_id] = []
        self._resource_reviews[resource_id].append(review_id)
        
        logger.info(f"Created review {review_id} for {resource_id} by {reviewer}")
        return review
    
    def get_review(self, review_id: str) -> Optional[Review]:
        """Get a review by ID."""
        return self._reviews.get(review_id)
    
    def get_reviews_for_resource(self, resource_id: str) -> List[Review]:
        """Get all reviews for a resource."""
        review_ids = self._resource_reviews.get(resource_id, [])
        return [self._reviews[rid] for rid in review_ids if rid in self._reviews]
    
    def add_comment(self, review_id: str, author: str, content: str, line_number: Optional[int] = None) -> bool:
        """Add a comment to a review."""
        review = self._reviews.get(review_id)
        if not review:
            logger.warning(f"Review {review_id} not found")
            return False
        
        review.add_comment(author, content, line_number)
        logger.info(f"Added comment to review {review_id}")
        return True
    
    def update_status(self, review_id: str, status: ReviewStatus) -> bool:
        """Update the status of a review."""
        review = self._reviews.get(review_id)
        if not review:
            logger.warning(f"Review {review_id} not found")
            return False
        
        review.status = status
        review.updated_at = datetime.now()
        logger.info(f"Updated review {review_id} status to {status}")
        return True
    
    def is_approved(self, resource_id: str, min_approvals: int = 1) -> bool:
        """
        Check if a resource has enough approvals.
        """
        reviews = self.get_reviews_for_resource(resource_id)
        approvals = sum(1 for r in reviews if r.status == ReviewStatus.APPROVED)
        return approvals >= min_approvals
    
    def get_review_summary(self, resource_id: str) -> Dict[str, Any]:
        """Get a summary of reviews for a resource."""
        reviews = self.get_reviews_for_resource(resource_id)
        
        status_counts = {
            ReviewStatus.PENDING: 0,
            ReviewStatus.APPROVED: 0,
            ReviewStatus.REJECTED: 0,
            ReviewStatus.CHANGES_REQUESTED: 0
        }
        
        for review in reviews:
            status_counts[review.status] += 1
        
        total_comments = sum(len(r.comments) for r in reviews)
        
        return {
            "total_reviews": len(reviews),
            "status_counts": {k.value: v for k, v in status_counts.items()},
            "total_comments": total_comments,
            "is_approved": self.is_approved(resource_id)
        }
