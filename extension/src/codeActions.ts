import * as vscode from "vscode";
import { ApiClient } from "./apiClient";
import { ChatPanel } from "./chatPanel";

/**
 * Provides code actions with safe editing.
 * Every AI modification shows a diff preview first.
 * Changes use WorkspaceEdit for undo support.
 */
export class CodeActionProvider {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  getSelectedOrLineText(): { text: string; isSelection: boolean } {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return { text: "", isSelection: false };

    const selection = editor.selection;
    if (!selection.isEmpty) {
      return { text: editor.document.getText(selection), isSelection: true };
    }

    const line = editor.document.lineAt(selection.active.line);
    return { text: line.text, isSelection: false };
  }

  getLanguage(): string {
    const editor = vscode.window.activeTextEditor;
    return editor ? editor.document.languageId : "text";
  }

  async explainCode(): Promise<void> {
    const { text } = this.getSelectedOrLineText();
    if (!text.trim()) {
      vscode.window.showWarningMessage("Select some code to explain.");
      return;
    }
    const language = this.getLanguage();
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "CodeForge: Analyzing code..." },
      async () => {
        try {
          const result = await this.apiClient.explainCode(text, language);
          ChatPanel.addMessage(`**Explaining ${language} code:**\n\n${result.response}`, "ai");
        } catch (error) {
          vscode.window.showErrorMessage(`CodeForge: ${error instanceof Error ? error.message : "Failed"}`);
        }
      }
    );
  }

  async generateCode(): Promise<void> {
    const { text } = this.getSelectedOrLineText();
    const language = this.getLanguage();
    const description = text.trim();
    if (!description) {
      vscode.window.showWarningMessage("Type a description first.");
      return;
    }
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "CodeForge: Generating code..." },
      async () => {
        try {
          const result = await this.apiClient.generateCode(description, language);
          const editor = vscode.window.activeTextEditor;
          if (!editor) return;

          // Show diff preview before inserting
          const accepted = await this.showDiffPreview(
            "",
            result.response,
            language,
            "Generated Code"
          );

          if (accepted) {
            await this.applyEdit(
              editor.document.uri,
              editor.selection,
              result.response
            );
          }
        } catch (error) {
          vscode.window.showErrorMessage(`CodeForge: ${error instanceof Error ? error.message : "Failed"}`);
        }
      }
    );
  }

  async rewriteCode(): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const selection = editor.selection;
    if (selection.isEmpty) {
      vscode.window.showWarningMessage("Select code to rewrite.");
      return;
    }

    const text = editor.document.getText(selection);
    const language = this.getLanguage();

    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "CodeForge: Rewriting code..." },
      async () => {
        try {
          const result = await this.apiClient.rewriteCode(text, language);

          // Show diff preview
          const accepted = await this.showDiffPreview(
            text,
            result.response,
            language,
            "Rewrite Suggestion"
          );

          if (accepted) {
            await this.applyEdit(
              editor.document.uri,
              selection,
              result.response
            );
            vscode.window.showInformationMessage("CodeForge: Changes applied ✓ (Ctrl+Z to undo)");
          }
        } catch (error) {
          vscode.window.showErrorMessage(`CodeForge: ${error instanceof Error ? error.message : "Failed"}`);
        }
      }
    );
  }

  /**
   * Show a diff preview and ask user to accept or reject.
   * Returns true if user accepts, false if rejected.
   */
  private async showDiffPreview(
    original: string,
    modified: string,
    language: string,
    title: string
  ): Promise<boolean> {
    // Create temp URIs for diff view
    const timestamp = Date.now();
    const originalUri = vscode.Uri.parse(`untitled:original-${timestamp}.${language}`);
    const modifiedUri = vscode.Uri.parse(`untitled:codeforge-${timestamp}.${language}`);

    // Create documents with content
    const origDoc = await vscode.workspace.openTextDocument(originalUri);
    const modDoc = await vscode.workspace.openTextDocument(modifiedUri);

    // Insert content using WorkspaceEdit
    const edit = new vscode.WorkspaceEdit();
    edit.insert(originalUri, new vscode.Position(0, 0), original);
    edit.insert(modifiedUri, new vscode.Position(0, 0), modified);
    await vscode.workspace.applyEdit(edit);

    // Close the documents (they'll reopen in diff view)
    await vscode.commands.executeCommand("workbench.action.closeActiveEditor");
    await vscode.commands.executeCommand("workbench.action.closeActiveEditor");

    // Open diff view
    await vscode.commands.executeCommand(
      "vscode.diff",
      originalUri,
      modifiedUri,
      `CodeForge: ${title} (Original vs AI Suggestion)`
    );

    // Ask user
    const choice = await vscode.window.showInformationMessage(
      `${title}: Apply this change to your file?`,
      { modal: true },
      "Accept",
      "Reject"
    );

    return choice === "Accept";
  }

  /**
   * Apply text to a document using WorkspaceEdit.
   * This makes the change undoable with Ctrl+Z.
   */
  private async applyEdit(
    uri: vscode.Uri,
    range: vscode.Range | vscode.Selection,
    newText: string
  ): Promise<void> {
    const edit = new vscode.WorkspaceEdit();

    if (range.isEmpty) {
      // Insert at position
      edit.insert(uri, range.start, newText);
    } else {
      // Replace selection
      edit.replace(uri, range, newText);
    }

    const success = await vscode.workspace.applyEdit(edit);
    if (!success) {
      vscode.window.showErrorMessage("CodeForge: Failed to apply edit. File may be read-only.");
    }
  }
}