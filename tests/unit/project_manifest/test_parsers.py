"""Unit tests for project manifest parsers."""

import pytest

from socialseed_e2e.project_manifest.models import HttpMethod
from socialseed_e2e.project_manifest.parsers import (
    JavaParser,
    NodeParser,
    PythonParser,
    parser_registry,
)


class TestPythonParser:
    """Test Python parser."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Python parser instance."""
        return PythonParser(tmp_path)

    def test_can_parse_python_file(self, parser, tmp_path):
        """Test that parser can handle Python files."""
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')")

        assert parser.can_parse(py_file) is True

    def test_cannot_parse_non_python_file(self, parser, tmp_path):
        """Test that parser rejects non-Python files."""
        java_file = tmp_path / "test.java"
        java_file.write_text("class Test {}")

        assert parser.can_parse(java_file) is False

    def test_detect_fastapi_framework(self, parser):
        """Test FastAPI framework detection."""
        code = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return []
"""
        framework = parser._detect_framework(code)
        assert framework == "fastapi"

    def test_detect_flask_framework(self, parser):
        """Test Flask framework detection."""
        code = """
from flask import Flask

app = Flask(__name__)

@app.route("/users", methods=["GET"])
def get_users():
    return []
"""
        framework = parser._detect_framework(code)
        assert framework == "flask"

    def test_parse_fastapi_endpoints(self, parser, tmp_path):
        """Test parsing FastAPI endpoints."""
        code = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return []

@app.post("/users")
def create_user():
    return {}
"""
        file_path = tmp_path / "routes.py"
        file_path.write_text(code)

        result = parser.parse_file(file_path)

        assert len(result.endpoints) == 2
        assert result.endpoints[0].method == HttpMethod.GET
        assert result.endpoints[0].path == "/users"
        assert result.endpoints[1].method == HttpMethod.POST

    def test_parse_pydantic_models(self, parser, tmp_path):
        """Test parsing Pydantic models."""
        code = """
from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    username: str
    email: str = Field(..., alias="emailAddress")
    age: int = Field(gt=0, lt=150)
"""
        file_path = tmp_path / "models.py"
        file_path.write_text(code)

        result = parser.parse_file(file_path)

        assert len(result.dto_schemas) == 1
        dto = result.dto_schemas[0]
        assert dto.name == "UserRequest"
        assert len(dto.fields) == 3

    def test_parse_environment_variables(self, parser):
        """Test parsing environment variables."""
        code = """
import os

DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.environ.get("API_KEY", "default")
REQUIRED_VAR = os.environ["REQUIRED_VAR"]
"""
        ports, env_vars = parser._parse_config(code, "test.py")

        assert len(env_vars) == 3
        assert any(v.name == "DATABASE_URL" for v in env_vars)
        assert any(v.name == "API_KEY" and v.default_value == "default" for v in env_vars)

    def test_parse_dependencies(self, parser):
        """Test parsing service dependencies."""
        code = """
import requests

response = requests.get("https://auth-service/api/validate")
response2 = requests.post("http://user-service:8080/users")
"""
        deps = parser._parse_dependencies(code, "test.py")

        assert len(deps) >= 1
        # Should find auth-service or user-service
        service_names = [d.service_name for d in deps]
        assert "auth-service" in service_names or "user-service" in service_names


class TestJavaParser:
    """Test Java parser."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Java parser instance."""
        return JavaParser(tmp_path)

    def test_can_parse_java_file(self, parser, tmp_path):
        """Test that parser can handle Java files."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        assert parser.can_parse(java_file) is True

    def test_parse_spring_endpoints(self, parser, tmp_path):
        """Test parsing Spring Boot endpoints."""
        code = """
@RestController
@RequestMapping("/api/v1")
public class UserController {

    @GetMapping("/users")
    public List<User> getUsers() {
        return userService.findAll();
    }

    @PostMapping("/users")
    public ResponseEntity<User> createUser(@RequestBody UserDTO dto) {
        return ResponseEntity.ok(userService.create(dto));
    }

    @DeleteMapping("/users/{id}")
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}
"""
        file_path = tmp_path / "UserController.java"
        file_path.write_text(code)

        result = parser.parse_file(file_path)

        assert len(result.endpoints) == 3

        get_endpoint = next((e for e in result.endpoints if e.method == HttpMethod.GET), None)
        assert get_endpoint is not None
        assert get_endpoint.path == "/users"
        assert get_endpoint.full_path == "/api/v1/users"

    def test_parse_java_record(self, parser, tmp_path):
        """Test parsing Java records."""
        code = """
public record UserDTO(
    String username,
    @Email String email,
    @NotNull @Size(min=8) String password
) {}
"""
        file_path = tmp_path / "UserDTO.java"
        file_path.write_text(code)

        result = parser.parse_file(file_path)

        assert len(result.dto_schemas) == 1
        dto = result.dto_schemas[0]
        assert dto.name == "UserDTO"
        assert len(dto.fields) == 3

    def test_parse_environment_variables(self, parser):
        """Test parsing environment variables in Java."""
        code = """
@Value("${database.url:localhost}")
private String databaseUrl;

@Value("${api.key}")
private String apiKey;

String value = System.getenv("ENV_VAR");
"""
        env_vars = parser._parse_env_vars(code, "Test.java")

        assert len(env_vars) >= 2
        assert any(v.name == "database.url" and v.default_value == "localhost" for v in env_vars)


class TestNodeParser:
    """Test Node.js parser."""

    @pytest.fixture
    def parser(self, tmp_path):
        """Create a Node parser instance."""
        return NodeParser(tmp_path)

    def test_can_parse_js_file(self, parser, tmp_path):
        """Test that parser can handle JavaScript files."""
        js_file = tmp_path / "test.js"
        js_file.write_text("console.log('hello');")

        assert parser.can_parse(js_file) is True

    def test_can_parse_ts_file(self, parser, tmp_path):
        """Test that parser can handle TypeScript files."""
        ts_file = tmp_path / "test.ts"
        ts_file.write_text("const x: string = 'hello';")

        assert parser.can_parse(ts_file) is True

    def test_parse_express_endpoints(self, parser, tmp_path):
        """Test parsing Express.js endpoints."""
        code = """
const express = require('express');
const app = express();

app.get('/users', (req, res) => {
    res.json([]);
});

app.post('/users', (req, res) => {
    res.json({});
});

app.listen(3000);
"""
        file_path = tmp_path / "server.js"
        file_path.write_text(code)

        result = parser.parse_file(file_path)

        assert len(result.endpoints) == 2
        assert result.endpoints[0].method == HttpMethod.GET
        assert result.endpoints[1].method == HttpMethod.POST

    def test_parse_typescript_interface(self, parser, tmp_path):
        """Test parsing TypeScript interfaces."""
        code = """
export interface UserRequest {
    username: string;
    email: string;
    age?: number;
    tags: string[];
}

interface ApiResponse<T> {
    data: T;
    status: number;
}
"""
        file_path = tmp_path / "types.ts"
        file_path.write_text(code)

        result = parser.parse_file(file_path)

        assert len(result.dto_schemas) == 2
        user_dto = next((d for d in result.dto_schemas if d.name == "UserRequest"), None)
        assert user_dto is not None
        assert len(user_dto.fields) == 4


class TestParserRegistry:
    """Test parser registry."""

    def test_default_parsers_registered(self):
        """Test that default parsers are registered."""
        registry = parser_registry

        assert len(registry._parsers) >= 3

    def test_get_parser_for_python_file(self, tmp_path):
        """Test getting parser for Python file."""
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')")

        parser = parser_registry.get_parser(py_file, tmp_path)

        assert parser is not None
        assert isinstance(parser, PythonParser)

    def test_get_parser_for_java_file(self, tmp_path):
        """Test getting parser for Java file."""
        java_file = tmp_path / "Test.java"
        java_file.write_text("class Test {}")

        parser = parser_registry.get_parser(java_file, tmp_path)

        assert parser is not None
        assert isinstance(parser, JavaParser)

    def test_get_parser_for_unsupported_file(self, tmp_path):
        """Test that None is returned for unsupported files."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")

        parser = parser_registry.get_parser(txt_file, tmp_path)

        assert parser is None

    def test_get_parser_by_language(self, tmp_path):
        """Test getting parser by language name."""
        parser = parser_registry.get_parser_for_language("python", tmp_path)

        assert parser is not None
        assert isinstance(parser, PythonParser)

    def test_get_parser_for_unknown_language(self, tmp_path):
        """Test that None is returned for unknown language."""
        parser = parser_registry.get_parser_for_language("ruby", tmp_path)

        assert parser is None
