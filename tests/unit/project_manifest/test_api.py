"""Unit tests for project manifest API."""

import json

import pytest

from socialseed_e2e.project_manifest.api import ManifestAPI, TokenOptimizedQuery
from socialseed_e2e.project_manifest.models import (
    DtoField,
    DtoSchema,
    EndpointInfo,
    EnvironmentVariable,
    HttpMethod,
    PortConfig,
    ProjectKnowledge,
    ServiceDependency,
    ServiceInfo,
)


@pytest.fixture
def sample_manifest(tmp_path):
    """Create a sample manifest for testing."""
    manifest = ProjectKnowledge(
        version="1.0.0",
        project_name="test-api",
        project_root=str(tmp_path),
        services=[
            ServiceInfo(
                name="users-service",
                language="python",
                framework="fastapi",
                root_path=str(tmp_path / "users"),
                endpoints=[
                    EndpointInfo(
                        name="get_users",
                        method=HttpMethod.GET,
                        path="/users",
                        full_path="/api/v1/users",
                        file_path="/routes.py",
                        requires_auth=False,
                        tags=["users", "list"],
                    ),
                    EndpointInfo(
                        name="create_user",
                        method=HttpMethod.POST,
                        path="/users",
                        full_path="/api/v1/users",
                        file_path="/routes.py",
                        requires_auth=True,
                        request_dto="UserRequest",
                        response_dto="UserResponse",
                        tags=["users", "create"],
                    ),
                    EndpointInfo(
                        name="get_user_by_id",
                        method=HttpMethod.GET,
                        path="/users/{id}",
                        full_path="/api/v1/users/{id}",
                        file_path="/routes.py",
                        requires_auth=True,
                        tags=["users", "get"],
                    ),
                ],
                dto_schemas=[
                    DtoSchema(
                        name="UserRequest",
                        fields=[
                            DtoField(name="username", type="str", required=True),
                            DtoField(name="email", type="str", required=True),
                            DtoField(name="age", type="int", required=False, default_value=0),
                        ],
                        file_path="/dtos.py",
                    ),
                    DtoSchema(
                        name="UserResponse",
                        fields=[
                            DtoField(name="id", type="int", required=True),
                            DtoField(name="username", type="str", required=True),
                            DtoField(name="email", type="str", required=True),
                        ],
                        file_path="/dtos.py",
                    ),
                ],
                ports=[PortConfig(port=8080, protocol="http")],
                environment_vars=[
                    EnvironmentVariable(name="DATABASE_URL", required=True),
                ],
                dependencies=[
                    ServiceDependency(
                        service_name="auth-service",
                        endpoint="/validate",
                        method=HttpMethod.POST,
                    ),
                ],
            ),
            ServiceInfo(
                name="auth-service",
                language="java",
                framework="spring",
                root_path=str(tmp_path / "auth"),
                endpoints=[
                    EndpointInfo(
                        name="login",
                        method=HttpMethod.POST,
                        path="/auth/login",
                        full_path="/api/v1/auth/login",
                        file_path="/AuthController.java",
                        requires_auth=False,
                        tags=["auth", "login"],
                    ),
                    EndpointInfo(
                        name="validate",
                        method=HttpMethod.POST,
                        path="/auth/validate",
                        full_path="/api/v1/auth/validate",
                        file_path="/AuthController.java",
                        requires_auth=True,
                        tags=["auth", "validate"],
                    ),
                ],
                dto_schemas=[
                    DtoSchema(
                        name="LoginRequest",
                        fields=[
                            DtoField(name="username", type="str", required=True),
                            DtoField(name="password", type="str", required=True),
                        ],
                        file_path="/LoginRequest.java",
                    ),
                ],
                ports=[PortConfig(port=8081, protocol="http")],
            ),
        ],
        global_env_vars=[
            EnvironmentVariable(name="API_KEY", required=True),
            EnvironmentVariable(name="LOG_LEVEL", default_value="INFO", required=False),
        ],
    )

    # Save manifest to file
    manifest_path = tmp_path / "project_knowledge.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2))

    return tmp_path, manifest


@pytest.fixture
def api(sample_manifest):
    """Create a ManifestAPI instance with sample data."""
    tmp_path, _ = sample_manifest
    return ManifestAPI(tmp_path)


class TestManifestAPI:
    """Test ManifestAPI class."""

    def test_init(self, api):
        """Test API initialization."""
        assert api.project_root.exists()
        assert api.manifest is not None

    def test_get_services(self, api):
        """Test getting all services."""
        services = api.get_services()

        assert len(services) == 2
        assert any(s.name == "users-service" for s in services)
        assert any(s.name == "auth-service" for s in services)

    def test_get_service(self, api):
        """Test getting a specific service."""
        service = api.get_service("users-service")

        assert service is not None
        assert service.name == "users-service"
        assert service.language == "python"
        assert service.framework == "fastapi"

    def test_get_nonexistent_service(self, api):
        """Test getting a non-existent service."""
        service = api.get_service("nonexistent")

        assert service is None

    def test_get_services_by_language(self, api):
        """Test filtering services by language."""
        python_services = api.get_services_by_language("python")

        assert len(python_services) == 1
        assert python_services[0].name == "users-service"

    def test_get_services_by_framework(self, api):
        """Test filtering services by framework."""
        spring_services = api.get_services_by_framework("spring")

        assert len(spring_services) == 1
        assert spring_services[0].name == "auth-service"

    def test_get_all_endpoints(self, api):
        """Test getting all endpoints."""
        endpoints = api.get_endpoints()

        assert len(endpoints) == 5  # 3 from users-service + 2 from auth-service

    def test_get_endpoints_by_method(self, api):
        """Test filtering endpoints by HTTP method."""
        get_endpoints = api.get_endpoints(method=HttpMethod.GET)

        assert len(get_endpoints) == 2
        assert all(ep.method == HttpMethod.GET for ep in get_endpoints)

    def test_get_endpoints_by_auth(self, api):
        """Test filtering endpoints by auth requirement."""
        auth_endpoints = api.get_endpoints(requires_auth=True)

        assert len(auth_endpoints) == 3
        assert all(ep.requires_auth for ep in auth_endpoints)

    def test_get_endpoints_by_service(self, api):
        """Test filtering endpoints by service."""
        endpoints = api.get_endpoints(service_name="auth-service")

        assert len(endpoints) == 2

    def test_get_endpoint(self, api):
        """Test getting a specific endpoint."""
        endpoint = api.get_endpoint("/api/v1/users", HttpMethod.GET)

        assert endpoint is not None
        assert endpoint.name == "get_users"
        assert endpoint.method == HttpMethod.GET

    def test_search_endpoints_by_query(self, api):
        """Test searching endpoints by query string."""
        results = api.search_endpoints(query="login")

        assert len(results) == 1
        assert results[0].name == "login"

    def test_search_endpoints_by_tags(self, api):
        """Test searching endpoints by tags."""
        results = api.search_endpoints(tags=["auth"])

        assert len(results) == 2
        assert all("auth" in ep.tags for ep in results)

    def test_search_endpoints_by_path_prefix(self, api):
        """Test searching endpoints by path prefix."""
        results = api.search_endpoints(path_prefix="/api/v1/users")

        assert len(results) == 3

    def test_get_endpoints_by_dto(self, api):
        """Test getting endpoints that use a specific DTO."""
        endpoints = api.get_endpoints_by_dto("UserRequest", "request")

        assert len(endpoints) == 1
        assert endpoints[0].request_dto == "UserRequest"

    def test_get_all_dtos(self, api):
        """Test getting all DTOs."""
        dtos = api.get_dtos()

        assert len(dtos) == 3  # 2 from users-service + 1 from auth-service

    def test_get_dtos_by_service(self, api):
        """Test filtering DTOs by service."""
        dtos = api.get_dtos(service_name="auth-service")

        assert len(dtos) == 1
        assert dtos[0].name == "LoginRequest"

    def test_get_dto(self, api):
        """Test getting a specific DTO."""
        dto = api.get_dto("UserRequest")

        assert dto is not None
        assert dto.name == "UserRequest"
        assert len(dto.fields) == 3

    def test_search_dtos(self, api):
        """Test searching DTOs."""
        results = api.search_dtos("Login")

        assert len(results) == 1
        assert results[0].name == "LoginRequest"

    def test_get_dto_fields(self, api):
        """Test getting fields of a DTO."""
        fields = api.get_dto_fields("UserRequest")

        assert len(fields) == 3
        assert any(f.name == "username" for f in fields)
        assert any(f.name == "email" for f in fields)

    def test_get_dto_hierarchy(self, api):
        """Test getting DTO hierarchy and relationships."""
        hierarchy = api.get_dto_hierarchy("UserRequest")

        assert "dto" in hierarchy
        assert "used_as_request_by" in hierarchy
        assert len(hierarchy["used_as_request_by"]) == 1

    def test_get_environment_variables(self, api):
        """Test getting environment variables."""
        env_vars = api.get_environment_variables()

        # Should include global vars + service vars
        assert len(env_vars) >= 2

    def test_get_environment_variables_by_service(self, api):
        """Test filtering environment variables by service."""
        env_vars = api.get_environment_variables(service_name="users-service", include_global=False)

        assert len(env_vars) == 1
        assert env_vars[0].name == "DATABASE_URL"

    def test_get_ports(self, api):
        """Test getting ports."""
        ports = api.get_ports()

        assert len(ports) == 2
        assert any(p.port == 8080 for p in ports)
        assert any(p.port == 8081 for p in ports)

    def test_get_ports_by_service(self, api):
        """Test filtering ports by service."""
        ports = api.get_ports(service_name="users-service")

        assert len(ports) == 1
        assert ports[0].port == 8080

    def test_get_dependencies(self, api):
        """Test getting service dependencies."""
        deps = api.get_dependencies()

        assert len(deps) == 1
        assert deps[0].service_name == "auth-service"

    def test_get_service_graph(self, api):
        """Test getting service dependency graph."""
        graph = api.get_service_graph()

        assert "users-service" in graph
        assert "auth-service" in graph["users-service"]

    def test_get_summary(self, api):
        """Test getting project summary."""
        summary = api.get_summary()

        assert summary["project_name"] == "test-api"
        assert summary["version"] == "1.0.0"
        assert summary["statistics"]["services"] == 2
        assert summary["statistics"]["endpoints"] == 5
        assert summary["statistics"]["dtos"] == 3

    def test_export_summary_json(self, api):
        """Test exporting summary as JSON."""
        json_output = api.export_summary(format="json")

        assert isinstance(json_output, str)
        data = json.loads(json_output)
        assert data["project_name"] == "test-api"

    def test_export_summary_markdown(self, api):
        """Test exporting summary as Markdown."""
        md_output = api.export_summary(format="markdown")

        assert isinstance(md_output, str)
        assert "# test-api" in md_output
        assert "## Statistics" in md_output

    def test_reload(self, api, sample_manifest):
        """Test reloading manifest."""
        tmp_path, _ = sample_manifest

        # Initial load
        api.manifest.project_name

        # Modify manifest
        manifest_path = tmp_path / "project_knowledge.json"
        data = json.loads(manifest_path.read_text())
        data["project_name"] = "updated-name"
        manifest_path.write_text(json.dumps(data))

        # Reload
        api.reload()

        assert api.manifest.project_name == "updated-name"


class TestTokenOptimizedQuery:
    """Test TokenOptimizedQuery class."""

    @pytest.fixture
    def optimized_query(self, api):
        """Create a TokenOptimizedQuery instance."""
        return TokenOptimizedQuery(api)

    def test_get_endpoint_signature(self, optimized_query):
        """Test getting compact endpoint signature."""
        sig = optimized_query.get_endpoint_signature("/api/v1/users", HttpMethod.POST)

        assert sig is not None
        assert sig["method"] == HttpMethod.POST
        assert sig["path"] == "/api/v1/users"
        assert sig["auth"] is True
        assert sig["request"] == "UserRequest"
        assert sig["response"] == "UserResponse"

    def test_get_dto_signature(self, optimized_query):
        """Test getting compact DTO signature."""
        sig = optimized_query.get_dto_signature("UserRequest")

        assert sig is not None
        assert sig["name"] == "UserRequest"
        assert len(sig["fields"]) == 3
        assert all("name" in f and "type" in f and "required" in f for f in sig["fields"])

    def test_get_service_overview(self, optimized_query):
        """Test getting compact service overview."""
        overview = optimized_query.get_service_overview("users-service")

        assert overview is not None
        assert overview["name"] == "users-service"
        assert overview["language"] == "python"
        assert overview["framework"] == "fastapi"
        assert overview["endpoints"] == 3
        assert overview["dtos"] == 2
        assert overview["ports"] == [8080]

    def test_list_all_endpoints_compact(self, optimized_query):
        """Test getting compact list of all endpoints."""
        endpoints = optimized_query.list_all_endpoints_compact()

        assert len(endpoints) == 5
        assert all("method" in ep and "path" in ep for ep in endpoints)

    def test_list_all_dtos_compact(self, optimized_query):
        """Test getting compact list of all DTOs."""
        dtos = optimized_query.list_all_dtos_compact()

        assert len(dtos) == 3
        assert all("name" in dto and "fields" in dto and "service" in dto for dto in dtos)


class TestManifestAPIErrorHandling:
    """Test ManifestAPI error handling."""

    def test_missing_manifest(self, tmp_path):
        """Test error when manifest doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            ManifestAPI(tmp_path)

        assert "Manifest not found" in str(exc_info.value)

    def test_invalid_manifest(self, tmp_path):
        """Test error with invalid manifest."""
        manifest_path = tmp_path / "project_knowledge.json"
        manifest_path.write_text("invalid json")

        with pytest.raises((json.JSONDecodeError, ValueError)):
            ManifestAPI(tmp_path)
