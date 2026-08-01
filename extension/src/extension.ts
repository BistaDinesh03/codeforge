import * as vscode from "vscode";
import { ApiClient, ServerConfig } from "./apiClient";
import { StatusBarManager } from "./statusBar";
import { ChatPanel } from "./chatPanel";
import { CodeActionProvider } from "./codeActions";
import { ServerDiscovery } from "./discovery";
import { InlineCompletionProvider } from "./inlineCompletion";
import { SettingsPanel } from "./settingsPanel";
import { showError } from "./errorHandler";

let statusBar: StatusBarManager;
let apiClient: ApiClient;
let codeActions: CodeActionProvider;
let reconnectTimer: NodeJS.Timeout | undefined;
let retryCount = 0;

export function activate(context: vscode.ExtensionContext) {
  const c = vscode.workspace.getConfiguration("codeforge");
  apiClient = new ApiClient({ serverUrl: c.get("serverUrl","http://127.0.0.1:8000"), maxTokens: c.get("maxTokens",2048), temperature: c.get("temperature",0.7) });
  statusBar = new StatusBarManager();
  codeActions = new CodeActionProvider(apiClient);
  ChatPanel.init(context);
  vscode.languages.registerInlineCompletionItemProvider({pattern:"**"}, new InlineCompletionProvider(apiClient));
  if (c.get("autoConnect",true)) connect();

  context.subscriptions.push(
    vscode.commands.registerCommand("codeforge.openChat", () => ChatPanel.createOrShow(context.extensionUri, apiClient, statusBar)),
    vscode.commands.registerCommand("codeforge.openSettings", () => SettingsPanel.createOrShow(apiClient)),
    vscode.commands.registerCommand("codeforge.explainCode", () => codeActions.explainCode().catch(showError)),
    vscode.commands.registerCommand("codeforge.generateCode", () => codeActions.generateCode().catch(showError)),
    vscode.commands.registerCommand("codeforge.rewriteCode", () => codeActions.rewriteCode().catch(showError)),
    vscode.commands.registerCommand("codeforge.reconnect", () => { retryCount=0; connect(); }),
    statusBar
  );
}

async function connect(): Promise<void> {
  statusBar.setConnected(false);
  if (await apiClient.healthCheck()) { statusBar.setConnected(true); retryCount=0; startMonitor(); return; }
  try {
    const s = await new ServerDiscovery().discover(5000);
    apiClient.updateConfig({serverUrl:`http://${s.host}:${s.port}`});
    if (await apiClient.healthCheck()) { statusBar.setConnected(true); retryCount=0; startMonitor(); return; }
  } catch {}
  retryCount++;
  if (retryCount <= 5) setTimeout(connect, Math.min(2000*Math.pow(2,retryCount-1),30000));
  else showError("Cannot connect. Check if server is running.");
}

function startMonitor(): void {
  if (reconnectTimer) clearInterval(reconnectTimer);
  reconnectTimer = setInterval(async () => { if (!await apiClient.healthCheck()) { statusBar.setConnected(false); retryCount=0; connect(); } }, 15000);
}

export function deactivate(): void { if (reconnectTimer) clearInterval(reconnectTimer); }