import * as vscode from "vscode";
import * as http from "http";

/**
 * Activates the CodeForge extension.
 * Registers the command to open the chat panel.
 */
export function activate(context: vscode.ExtensionContext) {
  console.log("CodeForge extension activated");

  const startCommand = vscode.commands.registerCommand(
    "codeforge.start",
    () => {
      ChatPanel.createOrShow(context.extensionUri);
    }
  );

  context.subscriptions.push(startCommand);
}

/**
 * Deactivates the extension and cleans up resources.
 */
export function deactivate() {
  console.log("CodeForge extension deactivated");
}

/**
 * Manages the chat panel webview.
 * Handles all communication between VS Code and the webview UI.
 */
class ChatPanel {
  private static currentPanel: ChatPanel | undefined;
  private readonly _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];

  private constructor(panel: vscode.WebviewPanel, extensionUri: vscode.Uri) {
    this._panel = panel;
    this._panel.webview.html = this._getHtml(extensionUri);
    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);

    // Handle messages from the webview
    this._panel.webview.onDidReceiveMessage(
      (message) => this._handleMessage(message),
      null,
      this._disposables
    );
  }

  /**
   * Creates a new chat panel or reveals the existing one.
   */
  public static createOrShow(extensionUri: vscode.Uri) {
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

    ChatPanel.currentPanel = new ChatPanel(panel, extensionUri);
  }

  /**
   * Handles messages sent from the webview.
   * User typed a message -> send to backend -> stream response back.
   */
  private async _handleMessage(message: { command: string; text?: string }) {
    switch (message.command) {
      case "sendMessage":
        if (!message.text) return;
        await this._streamResponse(message.text);
        break;
    }
  }

  /**
   * Sends user message to FastAPI backend and streams the response.
   */
  private async _streamResponse(userMessage: string) {
    const backendUrl = "http://127.0.0.1:8000/chat";

    try {
      // Tell the webview we're loading
      this._panel.webview.postMessage({
        command: "responseStart",
      });

      const response = await this._httpPost(backendUrl, {
        message: userMessage,
      });

      // Send the response back to the webview
      this._panel.webview.postMessage({
        command: "responseChunk",
        text: response,
      });

      this._panel.webview.postMessage({
        command: "responseDone",
      });
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

  /**
   * Simple HTTP POST helper.
   * Sends JSON to the backend and returns the response body.
   */
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
        timeout: 30000, // 30 second timeout
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

  /**
   * Generates the HTML for the chat panel.
   */
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
        #messageInput:focus {
            outline: 1px solid var(--vscode-focusBorder);
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
        .loading {
            color: var(--vscode-descriptionForeground);
            font-style: italic;
            padding: 8px 12px;
        }
    </style>
</head>
<body>
    <div id="chatContainer"></div>
    <div id="inputContainer">
        <textarea id="messageInput" rows="2" placeholder="Ask CodeForge..."></textarea>
        <button id="sendButton">Send</button>
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        let currentAiMessage = null;

        // Send message on button click
        sendButton.addEventListener('click', sendMessage);

        // Send message on Enter (Shift+Enter for new line)
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        function sendMessage() {
            const text = messageInput.value.trim();
            if (!text) return;

            // Add user message to chat
            addMessage(text, 'user-message');
            messageInput.value = '';
            sendButton.disabled = true;

            // Send to extension
            vscode.postMessage({ command: 'sendMessage', text: text });
        }

        // Handle messages from extension
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

  /**
   * Clean up resources when the panel is closed.
   */
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