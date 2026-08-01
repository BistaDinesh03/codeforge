import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { ApiClient } from "./apiClient";
import { StatusBarManager } from "./statusBar";

export class ChatPanel {
  public static currentPanel: ChatPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];
  private apiClient: ApiClient;
  private statusBar: StatusBarManager;

  private constructor(panel: vscode.WebviewPanel, extUri: vscode.Uri, apiClient: ApiClient, statusBar: StatusBarManager) {
    this.panel = panel; this.apiClient = apiClient; this.statusBar = statusBar;
    this.panel.webview.html = this.getHtml(extUri);
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage((msg) => this.handle(msg), null, this.disposables);
    this.updateStatus();
  }

  public static init(context: vscode.ExtensionContext): void {
    // Store context for history persistence
  }

  public static createOrShow(extUri: vscode.Uri, apiClient: ApiClient, statusBar: StatusBarManager, context?: vscode.ExtensionContext): void {
    if (ChatPanel.currentPanel) { ChatPanel.currentPanel.panel.reveal(vscode.ViewColumn.Two); return; }
    const panel = vscode.window.createWebviewPanel("codeforgeChat", "CodeForge", vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
    ChatPanel.currentPanel = new ChatPanel(panel, extUri, apiClient, statusBar);
  }

  public static addMessage(text: string, type: "user" | "ai" | "error"): void {
    ChatPanel.currentPanel?.panel.webview.postMessage({ command: "addMessage", text, type });
  }

  private updateStatus(): void {
    const ws = vscode.workspace.workspaceFolders?.[0]?.name || "-";
    this.panel.webview.postMessage({
      command: "updateStatus",
      connected: true, model: "Qwen 1.5B", files: 0, chats: 0, workspace: ws
    });
  }

  private async handle(msg: { command: string; text?: string; code?: string }): Promise<void> {
    switch (msg.command) {
      case "sendMessage":
        if (msg.text) await this.sendMessage(msg.text);
        break;
      case "applyCode":
        if (msg.text) {
          const editor = vscode.window.activeTextEditor;
          if (editor) await editor.edit(e => { if (editor.selection.isEmpty) e.insert(editor.selection.active, msg.text!); else e.replace(editor.selection, msg.text!); });
        }
        break;
      case "getStatus":
        this.updateStatus();
        break;
    }
  }

  private async sendMessage(text: string): Promise<void> {
    this.panel.webview.postMessage({ command: "addMessage", text, type: "user" });
    try {
      const r = await this.apiClient.chat(text);
      const codeMatch = r.response.match(/```(\w*)\n?([\s\S]*?)```/);
      if (codeMatch) {
        this.panel.webview.postMessage({ command: "addArtifact", code: codeMatch[2].trim(), language: codeMatch[1] || "text", title: "Generated Code" });
      } else {
        this.panel.webview.postMessage({ command: "addMessage", text: r.response, type: "ai" });
      }
    } catch (error) {
      this.panel.webview.postMessage({ command: "addMessage", text: error instanceof Error ? error.message : "Failed", type: "error" });
    }
  }

  private getHtml(extUri: vscode.Uri): string {
    return fs.readFileSync(path.join(extUri.fsPath, "src", "chat.html"), "utf-8");
  }

  private dispose(): void {
    ChatPanel.currentPanel = undefined; this.panel.dispose();
    while (this.disposables.length) { const d = this.disposables.pop(); if (d) d.dispose(); }
  }
}