"""Tests for capture_filter module."""

import re
import pytest
from datetime import datetime

from socialseed_e2e.shadow_runner.capture_filter import (
    FilterRule,
    CaptureFilter,
    SmartFilter,
)
from socialseed_e2e.shadow_runner.traffic_interceptor import (
    CapturedRequest,
    CapturedResponse,
    CapturedInteraction,
)


class TestFilterRule:
    """Test suite for FilterRule dataclass."""

    def test_filter_rule_creation(self):
        """Test creating a FilterRule instance."""
        rule = FilterRule(
            name="health_check_filter",
            description="Filter out health check requests",
            path_patterns=[re.compile(r"/health")],
            action="exclude",
        )

        assert rule.name == "health_check_filter"
        assert rule.description == "Filter out health check requests"
        assert rule.action == "exclude"
        assert rule.active is True

    def test_filter_rule_matches(self):
        """Test rule pattern matching."""
        rule = FilterRule(
            name="test_rule",
            description="Test rule",
            path_patterns=[re.compile(r"/api/.*")],
            action="exclude",
        )

        interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/users"),
            response=CapturedResponse(status_code=200),
        )

        assert rule.matches(interaction) is True

        interaction2 = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/health"),
            response=CapturedResponse(status_code=200),
        )

        assert rule.matches(interaction2) is False

    def test_filter_rule_inactive(self):
        """Test that inactive rules don't match."""
        rule = FilterRule(
            name="inactive_rule",
            description="Inactive rule",
            path_patterns=[re.compile(r"/api/.*")],
            action="exclude",
            active=False,
        )

        interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/users"),
            response=CapturedResponse(status_code=200),
        )

        assert rule.matches(interaction) is False

    def test_filter_rule_with_methods(self):
        """Test rule with method matching."""
        rule = FilterRule(
            name="post_only",
            description="POST only",
            methods={"POST"},
            action="exclude",
        )

        post_interaction = CapturedInteraction(
            request=CapturedRequest(method="POST", path="/api/users"),
            response=CapturedResponse(status_code=201),
        )

        get_interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/users"),
            response=CapturedResponse(status_code=200),
        )

        assert rule.matches(post_interaction) is True
        assert rule.matches(get_interaction) is False


class TestCaptureFilter:
    """Test suite for CaptureFilter class."""

    def test_capture_filter_creation(self):
        """Test creating a CaptureFilter instance."""
        cf = CaptureFilter()

        assert len(cf.rules) >= 0  # May have default rules
        assert cf.enabled is True

    def test_add_rule(self):
        """Test adding a custom rule."""
        cf = CaptureFilter()
        initial_count = len(cf.rules)

        rule = FilterRule(
            name="custom_rule",
            description="Custom rule",
            path_patterns=[re.compile(r"/custom")],
            action="exclude",
        )

        cf.add_rule(rule)

        assert len(cf.rules) == initial_count + 1

    def test_should_capture_health_check(self):
        """Test that health checks are filtered out."""
        cf = CaptureFilter()

        interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/health"),
            response=CapturedResponse(status_code=200),
        )

        result = cf.should_capture(interaction)

        assert result is False

    def test_should_capture_api_request(self):
        """Test that API requests are captured."""
        cf = CaptureFilter()

        request = CapturedRequest(
            method="POST",
            path="/api/users",
            headers={"Content-Type": "application/json"},
            body='{"name": "test"}',
        )
        interaction = CapturedInteraction(
            request=request,
            response=CapturedResponse(status_code=201),
        )

        result = cf.should_capture(interaction)

        assert result is True

    def test_should_capture_static_asset(self):
        """Test that static assets are filtered out."""
        cf = CaptureFilter()

        request = CapturedRequest(method="GET", path="/static/main.js")
        interaction = CapturedInteraction(
            request=request,
            response=CapturedResponse(status_code=200),
        )

        result = cf.should_capture(interaction)

        assert result is False

    def test_filter_interactions(self):
        """Test filtering a list of interactions."""
        cf = CaptureFilter()

        interactions = [
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/health"),
                response=CapturedResponse(status_code=200),
            ),
            CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/users"),
                response=CapturedResponse(status_code=201),
            ),
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/static/main.js"),
                response=CapturedResponse(status_code=200),
            ),
        ]

        filtered = cf.filter_interactions(interactions)

        assert len(filtered) == 1
        assert filtered[0].request.path == "/api/users"


class TestSmartFilter:
    """Test suite for SmartFilter class."""

    def test_smart_filter_creation(self):
        """Test creating a SmartFilter instance."""
        sf = SmartFilter()

        assert sf.endpoint_frequency == {}
        assert sf.noise_threshold == 0.5

    def test_record_interaction(self):
        """Test recording an interaction."""
        sf = SmartFilter()

        interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/users"),
            response=CapturedResponse(status_code=200),
        )

        sf.record_interaction(interaction)

        key = "GET /api/users"
        assert key in sf.endpoint_frequency
        assert sf.endpoint_frequency[key] == 1

    def test_record_multiple_interactions(self):
        """Test recording multiple interactions to same endpoint."""
        sf = SmartFilter()

        for _ in range(5):
            interaction = CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/users"),
                response=CapturedResponse(status_code=200),
            )
            sf.record_interaction(interaction)

        key = "GET /api/users"
        assert sf.endpoint_frequency[key] == 5

    def test_is_noise_high_frequency(self):
        """Test that high-frequency requests are considered noise."""
        sf = SmartFilter()

        # Record many requests to same endpoint
        for _ in range(100):
            interaction = CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/poll"),
                response=CapturedResponse(status_code=200),
            )
            sf.record_interaction(interaction)

        # Record some other requests
        for _ in range(10):
            interaction = CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/users"),
                response=CapturedResponse(status_code=201),
            )
            sf.record_interaction(interaction)

        poll_interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/poll"),
            response=CapturedResponse(status_code=200),
        )

        assert sf.is_noise(poll_interaction) is True

    def test_is_noise_normal_frequency(self):
        """Test that normal-frequency requests are not noise."""
        sf = SmartFilter()

        # Record some interactions
        for _ in range(10):
            interaction = CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/users"),
                response=CapturedResponse(status_code=200),
            )
            sf.record_interaction(interaction)

        test_interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/users"),
            response=CapturedResponse(status_code=200),
        )

        assert sf.is_noise(test_interaction) is False

    def test_should_capture_with_smart_filtering(self):
        """Test smart filtering in should_capture."""
        sf = SmartFilter()

        # Record many polling requests
        for _ in range(100):
            interaction = CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/poll"),
                response=CapturedResponse(status_code=200),
            )
            sf.record_interaction(interaction)

        # Test that poll request is filtered
        poll_interaction = CapturedInteraction(
            request=CapturedRequest(method="GET", path="/api/poll"),
            response=CapturedResponse(status_code=200),
        )

        assert sf.should_capture(poll_interaction) is False

    def test_get_statistics(self):
        """Test getting frequency statistics."""
        sf = SmartFilter()

        # Record some interactions
        for _ in range(10):
            sf.record_interaction(
                CapturedInteraction(
                    request=CapturedRequest(method="GET", path="/api/users"),
                    response=CapturedResponse(status_code=200),
                )
            )

        for _ in range(5):
            sf.record_interaction(
                CapturedInteraction(
                    request=CapturedRequest(method="POST", path="/api/users"),
                    response=CapturedResponse(status_code=201),
                )
            )

        stats = sf.get_statistics()

        assert stats["total_interactions"] == 15
        assert stats["unique_endpoints"] == 2
        assert "GET /api/users" in stats["top_endpoints"]


class TestFilterIntegration:
    """Integration tests for filtering."""

    def test_complex_filtering_scenario(self):
        """Test complex filtering with multiple rules and smart filtering."""
        cf = CaptureFilter()

        interactions = [
            # Health check - should be filtered
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/health"),
                response=CapturedResponse(status_code=200),
            ),
            # Static asset - should be filtered
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/static/main.js"),
                response=CapturedResponse(status_code=200),
            ),
            # API request - should be captured
            CapturedInteraction(
                request=CapturedRequest(method="POST", path="/api/users"),
                response=CapturedResponse(status_code=201),
            ),
            # GET users - should be captured
            CapturedInteraction(
                request=CapturedRequest(method="GET", path="/api/users"),
                response=CapturedResponse(status_code=200),
            ),
        ]

        filtered = cf.filter_interactions(interactions)

        # Should have only the two API requests
        assert len(filtered) == 2
        assert all(i.request.path.startswith("/api/") for i in filtered)
