"""
AI Alerting & Notification Engine - EPIC-013
Real-time alerting with AI-powered root cause analysis.
"""

import asyncio
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import httpx


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status."""
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class NotificationChannel(str, Enum):
    """Notification channel types."""
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    EMAIL = "email"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    metric: str
    threshold: float
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    duration_seconds: int = 60
    severity: AlertSeverity = AlertSeverity.WARNING
    channels: List[NotificationChannel] = field(default_factory=list)
    enabled: bool = True
    description: str = ""


@dataclass
class Alert:
    """An alert instance."""
    id: str
    rule_name: str
    metric: str
    value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.TRIGGERED
    triggered_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    root_cause_analysis: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlertRuleEngine:
    """Engine for evaluating alert rules."""
    
    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._lock = threading.Lock()
        self._alert_callbacks: List[Callable] = []
        self._metrics_buffer: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        with self._lock:
            self._rules[rule.name] = rule
    
    def remove_rule(self, name: str) -> bool:
        """Remove an alert rule."""
        with self._lock:
            if name in self._rules:
                del self._rules[name]
                return True
            return False
    
    def get_rule(self, name: str) -> Optional[AlertRule]:
        """Get an alert rule."""
        return self._rules.get(name)
    
    def list_rules(self) -> List[Dict[str, Any]]:
        """List all alert rules."""
        return [
            {
                "name": r.name,
                "metric": r.metric,
                "threshold": r.threshold,
                "condition": r.condition,
                "severity": r.severity.value,
                "enabled": r.enabled,
                "description": r.description,
            }
            for r in self._rules.values()
        ]
    
    def _evaluate_condition(self, value: float, threshold: float, condition: str) -> bool:
        """Evaluate a condition."""
        conditions = {
            "gt": value > threshold,
            "lt": value < threshold,
            "eq": value == threshold,
            "gte": value >= threshold,
            "lte": value <= threshold,
        }
        return conditions.get(condition, False)
    
    def process_metric(self, metric_name: str, value: float, metadata: Optional[Dict] = None) -> List[Alert]:
        """Process a metric and evaluate rules."""
        with self._lock:
            triggered_alerts = []
            
            if metric_name not in self._metrics_buffer:
                self._metrics_buffer[metric_name] = []
            
            self._metrics_buffer[metric_name].append({
                "value": value,
                "timestamp": datetime.now(),
                "metadata": metadata or {},
            })
            
            cutoff = datetime.now() - timedelta(seconds=60)
            self._metrics_buffer[metric_name] = [
                m for m in self._metrics_buffer[metric_name]
                if m["timestamp"] >= cutoff
            ]
            
            for rule in self._rules.values():
                if not rule.enabled:
                    continue
                if rule.metric != metric_name:
                    continue
                
                recent_values = [m["value"] for m in self._metrics_buffer[metric_name]]
                if not recent_values:
                    continue
                
                avg_value = sum(recent_values) / len(recent_values)
                
                if self._evaluate_condition(avg_value, rule.threshold, rule.condition):
                    alert = Alert(
                        id=f"alert-{rule.name}-{int(datetime.now().timestamp())}",
                        rule_name=rule.name,
                        metric=metric_name,
                        value=avg_value,
                        threshold=rule.threshold,
                        severity=rule.severity,
                        metadata=metadata or {},
                    )
                    triggered_alerts.append(alert)
                    
                    for callback in self._alert_callbacks:
                        callback(alert)
            
            return triggered_alerts
    
    def on_alert(self, callback: Callable[[Alert], None]) -> None:
        """Register an alert callback."""
        self._alert_callbacks.append(callback)


class NotificationManager:
    """Manager for sending notifications to various channels."""
    
    def __init__(self):
        self._channels: Dict[NotificationChannel, Dict[str, Any]] = {}
        self._enabled_channels: List[NotificationChannel] = []
    
    def configure_channel(
        self,
        channel: NotificationChannel,
        config: Dict[str, Any],
    ) -> None:
        """Configure a notification channel."""
        self._channels[channel] = config
        
        if channel not in self._enabled_channels:
            self._enabled_channels.append(channel)
    
    def disable_channel(self, channel: NotificationChannel) -> None:
        """Disable a notification channel."""
        if channel in self._enabled_channels:
            self._enabled_channels.remove(channel)
    
    async def send_alert(self, alert: Alert) -> Dict[str, Any]:
        """Send alert notification to all enabled channels."""
        results = {}
        
        for channel in self._enabled_channels:
            try:
                if channel == NotificationChannel.SLACK:
                    result = await self._send_slack(alert)
                elif channel == NotificationChannel.TEAMS:
                    result = await self._send_teams(alert)
                elif channel == NotificationChannel.DISCORD:
                    result = await self._send_discord(alert)
                elif channel == NotificationChannel.WEBHOOK:
                    result = await self._send_webhook(alert)
                else:
                    result = {"success": False, "error": f"Unknown channel: {channel}"}
                
                results[channel.value] = result
            except Exception as e:
                results[channel.value] = {"success": False, "error": str(e)}
        
        return results
    
    async def _send_slack(self, alert: Alert) -> Dict[str, Any]:
        """Send alert to Slack."""
        config = self._channels.get(NotificationChannel.SLACK, {})
        webhook_url = config.get("webhook_url")
        
        if not webhook_url:
            return {"success": False, "error": "Slack webhook not configured"}
        
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "🔴",
            AlertSeverity.CRITICAL: "🚨",
        }
        
        payload = {
            "text": f"{severity_emoji.get(alert.severity, '🔔')} *Alert: {alert.rule_name}*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔔 Alert: {alert.rule_name}",
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Severity:*\n{alert.severity.value}"},
                        {"type": "mrkdwn", "text": f"*Metric:*\n{alert.metric}"},
                        {"type": "mrkdwn", "text": f"*Value:*\n{alert.value:.2f}"},
                        {"type": "mrkdwn", "text": f"*Threshold:*\n{alert.threshold:.2f}"},
                    ]
                },
            ]
        }
        
        if alert.root_cause_analysis:
            payload["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Root Cause Analysis:*\n{alert.root_cause_analysis}"
                }
            })
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            return {"success": response.status_code == 200}
    
    async def _send_teams(self, alert: Alert) -> Dict[str, Any]:
        """Send alert to Microsoft Teams."""
        config = self._channels.get(NotificationChannel.TEAMS, {})
        webhook_url = config.get("webhook_url")
        
        if not webhook_url:
            return {"success": False, "error": "Teams webhook not configured"}
        
        color = {
            AlertSeverity.INFO: "0078D7",
            AlertSeverity.WARNING: "FFB900",
            AlertSeverity.ERROR: "D13438",
            AlertSeverity.CRITICAL: "A4262C",
        }.get(alert.severity, "0078D7")
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"Alert: {alert.rule_name}",
            "sections": [
                {
                    "activityTitle": f"🔔 Alert: {alert.rule_name}",
                    "facts": [
                        {"name": "Severity", "value": alert.severity.value},
                        {"name": "Metric", "value": alert.metric},
                        {"name": "Value", "value": f"{alert.value:.2f}"},
                        {"name": "Threshold", "value": f"{alert.threshold:.2f}"},
                    ]
                }
            ]
        }
        
        if alert.root_cause_analysis:
            payload["sections"].append({
                "activityTitle": "Root Cause Analysis",
                "text": alert.root_cause_analysis
            })
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            return {"success": response.status_code == 200}
    
    async def _send_discord(self, alert: Alert) -> Dict[str, Any]:
        """Send alert to Discord."""
        config = self._channels.get(NotificationChannel.DISCORD, {})
        webhook_url = config.get("webhook_url")
        
        if not webhook_url:
            return {"success": False, "error": "Discord webhook not configured"}
        
        color = {
            AlertSeverity.INFO: 3447003,
            AlertSeverity.WARNING: 16776960,
            AlertSeverity.ERROR: 15158332,
            AlertSeverity.CRITICAL: 10038562,
        }.get(alert.severity, 3447003)
        
        embed = {
            "title": f"🔔 Alert: {alert.rule_name}",
            "color": color,
            "fields": [
                {"name": "Severity", "value": alert.severity.value, "inline": True},
                {"name": "Metric", "value": alert.metric, "inline": True},
                {"name": "Value", "value": f"{alert.value:.2f}", "inline": True},
                {"name": "Threshold", "value": f"{alert.threshold:.2f}", "inline": True},
            ]
        }
        
        if alert.root_cause_analysis:
            embed["fields"].append({
                "name": "Root Cause Analysis",
                "value": alert.root_cause_analysis
            })
        
        payload = {"embeds": [embed]}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            return {"success": response.status_code == 204}
    
    async def _send_webhook(self, alert: Alert) -> Dict[str, Any]:
        """Send alert to generic webhook."""
        config = self._channels.get(NotificationChannel.WEBHOOK, {})
        webhook_url = config.get("url")
        
        if not webhook_url:
            return {"success": False, "error": "Webhook URL not configured"}
        
        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "metric": alert.metric,
            "value": alert.value,
            "threshold": alert.threshold,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "triggered_at": alert.triggered_at.isoformat(),
            "root_cause_analysis": alert.root_cause_analysis,
            "recommendations": alert.recommendations,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload)
            return {"success": response.status_code in [200, 201, 204]}


class AIAlertAnalyzer:
    """AI-powered root cause analysis for alerts."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
    
    async def analyze(self, alert: Alert, context: Optional[Dict] = None) -> str:
        """Analyze alert and generate root cause analysis."""
        if self.openai_api_key:
            return await self._ai_analyze(alert, context)
        else:
            return self._rule_based_analysis(alert, context)
    
    async def _ai_analyze(self, alert: Alert, context: Optional[Dict]) -> str:
        """Use OpenAI for analysis."""
        prompt = f"""
Analyze the following alert and provide a root cause analysis:

Alert: {alert.rule_name}
Metric: {alert.metric}
Value: {alert.value:.2f}
Threshold: {alert.threshold:.2f}
Severity: {alert.severity.value}

Context: {json.dumps(context) if context else 'No additional context'}

Provide a brief root cause analysis (2-3 sentences max).
"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            
            return response.choices[0].message.content
        except ImportError:
            return self._rule_based_analysis(alert, context)
    
    def _rule_based_analysis(self, alert: Alert, context: Optional[Dict]) -> str:
        """Rule-based analysis when AI is not available."""
        if "error" in alert.metric.lower() or "5xx" in alert.metric:
            return (
                f"Detected {alert.severity.value} level error rate on {alert.metric}. "
                f"This may indicate a service outage or internal server error. "
                f"Check service logs for more details."
            )
        elif "latency" in alert.metric.lower():
            return (
                f"High latency detected on {alert.metric}. "
                f"Consider checking for resource constraints or network issues."
            )
        else:
            return (
                f"Alert triggered for {alert.metric} exceeding threshold of {alert.threshold}. "
                f"Review recent changes and service health."
            )


class AlertManager:
    """Main alert manager combining rules, notifications, and AI."""
    
    def __init__(self):
        self.engine = AlertRuleEngine()
        self.notifier = NotificationManager()
        self.analyzer = AIAlertAnalyzer()
        self._active_alerts: Dict[str, Alert] = {}
        self._lock = threading.Lock()
        
        self.engine.on_alert(self._handle_alert)
    
    async def _handle_alert(self, alert: Alert) -> None:
        """Handle a triggered alert."""
        with self._lock:
            self._active_alerts[alert.id] = alert
        
        rca = await self.analyzer.analyze(alert, alert.metadata)
        alert.root_cause_analysis = rca
        
        await self.notifier.send_alert(alert)
    
    def create_rule(
        self,
        name: str,
        metric: str,
        threshold: float,
        condition: str = "gt",
        severity: AlertSeverity = AlertSeverity.WARNING,
    ) -> AlertRule:
        """Create an alert rule."""
        rule = AlertRule(
            name=name,
            metric=metric,
            threshold=threshold,
            condition=condition,
            severity=severity,
        )
        self.engine.add_rule(rule)
        return rule
    
    def configure_notification(
        self,
        channel: NotificationChannel,
        config: Dict[str, Any],
    ) -> None:
        """Configure a notification channel."""
        self.notifier.configure_channel(channel, config)
    
    async def process_metric(self, metric_name: str, value: float, metadata: Optional[Dict] = None) -> List[Alert]:
        """Process a metric through the alert engine."""
        return self.engine.process_metric(metric_name, value, metadata)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self._active_alerts.values())
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                return True
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                return True
            return False


_global_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get global alert manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = AlertManager()
    return _global_manager
