const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    const outputChannel = vscode.window.createOutputChannel('SocialSeed E2E');
    
    console.log('SocialSeed E2E extension is now active');

    // Command: Run All Tests
    let runAllTests = vscode.commands.registerCommand('socialseed-e2e.runAllTests', function () {
        runE2ECommand(['run']);
    });

    // Command: Initialize Project
    let initProject = vscode.commands.registerCommand('socialseed-e2e.initProject', async function () {
        const result = await vscode.window.showOpenDialog({
            canSelectFiles: false,
            canSelectFolders: true,
            canSelectMany: false,
            openLabel: 'Select folder to initialize'
        });

        if (result && result.length > 0) {
            runE2ECommand(['init', result[0].fsPath]);
        }
    });

    // Command: Create New Service
    let newService = vscode.commands.registerCommand('socialseed-e2e.newService', async function () {
        const serviceName = await vscode.window.showInputBox({
            prompt: 'Enter the service name',
            placeHolder: 'users-api'
        });

        if (serviceName) {
            runE2ECommand(['new-service', serviceName]);
        }
    });

    function runE2ECommand(args) {
        const config = vscode.workspace.getConfiguration('socialseed-e2e');
        const e2ePath = config.get('executablePath') || 'e2e';
        
        outputChannel.appendLine(`Executing: ${e2ePath} ${args.join(' ')}`);
        outputChannel.show();

        const workspaceFolder = vscode.workspace.workspaceFolders ? vscode.workspace.workspaceFolders[0].uri.fsPath : undefined;
        
        const child = cp.spawn(e2ePath, args, {
            cwd: workspaceFolder,
            shell: true
        });

        child.stdout.on('data', (data) => {
            outputChannel.append(data.toString());
        });

        child.stderr.on('data', (data) => {
            outputChannel.append(data.toString());
        });

        child.on('close', (code) => {
            outputChannel.appendLine(`\nProcess exited with code ${code}`);
            if (code === 0) {
                vscode.window.showInformationMessage(`E2E command successful: ${args[0]}`);
            } else {
                vscode.window.showErrorMessage(`E2E command failed with code ${code}`);
            }
        });
    }

    context.subscriptions.push(runAllTests, initProject, newService);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
