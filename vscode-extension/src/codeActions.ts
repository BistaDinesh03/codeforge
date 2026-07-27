import * as vscode from "vscode";

/**
 * Handles all code manipulation actions:
 * - Getting selected text
 * - Replacing code in editor
 * - Applying diffs
 */
export class CodeActions {
  /**
   * Gets the currently selected text in the active editor.
   * Returns null if nothing is selected.
   */
  static getSelectedText(): string | null {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return null;

    const selection = editor.selection;
    if (selection.isEmpty) return null;

    return editor.document.getText(selection);
  }

  /**
   * Gets the current line if nothing is selected.
   * Useful for comments like "// generate a sorting function"
   */
  static getCurrentLine(): string | null {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return null;

    const line = editor.document.lineAt(editor.selection.active.line);
    return line.text;
  }

  /**
   * Gets the language ID of the current file (e.g., "typescript", "python").
   */
  static getLanguage(): string {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return "text";

    return editor.document.languageId;
  }

  /**
   * Gets full file path of the current document.
   */
  static getFilePath(): string | null {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return null;

    return editor.document.uri.fsPath;
  }

  /**
   * Replaces the current selection with new text.
   */
  static async replaceSelection(newText: string): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    await editor.edit((editBuilder) => {
      editBuilder.replace(editor.selection, newText);
    });
  }

  /**
   * Inserts text at the current cursor position.
   */
  static async insertAtCursor(text: string): Promise<void> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    await editor.edit((editBuilder) => {
      editBuilder.insert(editor.selection.active, text);
    });
  }

  /**
   * Creates a new untitled document with the given content.
   * Used for showing AI-generated code before user accepts it.
   */
  static async showInNewEditor(
    content: string,
    language: string,
    title: string
  ): Promise<vscode.TextDocument> {
    const doc = await vscode.workspace.openTextDocument({
      content: content,
      language: language,
    });

    await vscode.window.showTextDocument(doc, {
      preview: true,
      viewColumn: vscode.ViewColumn.Beside,
    });

    return doc;
  }

  /**
   * Shows a diff between original and modified code.
   * Left = original, Right = AI suggestion.
   */
  static async showDiff(
    original: string,
    modified: string,
    title: string,
    language: string
  ): Promise<void> {
    // Create temp files for diff view
    const originalUri = vscode.Uri.parse(
      `untitled:CodeForge_Original.${language}`
    );
    const modifiedUri = vscode.Uri.parse(
      `untitled:CodeForge_Suggestion.${language}`
    );

    // Open original
    const origDoc = await vscode.workspace.openTextDocument(originalUri);
    const origEditor = await vscode.window.showTextDocument(origDoc, {
      preview: true,
      viewColumn: vscode.ViewColumn.One,
    });
    await origEditor.edit((edit) => {
      edit.insert(new vscode.Position(0, 0), original);
    });

    // Open modified
    const modDoc = await vscode.workspace.openTextDocument(modifiedUri);
    const modEditor = await vscode.window.showTextDocument(modDoc, {
      preview: true,
      viewColumn: vscode.ViewColumn.Two,
    });
    await modEditor.edit((edit) => {
      edit.insert(new vscode.Position(0, 0), modified);
    });

    // Show diff command
    await vscode.commands.executeCommand(
      "vscode.diff",
      originalUri,
      modifiedUri,
      `CodeForge: ${title}`
    );
  }

  /**
   * Applies the AI suggestion by replacing selected code.
   */
  static async acceptChange(modified: string): Promise<void> {
    await CodeActions.replaceSelection(modified);
    vscode.window.showInformationMessage("CodeForge: Changes applied");
  }

  /**
   * Shows quick pick to accept or reject changes.
   */
  static async promptAcceptReject(
    modified: string
  ): Promise<"accept" | "reject" | null> {
    const choice = await vscode.window.showInformationMessage(
      "CodeForge: Accept this change?",
      { modal: false },
      "Accept",
      "Reject"
    );

    if (choice === "Accept") {
      await CodeActions.acceptChange(modified);
      return "accept";
    } else if (choice === "Reject") {
      vscode.window.showInformationMessage("CodeForge: Changes rejected");
      return "reject";
    }

    return null;
  }
}