import * as vscode from "vscode";

/**
 * Maps technical errors to user-friendly messages with actions.
 */
export interface FriendlyError {
  message: string;
  action?: {
    label: string;
    callback: () => void;
  };
}

export function getFriendlyError(error: Error | string): FriendlyError {
  const msg = typeof error === "string" ? error : error.message;

  // Connection errors
  if (msg.includes("ECONNREFUSED") || msg.includes("Connection refused") || msg.includes("fetch failed")) {
    return {
      message: "Cannot reach CodeForge server. Is it running?",
      action: {
        label: "Start Server",
        callback: () => vscode.env.openExternal(vscode.Uri.parse("http://localhost:8000")),
      },
    };
  }

  // No model loaded
  if (msg.includes("503") || msg.includes("No AI model") || msg.includes("No model")) {
    return {
      message: "No AI model is loaded. Would you like to download one?",
      action: {
        label: "Open Dashboard",
        callback: () => vscode.env.openExternal(vscode.Uri.parse("http://localhost:8000")),
      },
    };
  }

  // Timeout
  if (msg.includes("timeout") || msg.includes("timed out") || msg.includes("AbortError")) {
    return {
      message: "Server is taking too long to respond. Try a shorter question or check your connection.",
    };
  }

  // Rate limit
  if (msg.includes("429") || msg.includes("Rate limit")) {
    return {
      message: "Too many requests. Please wait a moment and try again.",
    };
  }

  // Server error
  if (msg.includes("500") || msg.includes("Internal server")) {
    return {
      message: "Server encountered an error. Check the dashboard for details.",
      action: {
        label: "Open Dashboard",
        callback: () => vscode.env.openExternal(vscode.Uri.parse("http://localhost:8000/health/diagnostics")),
      },
    };
  }

  // Not found
  if (msg.includes("404")) {
    return {
      message: "Server endpoint not found. Make sure you're running the latest version.",
      action: {
        label: "Check for Updates",
        callback: () => vscode.commands.executeCommand("codeforge.reconnect"),
      },
    };
  }

  // Fallback
  return {
    message: `Something went wrong: ${msg}. Try reconnecting.`,
    action: {
      label: "Reconnect",
      callback: () => vscode.commands.executeCommand("codeforge.reconnect"),
    },
  };
}

/**
 * Show a friendly error to the user.
 */
export function showError(error: Error | string): void {
  const friendly = getFriendlyError(error);
  if (friendly.action) {
    vscode.window.showErrorMessage(friendly.message, friendly.action.label).then((choice) => {
      if (choice === friendly.action!.label) {
        friendly.action!.callback();
      }
    });
  } else {
    vscode.window.showErrorMessage(friendly.message);
  }
}