"""Interactive Doctor for test failures.

This module provides the interactive CLI for diagnosing and fixing test failures.
"""

import uuid
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from socialseed_e2e.core.interactive_doctor.analyzer import ErrorAnalyzer
from socialseed_e2e.core.interactive_doctor.fixer import AutoFixer
from socialseed_e2e.core.interactive_doctor.models import (
    AppliedFix,
    DiagnosisResult,
    DoctorSession,
    ErrorContext,
    FixStrategy,
)
from socialseed_e2e.core.interactive_doctor.suggester import FixSuggester

console = Console()


class InteractiveDoctor:
    """Interactive doctor for diagnosing and fixing test failures.

        This class provides an interactive CLI that analyzes test failures,
    presents diagnosis to the user, and applies fixes based on user choice.

        Example:
            >>> doctor = InteractiveDoctor("/path/to/project")
            >>> session = doctor.start_session()
            >>> context = ErrorContext(
            ...     test_name="test_login",
            ...     service_name="auth-service",
            ...     error_message="Validation error"
            ... )
            >>> doctor.diagnose_and_fix(context, session)
    """

    def __init__(self, project_root: str, interactive: bool = True):
        """Initialize the interactive doctor.

        Args:
            project_root: Root directory of the project
            interactive: Whether to run in interactive mode
        """
        self.project_root = project_root
        self.interactive = interactive
        self.analyzer = ErrorAnalyzer(project_root)
        self.suggester = FixSuggester()
        self.fixer = AutoFixer(project_root)

    def start_session(self) -> DoctorSession:
        """Start a new doctor session.

        Returns:
            New DoctorSession
        """
        session_id = str(uuid.uuid4())[:8]
        return DoctorSession(session_id=session_id, project_root=self.project_root)

    def diagnose_and_fix(
        self, context: ErrorContext, session: DoctorSession
    ) -> Optional[AppliedFix]:
        """Diagnose an error and offer to fix it.

        Args:
            context: Error context
            session: Current doctor session

        Returns:
            AppliedFix if a fix was applied, None otherwise
        """
        # Analyze error
        console.print("\n[bold cyan]Analyzing test failure...[/bold cyan]")
        diagnosis = self.analyzer.analyze(context)
        session.errors.append(diagnosis)

        # Display diagnosis
        self._display_diagnosis(diagnosis)

        # Get fix suggestions
        suggestions = self.suggester.suggest_fixes(diagnosis)

        if not suggestions:
            console.print("[yellow]No fix suggestions available.[/yellow]")
            return None

        # Display suggestions
        self._display_suggestions(suggestions)

        # Get user choice
        if self.interactive:
            choice = self._get_user_choice(suggestions)
        else:
            # Auto mode: apply first automatic fix
            choice = self._get_auto_choice(suggestions)

        if choice is None:
            console.print("[yellow]Skipping this error.[/yellow]")
            session.skipped_fixes.append(
                {"diagnosis": diagnosis, "reason": "User skipped"}
            )
            return None

        suggestion = suggestions[choice]

        # Check if suggestion can be applied automatically
        if not suggestion.automatic:
            console.print(
                "\n[yellow]⚠️  This fix requires manual implementation:[/yellow]"
            )
            console.print(
                Panel(
                    suggestion.preview or suggestion.description,
                    title="Manual Fix Required",
                    border_style="yellow",
                )
            )

            if suggestion.risks:
                console.print("\n[red]Risks:[/red]")
                for risk in suggestion.risks:
                    console.print(f"  • {risk}")

            session.skipped_fixes.append(
                {
                    "diagnosis": diagnosis,
                    "suggestion": suggestion,
                    "reason": "Requires manual implementation",
                }
            )
            return None

        # Confirm fix application
        if self.interactive:
            if suggestion.preview:
                console.print("\n[dim]Preview of changes:[/dim]")
                console.print(
                    Panel(suggestion.preview, title="Code Preview", border_style="dim")
                )

            if not Confirm.ask("Apply this fix?", default=True):
                console.print("[yellow]Fix cancelled.[/yellow]")
                session.skipped_fixes.append(
                    {
                        "diagnosis": diagnosis,
                        "suggestion": suggestion,
                        "reason": "User cancelled",
                    }
                )
                return None

        # Apply fix
        console.print("\n[bold green]Applying fix...[/bold green]")
        result = self.fixer.apply_fix(diagnosis, suggestion)

        if result.success:
            console.print("[bold green]✓ Fix applied successfully![/bold green]")
            if result.files_modified:
                console.print("\n[dim]Modified files:[/dim]")
                for file in result.files_modified:
                    console.print(f"  • {file}")

            if result.backup_paths:
                console.print(
                    f"\n[dim]Backups created in: {self.fixer.backup_dir}[/dim]"
                )

            session.applied_fixes.append(
                {"diagnosis": diagnosis, "suggestion": suggestion, "result": result}
            )

            return result
        else:
            console.print("[bold red]✗ Failed to apply fix:[/bold red]")
            console.print(f"[red]{result.error_message}[/red]")

            session.skipped_fixes.append(
                {
                    "diagnosis": diagnosis,
                    "suggestion": suggestion,
                    "reason": f"Application failed: {result.error_message}",
                }
            )

            return None

    def _display_diagnosis(self, diagnosis: DiagnosisResult) -> None:
        """Display diagnosis to user.

        Args:
            diagnosis: Diagnosis result
        """
        # Create diagnosis panel
        content = f"""
[bold]Error Type:[/bold] {diagnosis.error_type.name}
[bold]Confidence:[/bold] {diagnosis.confidence:.0%}
[bold]Description:[/bold] {diagnosis.description}

[bold]Context:[/bold]
  • Test: {diagnosis.context.test_name}
  • Service: {diagnosis.context.service_name}
  • Endpoint: {diagnosis.context.http_method or "N/A"} {diagnosis.context.endpoint_path or "N/A"}
        """

        if diagnosis.manifest_insights.get("endpoint_found"):
            content += "\n[bold green]✓[/bold green] Endpoint found in Project Manifest"

        if diagnosis.manifest_insights.get("dto_found"):
            content += (
                "\n[bold green]✓[/bold green] DTO schema found in Project Manifest"
            )

        if diagnosis.affected_files:
            content += "\n\n[bold]Affected Files:[/bold]"
            for file in diagnosis.affected_files:
                content += f"\n  • {file}"

        console.print(
            Panel(
                content,
                title=f"🔍 Diagnosis ({diagnosis.context.test_name})",
                border_style="cyan",
            )
        )

    def _display_suggestions(self, suggestions: List[Any]) -> None:
        """Display fix suggestions to user.

        Args:
            suggestions: List of suggestions
        """
        table = Table(title="💡 Fix Suggestions")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Strategy", style="green")
        table.add_column("Title", style="white")
        table.add_column("Auto", style="yellow")
        table.add_column("Description", style="dim")

        for i, suggestion in enumerate(suggestions, 1):
            auto_text = "✓" if suggestion.automatic else "✗"
            table.add_row(
                str(i),
                suggestion.strategy.name,
                suggestion.title,
                auto_text,
                suggestion.description[:50] + "..."
                if len(suggestion.description) > 50
                else suggestion.description,
            )

        console.print(table)

    def _get_user_choice(self, suggestions: List[Any]) -> Optional[int]:
        """Get user choice for fix.

        Args:
            suggestions: List of suggestions

        Returns:
            Index of chosen suggestion or None
        """
        choices = [str(i) for i in range(1, len(suggestions) + 1)]
        choices.append("S")  # Skip

        choice = Prompt.ask("\nSelect a fix to apply", choices=choices, default="1")

        if choice.upper() == "S":
            return None

        return int(choice) - 1

    def _get_auto_choice(self, suggestions: List[Any]) -> Optional[int]:
        """Get automatic choice (first automatic fix).

        Args:
            suggestions: List of suggestions

        Returns:
            Index of automatic suggestion or None
        """
        for i, suggestion in enumerate(suggestions):
            if suggestion.automatic and suggestion.strategy != FixStrategy.IGNORE:
                return i
        return None

    def end_session(self, session: DoctorSession) -> Dict[str, Any]:
        """End a doctor session and return summary.

        Args:
            session: Doctor session to end

        Returns:
            Session summary
        """
        import datetime

        session.end_time = datetime.datetime.now()

        summary = {
            "session_id": session.session_id,
            "duration_seconds": session.get_duration_seconds(),
            "total_errors": len(session.errors),
            "applied_fixes": len(session.applied_fixes),
            "skipped_fixes": len(session.skipped_fixes),
            "fix_success_rate": (
                len(session.applied_fixes) / len(session.errors) * 100
                if session.errors
                else 0
            ),
        }

        # Display summary
        console.print("\n" + "=" * 60)
        console.print("[bold]Doctor Session Summary[/bold]")
        console.print("=" * 60)
        console.print(f"Session ID: {session.session_id}")
        console.print(f"Duration: {summary['duration_seconds']:.1f}s")
        console.print(f"Errors Analyzed: {summary['total_errors']}")
        console.print(f"Fixes Applied: {summary['applied_fixes']}")
        console.print(f"Fixes Skipped: {summary['skipped_fixes']}")
        console.print(f"Success Rate: {summary['fix_success_rate']:.0f}%")

        if session.applied_fixes:
            console.print("\n[bold green]Applied Fixes:[/bold green]")
            for fix in session.applied_fixes:
                result = fix["result"]
                console.print(f"  ✓ {fix['suggestion'].title}")
                if result.files_modified:
                    for file in result.files_modified:
                        console.print(f"      → {file}")

        return summary


def run_interactive_doctor(
    project_root: str,
    test_name: Optional[str] = None,
    error_message: Optional[str] = None,
    auto_mode: bool = False,
) -> Dict[str, Any]:
    """Run the interactive doctor.

    This is a convenience function for running the doctor from CLI.

    Args:
        project_root: Project root directory
        test_name: Optional test name
        error_message: Optional error message
        auto_mode: Run in automatic mode (non-interactive)

    Returns:
        Session summary
    """
    doctor = InteractiveDoctor(project_root, interactive=not auto_mode)
    session = doctor.start_session()

    if test_name and error_message:
        # Create error context
        context = ErrorContext(
            test_name=test_name,
            service_name="unknown",  # Could be detected from manifest
            error_message=error_message,
        )

        # Diagnose and fix
        doctor.diagnose_and_fix(context, session)

    return doctor.end_session(session)
