import * as vscode from "vscode";
import { ApiClient } from "./apiClient";
import { StatusBarManager } from "./statusBar";
import { DashboardPanel } from "./dashboardPanel";

export function activate(context: vscode.ExtensionContext) {
  const c = vscode.workspace.getConfiguration("codetalk");
  const api = new ApiClient({serverUrl:c.get("serverUrl","http://127.0.0.1:8000")});
  const bar = new StatusBarManager();

  context.subscriptions.push(
    vscode.commands.registerCommand("codetalk.open", () => DashboardPanel.createOrShow(context.extensionUri, api)),
    bar
  );
}

export function deactivate(): void {}