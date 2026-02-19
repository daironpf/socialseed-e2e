"""Tests for Mock Engine Module.

This module tests the API mocking features.
"""

import pytest

from socialseed_e2e.mocks import (
    ContractMockGenerator,
    DynamicMock,
    MockResponse,
    MockRule,
    MockServer,
    MockSuite,
    MockType,
    ResponseMode,
    ScenarioSimulator,
)


class TestMockResponse:
    """Tests for MockResponse."""

    def test_initialization(self):
        """Test mock response initialization."""
        response = MockResponse(status_code=200, body={"test": "value"})
        assert response.status_code == 200
        assert response.body == {"test": "value"}

    def test_with_delay(self):
        """Test response with delay."""
        response = MockResponse(status_code=200, delay_ms=1000)
        assert response.delay_ms == 1000


class TestMockRule:
    """Tests for MockRule."""

    def test_initialization(self):
        """Test mock rule initialization."""
        rule = MockRule(path="/api/users", method="GET")
        assert rule.path == "/api/users"
        assert rule.method == "GET"


class TestDynamicMock:
    """Tests for DynamicMock."""

    def test_initialization(self):
        """Test dynamic mock initialization."""
        rule = MockRule(path="/api/users", method="GET")
        response = MockResponse(status_code=200, body={})
        mock = DynamicMock(rule=rule, response=response)

        assert mock.rule.path == "/api/users"
        assert mock.call_count == 0


class TestMockServer:
    """Tests for MockServer."""

    def test_initialization(self):
        """Test mock server initialization."""
        server = MockServer(port=8080)
        assert server.port == 8080
        assert len(server.mocks) == 0

    def test_add_mock(self):
        """Test adding mock."""
        server = MockServer()
        server.add_mock("/api/users", "GET", [{"id": "1", "name": "John"}])

        assert len(server.mocks) == 1
        assert "GET:/api/users" in server.mocks

    def test_get_mock(self):
        """Test getting mock."""
        server = MockServer()
        server.add_mock("/api/users", "GET", [{"id": "1", "name": "John"}])

        mock = server.get_mock("GET", "/api/users")
        assert mock is not None
        assert mock.status_code == 200

    def test_get_mock_not_found(self):
        """Test getting non-existent mock."""
        server = MockServer()
        mock = server.get_mock("GET", "/api/unknown")
        assert mock is None

    def test_add_scenario(self):
        """Test adding scenario."""
        server = MockServer()
        server.add_scenario(
            "error_test",
            [
                {"status_code": 500, "body": {"error": "Error 1"}},
                {"status_code": 500, "body": {"error": "Error 2"}},
            ],
        )

        assert "error_test" in server.scenarios
        assert len(server.scenarios["error_test"]) == 2

    def test_set_scenario(self):
        """Test setting active scenario."""
        server = MockServer()
        server.add_scenario(
            "test_scenario",
            [
                {"status_code": 200, "body": {"data": "test"}},
            ],
        )
        server.set_scenario("test_scenario")

        assert server.current_scenario == "test_scenario"

    def test_get_stats(self):
        """Test getting statistics."""
        server = MockServer()
        server.add_mock("/api/users", "GET", [])

        stats = server.get_stats()
        assert stats["total_mocks"] == 1

    def test_reset(self):
        """Test resetting server."""
        server = MockServer()
        server.add_mock("/api/users", "GET", [])
        server.reset()

        assert server.current_scenario is None


class TestScenarioSimulator:
    """Tests for ScenarioSimulator."""

    def test_initialization(self):
        """Test simulator initialization."""
        simulator = ScenarioSimulator()
        assert len(simulator.scenarios) == 0

    def test_add_error_scenario(self):
        """Test adding error scenario."""
        simulator = ScenarioSimulator()
        simulator.add_error_scenario("server_error", 500, "Internal Error")

        scenario = simulator.get_scenario("server_error")
        assert scenario is not None
        assert scenario.status_code == 500

    def test_add_latency_scenario(self):
        """Test adding latency scenario."""
        simulator = ScenarioSimulator()
        simulator.add_latency_scenario("slow", 5000)

        scenario = simulator.get_scenario("slow")
        assert scenario.delay_ms == 5000

    def test_add_rate_limit_scenario(self):
        """Test adding rate limit scenario."""
        simulator = ScenarioSimulator()
        simulator.add_rate_limit_scenario("rate_limited", 429, 60)

        scenario = simulator.get_scenario("rate_limited")
        assert scenario.status_code == 429

    def test_list_scenarios(self):
        """Test listing scenarios."""
        simulator = ScenarioSimulator()
        simulator.add_error_scenario("error1", 500, "Error")
        simulator.add_latency_scenario("latency", 1000)

        scenarios = simulator.list_scenarios()
        assert len(scenarios) == 2
        assert "error1" in scenarios
        assert "latency" in scenarios


class TestContractMockGenerator:
    """Tests for ContractMockGenerator."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = ContractMockGenerator()
        assert len(generator.endpoints) == 0

    def test_generate_from_openapi(self):
        """Test generating from OpenAPI spec."""
        generator = ContractMockGenerator()
        spec = {
            "paths": {
                "/api/users": {
                    "get": {"summary": "Get users", "responses": {"200": {}}}
                }
            }
        }

        generator.generate_from_openapi(spec)
        assert len(generator.endpoints) == 1

    def test_get_mocks(self):
        """Test getting mocks."""
        generator = ContractMockGenerator()
        spec = {
            "paths": {"/api/users": {"get": {"summary": "Get users", "responses": {}}}}
        }

        generator.generate_from_openapi(spec)
        mocks = generator.get_mocks()

        assert len(mocks) == 1
        assert mocks[0]["path"] == "/api/users"


class TestMockSuite:
    """Tests for MockSuite."""

    def test_initialization(self):
        """Test suite initialization."""
        suite = MockSuite()
        assert len(suite.servers) == 0

    def test_create_server(self):
        """Test creating server."""
        suite = MockSuite()
        server = suite.create_server(port=9000)

        assert server.port == 9000
        assert len(suite.servers) == 1

    def test_create_simulator(self):
        """Test creating simulator."""
        suite = MockSuite()
        simulator = suite.create_simulator()

        assert isinstance(simulator, ScenarioSimulator)
        assert len(suite.simulators) == 1

    def test_add_get_mock(self):
        """Test adding GET mock."""
        suite = MockSuite()
        server = suite.create_server()
        suite.add_get_mock(server, "/api/users", [{"id": "1"}])

        mock = server.get_mock("GET", "/api/users")
        assert mock is not None

    def test_add_post_mock(self):
        """Test adding POST mock."""
        suite = MockSuite()
        server = suite.create_server()
        suite.add_post_mock(server, "/api/users", {"id": "1", "name": "John"})

        mock = server.get_mock("POST", "/api/users")
        assert mock.status_code == 201

    def test_get_all_stats(self):
        """Test getting all stats."""
        suite = MockSuite()
        server = suite.create_server()
        server.add_mock("/api/users", "GET", [])

        stats = suite.get_all_stats()
        assert "server_0" in stats


class TestResponseMode:
    """Tests for ResponseMode enum."""

    def test_modes(self):
        """Test response modes."""
        assert ResponseMode.SEQUENTIAL.value == "sequential"
        assert ResponseMode.RANDOM.value == "random"
        assert ResponseMode.CONDITIONAL.value == "conditional"


class TestMockType:
    """Tests for MockType enum."""

    def test_types(self):
        """Test mock types."""
        assert MockType.DYNAMIC.value == "dynamic"
        assert MockType.STATIC.value == "static"
        assert MockType.SCENARIO.value == "scenario"
        assert MockType.CONTRACT.value == "contract"
