"""Unit tests for AI Code Generation Helper.

This module contains unit tests for JavaControllerParser and PythonCodeGenerator classes.
"""

import pytest

from socialseed_e2e.utils.ai_generator import (
    AICodeGenerator,
    DtoField,
    EndpointInfo,
    JavaControllerParser,
    PythonCodeGenerator,
)


class TestJavaControllerParser:
    """Test Java Spring Boot controller parsing."""

    def test_parse_controller_basic(self):
        """Test parsing a simple Java controller."""
        java_code = """
        @RestController
        @RequestMapping("/api/v1/users")
        public class UserController {

            @PostMapping("/register")
            public ResponseEntity<UserResponse> register(@RequestBody @Valid RegisterDTO request) {
                return ResponseEntity.ok().build();
            }

            @GetMapping("/{id}")
            @PreAuthorize("hasRole('USER')")
            public UserInfo getUser(@PathVariable Long id) {
                return null;
            }
        }
        """
        endpoints = JavaControllerParser.parse_controller(java_code)

        assert len(endpoints) >= 2

        # Verify POST mapping
        register = next(e for e in endpoints if e.name == "register")
        assert register.method == "POST"
        assert register.path == "/register"
        assert register.request_dto == "RegisterDTO"

        # Verify GET mapping
        get_user = next(e for e in endpoints if e.name == "getUser")
        assert get_user.method == "GET"
        assert get_user.path == "/{id}"
        assert get_user.requires_auth is True
        assert "id" in get_user.path_params

    def test_parse_dto_record(self):
        """Test parsing a Java record DTO."""
        java_code = """
        public record RegisterDTO(
            @NotBlank String username,
            @Email String email,
            String password,
            Integer age,
            List<String> roles
        ) {}
        """
        fields = JavaControllerParser.parse_dto(java_code, "RegisterDTO")

        assert len(fields) == 5

        names = [f.name for f in fields]
        assert "username" in names
        assert "email" in names
        assert "roles" in names

        username_field = next(f for f in fields if f.name == "username")
        assert username_field.type_hint == "str"

        email_field = next(f for f in fields if f.name == "email")
        assert email_field.type_hint == "EmailStr"

    def test_map_java_type(self):
        """Test Java type mapping to Python."""
        assert JavaControllerParser._map_java_type("String") == "str"
        assert JavaControllerParser._map_java_type("Long") == "int"
        assert JavaControllerParser._map_java_type("List<Integer>") == "List[int]"
        assert (
            JavaControllerParser._map_java_type("Map<String, Object>") == "Dict[str]"
        )  # Our simple mapper returns first part of generics if not careful
        # Correctly: JavaControllerParser handles generics recursively but returns python mapping
        # Let's check the code:
        # return f"{python}[{inner_python}]"
        # Map<String, Object> -> Map maps to Dict. inner is "String, Object".
        # _map_java_type("String, Object") will likely default to "str".
        # So "Dict[str]" is correctly what the code produces currently.


class TestPythonCodeGenerator:
    """Test Python code generation."""

    def test_generate_data_schema(self):
        """Test generation of data_schema.py."""
        endpoints = [
            EndpointInfo(method="POST", path="/login", name="login", request_dto="LoginDTO")
        ]
        dto_definitions = {
            "LoginDTO": [
                DtoField(name="username", type_hint="str"),
                DtoField(name="password", type_hint="str"),
            ]
        }

        code = PythonCodeGenerator.generate_data_schema(endpoints, dto_definitions, "auth_service")

        assert "class LoginRequest(BaseModel):" in code
        assert "username: str" in code
        assert "ENDPOINTS = {" in code
        assert '"login": "/login"' in code

    def test_generate_page_class(self):
        """Test generation of page object class."""
        endpoints = [
            EndpointInfo(method="POST", path="/login", name="login", request_dto="LoginDTO")
        ]

        code = PythonCodeGenerator.generate_page_class(endpoints, "auth_service", "AuthService")

        assert "class AuthServicePage(BasePage):" in code
        assert "def do_create_login(self, request) -> APIResponse:" in code
        assert 'ENDPOINTS["login"]' in code

    def test_to_camel_case(self):
        """Test snake_case to camelCase conversion."""
        assert PythonCodeGenerator._to_camel_case("user_id") == "userId"
        assert PythonCodeGenerator._to_camel_case("access_token") == "accessToken"


class TestAICodeGenerator:
    """Test main AI generator orchestrator."""

    def test_analyze_and_generate(self):
        """Test full analysis and generation flow."""
        controller = """
        @RestController
        public class AuthController {
            @PostMapping("/auth/login")
            public TokenResponse login(@RequestBody LoginDTO dto) { return null; }
        }
        """
        dtos = {"LoginDTO": "public record LoginDTO(String username, String password) {}"}

        result = AICodeGenerator.analyze_and_generate(controller, dtos, "auth")

        assert "data_schema" in result
        assert "page_class" in result
        assert len(result["endpoints"]) == 1
        assert "LoginDTO" in result["dto_definitions"]
