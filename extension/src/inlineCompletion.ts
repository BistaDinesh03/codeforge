import * as vscode from "vscode";
import { ApiClient } from "./apiClient";

export class InlineCompletionProvider implements vscode.InlineCompletionItemProvider {
  private apiClient: ApiClient;
  private lastRequest: AbortController | null = null;
  private cache = new Map<string, { completion: string; time: number }>();
  private cacheTTL = 30000;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async provideInlineCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position,
    context: vscode.InlineCompletionContext,
    token: vscode.CancellationToken
  ): Promise<vscode.InlineCompletionItem[]> {
    // Skip on very small files — no context needed check
    const line = document.lineAt(position.line);
    const lineText = line.text.substring(0, position.character);

    // Don't complete if cursor is at whitespace-only start
    if (lineText.trim().length < 3) return [];

    // Don't complete in comments
    if (lineText.trim().startsWith("//") || lineText.trim().startsWith("#") || lineText.trim().startsWith("--")) {
      return [];
    }

    // Don't complete in strings
    if (this.isInString(lineText)) return [];

    // Skip files larger than 100KB for performance
    if (document.getText().length > 100_000) return [];

    // Cancel any in-flight request
    if (this.lastRequest) {
      this.lastRequest.abort();
    }
    this.lastRequest = new AbortController();

    // Get prefix (last 50 lines max for performance)
    const fullPrefix = document.getText(new vscode.Range(new vscode.Position(0, 0), position));
    const prefixLines = fullPrefix.split("\n");
    const prefix = prefixLines.slice(-50).join("\n");

    // Get suffix (rest of current line)
    const lineEnd = document.lineAt(position.line).range.end;
    const suffix = document.getText(new vscode.Range(position, lineEnd));

    // Get function context
    const functionName = this.getFunctionContext(document, position);

    // Check cache
    const cacheKey = `${prefix.slice(-100)}|${functionName}`;
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.time < this.cacheTTL) {
      if (!cached.completion) return [];
      return [this.createItem(cached.completion, position)];
    }

    try {
      const result = await this.apiClient.complete(
        prefix,
        suffix,
        document.languageId,
        this.lastRequest.signal
      );

      if (token.isCancellationRequested || !result.completion) {
        this.cache.set(cacheKey, { completion: "", time: Date.now() });
        return [];
      }

      const completion = result.completion.trim();
      if (completion.length < 2) return [];

      // Cache result
      this.cache.set(cacheKey, { completion, time: Date.now() });

      return [this.createItem(completion, position)];
    } catch {
      return [];
    }
  }

  private createItem(text: string, position: vscode.Position): vscode.InlineCompletionItem {
    const item = new vscode.InlineCompletionItem(text, new vscode.Range(position, position));
    item.filterText = text;
    return item;
  }

  private isInString(lineText: string): boolean {
    let inString = false;
    let quoteChar = "";
    for (let i = 0; i < lineText.length; i++) {
      const ch = lineText[i];
      if ((ch === '"' || ch === "'" || ch === "`") && !inString) {
        inString = true;
        quoteChar = ch;
      } else if (ch === quoteChar && inString) {
        if (i > 0 && lineText[i - 1] !== "\\") {
          inString = false;
          quoteChar = "";
        }
      }
    }
    return inString;
  }

  private getFunctionContext(document: vscode.TextDocument, position: vscode.Position): string {
    // Find the nearest function/class definition above cursor
    for (let i = position.line; i >= 0; i--) {
      const line = document.lineAt(i).text.trim();
      const match = line.match(/(?:def|function|class|fn|func|public|private)\s+(\w+)/);
      if (match) return match[1];
    }
    return "";
  }
}