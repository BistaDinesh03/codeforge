import * as vscode from "vscode";
import { ApiClient } from "./apiClient";

export class SettingsPanel {
  public static currentPanel: SettingsPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];
  private apiClient: ApiClient;

  private constructor(panel: vscode.WebviewPanel, apiClient: ApiClient) {
    this.panel = panel;
    this.apiClient = apiClient;

    this.panel.webview.html = this.getHtml();
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage(
      (msg) => this.handleMessage(msg),
      null,
      this.disposables
    );
  }

  public static createOrShow(apiClient: ApiClient): void {
    if (SettingsPanel.currentPanel) {
      SettingsPanel.currentPanel.panel.reveal(vscode.ViewColumn.One);
      return;
    }
    const panel = vscode.window.createWebviewPanel(
      "codeforgeSettings",
      "CodeForge Settings",
      vscode.ViewColumn.One,
      { enableScripts: true, retainContextWhenHidden: true }
    );
    SettingsPanel.currentPanel = new SettingsPanel(panel, apiClient);
  }

  private async handleMessage(message: { command: string; key?: string; value?: any }): Promise<void> {
    if (message.command === "save" && message.key) {
      const config = vscode.workspace.getConfiguration("codeforge");
      await config.update(message.key, message.value, vscode.ConfigurationTarget.Global);
      this.panel.webview.postMessage({ command: "saved", key: message.key });
    }
    if (message.command === "load") {
      const config = vscode.workspace.getConfiguration("codeforge");
      this.panel.webview.postMessage({
        command: "config",
        data: {
          serverUrl: config.get("serverUrl", "http://127.0.0.1:8000"),
          maxTokens: config.get("maxTokens", 2048),
          temperature: config.get("temperature", 0.7),
          autoConnect: config.get("autoConnect", true),
          modelName: config.get("modelName", ""),
        },
      });
    }
  }

  private getHtml(): string {
    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:var(--vscode-font-family,sans-serif);font-size:13px;padding:24px;background:var(--vscode-editor-background,#1e1e1e);color:var(--vscode-editor-foreground,#d4d4d4)}
        h2{font-size:18px;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid var(--vscode-panel-border,#3c3c3c)}
        .group{margin-bottom:24px}
        .row{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--vscode-panel-border,#3c3c3c20)}
        .row label{font-weight:500;flex:1}
        .row .desc{font-size:11px;color:var(--vscode-descriptionForeground,#8b949e);margin-top:2px}
        input,select{background:var(--vscode-input-background,#3c3c3c);color:var(--vscode-input-foreground,white);border:1px solid var(--vscode-input-border,#555);border-radius:4px;padding:6px 10px;font-size:13px;width:200px}
        input[type=range]{width:150px;padding:0}
        .range-value{width:60px;text-align:center;font-weight:600}
        .toggle{position:relative;width:40px;height:22px}
        .toggle input{display:none}
        .toggle .slider{position:absolute;top:0;left:0;right:0;bottom:0;background:#555;border-radius:22px;cursor:pointer;transition:.2s}
        .toggle .slider:before{content:'';position:absolute;height:16px;width:16px;left:3px;bottom:3px;background:white;border-radius:50%;transition:.2s}
        .toggle input:checked+.slider{background:#238636}
        .toggle input:checked+.slider:before{transform:translateX(18px)}
        .saved{color:#3fb950;font-size:11px;margin-left:8px;opacity:0}
        .saved.show{opacity:1}
    </style>
</head>
<body>
    <h2>Server Connection</h2>
    <div class="group">
        <div class="row">
            <div>
                <label>Server Address</label>
                <div class="desc">Where your CodeForge server is running</div>
            </div>
            <input id="serverUrl" value="http://127.0.0.1:8000" onchange="save('serverUrl',this.value)">
        </div>
    </div>

    <h2>AI Model</h2>
    <div class="group">
        <div class="row">
            <div>
                <label>Model Name</label>
                <div class="desc">Leave empty for auto-detect</div>
            </div>
            <input id="modelName" placeholder="auto-detect" onchange="save('modelName',this.value)">
        </div>
        <div class="row">
            <div>
                <label>Max Tokens: <span class="range-value" id="tokensLabel">2048</span></label>
                <div class="desc">Maximum response length. Higher = longer responses.</div>
            </div>
            <input type="range" id="maxTokens" min="64" max="8192" step="64" value="2048" oninput="updateRange('maxTokens','tokensLabel')" onchange="save('maxTokens',parseInt(this.value))">
        </div>
        <div class="row">
            <div>
                <label>Temperature: <span class="range-value" id="tempLabel">0.7</span></label>
                <div class="desc">Creativity. 0 = precise, 1 = creative.</div>
            </div>
            <input type="range" id="temperature" min="0" max="2" step="0.1" value="0.7" oninput="updateRange('temperature','tempLabel')" onchange="save('temperature',parseFloat(this.value))">
        </div>
    </div>

    <h2>Behavior</h2>
    <div class="group">
        <div class="row">
            <div>
                <label>Auto-connect on startup</label>
                <div class="desc">Connect to server automatically when VS Code opens</div>
            </div>
            <label class="toggle">
                <input type="checkbox" id="autoConnect" checked onchange="save('autoConnect',this.checked)">
                <span class="slider"></span>
            </label>
        </div>
    </div>

    <script>
        var vscode = acquireVsCodeApi();
        vscode.postMessage({ command: 'load' });

        window.addEventListener('message', function(event) {
            var msg = event.data;
            if (msg.command === 'config') {
                document.getElementById('serverUrl').value = msg.data.serverUrl || '';
                document.getElementById('modelName').value = msg.data.modelName || '';
                document.getElementById('maxTokens').value = msg.data.maxTokens || 2048;
                document.getElementById('temperature').value = msg.data.temperature || 0.7;
                document.getElementById('autoConnect').checked = msg.data.autoConnect !== false;
                updateRange('maxTokens', 'tokensLabel');
                updateRange('temperature', 'tempLabel');
            }
            if (msg.command === 'saved') {
                var el = document.querySelector('[data-key="' + msg.key + '"]');
                if (el) { el.classList.add('show'); setTimeout(function() { el.classList.remove('show'); }, 1500); }
            }
        });

        function save(key, value) {
            vscode.postMessage({ command: 'save', key: key, value: value });
        }

        function updateRange(sliderId, labelId) {
            document.getElementById(labelId).textContent = document.getElementById(sliderId).value;
        }
    </script>
</body>
</html>`;
  }

  private dispose(): void {
    SettingsPanel.currentPanel = undefined;
    this.panel.dispose();
    while (this.disposables.length) { const d = this.disposables.pop(); if (d) d.dispose(); }
  }
}