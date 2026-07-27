import * as vscode from "vscode";
import * as http from "http";
import { AdbManager } from "./adbManager";

let adbManager: AdbManager;

/**
 * Activates the CodeForge extension.
 */
export function activate(context: vscode.ExtensionContext) {
  console.log("CodeForge extension activated");

  adbManager = new AdbManager();

  // Register: Connect to Android
  const connectCommand = vscode.commands.registerCommand(
    "codeforge.connect",
    async () => {
      const connected = await adbManager.connect();
      if (connected) {
        vscode.window.showInformationMessage(
          "CodeForge: Ready! Open chat panel to start."
        );
      }
    }
  );

  // Register: Open Chat Panel
  const chatCommand = vscode.commands.registerCommand(
    "codeforge.start",
    () => {
      ChatPanel.createOrShow(context.extensionUri, adbManager);
    }
  );

  // Register: Disconnect
  const disconnectCommand = vscode.commands.registerCommand(
    "codeforge.disconnect",
    async () => {
      await adbManager.disconnect();
    }
  );

  context.subscriptions.push(connectCommand, chatCommand, disconnectCommand);
}

/**
 * Deactivates the extension and cleans up.
 */
export async function deactivate() {
  if (adbManager) {
    await adbManager.disconnect();
  }
  console.log("CodeForge extension deactivated");
}

/**
 * Manages the chat panel webview.
 */
class ChatPanel {
  private static currentPanel: ChatPanel | undefined;
  private readonly _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];
  private _adbManager: AdbManager;

  private constructor(
    panel: vscode.WebviewPanel,
    extensionUri: vscode.Uri,
    adbManager: AdbManager
  ) {
    this._panel = panel;
    this._adbManager = adbManager;
    this._panel.webview.html = this._getHtml(extensionUri);
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

    this._panel.webview.onDidReceiveMessage(
      (message) => this._handleMessage(message),
      null,
      this._disposables
    );
  }

  public static createOrShow(
    extensionUri: vscode.Uri,
    adbManager: AdbManager
  ) {
    const column = vscode.ViewColumn.Two;

    if (ChatPanel.currentPanel) {
      ChatPanel.currentPanel._panel.reveal(column);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      "codeforgeChat",
      "CodeForge Chat",
      column,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );

    ChatPanel.currentPanel = new ChatPanel(panel, extensionUri, adbManager);
  }

  private async _handleMessage(message: { command: string; text?: string }) {
    switch (message.command) {
      case "sendMessage":
        if (!message.text) return;
        
        // Check connection before sending
        const isReachable = await this._adbManager.isBackendReachable();
        if (!isReachable) {
          this._panel.webview.postMessage({
            command: "responseError",
            error: "Not connected to CodeForge server. Run 'CodeForge: Connect to Android' first.",
          });
          return;
        }
        
        await this._streamResponse(message.text);
        break;
    }
  }

  private async _streamResponse(userMessage: string) {
    const backendUrl = "http://127.0.0.1:8000/chat";

    try {
      this._panel.webview.postMessage({ command: "responseStart" });

      const response = await this._httpPost(backendUrl, {
        message: userMessage,
      });

      this._panel.webview.postMessage({
        command: "responseChunk",
        text: response,
      });

      this._panel.webview.postMessage({ command: "responseDone" });
    } catch (error) {
      this._panel.webview.postMessage({
        command: "responseError",
        error:
          error instanceof Error
            ? error.message
            : "Failed to connect to CodeForge backend",
      });
    }
  }

  private _httpPost(url: string, data: object): Promise<string> {
    return new Promise((resolve, reject) => {
      const postData = JSON.stringify(data);
      const parsedUrl = new URL(url);

      const options: http.RequestOptions = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(postData),
        },
        timeout: 30000,
      };

      const req = http.request(options, (res) => {
        let body = "";
        res.on("data", (chunk: Buffer) => {
          body += chunk.toString();
        });
        res.on("end", () => {
          if (res.statusCode === 200) {
            const parsed = JSON.parse(body);
            resolve(parsed.response || body);
          } else {
            reject(new Error(`Backend returned status ${res.statusCode}`));
          }
        });
      });

      req.on("error", (error) => {
        reject(new Error(`Cannot reach backend: ${error.message}`));
      });

      req.on("timeout", () => {
        req.destroy();
        reject(new Error("Request timed out"));
      });

      req.write(postData);
      req.end();
    });
  }

  private _getHtml(extensionUri: vscode.Uri): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeForge Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: var(--vscode-font-family);
            background: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 16px;
        }
        #chatContainer {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 12px;
        }
        .message {
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 6px;
            max-width: 85%;
            word-wrap: break-word;
        }
        .user-message {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            margin-left: auto;
        }
        .ai-message {
            background: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
        }
        .error-message {
            background: var(--vscode-inputValidation-errorBackground);
            border: 1px solid var(--vscode-inputValidation-errorBorder);
            color: var(--vscode-inputValidation-errorForeground);
        }
        .status-bar {
            padding: 4px 8px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 12px;
            text-align: center;
        }
        .status-connected {
            background: var(--vscode-terminal-ansiGreen);
            color: white;
        }
        .status-disconnected {
            background: var(--vscode-inputValidation-errorBackground);
            color: var(--vscode-inputValidation-errorForeground);
        }
        #inputContainer {
            display: flex;
            gap: 8px;
        }
        #messageInput {
            flex: 1;
            padding: 8px 12px;
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            font-family: inherit;
            resize: none;
        }
        #sendButton {
            padding: 8px 16px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        #sendButton:hover {
            background: var(--vscode-button-hoverBackground);
        }
        #sendButton:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div id="statusBar" class="status-bar status-disconnected">Disconnected</div>
    <div id="chatContainer"></div>
    <div id="inputContainer">
        <textarea id="messageInput" rows="2" placeholder="Connect first: Ctrl+Shift+P → CodeForge: Connect to Android"></textarea>
        <button id="sendButton">Send</button>
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const statusBar = document.getElementById('statusBar');
        let currentAiMessage = null;

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        function sendMessage() {
            const text = messageInput.value.trim();
            if (!text) return;

            addMessage(text, 'user-message');
            messageInput.value = '';
            sendButton.disabled = true;

            vscode.postMessage({ command: 'sendMessage', text: text });
        }

        window.addEventListener('message', (event) => {
            const message = event.data;

            switch (message.command) {
                case 'responseStart':
                    currentAiMessage = addMessage('', 'ai-message');
                    break;
                case 'responseChunk':
                    if (currentAiMessage) {
                        currentAiMessage.textContent += message.text;
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                    break;
                case 'responseDone':
                    sendButton.disabled = false;
                    messageInput.focus();
                    currentAiMessage = null;
                    break;
                case 'responseError':
                    addMessage('❌ ' + message.error, 'error-message');
                    sendButton.disabled = false;
                    currentAiMessage = null;
                    break;
                case 'connectionStatus':
                    if (message.connected) {
                        statusBar.textContent = '🟢 Connected to Android';
                        statusBar.className = 'status-bar status-connected';
                        messageInput.placeholder = 'Ask CodeForge...';
                    } else {
                        statusBar.textContent = '🔴 Disconnected';
                        statusBar.className = 'status-bar status-disconnected';
                        messageInput.placeholder = 'Connect first: Ctrl+Shift+P → CodeForge: Connect to Android';
                    }
                    break;
            }
        });

        function addMessage(text, className) {
            const div = document.createElement('div');
            div.className = 'message ' + className;
            div.textContent = text;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            return div;
        }
    </script>
</body>
</html>`;
  }

  private dispose() {
    ChatPanel.currentPanel = undefined;
    this._panel.dispose();

    while (this._disposables.length) {
      const disposable = this._disposables.pop();
      if (disposable) {
        disposable.dispose();
      }
    }
  }
}