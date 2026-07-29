import * as vscode from "vscode";
import { AdbManager } from "./adbManager";
import { ApiClient } from "./apiClient";
import { CodeActions } from "./codeActions";
import { getChatHtml } from "./chatHtml";

let adbManager: AdbManager;
let apiClient: ApiClient;

export function activate(context: vscode.ExtensionContext) {
  console.log("CodeForge extension activated");

  adbManager = new AdbManager();
  apiClient = new ApiClient();

  const connectCommand = vscode.commands.registerCommand(
    "codeforge.connect",
    async () => {
      const result = await adbManager.connect();
      if (!result.success) return;
      vscode.window.showInformationMessage(
        `CodeForge: Connected to ${result.deviceId || "Android device"}`
      );
    }
  );

  const disconnectCommand = vscode.commands.registerCommand(
    "codeforge.disconnect",
    async () => { await adbManager.disconnect(); }
  );

  const chatCommand = vscode.commands.registerCommand(
    "codeforge.start",
    () => { ChatPanel.createOrShow(context.extensionUri, apiClient); }
  );

  const explainCommand = vscode.commands.registerCommand(
    "codeforge.explainCode",
    async () => {
      const selectedText = CodeActions.getSelectedText();
      if (!selectedText) {
        vscode.window.showWarningMessage("Select some code to explain first.");
        return;
      }
      const language = CodeActions.getLanguage();
      vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "CodeForge: Explaining code...", cancellable: false },
        async () => {
          try {
            const explanation = await apiClient.explainCode(selectedText, language);
            ChatPanel.createOrShow(context.extensionUri, apiClient);
            ChatPanel.addMessage("Explaining " + language + " code:\n\n" + explanation, "ai");
          } catch (error) {
            vscode.window.showErrorMessage("CodeForge: " + (error instanceof Error ? error.message : "Failed"));
          }
        }
      );
    }
  );

  const generateCommand = vscode.commands.registerCommand(
    "codeforge.generateCode",
    async () => {
      const description = CodeActions.getSelectedText() || CodeActions.getCurrentLine();
      if (!description) {
        vscode.window.showWarningMessage("Type a description or comment first.");
        return;
      }
      const language = CodeActions.getLanguage();
      vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "CodeForge: Generating code...", cancellable: false },
        async () => {
          try {
            const generatedCode = await apiClient.generateCode(description, language);
            await CodeActions.showDiff("", generatedCode, "Generated Code", language);
            const choice = await vscode.window.showInformationMessage(
              "Insert generated code?", { modal: false }, "Insert at Cursor", "Replace Selection", "Cancel"
            );
            if (choice === "Insert at Cursor") { await CodeActions.insertAtCursor(generatedCode); }
            else if (choice === "Replace Selection") { await CodeActions.replaceSelection(generatedCode); }
          } catch (error) {
            vscode.window.showErrorMessage("CodeForge: " + (error instanceof Error ? error.message : "Failed"));
          }
        }
      );
    }
  );

  const rewriteCommand = vscode.commands.registerCommand(
    "codeforge.rewriteCode",
    async () => {
      const selectedText = CodeActions.getSelectedText();
      if (!selectedText) {
        vscode.window.showWarningMessage("Select code to rewrite first.");
        return;
      }
      const language = CodeActions.getLanguage();
      vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "CodeForge: Rewriting code...", cancellable: false },
        async () => {
          try {
            const rewrittenCode = await apiClient.rewriteCode(selectedText, language);
            await CodeActions.showDiff(selectedText, rewrittenCode, "Rewrite Suggestion", language);
            await CodeActions.promptAcceptReject(rewrittenCode);
          } catch (error) {
            vscode.window.showErrorMessage("CodeForge: " + (error instanceof Error ? error.message : "Failed"));
          }
        }
      );
    }
  );

  context.subscriptions.push(connectCommand, disconnectCommand, chatCommand, explainCommand, generateCommand, rewriteCommand);
}

export async function deactivate() {
  if (adbManager) { await adbManager.disconnect(); }
  console.log("CodeForge extension deactivated");
}

class ChatPanel {
  private static currentPanel: ChatPanel | undefined;
  private readonly _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];
  private _apiClient: ApiClient;

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri, apiClient: ApiClient) {
    this._panel = panel;
    this._apiClient = apiClient;
    this._panel.webview.html = getChatHtml();
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
    this._panel.webview.onDidReceiveMessage(
      (message) => this.handleMessage(message), null, this._disposables
    );
  }

  public static createOrShow(extensionUri: vscode.Uri, apiClient: ApiClient) {
    if (ChatPanel.currentPanel) {
      ChatPanel.currentPanel._panel.reveal(vscode.ViewColumn.Two);
      return;
    }
    const panel = vscode.window.createWebviewPanel(
      "codeforgeChat", "CodeForge Chat", vscode.ViewColumn.Two,
      { enableScripts: true, retainContextWhenHidden: true }
    );
    ChatPanel.currentPanel = new ChatPanel(panel, extensionUri, apiClient);
  }

  public static addMessage(text: string, type: "user" | "ai") {
    if (ChatPanel.currentPanel) {
      ChatPanel.currentPanel._panel.webview.postMessage({ command: "addMessage", text, type });
    }
  }

  private async handleMessage(message: { command: string; text?: string }) {
    if (message.command === "sendMessage" && message.text) {
      await this.sendChatMessage(message.text);
    }
  }

  private async sendChatMessage(userMessage: string) {
    try {
      this._panel.webview.postMessage({ command: "responseStart" });
      const response = await this._apiClient.sendChat(userMessage);
      this._panel.webview.postMessage({ command: "responseChunk", text: response });
      this._panel.webview.postMessage({ command: "responseDone" });
    } catch (error) {
      this._panel.webview.postMessage({
        command: "responseError",
        error: error instanceof Error ? error.message : "Failed to connect"
      });
    }
  }

  private dispose() {
    ChatPanel.currentPanel = undefined;
    this._panel.dispose();
    while (this._disposables.length) {
      const d = this._disposables.pop();
      if (d) { d.dispose(); }
    }
  }
}