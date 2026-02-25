"""Auth flow generator for documenting authentication flows.

This module generates authentication flow documentation based on
detected endpoints and schemas.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AuthFlow:
    """Represents an authentication flow."""

    name: str
    description: str
    steps: List[Dict[str, Any]]
    endpoints_used: List[str]
    requires: List[str]
    returns: List[str]


class AuthFlowGenerator:
    """Generates authentication flow documentation."""

    # Known auth flow patterns
    FLOW_PATTERNS = {
        "register": {
            "endpoints": ["register", "signup", "create-user"],
            "returns": ["accessToken", "refreshToken", "user"],
        },
        "login": {
            "endpoints": ["login", "authenticate", "signin"],
            "returns": ["accessToken", "refreshToken", "user"],
        },
        "logout": {
            "endpoints": ["logout", "signout"],
            "returns": [],
        },
        "refresh_token": {
            "endpoints": ["refresh", "token/refresh"],
            "returns": ["accessToken", "refreshToken"],
        },
        "forgot_password": {
            "endpoints": ["forgot-password", "forgot", "reset-password-request"],
            "returns": [],
        },
        "reset_password": {
            "endpoints": ["reset-password", "resetpwd"],
            "returns": [],
        },
        "verify_email": {
            "endpoints": ["verify-email", "verify", "confirm-email"],
            "returns": [],
        },
        "change_password": {
            "endpoints": ["change-password", "update-password"],
            "returns": [],
        },
    }

    def __init__(self, endpoints: List[Any], schemas: List[Any]):
        self.endpoints = endpoints
        self.schemas = schemas
        self.flows: List[AuthFlow] = []

    def generate(self) -> List[AuthFlow]:
        """Generate authentication flows from endpoints."""

        # Find register flow
        register_endpoints = [
            ep
            for ep in self.endpoints
            if any(x in ep.path.lower() for x in ["register", "signup"]) and ep.method == "POST"
        ]
        if register_endpoints:
            self.flows.append(
                AuthFlow(
                    name="register",
                    description="User registration - create a new user account",
                    steps=[
                        {
                            "step": 1,
                            "action": "Send registration data",
                            "endpoint": register_endpoints[0].path,
                            "method": "POST",
                        },
                        {
                            "step": 2,
                            "action": "Receive tokens and user data",
                            "returns": "accessToken, refreshToken, user",
                        },
                    ],
                    endpoints_used=[ep.path for ep in register_endpoints],
                    requires=["username", "email", "password"],
                    returns=["accessToken", "refreshToken", "user"],
                )
            )

        # Find login flow
        login_endpoints = [
            ep
            for ep in self.endpoints
            if any(x in ep.path.lower() for x in ["login", "authenticate"]) and ep.method == "POST"
        ]
        if login_endpoints:
            self.flows.append(
                AuthFlow(
                    name="login",
                    description="User login - authenticate and receive tokens",
                    steps=[
                        {
                            "step": 1,
                            "action": "Send credentials",
                            "endpoint": login_endpoints[0].path,
                            "method": "POST",
                        },
                        {
                            "step": 2,
                            "action": "Receive tokens",
                            "returns": "accessToken, refreshToken",
                        },
                    ],
                    endpoints_used=[ep.path for ep in login_endpoints],
                    requires=["email", "password"],
                    returns=["accessToken", "refreshToken"],
                )
            )

        # Find refresh token flow
        refresh_endpoints = [
            ep for ep in self.endpoints if "refresh" in ep.path.lower() and ep.method == "POST"
        ]
        if refresh_endpoints:
            self.flows.append(
                AuthFlow(
                    name="refresh_token",
                    description="Refresh access token using refresh token",
                    steps=[
                        {
                            "step": 1,
                            "action": "Send refresh token",
                            "endpoint": refresh_endpoints[0].path,
                            "method": "POST",
                        },
                        {
                            "step": 2,
                            "action": "Receive new tokens",
                            "returns": "accessToken, refreshToken",
                        },
                    ],
                    endpoints_used=[ep.path for ep in refresh_endpoints],
                    requires=["refreshToken"],
                    returns=["accessToken", "refreshToken"],
                )
            )

        # Find logout flow
        logout_endpoints = [
            ep for ep in self.endpoints if "logout" in ep.path.lower() and ep.method == "POST"
        ]
        if logout_endpoints:
            self.flows.append(
                AuthFlow(
                    name="logout",
                    description="User logout - invalidate tokens",
                    steps=[
                        {
                            "step": 1,
                            "action": "Send logout request with tokens",
                            "endpoint": logout_endpoints[0].path,
                            "method": "POST",
                        },
                    ],
                    endpoints_used=[ep.path for ep in logout_endpoints],
                    requires=["accessToken", "refreshToken"],
                    returns=[],
                )
            )

        # Find forgot password flow
        forgot_endpoints = [
            ep for ep in self.endpoints if "forgot" in ep.path.lower() and ep.method == "POST"
        ]
        if forgot_endpoints:
            self.flows.append(
                AuthFlow(
                    name="forgot_password",
                    description="Request password reset - get reset token via email",
                    steps=[
                        {
                            "step": 1,
                            "action": "Send email",
                            "endpoint": forgot_endpoints[0].path,
                            "method": "POST",
                        },
                        {
                            "step": 2,
                            "action": "Receive email with reset link",
                            "returns": "resetToken sent to email",
                        },
                    ],
                    endpoints_used=[ep.path for ep in forgot_endpoints],
                    requires=["email"],
                    returns=[],
                )
            )

        # Find reset password flow
        reset_endpoints = [
            ep
            for ep in self.endpoints
            if "reset-password" in ep.path.lower() and ep.method == "POST"
        ]
        if reset_endpoints:
            self.flows.append(
                AuthFlow(
                    name="reset_password",
                    description="Reset password using reset token",
                    steps=[
                        {
                            "step": 1,
                            "action": "Send reset token and new password",
                            "endpoint": reset_endpoints[0].path,
                            "method": "POST",
                        },
                    ],
                    endpoints_used=[ep.path for ep in reset_endpoints],
                    requires=["token", "newPassword"],
                    returns=[],
                )
            )

        # Find email verification flow
        verify_endpoints = [
            ep
            for ep in self.endpoints
            if "verify" in ep.path.lower()
            or "confirm" in ep.path.lower()
            and ep.method in ["POST", "GET"]
        ]
        if verify_endpoints:
            self.flows.append(
                AuthFlow(
                    name="verify_email",
                    description="Verify email address using verification token",
                    steps=[
                        {
                            "step": 1,
                            "action": "Send verification token",
                            "endpoint": verify_endpoints[0].path,
                            "method": verify_endpoints[0].method,
                        },
                    ],
                    endpoints_used=[ep.path for ep in verify_endpoints],
                    requires=["token"],
                    returns=[],
                )
            )

        # Find change password flow
        change_pwd_endpoints = [
            ep
            for ep in self.endpoints
            if "change-password" in ep.path.lower() and ep.method == "POST"
        ]
        if change_pwd_endpoints:
            self.flows.append(
                AuthFlow(
                    name="change_password",
                    description="Change password for authenticated user",
                    steps=[
                        {
                            "step": 1,
                            "action": "Send current and new password",
                            "endpoint": change_pwd_endpoints[0].path,
                            "method": "POST",
                        },
                    ],
                    endpoints_used=[ep.path for ep in change_pwd_endpoints],
                    requires=["currentPassword", "newPassword"],
                    returns=[],
                )
            )

        return self.flows

    def to_markdown(self) -> str:
        """Generate markdown documentation for auth flows."""
        if not self.flows:
            return "# Authentication Flows\n\nNo authentication flows detected.\n"

        md = "# Authentication Flows\n\n"
        md += f"**Total flows detected:** {len(self.flows)}\n\n"

        for flow in self.flows:
            md += f"## {flow.name.replace('_', ' ').title()}\n\n"
            md += f"{flow.description}\n\n"

            md += "### Endpoints Used\n"
            for ep in flow.endpoints_used:
                md += f"- `{ep}`\n"
            md += "\n"

            if flow.requires:
                md += "### Required Data\n"
                for req in flow.requires:
                    md += f"- `{req}`\n"
                md += "\n"

            if flow.returns:
                md += "### Returns\n"
                for ret in flow.returns:
                    md += f"- `{ret}`\n"
                md += "\n"

            md += "### Flow Steps\n"
            for step in flow.steps:
                md += f"{step['step']}. {step['action']}\n"
                if "endpoint" in step:
                    md += f"   - Endpoint: `{step['method']} {step['endpoint']}`\n"
                if "returns" in step:
                    md += f"   - Returns: {step['returns']}\n"
            md += "\n"

            md += "---\n\n"

        return md


def generate_auth_flows(endpoints: List[Any], schemas: List[Any]) -> str:
    """Convenience function to generate auth flows documentation."""
    generator = AuthFlowGenerator(endpoints, schemas)
    generator.generate()
    return generator.to_markdown()
