"""Unit tests for project manifest models."""

import json

from socialseed_e2e.project_manifest.models import (
    DtoField,
    DtoSchema,
    EndpointInfo,
    EndpointParameter,
    EnvironmentVariable,
    HttpMethod,
    PortConfig,
    ProjectKnowledge,
    ServiceDependency,
    ServiceInfo,
    ValidationRule,
)


class TestHttpMethod:
    """Test HTTP method enum."""

    def test_http_method_values(self):
        """Test that all HTTP methods are defined."""
        assert HttpMethod.GET == "GET"
        assert HttpMethod.POST == "POST"
        assert HttpMethod.PUT == "PUT"
        assert HttpMethod.DELETE == "DELETE"
        assert HttpMethod.PATCH == "PATCH"
        assert HttpMethod.HEAD == "HEAD"
        assert HttpMethod.OPTIONS == "OPTIONS"


class TestValidationRule:
    """Test validation rule model."""

    def test_validation_rule_creation(self):
        """Test creating a validation rule."""
        rule = ValidationRule(
            rule_type="min_length",
            value=5,
            error_message="Must be at least 5 characters",
        )

        assert rule.rule_type == "min_length"
        assert rule.value == 5
        assert rule.error_message == "Must be at least 5 characters"

    def test_validation_rule_optional_error_message(self):
        """Test that error_message is optional."""
        rule = ValidationRule(rule_type="max_length", value=100)

        assert rule.rule_type == "max_length"
        assert rule.value == 100
        assert rule.error_message is None


class TestDtoField:
    """Test DTO field model."""

    def test_dto_field_creation(self):
        """Test creating a DTO field."""
        field = DtoField(
            name="username",
            type="str",
            required=True,
            validations=[
                ValidationRule(rule_type="min_length", value=3),
                ValidationRule(rule_type="max_length", value=50),
            ],
        )

        assert field.name == "username"
        assert field.type == "str"
        assert field.required is True
        assert len(field.validations) == 2
        assert field.alias is None

    def test_dto_field_with_alias(self):
        """Test DTO field with serialization alias."""
        field = DtoField(
            name="user_id",
            type="int",
            required=True,
            alias="userId",
        )

        assert field.name == "user_id"
        assert field.alias == "userId"


class TestDtoSchema:
    """Test DTO schema model."""

    def test_dto_schema_creation(self):
        """Test creating a DTO schema."""
        dto = DtoSchema(
            name="UserRequest",
            fields=[
                DtoField(name="username", type="str", required=True),
                DtoField(name="email", type="str", required=True),
            ],
            file_path="/app/dtos.py",
            line_number=10,
        )

        assert dto.name == "UserRequest"
        assert len(dto.fields) == 2
        assert dto.file_path == "/app/dtos.py"
        assert dto.line_number == 10


class TestEndpointParameter:
    """Test endpoint parameter model."""

    def test_endpoint_parameter_creation(self):
        """Test creating an endpoint parameter."""
        param = EndpointParameter(
            name="user_id",
            param_type="int",
            location="path",
            required=True,
        )

        assert param.name == "user_id"
        assert param.param_type == "int"
        assert param.location == "path"
        assert param.required is True


class TestEndpointInfo:
    """Test endpoint info model."""

    def test_endpoint_info_creation(self):
        """Test creating an endpoint info object."""
        endpoint = EndpointInfo(
            name="create_user",
            method=HttpMethod.POST,
            path="/api/users",
            full_path="/api/v1/users",
            requires_auth=True,
            auth_roles=["admin", "user"],
            file_path="/app/controllers.py",
            line_number=25,
        )

        assert endpoint.name == "create_user"
        assert endpoint.method == HttpMethod.POST
        assert endpoint.path == "/api/users"
        assert endpoint.full_path == "/api/v1/users"
        assert endpoint.requires_auth is True
        assert endpoint.auth_roles == ["admin", "user"]
        assert endpoint.file_path == "/app/controllers.py"
        assert endpoint.line_number == 25


class TestPortConfig:
    """Test port configuration model."""

    def test_port_config_creation(self):
        """Test creating a port configuration."""
        port = PortConfig(
            port=8080,
            protocol="http",
            description="Main API port",
            exposed=True,
        )

        assert port.port == 8080
        assert port.protocol == "http"
        assert port.description == "Main API port"
        assert port.exposed is True


class TestEnvironmentVariable:
    """Test environment variable model."""

    def test_env_var_creation(self):
        """Test creating an environment variable."""
        env_var = EnvironmentVariable(
            name="DATABASE_URL",
            default_value="postgresql://localhost/db",
            required=True,
            description="Database connection string",
            example="postgresql://user:pass@host/db",
        )

        assert env_var.name == "DATABASE_URL"
        assert env_var.default_value == "postgresql://localhost/db"
        assert env_var.required is True
        assert env_var.description == "Database connection string"
        assert env_var.example == "postgresql://user:pass@host/db"


class TestServiceDependency:
    """Test service dependency model."""

    def test_dependency_creation(self):
        """Test creating a service dependency."""
        dep = ServiceDependency(
            service_name="auth-service",
            endpoint="/api/auth/validate",
            method=HttpMethod.POST,
            description="Validates authentication tokens",
        )

        assert dep.service_name == "auth-service"
        assert dep.endpoint == "/api/auth/validate"
        assert dep.method == HttpMethod.POST
        assert dep.description == "Validates authentication tokens"


class TestServiceInfo:
    """Test service info model."""

    def test_service_info_creation(self):
        """Test creating a service info object."""
        service = ServiceInfo(
            name="users-api",
            language="python",
            framework="fastapi",
            root_path="/services/users",
            endpoints=[
                EndpointInfo(
                    name="get_users",
                    method=HttpMethod.GET,
                    path="/users",
                    full_path="/api/v1/users",
                    file_path="/services/users/routes.py",
                ),
            ],
            ports=[PortConfig(port=8080, protocol="http")],
        )

        assert service.name == "users-api"
        assert service.language == "python"
        assert service.framework == "fastapi"
        assert len(service.endpoints) == 1
        assert len(service.ports) == 1


class TestProjectKnowledge:
    """Test project knowledge model."""

    def test_project_knowledge_creation(self):
        """Test creating a project knowledge object."""
        manifest = ProjectKnowledge(
            version="1.0.0",
            project_name="my-api",
            project_root="/home/user/my-api",
            services=[
                ServiceInfo(
                    name="users-api",
                    language="python",
                    root_path="/services/users",
                ),
            ],
        )

        assert manifest.version == "1.0.0"
        assert manifest.project_name == "my-api"
        assert manifest.project_root == "/home/user/my-api"
        assert len(manifest.services) == 1

    def test_get_service(self):
        """Test getting a service by name."""
        manifest = ProjectKnowledge(
            version="1.0.0",
            project_name="my-api",
            project_root="/home/user/my-api",
            services=[
                ServiceInfo(name="users-api", language="python", root_path="/users"),
                ServiceInfo(name="auth-api", language="java", root_path="/auth"),
            ],
        )

        service = manifest.get_service("users-api")
        assert service is not None
        assert service.name == "users-api"
        assert service.language == "python"

        missing_service = manifest.get_service("non-existent")
        assert missing_service is None

    def test_get_endpoint(self):
        """Test getting an endpoint by path."""
        manifest = ProjectKnowledge(
            version="1.0.0",
            project_name="my-api",
            project_root="/home/user/my-api",
            services=[
                ServiceInfo(
                    name="users-api",
                    language="python",
                    root_path="/users",
                    endpoints=[
                        EndpointInfo(
                            name="get_users",
                            method=HttpMethod.GET,
                            path="/users",
                            full_path="/api/v1/users",
                            file_path="/routes.py",
                        ),
                        EndpointInfo(
                            name="create_user",
                            method=HttpMethod.POST,
                            path="/users",
                            full_path="/api/v1/users",
                            file_path="/routes.py",
                        ),
                    ],
                ),
            ],
        )

        endpoint = manifest.get_endpoint("/users", HttpMethod.GET)
        assert endpoint is not None
        assert endpoint.name == "get_users"

        # Without method filter
        endpoint_no_method = manifest.get_endpoint("/users")
        assert endpoint_no_method is not None

        # Non-existent endpoint
        missing_endpoint = manifest.get_endpoint("/non-existent")
        assert missing_endpoint is None

    def test_get_dto(self):
        """Test getting a DTO by name."""
        manifest = ProjectKnowledge(
            version="1.0.0",
            project_name="my-api",
            project_root="/home/user/my-api",
            services=[
                ServiceInfo(
                    name="users-api",
                    language="python",
                    root_path="/users",
                    dto_schemas=[
                        DtoSchema(
                            name="UserRequest",
                            fields=[DtoField(name="username", type="str", required=True)],
                            file_path="/dtos.py",
                        ),
                    ],
                ),
            ],
        )

        dto = manifest.get_dto("UserRequest")
        assert dto is not None
        assert dto.name == "UserRequest"

        missing_dto = manifest.get_dto("NonExistent")
        assert missing_dto is None

    def test_update_timestamp(self):
        """Test updating the last_updated timestamp."""
        manifest = ProjectKnowledge(
            version="1.0.0",
            project_name="my-api",
            project_root="/home/user/my-api",
        )

        old_timestamp = manifest.last_updated
        manifest.update_timestamp()
        new_timestamp = manifest.last_updated

        assert new_timestamp > old_timestamp

    def test_serialization(self):
        """Test serializing and deserializing project knowledge."""
        manifest = ProjectKnowledge(
            version="1.0.0",
            project_name="my-api",
            project_root="/home/user/my-api",
            services=[
                ServiceInfo(
                    name="users-api",
                    language="python",
                    root_path="/users",
                    endpoints=[
                        EndpointInfo(
                            name="get_users",
                            method=HttpMethod.GET,
                            path="/users",
                            full_path="/api/v1/users",
                            file_path="/routes.py",
                        ),
                    ],
                ),
            ],
        )

        # Serialize to JSON
        json_data = manifest.model_dump_json()
        assert isinstance(json_data, str)

        # Deserialize from JSON
        data = json.loads(json_data)
        manifest2 = ProjectKnowledge.model_validate(data)

        assert manifest2.project_name == manifest.project_name
        assert len(manifest2.services) == len(manifest.services)
        assert manifest2.services[0].name == manifest.services[0].name
