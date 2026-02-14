"""Curl command importer."""

import shlex
from pathlib import Path
from typing import Dict, List, Optional

from socialseed_e2e.importers.base import BaseImporter, ImportResult


class CurlImporter(BaseImporter):
    """Import curl commands into SocialSeed E2E tests."""

    def import_file(self, file_path: Path) -> ImportResult:
        """Import a file containing curl commands."""
        try:
            content = file_path.read_text()
            commands = self._parse_curl_commands(content)
        except FileNotFoundError:
            return ImportResult(False, f"File not found: {file_path}")

        tests = []
        for i, cmd in enumerate(commands):
            test_data = self._parse_curl_command(cmd)
            if test_data:
                test_data["name"] = f"curl_request_{i + 1}"
                tests.append(test_data)

        # Generate code for each test
        generated_files = []
        for test in tests:
            code = self.generate_code(test)
            test_name = test.get("name", "curl_test")
            file_path = self._write_test_file(self._sanitize_name(test_name), code)
            generated_files.append(file_path)

        message = f"Successfully imported {len(tests)} curl commands"
        return ImportResult(
            success=True,
            message=message,
            tests=tests,
            warnings=self.warnings,
        )

    def import_command(self, command: str) -> ImportResult:
        """Import a single curl command directly."""
        test_data = self._parse_curl_command(command)
        if not test_data:
            return ImportResult(False, "Failed to parse curl command")

        test_data["name"] = "curl_import"
        code = self.generate_code(test_data)
        file_path = self._write_test_file("curl_import", code)

        return ImportResult(
            success=True,
            message="Successfully imported curl command",
            tests=[test_data],
            warnings=self.warnings,
        )

    def _parse_curl_commands(self, content: str) -> List[str]:
        """Parse multiple curl commands from text."""
        commands = []
        lines = content.strip().split("\n")
        current_cmd = ""

        for line in lines:
            line = line.strip()
            if line.startswith("curl"):
                if current_cmd:
                    commands.append(current_cmd)
                current_cmd = line
            elif line.startswith("-") or line.startswith("'") or line.startswith('"'):
                current_cmd += " " + line
            elif current_cmd and line:
                current_cmd += " " + line

        if current_cmd:
            commands.append(current_cmd)

        return commands

    def _parse_curl_command(self, command: str) -> Optional[Dict]:
        """Parse a single curl command."""
        try:
            # Remove 'curl' prefix if present
            command = command.strip()
            if command.startswith("curl "):
                command = command[5:]
            elif command == "curl":
                return None

            # Tokenize
            try:
                tokens = shlex.split(command)
            except ValueError:
                # Fallback to simple split
                tokens = command.split()

            result = {
                "method": "GET",
                "url": "",
                "headers": {},
                "body": None,
            }

            i = 0
            while i < len(tokens):
                token = tokens[i]

                if token in ["-X", "--request"]:
                    i += 1
                    if i < len(tokens):
                        result["method"] = tokens[i].upper()

                elif token in ["-H", "--header"]:
                    i += 1
                    if i < len(tokens):
                        header_line = tokens[i]
                        if ":" in header_line:
                            key, value = header_line.split(":", 1)
                            result["headers"][key.strip()] = value.strip()

                elif token in ["-d", "--data", "--data-raw"]:
                    i += 1
                    if i < len(tokens):
                        result["body"] = tokens[i]
                        if result["method"] == "GET":
                            result["method"] = "POST"

                elif token in ["-u", "--user"]:
                    i += 1
                    if i < len(tokens):
                        auth = tokens[i]
                        import base64

                        encoded = base64.b64encode(auth.encode()).decode()
                        result["headers"]["Authorization"] = f"Basic {encoded}"

                elif token.startswith("-"):
                    # Skip unknown flags
                    pass

                elif not result["url"] and not token.startswith("-"):
                    # Assume it's the URL
                    url = token.strip("'\"")
                    if not url.startswith(("http://", "https://")):
                        url = "http://" + url
                    result["url"] = url

                i += 1

            return result if result["url"] else None

        except Exception as e:
            self.add_warning(f"Failed to parse curl command: {e}")
            return None

    def generate_code(self, data: Dict) -> str:
        """Generate Python test code from curl command."""
        method = data["method"].lower()
        url = data["url"]
        headers = data.get("headers", {})
        body = data.get("body")

        lines = [
            '"""Test imported from curl command"""',
            "",
            "async def run(page):",
            '    """Execute curl request"""',
            "",
            "    # Arrange",
        ]

        if headers:
            lines.append("    headers = {")
            for key, value in headers.items():
                lines.append(f'        "{key}": "{value}",')
            lines.append("    }")

        if body:
            lines.append(f"    data = {repr(body)}")

        lines.extend(
            [
                "",
                "    # Act",
            ]
        )

        args = [f'"{url}"']
        if headers:
            args.append("headers=headers")
        if body:
            args.append("data=data")

        lines.append(f"    response = await page.request.{method}({', '.join(args)})")
        lines.extend(
            [
                "",
                "    # Assert",
                "    assert response.status == 200",
                "",
            ]
        )

        return "\n".join(lines)
