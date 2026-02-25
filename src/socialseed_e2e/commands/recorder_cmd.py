"""Recorder commands for socialseed-e2e CLI.

This module provides the recorder commands (record, replay, convert) using POO and SOLID principles.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

console = Console()


class RecorderAgent:
    """Handles session recording (Single Responsibility)."""

    def __init__(self, name: str, port: int, output: Optional[str] = None):
        self.name = name
        self.port = port
        self.output = output or f"recordings/{name}.json"

    def record(self):
        """Start recording a session."""
        from socialseed_e2e.recorder import RecordingProxy

        os.makedirs(os.path.dirname(self.output), exist_ok=True)

        proxy = RecordingProxy(port=self.port)
        proxy.start(self.name)

        console.print(
            "\n[bold red]🔴 Recording Proxy active.[/bold red] [bold green]Press Ctrl+C to stop recording and save the session...[/bold green]\n"
        )

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            session = proxy.stop()
            session.save(self.output)
            console.print(
                f"\n[bold green]✓ Session saved to:[/bold green] {self.output}"
            )
            console.print(f"Recorded {len(session.interactions)} interactions.")


class ReplayAgent:
    """Handles session replay (Single Responsibility)."""

    def __init__(self, file: str):
        self.file = file

    def replay(self):
        """Replay a recorded session."""
        from playwright.sync_api import sync_playwright

        from socialseed_e2e.core.base_page import BasePage
        from socialseed_e2e.recorder import RecordedSession, SessionPlayer

        if not Path(self.file).exists():
            console.print(f"[red]❌ Error:[/red] File '{self.file}' not found.")
            return

        session = RecordedSession.load(self.file)

        with sync_playwright() as p:
            page = BasePage(base_url="", playwright=p)
            page.setup()
            try:
                SessionPlayer.play(session, page)
            finally:
                page.teardown()


class ConverterAgent:
    """Handles session to test code conversion (Single Responsibility)."""

    def __init__(self, file: str, output: Optional[str] = None):
        self.file = file
        self.output = output

    def convert(self):
        """Convert recorded session to Python test code."""
        from socialseed_e2e.recorder import RecordedSession, SessionConverter

        if not Path(self.file).exists():
            console.print(f"[red]❌ Error:[/red] File '{self.file}' not found.")
            return

        session = RecordedSession.load(self.file)
        code = SessionConverter.to_python_code(session)

        output_path = self.output or f"services/recorded/modules/{session.name}_flow.py"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(code)

        console.print(
            f"\n[bold green]✓ Test code generated:[/bold green] {output_path}"
        )


@click.group(name="recorder")
def get_recorder_group():
    """Commands for recording and replaying API sessions."""
    pass


@click.command(name="record")
@click.argument("name")
@click.option("--port", "-p", default=8090, help="Proxy port")
@click.option(
    "--output", "-o", help="Output file path (default: recordings/<name>.json)"
)
def get_record_command(name: str, port: int = 8090, output: Optional[str] = None):
    """Record a new API session via proxy."""
    try:
        agent = RecorderAgent(name, port, output)
        agent.record()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command(name="replay")
@click.argument("file")
def get_replay_command(file: str):
    """Replay a recorded session."""
    try:
        agent = ReplayAgent(file)
        agent.replay()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


@click.command(name="convert")
@click.argument("file")
@click.option("--output", "-o", help="Output test file path")
def get_convert_command(file: str, output: Optional[str] = None):
    """Convert a recorded session to Python test code."""
    try:
        agent = ConverterAgent(file, output)
        agent.convert()
    except Exception as e:
        console.print(f"[red]❌ Error:[/red] {e}")
        sys.exit(1)


recorder_group = get_recorder_group()
