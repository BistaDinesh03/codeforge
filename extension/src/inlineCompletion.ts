import * as vscode from "vscode";
import { ApiClient } from "./apiClient";

/**
 * Provides inline code completions (ghost text like Copilot).
 * Debounces requests to avoid overwhelming the server.
 */
export class InlineCompletionProvider implements vscode.InlineCompletionItemProvider {
  private apiClient: ApiClient;
  private debounceTimer: NodeJS.Timeout | null = null;
  private debounceMs = 500; // Wait 500ms after typing stops

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async provideInlineCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position,
    context: vscode.InlineCompletionContext,
    token: vscode.CancellationToken
  ): Promise<vscode.InlineCompletionItem[]> {
    // Don't complete on empty lines or very short prefixes
    const line = document.lineAt(position.line);
    const prefix = document.getText(new vscode.Range(new vscode.Position(0, 0), position));
    
    if (prefix.trim().length < 3) return [];

    // Get suffix (code after cursor on current line)
    const suffix = document.getText(
      new vscode.Range(position, document.lineAt(document.lineCount - 1).range.end)
    );

    try {
      const result = await this.apiClient.complete(
        prefix,
        suffix,
        document.languageId
      );

      if (!result.completion || token.isCancellationRequested) return [];

      // Create completion item
      const item = new vscode.InlineCompletionItem(
        result.completion,
        new vscode.Range(position, position)
      );

      return [item];
    } catch (error) {
      // Silently fail — don't spam user with errors while typing
      console.debug("Completion failed:", error);
      return [];
    }
  }
}