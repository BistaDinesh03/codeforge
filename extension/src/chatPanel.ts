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

  private constructor(
    panel: vscode.WebviewPanel,
    extensionUri: vscode.Uri,
    apiClient: ApiClient,
    statusBar: StatusBarManager
  ) {
    this.panel = panel;
    this.apiClient = apiClient;
    this.statusBar = statusBar;

    this.panel.webview.html = this.getHtml(extensionUri);
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage(
      (msg) => this.handleMessage(msg),
      null,
      this.disposables
    );
  }

  public static createOrShow(
    extensionUri: vscode.Uri,
    apiClient: ApiClient,
    statusBar: StatusBarManager
  ): void {
    if (ChatPanel.currentPanel) {
      ChatPanel.currentPanel.panel.reveal(vscode.ViewColumn.Two);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      "codeforgeChat",
      "CodeForge Chat",
      vscode.ViewColumn.Two,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );

    ChatPanel.currentPanel = new ChatPanel(panel, extensionUri, apiClient, statusBar);
  }

  public static addMessage(text: string, type: "user" | "ai" | "error"): void {
    ChatPanel.currentPanel?.panel.webview.postMessage({
      command: "addMessage",
      text,
      type,
    });
  }

  private async handleMessage(message: { command: string; text?: string }): Promise<void> {
    if (message.command === "sendMessage" && message.text) {
      await this.sendMessage(message.text);
    }
  }

  private async sendMessage(text: string): Promise<void> {
    try {
      this.panel.webview.postMessage({ command: "responseStart" });
      const response = await this.apiClient.chat(text);
      this.panel.webview.postMessage({
        command: "responseChunk",
        text: response.response,
        speed: response.tokens_per_second,
      });
      this.panel.webview.postMessage({ command: "responseDone" });
    } catch (error) {
      this.panel.webview.postMessage({
        command: "responseError",
        error: error instanceof Error ? error.message : "Connection failed",
      });
    }
  }

  private getHtml(extensionUri: vscode.Uri): string {
    const htmlPath = path.join(extensionUri.fsPath, "src", "chat.html");
    return fs.readFileSync(htmlPath, "utf-8");
  }

  private dispose(): void {
    ChatPanel.currentPanel = undefined;
    this.panel.dispose();
    while (this.disposables.length) {
      const d = this.disposables.pop();
      if (d) d.dispose();
    }
  }
}