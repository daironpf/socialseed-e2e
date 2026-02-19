"""
Team Collaboration and Test Sharing module for socialseed-e2e.
Provides tools for test sharing, permissions, review workflows,
notifications, and team analytics.
"""

from .sharing import TestRepository, TestMetadata, TestPackage
from .permissions import PermissionManager, Permission, Role
from .review import ReviewWorkflow, ReviewStatus, Review
from .notifications import (
    NotificationChannel,
    NotificationPriority,
    NotificationMessage,
    SlackNotifier,
    TeamsNotifier,
    JIRAIntegration,
    TeamAnalytics,
)

__all__ = [
    "TestRepository",
    "TestMetadata",
    "TestPackage",
    "PermissionManager",
    "Permission",
    "Role",
    "ReviewWorkflow",
    "ReviewStatus",
    "Review",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationMessage",
    "SlackNotifier",
    "TeamsNotifier",
    "JIRAIntegration",
    "TeamAnalytics",
]
