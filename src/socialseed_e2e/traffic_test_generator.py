"""
Traffic-based Test Generator - Generates E2E tests from captured traffic.

This module implements EPIC-003:
- T01: Group dependent call flows (Login -> GetProfile) by JWT/session
- T02: Map HTTP sequences to framework commands
- T03: Generate modular test scripts with assertions
- T04: Place tests in service folders

Extends the existing shadow_runner/test_generator.py
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import re


@dataclass
class FlowGroup:
    """A group of related HTTP calls (e.g., Login -> GetProfile)."""
    session_id: str
    interactions: List[Any] = field(default_factory=list)
    flow_type: str = "unknown"
    entry_point: Optional[str] = None


@dataclass
class GeneratedTestModule:
    """A complete test module file."""
    filename: str
    module_name: str
    code: str
    description: str
    dependencies: List[str] = field(default_factory=list)


class TrafficFlowAnalyzer:
    """Analyze and group traffic into logical flows."""
    
    def __init__(self):
        self._session_patterns = [
            r"authorization",
            r"bearer",
            r"token",
            r"session",
            r"jwt",
            r"auth",
        ]
    
    def extract_session_id(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract session/JWT identifier from headers."""
        # Check Authorization header
        auth = headers.get("Authorization") or headers.get("authorization")
        if auth:
            if auth.lower().startswith("bearer "):
                token = auth[7:]
                return f"jwt_{token[:20]}"
            return f"auth_{auth[:20]}"
        
        # Check cookie
        cookie = headers.get("Cookie") or headers.get("cookie")
        if cookie:
            return f"cookie_{hash(cookie) % 10000}"
        
        return None
    
    def identify_flow_type(self, path: str, method: str) -> str:
        """Identify the type of flow based on endpoint."""
        path_lower = path.lower()
        
        if "login" in path_lower or "auth" in path_lower:
            return "auth_flow"
        if "register" in path_lower or "signup" in path_lower:
            return "register_flow"
        if "profile" in path_lower or "user" in path_lower and method == "GET":
            return "profile_flow"
        if "refresh" in path_lower:
            return "refresh_flow"
        if "logout" in path_lower:
            return "logout_flow"
        if any(x in path_lower for x in ["post", "create", "add"]):
            return "create_flow"
        if any(x in path_lower for x in ["update", "edit", "patch"]):
            return "update_flow"
        if any(x in path_lower for x in ["delete", "remove"]):
            return "delete_flow"
        
        return "generic_flow"
    
    def group_by_session(self, interactions: List[Any]) -> Dict[str, FlowGroup]:
        """Group interactions by session/JWT.
        
        T01: Agrupar flujos de llamadas dependientes en base al JWT o session ID.
        """
        groups: Dict[str, FlowGroup] = defaultdict(lambda: FlowGroup(session_id=""))
        
        for interaction in interactions:
            session_id = self.extract_session_id(interaction.request.headers)
            
            if not session_id:
                # Create anonymous session
                session_id = f"anon_{hash(str(interaction)) % 10000}"
            
            if session_id not in groups:
                flow_type = self.identify_flow_type(
                    interaction.request.path,
                    interaction.request.method
                )
                groups[session_id] = FlowGroup(
                    session_id=session_id,
                    flow_type=flow_type,
                    entry_point=interaction.request.path
                )
            
            groups[session_id].interactions.append(interaction)
        
        # Sort interactions within each group by sequence
        for group in groups.values():
            group.interactions.sort(key=lambda x: getattr(x, 'sequence_number', 0))
        
        return dict(groups)


class FlowToCommandMapper:
    """Map HTTP sequences to framework commands."""
    
    def __init__(self):
        self._endpoint_to_command = {
            "login": "do_login",
            "register": "do_register",
            "logout": "do_logout",
            "refresh": "do_refresh_token",
            "profile": "do_get_profile",
            "user": "do_get_user",
            "post": "do_create_post",
            "users": "do_get_users",
        }
    
    def map_interaction(self, path: str, method: str) -> Dict[str, str]:
        """Map an HTTP interaction to framework commands.
        
        T02: Mapear secuencias HTTP a llamadas nativas del framework socialseed-e2e.
        """
        path_lower = path.lower()
        method_upper = method.upper()
        
        # Find matching command
        command = "do_request"
        for key, cmd in self._endpoint_to_command.items():
            if key in path_lower:
                command = cmd
                break
        
        # Map HTTP method to Playwright method
        http_method = {
            "GET": "get",
            "POST": "post",
            "PUT": "put",
            "PATCH": "patch",
            "DELETE": "delete",
        }.get(method_upper, "get")
        
        return {
            "command": command,
            "http_method": http_method,
            "path": path,
            "method": method_upper,
        }
    
    def map_flow(self, flow: FlowGroup) -> List[Dict[str, str]]:
        """Map an entire flow to commands."""
        return [
            self.map_interaction(i.request.path, i.request.method)
            for i in flow.interactions
        ]


class ModularTestGenerator:
    """Generate modular test scripts from traffic flows."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.flow_analyzer = TrafficFlowAnalyzer()
        self.command_mapper = FlowToCommandMapper()
    
    def generate_test_module(
        self,
        interactions: List[Any],
        module_number: int = 1,
    ) -> GeneratedTestModule:
        """Generate a test module from interactions.
        
        T03: Generar scripts modulares con assertions auto-generados.
        """
        # Group by session
        flow_groups = self.flow_analyzer.group_by_session(interactions)
        
        if not flow_groups:
            return self._generate_empty_module(module_number)
        
        # Use the first flow group
        main_flow = next(iter(flow_groups.values()))
        
        # Generate module code
        code = self._generate_module_code(main_flow, module_number)
        
        filename = f"{module_number:02d}_{main_flow.flow_type}.py"
        module_name = f"{main_flow.flow_type}_test"
        
        return GeneratedTestModule(
            filename=filename,
            module_name=module_name,
            code=code,
            description=f"Auto-generated test for {main_flow.flow_type}",
            dependencies=self._get_dependencies(main_flow),
        )
    
    def _generate_module_code(self, flow: FlowGroup, module_number: int) -> str:
        """Generate Python test module code."""
        lines = [
            f'"""Test module {module_number}: {flow.flow_type}."""',
            "",
            f"from services.{self.service_name}.data_schema import (",
            "    LoginRequest,",
            "    ENDPOINTS,",
            "    TEST_USER,",
            ")",
            "",
            "from typing import TYPE_CHECKING",
            "if TYPE_CHECKING:",
            f"    from services.{self.service_name}.{self.service_name}_page import {self.service_name.title()}Page",
            "",
            "",
            f"def run(page: \"{self.service_name.title()}Page\"):",
            f'    """Test: {flow.flow_type}."""',
            "",
        ]
        
        # Add comments for each step
        for i, interaction in enumerate(flow.interactions, 1):
            path = interaction.request.path
            method = interaction.request.method
            
            lines.append(f"    # Step {i}: {method} {path}")
            
            if "login" in path.lower():
                lines.append("    login_data = LoginRequest(")
                lines.append(f'        email=TEST_USER["email"],')
                lines.append(f'        password=TEST_USER["password"]')
                lines.append("    )")
                lines.append("    response = page.do_login(login_data)")
                lines.append('    assert response.ok, f"Login failed: {response.status}"')
            elif "logout" in path.lower():
                lines.append("    response = page.do_logout()")
                lines.append('    assert response.ok, f"Logout failed: {response.status}"')
            else:
                lines.append(f'    response = page.get("{path}")')
                lines.append('    assert response.ok, f"Request failed: {response.status}"')
            
            lines.append("")
        
        lines.append(f'    print("✓ {flow.flow_type} completed")')
        
        return "\n".join(lines)
    
    def _generate_empty_module(self, module_number: int) -> GeneratedTestModule:
        """Generate an empty module."""
        code = f'''"""Test module {module_number}: Empty test module."""
def run(page):
    """Empty test module - no traffic captured."""
    print("No traffic to test")
'''
        return GeneratedTestModule(
            filename=f"{module_number:02d}_empty.py",
            module_name="empty_test",
            code=code,
            description="Empty test module",
            dependencies=[],
        )
    
    def _get_dependencies(self, flow: FlowGroup) -> List[str]:
        """Get dependencies for this flow."""
        deps = set()
        
        for interaction in flow.interactions:
            path = interaction.request.path.lower()
            if "login" in path:
                deps.add("auth")
            if "register" in path:
                deps.add("register")
        
        return list(deps)


class TestIntegrator:
    """Integrate generated tests into service folders.
    
    T04: Integrador de Tests que coloque los scripts en la carpeta del servicio.
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    def integrate_test_module(
        self,
        test_module: GeneratedTestModule,
        service_name: str,
    ) -> Path:
        """Integrate test module into service folder."""
        # Create modules directory
        modules_dir = self.base_path / "services" / service_name / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py if needed
        init_file = modules_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Test modules for service."""\n')
        
        # Write test file
        test_file = modules_dir / test_module.filename
        test_file.write_text(test_module.code)
        
        return test_file
    
    def integrate_multiple_modules(
        self,
        test_modules: List[GeneratedTestModule],
        service_name: str,
    ) -> List[Path]:
        """Integrate multiple test modules."""
        paths = []
        
        for module in test_modules:
            path = self.integrate_test_module(module, service_name)
            paths.append(path)
        
        return paths


def generate_tests_from_captured_traffic(
    captured_traffic: List[Any],
    service_name: str,
    output_path: Path,
    module_count: int = 1,
) -> List[Path]:
    """Convenience function to generate and integrate tests from captured traffic.
    
    Usage:
        from socialseed_e2e.traffic_test_generator import generate_tests_from_captured_traffic
        
        # After capturing traffic with TrafficSniffer
        traffic = sniffer.get_traffic()
        
        # Generate tests
        test_files = generate_tests_from_captured_traffic(
            traffic,
            "auth-service",
            Path(".")
        )
    """
    generator = ModularTestGenerator(service_name)
    
    test_modules = []
    for i in range(module_count):
        module = generator.generate_test_module(
            captured_traffic,
            module_number=i + 1,
        )
        test_modules.append(module)
    
    integrator = TestIntegrator(output_path)
    paths = integrator.integrate_multiple_modules(test_modules, service_name)
    
    return paths


if __name__ == "__main__":
    # Example usage
    print("Traffic-based Test Generator")
    print("=" * 40)
    print()
    print("This module provides:")
    print("  - TrafficFlowAnalyzer: Groups traffic by session/JWT")
    print("  - FlowToCommandMapper: Maps HTTP to framework commands")
    print("  - ModularTestGenerator: Generates test modules")
    print("  - TestIntegrator: Places tests in service folders")
    print()
    print("Usage:")
    print("  from socialseed_e2e.traffic_test_generator import generate_tests_from_captured_traffic")
    print("  test_files = generate_tests_from_captured_traffic(traffic, 'auth-service', Path('.'))")