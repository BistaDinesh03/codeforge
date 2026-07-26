import * as vscode from 'vscode';

/**
 * Activates the CodeForge extension.
 * Called by VS Code when the extension is first activated.
 */
export function activate(context: vscode.ExtensionContext) {
    console.log('CodeForge extension activated');

    // Register the start command
    const startCommand = vscode.commands.registerCommand('codeforge.start', () => {
        vscode.window.showInformationMessage('CodeForge server starting...');
    });

    context.subscriptions.push(startCommand);
}

/**
 * Deactivates the extension.
 * Clean up resources when the extension is deactivated.
 */
export function deactivate() {
    console.log('CodeForge extension deactivated');
}