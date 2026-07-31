import * as vscode from "vscode";

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  private connected: boolean = false;
  private modelName: string = "";
  private tokensPerSecond: number = 0;

  constructor() {
    this.item = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.item.command = "codeforge.openChat";
    this.updateDisplay();
    this.item.show();
  }

  setConnected(connected: boolean): void {
    this.connected = connected;
    this.updateDisplay();
  }

  setModel(name: string): void {
    this.modelName = name;
    this.updateDisplay();
  }

  setSpeed(tps: number): void {
    this.tokensPerSecond = tps;
    this.updateDisplay();
  }

  private updateDisplay(): void {
    if (this.connected) {
      this.item.backgroundColor = undefined;
      this.item.text = `$(check) CodeForge`;
      this.item.tooltip = this.modelName
        ? `Connected • Model: ${this.modelName} • ${this.tokensPerSecond} t/s`
        : "Connected to CodeForge server";
    } else {
      this.item.backgroundColor = new vscode.ThemeColor(
        "statusBarItem.errorBackground"
      );
      this.item.text = `$(warning) CodeForge`;
      this.item.tooltip = "Disconnected • Click to connect";
    }
  }

  dispose(): void {
    this.item.dispose();
  }
}