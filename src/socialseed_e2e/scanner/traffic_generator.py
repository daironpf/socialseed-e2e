"""
Traffic Generator Bot - Core implementation for generating structured traffic to microservices.
This implements Task EPIC-001-T03: Desarrollar el core del bot generador de tráfico utilizando los DTOs descubiertos.
"""

import asyncio
import random
import time
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import uuid

# Try to import playwright, handle gracefully if not available
try:
    from playwright.sync_api import sync_playwright, Page, APIResponse
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class RequestConfig:
    """Configuration for a request."""
    endpoint: str
    method: str
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    delay_ms: int = 0  # Delay before making request
    timeout_ms: int = 30000


@dataclass
class RequestResult:
    """Result of a request."""
    timestamp: datetime
    endpoint: str
    method: str
    status: int
    duration_ms: float
    success: bool
    response_body: Optional[str] = None
    error: Optional[str] = None


@dataclass
class TrafficStats:
    """Statistics for traffic generation."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_duration_ms: float = 0.0
    requests_per_minute: float = 0.0
    errors: Dict[str, int] = field(default_factory=dict)


class TrafficGeneratorBot:
    """
    Bot que se conecta a microservicios y genera tráfico estructurado.
    
    Usage:
        bot = TrafficGeneratorBot(
            base_url="http://localhost:8085",
            endpoints=endpoints,  # From endpoint_scanner
            schemas=schemas      # From schema_scanner
        )
        
        # Generate 100 requests per minute
        bot.start(requests_per_minute=100, duration_seconds=60)
    """
    
    def __init__(
        self,
        base_url: str,
        endpoints: List[Dict[str, Any]],
        schemas: List[Any],
        auth_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the traffic generator bot.
        
        Args:
            base_url: Base URL for the API
            endpoints: List of endpoint dictionaries from EndpointScanner
            schemas: List of DTOInfo objects from SchemaScanner
            auth_token: Optional authentication token
            headers: Optional additional headers
        """
        self.base_url = base_url.rstrip('/')
        self.endpoints = endpoints
        self.schemas = schemas
        self.auth_token = auth_token
        self.headers = headers or {"Content-Type": "application/json"}
        
        self.results: List[RequestResult] = []
        self.stats = TrafficStats()
        self._running = False
        self._playwright = None
        self._page = None
        self._scheduler = None
        
        # Build schema lookup
        self._schema_lookup = {s.name: s for s in schemas}
        
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = self.headers.copy()
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    def _generate_request_body(self, endpoint: str, method: str) -> Optional[Dict[str, Any]]:
        """Generate request body based on endpoint and DTOs."""
        
        # Try to find matching DTO based on endpoint path
        matching_schema = None
        
        for schema in self.schemas:
            # Simple heuristic: look for schema name in endpoint path
            schema_name_lower = schema.name.lower()
            endpoint_lower = endpoint.lower()
            
            if schema_name_lower in endpoint_lower or endpoint_lower.endswith(schema_name_lower):
                matching_schema = schema
                break
        
        if not matching_schema:
            # Generate generic body based on HTTP method
            if method in ['POST', 'PUT', 'PATCH']:
                return self._generate_generic_body()
            return None
        
        # Generate body from schema
        body = {}
        for field in matching_schema.fields:
            if field.required or random.random() > 0.3:
                body[field.name if not field.alias else field.alias] = self._generate_field_value(field)
        
        return body
    
    def _generate_field_value(self, field) -> Any:
        """Generate a value for a field based on its type."""
        field_type = field.type.lower()
        
        # Handle Optional types
        if 'optional' in field_type:
            if random.random() > 0.7:  # 30% chance of None
                return None
            field_type = field_type.replace('optional[', '').replace(']', '')
        
        # String types
        if 'str' in field_type or 'string' in field_type:
            if 'email' in field_type:
                return f"test_{uuid.uuid4().hex[:8]}@example.com"
            if 'username' in field_type or 'name' in field_type:
                return f"user_{uuid.uuid4().hex[:8]}"
            if 'password' in field_type:
                return "TestPassword123!"
            if 'description' in field_type or 'bio' in field_type:
                return "Test description"
            return f"test_value_{uuid.uuid4().hex[:6]}"
        
        # Integer types
        if 'int' in field_type:
            if 'age' in field_type:
                return random.randint(18, 65)
            if 'id' in field_type:
                return random.randint(1, 1000)
            return random.randint(1, 100)
        
        # Float types
        if 'float' in field_type or 'double' in field_type:
            return round(random.uniform(1.0, 100.0), 2)
        
        # Boolean
        if 'bool' in field_type:
            return random.choice([True, False])
        
        # UUID
        if 'uuid' in field_type:
            return str(uuid.uuid4())
        
        # Default
        return "test_value"
    
    def _generate_generic_body(self) -> Dict[str, Any]:
        """Generate a generic request body."""
        return {
            "testId": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "value": random.randint(1, 100),
                "description": f"test_data_{uuid.uuid4().hex[:8]}"
            }
        }
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL for endpoint."""
        return f"{self.base_url}{endpoint}"
    
    async def _execute_request(self, config: RequestConfig) -> RequestResult:
        """Execute a single request."""
        start_time = time.time()
        
        # Apply delay if configured
        if config.delay_ms > 0:
            await asyncio.sleep(config.delay_ms / 1000.0)
        
        try:
            if not PLAYWRIGHT_AVAILABLE:
                raise ImportError("Playwright not installed. Install with: pip install playwright")
            
            # Use playwright to make request
            method = config.method.lower()
            url = self._build_url(config.endpoint)
            headers = self._get_auth_headers()
            if config.headers:
                headers.update(config.headers)
            
            request_kwargs = {
                "url": url,
                "headers": headers,
                "timeout": config.timeout_ms
            }
            
            if config.body and method in ['post', 'put', 'patch']:
                request_kwargs["data"] = json.dumps(config.body)
            
            # Execute request based on method
            response = getattr(self._page, method)(**request_kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return RequestResult(
                timestamp=datetime.utcnow(),
                endpoint=config.endpoint,
                method=config.method,
                status=response.status,
                duration_ms=duration_ms,
                success=response.ok,
                response_body=response.text if response.ok else None
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return RequestResult(
                timestamp=datetime.utcnow(),
                endpoint=config.endpoint,
                method=config.method,
                status=0,
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
    
    def _create_request_config(self) -> RequestConfig:
        """Create a random request configuration."""
        if not self.endpoints:
            raise ValueError("No endpoints available")
        
        endpoint_info = random.choice(self.endpoints)
        
        return RequestConfig(
            endpoint=endpoint_info['path'],
            method=endpoint_info['method'],
            body=self._generate_request_body(
                endpoint_info['path'],
                endpoint_info['method']
            ),
            headers=self._get_auth_headers(),
            delay_ms=random.randint(0, 500)
        )
    
    def start(
        self,
        requests_per_minute: int = 100,
        duration_seconds: Optional[int] = None,
        concurrent_requests: int = 1
    ):
        """
        Start generating traffic.
        
        Args:
            requests_per_minute: Target number of requests per minute
            duration_seconds: Optional duration limit (None = run until stopped)
            concurrent_requests: Number of concurrent requests
        """
        if not PLAYWRIGHT_AVAILABLE:
            print("ERROR: Playwright not available. Install with: pip install playwright")
            return
            
        self._running = True
        
        with sync_playwright() as p:
            self._playwright = p
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            self._page = context.new_page()
            
            start_time = time.time()
            request_interval = 60.0 / requests_per_minute
            
            print(f"Starting traffic generation: {requests_per_minute} req/min to {self.base_url}")
            print(f"Endpoints available: {len(self.endpoints)}")
            print("-" * 50)
            
            while self._running:
                # Check duration limit
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    break
                
                # Create and execute request
                config = self._create_request_config()
                
                # Run synchronously in thread pool
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(asyncio.run, self._execute_request(config))
                    result = future.result()
                
                self.results.append(result)
                self._update_stats(result)
                
                # Print progress every 10 requests
                if len(self.results) % 10 == 0:
                    self._print_progress()
                
                # Wait for next request interval
                time.sleep(max(0, request_interval - result.duration_ms / 1000))
            
            browser.close()
            
        self._print_final_stats()
    
    def stop(self):
        """Stop generating traffic."""
        self._running = False
    
    def _update_stats(self, result: RequestResult):
        """Update statistics with a new result."""
        self.stats.total_requests += 1
        
        if result.success:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
            error_type = result.error or f"HTTP_{result.status}"
            self.stats.errors[error_type] = self.stats.errors.get(error_type, 0) + 1
        
        # Calculate average duration
        total_duration = sum(r.duration_ms for r in self.results)
        self.stats.avg_duration_ms = total_duration / len(self.results)
        
        # Calculate requests per minute
        if self.results:
            first_time = self.results[0].timestamp
            last_time = self.results[-1].timestamp
            elapsed_minutes = (last_time - first_time).total_seconds() / 60.0
            if elapsed_minutes > 0:
                self.stats.requests_per_minute = len(self.results) / elapsed_minutes
    
    def _print_progress(self):
        """Print current progress."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Requests: {self.stats.total_requests} | "
              f"Success: {self.stats.successful_requests} | "
              f"Failed: {self.stats.failed_requests} | "
              f"Avg: {self.stats.avg_duration_ms:.1f}ms")
    
    def _print_final_stats(self):
        """Print final statistics."""
        print("\n" + "=" * 50)
        print("TRAFFIC GENERATION COMPLETE")
        print("=" * 50)
        print(f"Total Requests:     {self.stats.total_requests}")
        print(f"Successful:         {self.stats.successful_requests}")
        print(f"Failed:             {self.stats.failed_requests}")
        print(f"Success Rate:       {self.stats.successful_requests/max(1,self.stats.total_requests)*100:.1f}%")
        print(f"Avg Duration:       {self.stats.avg_duration_ms:.1f}ms")
        print(f"Requests/min:       {self.stats.requests_per_minute:.1f}")
        
        if self.stats.errors:
            print("\nErrors:")
            for error, count in self.stats.errors.items():
                print(f"  - {error}: {count}")
        
        print("=" * 50)
    
    def get_results(self) -> List[RequestResult]:
        """Get all request results."""
        return self.results
    
    def get_stats(self) -> TrafficStats:
        """Get traffic statistics."""
        return self.stats


def create_traffic_bot(
    base_url: str,
    project_path: str,
    auth_token: Optional[str] = None
) -> TrafficGeneratorBot:
    """
    Convenience function to create a traffic bot from a project.
    
    Args:
        base_url: Base URL for the API
        project_path: Path to the project with source code
        auth_token: Optional authentication token
        
    Returns:
        Configured TrafficGeneratorBot
    """
    # Import scanners
    from scanner.endpoint_scanner import EndpointScanner
    from scanner.schema_scanner import SchemaScanner
    
    # Scan for endpoints
    endpoint_scanner = EndpointScanner(project_path)
    endpoints = endpoint_scanner.scan()
    
    # Scan for schemas
    schema_scanner = SchemaScanner(project_path)
    schemas = schema_scanner.scan()
    
    return TrafficGeneratorBot(
        base_url=base_url,
        endpoints=endpoints,
        schemas=schemas,
        auth_token=auth_token
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python traffic_generator.py <base_url> <project_path> [requests_per_minute]")
        print("Example: python traffic_generator.py http://localhost:8085 ../SocialSeed/services/auth-service 100")
        sys.exit(1)
    
    base_url = sys.argv[1]
    project_path = sys.argv[2]
    requests_per_minute = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    print(f"Initializing Traffic Generator Bot...")
    print(f"Base URL: {base_url}")
    print(f"Project: {project_path}")
    
    # Create and start bot
    bot = create_traffic_bot(base_url, project_path)
    bot.start(requests_per_minute=requests_per_minute, duration_seconds=60)