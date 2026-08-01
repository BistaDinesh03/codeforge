import * as vscode from "vscode";
import { ApiClient } from "./apiClient";

export class SettingsPanel {
  public static currentPanel: SettingsPanel | undefined;
  private readonly panel: vscode.WebviewPanel;
  private disposables: vscode.Disposable[] = [];

  private constructor(panel: vscode.WebviewPanel, apiClient: ApiClient) {
    this.panel = panel;
    this.panel.webview.html = this.getHtml();
    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
    this.panel.webview.onDidReceiveMessage((msg) => this.handle(msg), null, this.disposables);
  }

  public static createOrShow(apiClient: ApiClient): void {
    if (SettingsPanel.currentPanel) { SettingsPanel.currentPanel.panel.reveal(vscode.ViewColumn.One); return; }
    const panel = vscode.window.createWebviewPanel("codeforgeSettings", "CodeForge Settings", vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
    SettingsPanel.currentPanel = new SettingsPanel(panel, apiClient);
  }

  private async handle(msg: { command: string; key?: string; value?: any }): Promise<void> {
    if (msg.command === "save" && msg.key) {
      const config = vscode.workspace.getConfiguration("codeforge");
      await config.update(msg.key, msg.value, vscode.ConfigurationTarget.Global);
      this.panel.webview.postMessage({ command: "saved", key: msg.key });
    }
    if (msg.command === "load") {
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
        body{font-family:var(--vscode-font-family);font-size:13px;padding:24px 32px;background:var(--vscode-editor-background,#1e1e1e);color:var(--vscode-editor-foreground,#d4d4d4)}
        h2{font-size:16px;margin-bottom:20px;padding-bottom:8px;border-bottom:1px solid var(--vscode-panel-border,#3c3c3c)}
        .section{margin-bottom:28px}
        .row{display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid rgba(128,128,128,0.08)}
        .row .info{flex:1}
        .row label{font-weight:500;font-size:13px}
        .row .desc{font-size:11px;color:var(--vscode-descriptionForeground,#999);margin-top:2px}
        .row input[type="text"],.row input[type="number"]{width:240px;padding:6px 10px;background:var(--vscode-input-background,#3c3c3c);color:var(--vscode-input-foreground,#fff);border:1px solid var(--vscode-input-border,#555);border-radius:4px;font-size:13px;font-family:inherit}
        .row input:focus{outline:none;border-color:var(--vscode-focusBorder,#1f6feb)}
        .row input[type="range"]{width:150px}
        .range-val{display:inline-block;width:50px;text-align:center;font-weight:600;font-size:13px}
        .toggle{position:relative;width:40px;height:22px;flex-shrink:0}
        .toggle input{display:none}
        .toggle .slider{position:absolute;top:0;left:0;right:0;bottom:0;background:#555;border-radius:22px;cursor:pointer;transition:.2s}
        .toggle .slider:before{content:'';position:absolute;height:16px;width:16px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.2s}
        .toggle input:checked+.slider{background:#238636}
        .toggle input:checked+.slider:before{transform:translateX(18px)}
        .saved{color:#3fb950;font-size:11px;margin-left:8px;opacity:0;transition:opacity .3s}.saved.show{opacity:1}
    </style>
</head>
<body>
    <h2>Server</h2>
    <div class="section">
        <div class="row">
            <div class="info"><label>Server URL</label><div class="desc">Where your CodeForge server is running</div></div>
            <input type="text" id="serverUrl" onchange="save('serverUrl',this.value)">
        </div>
        <div class="row">
            <div class="info"><label>Auto-connect on startup</label><div class="desc">Connect automatically when VS Code opens</div></div>
            <label class="toggle"><input type="checkbox" id="autoConnect" onchange="save('autoConnect',this.checked)"><span class="slider"></span></label>
        </div>
    </div>

    <h2>AI Model</h2>
    <div class="section">
        <div class="row">
            <div class="info"><label>Model Name</label><div class="desc">Leave empty to auto-detect best model</div></div>
            <input type="text" id="modelName" placeholder="auto-detect" onchange="save('modelName',this.value)">
        </div>
        <div class="row">
            <div class="info"><label>Max Tokens: <span class="range-val" id="tokensVal">2048</span></label><div class="desc">Maximum response length. Higher = longer responses, slower speed.</div></div>
            <input type="range" id="maxTokens" min="64" max="8192" step="64" value="2048" oninput="document.getElementById('tokensVal').textContent=this.value" onchange="save('maxTokens',parseInt(this.value))">
        </div>
        <div class="row">
            <div class="info"><label>Temperature: <span class="range-val" id="tempVal">0.7</span></label><div class="desc">Creativity level. 0 = precise/deterministic, 1 = creative/varied.</div></div>
            <input type="range" id="temperature" min="0" max="2" step="0.1" value="0.7" oninput="document.getElementById('tempVal').textContent=this.value" onchange="save('temperature',parseFloat(this.value))">
        </div>
    </div>

    <script>
        var vscode = acquireVsCodeApi();
        vscode.postMessage({command:'load'});
        
        window.addEventListener('message', function(e) {
            var m = e.data;
            if (m.command === 'config') {
                document.getElementById('serverUrl').value = m.data.serverUrl||'';
                document.getElementById('modelName').value = m.data.modelName||'';
                document.getElementById('maxTokens').value = m.data.maxTokens||2048;
                document.getElementById('temperature').value = m.data.temperature||0.7;
                document.getElementById('autoConnect').checked = m.data.autoConnect!==false;
                document.getElementById('tokensVal').textContent = m.data.maxTokens||2048;
                document.getElementById('tempVal').textContent = m.data.temperature||0.7;
            }
        });

        function save(key, value) {
            vscode.postMessage({command:'save',key:key,value:value});
        }
    </script>
</body>
</html>`;
  }

  private dispose(): void {
    SettingsPanel.currentPanel = undefined; this.panel.dispose();
    while (this.disposables.length) { const d = this.disposables.pop(); if (d) d.dispose(); }
  }
}