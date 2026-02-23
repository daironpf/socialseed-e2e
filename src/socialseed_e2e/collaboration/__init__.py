"""
Team Collaboration and Test Sharing module for socialseed-e2e.
Provides tools for test sharing, permissions, review workflows,
notifications, and team analytics.
"""

from .notifications import (
    JIRAIntegration,
    NotificationChannel,
    NotificationMessage,
    NotificationPriority,
    SlackNotifier,
    TeamAnalytics,
    TeamsNotifier,
)
from .permissions import Permission, PermissionManager, Role
from .review import Review, ReviewStatus, ReviewWorkflow
from .sharing import TestMetadata, TestPackage, TestRepository

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
