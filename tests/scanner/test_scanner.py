"""Tests for scanner package - Endpoint and Schema scanning."""

import pytest
import tempfile
import os
from pathlib import Path

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import scanner modules
from socialseed_e2e.scanner.endpoint_scanner import EndpointScanner
from socialseed_e2e.scanner.schema_scanner import SchemaScanner
from scanner.traffic_scheduler import (
    TrafficScheduler,
    SchedulerConfig,
    ScheduleType,
    RequestPriority,
    ScheduledRequest
)


class TestEndpointScanner:
    """Test cases for EndpointScanner."""
    
    def test_scanner_initialization(self):
        """Test scanner can be initialized."""
        scanner = EndpointScanner(".")
        assert scanner is not None
        assert scanner.endpoints == []
    
    def test_scan_empty_directory(self):
        """Test scanning a directory with no source files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = EndpointScanner(tmpdir)
            endpoints = scanner.scan()
            assert endpoints == []
    
    def test_scan_java_spring_boot(self):
        """Test scanning Java Spring Boot project."""
        # Test with the real auth-service
        auth_service_path = Path("D:/.dev/proyectos/SocialSeed/services/auth-service")
        
        if not auth_service_path.exists():
            pytest.skip("Auth service not found")
        
        scanner = EndpointScanner(str(auth_service_path))
        endpoints = scanner.scan()
        
        # Should find endpoints
        assert len(endpoints) > 0
        
        # Check endpoint structure
        for ep in endpoints:
            assert "path" in ep
            assert "method" in ep
            assert "language" in ep
            assert "framework" in ep
    
    def test_extract_class_mapping(self):
        """Test class-level request mapping extraction."""
        content = '''
package com.example;

@RestController
@RequestMapping("/api/users")
public class UserController {
    // ...
}
'''
        scanner = EndpointScanner(".")
        mapping = scanner._extract_class_mapping(content)
        assert mapping == "/api/users"
    
    def test_extract_method_mappings(self):
        """Test method-level mapping extraction."""
        content = '''
@RestController
public class UserController {
    @GetMapping("/users")
    public List<User> getUsers() { ... }
    
    @PostMapping("/users")
    public User createUser(@RequestBody User user) { ... }
    
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) { ... }
}
'''
        scanner = EndpointScanner(".")
        methods = scanner._extract_method_mappings(content)
        
        # Should find 3 methods
        assert len(methods) >= 3
        
        # Check method types
        methods_by_type = {m['method'] for m in methods}
        assert 'GET' in methods_by_type
        assert 'POST' in methods_by_type


class TestSchemaScanner:
    """Test cases for SchemaScanner."""
    
    def test_scanner_initialization(self):
        """Test schema scanner can be initialized."""
        scanner = SchemaScanner(".")
        assert scanner is not None
        assert scanner.dtos == []
    
    def test_scan_empty_directory(self):
        """Test scanning a directory with no source files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = SchemaScanner(tmpdir)
            dtos = scanner.scan()
            assert dtos == []
    
    def test_scan_java_entities(self):
        """Test scanning Java entity/DTO classes."""
        auth_service_path = Path("D:/.dev/proyectos/SocialSeed/services/auth-service")
        
        if not auth_service_path.exists():
            pytest.skip("Auth service not found")
        
        scanner = SchemaScanner(str(auth_service_path))
        dtos = scanner.scan()
        
        # Should find DTOs
        assert len(dtos) > 0
        
        # Check DTO structure
        for dto in dtos:
            assert isinstance(dto, DTOInfo)
            assert dto.name
            assert dto.language
    
    def test_dtoinfo_creation(self):
        """Test DTOInfo can be created."""
        dto = DTOInfo(
            name="TestDTO",
            fields=[
                FieldInfo(name="id", type="UUID", required=True),
                FieldInfo(name="name", type="String", required=True),
                FieldInfo(name="email", type="String", required=False)
            ],
            language="Java",
            framework="Spring Boot"
        )
        
        assert dto.name == "TestDTO"
        assert len(dto.fields) == 3
        assert dto.fields[0].required == True
        assert dto.fields[2].required == False


class TestTrafficScheduler:
    """Test cases for TrafficScheduler."""
    
    def test_scheduler_config_defaults(self):
        """Test default scheduler configuration."""
        config = SchedulerConfig()
        
        assert config.schedule_type == ScheduleType.FIXED_RATE
        assert config.requests_per_minute == 100
        assert config.concurrent_workers == 5
    
    def test_scheduler_creation(self):
        """Test scheduler can be created."""
        scheduler = TrafficScheduler(
            base_url="http://localhost:8085",
            config=SchedulerConfig(requests_per_minute=10)
        )
        
        assert scheduler.base_url == "http://localhost:8085"
        assert scheduler.total_scheduled == 0
        assert scheduler.total_completed == 0
    
    def test_scheduled_request_creation(self):
        """Test ScheduledRequest can be created."""
        request = ScheduledRequest(
            endpoint="/api/users",
            method="GET",
            priority=RequestPriority.NORMAL
        )
        
        assert request.endpoint == "/api/users"
        assert request.method == "GET"
        assert request.priority == RequestPriority.NORMAL
        assert request.id  # Should have an ID
    
    def test_priority_queues_initialization(self):
        """Test priority queues are properly initialized."""
        scheduler = TrafficScheduler("http://localhost:8085")
        
        assert RequestPriority.CRITICAL in scheduler._priority_queues
        assert RequestPriority.HIGH in scheduler._priority_queues
        assert RequestPriority.NORMAL in scheduler._priority_queues
        assert RequestPriority.LOW in scheduler._priority_queues
    
    def test_add_endpoints(self):
        """Test adding endpoints to scheduler."""
        scheduler = TrafficScheduler("http://localhost:8085")
        
        endpoints = [
            {"path": "/api/users", "method": "GET"},
            {"path": "/api/users", "method": "POST"},
            {"path": "/api/auth/login", "method": "POST"}
        ]
        
        scheduler.add_endpoints(endpoints)
        
        assert len(scheduler.endpoints) == 3
    
    def test_select_endpoint(self):
        """Test endpoint selection."""
        scheduler = TrafficScheduler("http://localhost:8085")
        
        endpoints = [
            {"path": "/api/users", "method": "GET"},
            {"path": "/api/auth/login", "method": "POST"}
        ]
        
        scheduler.add_endpoints(endpoint for endpoint in endpoints)
        
        # Should return a dict
        selected = scheduler._select_endpoint()
        assert selected is not None
        assert "path" in selected
    
    def test_stats_tracking(self):
        """Test statistics tracking."""
        scheduler = TrafficScheduler("http://localhost:8085")
        
        stats = scheduler.get_stats()
        
        assert stats["running"] == False
        assert stats["total_scheduled"] == 0
        assert stats["total_completed"] == 0
        assert stats["total_failed"] == 0


class TestScheduleTypes:
    """Test cases for ScheduleType enum."""
    
    def test_all_schedule_types_exist(self):
        """Test all schedule types are defined."""
        assert ScheduleType.FIXED_RATE.value == "fixed_rate"
        assert ScheduleType.INTERVAL.value == "interval"
        assert ScheduleType.RANDOM.value == "random"
        assert ScheduleType.CRON.value == "cron"
        assert ScheduleType.BURST.value == "burst"


class TestRequestPriority:
    """Test cases for RequestPriority enum."""
    
    def test_all_priorities_exist(self):
        """Test all priorities are defined."""
        assert RequestPriority.LOW.value == 1
        assert RequestPriority.NORMAL.value == 2
        assert RequestPriority.HIGH.value == 3
        assert RequestPriority.CRITICAL.value == 4


# Integration test marker
@pytest.mark.integration
class TestScannerIntegration:
    """Integration tests for scanner package."""
    
    def test_full_scan_workflow(self):
        """Test full scanning workflow."""
        auth_service_path = Path("D:/.dev/proyectos/SocialSeed/services/auth-service")
        
        if not auth_service_path.exists():
            pytest.skip("Auth service not found")
        
        # Scan endpoints
        endpoint_scanner = EndpointScanner(str(auth_service_path))
        endpoints = endpoint_scanner.scan()
        
        # Scan schemas
        schema_scanner = SchemaScanner(str(auth_service_path))
        schemas = schema_scanner.scan()
        
        # Should have both
        assert len(endpoints) > 0
        assert len(schemas) > 0
        
        # Endpoints should be from auth service
        auth_endpoints = [ep for ep in endpoints if ep.get('path', '').startswith('/auth')]
        assert len(auth_endpoints) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])