import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { ApiClient } from "./apiClient";
import { StatusBarManager } from "./statusBar";

interface Message {
  role: "user" | "ai" | "error";
  text: string;
  time: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
}

let globalContext: vscode.ExtensionContext;

export class ChatPanel {
  public static currentPanel: ChatPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];
  private apiClient: ApiClient;
  private statusBar: StatusBarManager;
  private conversations: Conversation[] = [];
  private activeConvId: string = "";

  private constructor(panel: vscode.WebviewPanel, extUri: vscode.Uri, apiClient: ApiClient, statusBar: StatusBarManager) {
    this.panel = panel; this.apiClient = apiClient; this.statusBar = statusBar;
    this.loadHistory();
    this.panel.webview.html = this.getHtml(extUri);
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage((msg) => this.handle(msg), null, this.disposables);
    this.sendConversations();
  }

  public static init(context: vscode.ExtensionContext): void {
    globalContext = context;
  }

  public static createOrShow(extUri: vscode.Uri, apiClient: ApiClient, statusBar: StatusBarManager): void {
    if (ChatPanel.currentPanel) { ChatPanel.currentPanel.panel.reveal(vscode.ViewColumn.Two); return; }
    const panel = vscode.window.createWebviewPanel("codeforgeChat", "CodeForge", vscode.ViewColumn.Two, { enableScripts: true, retainContextWhenHidden: true });
    ChatPanel.currentPanel = new ChatPanel(panel, extUri, apiClient, statusBar);
  }

  public static addMessage(text: string, type: "user" | "ai" | "error"): void {
    ChatPanel.currentPanel?.panel.webview.postMessage({ command: "addMessage", text, type });
  }

  private loadHistory(): void {
    this.conversations = globalContext.globalState.get<Conversation[]>("codeforge-conversations", []);
    if (this.conversations.length === 0) this.newConversation();
    else this.activeConvId = this.conversations[0].id;
  }

  private saveHistory(): void {
    globalContext.globalState.update("codeforge-conversations", this.conversations);
  }

  private newConversation(): void {
    const id = Date.now().toString();
    this.conversations.unshift({ id, title: "New Chat", messages: [], createdAt: new Date().toISOString() });
    this.activeConvId = id;
    this.saveHistory();
    this.sendConversations();
  }

  private getActiveConv(): Conversation | undefined {
    return this.conversations.find(c => c.id === this.activeConvId);
  }

  private sendConversations(): void {
    this.panel.webview.postMessage({
      command: "conversations",
      conversations: this.conversations.map(c => ({ id: c.id, title: c.title, count: c.messages.length })),
      activeId: this.activeConvId,
    });
  }

  private async handle(message: { command: string; text?: string; id?: string }): Promise<void> {
    switch (message.command) {
      case "sendMessage":
        if (message.text) await this.sendMessage(message.text);
        break;
      case "insertCode":
        if (message.text) {
          const editor = vscode.window.activeTextEditor;
          if (editor) editor.edit(e => e.insert(editor.selection.active, message.text!));
        }
        break;
      case "newConversation":
        this.newConversation();
        this.panel.webview.postMessage({ command: "clearMessages" });
        break;
      case "switchConversation":
        if (message.id) {
          this.activeConvId = message.id;
          this.panel.webview.postMessage({ command: "clearMessages" });
          const conv = this.getActiveConv();
          if (conv) conv.messages.forEach(m => this.panel.webview.postMessage({ command: "addMessage", text: m.text, type: m.role, time: m.time }));
          this.sendConversations();
        }
        break;
      case "deleteConversation":
        if (message.id) {
          this.conversations = this.conversations.filter(c => c.id !== message.id);
          if (this.activeConvId === message.id) {
            this.activeConvId = this.conversations[0]?.id || "";
            if (!this.activeConvId) this.newConversation();
            this.panel.webview.postMessage({ command: "clearMessages" });
            const conv = this.getActiveConv();
            if (conv) conv.messages.forEach(m => this.panel.webview.postMessage({ command: "addMessage", text: m.text, type: m.role, time: m.time }));
          }
          this.saveHistory();
          this.sendConversations();
        }
        break;
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