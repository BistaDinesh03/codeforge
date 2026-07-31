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
  }

  public static createOrShow(extUri: vscode.Uri, apiClient: ApiClient, statusBar: StatusBarManager): void {
    if (ChatPanel.currentPanel) { ChatPanel.currentPanel.panel.reveal(vscode.ViewColumn.Two); return; }
    const panel = vscode.window.createWebviewPanel("codeforgeChat", "CodeForge", vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
    ChatPanel.currentPanel = new ChatPanel(panel, extUri, apiClient, statusBar);
  }

  public static addMessage(text: string, type: "user" | "ai" | "error"): void {
    ChatPanel.currentPanel?.panel.webview.postMessage({ command: "addMessage", text, type });
  }

  private async handle(message: { command: string; text?: string }): Promise<void> {
    if (message.command === "sendMessage" && message.text) {
      await this.sendMessage(message.text);
    }
    if (message.command === "insertCode" && message.text) {
      const editor = vscode.window.activeTextEditor;
      if (editor) { editor.edit((e) => e.insert(editor.selection.active, message.text!)); }
    }
  }

  private async sendMessage(text: string): Promise<void> {
    this.panel.webview.postMessage({ command: "addMessage", text, type: "user" });
    try {
      this.panel.webview.postMessage({ command: "responseStart" });
      const r = await this.apiClient.chat(text);
      this.panel.webview.postMessage({ command: "addMessage", text: r.response, type: "ai" });
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Failed";
      this.panel.webview.postMessage({ command: "addMessage", text: msg, type: "error" });
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