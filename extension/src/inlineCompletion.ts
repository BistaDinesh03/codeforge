import * as vscode from "vscode";
import { ApiClient } from "./apiClient";

export class InlineCompletionProvider implements vscode.InlineCompletionItemProvider {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  async provideInlineCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position,
    context: vscode.InlineCompletionContext,
    token: vscode.CancellationToken
  ): Promise<vscode.InlineCompletionItem[]> {
    const line = document.lineAt(position.line);
    const lineText = line.text.substring(0, position.character);

    if (lineText.trim().length < 3) return [];
    if (this.isInComment(document, position)) return [];
    if (this.isInString(document, position)) return [];

    const prefix = document.getText(
      new vscode.Range(new vscode.Position(0, 0), position)
    );

    const lineEnd = document.lineAt(position.line).range.end;
    const suffix = document.getText(
      new vscode.Range(position, lineEnd)
    );

    const abortController = new AbortController();
    const timeoutId = setTimeout(() => abortController.abort(), 2000);

    try {
      const result = await this.apiClient.complete(
        prefix,
        suffix,
        document.languageId,
        abortController.signal
      );

      clearTimeout(timeoutId);

      if (token.isCancellationRequested || !result.completion) return [];

      const completion = result.completion.trim();
      if (completion.length < 2) return [];

      const item = new vscode.InlineCompletionItem(
        completion,
        new vscode.Range(position, position)
      );

      item.filterText = completion;
      return [item];
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof DOMException && error.name === "AbortError") {
        return [];
      }
      console.debug("Completion error:", error);
      return [];
    }
  }

  private isInComment(document: vscode.TextDocument, position: vscode.Position): boolean {
    const line = document.lineAt(position.line);
    const textBeforeCursor = line.text.substring(0, position.character).trim();

    if (textBeforeCursor.startsWith("//")) return true;
    if (textBeforeCursor.startsWith("#")) return true;
    if (textBeforeCursor.startsWith("--")) return true;

    const textBefore = document.getText(
      new vscode.Range(new vscode.Position(0, 0), position)
    );
    const lastOpen = textBefore.lastIndexOf("/*");
    const lastClose = textBefore.lastIndexOf("*/");
    if (lastOpen > lastClose) return true;

    return false;
  }

  private isInString(document: vscode.TextDocument, position: vscode.Position): boolean {
    const line = document.lineAt(position.line);
    const textBeforeCursor = line.text.substring(0, position.character);

    let inString = false;
    let quoteChar = "";

    for (let i = 0; i < textBeforeCursor.length; i++) {
      const ch = textBeforeCursor[i];
      if ((ch === '"' || ch === "'" || ch === "`") && !inString) {
        inString = true;
        quoteChar = ch;
      } else if (ch === quoteChar && inString) {
        if (i > 0 && textBeforeCursor[i - 1] !== "\\") {
          inString = false;
          quoteChar = "";
        }
      }
    }

    return inString;
  }
}