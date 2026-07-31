import * as vscode from "vscode";
import { ApiClient, ServerConfig } from "./apiClient";
import { StatusBarManager } from "./statusBar";
import { ChatPanel } from "./chatPanel";
import { CodeActionProvider } from "./codeActions";

let statusBar: StatusBarManager;
let apiClient: ApiClient;
let codeActions: CodeActionProvider;
let reconnectTimer: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext) {
  console.log("CodeForge extension activated");

  // Load config from VS Code settings
  const config = vscode.workspace.getConfiguration("codeforge");
  const serverConfig: ServerConfig = {
    serverUrl: config.get("serverUrl", "http://127.0.0.1:8000"),
    maxTokens: config.get("maxTokens", 2048),
    temperature: config.get("temperature", 0.7),
  };

  apiClient = new ApiClient(serverConfig);
  statusBar = new StatusBarManager();
  codeActions = new CodeActionProvider(apiClient);

  // Auto-connect if enabled
  if (config.get("autoConnect", true)) {
    checkConnection();
  }

  // Watch for config changes
  vscode.workspace.onDidChangeConfiguration((e) => {
    if (e.affectsConfiguration("codeforge")) {
      const newConfig = vscode.workspace.getConfiguration("codeforge");
      apiClient.updateConfig({
        serverUrl: newConfig.get("serverUrl", "http://127.0.0.1:8000"),
        maxTokens: newConfig.get("maxTokens", 2048),
        temperature: newConfig.get("temperature", 0.7),
      });
      checkConnection();
    }
  });

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand("codeforge.openChat", () => {
      ChatPanel.createOrShow(context.extensionUri, apiClient, statusBar);
    }),

    vscode.commands.registerCommand("codeforge.explainCode", () => {
      codeActions.explainCode();
    }),

    vscode.commands.registerCommand("codeforge.generateCode", () => {
      codeActions.generateCode();
    }),

    vscode.commands.registerCommand("codeforge.rewriteCode", () => {
      codeActions.rewriteCode();
    }),

    vscode.commands.registerCommand("codeforge.reconnect", () => {
      checkConnection();
    }),

    statusBar
  );
}

async function checkConnection(): Promise<void> {
  const healthy = await apiClient.healthCheck();
  statusBar.setConnected(healthy);

  if (healthy) {
    try {
      const version = await apiClient.getVersion();
      statusBar.setModel(version);
    } catch {
      // Server responded but version check failed
    }
    startReconnectTimer();
  } else {
    stopReconnectTimer();
  }
}

function startReconnectTimer(): void {
  stopReconnectTimer();
  reconnectTimer = setInterval(async () => {
    const healthy = await apiClient.healthCheck();
    if (!healthy) {
      statusBar.setConnected(false);
      stopReconnectTimer();
      // Try reconnecting
      setTimeout(checkConnection, 5000);
    }
  }, 30000); // Check every 30 seconds
}

function stopReconnectTimer(): void {
  if (reconnectTimer) {
    clearInterval(reconnectTimer);
    reconnectTimer = undefined;
  }
}

export function deactivate(): void {
  stopReconnectTimer();
  console.log("CodeForge extension deactivated");
}