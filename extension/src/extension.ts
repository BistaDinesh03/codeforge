import * as vscode from "vscode";
import { ApiClient, ServerConfig } from "./apiClient";
import { StatusBarManager } from "./statusBar";
import { ChatPanel } from "./chatPanel";
import { CodeActionProvider } from "./codeActions";
import { ServerDiscovery } from "./discovery";

let statusBar: StatusBarManager;
let apiClient: ApiClient;
let codeActions: CodeActionProvider;
let reconnectTimer: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext) {
  console.log("CodeForge extension activated");

  const config = vscode.workspace.getConfiguration("codeforge");
  const serverConfig: ServerConfig = {
    serverUrl: config.get("serverUrl", "http://127.0.0.1:8000"),
    maxTokens: config.get("maxTokens", 2048),
    temperature: config.get("temperature", 0.7),
  };

  apiClient = new ApiClient(serverConfig);
  statusBar = new StatusBarManager();
  codeActions = new CodeActionProvider(apiClient);

  // Auto-connect
  if (config.get("autoConnect", true)) {
    connect();
  }

  // Config changes
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

  // Commands
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
      connect();
    }),
    statusBar
  );
}

async function connect(): Promise<void> {
  statusBar.setConnected(false);

  // First, try current URL (might be localhost or manual IP)
  const healthy = await apiClient.healthCheck();
  if (healthy) {
    statusBar.setConnected(true);
    try {
      const version = await apiClient.getVersion();
      statusBar.setModel(version);
    } catch { /* ignore */ }
    startReconnectTimer();
    return;
  }

  // Try auto-discovery
  vscode.window.setStatusBarMessage("$(search) CodeForge: Searching for server...", 10000);

  try {
    const discovery = new ServerDiscovery();
    const server = await discovery.discover(8000); // 8 second timeout

    const serverUrl = `http://${server.host}:${server.port}`;
    apiClient.updateConfig({ serverUrl });

    // Update VS Code settings with discovered URL
    const config = vscode.workspace.getConfiguration("codeforge");
    config.update("serverUrl", serverUrl, vscode.ConfigurationTarget.Global);

    // Verify connection
    const found = await apiClient.healthCheck();
    if (found) {
      statusBar.setConnected(true);
      statusBar.setModel(server.version);
      vscode.window.showInformationMessage(
        `CodeForge: Connected to ${server.name} (${server.host})`
      );
      startReconnectTimer();
      return;
    }
  } catch (err) {
    // Discovery failed, show friendly message
    vscode.window.showWarningMessage(
      err instanceof Error ? err.message : "Cannot find CodeForge server",
      { modal: false },
      "Manual Setup..."
    ).then((choice) => {
      if (choice === "Manual Setup...") {
        vscode.commands.executeCommand(
          "workbench.action.openSettings",
          "codeforge.serverUrl"
        );
      }
    });
  }

  statusBar.setConnected(false);
}

function startReconnectTimer(): void {
  stopReconnectTimer();
  reconnectTimer = setInterval(async () => {
    const healthy = await apiClient.healthCheck();
    if (!healthy) {
      statusBar.setConnected(false);
      stopReconnectTimer();
      setTimeout(() => connect(), 5000);
    }
  }, 30000);
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