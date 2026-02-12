# IDE Extensions Guide

socialseed-e2e provides official extensions for **Visual Studio Code** and **PyCharm** to enhance your development experience.

## Visual Studio Code Extension

The VS Code extension provides integrated commands, syntax highlighting, and test management.

### Features
- **Integrated Commands**: Access `e2e init`, `e2e new-service`, and `e2e run` from the Command Palette (`Ctrl+Shift+P`).
- **Syntax Highlighting**: Enhanced highlighting for E2E-specific methods like `do_login()`, `get()`, `post()`, and `assert_status()`.
- **Test Output**: Integrated output channel to view test results in real-time.

### Installation (Development)
1. Navigate to `ide-extensions/vscode`.
2. Run `npm install`.
3. Press `F5` to open a new VS Code window with the extension enabled.

## PyCharm Plugin

The PyCharm plugin brings socialseed-e2e features directly into the JetBrains ecosystem.

### Features
- **Action Menu**: New "SocialSeed E2E" menu in the main menu bar.
- **Run Configurations**: Coming soon support for custom run configurations.
- **Tool Window**: Quick access to framework actions and docs.

### Installation (Development)
1. Open the `ide-extensions/pycharm` directory in PyCharm or IntelliJ IDEA.
2. The project will automatically be recognized as a Gradle project.
3. Run the `runIde` task from the Gradle tool window to launch a test instance of PyCharm with the plugin.

## Future Roadmap
- [ ] Test Explorer integration for VS Code.
- [ ] Inline test results and failure stack traces.
- [ ] Code completion (IntelliSense) for dynamically discovered Page Objects.
- [ ] Auto-generation of test stubs from `project_knowledge.json`.
