import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { ApiClient } from "./apiClient";

export class DashboardPanel {
  public static currentPanel: DashboardPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];
  private apiClient: ApiClient;

  private constructor(panel: vscode.WebviewPanel, extUri: vscode.Uri, apiClient: ApiClient) {
    this.panel = panel; this.apiClient = apiClient;
    this.panel.webview.html = fs.readFileSync(path.join(extUri.fsPath, "src", "dashboard.html"), "utf-8");
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage((msg) => this.handle(msg), null, this.disposables);
  }

  public static createOrShow(extUri: vscode.Uri, apiClient: ApiClient): void {
    if (DashboardPanel.currentPanel) { DashboardPanel.currentPanel.panel.reveal(vscode.ViewColumn.Two); return; }
    DashboardPanel.currentPanel = new DashboardPanel(vscode.window.createWebviewPanel("codetalk","CodeTalk",vscode.ViewColumn.Two,{enableScripts:true,retainContextWhenHidden:true}), extUri, apiClient);
  }

  private async handle(msg: { command: string }): Promise<void> {
    if (msg.command === "analyze") {
      const ws = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
      if (!ws) { this.panel.webview.postMessage({command:"analysis",data:{error:"No workspace open"}}); return; }
      try {
        const h = await this.apiClient.fetchJson("/insights/health", {workspace_path: ws});
        const p = await this.apiClient.fetchJson("/insights/personalities", {workspace_path: ws});
        const a = await this.apiClient.fetchJson("/insights/awards", {workspace_path: ws});
        const m = await this.apiClient.fetchJson("/insights/map", {workspace_path: ws});
        this.panel.webview.postMessage({command:"analysis",data:{...h, personalities:p, awards:a.awards, map:m}});
      } catch(e) {
        this.panel.webview.postMessage({command:"analysis",data:{error:"Failed. Is the server running?"}});
      }
    }
  }

  private dispose(): void { DashboardPanel.currentPanel = undefined; this.panel.dispose(); }
}