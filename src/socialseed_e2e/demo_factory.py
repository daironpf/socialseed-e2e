"""Demo Factory for socialseed-e2e

A factory system to generate demo APIs with consistent patterns.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from socialseed_e2e.utils import TemplateEngine


@dataclass
class DemoConfig:
    """Configuration for a demo."""

    name: str
    port: int
    title: str
    description: str
    entities: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)


class DemoFactory(ABC):
    """Base class for demo factories."""

    def __init__(self, target_path: Path, demo_name: str, port: int):
        self.target_path = target_path
        self.demo_name = demo_name
        self.port = port
        self.engine = TemplateEngine()
        self.service_name = f"{demo_name}-demo"

    @abstractmethod
    def get_config(self) -> DemoConfig:
        """Return demo configuration."""
        pass

    def create_all(self) -> dict[str, bool]:
        """Create all demo components."""
        results = {}
        config = self.get_config()

        results["api"] = self.create_api_server(config)
        results["service_page"] = self.create_service_page(config)
        results["data_schema"] = self.create_data_schema(config)
        results["config"] = self.create_config(config)
        results["tests"] = self.create_tests(config)

        return results

    def create_api_server(self, config: DemoConfig) -> bool:
        """Create the API server file."""
        demo_path = self.target_path / "demos" / self.demo_name
        demo_path.mkdir(parents=True, exist_ok=True)

        template_name = f"api_{self.demo_name}_demo.py.template"
        output_file = demo_path / f"api_{self.demo_name}_demo.py"

        try:
            self.engine.render_to_file(
                template_name,
                self._get_template_vars(config),
                str(output_file),
                overwrite=True,
            )
            return True
        except FileNotFoundError:
            # Use generic template if specific not found
            self.engine.render_to_file(
                "api_generic_demo.py.template",
                self._get_template_vars(config),
                str(output_file),
                overwrite=True,
            )
            return True
        except Exception:
            return False

    def create_service_page(self, config: DemoConfig) -> bool:
        """Create the service page file."""
        service_path = self.target_path / "services" / self.service_name
        service_path.mkdir(parents=True, exist_ok=True)
        (service_path / "modules").mkdir(exist_ok=True)
        (service_path / "__init__.py").write_text("")
        (service_path / "modules" / "__init__.py").write_text("")

        template_name = f"{self.demo_name}_service_page.py.template"
        output_file = service_path / f"{self.demo_name}_page.py"

        try:
            self.engine.render_to_file(
                template_name,
                self._get_template_vars(config),
                str(output_file),
                overwrite=True,
            )
            return True
        except FileNotFoundError:
            self.engine.render_to_file(
                "service_page.py.template",
                self._get_template_vars(config),
                str(output_file),
                overwrite=True,
            )
            return True
        except Exception:
            return False

    def create_data_schema(self, config: DemoConfig) -> bool:
        """Create the data schema file."""
        service_path = self.target_path / "services" / self.service_name
        template_name = f"{self.demo_name}_data_schema.py.template"
        output_file = service_path / "data_schema.py"

        try:
            self.engine.render_to_file(
                template_name,
                self._get_template_vars(config),
                str(output_file),
                overwrite=True,
            )
            return True
        except FileNotFoundError:
            self.engine.render_to_file(
                "data_schema.py.template",
                self._get_template_vars(config),
                str(output_file),
                overwrite=True,
            )
            return True
        except Exception:
            return False

    def create_config(self, config: DemoConfig) -> bool:
        """Create the config file."""
        service_path = self.target_path / "services" / self.service_name
        template_name = f"{self.demo_name}_config.py.template"
        output_file = service_path / "config.py"

        try:
            self.engine.render_to_file(
                template_name,
                self._get_template_vars(config),
                str(output_file),
                overwrite=True,
            )
            return True
        except FileNotFoundError:
            self.engine.render_to_file(
                "config.py.template",
                self._get_template_vars(config),
                str(output_file),
                overwrite=True,
            )
            return True
        except Exception:
            return False

    def create_tests(self, config: DemoConfig) -> bool:
        """Create test files."""
        modules_path = self.target_path / "services" / self.service_name / "modules"
        modules_path.mkdir(parents=True, exist_ok=True)

        test_names = ["health_check", "list", "create", "get", "update", "delete"]
        created = 0

        for i, test_name in enumerate(test_names, 1):
            template_name = f"generic_test_{test_name}.py.template"
            output_file = modules_path / f"0{i}_{test_name}.py"

            try:
                self.engine.render_to_file(
                    template_name,
                    self._get_template_vars(config),
                    str(output_file),
                    overwrite=True,
                )
                created += 1
            except FileNotFoundError:
                # Skip if template not found
                continue

        return created > 0

    def _get_template_vars(self, config: DemoConfig) -> dict[str, Any]:
        """Get template variables."""
        return {
            "demo_name": self.demo_name,
            "service_name": self.service_name,
            "port": self.port,
            "title": config.title,
            "description": config.description,
            "entities": config.entities,
            "features": config.features,
        }


class GenericDemoFactory(DemoFactory):
    """Generic demo factory for simple APIs."""

    def get_config(self) -> DemoConfig:
        return DemoConfig(
            name=self.demo_name,
            port=self.port,
            title=f"{self.demo_name.title()} Demo API",
            description=f"A simple {self.demo_name} API for testing",
            entities=["item"],
            features=["CRUD"],
        )


def create_demo_factory(demo_name: str, port: int, target_path: Path) -> DemoFactory:
    """Create a demo factory based on name."""
    return GenericDemoFactory(target_path, demo_name, port)
