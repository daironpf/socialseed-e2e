"""Notifications and integrations for team collaboration.

This module provides integrations with Slack, Teams, JIRA,
and other collaboration tools.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Available notification channels."""

    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    JIRA = "jira"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationMessage(BaseModel):
    """Notification message structure."""

    title: str
    body: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channel: NotificationChannel
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class SlackNotifier:
    """Send notifications to Slack."""

    def __init__(
        self, webhook_url: Optional[str] = None, channel: Optional[str] = None
    ):
        """Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL
            channel: Default channel to post to
        """
        self.webhook_url = webhook_url
        self.channel = channel

    async def send(self, message: NotificationMessage) -> bool:
        """Send notification to Slack.

        Args:
            message: Notification to send

        Returns:
            True if successful
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        import aiohttp

        payload = {
            "text": message.title,
            "channel": self.channel,
            "attachments": [
                {
                    "color": self._get_priority_color(message.priority),
                    "fields": [
                        {"title": k, "value": str(v), "short": True}
                        for k, v in message.metadata.items()
                    ],
                    "footer": f"SocialSeed E2E | {message.timestamp.isoformat()}",
                }
            ],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def _get_priority_color(self, priority: NotificationPriority) -> str:
        """Get color for priority level."""
        colors = {
            NotificationPriority.LOW: "#36a64f",
            NotificationPriority.MEDIUM: "#ff9900",
            NotificationPriority.HIGH: "#ff6600",
            NotificationPriority.CRITICAL: "#ff0000",
        }
        return colors.get(priority, "#cccccc")


class TeamsNotifier:
    """Send notifications to Microsoft Teams."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize Teams notifier.

        Args:
            webhook_url: Teams incoming webhook URL
        """
        self.webhook_url = webhook_url

    async def send(self, message: NotificationMessage) -> bool:
        """Send notification to Teams.

        Args:
            message: Notification to send

        Returns:
            True if successful
        """
        if not self.webhook_url:
            logger.warning("Teams webhook URL not configured")
            return False

        import aiohttp

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": self._get_priority_color(message.priority),
            "summary": message.title,
            "sections": [
                {
                    "activityTitle": message.title,
                    "facts": [
                        {"name": k, "value": str(v)}
                        for k, v in message.metadata.items()
                    ],
                    "markdown": True,
                }
            ],
            "potentialAction": [],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Failed to send Teams notification: {e}")
            return False

    def _get_priority_color(self, priority: NotificationPriority) -> str:
        """Get color for priority level."""
        colors = {
            NotificationPriority.LOW: "0078D4",
            NotificationPriority.MEDIUM: "FFB900",
            NotificationPriority.HIGH: "D83B01",
            NotificationPriority.CRITICAL: "E81123",
        }
        return colors.get(priority, "0078D4")


class JIRAIntegration:
    """Integration with JIRA for issue tracking."""

    def __init__(self, base_url: str, email: str, api_token: str):
        """Initialize JIRA integration.

        Args:
            base_url: JIRA base URL
            email: JIRA email
            api_token: JIRA API token
        """
        self.base_url = base_url
        self.email = email
        self.api_token = api_token

    def create_issue(
        self, project_key: str, summary: str, description: str, issue_type: str = "Bug"
    ) -> Optional[str]:
        """Create a JIRA issue.

        Args:
            project_key: JIRA project key
            summary: Issue summary
            description: Issue description
            issue_type: Issue type (Bug, Task, Story, etc.)

        Returns:
            Issue key if successful
        """
        import requests
        from requests.auth import HTTPBasicAuth

        url = f"{self.base_url}/rest/api/3/issue"

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": issue_type},
            }
        }

        try:
            auth = HTTPBasicAuth(self.email, self.api_token)
            response = requests.post(url, json=payload, auth=auth)

            if response.status_code == 201:
                return response.json()["key"]
            else:
                logger.error(f"Failed to create JIRA issue: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Failed to create JIRA issue: {e}")
            return None

    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add comment to JIRA issue.

        Args:
            issue_key: JIRA issue key
            comment: Comment text

        Returns:
            True if successful
        """
        import requests
        from requests.auth import HTTPBasicAuth

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"

        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment}],
                    }
                ],
            }
        }

        try:
            auth = HTTPBasicAuth(self.email, self.api_token)
            response = requests.post(url, json=payload, auth=auth)
            return response.status_code == 201
        except Exception as e:
            logger.error(f"Failed to add JIRA comment: {e}")
            return False


class TeamAnalytics:
    """Track team collaboration metrics."""

    def __init__(self, storage_path: str = "analytics"):
        """Initialize team analytics.

        Args:
            storage_path: Path to store analytics data
        """
        self.storage_path = storage_path

    def track_test_execution(
        self, test_name: str, user: str, status: str, duration_ms: float
    ):
        """Track test execution for analytics.

        Args:
            test_name: Name of test
            user: User who ran test
            status: Test status (passed, failed, skipped)
            duration_ms: Test duration
        """
        self._append_event(
            "test_execution",
            {
                "test_name": test_name,
                "user": user,
                "status": status,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def track_contribution(self, user: str, action: str, resource: str):
        """Track user contributions.

        Args:
            user: User who contributed
            action: Action performed
            resource: Resource affected
        """
        self._append_event(
            "contribution",
            {
                "user": user,
                "action": action,
                "resource": resource,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def get_user_stats(self, user: str) -> Dict[str, Any]:
        """Get statistics for a user.

        Args:
            user: Username

        Returns:
            Statistics dictionary
        """
        events = self._load_events()
        user_events = [e for e in events if e.get("user") == user]

        test_executions = [e for e in user_events if e.get("type") == "test_execution"]
        passed = len([e for e in test_executions if e.get("status") == "passed"])
        failed = len([e for e in test_executions if e.get("status") == "failed"])

        contributions = len([e for e in user_events if e.get("type") == "contribution"])

        return {
            "user": user,
            "total_tests": len(test_executions),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(test_executions) * 100 if test_executions else 0,
            "contributions": contributions,
        }

    def get_team_stats(self) -> Dict[str, Any]:
        """Get statistics for the entire team.

        Returns:
            Team statistics dictionary
        """
        events = self._load_events()

        unique_users = set(e.get("user") for e in events if e.get("user"))
        total_tests = len([e for e in events if e.get("type") == "test_execution"])

        return {
            "total_users": len(unique_users),
            "total_tests": total_tests,
            "active_users": len(unique_users),
        }

    def _append_event(self, event_type: str, event_data: Dict[str, Any]):
        """Append event to storage."""
        import os
        from pathlib import Path

        event_data["type"] = event_type

        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

        filename = (
            f"{self.storage_path}/events_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )

        with open(filename, "a") as f:
            f.write(json.dumps(event_data) + "\n")

    def _load_events(self) -> List[Dict[str, Any]]:
        """Load events from storage."""
        events = []

        if not Path(self.storage_path).exists():
            return events

        for filepath in Path(self.storage_path).glob("*.jsonl"):
            with open(filepath) as f:
                for line in f:
                    try:
                        events.append(json.loads(line))
                    except:
                        pass

        return events


# Add missing import for pydantic
from pydantic import BaseModel, Field
