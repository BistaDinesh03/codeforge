import * as vscode from "vscode";
import { ApiClient } from "./apiClient";
import { ChatPanel } from "./chatPanel";

export class CodeActionProvider {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /** Get selected text, or current line if nothing selected */
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

  /** Get language of current file */
  getLanguage(): string {
    const editor = vscode.window.activeTextEditor;
    return editor ? editor.document.languageId : "text";
  }

  /** Get workspace folder path */
  getWorkspacePath(): string | undefined {
    const folder = vscode.workspace.workspaceFolders?.[0];
    return folder?.uri.fsPath;
  }

  /** Explain selected code */
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
          const explanation = await this.apiClient.explainCode(text, language);
          ChatPanel.addMessage(
            `**Explaining ${language} code:**\n\n${explanation}`,
            "ai"
          );
        } catch (error) {
          vscode.window.showErrorMessage(
            `CodeForge: ${error instanceof Error ? error.message : "Failed"}`
          );
        }
      }
    );
  }

  /** Generate code from description */
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
          const code = await this.apiClient.generateCode(description, language);
          const choice = await vscode.window.showInformationMessage(
            "Insert generated code?",
            { modal: false },
            "Insert at Cursor",
            "Replace Selection",
            "Cancel"
          );

          const editor = vscode.window.activeTextEditor;
          if (!editor) return;

          if (choice === "Insert at Cursor") {
            await editor.edit((edit) => {
              edit.insert(editor.selection.active, code);
            });
          } else if (choice === "Replace Selection") {
            await editor.edit((edit) => {
              edit.replace(editor.selection, code);
            });
          }
        } catch (error) {
          vscode.window.showErrorMessage(
            `CodeForge: ${error instanceof Error ? error.message : "Failed"}`
          );
        }
      }
    );
  }

  /** Rewrite selected code */
  async rewriteCode(): Promise<void> {
    const { text } = this.getSelectedOrLineText();
    if (!text.trim()) {
      vscode.window.showWarningMessage("Select code to rewrite.");
      return;
    }

    const language = this.getLanguage();

    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "CodeForge: Rewriting code..." },
      async () => {
        try {
          const rewritten = await this.apiClient.rewriteCode(text, language);

          // Show diff preview
          const originalUri = vscode.Uri.parse(`untitled:original.${language}`);
          const rewrittenUri = vscode.Uri.parse(`untitled:rewritten.${language}`);

          const origDoc = await vscode.workspace.openTextDocument(originalUri);
          const rewrDoc = await vscode.workspace.openTextDocument(rewrittenUri);

          const origEdit = new vscode.WorkspaceEdit();
          origEdit.insert(originalUri, new vscode.Position(0, 0), text);
          await vscode.workspace.applyEdit(origEdit);

          const rewrEdit = new vscode.WorkspaceEdit();
          rewrEdit.insert(rewrittenUri, new vscode.Position(0, 0), rewritten);
          await vscode.workspace.applyEdit(rewrEdit);

          await vscode.commands.executeCommand(
            "vscode.diff",
            originalUri,
            rewrittenUri,
            "CodeForge: Original ↔ Rewritten"
          );

          // Ask accept or reject
          const choice = await vscode.window.showInformationMessage(
            "Accept this rewrite?",
            { modal: false },
            "Accept",
            "Reject"
          );

          if (choice === "Accept") {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
              await editor.edit((edit) => {
                edit.replace(editor.selection, rewritten);
              });
            }
            vscode.window.showInformationMessage("CodeForge: Changes applied ✓");
          }
        } catch (error) {
          vscode.window.showErrorMessage(
            `CodeForge: ${error instanceof Error ? error.message : "Failed"}`
          );
        }
      }
    );
  }
}