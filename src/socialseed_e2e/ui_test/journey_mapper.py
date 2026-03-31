"""
Semantic User Journey Mapping - EPIC-024
Generates UI test drafts from HTTP traffic analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ScreenType(str, Enum):
    """Types of frontend screens."""
    LOGIN = "login"
    REGISTER = "register"
    DASHBOARD = "dashboard"
    PROFILE = "profile"
    SETTINGS = "settings"
    LIST_VIEW = "list_view"
    DETAIL_VIEW = "detail_view"
    FORM = "form"
    UNKNOWN = "unknown"


@dataclass
class UIStep:
    """A UI step in a user journey."""
    step_id: str
    screen_type: ScreenType
    screen_name: str
    api_calls: List[Dict[str, Any]] = field(default_factory=list)
    form_fields: List[str] = field(default_factory=list)
    selectors: Dict[str, str] = field(default_factory=dict)


@dataclass
class UserJourney:
    """A complete user journey."""
    journey_id: str
    name: str
    steps: List[UIStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class JourneyMapper:
    """Maps HTTP traffic to user journeys."""
    
    def __init__(self):
        self._screen_patterns = {
            "login": ["auth/login", "auth/token", "/api/v1/auth"],
            "register": ["auth/register", "users/create", "/signup"],
            "dashboard": ["dashboard", "stats", "/api/v1/home"],
            "profile": ["users/me", "profile", "/api/v1/user"],
            "settings": ["settings", "config", "/api/v1/settings"],
            "list": ["list", "all", "/api/v1/"],
            "detail": ["get", "/api/v1/", "/id/"],
        }
        self._journeys: List[UserJourney] = []
    
    def analyze_traffic(
        self,
        traffic_logs: List[Dict[str, Any]],
    ) -> UserJourney:
        """Analyze traffic to create user journey."""
        import uuid
        
        journey = UserJourney(
            journey_id=f"journey-{uuid.uuid4().hex[:8]}",
            name="Auto-generated Journey",
        )
        
        current_screen = None
        current_step = None
        
        for log in traffic_logs:
            path = log.get("path", "")
            method = log.get("method", "GET")
            body = log.get("request_body") or {}
            
            screen = self._detect_screen(path)
            
            if screen != current_screen or current_step is None:
                if current_step:
                    journey.steps.append(current_step)
                
                step_id = f"step-{len(journey.steps)}"
                current_step = UIStep(
                    step_id=step_id,
                    screen_type=screen,
                    screen_name=screen.value,
                )
                current_screen = screen
            
            current_step.api_calls.append({
                "method": method,
                "path": path,
                "status": log.get("status_code"),
            })
            
            if body:
                for field_name in body.keys():
                    if field_name not in current_step.form_fields:
                        current_step.form_fields.append(field_name)
        
        if current_step:
            journey.steps.append(current_step)
        
        self._journeys.append(journey)
        return journey
    
    def _detect_screen(self, path: str) -> ScreenType:
        """Detect screen type from API path."""
        path_lower = path.lower()
        
        for screen_type, patterns in self._screen_patterns.items():
            for pattern in patterns:
                if pattern in path_lower:
                    return ScreenType(screen_type)
        
        return ScreenType.UNKNOWN
    
    def generate_playwright_draft(self, journey: UserJourney) -> str:
        """Generate Playwright UI test draft."""
        code = '''"""
UI Test Draft - Auto-generated from HTTP traffic
EPIC-024: Semantic User Journey Mapping
"""

import pytest
from playwright.sync_api import Page, expect


'''
        
        for step in journey.steps:
            code += f'\ndef test_{step.screen_name}(page: Page):\n'
            code += f'    """Test {step.screen_name} screen."""\n\n'
            
            if step.form_fields:
                code += f'    # Form fields detected: {step.form_fields}\n'
                for field in step.form_fields:
                    semantic_selector = self._generate_semantic_selector(field)
                    code += f'    page.locator("{semantic_selector}").fill("test_value")\n'
            
            code += '\n'
            
            for call in step.api_calls[:3]:
                code += f'    # API: {call["method"]} {call["path"]}\n'
            
            code += '\n'
        
        return code
    
    def _generate_semantic_selector(self, field_name: str) -> str:
        """Generate semantic selector from field name."""
        clean_name = field_name.lower().replace("_", "-")
        
        selectors = [
            f'input[name="{clean_name}"]',
            f'input[id="{clean_name}"]',
            f'[data-testid="{clean_name}"]',
            f'input[placeholder*="{clean_name}"]',
        ]
        
        return selectors[0]
    
    def get_journeys(self) -> List[Dict[str, Any]]:
        """Get all mapped journeys."""
        return [
            {
                "journey_id": j.journey_id,
                "name": j.name,
                "steps": [
                    {
                        "step_id": s.step_id,
                        "screen_type": s.screen_type.value,
                        "screen_name": s.screen_name,
                        "api_calls": len(s.api_calls),
                        "form_fields": s.form_fields,
                    }
                    for s in j.steps
                ],
                "created_at": j.created_at.isoformat(),
            }
            for j in self._journeys
        ]
    
    def export_sequence_diagram(self, journey: UserJourney) -> str:
        """Export journey as sequence diagram (Mermaid)."""
        diagram = "```mermaid\n"
        diagram += "sequenceDiagram\n"
        
        for i, step in enumerate(journey.steps):
            if i == 0:
                diagram += f"    User->>+{step.screen_name}: Load\n"
            
            for call in step.api_calls:
                diagram += f"    {step.screen_name}->>+API: {call['method']} {call['path']}\n"
                diagram += f"    API-->>-{step.screen_name}: Response\n"
            
            if i < len(journey.steps) - 1:
                next_step = journey.steps[i + 1]
                diagram += f"    {step.screen_name}->>+{next_step.screen_name}: Navigate\n"
            else:
                diagram += f"    {step.screen_name}-->>-User: Complete\n"
        
        diagram += "```"
        return diagram


_global_mapper: Optional[JourneyMapper] = None


def get_journey_mapper() -> JourneyMapper:
    """Get global journey mapper."""
    global _global_mapper
    if _global_mapper is None:
        _global_mapper = JourneyMapper()
    return _global_mapper
