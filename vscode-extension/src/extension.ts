import * as vscode from "vscode";
import { AdbManager } from "./adbManager";
import { ApiClient } from "./apiClient";
import { CodeActions } from "./codeActions";

let adbManager: AdbManager;
let apiClient: ApiClient;

export function activate(context: vscode.ExtensionContext) {
  console.log("CodeForge extension activated");

  adbManager = new AdbManager();
  apiClient = new ApiClient();

  const connectCommand = vscode.commands.registerCommand(
    "codeforge.connect",
    async () => {
      const connected = await adbManager.connect();
      if (connected) {
        vscode.window.showInformationMessage("CodeForge: Ready! Connected to Android AI server.");
      }
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
    this._panel.webview.html = this.getHtml();
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
      const response = await (this._apiClient as any).sendChat(userMessage);
      this._panel.webview.postMessage({ command: "responseChunk", text: response });
      this._panel.webview.postMessage({ command: "responseDone" });
    } catch (error) {
      this._panel.webview.postMessage({
        command: "responseError",
        error: error instanceof Error ? error.message : "Failed to connect"
      });
    }
  }

  private getHtml(): string {
    const html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: sans-serif; padding: 12px; margin: 0; background: #1e1e1e; color: #d4d4d4; }
        #chatContainer { height: calc(100vh - 120px); overflow-y: auto; margin-bottom: 8px; }
        .message { margin: 8px 0; padding: 8px 12px; border-radius: 6px; max-width: 90%; }
        .user-message { background: #0e639c; color: white; margin-left: auto; }
        .ai-message { background: #2d2d2d; border: 1px solid #404040; }
        .error-message { background: #5a1d1d; border: 1px solid #ff4444; color: #ff8888; }
        #inputContainer { display: flex; gap: 8px; }
        #messageInput { flex: 1; padding: 8px; background: #3c3c3c; color: #d4d4d4; border: 1px solid #555; border-radius: 4px; resize: none; }
        #sendButton { padding: 8px 16px; background: #0e639c; color: white; border: none; border-radius: 4px; cursor: pointer; }
        #sendButton:disabled { opacity: 0.5; }
    </style>
</head>
<body>
    <div id="chatContainer"></div>
    <div id="inputContainer">
        <textarea id="messageInput" rows="2" placeholder="Ask CodeForge..."></textarea>
        <button id="sendButton">Send</button>
    </div>
    <script>
        var vscode = acquireVsCodeApi();
        var chatContainer = document.getElementById('chatContainer');
        var messageInput = document.getElementById('messageInput');
        var sendButton = document.getElementById('sendButton');
        var currentAiMessage = null;

        sendButton.addEventListener('click', function() {
            var text = messageInput.value.trim();
            if (!text) return;
            addMessage(text, 'user-message');
            messageInput.value = '';
            sendButton.disabled = true;
            vscode.postMessage({ command: 'sendMessage', text: text });
        });

        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendButton.click();
            }
        });

        window.addEventListener('message', function(event) {
            var msg = event.data;
            switch (msg.command) {
                case 'responseStart':
                    currentAiMessage = addMessage('', 'ai-message');
                    break;
                case 'responseChunk':
                    if (currentAiMessage) {
                        currentAiMessage.textContent = msg.text;
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                    break;
                case 'responseDone':
                    sendButton.disabled = false;
                    messageInput.focus();
                    currentAiMessage = null;
                    break;
                case 'responseError':
                    addMessage('Error: ' + msg.error, 'error-message');
                    sendButton.disabled = false;
                    currentAiMessage = null;
                    break;
                case 'addMessage':
                    var cls = msg.type === 'user' ? 'user-message' : 'ai-message';
                    addMessage(msg.text, cls);
                    break;
            }
        });

        function addMessage(text, className) {
            var div = document.createElement('div');
            div.className = 'message ' + className;
            div.textContent = text;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return div;
        }
    </script>
</body>
</html>`;
    return html;
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