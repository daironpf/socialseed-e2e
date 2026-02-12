"""Converter to transform recorded sessions into Python test code."""

import json
from pathlib import Path
from typing import Optional

from socialseed_e2e.recorder.models import RecordedSession


class SessionConverter:
    """Converts recorded sessions to runnable test modules."""

    @staticmethod
    def to_python_code(session: RecordedSession, service_name: Optional[str] = None) -> str:
        """Generate Python code from a session."""
        lines = [
            f'"""Recorded test session: {session.name}"""',
            "from socialseed_e2e.core import tag, priority, Priority",
            "",
            "",
            '@tag("recorded")',
            "def run(page):",
            f'    """Run recorded interactions for {session.name}."""',
            f'    print("Running recorded session: {session.name}...")',
            "",
        ]

        # Tracking base URL if we want to make it relative
        # For now, we use absolute URLs as recorded

        for i, interaction in enumerate(session.interactions):
            lines.append(f"    # Interaction {i+1}: {interaction.method} {interaction.url}")
            lines.append(
                f"    # Status: {interaction.response_status}, "
                f"Duration: {interaction.duration_ms:.0f}ms"
            )

            # Prepare method call
            method = interaction.method.lower()
            url = interaction.url

            # Escape single quotes in URL if needed
            url_escaped = url.replace("'", "\\'")

            call_args = [f"'{url_escaped}'"]

            if interaction.request_body:
                if isinstance(interaction.request_body, dict):
                    body_json = json.dumps(interaction.request_body, indent=8)
                    # Clean up indentation for the generated code
                    body_str = body_json.replace("\n", "\n    ")
                    call_args.append(f"json={body_str.strip()}")
                else:
                    call_args.append(f"data={repr(interaction.request_body)}")

            # Handle headers if they are significant (e.g. Auth)
            # For simplicity in demo, we might skip some headers or include them all
            # Let's include non-standard headers
            significant_headers = {
                k: v
                for k, v in interaction.request_headers.items()
                if k.lower()
                not in ["host", "connection", "content-length", "user-agent", "accept-encoding"]
            }
            if significant_headers:
                call_args.append(f"headers={repr(significant_headers)}")

            lines.append(f"    response = page.{method}({', '.join(call_args)})")
            lines.append(f"    page.assert_status(response, {interaction.response_status})")

            # Add basic JSON validation if it was a JSON response
            if interaction.response_body and isinstance(interaction.response_body, dict):
                lines.append("    # Basic verification of response structure")
                lines.append("    data = page.assert_json(response)")
                # We could add more specific assertions here if we had a way to infer them

            lines.append("")

        lines.append('    print("🎉 Recorded session completed successfully!")')
        return "\n".join(lines)

    @classmethod
    def save_as_module(cls, session: RecordedSession, output_path: Path):
        """Save a session as a Python module file."""
        code = cls.to_python_code(session)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)
        return output_path
