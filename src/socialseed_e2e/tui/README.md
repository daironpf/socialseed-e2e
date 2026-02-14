# Rich Terminal Interface (TUI)

The Rich Terminal Interface provides a powerful, keyboard-driven UI for power users who prefer terminal-based interaction.

## Features

- **Keyboard Navigation**: Navigate test suites with arrow keys
- **Quick Actions**: Run/Stop/Filter tests with hotkeys
- **Split View**: Test list and execution details side-by-side
- **Instant Feedback**: Colored status indicators (green=pass, red=fail, yellow=skip)
- **Environment Toggling**: Switch environments without restarting

## Installation

```bash
# Install with TUI support
pip install socialseed-e2e[tui]

# Or install textual separately
pip install textual>=0.41.0
```

## Usage

Launch the TUI:

```bash
e2e tui                    # Launch with default settings
e2e tui --service users    # Filter by service
e2e tui --config ./e2e.conf  # Use custom config
```

## Key Bindings

| Key | Action |
|-----|--------|
| ↑/↓ | Navigate test list |
| Enter | Run selected test |
| r | Run selected test |
| R | Run all tests |
| s | Stop running tests |
| f | Toggle filter |
| e | Switch environment |
| q | Quit |
| ? | Show help |

## Interface Layout

The TUI uses a split-pane layout:

```
┌─────────────────────────────────────────────────────────────┐
│  Test List               │  Test Details                    │
│  ├── 01_login_flow       │  Status: Pending                 │
│  ├── 02_register_flow    │  Duration: --                    │
│  ├── 03_create_user      │  Last Run: Never                 │
│  └── ...                 │                                  │
├──────────────────────────┴──────────────────────────────────┤
│  Execution Logs                                              │
│  [timestamp] Starting test execution...                      │
│  [timestamp] Test completed successfully                     │
└─────────────────────────────────────────────────────────────┘
```

## Architecture

The TUI is built using **Textual** framework:

- **TuiApp**: Main application orchestrator
- **TestList**: DataTable component for test navigation
- **TestDetail**: Detail panel for test information
- **LogView**: RichLog for real-time execution logs
- **StatusBar**: Status indicators and hotkey help

## Comparison with Dashboard

| Feature | TUI | Web Dashboard |
|---------|-----|---------------|
| Keyboard-only | ✅ | Partial |
| Split-pane view | ✅ | ✅ |
| Execution logs | ✅ | ✅ |
| Test filtering | ✅ | ✅ |
| Web-based | ❌ | ✅ |
| Cross-platform | ✅ | ✅ |
| Requires browser | ❌ | ✅ |

## Configuration

The TUI respects all settings from `e2e.conf`:

```yaml
environment: dev
timeout: 30000
verbose: true
```

## Customization

The TUI uses CSS-like styling. You can customize colors in the app:

```python
from socialseed_e2e.tui import TuiApp

app = TuiApp()
app.dark = False  # Light mode
app.run()
```

## Troubleshooting

### TUI won't start

```bash
# Check textual is installed
pip show textual

# Install if missing
pip install textual>=0.41.0
```

### Display issues

The TUI requires a terminal with Unicode and color support:

- **Windows**: Use Windows Terminal or PowerShell
- **macOS**: Terminal.app or iTerm2
- **Linux**: Any modern terminal emulator

### Performance with large test suites

The TUI handles large test suites efficiently:

- Lazy loading of test details
- Virtualized list rendering
- Debounced log updates

## Development

To modify the TUI:

```python
# src/socialseed_e2e/tui/app.py
from textual.app import App
from textual.containers import Grid, Horizontal, Vertical

class TuiApp(App):
    CSS = """
    Screen { align: center middle; }
    # ... custom styles
    """

    # Add custom widgets or modify existing ones
```

## Roadmap

- [ ] Multi-select for batch operations
- [ ] Test search with regex
- [ ] Export results to file
- [ ] Custom themes
- [ ] Mouse support (optional)

## Contributing

See the main project documentation for contribution guidelines.
