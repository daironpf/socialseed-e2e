"""Unit tests for deep scanner."""

import pytest

from socialseed_e2e.project_manifest.deep_scanner import (
    DeepScanner,
    EnvironmentDetector,
    TechStackDetector,
)


class TestTechStackDetector:
    """Tests for TechStackDetector."""

    @pytest.fixture
    def detector(self):
        """Create a TechStackDetector fixture."""
        return TechStackDetector()

    def test_detect_fastapi(self, tmp_path, detector):
        """Test FastAPI detection."""
        # Create a FastAPI file
        app_file = tmp_path / "main.py"
        app_file.write_text(
            """
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
"""
        )

        frameworks = detector.detect(tmp_path)

        # Should detect FastAPI
        fastapi_detection = [f for f in frameworks if f["framework"] == "fastapi"]
        assert len(fastapi_detection) > 0
        assert fastapi_detection[0]["language"] == "python"
        assert fastapi_detection[0]["confidence"] > 0

    def test_detect_flask(self, tmp_path, detector):
        """Test Flask detection."""
        app_file = tmp_path / "app.py"
        app_file.write_text(
            """
from flask import Flask

app = Flask(__name__)

@app.route('/hello')
def hello():
    return 'Hello World'
"""
        )

        frameworks = detector.detect(tmp_path)

        flask_detection = [f for f in frameworks if f["framework"] == "flask"]
        assert len(flask_detection) > 0
        assert flask_detection[0]["language"] == "python"

    def test_detect_express(self, tmp_path, detector):
        """Test Express.js detection."""
        app_file = tmp_path / "server.js"
        app_file.write_text(
            """
const express = require('express');
const app = express();

app.get('/users', (req, res) => {
    res.json({ users: [] });
});
"""
        )

        frameworks = detector.detect(tmp_path)

        express_detection = [f for f in frameworks if f["framework"] == "express"]
        assert len(express_detection) > 0
        assert express_detection[0]["language"] == "javascript"

    def test_detect_spring(self, tmp_path, detector):
        """Test Spring Boot detection."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text(
            """
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
}
"""
        )

        frameworks = detector.detect(tmp_path)

        spring_detection = [f for f in frameworks if f["framework"] == "spring"]
        assert len(spring_detection) > 0
        assert spring_detection[0]["language"] == "java"

    def test_no_framework(self, tmp_path, detector):
        """Test detection with no recognizable framework."""
        random_file = tmp_path / "script.txt"
        random_file.write_text("This is just a random text file")

        frameworks = detector.detect(tmp_path)

        # Should return empty list or very low confidence results
        assert isinstance(frameworks, list)


class TestEnvironmentDetector:
    """Tests for EnvironmentDetector."""

    @pytest.fixture
    def detector(self):
        """Create an EnvironmentDetector fixture."""
        return EnvironmentDetector()

    def test_detect_docker_compose(self, tmp_path, detector):
        """Test docker-compose detection."""
        docker_file = tmp_path / "docker-compose.yml"
        docker_file.write_text(
            """
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://localhost/db
      - API_KEY=secret
"""
        )

        config = detector.detect(tmp_path)

        assert len(config["ports"]) > 0
        assert config["ports"][0].port == 8000
        assert len(config["env_vars"]) > 0
        assert "docker-compose.yml" in config["config_files"][0]

    def test_detect_env_file(self, tmp_path, detector):
        """Test .env file detection."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
DATABASE_URL=postgresql://localhost:5432/mydb
API_KEY=secret123
DEBUG=true
"""
        )

        config = detector.detect(tmp_path)

        env_vars = {v.name: v.default_value for v in config["env_vars"]}
        assert "DATABASE_URL" in env_vars
        assert "API_KEY" in env_vars
        assert ".env" in config["config_files"][0]

    def test_detect_spring_properties(self, tmp_path, detector):
        """Test Spring Boot properties detection."""
        props_file = tmp_path / "application.properties"
        props_file.write_text(
            """
server.port=8080
spring.datasource.url=jdbc:postgresql://localhost:5432/db
"""
        )

        config = detector.detect(tmp_path)

        assert len(config["ports"]) > 0
        assert config["ports"][0].port == 8080
        assert "application.properties" in config["config_files"][0]


class TestDeepScanner:
    """Tests for DeepScanner."""

    def test_scan_finds_services(self, tmp_path):
        """Test that scan finds services."""
        # Create a simple FastAPI app
        app_file = tmp_path / "main.py"
        app_file.write_text(
            """
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
        )

        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("PORT=8000")

        scanner = DeepScanner(str(tmp_path))
        result = scanner.scan()

        assert "frameworks" in result
        assert "services" in result
        assert "recommendations" in result
        assert "environment" in result

    def test_scan_recommendations(self, tmp_path):
        """Test that scan generates recommendations."""
        # Create FastAPI app
        app_file = tmp_path / "main.py"
        app_file.write_text(
            """
from fastapi import FastAPI
app = FastAPI()
"""
        )

        scanner = DeepScanner(str(tmp_path))
        result = scanner.scan()

        recommendations = result["recommendations"]
        assert "base_url" in recommendations
        assert "health_endpoint" in recommendations

    def test_scan_empty_project(self, tmp_path):
        """Test scanning an empty project."""
        scanner = DeepScanner(str(tmp_path))
        result = scanner.scan()

        # Should handle empty projects gracefully
        assert result["project_root"] == str(tmp_path)
        assert isinstance(result["frameworks"], list)
        assert isinstance(result["services"], list)
