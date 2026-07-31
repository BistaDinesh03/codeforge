import * as vscode from "vscode";
import { ApiClient, ServerConfig } from "./apiClient";
import { StatusBarManager } from "./statusBar";
import { ChatPanel } from "./chatPanel";
import { CodeActionProvider } from "./codeActions";
import { ServerDiscovery } from "./discovery";
import { InlineCompletionProvider } from "./inlineCompletion";
import { showError } from "./errorHandler";

let statusBar: StatusBarManager;
let apiClient: ApiClient;
let codeActions: CodeActionProvider;
let reconnectTimer: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration("codeforge");
  const serverConfig: ServerConfig = {
    serverUrl: config.get("serverUrl", "http://127.0.0.1:8000"),
    maxTokens: config.get("maxTokens", 2048),
    temperature: config.get("temperature", 0.7),
  };

  apiClient = new ApiClient(serverConfig);
  statusBar = new StatusBarManager();
  codeActions = new CodeActionProvider(apiClient);

  vscode.languages.registerInlineCompletionItemProvider(
    { pattern: "**" },
    new InlineCompletionProvider(apiClient)
  );

  if (config.get("autoConnect", true)) {
    connect();
  }

  vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration("codeforge")) {
      const c = vscode.workspace.getConfiguration("codeforge");
      apiClient.updateConfig({
        serverUrl: c.get("serverUrl", "http://127.0.0.1:8000"),
        maxTokens: c.get("maxTokens", 2048),
        temperature: c.get("temperature", 0.7),
      });
      connect();
    }
  });

  context.subscriptions.push(
    vscode.commands.registerCommand("codeforge.openChat", () => {
      ChatPanel.createOrShow(context.extensionUri, apiClient, statusBar);
    }),
    vscode.commands.registerCommand("codeforge.explainCode", () => {
      codeActions.explainCode().catch(showError);
    }),
    vscode.commands.registerCommand("codeforge.generateCode", () => {
      codeActions.generateCode().catch(showError);
    }),
    vscode.commands.registerCommand("codeforge.rewriteCode", () => {
      codeActions.rewriteCode().catch(showError);
    }),
    vscode.commands.registerCommand("codeforge.reconnect", () => {
      connect();
    }),
    statusBar
  );
}

async function connect(): Promise<void> {
  statusBar.setConnected(false);
  const healthy = await apiClient.healthCheck();
  if (healthy) {
    statusBar.setConnected(true);
    startReconnectTimer();
    return;
  }

  try {
    const discovery = new ServerDiscovery();
    const server = await discovery.discover(8000);
    apiClient.updateConfig({ serverUrl: `http://${server.host}:${server.port}` });
    const found = await apiClient.healthCheck();
    if (found) {
      statusBar.setConnected(true);
      vscode.window.showInformationMessage(`Connected to ${server.name}`);
      startReconnectTimer();
      return;
    }
  } catch {
    showError("Cannot find CodeForge server on your network.");
  }
  statusBar.setConnected(false);
}

function startReconnectTimer(): void {
  stopReconnectTimer();
  reconnectTimer = setInterval(async () => {
    if (!(await apiClient.healthCheck())) {
      statusBar.setConnected(false);
      stopReconnectTimer();
      setTimeout(() => connect(), 5000);
    }
  }, 30000);
}

function stopReconnectTimer(): void {
  if (reconnectTimer) { clearInterval(reconnectTimer); reconnectTimer = undefined; }
}

export function deactivate(): void {
  stopReconnectTimer();
}