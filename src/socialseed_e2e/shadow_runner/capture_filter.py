"""Capture Filter for Shadow Runner.

This module provides intelligent filtering to remove noise from captured traffic.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Pattern, Set

from socialseed_e2e.shadow_runner.traffic_interceptor import CapturedInteraction


@dataclass
class FilterRule:
    """A filter rule for captured traffic."""

    name: str
    description: str
    priority: int = 0  # Higher priority = applied first
    active: bool = True

    # Match conditions
    path_patterns: List[Pattern] = field(default_factory=list)
    methods: Set[str] = field(default_factory=set)
    status_codes: Set[int] = field(default_factory=set)
    header_patterns: Dict[str, Pattern] = field(default_factory=dict)
    content_type_patterns: List[Pattern] = field(default_factory=list)

    # Actions
    action: str = "exclude"  # "exclude" or "include"

    def matches(self, interaction: CapturedInteraction) -> bool:
        """Check if interaction matches this rule.

        Args:
            interaction: Captured interaction

        Returns:
            True if matches
        """
        # Inactive rules never match
        if not self.active:
            return False

        request = interaction.request

        # Check path patterns
        if self.path_patterns:
            path_matched = any(pattern.search(request.path) for pattern in self.path_patterns)
            if not path_matched:
                return False

        # Check methods
        if self.methods and request.method not in self.methods:
            return False

        # Check status codes (if response exists)
        if self.status_codes and interaction.response:
            if interaction.response.status_code not in self.status_codes:
                return False

        # Check headers
        for header_name, pattern in self.header_patterns.items():
            header_value = request.headers.get(header_name, "")
            if not pattern.search(header_value):
                return False

        # Check content-type
        if self.content_type_patterns:
            content_type = request.headers.get("Content-Type", "")
            content_type_matched = any(
                pattern.search(content_type) for pattern in self.content_type_patterns
            )
            if not content_type_matched:
                return False

        return True


class CaptureFilter:
    """Filters captured traffic to remove noise."""

    # Default patterns for common noise
    DEFAULT_EXCLUDE_PATHS = [
        r"^/health",  # Health checks
        r"^/ready",  # Readiness checks
        r"^/alive",  # Liveness checks
        r"^/metrics",  # Metrics endpoints
        r"^/static",  # Static assets
        r"^/assets",  # Assets
        r".*\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$",  # Static files
        r"^/favicon",  # Favicon
        r"^/robots\.txt",  # Robots.txt
        r"^/sitemap",  # Sitemap
    ]

    DEFAULT_INCLUDE_METHODS = {
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
    }

    DEFAULT_EXCLUDE_CONTENT_TYPES = [
        r"text/css",
        r"text/javascript",
        r"application/javascript",
        r"image/.*",
        r"font/.*",
    ]

    def __init__(self):
        """Initialize the capture filter."""
        self.enabled = True
        self.rules: List[FilterRule] = []
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """Set up default filtering rules."""
        # Rule 1: Exclude health checks and static assets
        health_check_rule = FilterRule(
            name="exclude_health_checks",
            description="Exclude health checks, static assets, and monitoring endpoints",
            priority=100,
            path_patterns=[re.compile(pattern) for pattern in self.DEFAULT_EXCLUDE_PATHS],
            action="exclude",
        )
        self.add_rule(health_check_rule)

        # Rule 2: Include only standard HTTP methods
        methods_rule = FilterRule(
            name="include_http_methods",
            description="Include only standard HTTP methods",
            priority=90,
            methods=self.DEFAULT_INCLUDE_METHODS,
            action="include",
        )
        self.add_rule(methods_rule)

        # Rule 3: Exclude static content types
        content_type_rule = FilterRule(
            name="exclude_static_content",
            description="Exclude static content types (CSS, JS, images, fonts)",
            priority=80,
            content_type_patterns=[
                re.compile(pattern) for pattern in self.DEFAULT_EXCLUDE_CONTENT_TYPES
            ],
            action="exclude",
        )
        self.add_rule(content_type_rule)

        # Rule 4: Exclude successful OPTIONS requests (CORS preflight)
        cors_rule = FilterRule(
            name="exclude_cors_preflight",
            description="Exclude CORS preflight OPTIONS requests",
            priority=70,
            methods={"OPTIONS"},
            action="exclude",
        )
        self.add_rule(cors_rule)

    def add_rule(self, rule: FilterRule) -> None:
        """Add a filter rule.

        Args:
            rule: Filter rule to add
        """
        self.rules.append(rule)
        # Sort by priority (higher first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a filter rule.

        Args:
            rule_name: Name of rule to remove

        Returns:
            True if removed
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False

    def enable_rule(self, rule_name: str) -> bool:
        """Enable a filter rule.

        Args:
            rule_name: Name of rule to enable

        Returns:
            True if enabled
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.active = True
                return True
        return False

    def disable_rule(self, rule_name: str) -> bool:
        """Disable a filter rule.

        Args:
            rule_name: Name of rule to disable

        Returns:
            True if disabled
        """
        for rule in self.rules:
            if rule.name == rule_name:
                rule.active = False
                return True
        return False

    def should_capture(self, interaction: CapturedInteraction) -> bool:
        """Determine if an interaction should be captured.

        Args:
            interaction: Captured interaction

        Returns:
            True if should be captured
        """
        # Default is to include
        should_include = True

        for rule in self.rules:
            if not rule.active:
                continue

            if rule.matches(interaction):
                if rule.action == "exclude":
                    return False
                elif rule.action == "include":
                    should_include = True

        return should_include

    def filter_interactions(
        self, interactions: List[CapturedInteraction]
    ) -> List[CapturedInteraction]:
        """Filter a list of interactions.

        Args:
            interactions: List of interactions

        Returns:
            Filtered list
        """
        return [i for i in interactions if self.should_capture(i)]

    def add_custom_exclude_path(self, path_pattern: str) -> None:
        """Add a custom path exclusion pattern.

        Args:
            path_pattern: Regex pattern for paths to exclude
        """
        rule = FilterRule(
            name=f"custom_exclude_{path_pattern}",
            description=f"Custom exclusion for {path_pattern}",
            priority=50,
            path_patterns=[re.compile(path_pattern)],
            action="exclude",
        )
        self.add_rule(rule)

    def add_custom_include_method(self, method: str) -> None:
        """Add a custom method to include.

        Args:
            method: HTTP method to include
        """
        # Check if rule exists
        for rule in self.rules:
            if rule.name == "include_http_methods":
                rule.methods.add(method.upper())
                return

        # Create new rule
        rule = FilterRule(
            name="include_http_methods",
            description="Include standard HTTP methods",
            priority=90,
            methods={method.upper()},
            action="include",
        )
        self.add_rule(rule)

    def get_active_rules(self) -> List[FilterRule]:
        """Get list of active filter rules.

        Returns:
            List of active rules
        """
        return [rule for rule in self.rules if rule.active]

    def get_statistics(self, interactions: List[CapturedInteraction]) -> Dict:
        """Get filtering statistics.

        Args:
            interactions: List of interactions

        Returns:
            Statistics dictionary
        """
        total = len(interactions)
        filtered = self.filter_interactions(interactions)
        filtered_count = len(filtered)

        # Count by rule
        rule_counts = {}
        for rule in self.rules:
            if not rule.active:
                continue
            count = sum(1 for i in interactions if rule.matches(i))
            rule_counts[rule.name] = count

        return {
            "total_captured": total,
            "after_filtering": filtered_count,
            "filtered_out": total - filtered_count,
            "filter_rate": (total - filtered_count) / total if total > 0 else 0,
            "active_rules": len(self.get_active_rules()),
            "matches_by_rule": rule_counts,
        }


class SmartFilter(CaptureFilter):
    """Smart filter with machine learning-like capabilities."""

    def __init__(self):
        """Initialize smart filter."""
        super().__init__()
        self.path_frequency: Dict[str, int] = {}
        self.endpoint_frequency: Dict[str, int] = {}
        self.response_time_threshold = 5000  # ms
        self.noise_threshold = 0.5

    def learn_from_interactions(self, interactions: List[CapturedInteraction]) -> None:
        """Learn patterns from interactions.

        Args:
            interactions: List of interactions
        """
        # Count path frequency
        for interaction in interactions:
            path = interaction.request.path
            self.path_frequency[path] = self.path_frequency.get(path, 0) + 1

        # Identify high-frequency paths (likely noise)
        avg_frequency = (
            sum(self.path_frequency.values()) / len(self.path_frequency)
            if self.path_frequency
            else 0
        )

        for path, count in self.path_frequency.items():
            if count > avg_frequency * 3:  # 3x average
                # Add exclusion rule for this path
                self.add_custom_exclude_path(re.escape(path))

    def record_interaction(self, interaction: CapturedInteraction) -> None:
        """Record an interaction for frequency tracking.

        Args:
            interaction: Captured interaction
        """
        key = f"{interaction.request.method} {interaction.request.path}"
        self.endpoint_frequency[key] = self.endpoint_frequency.get(key, 0) + 1

    def is_noise(self, interaction: CapturedInteraction) -> bool:
        """Check if interaction is considered noise based on frequency.

        Args:
            interaction: Captured interaction

        Returns:
            True if considered noise
        """
        key = f"{interaction.request.method} {interaction.request.path}"
        frequency = self.endpoint_frequency.get(key, 0)

        # Calculate total interactions
        total = sum(self.endpoint_frequency.values()) if self.endpoint_frequency else 0

        if total == 0:
            return False

        # Only consider noise if we have a significant number of interactions
        # and the endpoint dominates
        if total < 50:
            return False

        # Check if this endpoint's frequency exceeds the threshold ratio
        endpoint_ratio = frequency / total
        if endpoint_ratio > self.noise_threshold:
            return True

        return False

    def should_capture(self, interaction: CapturedInteraction) -> bool:
        """Smart filtering with additional heuristics.

        Args:
            interaction: Captured interaction

        Returns:
            True if should be captured
        """
        # Record interaction for frequency tracking
        self.record_interaction(interaction)

        # Apply base filtering
        if not super().should_capture(interaction):
            return False

        # Additional smart filters

        # Filter out very fast responses (likely cached/static)
        if interaction.response and interaction.response.latency_ms < 10:
            # Check if it's a GET request to a static-looking path
            if interaction.request.method == "GET":
                path = interaction.request.path
                if "." in path.split("/")[-1]:  # Has file extension
                    return False

        # Filter out error responses that are likely not user-initiated
        if interaction.response and interaction.response.status_code >= 500:
            # Only capture 5xx errors if they have a body (likely real errors)
            if not interaction.response.body:
                return False

        # Check if this interaction is considered noise
        if self.is_noise(interaction):
            return False

        return True

    def get_statistics(self, interactions=None) -> Dict:
        """Get frequency statistics.

        Args:
            interactions: Optional list of interactions (for compatibility with parent class)

        Returns:
            Statistics dictionary
        """
        total = sum(self.endpoint_frequency.values()) if self.endpoint_frequency else 0

        # Get top endpoints sorted by frequency
        sorted_endpoints = sorted(self.endpoint_frequency.items(), key=lambda x: x[1], reverse=True)
        top_endpoints = [endpoint for endpoint, count in sorted_endpoints[:10]]

        return {
            "total_interactions": total,
            "unique_endpoints": len(self.endpoint_frequency),
            "endpoint_frequency": self.endpoint_frequency.copy(),
            "top_endpoints": top_endpoints,
        }

    def get_smart_suggestions(self) -> List[str]:
        """Get suggestions for improving filters.

        Returns:
            List of suggestions
        """
        suggestions = []

        # Identify repetitive paths
        sorted_paths = sorted(self.path_frequency.items(), key=lambda x: x[1], reverse=True)

        if sorted_paths and sorted_paths[0][1] > 100:
            path, count = sorted_paths[0]
            suggestions.append(
                f"High-frequency path detected: {path} ({count} requests). "
                f"Consider adding exclusion rule."
            )

        return suggestions
