"""Unit tests for project manifest generator."""

import json

import pytest

from socialseed_e2e.project_manifest.generator import ManifestGenerator
from socialseed_e2e.project_manifest.models import EnvironmentVariable, HttpMethod


class TestManifestGenerator:
    """Test ManifestGenerator class."""

    @pytest.fixture
    def empty_project(self, tmp_path):
        """Create an empty project structure."""
        return tmp_path

    @pytest.fixture
    def python_project(self, tmp_path):
        """Create a sample Python project."""
        # Create FastAPI app
        api_dir = tmp_path / "api"
        api_dir.mkdir()

        (api_dir / "main.py").write_text(
            """
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserRequest(BaseModel):
    username: str
    email: str

@app.get("/users")
def get_users():
    return []

@app.post("/users")
def create_user(request: UserRequest):
    return {}
"""
        )

        # Create config
        (tmp_path / "config.py").write_text(
            """
import os

PORT = int(os.getenv("PORT", "8080"))
DATABASE_URL = os.getenv("DATABASE_URL")
"""
        )

        return tmp_path

    @pytest.fixture
    def java_project(self, tmp_path):
        """Create a sample Java project."""
        # Create Spring Boot controller
        src_dir = tmp_path / "src" / "main" / "java" / "com" / "example"
        src_dir.mkdir(parents=True)

        (src_dir / "UserController.java").write_text(
            """
package com.example;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
public class UserController {

    @GetMapping("/users")
    public List<User> getUsers() {
        return userService.findAll();
    }

    @PostMapping("/users")
    public User createUser(@RequestBody UserDTO dto) {
        return userService.create(dto);
    }
}
"""
        )

        (src_dir / "UserDTO.java").write_text(
            """
package com.example;

public record UserDTO(
    String username,
    String email
) {}
"""
        )

        return tmp_path

    def test_init(self, empty_project):
        """Test generator initialization."""
        generator = ManifestGenerator(empty_project)

        assert generator.project_root == empty_project
        assert generator.manifest_path == empty_project / "project_knowledge.json"

    def test_generate_empty_project(self, empty_project):
        """Test generating manifest for empty project."""
        generator = ManifestGenerator(empty_project)
        manifest = generator.generate()

        assert manifest is not None
        assert manifest.project_name == empty_project.name
        assert len(manifest.services) == 0

    def test_generate_python_project(self, python_project):
        """Test generating manifest for Python project."""
        generator = ManifestGenerator(python_project)
        manifest = generator.generate()

        assert manifest is not None
        assert len(manifest.services) >= 1

        # Find API service
        api_service = next((s for s in manifest.services if "api" in s.name), None)
        assert api_service is not None

        assert api_service.language == "python"
        assert api_service.framework == "fastapi"
        assert len(api_service.endpoints) == 2

        # Check endpoints
        get_endpoint = next((e for e in api_service.endpoints if e.method == HttpMethod.GET), None)
        assert get_endpoint is not None
        assert get_endpoint.path == "/users"

        # Check DTOs
        assert len(api_service.dto_schemas) == 1
        assert api_service.dto_schemas[0].name == "UserRequest"

    def test_generate_java_project(self, java_project):
        """Test generating manifest for Java project."""
        generator = ManifestGenerator(java_project)
        manifest = generator.generate()

        assert manifest is not None

        # Should find Java service
        java_service = next((s for s in manifest.services if s.language == "java"), None)
        assert java_service is not None

        assert java_service.framework == "spring"
        assert len(java_service.endpoints) == 2

    def test_manifest_saved_to_disk(self, python_project):
        """Test that manifest is saved to disk."""
        generator = ManifestGenerator(python_project)
        manifest = generator.generate()

        assert generator.manifest_path.exists()

        # Verify content
        content = generator.manifest_path.read_text()
        data = json.loads(content)
        assert data["project_name"] == manifest.project_name

    def test_get_existing_manifest(self, python_project):
        """Test getting existing manifest."""
        generator = ManifestGenerator(python_project)

        # Generate first
        manifest1 = generator.generate()

        # Get manifest
        manifest2 = generator.get_manifest()

        assert manifest2 is not None
        assert manifest2.project_name == manifest1.project_name

    def test_force_full_scan(self, python_project):
        """Test forcing a full scan."""
        generator = ManifestGenerator(python_project)

        # Generate initial manifest
        manifest1 = generator.generate()
        first_update = manifest1.last_updated

        # Force full scan
        manifest2 = generator.generate(force_full_scan=True)

        assert manifest2.last_updated > first_update


class TestManifestGeneratorSmartSync:
    """Test smart sync functionality."""

    @pytest.fixture
    def python_project(self, tmp_path):
        """Create a sample Python project."""
        api_dir = tmp_path / "api"
        api_dir.mkdir()

        (api_dir / "routes.py").write_text(
            """
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return []
"""
        )

        return tmp_path

    def test_smart_sync_no_changes(self, python_project):
        """Test smart sync when no changes detected."""
        generator = ManifestGenerator(python_project)

        # Initial generation
        manifest1 = generator.generate()
        first_update = manifest1.last_updated

        # Generate again without changes
        manifest2 = generator.generate()

        # Should be same manifest
        assert manifest2.last_updated == first_update

    def test_smart_sync_with_file_change(self, python_project):
        """Test smart sync detects file changes."""
        generator = ManifestGenerator(python_project)

        # Initial generation
        manifest1 = generator.generate()
        assert len(manifest1.services[0].endpoints) == 1

        # Modify file - add new endpoint
        routes_file = python_project / "api" / "routes.py"
        routes_file.write_text(
            """
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return []

@app.post("/users")
def create_user():
    return {}
"""
        )

        # Generate again - should detect change
        manifest2 = generator.generate()

        # Should have 2 endpoints now
        assert len(manifest2.services[0].endpoints) == 2

    def test_smart_sync_with_new_file(self, python_project):
        """Test smart sync detects new files."""
        generator = ManifestGenerator(python_project)

        # Initial generation
        manifest1 = generator.generate()
        initial_services = len(manifest1.services)

        # Add new service
        auth_dir = python_project / "auth"
        auth_dir.mkdir()
        (auth_dir / "routes.py").write_text(
            """
from fastapi import FastAPI

app = FastAPI()

@app.post("/login")
def login():
    return {}
"""
        )

        # Generate again - should detect new file
        manifest2 = generator.generate()

        # Should have more services
        assert len(manifest2.services) > initial_services


class TestManifestGeneratorDetection:
    """Test project detection features."""

    def test_detect_project_name_from_directory(self, tmp_path):
        """Test project name detection from directory name."""
        generator = ManifestGenerator(tmp_path)
        name = generator._detect_project_name()

        assert name == tmp_path.name

    def test_detect_project_name_from_package_json(self, tmp_path):
        """Test project name detection from package.json."""
        (tmp_path / "package.json").write_text('{"name": "my-awesome-api"}')

        generator = ManifestGenerator(tmp_path)
        name = generator._detect_project_name()

        assert name == "my-awesome-api"

    def test_detect_project_name_from_pyproject(self, tmp_path):
        """Test project name detection from pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text(
            """
[project]
name = "my-python-api"
version = "1.0.0"
"""
        )

        generator = ManifestGenerator(tmp_path)
        name = generator._detect_project_name()

        assert name == "my-python-api"

    def test_detect_global_env_vars(self, tmp_path):
        """Test detection of global environment variables."""
        from socialseed_e2e.project_manifest.models import ServiceInfo

        generator = ManifestGenerator(tmp_path)

        services = [
            ServiceInfo(
                name="test",
                language="python",
                root_path=str(tmp_path),
                environment_vars=[
                    EnvironmentVariable(name="DATABASE_URL", required=True),
                    EnvironmentVariable(name="JWT_SECRET", required=True),
                ],
            ),
        ]

        global_vars = generator._detect_global_env_vars(services)

        assert len(global_vars) > 0
        assert any(v.name == "DATABASE_URL" for v in global_vars)
        assert any(v.name == "JWT_SECRET" for v in global_vars)


class TestManifestGeneratorExcludePatterns:
    """Test exclude patterns functionality."""

    def test_default_exclude_patterns(self, empty_project):
        """Test that default exclude patterns are set."""
        generator = ManifestGenerator(empty_project)

        assert len(generator.exclude_patterns) > 0
        assert "**/node_modules/**" in generator.exclude_patterns
        assert "**/__pycache__/**" in generator.exclude_patterns

    def test_custom_exclude_patterns(self, empty_project):
        """Test custom exclude patterns."""
        custom_patterns = ["**/custom/**", "**/*.tmp"]
        generator = ManifestGenerator(empty_project, exclude_patterns=custom_patterns)

        assert generator.exclude_patterns == custom_patterns

    def test_should_exclude(self, empty_project):
        """Test file exclusion logic."""
        generator = ManifestGenerator(empty_project)

        # Should exclude
        assert generator._should_exclude(empty_project / "node_modules" / "test.js") is True
        assert (
            generator._should_exclude(empty_project / "__pycache__" / "test.cpython-39.pyc") is True
        )

        # Should not exclude
        assert generator._should_exclude(empty_project / "src" / "main.py") is False
