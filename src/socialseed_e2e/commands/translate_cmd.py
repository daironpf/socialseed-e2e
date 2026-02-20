"""Translate command for socialseed-e2e CLI.

This module provides the translate command using POO and SOLID principles.
"""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console


console = Console()


class NLTranslator:
    """Handles natural language to test translation (Single Responsibility)."""

    def __init__(self):
        self.supported_languages = ["python", "javascript", "typescript"]

    def translate(
        self,
        description: str,
        service: str,
        language: str,
        output_path: Optional[str],
    ) -> str:
        """Translate natural language to test code."""
        if language.lower() not in self.supported_languages:
            console.print(
                f"[yellow]Warning:[/yellow] Language '{language}' not fully supported. "
                f"Using Python."
            )
            language = "python"

        # Generate test code from description
        test_code = self._generate_test_code(description, service, language)

        if output_path:
            self._save_to_file(output_path, test_code)
            console.print(f"\n[green]✓[/green] Test saved to: {output_path}")

        return test_code

    def _generate_test_code(self, description: str, service: str, language: str) -> str:
        """Generate test code from description."""
        # Basic template - in production would use LLM
        test_name = description.split()[0].lower().replace(" ", "_")

        if language == "python":
            return f'''"""Test: {description}"""

from socialseed_e2e.core.base_page import BasePage


def test_{test_name}(page: BasePage):
    """Test case: {description}"""
    # TODO: Implement test based on: {description}
    pass
'''
        elif language == "javascript":
            return f"""// Test: {description}

/**
 * Test case: {description}
 */
async function test_{test_name}(page) {{
    // TODO: Implement test based on: {description}
}}
"""

        return f"// Test: {description}\n// TODO: Implement"

    def _save_to_file(self, path: str, content: str) -> None:
        """Save test code to file."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content)


@click.command()
@click.option("--project", "-p", default=".", help="Project directory")
@click.option(
    "--description",
    "-d",
    required=True,
    help="Natural language description of the test",
)
@click.option("--service", "-s", help="Service name")
@click.option(
    "--language",
    "-l",
    default="python",
    type=click.Choice(["python", "javascript", "typescript"]),
    help="Target language",
)
@click.option("--output", "-o", help="Output file path")
def translate_cmd(
    project: str,
    description: str,
    service: str,
    language: str,
    output: str,
):
    """Translate natural language to test code.

    Converts natural language descriptions into executable test code.

    Examples:
        e2e translate -d "Verify user login with valid credentials"
        e2e translate -d "Test payment flow" -s payment-api -o tests/test_payment.py
    """
    console.print("\n📝 [bold cyan]Natural Language to Test Translation[/bold cyan]\n")
    console.print(f"Description: {description}")
    console.print(f"Language: {language}\n")

    translator = NLTranslator()
    test_code = translator.translate(description, service, language, output)

    console.print("[bold]Generated test code:[/bold]\n")
    console.print(test_code)


def get_translate_command():
    """Get the translate command for lazy loading."""
    return translate_cmd


__all__ = ["translate_cmd", "get_translate_command"]
