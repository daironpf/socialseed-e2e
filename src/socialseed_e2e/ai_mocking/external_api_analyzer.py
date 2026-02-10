"""External API Analyzer for detecting third-party HTTP calls.

This module scans codebases to identify calls to external APIs like Stripe,
Google Maps, AWS, and other third-party services.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class ExternalAPICall:
    """Represents a detected external API call."""

    service_name: str
    url_pattern: str
    method: str
    file_path: str
    line_number: int
    code_context: str
    detected_headers: List[str] = field(default_factory=list)
    detected_params: List[str] = field(default_factory=list)
    confidence: float = 0.8


@dataclass
class ExternalAPIDependency:
    """Aggregated information about an external API dependency."""

    service_name: str
    base_url: str
    detected_calls: List[ExternalAPICall] = field(default_factory=list)
    auth_header_detected: bool = False
    env_var_keys: List[str] = field(default_factory=list)
    endpoints: Set[str] = field(default_factory=set)


class ExternalAPIAnalyzer:
    """Analyzes code to detect external third-party API calls."""

    # Common third-party API patterns
    KNOWN_APIS = {
        "stripe": {
            "patterns": [r"api\.stripe\.com", r"stripe\.com"],
            "base_url": "https://api.stripe.com",
            "env_vars": [
                "STRIPE_SECRET_KEY",
                "STRIPE_API_KEY",
                "STRIPE_PUBLISHABLE_KEY",
            ],
        },
        "google_maps": {
            "patterns": [r"maps\.googleapis\.com", r"maps\.google\.com"],
            "base_url": "https://maps.googleapis.com",
            "env_vars": ["GOOGLE_MAPS_API_KEY", "GOOGLE_API_KEY", "MAPS_API_KEY"],
        },
        "aws": {
            "patterns": [r"amazonaws\.com", r"\.amazonaws\.com"],
            "base_url": "https://{service}.{region}.amazonaws.com",
            "env_vars": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
        },
        "sendgrid": {
            "patterns": [r"api\.sendgrid\.com"],
            "base_url": "https://api.sendgrid.com",
            "env_vars": ["SENDGRID_API_KEY"],
        },
        "twilio": {
            "patterns": [r"api\.twilio\.com"],
            "base_url": "https://api.twilio.com",
            "env_vars": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
        },
        "github": {
            "patterns": [r"api\.github\.com"],
            "base_url": "https://api.github.com",
            "env_vars": ["GITHUB_TOKEN", "GITHUB_API_TOKEN"],
        },
        "slack": {
            "patterns": [r"slack\.com/api"],
            "base_url": "https://slack.com/api",
            "env_vars": ["SLACK_BOT_TOKEN", "SLACK_API_TOKEN"],
        },
        "openai": {
            "patterns": [r"api\.openai\.com"],
            "base_url": "https://api.openai.com",
            "env_vars": ["OPENAI_API_KEY"],
        },
        "paypal": {
            "patterns": [r"api\.paypal\.com", r"api\.sandbox\.paypal\.com"],
            "base_url": "https://api.paypal.com",
            "env_vars": ["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET"],
        },
        "firebase": {
            "patterns": [r"firestore\.googleapis\.com", r"firebaseio\.com"],
            "base_url": "https://firestore.googleapis.com",
            "env_vars": ["FIREBASE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"],
        },
    }

    # HTTP client patterns by language
    HTTP_CLIENT_PATTERNS = {
        "python": {
            "requests": r'requests\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            "httpx": r'httpx\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            "aiohttp": r'aiohttp\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            "urllib": r'urllib\.request\.urlopen\s*\(\s*["\']([^"\']+)["\']',
        },
        "javascript": {
            "fetch": r'fetch\s*\(\s*["\']([^"\']+)["\']',
            "axios": r'axios\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            "http": r'http\.(get|request)\s*\(\s*.*?["\']([^"\']+)["\']',
        },
        "java": {
            "rest_template": (
                r"restTemplate\.(getForObject|postForObject|exchange)"
                r'\s*\(\s*["\']([^"\']+)["\']'
            ),
            "web_client": (
                r"webClient\.(get|post|put|delete)\s*\(\s*\)"
                r'\s*\.uri\s*\(\s*["\']([^"\']+)["\']'
            ),
            "http_client": r"HttpClient\.newHttpClient\s*\(\s*\)",
        },
    }

    # Authorization header patterns
    AUTH_PATTERNS = [
        r'Authorization["\']?\s*[:=]\s*["\']?\s*\w+\s+\$?\{?\w+',
        r"Bearer\s+\$?\{?\w+",
        r'api[-_]?key["\']?\s*[:=]',
        r"x-api-key",
    ]

    def __init__(self, project_root: Path):
        """Initialize the analyzer.

        Args:
            project_root: Root directory of the project to analyze
        """
        self.project_root = project_root
        self.detected_apis: Dict[str, ExternalAPIDependency] = {}

    def analyze_project(self) -> Dict[str, ExternalAPIDependency]:
        """Scan entire project for external API calls.

        Returns:
            Dictionary of service_name -> ExternalAPIDependency
        """
        self.detected_apis = {}

        # Scan all source files
        for file_path in self._get_source_files():
            self._analyze_file(file_path)

        # Check for environment variables
        self._scan_env_files()

        return self.detected_apis

    def _get_source_files(self) -> List[Path]:
        """Get all source files to analyze."""
        source_files = []
        extensions = {".py", ".js", ".ts", ".java", ".go", ".rb", ".php"}

        for ext in extensions:
            source_files.extend(self.project_root.rglob(f"*{ext}"))

        # Exclude common directories
        exclude_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".e2e"}
        source_files = [
            f
            for f in source_files
            if not any(excluded in f.parts for excluded in exclude_dirs)
        ]

        return source_files

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for external API calls."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
        except (UnicodeDecodeError, IOError):
            return

        # Detect language
        language = self._detect_language(file_path)

        # Look for HTTP calls
        self._find_http_calls(content, lines, file_path, language)

        # Look for known API patterns
        self._find_known_api_patterns(content, lines, file_path)

        # Look for SDK imports
        self._find_sdk_imports(content, file_path)

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext = file_path.suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "javascript",
            ".jsx": "javascript",
            ".tsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
        }
        return mapping.get(ext, "unknown")

    def _find_http_calls(
        self, content: str, lines: List[str], file_path: Path, language: str
    ) -> None:
        """Find HTTP client calls to external APIs."""
        patterns = self.HTTP_CLIENT_PATTERNS.get(language, {})

        for client_name, pattern in patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                groups = match.groups()
                if len(groups) >= 2:
                    method = groups[0].upper() if groups[0] else "GET"
                    url = groups[-1]
                elif len(groups) == 1:
                    method = "GET"
                    url = groups[0]
                else:
                    continue

                # Skip relative URLs
                if url.startswith("/") and not url.startswith("//"):
                    continue

                # Check if it's an external URL
                if self._is_external_url(url):
                    line_num = content[: match.start()].count("\n") + 1
                    context = lines[line_num - 1] if line_num <= len(lines) else ""

                    # Determine service name
                    service_name = self._extract_service_name(url)

                    call = ExternalAPICall(
                        service_name=service_name,
                        url_pattern=url,
                        method=method,
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        code_context=context.strip(),
                    )

                    self._add_call(service_name, url, call)

    def _find_known_api_patterns(
        self, content: str, lines: List[str], file_path: Path
    ) -> None:
        """Find calls to known third-party APIs."""
        for service_name, config in self.KNOWN_APIS.items():
            for pattern in config["patterns"]:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    line_num = content[: match.start()].count("\n") + 1
                    context = lines[line_num - 1] if line_num <= len(lines) else ""

                    # Extract method from context
                    method = self._detect_method_from_context(context)

                    call = ExternalAPICall(
                        service_name=service_name,
                        url_pattern=pattern,
                        method=method,
                        file_path=str(file_path.relative_to(self.project_root)),
                        line_number=line_num,
                        code_context=context.strip(),
                        confidence=0.95,
                    )

                    self._add_call(service_name, config["base_url"], call)

    def _find_sdk_imports(self, content: str, file_path: Path) -> None:
        """Find SDK imports that indicate external API usage."""
        sdk_patterns = {
            "stripe": r'import\s+stripe|from\s+stripe|require\s*\(\s*["\']stripe',
            "google_maps": r"import\s+.*google.*maps|@google/maps",
            "aws": r"import\s+boto3|from\s+boto3|aws-sdk|@aws-sdk",
            "twilio": r'import\s+twilio|from\s+twilio|require\s*\(\s*["\']twilio',
            "sendgrid": r"sendgrid|@sendgrid/mail",
            "openai": r'import\s+openai|from\s+openai|require\s*\(\s*["\']openai',
        }

        for service_name, pattern in sdk_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                # Check if we already detected this service
                if service_name not in self.detected_apis:
                    config = self.KNOWN_APIS.get(service_name, {})
                    self.detected_apis[service_name] = ExternalAPIDependency(
                        service_name=service_name,
                        base_url=config.get("base_url", ""),
                        env_var_keys=config.get("env_vars", []),
                    )

    def _scan_env_files(self) -> None:
        """Scan .env files for API keys."""
        env_files = list(self.project_root.glob(".env*"))

        for env_file in env_files:
            try:
                content = env_file.read_text()
                for service_name, config in self.KNOWN_APIS.items():
                    for env_var in config.get("env_vars", []):
                        if env_var in content:
                            if service_name in self.detected_apis:
                                if (
                                    env_var
                                    not in self.detected_apis[service_name].env_var_keys
                                ):
                                    self.detected_apis[
                                        service_name
                                    ].env_var_keys.append(env_var)
                            else:
                                self.detected_apis[service_name] = (
                                    ExternalAPIDependency(
                                        service_name=service_name,
                                        base_url=config.get("base_url", ""),
                                        env_var_keys=[env_var],
                                    )
                                )
            except IOError:
                continue

    def _is_external_url(self, url: str) -> bool:
        """Check if URL is an external API call."""
        external_indicators = [
            "http://",
            "https://",
            "api.",
        ]
        return any(indicator in url.lower() for indicator in external_indicators)

    def _extract_service_name(self, url: str) -> str:
        """Extract service name from URL."""
        # Match known services
        for service_name, config in self.KNOWN_APIS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, url, re.IGNORECASE):
                    return service_name

        # Extract from URL
        match = re.search(r"https?://([^/]+)", url)
        if match:
            domain = match.group(1)
            # Clean up domain
            domain = re.sub(r"^api\.", "", domain)
            domain = re.sub(r"\.(com|org|net|io)$", "", domain)
            return domain.replace(".", "_")

        return "unknown"

    def _detect_method_from_context(self, context: str) -> str:
        """Try to detect HTTP method from code context."""
        method_patterns = [
            (r"\.get\s*\(", "GET"),
            (r"\.post\s*\(", "POST"),
            (r"\.put\s*\(", "PUT"),
            (r"\.delete\s*\(", "DELETE"),
            (r"\.patch\s*\(", "PATCH"),
        ]

        for pattern, method in method_patterns:
            if re.search(pattern, context, re.IGNORECASE):
                return method

        return "GET"

    def _add_call(
        self, service_name: str, base_url: str, call: ExternalAPICall
    ) -> None:
        """Add a detected call to the registry.

        Args:
            service_name: Name of the external service
            base_url: Base URL for the service
            call: The detected API call to add
        """
        if service_name not in self.detected_apis:
            config = self.KNOWN_APIS.get(service_name, {})
            self.detected_apis[service_name] = ExternalAPIDependency(
                service_name=service_name,
                base_url=config.get("base_url", base_url),
                env_var_keys=config.get("env_vars", []),
            )

        self.detected_apis[service_name].detected_calls.append(call)
        self.detected_apis[service_name].endpoints.add(call.url_pattern)

        # Check for auth headers
        if any(
            auth in call.code_context.lower()
            for auth in ["authorization", "api-key", "api_key"]
        ):
            self.detected_apis[service_name].auth_header_detected = True


def analyze_external_apis(project_root: str) -> Dict[str, ExternalAPIDependency]:
    """Convenience function to analyze a project for external APIs.

    Args:
        project_root: Path to project root directory

    Returns:
        Dictionary of detected external API dependencies
    """
    analyzer = ExternalAPIAnalyzer(Path(project_root))
    return analyzer.analyze_project()
